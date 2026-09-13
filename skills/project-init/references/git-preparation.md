# Preparing a commit or push

## Establish the scope

Inspect `git status`, branch/upstream, existing staged changes, and the requested
files. A `.git` path alone does not prove a valid repository. Use the read-only
helper with `check PATH --for-commit`; add `--profile existing` when the task
does not require a full documentation structure.

If the repository or remote is missing, report the exact gap. Documentation work
can still be completed. Do not invent a remote or publish a new repository to
solve a missing URL.

The helper records the enclosing repository as `git.root`, but scans only the
requested target. Staged paths are target-relative. A subproject's report does
not certify the rest of the repository. An empty index means there is no staged
commit to review; no remote is required for a local commit.

## Prepare

1. Reconcile the README, AGENTS.md, affected docs, and Unreleased against actual
   changes. Preserve published history and established version rules.
2. Run relevant declared checks and record their results. Detecting a command is
   not the same as running it successfully.
3. Inspect intended changes and file links. Exclude caches, credentials, generated
   local state, and unrelated changes according to project rules.
4. If a commit was requested, stage intended paths and inspect the exact staged
   diff. Run the helper again; its staged scan reads the Git index rather than
    assuming the current working tree matches it.
5. Commit/push only within the user's requested scope. Respect existing approval
   and branch policies without asking for the same authorization again.

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
any concrete repository/remote issue. A passed structural check does not by
itself mean a repository is ready for publication.
