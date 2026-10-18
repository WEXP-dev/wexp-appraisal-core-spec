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

Manual submission through the [Datatracker](https://datatracker.ietf.org/submit/)
is the standard transport. Upload the approved XML file without rebuilding it.
Follow the confirmation required by Datatracker; a successful upload or queued
API response is not a verified publication. If an outcome is uncertain, check
the existing submission before retrying.

After posting, download the official XML/TXT and record their identities and
comparison with the approved package. Explain any server-generated rendering
differences. Preserve earlier observations if metadata APIs lag the archive.
An authorized GitHub release then records the already posted revision, binds
the source commit and official files, and verifies uploaded release assets.
Existing revision tags and archived files are not overwritten.

Ordinary PR/push checks have no submission authority. Any future automated
transport requires a separately reviewed implementation and author decision;
it must consume the already approved bytes and check their externally pinned
manifest digest. It must not rebuild at send time.

References: [submission instructions](https://datatracker.ietf.org/submit/tool-instructions/),
[API contract](https://datatracker.ietf.org/api/submission),
[Note Well](https://www.ietf.org/about/note-well/).
