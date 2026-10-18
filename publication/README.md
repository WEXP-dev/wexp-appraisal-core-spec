# Preparing and submitting a WEXP Internet-Draft

[PUBLICATION-PROCESS.md](../PUBLICATION-PROCESS.md) is the governing process.
The IETF archive is authoritative for posted revisions. The XML/TXT under
`drafts/`, their manifests and historical authorization records are preserved.

## Normal path

1. Prepare and review the source, full diff and exact rendered XML/TXT.
2. Record the build and current idnits preflight, including modes, versions,
   timestamps, input hashes, original logs and dispositions of findings.
3. Freeze the selected existing files as an `ietf-draft-bundle-v1` directory.
   Its `MANIFEST.json` is pinned by a SHA-256 kept outside that directory.
4. Record the author's actual decision for that digest and the intended
   actions/destinations. Review and decision records remain outside the bundle.
5. Upload the saved approved XML through the
   [Datatracker web tool](https://datatracker.ietf.org/submit/).
   Do not rebuild, redate or normalize it at this step.
6. Follow the actual confirmation state. Download the official XML/TXT,
   record their identities and resolve differences. Only then create the final
   revision tag/release when authorized.

A candidate tag, if useful, has a distinct name. An annotated signed tag can
help identify an artifact; it is neither proof of author approval nor a
prerequisite for manual submission. No second author approval is required
merely because the same unchanged, already authorized package is used again
within its approved scope. An uncertain prior submission must first be resolved.

## Freeze and verify

The offline `scripts/draft_bundle.py` uses the common
[bundle contract](BUNDLE-FORMAT.md), version 1.0.0:

```sh
python3 scripts/draft_bundle.py freeze \
  --descriptor descriptor.json --source-root selected-files --output candidate
python3 scripts/draft_bundle.py verify candidate \
  --expected-manifest-sha256 MANIFEST_SHA256_FROM_THE_REVIEWED_RECORD
```

The destination must be new. No existing package is overwritten. Verification
checks the complete listed file set, lengths, SHA-256 values, XML identity and
safe paths. It does not establish semantic correctness, source authenticity,
the truth of a review record, current idnits results or author approval.
Later evidence is stored separately; changed package bytes require a new
candidate identity. Repository backups or controlled archives, not the
expiration period of an Actions artifact, provide preservation.

## Optional API transport

`scripts/submit_publication.py` reads the frozen bundle directly. It does not
invoke xml2rfc, idnits, Node, the legacy preparation script or git tag creation.
It takes externally pinned digests for the manifest, author decision and review
record. [The optional transport record profile](BUNDLE-FORMAT.md#transport-records)
makes their fields explicit; a declaration of approval is not authentication
of the person who made it.

WEXP's artifact scan is retained for XML/TXT/HTML: known secret shapes, local
paths, candidate identifiers and repository references outside the reviewed
public allowlist cause refusal. This limited scan complements the export
review; it is not proof that an artifact contains no private information.
Supporting review evidence is not posted or automatically uploaded by the client.

Without the live option, this is an offline preview:

```sh
python3 scripts/submit_publication.py \
  --bundle-root candidate --identity draft-example-core-02 \
  --expected-manifest-sha256 MANIFEST_SHA256 \
  --author-decision records/author-decision.json \
  --expected-decision-sha256 DECISION_SHA256 \
  --review-record records/review.json --expected-review-sha256 REVIEW_SHA256 \
  --user author@example.com --json records/new-preview.json
```

Replace the example identity, paths and digest placeholders with independently
checked values. A prior `BUNDLE-MANIFEST.json` or historical import is not
accepted as a current submission bundle. Existing authorizations are not
automatically upgraded or used to resubmit an already posted revision.

Future live CLI use additionally requires `--live`,
`WEXP_DATATRACKER_SUBMIT=PUBLISH`, `--operator-checked-current-decision` and an
existing persistent `--state-dir` outside the bundle. The operator checks the
actual author decision, its scope and absence of revocation, the review evidence
and the current Datatracker state. These switches record that responsibility;
they do not prove it was fulfilled.

Before any POST the client exclusively creates and durably records an attempt
for that exact draft revision. The journal is append-only. A prior attempt
blocks another attempt in the same store, even after a crash, timeout or an
unexpected response. Preserve the store across runs; changing or deleting it
does not establish that retry is safe. This is a local POSIX filesystem control,
not a distributed exactly-once guarantee. Resolve prior state manually; this
tool provides no automatic retry or reset.

The client checks the actual XML bytes encoded in the multipart request.
Only a matching API response with submission ID, draft name/revision and
status URL is reported as queued. Queued is not posted, and does not prove that
a confirmation email was delivered. The API requires author confirmation;
the web tool may offer an authenticated author immediate posting. Follow the
returned state, then verify the official archive separately.

## Hosted automation remains unable to submit

`ietf-publication-submit.yml` is an explicitly dispatched **preview only**.
It reads public-authorized inputs from a full public commit SHA as data; it
runs code from the reviewed main revision, not from the data checkout.
It performs no rebuild and supplies no live option or switch. A variable
cannot turn this workflow into a POST.

Public input storage is optional. Do not disclose a private candidate or
decision record merely to use this preview; use the local path instead.
A future hosted sender needs a separately reviewed durable attempt store,
canonical-repository/branch restrictions, actual environment protection and
a specific author decision for submission. No YAML comment establishes those
Settings. Current preparation and ordinary PR/push CI have no submission
authority.

## Historical preparation and guards

`prepare_publication.py`, `publication_guard.py` and the existing
`authorizations/` preserve the earlier tag-based pipeline and its G01–G14
checks for historical analysis. The preparation workflow is now manual-only.
It writes a new rehearsal directory and labels passing checks as
`LEGACY CHECKS PASSED — CURRENT APPROVAL NOT EVALUATED`.
It cannot replace the common freeze/review/decision path above.

Keep the useful predicates: exact identity and byte bindings, explicit
provenance, review dispositions, scoped export checks and the separation of
CI from semantic claims. Do not turn an old signed-tag gate, an offline lint
result or a successful implementation test into current publication authority.
Engineering conformance debt is tracked separately unless it invalidates a
claim actually made in the draft.

[Main specification navigation](../README.md) ·
[Official submission instructions](https://datatracker.ietf.org/submit/tool-instructions/) ·
[API contract](https://datatracker.ietf.org/api/submission)
