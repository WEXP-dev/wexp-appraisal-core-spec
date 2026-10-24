# Preparing and publishing Internet-Draft revisions

The IETF archive is authoritative for posted revisions. The editor's source,
a review candidate, an author-approved submission and a posted revision have
distinct identities. Repository checks do not establish WG adoption, consensus,
protocol conformance or approval to publish.

## Development

Use a focused pull request for a substantive change. Record the problem,
editorial decision, affected normative text and relevant checks. Feedback by
email is equally welcome. Preserve agreed contributor text and attribution;
consult contributors when a proposed change affects the scope of their consent.
Maintain one editable manuscript source; generated renderings are review aids.

## Preparing a revision

1. Pin the source commit and previous official revision; review the complete diff.
2. Check terminology, normative consistency, examples, references, metadata,
   Security/IANA Considerations and applicable IETF IPR obligations.
3. Build with a pinned xml2rfc version. Run a current idnits preflight, recording
   version, modes, commands, timestamps, input hashes and original logs. Preserve
   failed results and document dispositions separately.
4. Freeze the standalone RFCXML v3, review TXT and available review evidence.
   Record SHA-256 and byte counts. Subsequent evidence belongs outside the frozen
   package. A byte change creates a new candidate identity.
5. Obtain the author's decision for that exact package and the intended actions.
   Existing permission remains sufficient for the unchanged files and scope.

An open engineering issue does not automatically prevent an individual I-D
revision. A claimed property must nevertheless have adequate support, or the
claim must be qualified. See [RFC 8874, Section 6](https://www.rfc-editor.org/rfc/rfc8874.html#section-6).

## Submission and verification

The selected GitHub route is a reviewed source commit, successful checks, and
an explicitly published release for the exact draft revision. The revision's
release workflow submits the existing approved XML through the documented
[Datatracker API](https://datatracker.ietf.org/api/submission), without rebuilding
or changing its date. See [the GitHub submission procedure](publication/GITHUB-SUBMISSION.md)
for the release trigger, attempt records and confirmation steps. This follows
the common IETF GitHub release workflow, with a small repository adapter to
preserve the selected RFCXML bytes instead of rebuilding them.

Manual upload of the same approved XML through the
[Datatracker](https://datatracker.ietf.org/submit/) remains an alternative, but
must not be used in parallel with an unresolved API attempt. Follow the actual
confirmation state; an upload or queued API response is not verified posting.

After posting, download the official XML/TXT and record their identities and
comparison with the approved package. Explain any server-generated rendering
differences. Preserve earlier observations if metadata APIs lag the archive.
The submission release initially remains a prerelease and clearly says that
posting is not yet verified. Its tag identifies the selected source; it does
not establish IETF acceptance. After official archive verification, update the
release's status and evidence without moving its tag or replacing frozen files.
Existing revision tags and archived files are not overwritten.

Ordinary PR/push checks have no submission authority. The revision-specific
release workflow requires a prior author decision for the exact package and
submission action. It checks the configured XML and manifest digests, current
main commit, successful CI and retained earlier attempts. Publishing the
release is the operator's explicit invocation of that authorized action.
The older hosted preview workflow remains unable to submit.

References: [submission instructions](https://datatracker.ietf.org/submit/tool-instructions/),
[API contract](https://datatracker.ietf.org/api/submission),
[Note Well](https://www.ietf.org/about/note-well/).
