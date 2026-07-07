#!/usr/bin/env bash
set -euo pipefail

curl -s http://localhost:8000/health | jq .

curl -s -X POST http://localhost:8000/api/v1/leads \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Test Lead","email":"test@example.com","intent":"study_abroad","target_country":"Germany","source":"smoke_test"}' | jq .

curl -s -X POST http://localhost:8000/api/v1/truth/verify \
  -H "Content-Type: application/json" \
  -d '{"claim":"Germany student visa is guaranteed without financial proof","domain":"visa","country":"Germany"}' | jq .
