# License and provenance map

## Separately authored repository tooling

The following repository-authored files are available under the
[BSD-3-Clause terms](LICENSE-CODE). This is an explicit file list; placing a
different file next to one of them does not extend the grant automatically.

- `scripts/datatracker_submit.py`
- `scripts/draft_bundle.py`
- `scripts/github_release_submit.py`
- `scripts/prepare_publication.py`
- `scripts/provision_toolchain.py`
- `scripts/publication_guard.py`
- `scripts/submit_publication.py`
- `scripts/verify_publication.py`
- `scripts/verify_published.py`
- `tests/support.py`
- `tests/test_datatracker_submit.py`
- `tests/test_draft_bundle.py`
- `tests/test_github_release_submit.py`
- `tests/test_prepare_publication.py`
- `tests/test_publication_guard.py`
- `tests/test_signature_guard.py`
- `tests/test_submit_publication.py`
- `tests/test_toolchain_provenance.py`
- `tests/test_verify_publication.py`
- `tests/test_verify_published.py`
- `tests/test_workflow_triggers.py`
- `tests/workflow_reader.py`
- `tools/refresh_toolchain_lock.py`
- `.github/workflows/ietf-submit-core-02.yml`
- `publication/submission/core-02.json`

The grant also covers the repository-owned configuration in
`tools/toolchain.json`, `tools/python-toolchain.lock`, `tools/node/package.json`,
and the root-project metadata of `tools/node/package-lock.json`. Package entries
in lock files describe dependencies; they do not relicense those dependencies.

The existing scripts, tests and toolchain configuration were introduced and
maintained in this repository's Mikhail Sergeev commit history, including
`cfbf110` (initial public state), `f2c8239` (publication tooling), `7f358bc`
(repository-owned toolchain) and subsequent corrections. The navigation and
submission update extends that repository tooling.

`scripts/draft_bundle.py` is a verbatim copy of the author's shared
`ietf-draft-bundle-v1` tool, version 1.0.0. Its SHA-256 is
`e83753f35bbf54f9ca2e1793b7af5cb47fcb04764acfc77c8f2be7f5327ed51a`.
Its license is recorded here without altering those shared source bytes.

## IETF material and historical records

The tooling grant does **not** cover specification artifacts under `drafts/`,
their renderings, publication manifests, or historical publication records under
`publication/authorizations/`. IETF documents and their Code Components retain
the applicable notices and [IETF Trust provisions](LICENSES/IETF-TRUST.md).
Do not replace those notices with the repository tooling license.

This map does not grant a new general license over other repository prose or
assets. Material outside the explicit tooling scope retains its existing terms;
where no grant is stated, ask before reusing it in a way that needs permission.

## Dependencies and future contributions

Downloaded Python/Node packages, xml2rfc, GitHub Actions, and other third-party
tools retain their own licenses and notices. Their inclusion in a toolchain or
workflow is not a grant by this repository's author. Preserve any applicable
notices when redistributing them.

Identify imported code and its origin in a contribution, preserve its notices,
and update this map when adding separately licensed material. Contributions
that are or become IETF Contributions remain subject to the applicable IETF
rules; the tooling grant does not replace those obligations.
