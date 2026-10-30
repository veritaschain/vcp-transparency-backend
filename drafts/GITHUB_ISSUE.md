# GitHub Issue Draft

> **Dated note — 25 October 2026:** This outreach draft was added to the repository on 5 January 2026. Whether and where it was posted is not recorded in this repository, so its text is left as written. Its description of IETF status is not accurate: `draft-kamimura-scitt-vcp` is an individual Internet-Draft (current revision `-05`), not adopted by the SCITT Working Group, and it is not "going through" or "progressing through" IETF as a SCITT profile. VCP v1.0 is superseded by VCP v1.2 (Released, tag `v1.2.0`). Do not reuse this text without correcting it.

**Repository:** `transparency-dev/trillian-tessera` (preferred) or `google/trillian`

**Title:** VCP: Proposal for Trillian/Tessera-backed transparency log adapter (non-normative)

---

## Summary

[VeritasChain Protocol (VCP)](https://veritaschain.org) is an open standard for cryptographic audit trails in algorithmic trading systems, currently progressing through IETF as a SCITT profile ([draft-kamimura-scitt-vcp](https://datatracker.ietf.org/doc/draft-kamimura-scitt-vcp/)).

We're building an adapter to use Trillian/Tessera as a transparency log backend for VCP events. This is **not** a modification to Trillian/Tessera — we're consuming the existing APIs to anchor financial audit data in a verifiable append-only structure.

**Use case:** Regulators and auditors can independently verify that trading algorithm logs have not been altered, without trusting the firm operating the log.

## Proposed Mapping

| VCP Concept | Trillian/Tessera Mapping |
|-------------|-------------------------|
| VCP event JSON | RFC 8785 canonicalized → `leaf_value` |
| Ed25519 signature | Verified in personality layer (not Trillian) |
| Inclusion proof | Standard Merkle inclusion proof |
| Evidence package | `leaf_data` + `inclusion_proof` + `signed_tree_head` |

**Adapter spec:** https://github.com/veritaschain/vcp-transparency-backend/blob/main/ADAPTER_SPEC.md

## Questions

We'd appreciate guidance on three design decisions:

### 1. Tessera vs Trillian v1

For a new deployment starting now, is Tessera stable enough for production, or should we implement Trillian v1 first and plan migration?

### 2. Identity Hash Strategy

VCP events are timestamped audit records. Should the identity hash:
- **Include timestamp** → Every submission is unique (no dedup)
- **Exclude timestamp** → Same event content deduplicates (idempotent retries)

Which pattern is more common for append-only audit logs?

### 3. Proof Packaging Minimum

For portable verification, what's the minimum required set?
- `root_hash` + `inclusion_proof` + `tree_size` (sufficient?)
- Or is `checkpoint_signature` expected by verifiers?

---

We've introduced ourselves in Slack ([link to thread]) and are happy to iterate based on feedback. If there's a better place to discuss integration patterns, please let us know.

**Contact:** technical@veritaschain.org  
**Repo:** https://github.com/veritaschain/vcp-transparency-backend
