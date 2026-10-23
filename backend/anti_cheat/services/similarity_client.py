"""Optional internal similarity service with a local fallback."""

import logging
import os

import requests

from .similarity import ALGORITHM_VERSION, similarity_score, source_digest


logger = logging.getLogger(__name__)


def compare(first, second, first_fingerprint, second_fingerprint):
    local_score = similarity_score(first_fingerprint, second_fingerprint)
    local = (local_score, ALGORITHM_VERSION, {
        'common_fingerprints': len(first_fingerprint & second_fingerprint),
        'fingerprints_a': len(first_fingerprint),
        'fingerprints_b': len(second_fingerprint),
        'method': 'Jaccard similarity of normalized token fingerprints',
    })
    url = os.getenv('AI_SIMILARITY_URL', '').rstrip('/')
    token = os.getenv('AI_SIMILARITY_TOKEN', '')
    if not url or not token:
        return local
    try:
        response = requests.post(
            f'{url}/compare',
            json={
                'source_a': first.source, 'source_b': second.source,
                'language': first.language.key or first.language.name,
            },
            headers={'X-Service-Token': token}, timeout=2,
        )
        response.raise_for_status()
        result = response.json()
        if (result['source_a_sha256'] != source_digest(first.source)
                or result['source_b_sha256'] != source_digest(second.source)):
            raise ValueError('Similarity response source digests differ')
        score = float(result['score'])
        if not 0 <= score <= 100:
            raise ValueError('Similarity score outside 0..100')
        return score, str(result['algorithm_version'])[:32], {
            'common_fingerprints': int(result['common_fingerprints']),
            'fingerprints_a': int(result['fingerprints_a']),
            'fingerprints_b': int(result['fingerprints_b']),
            'method': 'Internal similarity service',
        }
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        logger.warning('Similarity service unavailable; using local score: %s', exc)
        return local
