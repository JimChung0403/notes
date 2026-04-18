# Claude Code 已安裝後：GSD / Superpowers 安裝教學

這份文件現在假設：

- `Claude Code` 本體已經安裝完成
- 公司可以走 `npm install`
- 公司 **不能直接用外部 marketplace / plugin marketplace**

所以這份文件回答三件事：

1. 怎麼在 `Claude Code` 裝 `GSD`
2. `Superpowers` 官方怎麼裝
3. 怎麼在 **不能用 marketplace** 的情況下手動導入 `Superpowers`

---

## 1. 先講結論

### `GSD`

`GSD` 不依賴 `Claude Code` marketplace。  
它有官方安裝器，可以直接裝到：

- 專案內的 `.claude/`
- 或使用者的 `~/.claude/`

### `Superpowers`

`Superpowers` 對 `Claude Code` 的官方主路徑是 plugin marketplace。  
如果公司不能用 marketplace，仍然有兩種可行 fallback：

1. **內部鏡像 marketplace**
2. **抓原始碼後手動導入 commands / skills**

---

## 2. 安裝 GSD

### 專案內安裝

在專案根目錄執行：

```bash
npx get-shit-done-cc --claude --local
```

這會把 `GSD` 安裝到：

- `./.claude/`

### 使用者全域安裝

如果你想讓同一台機器的所有專案都能用：

```bash
npx get-shit-done-cc --claude --global
```

這會安裝到：

- `~/.claude/`

### 驗證 GSD 有沒有裝好

重新啟動 `Claude Code`，然後執行：

```text
/gsd:help
```

如果正常，代表：

- slash commands 已載入
- `GSD` 基本可用

再進一步可以測：

```text
/gsd:map-codebase
```

如果 command 能正常啟動，就代表安裝成功。

---

## 3. 安裝 Superpowers：官方路徑

`Superpowers` 官方 README 對 `Claude Code` 的安裝方式，寫的是：

- `/plugin install superpowers@claude-plugins-official`
- 或先 `/plugin marketplace add obra/superpowers-marketplace`
- 再 `/plugin install superpowers@superpowers-marketplace`

也就是說，**官方主路徑就是 marketplace**。

如果你公司 proxy 可以連到官方 marketplace，優先走這條路。

---

## 4. 公司可行方案 A：做內部鏡像 marketplace

這是最接近官方做法的方案。

### 你們公司內部要準備

至少鏡像這兩個 repo：

- `obra/superpowers`
- `obra/superpowers-marketplace`

### 公司內部安裝方式

如果你們的內部 Git / 檔案系統有一份可讀取的 marketplace 目錄，可以先在 `Claude Code` 裡註冊這個內部路徑：

```text
/plugin marketplace add /path/to/internal/superpowers-marketplace
```

然後再安裝：

```text
/plugin install superpowers@superpowers-marketplace
```

### 驗證方式

安裝後重新開一個 session，然後：

```text
/help
```

你至少要確認：

- 有 `Superpowers` 相關 commands 或 workflow
- 它會在你要求規劃或實作時自動觸發相關 skill

最簡單的功能測試是：

```text
請先幫我規劃這個功能，不要直接寫 code。
```

如果它開始走較強的 spec / plan / TDD workflow，通常就代表 `Superpowers` 已經在作用。

---

## 5. 公司可行方案 B：抓原始碼後手動導入

這一條不是 `Claude Code` 官方完整安裝路徑，但對封閉網路公司是實務可行方案。

### 5.1 先準備原始碼

請先在可存取的環境取得下列 repo，或做成公司內部 mirror：

- `obra/superpowers`

### 5.2 你會用到哪些目錄

`Superpowers` repo 內你至少要看這幾個目錄：

- `commands/`
- `skills/`
- `agents/`
- `hooks/`

對 `Claude Code` 而言，**最容易先落地的是 `commands/` 與 `skills/`**。

### 5.3 最小手動導入做法

如果你公司現在只想先得到接近 `Superpowers` 的工作流，建議先做這件事：

1. 從 `obra/superpowers` 挑出你要的 commands  
   例如：
   - `/brainstorm`
   - `/write-plan`
   - `/execute-plan`

2. 把這些 command 改寫成你公司自己的 `.claude/commands/*.md`  
   例如：
   - `.claude/commands/brainstorm.md`
   - `.claude/commands/write-plan.md`
   - `.claude/commands/execute-plan.md`

3. 再挑出你們第一版真的需要的 skill 流程，轉成公司內部文件或 prompt 規則  
   建議先從：
   - `brainstorming`
   - `writing-plans`
   - `executing-plans`
   - `test-driven-development`
   - `requesting-code-review`
   開始

4. 把這些規則收斂進：
   - `CLAUDE.md`
   - repo 內的 `.claude/commands/`
   - 你們的 `run-prd` 套件

### 5.4 這種手動導入的缺點

這樣做可以用，但**不等於完整官方 plugin**。  
你通常會少掉或不保證完整拿到：

- plugin marketplace 的安裝與更新機制
- `skills-search`
- `SessionStart context injection`
- 某些自動觸發行為

所以這條路更準確的定位是：

**公司內部版 `Superpowers-style workflow`**

不是：

**完整官方 `Superpowers plugin`**

### 5.5 怎麼驗證手動導入有沒有生效

你至少要做這 3 個測試：

1. command 可被叫出  
   例如：

   ```text
   /brainstorm 我要為既有 Java service 加 pagination，先不要寫 code
   ```

2. planning command 可生成結構化 plan  
   例如：

   ```text
   /write-plan 根據 docs/feature-briefs/ORDER-123.md 產 implementation plan
   ```

3. execution command 會要求驗證與 review  
   例如：

   ```text
   /execute-plan
   ```

如果這三個都能工作，代表你已經有一個最低可用的 `Superpowers` fallback。

---

## 6. 公司可行方案 C：先不要在 Claude Code 裝 Superpowers

如果你們公司：

- 不能用 marketplace
- 也不想自己維護內部鏡像 marketplace

那我建議：

- `Claude Code` 先只裝 `GSD`
- `Superpowers` 不列入第一版公司標準

原因很簡單：

- `GSD` 有官方 installer
- `Superpowers` 對 `Claude Code` 的官方安裝目前明顯偏 marketplace

這種情況下，你仍然可以用：

- `GSD`
- 你們 repo 內自己的 `.claude/commands/*.md`
- `run-prd` 這套流程

---

## 7. 我對公司版的實際建議

### 第一版建議

- `Claude Code` 本體
- `GSD`
- 你們 repo 內的 `.claude/commands/`

### 第二版再評估

- 內部鏡像 `Superpowers marketplace`
- 或公司版手動導入 `/brainstorm`、`/write-plan`、`/execute-plan`

這樣風險最小。

---

## 8. 最小驗收標準

### `GSD`

以下通過就算成功：

- `npx get-shit-done-cc --claude --local` 可完成
- 重開 `Claude Code`
- `/gsd:help` 正常

### `Superpowers`：marketplace 版

以下通過才算成功：

- `/plugin marketplace add /path/to/internal/superpowers-marketplace` 可成功
- `/plugin install superpowers@superpowers-marketplace` 可成功
- 新 session 中能看到 `Superpowers` workflow 生效

### `Superpowers`：手動 fallback 版

以下通過就算最低成功：

- `.claude/commands/brainstorm.md`、`.claude/commands/write-plan.md`、`.claude/commands/execute-plan.md` 已存在
- `/brainstorm`、`/write-plan`、`/execute-plan` 可以在新 session 直接使用
- command 內容會要求：
  - 先做規劃
  - 再做 implementation
  - 再做 verification / review

---

## 9. 一句話版

- `GSD`：可以直接裝，適合公司第一版
- `Superpowers`：對 `Claude Code` 官方是 marketplace 路徑；公司如果不能用 marketplace，可以走：
  - 內部鏡像 marketplace
  - 或手動導入 commands / skills 的 fallback 方案
