#!/usr/bin/env python3
"""
Verify VCP transparency log inclusion proof.

Usage:
    python3 verify.py sample_event.json proof.json
"""

import json
import sys
import hashlib
import base64
from typing import List

# Import canonicalize from sibling module
from canonicalize import canonicalize


def sha256(data: bytes) -> bytes:
    """Compute SHA-256 hash."""
    return hashlib.sha256(data).digest()


def compute_leaf_hash(data: bytes) -> bytes:
    """
    Compute Merkle leaf hash per RFC 6962.
    leaf_hash = SHA-256(0x00 || data)
    """
    return sha256(b'\x00' + data)


def compute_root_from_proof(
    leaf_hash: bytes,
    leaf_index: int,
    tree_size: int,
    proof_hashes: List[bytes]
) -> bytes:
    """
    Compute Merkle root from leaf hash and inclusion proof.
    
    RFC 6962 / RFC 9162 proof verification algorithm.
    """
    if tree_size == 0:
        raise ValueError("Tree size cannot be 0")
    
    if tree_size == 1:
        # Single-leaf tree: leaf hash is root hash
        if proof_hashes:
            raise ValueError("Proof should be empty for single-leaf tree")
        return leaf_hash
    
    # Walk the proof
    node = leaf_hash
    index = leaf_index
    size = tree_size
    
    for sibling in proof_hashes:
        if index % 2 == 1 or index + 1 == size:
            # Node is right child, or last node at this level
            if index % 2 == 1:
                # Hash(sibling || node)
                node = sha256(b'\x01' + sibling + node)
            else:
                # Hash(node || sibling)
                node = sha256(b'\x01' + node + sibling)
        else:
            # Node is left child
            node = sha256(b'\x01' + node + sibling)
        
        index //= 2
        size = (size + 1) // 2
    
    return node


def verify_inclusion_proof(event_json: dict, proof: dict) -> bool:
    """
    Verify that event is included in transparency log.
    
    Steps:
    1. Re-canonicalize the event
    2. Compute leaf hash
    3. Walk inclusion proof to compute root
    4. Compare with claimed root hash
    """
    # 1. Re-canonicalize
    canonical_str = canonicalize(event_json)
    canonical_bytes = canonical_str.encode('utf-8')
    
    # 2. Compute leaf hash
    leaf_hash = compute_leaf_hash(canonical_bytes)
    
    # 3. Extract proof components
    anchor = proof.get('transparency_anchor', proof)
    leaf_index = anchor['leaf_index']
    tree_size = anchor['tree_size']
    root_hash = base64.b64decode(anchor['root_hash'])
    
    inclusion = anchor.get('inclusion_proof', {})
    proof_hashes_b64 = inclusion.get('hashes', [])
    proof_hashes = [base64.b64decode(h) for h in proof_hashes_b64]
    
    # 4. Compute root from proof
    computed_root = compute_root_from_proof(
        leaf_hash, leaf_index, tree_size, proof_hashes
    )
    
    # 5. Compare
    return computed_root == root_hash


def main():
    if len(sys.argv) < 3:
        print("Usage: verify.py <event.json> <proof.json>", file=sys.stderr)
        sys.exit(1)
    
    event_file = sys.argv[1]
    proof_file = sys.argv[2]
    
    with open(event_file, 'r', encoding='utf-8') as f:
        event = json.load(f)
    
    with open(proof_file, 'r', encoding='utf-8') as f:
        proof = json.load(f)
    
    # Verify
    try:
        valid = verify_inclusion_proof(event, proof)
        
        if valid:
            print("✓ Inclusion proof valid")
            print(f"  Leaf index: {proof.get('transparency_anchor', proof)['leaf_index']}")
            print(f"  Tree size:  {proof.get('transparency_anchor', proof)['tree_size']}")
            sys.exit(0)
        else:
            print("✗ Inclusion proof INVALID")
            print("  Computed root does not match claimed root")
            sys.exit(1)
            
    except Exception as e:
        print(f"✗ Verification failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
