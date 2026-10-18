# Handling external issues

Every substantive report should lead to a publicly checkable disposition:
the question understood, the editorial decision, the resulting change or
reason for no change, the checks performed, and the publication status.
This process complements [CONTRIBUTING.md](CONTRIBUTING.md) and
[PUBLICATION-PROCESS.md](PUBLICATION-PROCESS.md).

## Bringing a question

An issue or an email to the editor is sufficient. A patch, implementation,
GitHub account, or agreement with the editor is not required. Identify the
draft revision and section when possible, describe the ambiguity or problem,
and give an example or public reference if useful. The editor can help refine
an incomplete report. Do not publish private correspondence or sensitive
evidence without permission; use a public source or an agreed safe summary.

## Response and triage

The editor aims to acknowledge a substantive report within two working days
and provide an initial disposition or next step within five working days.
These are local service targets, not IETF requirements. If more time is needed,
state the reason and the next review point. Keep the burden on the editor,
rather than requiring the reporter to produce a patch.

Record the following in the issue body or a durable conversation comment;
labels are optional conveniences, not a substitute for the record:

- Type: editorial, technical, or process; the affected revision and section.
- Owner and next action; needs-info or in-review when applicable.
- The understood problem and evidence, distinguishing author reports,
  text review, executed tests, and independently obtained observations.
- Decision: accepted, partly accepted, deferred, declined, or duplicate,
  with reasons and any unresolved disagreement. Acceptance of a need does
  not automatically accept the proposed wording.

Acceptance, incorporation in a particular working commit, and publication
are distinct events. Do not use an accepted decision as proof of either
incorporation or publication.

## Reviewing a change

Use a focused pull request and connect it with a plain `Related to #N`
reference while discussion or review is outstanding. Avoid automatic closing
keywords and GitHub Development links until automatic closure is intended;
merging a linked PR into the default branch can close an issue.

State what changes, why, the exact reviewed source or commit, and meaningful
checks with their limits. Include a counterexample or small reading case when
it helps resolve a technical distinction. A passing build is not a semantic,
conformance, interoperability, or IETF approval result. Keep substantive
reasoning in the issue or a stable linked document, not only in inline PR
comments that may become outdated.

Invite the reporter to assess whether the proposed text addresses the problem.
For a routine ready-to-review change, five working days is a useful default
feedback window; state a different window when appropriate. Silence is not
agreement. After the stated window, the editor may make a reasoned decision
with objections preserved; an individual draft does not require an indefinite
reporter veto. Do not automatically close issues for inactivity.

Keep discussion accessible by email. For substantive technical changes that
need the relevant IETF community's consideration, provide a concise public
mailing-list summary with stable issue/PR links and remaining questions.
GitHub activity does not replace the applicable IETF discussion and consensus
process. Avoid duplicate routine notifications across every channel.

## Disposition and closure

Before closing an issue, add a durable disposition recording:

1. The problem and the accepted resolution, or a reasoned non-change decision.
2. The exact public incorporation commit and affected sections, if changed.
3. The checks actually performed, their scope, and unresolved limitations.
4. Remaining work, with a link and owner when it is tracked separately.
5. Whether the change is only in working text or in a specific posted I-D.

For a declined, deferred, duplicate, or out-of-scope report, explain the reason
and give the relevant destination or reconsideration condition where one exists.
A deferred item may stay open; closure must not imply that it was fixed.
Reopen a report when new evidence materially challenges its disposition.
Issue closure does not establish contributor endorsement, IETF consensus,
implementation behavior, or an IETF publication event.

## Repository role

This is a repository of published specification states. Public issues are
welcome even though pre-publication development is maintained separately.
Do not put a future manuscript into `drafts/core/NN/` as an issue-handling
shortcut or rewrite the bytes of a posted revision.

Public repository documentation, integrity tooling, and project-maintained
known-issue notes can be corrected through focused PRs. Known-issue notes
record the project's assessment; they are not RFC Editor errata and do not
amend the published draft. Distinguish correcting such a note from correcting
the specification itself.

For a specification change developed elsewhere, publish the technical
disposition and track the intended future revision here. An inaccessible
private commit is not a publicly checkable fix and is not sufficient to close
the report as fixed. Record the publicly inspectable resolution and exact
incorporation/publication locator when available; until then, keep the issue
open or use an explicit non-fixed disposition with its rationale.

Use [SECURITY.md](SECURITY.md) for vulnerability reports. Non-sensitive draft
feedback can also be sent to [the editor](mailto:mikhailsergeev369@gmail.com).

## Attribution and automation

Preserve attribution for substantive contributions and update acknowledgments
where appropriate. Attribution does not imply endorsement or confer authorship.
Do not add an extra CLA or signed editorial approval form to this workflow;
the contribution terms in CONTRIBUTING.md continue to apply.

Ordinary checks should use read-only permissions and no submission credentials.
Do not execute untrusted pull-request code in a privileged workflow, including
through an unsafe use of `pull_request_target`. Issue handling does not authorize
submission, release, tag changes, or a change to frozen publication artifacts.

## Basis

This local workflow draws on [RFC 8874](https://www.rfc-editor.org/rfc/rfc8874.html)
for GitHub and IETF discussion boundaries, [RFC 7282](https://www.rfc-editor.org/rfc/rfc7282.html)
for addressing substantive objections, and
[GitHub's issue-linking behavior](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue).
It does not turn an individual draft into a working-group document or claim
working-group consensus. Follow the upstream project's process when working
on a fork; this policy does not govern its upstream repository.
