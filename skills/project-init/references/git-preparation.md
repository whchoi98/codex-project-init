# Preparing a commit or push

## Establish the scope

Inspect `git status`, branch/upstream, existing staged changes, and the requested
files, using current evidence already available. A `.git` path alone does not
prove a valid repository. Select checks with [verification scope and reuse](verification.md).
This workflow is for explicitly requested documentation preparation; an ordinary
commit/push request does not start it automatically.

If the repository or remote is missing, report the exact gap. Documentation work
can still be completed. Do not invent a remote or publish a new repository to
solve a missing URL.

The helper records the enclosing repository as `git.root`, but scans only the
requested target. Staged paths are target-relative. A subproject's report does
not certify the rest of the repository. An empty index means there is no staged
commit to review; no remote is required for a local commit.

## Prepare

1. Map actual changes to affected documentation. Read the [README](readme.md) or
   [CHANGELOG](changelog.md) guide only when that document needs authoring.
   Preserve structure and history; do not reopen every document for unchanged code.
2. Check existing implementation-test and review results against their current
   inputs. Reuse valid evidence. The primary development/CI workflow executes
   missing required checks once; Project Init does not start a parallel tester
   or code reviewer. Ordinary prose edits need documentation checks, not the
   application suite. Detecting a command is not evidence that it ran.
3. Inspect intended changes and file links. Exclude caches, credentials, generated
   local state, and unrelated changes according to project rules.
4. If a commit was requested, stage intended paths and inspect the exact staged
   diff. Run one final `check PATH --profile existing --for-commit` for the current
   state (use core only if full documentation structure is required). The report
   includes project observations, document checks, and index findings, so another
   `inspect` or duplicate audit is unnecessary. If staging was not authorized,
   inspect the existing index and describe any difference from authored files.
5. Commit/push only within the user's requested scope. Respect existing approval
   and branch policies without asking for the same authorization again.
   A subsequent Git-only step does not invalidate tests whose inputs are unchanged.

The helper's staged checks recognize private-key headers, AWS access-key IDs,
GitHub token shapes, and credential-oriented filenames. It reports paths/rules,
never matching values. This is a narrow preflight, not a full secret scanner.
Use an established repository scanner when present.

Check `scan.complete` and skipped blobs. The helper disables executable Git
filters and hooks during its observations; it does not modify Git configuration.
Its whitespace result can differ from a repository's filter-normalized content,
so review the exact staged content before an authorized commit.

## Hooks and attribution

Do not install hooks or change `core.hooksPath` as a side effect of writing docs.
If hooks are requested, inspect existing hooks, preserve their behavior, and
verify the proposed integration with sample events or a temporary Git repo.

Follow explicit project attribution rules when writing commit messages. Do not
silently install the original Claude template's blanket trailer-removal hook:
it can remove human co-author attribution too.

## Handoff

Provide the changed paths, actual validation results, staged-change status, and
any concrete repository/remote issue. Distinguish new executions, reused results,
unneeded checks, and unverified requirements. A passed structural check does not by
itself mean a repository is ready for publication.
