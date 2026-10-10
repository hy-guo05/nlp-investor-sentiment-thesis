#!/bin/bash
# Push files to GitHub via API using curl (bypasses proxy issues)
TOKEN="$1"
OWNER="hy-guo05"
REPO="nlp-investor-sentiment-thesis"
BRANCH="main"
API="https://api.github.com"

# 关闭代理干扰
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY

cd "$(dirname "$0")"

# 收集文件列表（排除 .git / __pycache__ / site / push脚本自身）
FILES=$(find . -type f \
  -not -path "./.git/*" \
  -not -path "*/__pycache__/*" \
  -not -path "./site/*" \
  -not -name "*.pyc" \
  -not -name "push_via_api.py" \
  | sed 's|^\./||' | sort)

echo "=== files ==="
echo "$FILES"
echo "=== uploading ==="

while IFS= read -r f; do
  [ -z "$f" ] && continue
  enc=$(printf '%s' "$f" | sed 's/ /%20/g')
  content=$(base64 -w0 "$f" 2>/dev/null || base64 "$f" | tr -d '\n')

  # get existing sha
  sha=$(curl -s --noproxy '*' --max-time 30 \
    -H "Authorization: token $TOKEN" \
    -H "User-Agent: push" \
    "$API/repos/$OWNER/$REPO/contents/$enc?ref=$BRANCH" \
    | grep -o '"sha":"[^"]*"' | head -1 | cut -d'"' -f4)

  if [ -n "$sha" ]; then
    body=$(printf '{"message":"Update %s","content":"%s","branch":"%s","sha":"%s"}' "$f" "$content" "$BRANCH" "$sha")
    act="update"
  else
    body=$(printf '{"message":"Add %s","content":"%s","branch":"%s"}' "$f" "$content" "$BRANCH")
    act="add"
  fi

  code=$(curl -s --noproxy '*' --max-time 60 -o /tmp/resp.json -w "%{http_code}" \
    -X PUT \
    -H "Authorization: token $TOKEN" \
    -H "User-Agent: push" \
    -H "Accept: application/vnd.github+json" \
    -H "Content-Type: application/json" \
    "$API/repos/$OWNER/$REPO/contents/$enc" \
    -d "$body")

  echo "[$code $act] $f"
done <<< "$FILES"
