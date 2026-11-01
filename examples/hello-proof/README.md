# Hello Proof Example

> **Scope and hardening — 1 November 2026:** This is a local mock example. It does not connect to Trillian or Tessera. The bundled event, canonical output and proof are preserved. The verifier checks a local hash relationship and proof geometry; a match is `INDETERMINATE` (exit 2) because the root and event are unauthenticated. See the [repository status](../../README.md).

## What is checked

1. Serialize an illustrative event using the existing example serializer.
2. Compute the domain-separated leaf hash `SHA-256(0x00 || serialized_bytes)`.
3. Reconstruct the root using the claimed tree size, leaf index and inclusion path.
4. Compare that root with the root supplied in the proof.

Tree sizes must be positive uint64 integers and leaf indices must be within the tree; booleans, floats and strings are rejected. Every digest must be exactly 32 bytes in canonical Base64. The proof must consume exactly the sibling nodes required for that tree shape, including odd-sized trees. Missing, extra or malformed paths are rejected. The CLI rejects duplicate JSON keys and non-finite numbers.

The tree-size and root claims still come from the untrusted input. Valid local geometry does not authenticate those claims or establish a real log's size.

## Files

| File | Description |
|------|-------------|
| `sample_event.json` | Illustrative event with a placeholder signature; not a VCP-conformant event |
| `canonical.json` | Unchanged bundled serializer output |
| `canonicalize.py` | Legacy local serializer with documented RFC 8785 differences |
| `mock_proof.py` | Generates a local single-leaf mock proof |
| `proof.json` | Unchanged bundled mock proof; not obtained from a transparency service |
| `verify.py` | Local consistency checker with input and path validation |
| `test.sh` | Runs regression tests without overwriting bundled evidence |

## Run the bundled check

No Trillian/Tessera server or third-party Python package is required.

```bash
python3 -B verify.py sample_event.json proof.json
# INDETERMINATE: local inclusion consistency matches an unauthenticated root
# Exit code: 2
```

| Result | CLI exit code | Meaning |
|--------|---------------|---------|
| `INVALID` | 1 | Malformed input, invalid proof geometry or a hash mismatch |
| `INDETERMINATE` | 2 | Local consistency matches, but authentication is unavailable |

There is no authenticated-success exit code. Callers that previously treated exit 0 as a verified log must handle this deliberate behavior change. `check_inclusion_consistency()` returns a boolean for the mathematical check only; `verify_inclusion_proof()` remains a compatibility alias with that same limited meaning. Neither function verifies signatures, log identity or conformance.

## Regression tests

From the repository root:

```bash
python3 -I -B -m unittest discover -s tests -v
# 21 tests; exits 0 if the regression suite passes
```

The suite uses an independent recursive oracle for all positions in trees of 1–33 leaves. It also exercises wrong targets, malformed hashes, insufficient/excess/reordered paths, invalid indices and sizes, duplicate keys, non-finite values, CLI result codes and a generated mock round trip. Temporary output does not replace the bundled files.

## Generate a separate mock proof

```bash
python3 -B mock_proof.py sample_event.json > proof.generated.json
python3 -B verify.py sample_event.json proof.generated.json
# Expected result: INDETERMINATE, exit 2
```

The generated timestamp is from the local clock. It is not an independently verified timestamp.

## Remaining limitations

- **Illustrative event:** the sample does not use the VCP v1.0 event structure. Its signature is a placeholder and its event ID uses a non-RFC UUID variant. Event structure, identifiers and signatures are not validated.
- **Canonicalization:** the finite-value format is unchanged and is not full RFC 8785 JCS. For example, `1e-6` is serialized as `1e-06`, and keys are sorted by Unicode code points rather than UTF-16 code units. Rejecting non-finite values does not resolve these differences.
- **Unauthenticated claims:** the root and tree metadata are supplied by the proof itself. Checkpoint signatures, event signatures, consistency proofs, external anchors and log identity are not checked.
- **Backend integration:** no Trillian/Tessera client or `submit_and_prove.py` is present. [ADAPTER_SPEC.md](../../ADAPTER_SPEC.md) describes proposed behavior, not a working integration.

The SHA-256 tree geometry follows the recursive definitions in [RFC 9162 §§2.1.1 and 2.1.3](https://www.rfc-editor.org/rfc/rfc9162.html#section-2.1). This local check is not a claim of complete CT, VCP or JCS conformance.
