# AI E2E 自動修復方案包

這一包的目的很單純：

- AI 完成開發後，自動啟動系統
- 自動執行快速守門與 E2E
- 失敗時把日誌與工件交給 AI 修復
- 修完後自動重跑
- 成功才結束，失敗則在達到上限後停止

這份重建版保留原本用途，但改成更精簡、全中文、前後一致的結構。

## 目錄

- `01-可行性報告.md`：什麼情況適合導入，核心風險是什麼
- `02-SOP.md`：實際落地步驟
- `03-導入清單.md`：導入前檢查表
- `templates/run-autofix-loop.sh`：本地修復迴圈腳本模板
- `templates/github-actions-e2e-autofix.yml`：CI 工作流模板
- `templates/qwen-autofix-prompt.md`：給 Qwen Code CLI 的中文修復 prompt
- `templates/opencode-autofix-prompt.md`：給 OpenCode CLI 的中文修復 prompt
- `templates/triage-report-template.md`：到達停止條件後的標準報告

## 使用順序

1. 先讀 `01-可行性報告.md`
2. 再用 `02-SOP.md` 決定你專案的流程
3. 用 `03-導入清單.md` 補齊缺口
4. 最後把 `templates/` 套到實際專案

## 核心原則

- 驗證標準必須交給 Playwright，不交給 AI 自我宣告
- AI 只負責分析、修復、重跑必要檢查
- 外層腳本或 CI 要負責輪次上限、工件保存、退出條件
- Prompt、報告欄位、腳本中的上下文描述要用同一套詞彙
