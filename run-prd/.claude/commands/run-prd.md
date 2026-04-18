---
description: "執行 PRD-driven 開發流程：先讓 PRD 與 codebase 對齊，再 hand off 給 Superpowers，最後做 local verification 與 writeback。"
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

當 PM 給你一份已經包含以下資訊的 PRD 時，把這個 command 當成主入口：

- 要做什麼
- 大致怎麼做
- 預期要改哪裡

這個 command 必須把 PRD 轉成一條安全的開發流程：

1. 讀取 PRD
2. 讓 PRD 與實際 codebase 對齊
3. 寫出 feature brief file
4. 如果對齊不足就提早停止
5. 產出給 Superpowers 的嚴格 handoff
6. 提醒使用者完成 local verification
7. 把 implementation delta 回寫到 decision notes

## 必要輸入

- `$ARGUMENTS` 必須指向一個 PRD file path，或能清楚辨識 PRD 的位置

## 流程

### Step 1: 讀取 PRD

讀取 PRD，並萃取：

- feature brief
- business goal
- PRD 提到的 classes、methods、modules、DTOs、APIs、configs 或 files
- constraints
- acceptance criteria

### Step 2: 讀取 GSD context

如果存在，就讀取：

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

把這些檔案當成目前 architecture 與已知風險的 source of truth。

### Step 3: 讓 PRD 與 codebase 對齊

搜尋 PRD 提到的 symbols 與 modules。

產出一份 `alignment_report`，內容包含：

- 與 codebase 相符的 PRD assumptions
- 看起來已過時的 PRD assumptions
- PRD 沒提到、但可能會受影響的 files 或 callers
- 可能需要一起調整的 tests

如果對齊結果偏弱或不清楚，就停止，回傳 mismatch summary，不要直接往下做。

### Step 4: 寫出 feature brief file

建立或更新：

- `docs/feature-briefs/<PRD-ID>.md`

如果看不出明確的 PRD ID，就從 PRD filename 推導一個穩定的檔名。

如果存在：

- `templates/feature-brief.template.md`

優先依照這個 template 的結構建立 `docs/feature-briefs/<PRD-ID>.md`。

feature brief file 必須包含：

- feature brief
- business goal
- actual change scope
- constraints
- acceptance criteria
- context files
- alignment report summary
- open questions

### Step 5: 判斷能不能開始 implementation

只有在以下條件都成立時，才能往下：

- feature brief 足夠清楚
- codebase alignment 可以接受
- 沒有會阻塞的 open questions
- 可以組出完整的 Superpowers handoff

### Step 6: 產出 Superpowers handoff

如果可以開始 implementation，就輸出一份嚴格的 handoff：

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

並且包含以下這段固定指令：

```text
Before planning or implementation:
1. Read feature_brief_file first.
2. Then read all context_files.
Use the feature brief as the primary implementation scope.
Use GSD files as the source of truth for architecture, conventions,
testing approach, integrations, and known concerns.
Do not start implementation planning until feature_brief_file and all context_files are read.
```

### Step 7: 提醒後續 verification

implementation 完成後，預期下一步是：

- `/impact`
- compile or test-compile
- targeted tests
- `/review`

### Step 8: 定義 writeback 內容

完成後，把 implementation delta 回寫到：

- `STATE.md`
- `DECISIONS.md` if available

writeback 應至少記錄：

- PRD 原本宣稱的內容
- 實際 implementation 需要調整的內容
- 產生 delta 的原因
- PRD 沒列出的 callers、tests 或 dependencies

## 輸出格式

只回傳 Markdown，且包含以下區塊：

### PRD Summary
- 使用單層 bullet list

### Alignment Report
- 使用單層 bullet list

### Blocking Issues
- 使用單層 bullet list，或寫 `none`

### Can Proceed
- `yes` or `no`

### Feature Brief File
- `docs/feature-briefs/<PRD-ID>.md`

### Superpowers Handoff
```yaml
<handoff yaml or none>
```

### Next Steps
- 使用單層 bullet list

## Current Request

$ARGUMENTS
