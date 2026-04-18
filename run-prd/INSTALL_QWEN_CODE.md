# Qwen Code 已安裝後：GSD / Superpowers 可行性說明

這份文件現在假設：

- `Qwen Code` 本體已經安裝完成
- 你想知道：在公司環境下，能不能再裝 `GSD` / `Superpowers`

這份文件重點不是一般安裝，而是：

- 現在有沒有官方支援
- 如果沒有，手動 local 導入是否值得做
- 如果公司一定要用，應該怎麼定位

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

## 3. 如果硬要 local 導入，可以怎麼做

可以做，但我把它定位成：

**公司內部 workaround**

不是：

**官方支援安裝方式**

### 3.1 可能的做法

如果你公司一定要讓 `Qwen Code` 參與這套流程，可以考慮：

1. 先準備內部 mirror：
   - `obra/superpowers`
2. 不追求官方 plugin 安裝
3. 只手動複製或改寫你們真正要用的 workflow 內容：
   - `brainstorming`
   - `writing-plans`
   - `executing-plans`
   - `test-driven-development`
4. 把這些內容轉成：
   - 你們 repo 內的 command 文件
   - 或 `Qwen Code` 可讀的內部工作流說明

### 3.2 為什麼我不建議把這條路寫成公司標準

因為這樣做：

- 不屬於官方已驗證路徑
- 更新維護要自己扛
- 不同版本的 `Qwen Code` 行為可能不穩定
- 團隊交接成本會比 `Claude Code` / `OpenCode` 高

---

## 4. 那 Qwen Code 可以做什麼

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

## 5. 公司版建議

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

## 6. 最務實的做法

如果公司裡一定要讓 `Qwen Code` 參與這套流程，最穩的方式是：

1. `GSD` / `Superpowers` 先由 `Claude Code` 或 `OpenCode` 承載
2. `Qwen Code` 只拿來做：
   - 第二模型 review
   - 需求理解交叉檢查
   - 測試案例補充

這樣你不會把整套流程綁在一條未明確官方支援的路徑上。

---

## 7. 一句話版

`Qwen Code` 可以做公司內部 fallback，但目前我不建議你把它當成 `GSD` / `Superpowers` 的正式安裝平台。  
公司標準路徑應該先放在 `Claude Code` 或 `OpenCode`，`Qwen Code` 更適合做備援或第二模型驗證。
