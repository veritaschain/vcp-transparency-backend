# Hello Proof Example

> **Status correction — 30 October 2026:** This is a local mock single-leaf proof example. It does not connect to Trillian or Tessera. The bundled event and proof are preserved; a successful run checks their local hash relationship, not log authenticity or VCP/RFC conformance. See the [repository status](../../README.md).

## Goal

Demonstrate the following local calculation:

1. Serialize an illustrative event using the bundled serializer.
2. Compute the domain-separated leaf hash `SHA-256(0x00 || serialized_bytes)`.
3. Compare it with the root supplied in the bundled single-leaf mock proof.

For this mock, `tree_size` is 1, `leaf_index` is 0 and the inclusion path is empty. No backend submission, proof retrieval or independent checkpoint is involved.

## Files

| File | Description |
|------|-------------|
| `sample_event.json` | Illustrative event with a placeholder signature; not a VCP-conformant event |
| `canonical.json` | Bundled serializer output for that sample |
| `canonicalize.py` | Local serializer with known RFC 8785 differences |
| `mock_proof.py` | Generates a local single-leaf mock proof |
| `proof.json` | Bundled mock proof; not a proof retrieved from a transparency service |
| `verify.py` | Local hash comparison and incomplete general inclusion-proof logic |

## Run the Bundled Check

No Trillian/Tessera server or third-party Python package is required for this local example.

```bash
python3 -B verify.py sample_event.json proof.json
# Expected output begins: "✓ Inclusion proof valid"
```

The printed success message describes this local calculation. It does not establish event authenticity, a log operator's identity, an external timestamp, append-only behavior or VCP conformance.

## Generate a Separate Mock Proof

To generate a new local mock proof without overwriting the bundled `proof.json`:

```bash
python3 -B mock_proof.py sample_event.json > proof.generated.json
python3 -B verify.py sample_event.json proof.generated.json
```

`timestamp_nanos` in the generated proof comes from the local clock. It is not an independently verified timestamp.

## Known Limitations

- **Illustrative event:** the sample does not use the VCP v1.0 event structure. Its signature is a placeholder and its event ID uses a non-RFC UUID variant. The verifier does not validate VCP event structure, event identifiers or signatures.
- **Canonicalization:** `canonicalize.py` is not fully RFC 8785-conformant. For example, it serializes `1e-6` as `1e-06` instead of `0.000001`, sorts keys by Unicode code points rather than UTF-16 code units, and does not reject NaN or Infinity.
- **Inclusion proofs:** `verify.py` is not a general-purpose RFC 6962/9162 verifier. It accepts an out-of-range leaf index in a single-leaf tree and fails a valid proof for the last leaf of a three-leaf RFC 6962 tree.
- **Unauthenticated root:** the root is supplied in the proof being checked. The example does not verify checkpoint signatures, consistency proofs or external anchors.

These limitations are documented without changing the implementation or the bundled sample, canonical output or proof.

## Proposed Backend Work

Backend integration remains unimplemented. The earlier workflow referring to `submit_and_prove.py` cannot be run because that script is not present. See [ADAPTER_SPEC.md](../../ADAPTER_SPEC.md) for the proposed design; consult upstream projects for their current APIs and deployment instructions.

Event-signature verification, checkpoint authentication and consistency checking remain future work.
