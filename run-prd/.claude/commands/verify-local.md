---
description: "檢查 local Java changes 的 compile、建議的 targeted tests 與 review readiness。"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(git diff --name-only:*)
  - Bash(ls:*)
  - Bash(test -f:*)
  - Bash(mvn test-compile:*)
  - Bash(./gradlew testClasses:*)
  - Bash(pwd)
---

## 目的

當已經有 code changes 時，用這個 command 準備 local review 與收尾。

## 要做的事

1. 用 `git diff --name-only` 找出 changed files
2. 判斷專案看起來是 Maven-based 還是 Gradle-based
3. 建議合適的 compile 或 test-compile command
4. 根據 changed files、命名、packages 與常見 Java 慣例，建議 targeted tests
5. 提醒使用者在 compile 與 targeted tests 完成後執行 `/review`

不要在沒有說明的情況下憑空編造 test names；若是推測結果，要明講它們是 inferred suggestions。

## Maven / Gradle 判斷

- 如果存在 `pom.xml`，優先使用 Maven commands
- 如果存在 `build.gradle` 或 `build.gradle.kts`，優先使用 Gradle commands
- 如果兩者都存在，就兩者都提到，並根據 repository structure 說明哪個看起來是主要工具

## 輸出格式

只回傳 Markdown，並包含以下區塊：

### Changed Files
- 使用單層 bullet list

### Compile Step
```bash
<command>
```

### Suggested Targeted Tests
- 每個建議 command 各用一個單層 bullet

### Why These Tests
- 使用單層 bullet list

### Review Step
```text
/review
```

### Closure Rule
- 用一小段短文說明：在 compile、targeted tests 與 `/review` 全部完成前，這份工作都不應視為 done。

## Current Request

$ARGUMENTS
