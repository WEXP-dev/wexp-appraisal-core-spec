"""Exact-package transport tests. All positive POST paths are mocked."""
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support
import datatracker_submit as dts
import draft_bundle as bundle
import submit_publication as transport

IDENTITY = "draft-example-wexp-core-02"


class TransportTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.xml_bytes = support.MINIMAL_XML.format(identity=IDENTITY).replace(
            "<rfc ", '<rfc version="3" ').encode()
        (self.source / "draft.xml").write_bytes(self.xml_bytes)
        (self.source / "draft.txt").write_bytes(b"fixture review\r\n")
        descriptor = {
            "schema": bundle.SCHEMA, "candidate_id": "TEST-02-001",
            "purpose": "publication-candidate", "draft_name": IDENTITY[:-3], "revision": "02",
            "source": {"repository": "example/fixture", "repository_id": 1, "commit": "a" * 40},
            "toolchain": {"fixture": "synthetic; not a real publication review"},
            "artifacts": [{"path": "draft.xml", "role": "submission-xml"},
                          {"path": "draft.txt", "role": "review-txt"}],
        }
        self.frozen = self.root / "frozen"
        self.manifest_hash = bundle.freeze(descriptor, self.source, self.frozen)["manifest_sha256"]
        now = datetime.now(timezone.utc)
        self.decision = {
            "schema": "ietf-draft-author-decision-v1", "status": "AUTHOR_APPROVED",
            "candidate_id": "TEST-02-001", "manifest_sha256": self.manifest_hash,
            "author": "Synthetic fixture", "decision_source": "fixture only",
            "decision_source_sha256": "b" * 64, "decided_at": (now - timedelta(minutes=5)).isoformat(),
            "authorized_actions": ["datatracker-submit"], "destinations": [dts.DATATRACKER_SUBMISSION_URL],
            "submission": {"user": "fixture@example.com", "replaces": []},
        }
        self.review = {
            "schema": "ietf-draft-review-record-v1", "status": "REVIEW_COMPLETE",
            "candidate_id": "TEST-02-001", "manifest_sha256": self.manifest_hash,
            "reviewer": "Synthetic fixture", "reviewed_at": (now - timedelta(minutes=10)).isoformat(),
            "preflight_valid_until": (now + timedelta(hours=1)).isoformat(),
            "technical_conclusion": "READY_FOR_SUBMISSION",
            "checks": [{"id": x, "result": "PASS", "evidence": ["synthetic-fixture-only"]}
                       for x in sorted(transport.CHECKS)],
            "finding_dispositions": [], "engineering_backlog": ["Unfinished implementation; no such claim in draft"],
        }
        self.decision_path, self.review_path = self.root / "decision.json", self.root / "review.json"
        self.state = self.root / "attempts"
        self.state.mkdir()
        self.save_records()
        blocker = mock.patch("socket.socket", side_effect=AssertionError("NETWORK FORBIDDEN IN TEST"))
        blocker.start()
        self.addCleanup(blocker.stop)

    def save_records(self):
        self.decision_path.write_bytes(bundle.json_bytes(self.decision))
        self.review_path.write_bytes(bundle.json_bytes(self.review))

    def arguments(self, *extra):
        return [
            "--bundle-root", str(self.frozen), "--identity", IDENTITY,
            "--expected-manifest-sha256", self.manifest_hash,
            "--author-decision", str(self.decision_path),
            "--expected-decision-sha256", hashlib.sha256(self.decision_path.read_bytes()).hexdigest(),
            "--review-record", str(self.review_path),
            "--expected-review-sha256", hashlib.sha256(self.review_path.read_bytes()).hexdigest(),
            "--user", "fixture@example.com", *extra,
        ]

    def run_client(self, *extra, sender=None):
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            if sender is None:
                code = transport.main(self.arguments(*extra))
            else:
                with mock.patch.object(dts, "submit_request", sender):
                    code = transport.main(self.arguments(*extra))
        return code, output.getvalue()

    def assert_blocked_before_post(self, *extra):
        sender = mock.Mock(side_effect=AssertionError("must not reach sender"))
        code, text = self.run_client("--live", *extra, sender=sender)
        self.assertEqual(code, 1, text)
        sender.assert_not_called()

    def test_dry_run_preserves_every_frozen_byte_and_never_calls_network(self):
        before = {p.name: p.read_bytes() for p in self.frozen.iterdir()}
        code, text = self.run_client("--json", str(self.root / "preview.json"))
        self.assertEqual(code, 0, text)
        self.assertIn(dts.NOT_PERFORMED, text)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.frozen.iterdir()})
        self.assertFalse(list(self.state.iterdir()))

    def test_xml_and_txt_mutations_block_before_sender(self):
        for name in ("draft.xml", "draft.txt"):
            p = self.frozen / name
            original = p.read_bytes()
            p.write_bytes(original + b"changed")
            self.assert_blocked_before_post()
            p.write_bytes(original)

    def test_substituting_both_artifact_and_its_hash_does_not_bypass_external_pin(self):
        (self.frozen / "draft.txt").write_text("replacement")
        m = bundle.read_json(self.frozen / bundle.MANIFEST)
        item = next(x for x in m["artifacts"] if x["role"] == "review-txt")
        item.update(bytes=11, sha256=hashlib.sha256(b"replacement").hexdigest())
        (self.frozen / bundle.MANIFEST).write_bytes(bundle.json_bytes(m))
        self.assert_blocked_before_post()

    def test_missing_extra_and_symlink_files_are_blocked(self):
        p = self.frozen / "draft.txt"
        original = p.read_bytes()
        p.unlink()
        self.assert_blocked_before_post()
        p.symlink_to(self.source / "draft.txt")
        self.assert_blocked_before_post()
        p.unlink()
        p.write_bytes(original)
        (self.frozen / "extra").write_text("later evidence")
        self.assert_blocked_before_post()

    def test_historical_bundle_cannot_be_promoted_by_an_author_record(self):
        m = bundle.read_json(self.frozen / bundle.MANIFEST)
        m["purpose"] = "historical-pilot"
        (self.frozen / bundle.MANIFEST).write_bytes(bundle.json_bytes(m))
        self.manifest_hash = hashlib.sha256((self.frozen / bundle.MANIFEST).read_bytes()).hexdigest()
        for r in (self.decision, self.review):r["manifest_sha256"] = self.manifest_hash
        self.save_records()
        self.assert_blocked_before_post()

    def test_author_template_revocation_wrong_scope_or_identity_are_rejected(self):
        mutations = [
            {"status": "TEMPLATE_NOT_AUTHORIZATION"}, {"status": "REVOKED"},
            {"authorized_actions": ["public-export"]}, {"destinations": ["https://example.invalid/"]},
            {"candidate_id": "other"}, {"manifest_sha256": "0" * 64},
            {"submission": {"user": "other@example.com", "replaces": []}},
        ]
        original = dict(self.decision)
        for update in mutations:
            with self.subTest(update=update):
                self.decision = {**original, **update}
                self.save_records()
                self.assert_blocked_before_post()

    def test_review_missing_or_expired_cannot_be_hidden_by_approval(self):
        for update in [{"status": "TEMPLATE_INCOMPLETE"}, {"checks": []},
                       {"preflight_valid_until": "2000-01-01T00:00:00Z"}]:
            with self.subTest(update=update):
                before = dict(self.review)
                self.review.update(update)
                self.save_records()
                self.assert_blocked_before_post()
                self.review = before

    def test_warnings_with_explicit_disposition_and_engineering_debt_do_not_block(self):
        check = next(x for x in self.review["checks"] if x["id"] == "idnits-current")
        check["result"] = "ACCEPTED_WITH_DISPOSITION"
        self.review["finding_dispositions"] = [
            {"check_id": "idnits-current", "status": "ACCEPTED", "rationale": "Fixture disposition"}]
        self.save_records()
        code, text = self.run_client()
        self.assertEqual(code, 0, text)

    def test_accepted_warning_without_disposition_is_blocked(self):
        self.review["checks"][0]["result"] = "ACCEPTED_WITH_DISPOSITION"
        self.save_records()
        self.assert_blocked_before_post()

    def test_optional_engineering_check_does_not_become_an_id_gate(self):
        self.review["checks"].append({"id": "full-cross-platform-conformance", "result": "NOT_RUN", "evidence": []})
        self.save_records()
        code, text = self.run_client()
        self.assertEqual(code, 0, text)

    def test_record_substitution_is_detected(self):
        args = self.arguments("--live")
        self.decision_path.write_text("{}")
        with mock.patch.object(dts, "submit_request") as sender, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(transport.main(args), 1)
            sender.assert_not_called()

    def test_approval_does_not_bypass_scoped_artifact_leak_check(self):
        p = self.frozen / "draft.txt"
        p.write_text("-----BEGIN PRIVATE KEY-----\n")
        m = bundle.read_json(self.frozen / bundle.MANIFEST)
        entry = next(x for x in m["artifacts"] if x["role"] == "review-txt")
        entry.update(bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        (self.frozen / bundle.MANIFEST).write_bytes(bundle.json_bytes(m))
        self.manifest_hash = hashlib.sha256((self.frozen / bundle.MANIFEST).read_bytes()).hexdigest()
        for r in (self.decision, self.review):r["manifest_sha256"] = self.manifest_hash
        self.save_records()
        self.assert_blocked_before_post()

    def test_public_interop_links_are_not_misclassified_as_private(self):
        self.assertEqual(transport.guard.scan_bytes(b"https://github.com/WEXP-dev/wexp-interop", "fixture"), [])

    def test_decision_and_output_inside_bundle_are_refused(self):
        self.assert_blocked_before_post("--json", str(self.frozen / "result.json"))
        self.decision_path = self.frozen / "decision.json"
        self.save_records()
        self.assert_blocked_before_post()

    def test_environment_operator_check_and_state_are_all_required(self):
        self.assert_blocked_before_post()
        self.assert_blocked_before_post("--operator-checked-current-decision")
        with mock.patch.dict(os.environ, {dts.LIVE_SWITCH_NAME: dts.LIVE_SWITCH_VALUE}):
            self.assert_blocked_before_post("--operator-checked-current-decision")

    def live_args(self):
        return ("--live", "--operator-checked-current-decision", "--state-dir", str(self.state))

    def test_matching_mock_response_records_queued_not_published_and_blocks_retry(self):
        body = {"id": "123", "name": IDENTITY[:-3], "rev": "02",
                "status_url": dts.DATATRACKER_SUBMISSION_URL + "/123/status"}
        def send(request, **kw):
            journal = self.state / (IDENTITY + ".jsonl")
            self.assertEqual(json.loads(journal.read_text())["result"], "OUTCOME_UNKNOWN")
            self.assertIn(self.xml_bytes, dts.encode_multipart(request, "testboundary"))
            return dts.SubmissionResponse(201, body)
        sender = mock.Mock(side_effect=send)
        with mock.patch.dict(os.environ, {dts.LIVE_SWITCH_NAME: dts.LIVE_SWITCH_VALUE}):
            code, text = self.run_client(*self.live_args(), sender=sender)
            self.assertEqual(code, 0, text)
            self.assertIn("SUBMISSION_QUEUED", text)
            self.assertIn('"publication_verified": false', text)
            code, _ = self.run_client(*self.live_args(), sender=sender)
            self.assertEqual(code, 1)
            self.assertEqual(sender.call_count, 1)

    def test_timeout_is_unknown_and_prevents_retry(self):
        sender = mock.Mock(side_effect=TimeoutError("fixture"))
        with mock.patch.dict(os.environ, {dts.LIVE_SWITCH_NAME: dts.LIVE_SWITCH_VALUE}):
            code, text = self.run_client(*self.live_args(), sender=sender)
            self.assertEqual(code, 2, text)
            self.assertIn("OUTCOME_UNKNOWN", text)
            self.run_client(*self.live_args(), sender=sender)
            self.assertEqual(sender.call_count, 1)

    def test_http_success_for_different_revision_is_not_queued(self):
        sender = mock.Mock(return_value=dts.SubmissionResponse(200, {"id": 123, "name": IDENTITY[:-3], "rev": "01"}))
        with mock.patch.dict(os.environ, {dts.LIVE_SWITCH_NAME: dts.LIVE_SWITCH_VALUE}):
            code, text = self.run_client(*self.live_args(), sender=sender)
        self.assertEqual(code, 2, text)
        self.assertIn("OUTCOME_UNKNOWN", text)

    def test_result_journal_failure_does_not_claim_no_submission(self):
        body = {"id": "123", "name": IDENTITY[:-3], "rev": "02",
                "status_url": dts.DATATRACKER_SUBMISSION_URL + "/123/status"}
        sender = mock.Mock(return_value=dts.SubmissionResponse(201, body))
        original = transport.append_event
        calls = []
        def append(stream, event):
            calls.append(event)
            if len(calls) == 2:
                raise OSError("simulated result write failure")
            original(stream, event)
        with mock.patch.dict(os.environ, {dts.LIVE_SWITCH_NAME: dts.LIVE_SWITCH_VALUE}), \
             mock.patch.object(transport, "append_event", append):
            code, text = self.run_client(*self.live_args(), sender=sender)
        self.assertEqual(code, 2, text)
        self.assertIn("OUTCOME_UNKNOWN", text)
        self.assertNotIn(dts.NOT_PERFORMED, text)
        sender.assert_called_once()

    def test_live_path_cannot_rebuild_or_rewrite_the_bundle(self):
        with mock.patch("subprocess.run", side_effect=AssertionError("build is forbidden")):
            code, text = self.run_client()
        self.assertEqual(code, 0, text)


if __name__ == "__main__":
    unittest.main()
