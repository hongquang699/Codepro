import logging
from ..services.rating_service import RatingService

logger = logging.getLogger(__name__)

def run_compute_ratings(contest_id):
    try:
        res = RatingService.calculate_and_apply_contest_ratings(contest_id)
        logger.info(f"Computed ratings for contest {contest_id}: {res}")
        return res
    except Exception as e:
        logger.error(f"Error computing ratings for contest {contest_id}: {e}")
        return {'status': 'error', 'message': str(e)}

if __name__ == '__main__':
    import sys, django, os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')
    django.setup()
    cid = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    print(run_compute_ratings(cid))
