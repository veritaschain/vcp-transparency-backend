# Hello Proof Example

Minimal end-to-end demonstration of VCP → Transparency Log → Proof → Verification.

## Goal

Prove the adapter works by:
1. Canonicalizing a VCP event (RFC 8785)
2. Submitting to a local Trillian/Tessera instance
3. Retrieving an inclusion proof
4. Verifying the proof client-side

## Files

| File | Description |
|------|-------------|
| `sample_event.json` | Example VCP event (order.new) |
| `canonical.json` | RFC 8785 canonicalized output |
| `proof.json` | Retrieved inclusion proof + tree head |
| `verify.py` | Client-side verification script |

## Prerequisites

### Option A: Tessera (Recommended)

```bash
# Clone and build Tessera
git clone https://github.com/transparency-dev/trillian-tessera
cd trillian-tessera
go build ./cmd/example-posix/

# Start local server (uses filesystem storage)
./example-posix --storage_path=/tmp/tessera-vcp --listen=:8080
```

### Option B: Trillian v1

```bash
# Start Trillian with Docker Compose
git clone https://github.com/google/trillian
cd trillian
docker-compose up -d

# Create a log tree
go run github.com/google/trillian/cmd/createtree \
  --admin_server=localhost:8090 \
  --tree_type=LOG
```

## Running the Example

```bash
# 1. Canonicalize the event
python3 canonicalize.py sample_event.json > canonical.json

# 2. Submit to transparency log and get proof
python3 submit_and_prove.py canonical.json > proof.json

# 3. Verify the proof
python3 verify.py sample_event.json proof.json
# Expected output: "✓ Inclusion proof valid"
```

## Expected Output: proof.json

```json
{
  "transparency_anchor": {
    "backend_type": "tessera",
    "log_id": "vcp-hello-proof",
    "leaf_index": 0,
    "tree_size": 1,
    "root_hash": "base64...",
    "timestamp_nanos": 1735689600000000000,
    "inclusion_proof": {
      "hashes": []
    }
  },
  "leaf_hash": "base64...",
  "canonical_bytes_sha256": "base64..."
}
```

Note: For a single-leaf tree, the inclusion proof is empty (leaf hash = root hash).

## Verification Logic

```python
def verify_inclusion(event_json, proof):
    # 1. Re-canonicalize
    canonical = canonicalize(event_json)
    
    # 2. Compute leaf hash (RFC 6962)
    leaf_hash = sha256(b'\x00' + canonical)
    
    # 3. Walk inclusion proof to root
    computed_root = leaf_hash
    for i, sibling in enumerate(proof['inclusion_proof']['hashes']):
        if proof['leaf_index'] & (1 << i):
            computed_root = sha256(b'\x01' + sibling + computed_root)
        else:
            computed_root = sha256(b'\x01' + computed_root + sibling)
    
    # 4. Compare with claimed root
    return computed_root == proof['root_hash']
```

## Next Steps

After this works:
1. Add Ed25519 signature verification
2. Add consistency proof checking
3. Package as reusable library
