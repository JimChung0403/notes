---
description: "Run pre-change impact analysis or post-change impact verification for the current Java CLI project."
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(git diff --name-only:*)
  - Bash(ls:*)
  - Bash(test -f:*)
  - Bash(find:*)
  - Bash(pwd)
---

## Purpose

Use this command to analyze likely impact areas before coding, or verify possible missed changes after coding.

## Mode Detection

- If `git diff --name-only` is empty, do **pre-change impact analysis**
- If `git diff --name-only` is non-empty, do **post-change impact verification**

## What To Do

### Pre-change impact analysis

1. Identify the likely changed symbols, modules, classes, methods, interfaces, DTOs, or tests based on the request.
2. Use repository search to find:
   - usages
   - callers
   - DTO or interface consumers
   - likely affected tests
3. Return a concise impact summary.

### Post-change impact verification

1. Read current changed files from `git diff --name-only`
2. Infer likely changed classes, methods, interfaces, DTOs, or modules
3. Search for:
   - related usages not updated
   - tests that should probably be run
   - callers or consumers that might also require updates
4. Return likely missed areas.

## Suggested Search Style

Use repository search patterns such as:

- class names
- method names
- interface names
- DTO names
- package names

Prefer concise grep-driven evidence.

## Output Format

Return only Markdown with these sections:

### Mode
- `pre-change` or `post-change`

### Changed Files
- list files if any, otherwise `none`

### Likely Impact Areas
- flat bullet list

### Likely Related Tests
- flat bullet list

### Possible Missed Changes
- flat bullet list

### Recommended Next Step
- one short paragraph

## Current Request

$ARGUMENTS
