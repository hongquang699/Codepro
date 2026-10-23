"""Contract checks for the optional similarity service and worker fallback."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from backend.anti_cheat.services.similarity_client import compare as worker_compare
from backend.anti_cheat.services.similarity import fingerprint, normalize_tokens


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ai_similarity', ROOT / 'apps' / 'ai-similarity' / 'main.py')
service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service)


SOURCE = 'int main() { int value = 1; return value; }'


def submission(source=SOURCE):
    return SimpleNamespace(source=source, language=SimpleNamespace(key='cpp17', name='C++17'))


def test_service_requires_token(monkeypatch):
    monkeypatch.setenv('AI_SIMILARITY_TOKEN', 'test-token')
    with pytest.raises(HTTPException) as error:
        service.require_token('wrong')
    assert error.value.status_code == 401
    service.require_token('test-token')


def test_service_matches_local_algorithm():
    result = service.compare(service.CompareRequest(
        source_a=SOURCE, source_b=SOURCE.replace('value', 'answer'), language='cpp17',
    ))
    assert result.score == 100
    assert result.common_fingerprints > 0
    assert result.source_a_sha256 != result.source_b_sha256


def test_worker_falls_back_when_service_unavailable(monkeypatch):
    monkeypatch.setenv('AI_SIMILARITY_URL', 'http://ai-similarity:8010')
    monkeypatch.setenv('AI_SIMILARITY_TOKEN', 'test-token')
    first = submission()
    second = submission(SOURCE.replace('value', 'answer'))
    first_fingerprint = fingerprint(normalize_tokens(first.source, 'cpp17'))
    second_fingerprint = fingerprint(normalize_tokens(second.source, 'cpp17'))
    from requests import Timeout
    with patch('backend.anti_cheat.services.similarity_client.requests.post', side_effect=Timeout):
        score, version, evidence = worker_compare(
            first, second, first_fingerprint, second_fingerprint,
        )
    assert score == 100
    assert version == 'token-winnow-1'
    assert evidence['method'] == 'Jaccard similarity of normalized token fingerprints'


def test_worker_accepts_service_result_only_for_matching_sources(monkeypatch):
    monkeypatch.setenv('AI_SIMILARITY_URL', 'http://ai-similarity:8010')
    monkeypatch.setenv('AI_SIMILARITY_TOKEN', 'test-token')
    first = submission()
    second = submission(SOURCE.replace('value', 'answer'))
    first_fingerprint = fingerprint(normalize_tokens(first.source, 'cpp17'))
    second_fingerprint = fingerprint(normalize_tokens(second.source, 'cpp17'))
    service_result = service.compare(service.CompareRequest(
        source_a=first.source, source_b=second.source, language='cpp17',
    )).model_dump()
    response = SimpleNamespace(raise_for_status=lambda: None, json=lambda: service_result)
    with patch('backend.anti_cheat.services.similarity_client.requests.post', return_value=response) as post:
        score, _, evidence = worker_compare(first, second, first_fingerprint, second_fingerprint)
    assert score == 100
    assert evidence['method'] == 'Internal similarity service'
    assert post.call_args.kwargs['timeout'] == 2

    service_result['source_b_sha256'] = '0' * 64
    with patch('backend.anti_cheat.services.similarity_client.requests.post', return_value=response):
        _, _, evidence = worker_compare(first, second, first_fingerprint, second_fingerprint)
    assert evidence['method'] == 'Jaccard similarity of normalized token fingerprints'
