#!/bin/bash
# Quick test of hello-proof example (no Trillian/Tessera required)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== VCP Transparency Backend: Hello Proof Test ==="
echo ""

echo "1. Input event:"
cat sample_event.json | head -10
echo "   ..."
echo ""

echo "2. Canonicalizing (RFC 8785)..."
python3 canonicalize.py sample_event.json > canonical.json
echo "   Output: canonical.json ($(wc -c < canonical.json) bytes)"
echo ""

echo "3. Generating mock proof (single-leaf tree)..."
python3 mock_proof.py sample_event.json > proof.json
echo "   Output: proof.json"
echo ""

echo "4. Verifying inclusion proof..."
python3 verify.py sample_event.json proof.json
echo ""

echo "=== Test complete ==="
