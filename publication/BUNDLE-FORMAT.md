# Frozen bundle and optional transport records

## Bundle

`MANIFEST.json` uses `schema: ietf-draft-bundle-v1` and
`bundle_tool_version: 1.0.0`. The common contract has these other fields:

| Field | Content |
|---|---|
| candidate_id | New immutable candidate identity |
| purpose | publication-candidate or historical-pilot |
| draft_name / revision | Full draft name without revision / two-digit revision |
| source | repository, numeric repository_id, full commit SHA |
| toolchain | Nonempty map of explicit version/provenance strings |
| artifacts | path, role, bytes, sha256 for each exact file |

There is exactly one `submission-xml` and one `review-txt`; optional roles
are `review-html`, `evidence` and `auxiliary`. All files are listed.
Paths are canonical relative POSIX paths. Symlinks, traversal, duplicate JSON
keys, DTD/entities and XInclude are rejected. The XML is standalone RFCXML v3
with matching docName. The external manifest digest binds the whole package,
including TXT and supporting evidence. The manifest does not hash itself.

A freeze descriptor has the same header without `bundle_tool_version`, and
each artifact supplies only `path` and `role`. Freeze copies exact bytes and
computes lengths/hashes. It does not render or edit them. Unknown historical
toolchain provenance must be stated as unknown.

## Transport records

These are concrete local conventions for the optional WEXP API client.
They do not add mandatory IETF requirements or change the manual submission
route. Record an existing actual decision faithfully; filling a template,
signing a tag or passing CI does not create authorization.

The author record uses the common `ietf-draft-author-decision-v1` schema:

- `status: AUTHOR_APPROVED`, exact `candidate_id` and `manifest_sha256`;
- nonempty `author`, `decision_source`, its `decision_source_sha256`,
  and timezone-aware `decided_at`;
- `authorized_actions` contains `datatracker-submit`;
- `destinations` contains `https://datatracker.ietf.org/api/submission`;
- `submission` records the exact `user` and `replaces` list for this
  transport. An ordinary revision normally has an empty replaces list.

The review uses the common `ietf-draft-review-record-v1` schema:

- `status: REVIEW_COMPLETE`, exact `candidate_id` and `manifest_sha256`;
- `reviewer`, timezone-aware `reviewed_at`, and
  `technical_conclusion: READY_FOR_SUBMISSION`;
- `preflight_valid_until` is the reviewer's explicit, timezone-aware
  validity limit for this submission context. No fixed lifetime is invented by
  the client. This field does not prove that an online/current check ran.
- `checks` includes semantic-diff, agreed-text-preservation,
  metadata-ipr-security-iana, references, xml2rfc-build, idnits-current,
  export-allowlist and remote-byte-readback. Each required check has nonempty evidence
  references and a result of PASS or ACCEPTED_WITH_DISPOSITION.
- An accepted finding has a corresponding `finding_dispositions` entry with
  `check_id`, `status: ACCEPTED` and `rationale`. Original failed/warning
  results and logs remain evidence; the disposition does not rewrite them.
- `engineering_backlog` is retained and is not an automatic rejection gate.
  Additional engineering checks may remain NOT_RUN. They do not silently expand
  the required set; the human technical conclusion must account for the claims
  actually made in the draft.

All record files and output journals stay outside the frozen directory.
Their expected digests are supplied from the operator's reviewed records, not
derived from whatever untrusted bundle or workflow artifact was just received.
A preflight may be refreshed with a new review record for unchanged bytes
without obtaining another author decision for the same authorized scope.
Revocation and later superseding decisions must still be checked by the operator.

The client verifies record bindings and declared status, not the truth of the
underlying review or the identity of its author. Evidence references are for
human inspection; their mere presence is not a passing semantic finding.
No real author decision or current review is supplied with this implementation.
