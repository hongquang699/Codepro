"""Read-only submission status stream.

Only public status fields are sent. Clients fetch any detailed result through
the normal HTTP API, which applies its own visibility rules.
"""

import logging

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)
PUBLIC_FIELDS = frozenset({'id', 'status', 'verdict', 'score', 'time', 'memory', 'finished', 'progress'})


def submission_group(submission_id):
    return f"submission.{int(submission_id)}"


def broadcast_submission_update(submission_id, data):
    """Publish a status change from synchronous judge code."""
    layer = get_channel_layer()
    if layer is None:
        logger.warning("Submission WebSocket channel layer is unavailable")
        return
    async_to_sync(layer.group_send)(
        submission_group(submission_id),
        {"type": "submission.update", "data": {
            key: value for key, value in data.items() if key in PUBLIC_FIELDS
        }},
    )


class SubmissionConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.submission_id = int(self.scope["url_route"]["kwargs"]["submission_id"])
        self.group_name = submission_group(self.submission_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        status = await self.initial_status(self.submission_id)
        if status is None:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            await self.close(code=4404)
            return
        await self.accept()
        await self.send_json(status)

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        await self.close(code=1008)

    async def submission_update(self, event):
        await self.send_json(event["data"])

    @database_sync_to_async
    def initial_status(self, submission_id):
        from backend.judge.models import Submission
        sub = Submission.objects.filter(pk=submission_id).values(
            'id', 'status', 'result', 'points', 'time', 'memory'
        ).first()
        if sub is None:
            return None
        return {
            'id': sub['id'],
            'status': 'FINISHED' if sub['status'] == 'D' else {
                'QU': 'QUEUED', 'P': 'PROCESSING', 'G': 'GRADING'
            }.get(sub['status'], sub['status']),
            'verdict': sub['result'] or 'JUDGING',
            'score': sub['points'] or 0,
            'time': round((sub['time'] or 0) * 1000, 1),
            'memory': round((sub['memory'] or 0) / 1024, 2),
            'finished': sub['status'] == 'D',
        }
