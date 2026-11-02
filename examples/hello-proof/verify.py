#!/usr/bin/env python3
"""Check local inclusion consistency; never authenticate a log or VCP event.

Changed 2026-11-01: validate proof shape and input bounds, and distinguish an
unauthenticated hash match (INDETERMINATE, exit 2) from invalid input (exit 1).
The legacy serializer is retained; this is not a complete RFC 8785/CT verifier.
"""

import base64
import binascii
import hashlib
import json
import math
import sys
from typing import List

from canonicalize import canonicalize


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def compute_leaf_hash(data: bytes) -> bytes:
    """Hash the exact supplied bytes with the Merkle leaf domain separator."""
    return sha256(b"\x00" + data)


def _digest(value: bytes) -> None:
    if not isinstance(value, bytes) or len(value) != 32:
        raise ValueError("Every SHA-256 node must be exactly 32 bytes")


def compute_root_from_proof(
    leaf_hash: bytes,
    leaf_index: int,
    tree_size: int,
    proof_hashes: List[bytes],
) -> bytes:
    """Reconstruct a SHA-256 tree root for a fully consumed inclusion path.

    Derive the path's shape by splitting each subtree at the largest power of
    two smaller than its size (RFC 9162 sections 2.1.1 and 2.1.3.1). This avoids
    duplicating an odd last node and checks the required number of siblings.
    The resulting root still needs authentication outside this local helper.
    """
    _digest(leaf_hash)
    if type(tree_size) is not int or not 1 <= tree_size < 2**64:
        raise ValueError("Tree size must be a positive uint64 integer")
    if type(leaf_index) is not int or not 0 <= leaf_index < tree_size:
        raise ValueError("Leaf index must be an integer within the tree")
    if not isinstance(proof_hashes, list):
        raise ValueError("Inclusion path must be a list")

    sibling_sides = []
    size, index = tree_size, leaf_index
    while size > 1:
        split = 1 << ((size - 1).bit_length() - 1)
        if index < split:
            sibling_sides.append("right")
            size = split
        else:
            sibling_sides.append("left")
            index -= split
            size -= split
    if len(proof_hashes) != len(sibling_sides):
        raise ValueError("Inclusion path does not match tree size and leaf index")

    node = leaf_hash
    for side, sibling in zip(reversed(sibling_sides), proof_hashes):
        _digest(sibling)
        left, right = (sibling, node) if side == "left" else (node, sibling)
        node = sha256(b"\x01" + left + right)
    return node


def _decode_digest(value: str) -> bytes:
    if not isinstance(value, str) or len(value) != 44:
        raise ValueError("Digest must be canonical Base64 for 32 bytes")
    decoded = base64.b64decode(value, validate=True)
    _digest(decoded)
    if base64.b64encode(decoded).decode("ascii") != value:
        raise ValueError("Digest has a non-canonical Base64 representation")
    return decoded


def check_inclusion_consistency(event_json: dict, proof: dict) -> bool:
    """Return only whether the event matches the proof's untrusted root.

    False includes malformed input. True authenticates neither the event nor
    the root's source. The event uses the existing example serializer, whose
    documented number formatting and key-ordering differences are unchanged.
    """
    try:
        if not isinstance(event_json, dict) or not isinstance(proof, dict):
            return False
        anchor = proof.get("transparency_anchor", proof)
        if not isinstance(anchor, dict):
            return False
        inclusion = anchor["inclusion_proof"]
        if not isinstance(inclusion, dict) or not isinstance(inclusion["hashes"], list):
            return False
        # A uint64 tree never needs more than 64 sibling nodes.
        if len(inclusion["hashes"]) > 64:
            return False
        root = _decode_digest(anchor["root_hash"])
        path = [_decode_digest(value) for value in inclusion["hashes"]]
        leaf = compute_leaf_hash(canonicalize(event_json).encode("utf-8"))
        computed = compute_root_from_proof(
            leaf, anchor["leaf_index"], anchor["tree_size"], path
        )
        return computed == root
    except (KeyError, TypeError, ValueError, binascii.Error, UnicodeError, RecursionError):
        return False


def verify_inclusion_proof(event_json: dict, proof: dict) -> bool:
    """Compatibility alias for local consistency only, not authentication."""
    return check_inclusion_consistency(event_json, proof)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("Non-finite JSON number")


def _finite_float(value):
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError("JSON number overflows a finite float")
    return parsed


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print("Usage: verify.py <event.json> <proof.json>", file=sys.stderr)
        return 1
    try:
        documents = []
        for path in args:
            with open(path, "r", encoding="utf-8") as stream:
                documents.append(json.load(
                    stream, object_pairs_hook=_unique_object,
                    parse_constant=_reject_constant,
                    parse_float=_finite_float,
                ))
    except (OSError, ValueError, UnicodeError, RecursionError):
        print("INVALID: input cannot be read as unambiguous finite JSON", file=sys.stderr)
        return 1
    if not check_inclusion_consistency(*documents):
        print("INVALID: malformed input or inconsistent inclusion proof")
        return 1
    print("INDETERMINATE: local inclusion consistency matches an unauthenticated root")
    print("Event signatures, checkpoint identity, consistency and external anchors: NOT CHECKED")
    return 2


if __name__ == "__main__":
    sys.exit(main())
