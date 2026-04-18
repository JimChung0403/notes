# Claude Code 已安裝後：GSD / Superpowers 安裝教學

這份文件現在假設：

- `Claude Code` 本體已經安裝完成
- 公司可以走 `npm install`
- 公司 **不能直接用外部 marketplace / plugin marketplace**

所以這份文件只回答兩件事：

1. 怎麼在 `Claude Code` 裝 `GSD`
2. 怎麼在 **不能用 marketplace** 的情況下處理 `Superpowers`

---

## 1. 先講結論

### `GSD`

`GSD` 不依賴 `Claude Code` marketplace。  
它有官方安裝器，可以直接裝到：

- 專案內的 `.claude/`
- 或使用者的 `~/.claude/`

### `Superpowers`

`Superpowers` 對 `Claude Code` 的官方安裝說明，主路徑是：

- Anthropic 官方 plugin marketplace
- 或 `obra/superpowers-marketplace`

如果你公司不能用 marketplace，**官方 README 沒有提供一條同樣正式的「無 marketplace 直接安裝」路徑**。  
所以你在公司裡有兩種選擇：

1. **內部鏡像 marketplace**
2. **先不要把 `Superpowers` 當公司標準安裝件**

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

## 3. `Superpowers` 在不能用 marketplace 時怎麼辦

## 官方支援現況

`Superpowers` 官方 README 對 `Claude Code` 的安裝方式，寫的是：

- `/plugin install superpowers@claude-plugins-official`
- 或先 `/plugin marketplace add obra/superpowers-marketplace`
- 再 `/plugin install superpowers@superpowers-marketplace`

也就是說，**官方主路徑就是 marketplace**。

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

## 5. 公司可行方案 B：先不要在 Claude Code 裝 Superpowers

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

## 6. 我對公司版的實際建議

### 第一版建議

- `Claude Code` 本體
- `GSD`
- 你們 repo 內的 `.claude/commands/`

### 第二版再評估

- 內部鏡像 `Superpowers marketplace`

這樣風險最小。

---

## 7. 最小驗收標準

### `GSD`

以下通過就算成功：

- `npx get-shit-done-cc --claude --local` 可完成
- 重開 `Claude Code`
- `/gsd:help` 正常

### `Superpowers`

以下通過才算成功：

- `/plugin marketplace add /path/to/internal/superpowers-marketplace` 可成功
- `/plugin install superpowers@superpowers-marketplace` 可成功
- 新 session 中能看到 `Superpowers` workflow 生效

---

## 8. 一句話版

- `GSD`：可以直接裝，適合公司第一版
- `Superpowers`：對 `Claude Code` 官方是 marketplace 路徑；公司如果不能用 marketplace，就走內部鏡像，不然先不要列為標準安裝件
