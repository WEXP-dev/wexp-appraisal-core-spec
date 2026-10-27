# Repository location

On 27 October 2026 the existing repository was renamed from
`WEXP-dev/wexp-spec` to `WEXP-dev/wexp-appraisal-core-spec`.
Its GitHub repository ID remains `1331243525`. This is a location and naming
change, not a replacement repository or a new specification revision.

## Canonical references

Use [wexp-appraisal-core-spec](https://github.com/WEXP-dev/wexp-appraisal-core-spec)
for current repository navigation. Internet-Draft names, document titles,
semantic-version identifiers and normative artifact paths are unchanged.
[Core-02](https://datatracker.ietf.org/doc/draft-sergeev-wexp-core/02/)
and [Coverage-00](https://datatracker.ietf.org/doc/draft-sergeev-wexp-coverage/00/)
remain separate individual Internet-Drafts.

Existing local clones can update their remote without recloning:

```sh
git remote set-url origin https://github.com/WEXP-dev/wexp-appraisal-core-spec.git
```

Run this only inside a clone of this repository. Do not change another
repository's remote.

## Preserve historical identities

Do not replace the old location in frozen manuscripts, manifests, provenance,
publication records, historical packages or revision-specific submission
configuration. Those references identify their original state. Current
navigation can use the new location without rewriting archived evidence.

The post-rename source observation at
`a75dc837dd743ce988da52472757ce4c2684eb1c` retained these Git subtree identities:

| Subtree | Git tree SHA |
|---|---|
| `drafts` | `17c05ec57db874f711eeb41bc8e951aea3659226` |
| `manifests` | `7b7e517d9f92419a3480bd17699ad4a8745de6c8` |
| `provenance` | `3a18cecff51125f7c20bcaaa64e66cf8b65c4ffd` |
| `publication` | `90f78fc2f6d0d93ebb6f2214f1246251c1827e0f` |

The tag `draft-sergeev-wexp-core-02` still points to
`09ed22f65c3c8af97d58c6ab1dda86202afa154d`; its release ID is `422500492`.
This observation checks preservation of Git identities, not a fresh comparison
of all bytes against the IETF archive.

## Submission safety

Core-02 is already posted. Do not rerun its submission, move its tag or recreate
its release as a rename test. Its historical live-submission guard remains
bound to the former name and is not broadened to authorize another submission.
The manual-only read-only preview accepts the stable repository ID and either
location; it still cannot submit. Future revisions require their own reviewed
configuration and authorization.

## Redirects and limits

The old public repository and release pages resolved to the new location during
the 27 October check. The old raw README URL remained readable; the old API tree
URL returned a permanent redirect to the same numeric repository identity.
A local Git clone/fetch check was not performed in that observation.

Do not create another repository under the old name: it would break GitHub's
redirects. See [GitHub's rename guidance](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository)
for Git operations and the GitHub Pages/hosted Actions exceptions. The observed
repository metadata had `has_pages: false`. This record does not establish the
state of every external integration or local clone.
