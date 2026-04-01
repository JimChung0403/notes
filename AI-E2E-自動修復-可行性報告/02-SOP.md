# AI 開發後自動 E2E 驗證與自動修復 SOP

## 1. 目標

建立一條無人值守流程：

- AI 完成開發
- 自動啟動系統
- 自動執行 E2E
- 失敗後自動修復
- 自動重跑
- 成功才結束

## 2. 前置條件

執行前必須具備：

- 專案能用單一命令啟動，例如 `npm run dev` 或 `docker compose up`
- 專案有健康檢查端點或可檢查首頁是否可用
- 已有 Playwright 測試
- 可區分 smoke 與 critical path
- AI CLI 可在目前環境執行
- 已定義允許 AI 修改的目錄

## 3. 標準流程

## 3.1 開發完成後

1. 停止 agent 繼續新增功能
2. 將當前工作樹視為待驗證版本
3. 記錄當前 commit 或 branch 狀態

## 3.2 啟動環境

1. 啟動 app、db、cache、mock service
2. 等待健康檢查通過
3. 若健康檢查失敗，先停止流程，不進入 E2E

## 3.3 快速守門

依序執行：

1. `lint`
2. `typecheck`
3. `unit test`

若這一層失敗：

- 直接交給 AI 修復
- 修完後重跑快速守門
- 不要立刻進入完整 E2E

## 3.4 E2E 驗證

先跑：

- smoke tests

再跑：

- critical path tests

建議不要一開始就全量跑所有測試，先用小而穩的 smoke 集合當第一道門。

## 3.5 失敗後蒐證

若 E2E 失敗，保存：

- `playwright-report/`
- `test-results/`
- trace
- screenshot
- video
- 應用程式日誌
- 測試日誌

同時產出一份簡短清單：

- 哪些 spec 失敗
- 失敗步驟是什麼
- 是否卡在環境啟動
- 是否有明確 selector、timeout、network 或 assertion 錯誤

## 3.6 AI 修復

把以下資訊交給 AI：

- 失敗 spec 清單
- 主要錯誤訊息
- trace 與 screenshot 路徑
- app logs 路徑
- 允許修改的目錄
- 禁止修改的目錄
- 最大修改範圍

要求 AI 嚴格遵守：

- 先分類錯誤
- 再做最小修復
- 修完後只重跑必要測試

## 3.7 重跑策略

建議策略：

1. 優先只重跑剛才失敗的 smoke 或 spec
2. 若失敗點修正後通過，再重跑整個 smoke
3. smoke 全綠後，再跑 critical path
4. 最後視需要跑全量 E2E

## 3.8 停止條件

發生以下任一情況就停止自動修復：

- 超過最大輪數
- 需要修改 infra 或 deploy
- 需要人工提供帳號、驗證碼、secret
- 同一錯誤重複出現
- 修復造成快速守門回歸失敗
- diff 超過設定上限

## 4. 建議角色分工

## 4.1 Playwright

負責：

- 真實 E2E 執行
- pass/fail 判定
- artifacts 產出

## 4.2 AI CLI

負責：

- 閱讀錯誤與工件
- 判斷根因
- 做最小修復
- 執行重跑命令

## 4.3 Orchestrator

負責：

- 啟動服務
- 控制輪次
- 保留報告
- 最終退出碼

## 5. 錯誤分類規則

AI 在每次修復前，先把失敗分類成下列四類之一：

### A. App Bug

例：

- 按鈕不可點
- API 回傳錯誤
- 頁面沒渲染
- 狀態流程錯誤

### B. Flaky Test

例：

- 偶發 timeout
- 等待條件太脆弱
- 非同步事件尚未完成

### C. Test Data Issue

例：

- 沒有測試帳號
- 初始資料與預期不一致
- seed 不完整

### D. Environment Issue

例：

- 服務沒啟動
- port 衝突
- env vars 缺漏
- mock server 未啟動

只有 A、B 兩類才適合直接讓 AI 在同一輪自動修 code。

## 6. 可修改範圍建議

建議白名單：

- `src/`
- `app/`
- `components/`
- `tests/e2e/`
- `playwright.config.*`

建議黑名單：

- `infra/`
- `deploy/`
- `.github/workflows/production-*`
- secrets 相關設定
- production 專用設定檔

## 7. 每輪輸出格式

每輪都要產出：

- 第幾輪
- 失敗摘要
- 錯誤分類
- 修改檔案清單
- 修復理由
- 重跑結果
- 是否繼續下一輪

## 8. 建議實施順序

1. 先導入本地版腳本
2. 在單一專案跑通 smoke 自修
3. 再加 critical path
4. 穩定後再搬到 CI

## 9. 最後原則

不要把 AI 當最終裁判。

AI 是修復代理，測試框架才是驗證標準；外層編排腳本才是流程控制者。這三者分清楚，整條自動修復鏈才會穩。
