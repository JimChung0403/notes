---
description: Verify local Java changes by checking compile, suggested targeted tests, and review readiness.
allowed-tools: Read, Glob, Grep, Bash(git diff --name-only:*), Bash(ls:*), Bash(test -f:*), Bash(mvn test-compile:*), Bash(./gradlew testClasses:*), Bash(pwd)
---

## Purpose

Use this command after code changes exist to prepare for local review and closure.

## What To Do

1. Detect changed files with `git diff --name-only`
2. Decide whether the project looks Maven-based or Gradle-based
3. Recommend the appropriate compile or test-compile command
4. Suggest targeted tests based on changed files, names, packages, and common Java conventions
5. Remind the user to run `/review` after compile and targeted tests

Do not invent test names without explaining that they are inferred suggestions.

## Maven / Gradle Detection

- If `pom.xml` exists, prefer Maven commands
- If `build.gradle` or `build.gradle.kts` exists, prefer Gradle commands
- If both exist, mention both and say which one appears primary based on repository structure

## Output Format

Return only Markdown with these sections:

### Changed Files
- flat bullet list

### Compile Step
```bash
<command>
```

### Suggested Targeted Tests
- one flat bullet per suggested command

### Why These Tests
- flat bullet list

### Review Step
```text
/review
```

### Closure Rule
- one short paragraph stating that work should not be considered done until compile, targeted tests, and `/review` have all been completed.

## Current Request

$ARGUMENTS
