from backend.judge.models import Submission, Language, Problem, Profile, Contest
import hashlib

# Aliasing & helper methods
def get_source_hash(source_code: str) -> str:
    return hashlib.sha256(source_code.encode('utf-8')).hexdigest()

Submission.get_source_hash = get_source_hash
__all__ = ['Submission', 'Language', 'Problem', 'Profile', 'Contest', 'get_source_hash']
