# OpenCode 已安裝後：GSD / Superpowers 安裝教學

這份文件現在假設：

- `OpenCode` 本體已經安裝完成
- 公司不能直接用外部 marketplace
- 但公司可以使用內部 Git / 內部鏡像 repo

這份文件只回答兩件事：

1. 怎麼在 `OpenCode` 裝 `GSD`
2. 怎麼在沒有 marketplace 的情況下裝 `Superpowers`

---

## 1. 先講結論

### `GSD`

`GSD` 官方安裝器支援 `OpenCode`，可以直接裝到：

- `~/.config/opencode/`

### `Superpowers`

`Superpowers` 官方 README 對 `OpenCode` 的說法是：

- 讓 `OpenCode` 去抓 `https://raw.githubusercontent.com/obra/superpowers/refs/heads/main/.opencode/INSTALL.md`
- 再照裡面的步驟做

所以如果公司不能直接抓外網，你最合理的做法是：

- 先把 `obra/superpowers` 做成公司內部鏡像
- 再改成讀公司內部鏡像裡的 `.opencode/INSTALL.md`

---

## 2. 安裝 GSD

執行：

```bash
npx get-shit-done-cc --opencode --global
```

官方安裝器會把內容裝到：

- `~/.config/opencode/`

### 驗證 GSD 有沒有裝好

你至少要確認：

- `~/.config/opencode/` 下有新內容
- 重新啟動 `OpenCode`
- 可以使用 `GSD` workflow

如果你們的 `OpenCode` 對 slash command / workflow 有對應入口，請直接用該入口測：

- `gsd help`
- `map-codebase`
- 或等價命令

如果沒有固定 slash 入口，就至少測試一個明確指令：

```text
請先執行 GSD 的 codebase mapping，不要直接開始寫 code。
```

---

## 3. 安裝 Superpowers

## 官方方式

官方 README 對 `OpenCode` 的安裝方式是：

```text
Fetch and follow instructions from https://raw.githubusercontent.com/obra/superpowers/refs/heads/main/.opencode/INSTALL.md
```

這代表：

- `OpenCode` 路徑不是 marketplace
- 而是讀 repo 內的 `.opencode/INSTALL.md`

---

## 4. 內網版本怎麼做

### Step 1. 建公司內部鏡像

把這個 repo 鏡像到公司內部：

- `obra/superpowers`

### Step 2. 讓 OpenCode 讀內部鏡像的 `.opencode/INSTALL.md`

你們內部可以改成這樣的指令思路：

```text
Fetch and follow instructions from <internal-git>/obra/superpowers/.opencode/INSTALL.md
```

如果公司政策不允許讓 agent 自己 fetch，也可以改成人工方式：

1. 打開內部鏡像 repo
2. 找 `.opencode/INSTALL.md`
3. 照它的步驟手動安裝

### Step 3. 驗證是否生效

開一個新 session，直接測：

```text
請先為這個功能做 implementation plan，不要直接寫 code。
```

或：

```text
請用 test-driven-development 的方式處理這個需求。
```

如果 `Superpowers` 有作用，通常你會看到：

- 更強的 planning
- 更明確的 TDD workflow
- 更明顯的 skill 驅動行為

---

## 5. 如果公司不想維護內部鏡像

那建議：

- `OpenCode` 先裝 `GSD`
- `Superpowers` 先不列入公司標準

理由：

- `GSD` 有官方 installer
- `Superpowers` 在 `OpenCode` 是透過 repo 內安裝檔運作
- 若你們不願意維護 repo 鏡像，就會增加維運成本

---

## 6. 最小驗收標準

### `GSD`

以下通過就算成功：

- `npx get-shit-done-cc --opencode --global` 可完成
- `~/.config/opencode/` 有對應安裝內容
- 重開 `OpenCode` 後能觸發 `GSD` workflow

### `Superpowers`

以下通過才算成功：

- 公司內部鏡像可讀
- `.opencode/INSTALL.md` 可被跟隨或手動執行
- 新 session 中可明顯觸發 planning / TDD / workflow 行為

---

## 7. 一句話版

- `GSD`：OpenCode 可直接裝，適合第一版
- `Superpowers`：OpenCode 官方不是 marketplace，而是 `.opencode/INSTALL.md`；公司版最適合走內部鏡像 repo
