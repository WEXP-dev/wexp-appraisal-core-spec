#!/usr/bin/env python3
"""Freeze and verify local I-D bundles. No network, submission, or authorization API."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path, PurePosixPath

VERSION = "1.0.0"
SCHEMA = "ietf-draft-bundle-v1"
ROLES = {"submission-xml", "review-txt", "review-html", "evidence", "auxiliary"}
MANIFEST = "MANIFEST.json"


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique_object)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def keys(value, expected, label):
    require(type(value) is dict and set(value) == set(expected), f"invalid {label} fields")


def safe_name(value):
    require(type(value) is str and bool(value), "empty/non-string path")
    p = PurePosixPath(value)
    require(not p.is_absolute() and p.as_posix() == value, f"noncanonical path: {value}")
    require(all(x not in {".", "..", ".git"} for x in p.parts), f"unsafe path: {value}")
    require(not any(c in value for c in "\\\r\n\0:"), f"unsafe path: {value}")
    require(value != MANIFEST, "manifest cannot list itself")
    return p


def read_regular(root, name):
    parts = safe_name(name).parts
    path = Path(root)
    require(path.is_dir() and not path.is_symlink(), "root must be a real directory")
    for part in parts:
        path = path / part
        require(not path.is_symlink(), f"symlink is forbidden: {name}")
    require(path.is_file(), f"missing/non-regular artifact: {name}")
    return path.read_bytes()


def validate_header(data):
    require(data["schema"] == SCHEMA, "unsupported schema")
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", data["candidate_id"] or ""), "invalid candidate ID")
    require(data["purpose"] in {"publication-candidate", "historical-pilot"}, "invalid purpose")
    require(re.fullmatch(r"draft-[a-z0-9]+(?:-[a-z0-9]+)*", data["draft_name"] or ""), "invalid draft name")
    require(type(data["revision"]) is str and re.fullmatch(r"[0-9]{2}", data["revision"]), "revision must be a two-digit string")
    source = data["source"]
    keys(source, {"repository", "repository_id", "commit"}, "source")
    require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", source["repository"] or ""), "invalid source repository")
    require(type(source["repository_id"]) is int and source["repository_id"] > 0, "repository ID must be a positive integer")
    require(type(source["commit"]) is str and re.fullmatch(r"[0-9a-f]{40}", source["commit"]), "source commit must be a full SHA")
    require(type(data["toolchain"]) is dict and bool(data["toolchain"]), "toolchain provenance required")
    require(all(type(k) is str and type(v) is str and k and v for k, v in data["toolchain"].items()), "toolchain values must be explicit strings")
    require(type(data["artifacts"]) is list and bool(data["artifacts"]), "artifact list required")
    counts = Counter()
    seen = set()
    for item in data["artifacts"]:
        safe_name(item["path"])
        require(item["path"] not in seen, "duplicate artifact path")
        seen.add(item["path"])
        require(item["role"] in ROLES, "unknown artifact role")
        counts[item["role"]] += 1
    require(counts["submission-xml"] == 1 and counts["review-txt"] == 1, "exactly one XML and one review TXT required")


def validate_xml(data, manifest):
    # This deliberately checks identity only. xml2rfc/idnits and semantic review remain separate.
    text = data.decode("utf-8")
    require("<!DOCTYPE" not in text.upper() and "<!ENTITY" not in text.upper(), "standalone XML without DTD/entities required")
    root = ET.fromstring(data)
    require(root.tag == "rfc" and root.get("version") == "3", "RFCXML v3 root required")
    identity = manifest["draft_name"] + "-" + manifest["revision"]
    require(root.get("docName") == identity, "XML docName differs from manifest")
    require(not any(e.tag == "{http://www.w3.org/2001/XInclude}include" for e in root.iter()), "resolve XInclude before freezing")
    return {"docName": identity, "submissionType": root.get("submissionType", "IETF")}


def freeze(descriptor, source_root, destination):
    keys(descriptor, {"schema", "candidate_id", "purpose", "draft_name", "revision", "source", "toolchain", "artifacts"}, "descriptor")
    validate_header(descriptor)
    target = Path(destination)
    require(not target.exists() and not target.is_symlink(), "destination exists; use a new candidate ID/directory")
    payloads = {}
    entries = []
    for item in descriptor["artifacts"]:
        keys(item, {"path", "role"}, "descriptor artifact")
        content = read_regular(source_root, item["path"])
        if item["role"] == "submission-xml":
            validate_xml(content, descriptor)
        payloads[item["path"]] = content
        entries.append({**item, "bytes": len(content), "sha256": digest(content)})
    result = {**descriptor, "artifacts": sorted(entries, key=lambda x: x["path"]), "bundle_tool_version": VERSION}
    # Exclusive creation: a pre-existing candidate is never modified.
    target.mkdir(parents=True, exist_ok=False)
    for name, content in payloads.items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as output:
            output.write(content)
    with (target / MANIFEST).open("xb") as output:
        output.write(json_bytes(result))
    return verify(target)


def verify(root, expected_manifest=None):
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), "bundle root must be a real directory")
    manifest_path = root / MANIFEST
    require(manifest_path.is_file() and not manifest_path.is_symlink(), "missing/non-regular manifest")
    raw = manifest_path.read_bytes()
    manifest_hash = digest(raw)
    if expected_manifest is not None:
        require(type(expected_manifest) is str and re.fullmatch(r"[0-9a-f]{64}", expected_manifest), "expected manifest digest must be SHA-256")
        require(manifest_hash == expected_manifest, "manifest digest mismatch")
    data = read_json(manifest_path)
    keys(data, {"schema", "candidate_id", "purpose", "draft_name", "revision", "source", "toolchain", "artifacts", "bundle_tool_version"}, "manifest")
    require(data["bundle_tool_version"] == VERSION, "unsupported bundle tool version")
    validate_header(data)
    listed = {MANIFEST}
    xml_metadata = None
    for item in data["artifacts"]:
        keys(item, {"path", "role", "bytes", "sha256"}, "manifest artifact")
        require(type(item["bytes"]) is int and item["bytes"] >= 0, "byte count must be a nonnegative integer")
        require(type(item["sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", item["sha256"]), "invalid SHA-256")
        content = read_regular(root, item["path"])
        require(len(content) == item["bytes"] and digest(content) == item["sha256"], f"artifact differs: {item['path']}")
        listed.add(item["path"])
        if item["role"] == "submission-xml":
            xml_metadata = validate_xml(content, data)
    actual = set()
    for path in root.rglob("*"):
        require(not path.is_symlink(), f"symlink in bundle: {path.name}")
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
        else:
            require(path.is_dir(), "non-regular bundle entry")
    require(actual == listed, "unlisted or missing artifact(s)")
    return {"result": "INTEGRITY_VERIFIED", "candidate_id": data["candidate_id"], "purpose": data["purpose"],
            "manifest_sha256": manifest_hash, "artifact_count": len(data["artifacts"]),
            "xml_metadata": xml_metadata, "technical_readiness": "NOT_EVALUATED", "authorization": "NOT_EVALUATED",
            "submission_performed": False, "publication_verified": False,
            "limit": "Local file identity only; source provenance is declared, not remotely authenticated."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("freeze")
    create.add_argument("--descriptor", required=True, type=Path)
    create.add_argument("--source-root", required=True, type=Path)
    create.add_argument("--output", required=True, type=Path)
    check = sub.add_parser("verify")
    check.add_argument("bundle", type=Path)
    check.add_argument("--expected-manifest-sha256")
    args = parser.parse_args(argv)
    try:
        result = freeze(read_json(args.descriptor), args.source_root, args.output) if args.command == "freeze" else verify(args.bundle, args.expected_manifest_sha256)
    except (Invalid, OSError, UnicodeError, ET.ParseError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"result": "FAIL", "reason": str(exc), "submission_performed": False}), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
