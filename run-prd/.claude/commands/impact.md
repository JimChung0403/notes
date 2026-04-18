---
description: "為目前的 Java CLI 專案執行 pre-change impact analysis 或 post-change impact verification。"
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

## 目的

用這個 command 在 coding 前分析可能的 impact 範圍，或在 coding 後驗證是否有漏改。

## 模式判斷

- 如果 `git diff --name-only` 為空，執行 **pre-change impact analysis**
- 如果 `git diff --name-only` 非空，執行 **post-change impact verification**

## 要做的事

### Pre-change impact analysis

1. 根據需求辨識可能會變動的 symbols、modules、classes、methods、interfaces、DTOs 或 tests。
2. 用 repository search 找出：
   - usages
   - callers
   - DTO 或 interface 的 consumers
   - 可能受影響的 tests
3. 回傳精簡的 impact summary。

### Post-change impact verification

1. 從 `git diff --name-only` 讀取目前的 changed files
2. 推論可能變動的 classes、methods、interfaces、DTOs 或 modules
3. 搜尋：
   - 相關但尚未更新的 usages
   - 可能應該一起執行的 tests
   - 可能也需要更新的 callers 或 consumers
4. 回傳可能漏改的區域。

## 建議的搜尋方式

使用這類 repository search patterns：

- class names
- method names
- interface names
- DTO names
- package names

優先使用精簡、以 grep 為主的證據。

## 輸出格式

只回傳 Markdown，並包含以下區塊：

### Mode
- `pre-change` or `post-change`

### Changed Files
- 如果有就列出 files，否則寫 `none`

### Likely Impact Areas
- 使用單層 bullet list

### Likely Related Tests
- 使用單層 bullet list

### Possible Missed Changes
- 使用單層 bullet list

### Recommended Next Step
- 一小段短文

## Current Request

$ARGUMENTS
