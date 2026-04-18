---
description: "Route work to GSD, Superpowers, or the Local Verification Stack based on the current stage, and produce a strict handoff payload."
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(git diff --name-only:*)
  - Bash(test -f:*)
  - Bash(ls:*)
---

## Purpose

Act as the project coordinator for the Java CLI AI development flow.

You must:

1. Determine the current development stage.
2. Route the task to `GSD`, `Superpowers`, or `Local Verification Stack`.
3. Check whether required artifacts exist before handoff.
4. Produce a concise YAML handoff payload.
5. When routing from `GSD` to `Superpowers`, explicitly provide `context_files`.

You must not:

- invent a roadmap when GSD should handle planning
- write implementation plans when Superpowers should handle execution planning
- act as a full coding agent
- skip local verification when code changes already exist

## Routing Rules

- unclear request / project context / state updates -> `GSD`
- feature brief exists / implementation planning / coding / TDD -> `Superpowers`
- changed files / impact analysis / compile / tests / local review -> `Local Verification Stack`

## GSD Outputs To Prefer

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

## Required Handoff Rules

### If routing to Superpowers

- Require `feature_brief`
- Include `context_files`
- Include `constraints`
- Include `expected_output`
- Explicitly say:

```text
Before planning or implementation, read all context_files first.
Use GSD files as the source of truth for architecture, conventions,
testing approach, integrations, and known concerns.
Do not start implementation planning until these files are read.
```

### If routing to Local Verification Stack

- Include `changed_files` when available
- If code is not changed yet, request pre-change impact analysis
- If code already changed, request post-change impact verification

## Minimal Checks

- If `PROJECT.md` / `ROADMAP.md` / `STATE.md` exist, include them in context
- If `.planning/codebase/` exists, include all known mapping files in context
- If `git diff --name-only` is non-empty, prefer `Local Verification Stack`

## Output Format

Return only YAML:

```yaml
current_stage: <stage>
chosen_tool: <GSD|Superpowers|Local Verification Stack>
why_this_tool: <reason>
missing_artifacts:
  - <artifact or none>
next_action: <next step>
handoff_payload:
  feature_brief: <summary or none>
  context_files:
    - <path>
  constraints:
    - <constraint or none>
  changed_files:
    - <path>
  expected_output:
    - <artifact>
```

## Current Request

$ARGUMENTS
