# AI 開發後自動 E2E 驗證與自動修復 SOP

## 1. 目標

建立一條可重複執行的修復鏈：

- AI 完成開發
- 系統自動啟動
- 自動跑快速守門
- 自動跑 E2E
- 失敗時交給 AI 修復
- 修完後只重跑必要檢查

## 2. 前置條件

- 專案可用單一命令啟動
- 有固定測試 URL 或健康檢查端點
- 已有 lint、typecheck、unit 或等價檢查
- 已有 Playwright smoke tests
- AI CLI 可非互動執行
- 已定義可修改與不可修改路徑

## 3. 標準流程

### 3.1 啟動環境

1. 啟動 app 與必要依賴
2. 做健康檢查
3. 健康檢查失敗就停止，不進入 E2E

### 3.2 快速守門

依序執行：

1. `lint`
2. `typecheck`
3. `unit`

若這一層失敗：

- 保存 stdout、stderr、app log
- 交給 AI 修復
- 修完只重跑快速守門

### 3.3 E2E 驗證

依序執行：

1. smoke
2. critical path

先過 smoke，再過 critical path，不建議一開始就跑全量。

### 3.4 蒐證

E2E 或快速守門失敗後，至少保存：

- HTML report
- trace
- screenshot
- video
- app log
- test stdout
- test stderr

### 3.5 AI 修復

交給 AI 的內容至少包含：

- 失敗分類要求
- 允許修改路徑
- 禁止修改路徑
- 失敗日誌與工件路徑
- 本輪目標是「最小修補」

### 3.6 重跑策略

建議順序：

1. 先重跑剛剛失敗的最小檢查
2. 通過後再回補 smoke
3. smoke 通過後再跑 critical path

## 4. 停止條件

任何一項成立就停止：

- 超過最大輪數
- 根因屬於環境問題
- 需要 secrets、帳密、驗證碼
- 需要改 infra、deploy、production config
- 同一類錯誤重複出現
- 單輪 diff 超過預設上限

## 5. 每輪都要留下的輸出

- 第幾輪
- 錯誤分類
- 根因摘要
- 修改檔案
- 重跑命令
- 目前結果
- 是否繼續下一輪

## 6. 實務原則

- AI 不是裁判，Playwright 才是
- 先修最可能的單點根因，不做大改
- 只在可控白名單內修改
- 先求收斂，再求自動化覆蓋率
