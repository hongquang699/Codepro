#!/bin/bash

URL="http://127.0.0.1:9999/api/v1/health"
RESPONSE=$(curl -s "$URL")

if echo "$RESPONSE" | grep -q '"status": "healthy"'; then
    echo "Judge Server is HEALTHY: $RESPONSE"
    exit 0
else
    echo "Judge Server is UNHEALTHY or unreachable: $RESPONSE"
    exit 1
fi
