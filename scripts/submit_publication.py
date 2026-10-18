#!/usr/bin/env python3
"""Preview or submit an already frozen ietf-draft-bundle-v1; never build it.

The default is offline. Live use also needs an actual author decision, review
of the exact bundle, an operator's current-decision check, the environment
switch and a persistent attempt directory. Records declare decisions/checks;
the operator checks their authenticity, scope and current standing.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Sequence
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datatracker_submit as dts
import draft_bundle as bundle
import publication_guard as guard

CHECKS = {
    "semantic-diff", "agreed-text-preservation", "metadata-ipr-security-iana",
    "references", "xml2rfc-build", "idnits-current", "export-allowlist",
    "remote-byte-readback",
}


def outside(path: Path, root: Path) -> None:
    bundle.require(not path.resolve().is_relative_to(root.resolve()),
                   "decisions, review, attempt state and results must stay outside the frozen bundle")


def pinned_json(path: Path, expected: str) -> dict:
    bundle.require(type(expected) is str and re.fullmatch(r"[0-9a-f]{64}", expected),
                   "an external SHA-256 is required for every pinned record")
    bundle.require(path.is_file() and not path.is_symlink(), "record must be a regular file")
    raw = path.read_bytes()
    bundle.require(hashlib.sha256(raw).hexdigest() == expected, "record digest mismatch")
    result = json.loads(raw, object_pairs_hook=bundle.unique_object)
    bundle.require(type(result) is dict, "record must be a JSON object")
    return result


def timestamp(value: str) -> datetime:
    bundle.require(type(value) is str, "record time must be a string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    bundle.require(parsed.tzinfo is not None, "record time must include a timezone")
    return parsed


def validate_records(manifest: dict, manifest_hash: str, decision: dict, review: dict,
                     now: datetime) -> None:
    for record in (decision, review):
        bundle.require(record.get("candidate_id") == manifest["candidate_id"], "candidate identity mismatch")
        bundle.require(record.get("manifest_sha256") == manifest_hash, "record binds a different manifest")
    bundle.require(manifest["purpose"] == "publication-candidate", "a historical pilot cannot be submitted")
    bundle.require(decision.get("schema") == "ietf-draft-author-decision-v1", "unsupported author record")
    bundle.require(decision.get("status") == "AUTHOR_APPROVED", "no completed author approval")
    for field in ("author", "decision_source"):
        bundle.require(type(decision.get(field)) is str and decision[field].strip(), f"missing {field}")
    source_hash = decision.get("decision_source_sha256")
    bundle.require(type(source_hash) is str and re.fullmatch(r"[0-9a-f]{64}", source_hash),
                   "author-decision source digest required")
    bundle.require(timestamp(decision["decided_at"]) <= now, "author decision is dated in the future")
    actions, destinations = decision.get("authorized_actions"), decision.get("destinations")
    bundle.require(type(actions) is list and "datatracker-submit" in actions, "submission action not authorized")
    bundle.require(type(destinations) is list and dts.DATATRACKER_SUBMISSION_URL in destinations,
                   "submission destination not authorized")
    bundle.require(review.get("schema") == "ietf-draft-review-record-v1", "unsupported review record")
    bundle.require(review.get("status") == "REVIEW_COMPLETE" and
                   review.get("technical_conclusion") == "READY_FOR_SUBMISSION", "review is incomplete or not ready")
    bundle.require(type(review.get("reviewer")) is str and review["reviewer"].strip(), "reviewer is missing")
    bundle.require(timestamp(review["reviewed_at"]) <= now <= timestamp(review["preflight_valid_until"]),
                   "preflight is expired or review is dated in the future")
    checks = review.get("checks")
    bundle.require(type(checks) is list, "review checks must be a list")
    seen = set()
    dispositions = review.get("finding_dispositions", [])
    bundle.require(type(dispositions) is list, "finding dispositions must be a list")
    for check in checks:
        bundle.require(type(check) is dict and type(check.get("id")) is str, "invalid check")
        bundle.require(check["id"] not in seen, "duplicate review check")
        seen.add(check["id"])
        if check["id"] not in CHECKS:
            # Additional engineering observations do not become I-D gates.
            # The human technical conclusion must still account for claims made.
            continue
        bundle.require(check.get("result") in {"PASS", "ACCEPTED_WITH_DISPOSITION"}, "unresolved review check")
        bundle.require(type(check.get("evidence")) is list and bool(check["evidence"]), "check has no evidence references")
        if check["result"] == "ACCEPTED_WITH_DISPOSITION":
            bundle.require(any(type(d) is dict and d.get("check_id") == check["id"] and
                               d.get("status") == "ACCEPTED" and d.get("rationale") for d in dispositions),
                           "accepted finding needs its own disposition")
    bundle.require(CHECKS <= seen, "required review checks are missing")
    # Engineering backlog is deliberately not a transport gate.


def prepared_request(args, now: datetime):
    for path in (args.author_decision, args.review_record):
        outside(path, args.bundle_root)
    bundle.verify(args.bundle_root, args.expected_manifest_sha256)
    # Parse the same externally pinned bytes, not an unpinned replacement.
    manifest = pinned_json(args.bundle_root / bundle.MANIFEST, args.expected_manifest_sha256)
    decision = pinned_json(args.author_decision, args.expected_decision_sha256)
    review = pinned_json(args.review_record, args.expected_review_sha256)
    validate_records(manifest, args.expected_manifest_sha256, decision, review, now)
    bundle.require(decision.get("submission") == {"user": args.user, "replaces": args.replaces},
                   "submitter/replaces differ from the recorded authorization scope")
    identity = manifest["draft_name"] + "-" + manifest["revision"]
    bundle.require(identity == args.identity, "requested draft identity differs from bundle")
    xml = next(x for x in manifest["artifacts"] if x["role"] == "submission-xml")
    # Keep scoped artifact-leak checks, not the old tag-before-submit gate.
    # Private supporting review evidence is not transmitted by this client.
    for artifact in manifest["artifacts"]:
        if artifact["role"] in {"submission-xml", "review-txt", "review-html"}:
            findings = guard.scan_bytes(bundle.read_regular(args.bundle_root, artifact["path"]), artifact["path"])
            bundle.require(not findings, "; ".join(findings))
    request = dts.prepare_request(
        args.bundle_root / xml["path"], user=args.user, replaces=args.replaces,
        artifact_identity=identity, authorization_id=args.expected_decision_sha256,
        guard_passed=True, submission_authorized=True,
    )
    bundle.require(request.xml_sha256 == xml["sha256"] and request.xml_size == xml["bytes"],
                   "XML changed after bundle verification")
    return request, manifest


def append_event(stream, event: dict) -> None:
    stream.write(json.dumps(event, sort_keys=True) + "\n")
    stream.flush()
    os.fsync(stream.fileno())


def accepted_response(response: dts.SubmissionResponse, identity: str) -> bool:
    data = response.body
    name, revision = identity.rsplit("-", 1)
    sid = str(data.get("id", ""))
    return bool(response.ok and re.fullmatch(r"[0-9]+", sid) and
                data.get("name") == name and data.get("rev") == revision and
                data.get("status_url") == f"{dts.DATATRACKER_SUBMISSION_URL}/{sid}/status")


def live_attempt(args, request, evidence: dict) -> tuple[int, dict]:
    bundle.require(args.operator_checked_current_decision,
                   "operator must check the actual decision, review and absence of revocation")
    reasons = dts.blocking_reasons(request, live=True)
    bundle.require(not reasons, "; ".join(reasons))
    bundle.require(args.state_dir is not None, "live submission requires persistent --state-dir")
    outside(args.state_dir, args.bundle_root)
    bundle.require(args.state_dir.is_dir() and not args.state_dir.is_symlink(), "state directory must already exist")
    journal = args.state_dir / (request.artifact_identity + ".jsonl")
    # Exclusive create serializes attempts for this revision in this state store.
    # A crash leaves a durable refusal of a retry, not an inference of no effect.
    with journal.open("x", encoding="utf-8") as stream:
        pending = {**evidence, "result": "OUTCOME_UNKNOWN", "network_submission_performed": None,
                   "recorded_at": datetime.now(timezone.utc).isoformat()}
        append_event(stream, pending)
        fd = os.open(args.state_dir, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        # If a later I/O/close error escapes, the caller must not report that
        # nothing was sent. The durable journal already carries this uncertainty.
        evidence.update(result="OUTCOME_UNKNOWN", network_submission_performed=None)
        try:
            response = dts.submit_request(request, live=True)
        except (dts.SubmissionBlocked, dts.SubmissionRequestError):
            outcome = {**evidence, "result": dts.NOT_PERFORMED, "network_submission_performed": False}
            code = 1
        except Exception as exc:
            outcome = {**pending, "error_type": type(exc).__name__,
                       "next_action": "Inspect Datatracker state before considering another attempt."}
            code = 2
        else:
            queued = accepted_response(response, request.artifact_identity)
            outcome = {**evidence, "result": "SUBMISSION_QUEUED" if queued else "OUTCOME_UNKNOWN",
                       "network_submission_performed": True, "http_status": response.status_code,
                       "response": response.body, "publication_verified": False,
                       "confirmation": "Follow the actual Datatracker state; the API requires author confirmation.",
                       "next_action": "Read submission status; do not repeat the POST."}
            code = 0 if queued else 2
        try:
            append_event(stream, outcome)
        except OSError:
            return 2, {**pending, "error_type": "AttemptJournalWriteFailed",
                       "next_action": "Inspect Datatracker; the initial attempt entry prohibits retry."}
    return code, outcome


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--identity", required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--author-decision", type=Path, required=True)
    parser.add_argument("--expected-decision-sha256", required=True)
    parser.add_argument("--review-record", type=Path, required=True)
    parser.add_argument("--expected-review-sha256", required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--replaces", action="append", default=[])
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--operator-checked-current-decision", action="store_true")
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--json", dest="json_out", type=Path)
    args = parser.parse_args(argv)
    evidence = {"result": dts.NOT_PERFORMED, "network_submission_performed": False,
                "publication_verified": False, "live_requested": args.live,
                "manifest_sha256": args.expected_manifest_sha256,
                "author_decision_sha256": args.expected_decision_sha256,
                "review_record_sha256": args.expected_review_sha256}
    try:
        if args.json_out:
            outside(args.json_out, args.bundle_root)
            bundle.require(not args.json_out.exists() and not args.json_out.is_symlink(), "result path already exists")
        request, manifest = prepared_request(args, datetime.now(timezone.utc))
        evidence.update(artifact_identity=request.artifact_identity, candidate_id=manifest["candidate_id"],
                        submitted_xml_sha256=request.xml_sha256, request_preview=request.preview())
        if args.live:
            code, evidence = live_attempt(args, request, evidence)
        else:
            evidence.update(dts.dry_run(request))
            code = 0
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            with args.json_out.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(evidence, indent=2) + "\n")
    except (ValueError, TypeError, KeyError, OSError, ET.ParseError, dts.SubmissionBlocked) as exc:
        if evidence["network_submission_performed"] is not False:
            print(json.dumps(evidence, indent=2))
            print("EVIDENCE WRITE FAILED — inspect Datatracker; do not retry", file=sys.stderr)
            return 2
        print(f"BLOCKED: {exc}", file=sys.stderr)
        print(dts.NOT_PERFORMED)
        return 1
    print(json.dumps(evidence, indent=2))
    print(evidence["result"])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
