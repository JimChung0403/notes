---
description: Run the PRD-driven development flow: align PRD with codebase, hand off to Superpowers, then verify locally and write back decisions.
allowed-tools: Read, Glob, Grep, Bash(git diff --name-only:*), Bash(ls:*), Bash(test -f:*), Bash(find:*), Bash(pwd)
---

## Purpose

Use this as the main entrypoint when a PM gives you a PRD that already includes:

- what to build
- how it should roughly work
- where changes are expected

This command must turn the PRD into a safe development flow:

1. read PRD
2. align PRD with the actual codebase
3. write a feature brief file
4. stop early if alignment is weak
5. produce a strict handoff for Superpowers
6. remind the user to complete local verification
7. write back implementation deltas into decision notes

## Required Inputs

- `$ARGUMENTS` must point to a PRD file path, or clearly identify the PRD location

## Workflow

### Step 1: Read PRD

Read the PRD and extract:

- feature brief
- business goal
- mentioned classes, methods, modules, DTOs, APIs, configs, or files
- constraints
- acceptance criteria

### Step 2: Read GSD context

If they exist, read:

- `PROJECT.md`
- `ROADMAP.md`
- `STATE.md`
- `.planning/codebase/STACK.md`
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/STRUCTURE.md`
- `.planning/codebase/CONVENTIONS.md`
- `.planning/codebase/TESTING.md`
- `.planning/codebase/INTEGRATIONS.md`
- `.planning/codebase/CONCERNS.md`

Use these as the source of truth for current architecture and known risks.

### Step 3: Align PRD with codebase

Search for the PRD-mentioned symbols and modules.

Produce an `alignment_report` with:

- PRD assumptions that match the codebase
- PRD assumptions that appear outdated
- likely affected files or callers that PRD did not mention
- likely tests that should be touched

If alignment is weak or unclear, stop and return the mismatch summary instead of proceeding.

### Step 4: Write feature brief file

Write or update:

- `docs/feature-briefs/<PRD-ID>.md`

If no PRD ID is obvious, derive a stable filename from the PRD filename.

The feature brief file must include:

- feature brief
- business goal
- actual change scope
- constraints
- acceptance criteria
- context files
- alignment report summary
- open questions

### Step 5: Decide whether implementation can start

Only proceed if all of the following are true:

- feature brief is clear enough
- codebase alignment is acceptable
- there are no blocking open questions
- a Superpowers handoff can be constructed

### Step 6: Produce Superpowers handoff

If implementation can start, output a strict handoff with:

```yaml
feature_brief: <summary>
feature_brief_file: docs/feature-briefs/<PRD-ID>.md
context_files:
  - PROJECT.md
  - ROADMAP.md
  - STATE.md
  - .planning/codebase/STACK.md
  - .planning/codebase/ARCHITECTURE.md
  - .planning/codebase/STRUCTURE.md
  - .planning/codebase/CONVENTIONS.md
  - .planning/codebase/TESTING.md
  - .planning/codebase/INTEGRATIONS.md
  - .planning/codebase/CONCERNS.md
constraints:
  - <constraint>
acceptance_criteria:
  - <criterion>
expected_output:
  - implementation_plan
  - task_list
  - test_strategy
```

And include this exact instruction:

```text
Before planning or implementation, read all context_files first.
Use GSD files as the source of truth for architecture, conventions,
testing approach, integrations, and known concerns.
Do not start implementation planning until these files are read.
```

### Step 7: Remind downstream verification

After implementation, the expected next steps are:

- `/impact`
- compile or test-compile
- targeted tests
- `/review`

### Step 8: Writeback expectations

At completion, write implementation deltas to:

- `STATE.md`
- `DECISIONS.md` if available

The writeback should capture:

- PRD originally claimed X
- actual implementation required Y
- reason for the delta
- missing callers, tests, or dependencies that PRD did not include

## Output Format

Return only Markdown with these sections:

### PRD Summary
- flat bullet list

### Alignment Report
- flat bullet list

### Blocking Issues
- flat bullet list, or `none`

### Can Proceed
- `yes` or `no`

### Feature Brief File
- `docs/feature-briefs/<PRD-ID>.md`

### Superpowers Handoff
```yaml
<handoff yaml or none>
```

### Next Steps
- flat bullet list

## Current Request

$ARGUMENTS
