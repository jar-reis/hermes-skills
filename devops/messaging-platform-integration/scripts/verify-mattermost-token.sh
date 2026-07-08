#!/bin/bash
# Verify Mattermost bot token
# Usage: ./verify-mattermost-token.sh [API_URL] [TOKEN]

API_URL=${1:-http://localhost:8065/api/v4}
TOKEN=${2:-$(grep MATTERMOST_BOT_TOKEN ~/.hermes/.env | cut -d '=' -f2- | tr -d '"')}

if [ -z "$TOKEN" ]; then
  echo "ERROR: MATTERMOST_BOT_TOKEN not found in ~/.hermes/.env"
  exit 1
fi

response=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_URL/users/me")

if echo "$response" | grep -q '"username":"hermes"'; then
  echo "✅ Token valid. Bot username: hermes"
  exit 0
else
  echo "❌ Token invalid or bot not found:"
  echo "$response" | jq .
  exit 1
fi