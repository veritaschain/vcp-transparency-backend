"""Boundary and end-to-end regressions for the local proof example."""

import base64
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "hello-proof"
sys.path.insert(0, str(EXAMPLE))
spec = importlib.util.spec_from_file_location("local_proof_verifier", EXAMPLE / "verify.py")
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


def h(data):
    return hashlib.sha256(data).digest()


def root_for(entries):
    if len(entries) == 1:
        return h(b"\x00" + entries[0])
    split = 1
    while split * 2 < len(entries):
        split *= 2
    return h(b"\x01" + root_for(entries[:split]) + root_for(entries[split:]))


def path_for(entries, index):
    if len(entries) == 1:
        return []
    split = 1
    while split * 2 < len(entries):
        split *= 2
    if index < split:
        return path_for(entries[:split], index) + [root_for(entries[split:])]
    return path_for(entries[split:], index - split) + [root_for(entries[:split])]


def b64(data):
    return base64.b64encode(data).decode("ascii")


def proof_for(entries, index):
    return {
        "tree_size": len(entries),
        "leaf_index": index,
        "root_hash": b64(root_for(entries)),
        "inclusion_proof": {"hashes": [b64(x) for x in path_for(entries, index)]},
    }


class ProofTests(unittest.TestCase):
    def setUp(self):
        self.event = {"sequence": 0}
        self.proof = proof_for([b'{"sequence":0}'], 0)

    def test_recursive_oracle_all_positions_one_to_33(self):
        for size in range(1, 34):
            entries = [b'{"sequence":' + str(i).encode("ascii") + b"}" for i in range(size)]
            expected = root_for(entries)
            for index in range(size):
                with self.subTest(size=size, index=index):
                    path = path_for(entries, index)
                    self.assertEqual(
                        verify.compute_root_from_proof(h(b"\x00" + entries[index]), index, size, path),
                        expected,
                    )
                    proof = proof_for(entries, index)
                    self.assertTrue(verify.check_inclusion_consistency({"sequence": index}, proof))
                    self.assertFalse(verify.check_inclusion_consistency({"sequence": -1}, proof))

    def test_original_three_leaf_last_position_regression(self):
        entries = [b"a", b"b", b"c"]
        self.assertEqual(
            verify.compute_root_from_proof(h(b"\x00c"), 2, 3, path_for(entries, 2)),
            root_for(entries),
        )

    def test_out_of_range_single_leaf_is_rejected(self):
        for index in [-1, 1, 999]:
            with self.subTest(index=index):
                self.proof["leaf_index"] = index
                self.assertFalse(verify.check_inclusion_consistency(self.event, self.proof))

    def test_empty_path_for_larger_tree_is_rejected(self):
        self.proof["tree_size"] = 7
        self.assertFalse(verify.check_inclusion_consistency(self.event, self.proof))

    def test_integer_bounds_and_types(self):
        for field, values in {
            "tree_size": [0, -1, True, False, 1.0, "1", None, 2**64],
            "leaf_index": [-1, True, False, 0.0, "0", None, 2**64],
        }.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    proof = copy.deepcopy(self.proof)
                    proof[field] = value
                    self.assertFalse(verify.check_inclusion_consistency(self.event, proof))

    def test_short_and_extra_paths(self):
        entries = [b'{"sequence":' + str(i).encode() + b"}" for i in range(7)]
        for index in range(7):
            proof = proof_for(entries, index)
            for nodes in [proof["inclusion_proof"]["hashes"][:-1],
                          proof["inclusion_proof"]["hashes"] + [b64(b"x" * 32)]]:
                with self.subTest(index=index, count=len(nodes)):
                    proof_copy = copy.deepcopy(proof)
                    proof_copy["inclusion_proof"]["hashes"] = nodes
                    self.assertFalse(verify.check_inclusion_consistency({"sequence": index}, proof_copy))

    def test_modified_and_reordered_siblings(self):
        entries = [b'{"sequence":' + str(i).encode() + b"}" for i in range(7)]
        proof = proof_for(entries, 0)
        nodes = proof["inclusion_proof"]["hashes"]
        for replacement in [list(reversed(nodes)), [b64(b"x" * 32)] + nodes[1:]]:
            proof["inclusion_proof"]["hashes"] = replacement
            self.assertFalse(verify.check_inclusion_consistency(self.event, proof))

    def test_wrong_root_and_target(self):
        self.assertFalse(verify.check_inclusion_consistency({"sequence": 1}, self.proof))
        self.proof["root_hash"] = b64(b"x" * 32)
        self.assertFalse(verify.check_inclusion_consistency(self.event, self.proof))

    def test_digest_encoding_and_lengths(self):
        for value in ["", "!", b64(b"x" * 31), b64(b"x" * 33),
                      self.proof["root_hash"] + "\n", None, 7]:
            with self.subTest(value=value):
                proof = copy.deepcopy(self.proof)
                proof["root_hash"] = value
                self.assertFalse(verify.check_inclusion_consistency(self.event, proof))
        # Same decoded bytes with nonzero padding bits must not be accepted.
        proof = copy.deepcopy(self.proof)
        encoded = proof["root_hash"]
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        proof["root_hash"] = encoded[:-2] + alphabet[alphabet.index(encoded[-2]) + 1] + "="
        self.assertEqual(base64.b64decode(encoded), base64.b64decode(proof["root_hash"]))
        self.assertFalse(verify.check_inclusion_consistency(self.event, proof))

    def test_missing_or_malformed_structures(self):
        for proof in [None, [], {}, {"transparency_anchor": None},
                      {**self.proof, "inclusion_proof": {}},
                      {**self.proof, "inclusion_proof": {"hashes": "not-a-list"}},
                      {**self.proof, "inclusion_proof": {"hashes": [b64(b"x" * 32)] * 65}}]:
            with self.subTest(proof=proof):
                self.assertFalse(verify.check_inclusion_consistency(self.event, proof))
        self.assertFalse(verify.check_inclusion_consistency([], self.proof))

    def test_missing_required_fields(self):
        for field in self.proof:
            proof = copy.deepcopy(self.proof)
            del proof[field]
            self.assertFalse(verify.check_inclusion_consistency(self.event, proof))

    def test_non_finite_and_invalid_json_values(self):
        for value in [math.nan, math.inf, -math.inf, {1: "non-string-key"}, "\ud800"]:
            with self.subTest(value=repr(value)):
                self.assertFalse(verify.check_inclusion_consistency({"sequence": value}, self.proof))

    def test_raw_helper_rejects_invalid_node_bytes(self):
        for leaf, nodes in [(b"x", []), ("x" * 32, []), (b"x" * 32, None)]:
            with self.subTest(leaf=leaf, nodes=nodes):
                with self.assertRaises(ValueError):
                    verify.compute_root_from_proof(leaf, 0, 1, nodes)
        with self.assertRaises(ValueError):
            verify.compute_root_from_proof(b"x" * 32, 0, 2, [b"short"])

    def test_wrapped_proof_and_compatibility_alias(self):
        self.assertTrue(verify.check_inclusion_consistency(self.event, {"transparency_anchor": self.proof}))
        self.assertTrue(verify.verify_inclusion_proof(self.event, self.proof))

    def test_bundled_sample_local_relationship_is_preserved(self):
        event = json.loads((EXAMPLE / "sample_event.json").read_text())
        proof = json.loads((EXAMPLE / "proof.json").read_text())
        self.assertTrue(verify.check_inclusion_consistency(event, proof))
        self.assertEqual(verify.canonicalize(event), (EXAMPLE / "canonical.json").read_text().rstrip("\n"))


class CliTests(unittest.TestCase):
    def run_cli(self, event_text, proof_text):
        with tempfile.TemporaryDirectory() as directory:
            event = Path(directory) / "event.json"
            proof = Path(directory) / "proof.json"
            event.write_text(event_text)
            proof.write_text(proof_text)
            return subprocess.run(
                [sys.executable, "-B", str(EXAMPLE / "verify.py"), str(event), str(proof)],
                text=True, capture_output=True, timeout=10,
            )

    def test_bundled_sample_is_indeterminate_exit_2(self):
        result = self.run_cli(
            (EXAMPLE / "sample_event.json").read_text(),
            (EXAMPLE / "proof.json").read_text(),
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("INDETERMINATE", result.stdout)
        self.assertIn("NOT CHECKED", result.stdout)

    def test_json_and_shape_errors_are_invalid(self):
        proof = json.dumps(proof_for([b'{"sequence":0}'], 0))
        for event in ['{"sequence":0,"sequence":0}', '{"sequence":NaN}', '{"sequence":Infinity}',
                      '{"sequence":1e999}', "{", "[]"]:
            with self.subTest(event=event):
                result = self.run_cli(event, proof)
                self.assertEqual(result.returncode, 1)
                self.assertIn("INVALID", result.stdout + result.stderr)

    def test_duplicate_proof_keys_are_invalid(self):
        proof = json.dumps(proof_for([b'{"sequence":0}'], 0))
        proof = proof.replace('"tree_size": 1', '"tree_size": 1, "tree_size": 1')
        result = self.run_cli('{"sequence":0}', proof)
        self.assertEqual(result.returncode, 1)
        self.assertIn("INVALID", result.stdout + result.stderr)

    def test_overflow_in_unused_proof_metadata_is_invalid(self):
        proof = (EXAMPLE / "proof.json").read_text()
        proof = proof.replace("{", '{"ignored_metadata":1e999,', 1)
        result = self.run_cli((EXAMPLE / "sample_event.json").read_text(), proof)
        self.assertEqual(result.returncode, 1)
        self.assertIn("INVALID", result.stdout + result.stderr)

    def test_mismatch_and_missing_files_are_invalid(self):
        result = self.run_cli('{"sequence":1}', json.dumps(proof_for([b'{"sequence":0}'], 0)))
        self.assertEqual(result.returncode, 1)
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-B", str(EXAMPLE / "verify.py"),
                 str(Path(directory) / "absent"), str(Path(directory) / "also-absent")],
                text=True, capture_output=True, timeout=10,
            )
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)

    def test_generated_mock_round_trip_uses_temporary_files(self):
        with tempfile.TemporaryDirectory() as directory:
            before = {name: (EXAMPLE / name).read_bytes()
                      for name in ["sample_event.json", "canonical.json", "proof.json"]}
            result = subprocess.run(
                [sys.executable, "-B", str(EXAMPLE / "mock_proof.py"), str(EXAMPLE / "sample_event.json")],
                text=True, capture_output=True, check=True, timeout=10,
            )
            proof = Path(directory) / "generated.json"
            proof.write_text(result.stdout)
            result = subprocess.run(
                [sys.executable, "-B", str(EXAMPLE / "verify.py"),
                 str(EXAMPLE / "sample_event.json"), str(proof)],
                text=True, capture_output=True, timeout=10,
            )
            self.assertEqual(result.returncode, 2, result.stderr)
            for name, data in before.items():
                self.assertEqual((EXAMPLE / name).read_bytes(), data)


if __name__ == "__main__":
    unittest.main()
