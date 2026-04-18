# Qwen Code 已安裝後：GSD / Superpowers 可行性說明

這份文件現在假設：

- `Qwen Code` 本體已經安裝完成
- 你想知道：在公司環境下，能不能再裝 `GSD` / `Superpowers`

這份文件重點不是一般安裝，而是：

- 現在有沒有官方支援
- 如果沒有，該怎麼決策

---

## 1. 先講結論

### `GSD`

我目前沒有找到 `GSD` 官方 README 對 `Qwen Code` 的正式安裝說明。

### `Superpowers`

我目前也沒有看到 `Superpowers` 官方 README 把 `Qwen Code` 列為正式支援平台。

所以對 `Qwen Code` 而言：

- `GSD`：**目前不建議當成已驗證的官方路徑**
- `Superpowers`：**目前也不建議當成已驗證的官方路徑**

---

## 2. 這代表什麼

如果你公司要的是：

- 可交接
- 可重複
- 可寫進標準文件

那我不建議你把：

- `Qwen Code + GSD`
- `Qwen Code + Superpowers`

當成第一版公司標準。

---

## 3. 那 Qwen Code 可以做什麼

如果公司已經裝好 `Qwen Code`，它仍然可以做這些事：

- 跑你們 repo 內的流程文件
- 依照 `run-prd` 的說明做本地 workflow
- 配合：
  - `feature brief`
  - `rg`
  - `mvn test-compile`
  - targeted tests
  - review

也就是說：

你仍然可以把 `Qwen Code` 當成一個 terminal coding agent 使用，  
只是不要把 `GSD` / `Superpowers` 當成它的官方擴充方案。

---

## 4. 公司版建議

### 如果你要穩定標準

建議：

- `Claude Code + GSD`
- `OpenCode + GSD`
- `OpenCode + Superpowers`

### 如果你要讓 Qwen Code 也能加入

建議把它定位成：

- 備用 agent
- 平行驗證 agent
- 第二模型 reviewer

而不是：

- `GSD` / `Superpowers` 的正式承載平台

---

## 5. 最務實的做法

如果公司裡一定要讓 `Qwen Code` 參與這套流程，最穩的方式是：

1. `GSD` / `Superpowers` 先由 `Claude Code` 或 `OpenCode` 承載
2. `Qwen Code` 只拿來做：
   - 第二模型 review
   - 需求理解交叉檢查
   - 測試案例補充

這樣你不會把整套流程綁在一條未明確官方支援的路徑上。

---

## 6. 一句話版

`Qwen Code` 可以用，但目前我不建議你把它當成 `GSD` / `Superpowers` 的正式安裝平台。  
公司標準路徑應該先放在 `Claude Code` 或 `OpenCode`。
