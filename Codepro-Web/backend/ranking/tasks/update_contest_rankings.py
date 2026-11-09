import logging
from ..services.contest_ranking_service import ContestRankingService
from ..cache.scoreboard_cache import ScoreboardCache

logger = logging.getLogger(__name__)

def run_update_contest_rankings(contest_id):
    try:
        res = ContestRankingService.get_scoreboard(contest_id, live=True)
        ScoreboardCache.invalidate(contest_id)
        return {'status': 'success', 'participants': len(res.get('rows', []))}
    except Exception as e:
        logger.error(f"Error updating contest rankings: {e}")
        return {'status': 'error', 'message': str(e)}

if __name__ == '__main__':
    import sys, django, os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')
    django.setup()
    cid = sys.argv[1] if len(sys.argv) > 1 else 1
    print(run_update_contest_rankings(cid))
