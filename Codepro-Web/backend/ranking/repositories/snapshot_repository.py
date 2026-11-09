from ..models.ranking_snapshot import RankingSnapshot

class SnapshotRepository:
    @staticmethod
    def save_snapshot(snapshot_type, key, data):
        return RankingSnapshot.objects.create(
            snapshot_type=snapshot_type,
            snapshot_key=key,
            data=data
        )

    @staticmethod
    def get_latest_snapshot(snapshot_type, key):
        return RankingSnapshot.objects.filter(
            snapshot_type=snapshot_type,
            snapshot_key=key
        ).order_by('-created_at').first()
