# Agent Skills Frontmatter 相容性研究報告

日期: 2026-04-13

## 結論摘要

這次研究的核心結論有三個:

1. `model:` 不是 Agent Skills 開放標準的通用 `SKILL.md` key。它是 Claude Code 在 skills 上額外加的擴充欄位。
2. `path:` 也不是通用的 `SKILL.md` frontmatter key。你看到的 `path`，在 Codex 官方文件中是寫在 `~/.codex/config.toml` 的 `[[skills.config]]` 設定裡，用來指向某個 skill 的 `SKILL.md` 路徑。
3. Skills 不是 Claude Code 專屬。Claude Code、Codex、OpenCode 都使用或相容於 Agent Skills 這個 open standard，但三者支援的 metadata 範圍不完全相同。

如果你的目標是「一份 skill 同時盡量相容 Claude Code、Codex、OpenCode」，最保守的寫法是:

```yaml
---
name: your-skill-name
description: Explain what the skill does and when it should be used.
---
```

如果還要多寫一些可攜 metadata，可優先考慮:

```yaml
---
name: your-skill-name
description: Explain what the skill does and when it should be used.
license: MIT
compatibility: Requires git and network access.
metadata:
  author: your-team
  version: "1.0"
---
```

`model:`、`paths:`、`context:`、`agent:`、`hooks:` 這些就要視產品而定，不應假設所有實作都會吃。

## 研究範圍

本報告分三層來看:

1. Agent Skills 開放標準本身定義了什麼
2. Claude Code 在標準之上額外擴充了什麼
3. Codex 與 OpenCode 官方目前明確文件化支援哪些欄位

另外，因為你特別問到 `model:` 與 `path:`，我把「不是寫在 `SKILL.md` frontmatter，而是寫在別的設定檔」的東西獨立列出。

## 一、Open Agent Skills 標準 key

根據 Agent Skills specification，`SKILL.md` 必須先有 YAML frontmatter，再接 markdown 內容。標準 frontmatter 目前定義如下:

| Key | 是否必填 | 用途 | 備註 |
| --- | --- | --- | --- |
| `name` | 必填 | skill 識別名稱 | 1-64 字元，小寫英數與連字號，且要與資料夾名稱一致 |
| `description` | 必填 | 描述 skill 做什麼、何時使用 | agent 會用它來判斷是否應該觸發這個 skill |
| `license` | 選填 | skill 授權資訊 | 可以是 license 名稱或指向 bundled license 檔 |
| `compatibility` | 選填 | 說明環境需求 | 例如適用產品、依賴套件、是否需要網路 |
| `metadata` | 選填 | 任意 key-value metadata | 標準允許額外附加字串型 metadata |
| `allowed-tools` | 選填 | skill 可預先核准使用的工具 | 標準標示為 experimental，不同實作支援度可能不同 |

### 每個標準 key 的用途

#### `name`

- 用來識別 skill。
- 通常也會成為 UI 上的 skill 名稱或命令名稱。
- 標準要求它和資料夾名一致，所以不建議用別名或顯示名來取代真正的 skill id。

#### `description`

- 這是最重要的欄位之一。
- 不只是在說明 skill 功能，也是在告訴 agent「什麼情境下應該選用這個 skill」。
- 如果 `description` 寫得太模糊，agent 就可能不會觸發，或誤觸發。

#### `license`

- 用來標示 skill 的授權資訊。
- 對團隊內部共用或外部分享很有用，但對觸發行為本身沒有直接影響。

#### `compatibility`

- 用來描述 skill 的執行前提。
- 常見寫法會包含: 「Designed for Claude Code」、需要 `git` / `docker` / `jq`、需要網路、需要 Python 版本等。
- 這個欄位不是控制邏輯，而是告訴使用者或 agent 這個 skill 的適用環境。

#### `metadata`

- 用來放額外資訊，不是核心調度欄位。
- 例如作者、版本、團隊、領域、workflow 類型等。
- 標準把它定義成任意 key-value mapping。

#### `allowed-tools`

- 用來宣告 skill 需要預先核准哪些工具。
- 標準有定義，但明確標註為 experimental。
- 這代表「標準有這欄」不等於「所有客戶端都完整支援」。

## 二、Claude Code 額外支援的 `SKILL.md` frontmatter

Claude Code 官方明講它遵循 Agent Skills open standard，但又在其上加入額外功能，例如 invocation control、subagent execution、dynamic context injection。這些額外欄位如下:

| Key | 用途 | 代表性效果 |
| --- | --- | --- |
| `name` | 顯示名稱；省略時用資料夾名 | 同時會影響 slash command 名稱 |
| `description` | 說明 skill 做什麼、何時用 | Claude 會用它判斷是否載入 |
| `argument-hint` | 顯示參數提示 | 例如 `[issue-number]` |
| `disable-model-invocation` | 禁止 Claude 自動觸發 | 只能手動 `/name` 使用 |
| `user-invocable` | 是否顯示在 `/` 選單 | `false` 代表隱藏，但仍可被 Claude 內部用 |
| `allowed-tools` | skill 啟用時可無需另問直接使用的工具 | 可寫成空白分隔字串或 YAML list |
| `model` | skill 啟用時要用哪個模型 | 這就是你看到的 `model:` 來源 |
| `effort` | skill 啟用時的推理 effort | 覆蓋 session 的 effort |
| `context` | skill 是否在 forked subagent context 執行 | 目前文件提到 `fork` |
| `agent` | 指定 `context: fork` 時用哪個 subagent type | 和 subagent 搭配 |
| `hooks` | skill 生命週期 hooks | 用於技能執行期間的掛鉤 |
| `paths` | 用檔案路徑 pattern 限制自動觸發範圍 | 是 `paths:`，不是 `path:` |
| `shell` | 指定 skill 內 `!` 命令區塊使用的 shell | `bash` 或 `powershell` |

### 你問的兩個重點

#### `model:`

- Claude Code 有官方記載。
- 用途是「當這個 skill 啟用時，切換使用指定模型」。
- 這不是 open standard 通用欄位。

#### `path:` / `paths:`

- Claude Code 官方文件中是 `paths:`，不是 `path:`。
- 用途是用 glob patterns 限制這個 skill 只會在某些檔案路徑工作時自動載入。
- 它控制的是自動啟用範圍，不是 skill 位置。

## 三、OpenCode 官方目前明確支援什麼

OpenCode 官方 skills 文件寫得很直接: `SKILL.md` 只認以下 frontmatter 欄位:

- `name`
- `description`
- `license`
- `compatibility`
- `metadata`

未知欄位會被忽略。

這有兩個很重要的解讀:

1. `model:` 不是 OpenCode 官方技能 frontmatter。
2. `path:` 或 `paths:` 也不是 OpenCode 官方技能 frontmatter。

OpenCode 另外一個值得注意的點是，它會掃描:

- `.opencode/skills/...`
- `.claude/skills/...`
- `.agents/skills/...`

這代表它刻意做了和 Claude / agent skills 生態相容的 discovery，但並沒有承諾接受 Claude Code 的所有擴充欄位。

## 四、Codex 官方目前明確支援什麼

Codex 官方 skills 文件目前明確寫到:

- Skills 建立在 open agent skills standard 上
- `SKILL.md` 必須包含 `name` 與 `description`
- Codex 也會讀取 skill 的 file path 與 `agents/openai.yaml` 中的 optional metadata

Codex 文件中沒有像 Claude Code 那樣列出一張完整的 `SKILL.md` frontmatter 參考表，因此目前最穩妥的理解是:

1. 官方明確保證的 `SKILL.md` 最低欄位是 `name` 與 `description`
2. 額外 metadata 主要是透過 `agents/openai.yaml` 來做，不是全部塞進 `SKILL.md`
3. 雖然 Codex 說它建立在 open agent skills standard 上，但對 `license`、`compatibility`、`metadata`、`allowed-tools` 在 Codex 內的完整處理方式，skills 頁面沒有逐欄保證

### Codex 的 `agents/openai.yaml`

Codex 的 skill 旁邊可放 `agents/openai.yaml`，目前文件列出的欄位如下:

#### `interface`

- `display_name`: 使用者看到的名稱
- `short_description`: 使用者看到的簡短說明
- `icon_small`: 小圖示
- `icon_large`: 大圖示
- `brand_color`: 品牌色
- `default_prompt`: 這個 skill 常用的包裝 prompt

#### `policy`

- `allow_implicit_invocation`: 是否允許 Codex 依照 prompt 自動隱式觸發 skill

#### `dependencies`

- `tools`: 宣告 skill 依賴的工具，例如某個 MCP server

也就是說，在 Codex 生態裡，如果你想設定較多「產品層」資訊，正規做法不是往 `SKILL.md` 加一堆自訂 key，而是另外加 `agents/openai.yaml`。

## 五、`model` 與 `path` 在 Codex 裡真正出現在哪裡

你問到 `model:xxxx`、`path: xxx`，這兩個字在 Codex 裡確實都出現，但不是出現在同一個地方。

### 1. `path`

Codex skills 文件中的 `path` 出現在:

```toml
[[skills.config]]
path = "/path/to/skill/SKILL.md"
enabled = false
```

這是在 `~/.codex/config.toml` 裡控制 skill 啟用/停用的設定，不是 `SKILL.md` frontmatter。

### 2. `model`

Codex 的 `model` 出現在 custom subagent 的 TOML 設定，不是 skill 的 `SKILL.md`。官方文件列出的 optional fields 包含:

- `model`
- `model_reasoning_effort`
- `sandbox_mode`
- `mcp_servers`
- `skills.config`

所以如果你在 Codex 生態看到 `model = ...`，要先判斷你看到的是不是 `.codex/agents/*.toml` 這一類 subagent 設定檔，而不是 skill 定義本身。

## 六、相容性總表

下面這張表用「官方文件是否明確記載」做區分。

| Key | Agent Skills 標準 | Claude Code | OpenCode | Codex |
| --- | --- | --- | --- | --- |
| `name` | 有 | 有 | 有 | 有 |
| `description` | 有 | 有 | 有 | 有 |
| `license` | 有 | 標準層有，但 Claude 頁面未逐欄列出 | 有 | 標準層有，但 Codex skills 頁面未逐欄列出 |
| `compatibility` | 有 | 標準層有，但 Claude 頁面未逐欄列出 | 有 | 標準層有，但 Codex skills 頁面未逐欄列出 |
| `metadata` | 有 | 標準層有，但 Claude 頁面未逐欄列出 | 有 | Codex 另有 `agents/openai.yaml` optional metadata；`SKILL.md` 層面未逐欄列出 |
| `allowed-tools` | 有，experimental | 有 | 文件未列，未知欄位忽略 | skills 頁面未列，不能當成 Codex 官方保證 |
| `argument-hint` | 無 | 有 | 無 | 無官方記載 |
| `disable-model-invocation` | 無 | 有 | 無 | 無官方記載 |
| `user-invocable` | 無 | 有 | 無 | 無官方記載 |
| `model` | 無 | 有 | 無 | `SKILL.md` 無官方記載；subagent TOML 有 |
| `effort` | 無 | 有 | 無 | `SKILL.md` 無官方記載 |
| `context` | 無 | 有 | 無 | `SKILL.md` 無官方記載 |
| `agent` | 無 | 有 | 無 | `SKILL.md` 無官方記載 |
| `hooks` | 無 | 有 | 無 | `SKILL.md` 無官方記載 |
| `paths` | 無 | 有 | 無 | `SKILL.md` 無官方記載 |
| `shell` | 無 | 有 | 無 | `SKILL.md` 無官方記載 |
| `path` | 無 | 無 | 無 | 不是 `SKILL.md` key；出現在 `config.toml` 的 `skills.config` |

## 七、實務建議

### 如果你要做「三家都盡量能吃」的 skill

請只依賴這些:

- `name`
- `description`
- `license`
- `compatibility`
- `metadata`

其中真正最保險的是:

- `name`
- `description`

### 如果你只打算給 Claude Code 用

可以合理使用這些進階欄位:

- `model`
- `effort`
- `disable-model-invocation`
- `user-invocable`
- `allowed-tools`
- `context`
- `agent`
- `paths`
- `hooks`
- `shell`

### 如果你主要是給 Codex 用

建議拆成三個層次:

1. `SKILL.md` 只寫標準與最小必要欄位
2. `agents/openai.yaml` 補 UI、policy、dependencies
3. `.codex/agents/*.toml` 才去管 subagent 的 `model`、`model_reasoning_effort`、sandbox 等

這樣資訊分層會最清楚，也最符合 Codex 目前文件的設計方式。

## 八、最終判斷

如果你問的是:

「在 `SKILL.md` 最上面，到底總共有哪一些 key 可以寫？」

最嚴謹的答案是:

- 從 open standard 看: `name`、`description`、`license`、`compatibility`、`metadata`、`allowed-tools`
- 從 Claude Code extension 看: 再加上 `argument-hint`、`disable-model-invocation`、`user-invocable`、`allowed-tools`、`model`、`effort`、`context`、`agent`、`hooks`、`paths`、`shell`
- 從 OpenCode 官方看: 明確只認 `name`、`description`、`license`、`compatibility`、`metadata`
- 從 Codex 官方看: 明確要求 `name`、`description`，其餘產品層 metadata 主要放在 `agents/openai.yaml`，而不是在 `SKILL.md` 公開列出一長串 frontmatter keys

因此:

- `model:` 可以寫，但屬於 Claude Code 擴充，不應假設 OpenCode / Codex 也會照單全收
- `path:` 不是標準 skill frontmatter key
- Claude Code 用的是 `paths:`，Codex 的 `path` 則是 config 用法，不是 `SKILL.md` 用法

## 來源

- Agent Skills specification
- Claude Code docs: Extend Claude with skills
- OpenCode docs: Agent Skills
- OpenAI Codex docs: Agent Skills
- OpenAI Codex docs: Subagents
