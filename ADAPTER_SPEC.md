# VCP Transparency Backend Adapter Specification

**Version:** 0.1-draft  
**Status:** Seeking community feedback  
**Date:** 2026-01-05

---

## 1. Inputs

**VCP Event JSON** — Any VCP v1.0 compliant event structure:

```json
{
  "event_id": "01941234-5678-7abc-def0-123456789abc",
  "event_type": "order.new",
  "timestamp": "2026-01-05T12:00:00.123456789Z",
  "payload": { /* event-specific data */ },
  "signature": "base64..."
}
```

The adapter accepts events that have already been signed per VCP specification (Ed25519).

---

## 2. Canonicalization

**Method:** RFC 8785 JSON Canonicalization Scheme (JCS)

```
Input:  VCP event JSON (any whitespace/ordering)
Output: Deterministic UTF-8 bytes (no trailing newline)
```

**Process:**
1. Parse JSON into language-native structure
2. Apply RFC 8785 serialization rules:
   - Object keys sorted lexicographically (UTF-16 code units)
   - No whitespace between tokens
   - Numbers in shortest form (no trailing zeros)
   - Strings with minimal escaping
3. Encode as UTF-8 bytes

**Implementation:** Use `json-canonicalize` (Python), `canonicalize` (Go), or equivalent RFC 8785 library.

---

## 3. Leaf Mapping

| Field | Value | Notes |
|-------|-------|-------|
| `leaf_value` | `canonical_bytes` | RFC 8785 output, hashed as `SHA-256(0x00 \|\| leaf_value)` per RFC 6962 |
| `extra_data` | Original JSON (optional) | For retrieval convenience; not part of Merkle commitment |

**Merkle leaf hash** (computed by backend):
```
merkle_leaf_hash = SHA-256(0x00 || canonical_bytes)
```

---

## 4. Identity Hash Strategy

The identity hash determines deduplication behavior. Two candidate approaches:

### Option A: Full canonical hash (no dedup)
```
identity_hash = SHA-256(canonical_bytes)
```
- Every submission creates a new leaf
- Same event resubmitted = duplicate entries
- Simpler, matches append-only audit semantics

### Option B: Timestamp-excluded canonical hash (dedup enabled)
```
identity_hash = SHA-256(canonicalize(event - timestamp))
```
- Same event content with different timestamps = single entry
- Resubmission returns original leaf index
- Useful for idempotent retry logic

**Seeking feedback:** Which approach better serves transparency log use cases for financial audit trails?

---

## 5. Proof Packaging

The adapter retrieves and packages proofs into VCP-compatible evidence structures.

### Minimum Required Fields

```json
{
  "transparency_anchor": {
    "backend_type": "tessera | trillian",
    "log_id": "string (log identifier)",
    "leaf_index": 12345,
    "tree_size": 67890,
    "root_hash": "base64 (32 bytes)",
    "timestamp_nanos": 1735689600000000000,
    "inclusion_proof": {
      "hashes": ["base64...", "base64..."]
    }
  }
}
```

### Optional Extensions

| Field | Purpose |
|-------|---------|
| `consistency_proof` | Proves append-only property between two tree sizes |
| `checkpoint_signature` | Log operator signature over tree head |
| `witness_cosignatures` | Third-party witness signatures (Tessera witness network) |

### Verification Flow

1. Re-canonicalize event → compute expected `leaf_hash`
2. Walk inclusion proof from `leaf_hash` to `root_hash`
3. Compare computed root with `root_hash` in anchor
4. (Optional) Verify checkpoint signature
5. (Optional) Check consistency with previously seen tree head

---

## 6. Backend Targets

### Tessera (Recommended)

| Aspect | Detail |
|--------|--------|
| API | Library-based (embedded), HTTP tile serving |
| Leaf submission | `tessera.Add()` — synchronous, returns index immediately |
| Proof retrieval | Tile-based, CDN-cacheable |
| Storage | GCS, S3, MySQL, POSIX filesystem |
| Status | Active development, expected stable Q1 2025 |

### Trillian v1 (Maintenance)

| Aspect | Detail |
|--------|--------|
| API | gRPC (`TrillianLog` service) |
| Leaf submission | `QueueLeaf` — async, requires signer to sequence |
| Proof retrieval | `GetInclusionProof`, `GetInclusionProofByHash` |
| Storage | MySQL/MariaDB only |
| Status | Stable, feature-frozen, maintenance only |

---

## 7. Open Questions for Community

1. **Tessera production readiness:** What is the current recommended path for new deployments? Any blockers for production use?

2. **Identity hash best practice:** For timestamped event logs where each event is unique, should we enable deduplication or treat every submission as distinct?

3. **Proof packaging minimum:** What fields are essential for portable verification? Is `checkpoint_signature` expected, or is `root_hash + inclusion_proof` sufficient for most verifiers?

---

## References

- [RFC 8785: JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785)
- [RFC 6962: Certificate Transparency](https://www.rfc-editor.org/rfc/rfc6962)
- [Trillian API Documentation](https://github.com/google/trillian/blob/master/docs/api.md)
- [Tessera Repository](https://github.com/transparency-dev/trillian-tessera)
- [VCP Specification v1.0](https://github.com/veritaschain/vcp-spec)
