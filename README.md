> **Status correction — 25 October 2026**
>
> - This is first-party draft code and specification by VeritasChain Co., Ltd., which operates the VeritasChain Standards Organization (VSO). It targets VCP v1.0, which is superseded by VCP v1.2 (Released, tag `v1.2.0`).
> - Conformance to any VCP tier, or to VAP, has not been independently established. There are zero external implementations of VAP or any of its profiles, including VCP. Not certified: VSO does not issue certifications itself, and the only registered Conformity Assessment Body (VeritasChain Co., Ltd.) is not independent of the scheme owner (VAP v1.2 ERRATA E-2026-10-21).
> - `draft-kamimura-scitt-vcp` is an individual Internet-Draft (current revision `-05`), not adopted by the IETF SCITT Working Group or any other IETF working group.
> - Known limitations: the repository contains no Trillian or Tessera client code. `examples/hello-proof` verifies a mock single-leaf proof (`mock_proof.py`); the `submit_and_prove.py` script named in its README is not in the repository.

# vcp-transparency-backend

Transparency log backend adapter for [VeritasChain Protocol (VCP)](https://veritaschain.org) — enabling cryptographically verifiable audit trails for algorithmic trading systems.

## What This Is

This repository provides an adapter layer that connects VCP event streams to transparency log backends (Trillian, Tessera). The adapter:

- Canonicalizes VCP evidence using RFC 8785 (JSON Canonicalization Scheme)
- Submits canonicalized data as Merkle tree leaves
- Retrieves and packages inclusion/consistency proofs into VCP evidence structures
- Enables third-party verification without trusting the log operator

**Use case:** Financial regulators, auditors, and counterparties can independently verify that trading algorithm audit logs have not been altered after the fact.

## Non-Goals

This project does **not**:

- Replace or compete with Trillian/Tessera — we consume their APIs as a backend
- Implement a new transparency log protocol — we use established cryptographic primitives
- Require modifications to VCP core specification — this is an optional external anchoring mechanism
- Provide a hosted service — this is reference implementation code

VCP is an audit trail format; Trillian/Tessera provides the append-only data structure. This adapter bridges them.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VCP Personality Layer                        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────────┐ │
│  │ VCP Event    │──▶│ RFC 8785     │──▶│ leaf_value =             │ │
│  │ (JSON)       │   │ Canonicalize │   │ canonical_bytes          │ │
│  └──────────────┘   └──────────────┘   └──────────────────────────┘ │
│                                                      │              │
│  ┌──────────────┐   ┌──────────────┐                 ▼              │
│  │ Ed25519      │   │ Identity     │   ┌──────────────────────────┐ │
│  │ Signing      │   │ Hash Logic   │   │ QueueLeaf / AddEntry     │ │
│  └──────────────┘   └──────────────┘   └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Trillian Log Server  /  Tessera                        │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Merkle Tree Operations (SHA-256, RFC 6962 hashing strategy)     ││
│  │ • Append leaves                                                 ││
│  │ • Generate inclusion proofs                                     ││
│  │ • Generate consistency proofs                                   ││
│  │ • Sign tree heads                                               ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Storage Backend                             │
│                    MySQL / MariaDB / GCS / S3                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Component | Approach |
|-----------|----------|
| **Canonicalization** | RFC 8785 JCS applied before submission |
| **Signing** | Ed25519 in personality layer (Trillian removed native signing) |
| **Leaf value** | Canonicalized VCP event bytes |
| **Identity hash** | TBD — seeking community input on deduplication strategy |
| **Proof packaging** | SignedLogRoot + inclusion proof wrapped in VCP evidence |

## Output: VCP Evidence with Transparency Proof

The adapter produces VCP evidence packages containing:

```json
{
  "vcp_version": "1.0",
  "event": { /* original VCP event */ },
  "transparency_proof": {
    "backend": "tessera",
    "log_id": "example-log-2025",
    "leaf_index": 12345,
    "tree_size": 67890,
    "root_hash": "base64...",
    "inclusion_proof": ["base64...", "base64..."],
    "timestamp_nanos": 1735689600000000000
  },
  "signatures": {
    "event_signature": "base64... (Ed25519)",
    "log_checkpoint_signature": "base64..."
  }
}
```

Verifiers can:
1. Re-canonicalize the event and confirm leaf hash
2. Validate inclusion proof against root hash
3. Verify checkpoint signature from log operator
4. Optionally check consistency with previous tree heads

## Backend Targets

| Backend | Status | Notes |
|---------|--------|-------|
| **Tessera** | Recommended | Actively developed, synchronous leaf indexing, CDN-cacheable |
| **Trillian v1** | Supported | Stable but maintenance-only, async sequencing |

We recommend Tessera for new deployments. Trillian v1 support is provided for environments with existing infrastructure.

## Status

**🚧 Draft — Seeking Feedback**

This specification is in early development. We are seeking input from the transparency.dev community on:

1. **Tessera readiness** — Current production status and migration path
2. **Leaf identity hash** — Best practices for deduplication in timestamped event logs
3. **Proof packaging** — Minimum required fields for portable verification

See [ADAPTER_SPEC.md](./ADAPTER_SPEC.md) for detailed technical mapping.

## Related Resources

- [VCP Specification](https://github.com/veritaschain/vcp-spec) (this adapter was written against v1.0; current release v1.2)
- [Individual Internet-Draft: draft-kamimura-scitt-vcp](https://datatracker.ietf.org/doc/draft-kamimura-scitt-vcp/) (not WG-adopted)
- [Trillian](https://github.com/google/trillian)
- [Tessera](https://github.com/transparency-dev/trillian-tessera)
- [transparency.dev](https://transparency.dev)

## Contributing

We welcome feedback via GitHub issues. For design discussions, please join the [transparency.dev Slack](https://transparency.dev/slack/).

## License

Apache 2.0

## Contact

- Standards: standards@veritaschain.org
- Technical: technical@veritaschain.org
- GitHub: https://github.com/veritaschain
