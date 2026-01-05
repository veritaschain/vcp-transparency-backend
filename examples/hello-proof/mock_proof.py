#!/usr/bin/env python3
"""
Generate a mock proof for testing verification logic.
Does not require Trillian/Tessera - creates a valid single-leaf tree.

Usage:
    python3 mock_proof.py sample_event.json > proof.json
    python3 verify.py sample_event.json proof.json
"""

import json
import sys
import hashlib
import base64
import time
from canonicalize import canonicalize


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def compute_leaf_hash(data: bytes) -> bytes:
    """RFC 6962 leaf hash: SHA-256(0x00 || data)"""
    return sha256(b'\x00' + data)


def generate_mock_proof(event_json: dict) -> dict:
    """
    Generate a valid proof for a single-leaf tree.
    
    In a single-leaf tree:
    - leaf_index = 0
    - tree_size = 1
    - root_hash = leaf_hash
    - inclusion_proof.hashes = [] (empty)
    """
    # Canonicalize
    canonical_str = canonicalize(event_json)
    canonical_bytes = canonical_str.encode('utf-8')
    
    # Compute leaf hash
    leaf_hash = compute_leaf_hash(canonical_bytes)
    
    # In single-leaf tree, root = leaf
    root_hash = leaf_hash
    
    # Build proof structure
    proof = {
        "transparency_anchor": {
            "backend_type": "mock",
            "log_id": "vcp-hello-proof-mock",
            "leaf_index": 0,
            "tree_size": 1,
            "root_hash": base64.b64encode(root_hash).decode('ascii'),
            "timestamp_nanos": int(time.time() * 1_000_000_000),
            "inclusion_proof": {
                "hashes": []  # Empty for single-leaf tree
            }
        },
        "debug": {
            "canonical_json": canonical_str,
            "canonical_sha256": base64.b64encode(sha256(canonical_bytes)).decode('ascii'),
            "leaf_hash": base64.b64encode(leaf_hash).decode('ascii')
        }
    }
    
    return proof


def main():
    if len(sys.argv) < 2:
        print("Usage: mock_proof.py <event.json>", file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    with open(input_file, 'r', encoding='utf-8') as f:
        event = json.load(f)
    
    proof = generate_mock_proof(event)
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()
