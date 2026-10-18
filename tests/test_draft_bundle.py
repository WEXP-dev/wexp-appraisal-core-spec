import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "draft_bundle.py"
spec = importlib.util.spec_from_file_location("draft_bundle", MODULE)
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / "draft.xml").write_text('<rfc version="3" docName="draft-example-test-00"><front/></rfc>\n')
        (self.source / "draft.txt").write_text("Review rendering\n")
        self.descriptor = {
            "schema": bundle.SCHEMA, "candidate_id": "TEST-001", "purpose": "historical-pilot",
            "draft_name": "draft-example-test", "revision": "00",
            "source": {"repository": "example/draft", "repository_id": 1, "commit": "a" * 40},
            "toolchain": {"rendering": "fixture; not an xml2rfc run"},
            "artifacts": [{"path": "draft.xml", "role": "submission-xml"}, {"path": "draft.txt", "role": "review-txt"}]}
        self.target = self.root / "candidate"

    def freeze(self):
        return bundle.freeze(self.descriptor, self.source, self.target)

    def rewrite_manifest(self, edit):
        path = self.target / bundle.MANIFEST
        value = bundle.read_json(path)
        edit(value)
        path.write_bytes(bundle.json_bytes(value))

    def test_roundtrip_does_not_claim_readiness_or_authorization(self):
        result = self.freeze()
        self.assertEqual(result["artifact_count"], 2)
        self.assertEqual(result["technical_readiness"], "NOT_EVALUATED")
        self.assertFalse(result["submission_performed"])
        self.assertFalse(result["publication_verified"])
        self.assertEqual(result, bundle.verify(self.target, result["manifest_sha256"]))

    def test_omitted_submission_type_has_rfc_default(self):
        self.assertEqual(self.freeze()["xml_metadata"]["submissionType"], "IETF")

    def test_bytes_are_preserved_without_line_ending_normalization(self):
        content = b"review\r\nwith CRLF\r\n"
        (self.source / "draft.txt").write_bytes(content)
        self.freeze()
        self.assertEqual((self.target / "draft.txt").read_bytes(), content)

    def test_deterministic_bundle(self):
        first = self.freeze()
        second = bundle.freeze(self.descriptor, self.source, self.root / "second")
        self.assertEqual(first["manifest_sha256"], second["manifest_sha256"])

    def test_refuses_to_overwrite_frozen_candidate(self):
        self.freeze()
        before = (self.target / bundle.MANIFEST).read_bytes()
        with self.assertRaises(bundle.Invalid):
            self.freeze()
        self.assertEqual((self.target / bundle.MANIFEST).read_bytes(), before)

    def test_detects_content_mutation(self):
        self.freeze()
        (self.target / "draft.txt").write_text("changed\n")
        with self.assertRaises(bundle.Invalid):
            bundle.verify(self.target)

    def test_detects_rehashed_manifest_change_with_external_digest(self):
        result = self.freeze()
        self.rewrite_manifest(lambda m: m.update(candidate_id="SUBSTITUTED"))
        with self.assertRaises(bundle.Invalid):
            bundle.verify(self.target, result["manifest_sha256"])

    def test_rejects_missing_file(self):
        self.freeze()
        (self.target / "draft.txt").unlink()
        with self.assertRaises(bundle.Invalid):
            bundle.verify(self.target)

    def test_rejects_unlisted_file(self):
        self.freeze()
        (self.target / "later-evidence.json").write_text("{}")
        with self.assertRaises(bundle.Invalid):
            bundle.verify(self.target)

    def test_rejects_path_traversal_absolute_and_noncanonical_paths(self):
        for path in ["../secret", "/tmp/secret", "a//b", "./file", "a/../b", "a\\b", "C:secret", "a\nfile", ".git/config", "MANIFEST.json"]:
            with self.subTest(path=path), self.assertRaises(bundle.Invalid):
                bundle.safe_name(path)

    def test_rejects_artifact_symlink(self):
        (self.source / "draft.txt").unlink()
        (self.source / "draft.txt").symlink_to(self.source / "draft.xml")
        with self.assertRaises(bundle.Invalid):
            self.freeze()

    def test_rejects_directory_symlink(self):
        (self.source / "linked").symlink_to(self.source, target_is_directory=True)
        self.descriptor["artifacts"][1]["path"] = "linked/draft.txt"
        with self.assertRaises(bundle.Invalid):
            self.freeze()

    def test_rejects_duplicate_paths(self):
        self.descriptor["artifacts"].append(self.descriptor["artifacts"][0])
        with self.assertRaises(bundle.Invalid):
            self.freeze()

    def test_rejects_boolean_byte_count(self):
        self.freeze()
        self.rewrite_manifest(lambda m: m["artifacts"][0].update(bytes=True))
        with self.assertRaises(bundle.Invalid):
            bundle.verify(self.target)

    def test_rejects_boolean_repository_id(self):
        self.descriptor["source"]["repository_id"] = True
        with self.assertRaises(bundle.Invalid):
            self.freeze()

    def test_rejects_mutable_source_ref(self):
        self.descriptor["source"]["commit"] = "main"
        with self.assertRaises(bundle.Invalid):
            self.freeze()

    def test_rejects_wrong_document_identity(self):
        self.descriptor["revision"] = "01"
        with self.assertRaises(bundle.Invalid):
            self.freeze()

    def test_rejects_dtd_and_xinclude(self):
        samples = ['<!DOCTYPE rfc [<!ENTITY x "x">]><rfc version="3" docName="draft-example-test-00"/>', '<rfc version="3" docName="draft-example-test-00" xmlns:xi="http://www.w3.org/2001/XInclude"><xi:include href="secret"/></rfc>']
        for value in samples:
            with self.subTest(xml=value):
                (self.source / "draft.xml").write_text(value)
                with self.assertRaises(bundle.Invalid):
                    self.freeze()

    def test_rejects_self_declared_approval_field(self):
        self.descriptor["approved"] = True
        with self.assertRaises(bundle.Invalid):
            self.freeze()

    def test_rejects_duplicate_json_keys(self):
        p = self.root / "duplicate.json"
        p.write_text('{"candidate_id":"one","candidate_id":"two"}')
        with self.assertRaises(bundle.Invalid):
            bundle.read_json(p)

    def test_only_local_commands_are_exposed(self):
        with self.assertRaises(SystemExit) as raised:
            bundle.main(["submit"])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
