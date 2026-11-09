import logging
from ..services.ranking_service import RankingService
from ..cache.ranking_cache import RankingCache

logger = logging.getLogger(__name__)

def run_update_global_rankings():
    try:
        count = RankingService.recalculate_all_global_rankings()
        RankingCache.invalidate()
        logger.info(f"Successfully updated global rankings for {count} users.")
        return {'status': 'success', 'count': count}
    except Exception as e:
        logger.error(f"Error updating global rankings: {e}")
        return {'status': 'error', 'message': str(e)}

if __name__ == '__main__':
    import django, os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')
    django.setup()
    res = run_update_global_rankings()
    print(res)
