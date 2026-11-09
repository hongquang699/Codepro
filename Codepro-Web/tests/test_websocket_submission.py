import asyncio
from unittest.mock import AsyncMock, patch

from asgiref.testing import ApplicationCommunicator
from channels.layers import get_channel_layer
from channels.routing import URLRouter
from django.test import SimpleTestCase, override_settings

from backend.core.asgi import application
from websocket.routing import websocket_urlpatterns
from websocket.submission.consumer import SubmissionConsumer, broadcast_submission_update


@override_settings(CHANNEL_LAYERS={'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}})
class SubmissionWebSocketTests(SimpleTestCase):
    def test_status_stream_and_private_fields(self):
        async def scenario():
            app = URLRouter(websocket_urlpatterns)
            client = ApplicationCommunicator(app, {
                'type': 'websocket', 'path': '/ws/submissions/42/',
                'query_string': b'', 'headers': [], 'subprotocols': [],
            })
            with patch.object(SubmissionConsumer, 'initial_status', new=AsyncMock(return_value={'status': 'GRADING', 'finished': False})):
                await client.send_input({'type': 'websocket.connect'})
                self.assertEqual((await client.receive_output())['type'], 'websocket.accept')
                self.assertEqual((await client.receive_output())['text'], '{"status": "GRADING", "finished": false}')
                await get_channel_layer().group_send('submission.42', {
                    'type': 'submission.update', 'data': {'status': 'FINISHED', 'verdict': 'AC'}
                })
                self.assertEqual((await client.receive_output())['text'], '{"status": "FINISHED", "verdict": "AC"}')
                await client.send_input({'type': 'websocket.disconnect', 'code': 1000})
                await client.wait()

        asyncio.run(scenario())

        received = {}

        class Layer:
            async def group_send(self, group, event):
                received.update(group=group, event=event)

        with patch('websocket.submission.consumer.get_channel_layer', return_value=Layer()):
            broadcast_submission_update(42, {'status': 'FINISHED', 'verdict': 'AC', 'testcases': ['secret'], 'source': 'secret'})
        self.assertEqual(received['group'], 'submission.42')
        self.assertEqual(received['event']['data'], {'status': 'FINISHED', 'verdict': 'AC'})

    def test_unknown_submission_is_rejected(self):
        async def scenario():
            client = ApplicationCommunicator(URLRouter(websocket_urlpatterns), {
                'type': 'websocket', 'path': '/ws/submissions/999/',
                'query_string': b'', 'headers': [], 'subprotocols': [],
            })
            with patch.object(SubmissionConsumer, 'initial_status', new=AsyncMock(return_value=None)):
                await client.send_input({'type': 'websocket.connect'})
                self.assertEqual((await client.receive_output())['type'], 'websocket.close')
                await client.wait()

        asyncio.run(scenario())

    def test_same_origin_required(self):
        async def connect(origin):
            client = ApplicationCommunicator(application, {
                'type': 'websocket', 'path': '/ws/submissions/42/',
                'query_string': b'', 'subprotocols': [],
                'headers': [(b'host', b'localhost:8888'), (b'origin', origin)],
            })
            with patch.object(SubmissionConsumer, 'initial_status', new=AsyncMock(return_value={'status': 'FINISHED'})):
                await client.send_input({'type': 'websocket.connect'})
                response = await client.receive_output()
                if response['type'] == 'websocket.accept':
                    await client.receive_output()
                    await client.send_input({'type': 'websocket.disconnect', 'code': 1000})
                await client.wait()
                return response['type']

        self.assertEqual(asyncio.run(connect(b'http://localhost:8888')), 'websocket.accept')
        self.assertEqual(asyncio.run(connect(b'https://evil.example')), 'websocket.close')
