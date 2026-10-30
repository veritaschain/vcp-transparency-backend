> **Status correction — 25 October 2026 (verification scope clarified 30 October 2026)**
>
> - This is a first-party draft adapter design and local mock example by VeritasChain Co., Ltd., which operates the VeritasChain Standards Organization (VSO). It was drafted with VCP v1.0 as its target; that version is superseded by VCP v1.2 (Released, tag `v1.2.0`).
> - Conformance to any VCP tier, or to VAP, has not been independently established. VSO's published disclosure dated 25 October 2026 reports zero external implementations of VAP or any of its profiles, including VCP. Not certified: VSO does not issue certifications itself, and the only registered Conformity Assessment Body (VeritasChain Co., Ltd.) is not independent of the scheme owner (VAP v1.2 ERRATA E-2026-10-21).
> - `draft-kamimura-scitt-vcp` is an individual Internet-Draft (current revision `-05`), not adopted by the IETF SCITT Working Group or any other IETF working group.
> - Implementation scope: the repository contains no Trillian or Tessera client code. `examples/hello-proof` generates and checks a local mock single-leaf proof. Backend submission, proof retrieval, checkpoint-signature verification and consistency checking described below are proposed behavior, not implemented capabilities. `submit_and_prove.py` is absent.
> - Verification limits: the sample uses an illustrative event format, a placeholder signature and a non-RFC UUID variant. The example does not validate VCP event structure or signatures. Its canonicalizer differs from RFC 8785 in number formatting and UTF-16 key ordering and does not reject NaN or Infinity. Its proof verifier has incomplete bounds checks and does not correctly verify all RFC 6962 tree shapes. A successful run demonstrates the bundled local hash relationship; it does not authenticate a log, establish backend integration or demonstrate VCP/RFC conformance.

# vcp-transparency-backend

Draft design for a transparency-log backend adapter for [VeritasChain Protocol (VCP)](https://veritaschain.org), with a local mock inclusion-proof example.

## Proposed Adapter

This repository sketches an adapter between VCP event streams and transparency log backends (Trillian, Tessera). The proposed adapter would:

- Canonicalize VCP evidence using RFC 8785 (JSON Canonicalization Scheme)
- Submit canonicalized data as Merkle tree leaves
- Retrieve and package inclusion/consistency proofs into proposed evidence structures
- Package evidence for third-party verification

**Intended use case:** Evidence for regulators, auditors and counterparties assessing the integrity of trading audit records. The bundled mock does not demonstrate this use case or authenticate an external log checkpoint.

## Non-Goals

This project does **not**:

- Replace or compete with Trillian/Tessera — their APIs are proposed backend interfaces
- Implement a new transparency log protocol — we use established cryptographic primitives
- Require modifications to VCP core specification — this is an optional external anchoring mechanism
- Provide a hosted service — this repository contains a draft design and local example

The proposed adapter would connect VCP event records to an append-only transparency log. That integration is not implemented here.

## Proposed Architecture

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

### Proposed Design Choices

| Component | Approach |
|-----------|----------|
| **Canonicalization** | RFC 8785 JCS applied before submission |
| **Signing** | Ed25519 in the proposed personality layer; not implemented here |
| **Leaf value** | Canonicalized VCP event bytes |
| **Identity hash** | TBD — seeking community input on deduplication strategy |
| **Proof packaging** | SignedLogRoot + inclusion proof wrapped in VCP evidence |

## Proposed Output Format

A future adapter could package event data and transparency proofs in the illustrative format below. Its mapping to VCP has not been validated:

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

The intended verification flow is shown below; the local example does not implement it in full:
1. Re-canonicalize the event and confirm leaf hash
2. Validate inclusion proof against root hash
3. Verify checkpoint signature from log operator
4. Optionally check consistency with previous tree heads

## Backend Targets

| Backend | Adapter status in this repository |
|---------|-----------------------------------|
| **Tessera** | Proposed target; no client integration implemented |
| **Trillian v1** | Proposed target; no client integration implemented |

Consult the upstream projects for current APIs and deployment guidance. This repository does not establish backend compatibility or production readiness.

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
