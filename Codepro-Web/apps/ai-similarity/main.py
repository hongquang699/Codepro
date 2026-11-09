"""Internal code similarity service. Results are review signals, never verdicts."""

import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from backend.anti_cheat.services.similarity import (
    ALGORITHM_VERSION,
    fingerprint,
    normalize_tokens,
    similarity_score,
    source_digest,
)


app = FastAPI(title="CodeProOJ similarity", docs_url=None, redoc_url=None)


class CompareRequest(BaseModel):
    source_a: str = Field(max_length=200_000)
    source_b: str = Field(max_length=200_000)
    language: str = Field(max_length=64)


class CompareResponse(BaseModel):
    score: float
    algorithm_version: str
    source_a_sha256: str
    source_b_sha256: str
    common_fingerprints: int
    fingerprints_a: int
    fingerprints_b: int


def require_token(x_service_token: str | None = Header(default=None)) -> None:
    expected = os.getenv("AI_SIMILARITY_TOKEN", "")
    if not expected or not x_service_token or not secrets.compare_digest(x_service_token, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/compare", response_model=CompareResponse, dependencies=[Depends(require_token)])
def compare(request: CompareRequest):
    first = fingerprint(normalize_tokens(request.source_a, request.language))
    second = fingerprint(normalize_tokens(request.source_b, request.language))
    return CompareResponse(
        score=similarity_score(first, second),
        algorithm_version=ALGORITHM_VERSION,
        source_a_sha256=source_digest(request.source_a),
        source_b_sha256=source_digest(request.source_b),
        common_fingerprints=len(first & second),
        fingerprints_a=len(first),
        fingerprints_b=len(second),
    )
