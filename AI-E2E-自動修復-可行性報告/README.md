# AI E2E 自動修復方案包

這個資料夾整理的是「AI 開發完成後，自動開站、自動跑 end-to-end 測試、失敗就自動修、再重跑，直到成功或達到上限」的落地方案。

內容包含：

- `01-可行性報告.md`：完整可行性分析、風險、方案比較、建議架構
- `02-SOP.md`：實際執行流程與操作規範
- `03-導入清單.md`：導入前需要確認的環境、邊界、停止條件
- `templates/run-autofix-loop.sh`：自動修復迴圈腳本模板
- `templates/github-actions-e2e-autofix.yml`：CI 工作流模板
- `templates/qwen-autofix-prompt.md`：給 Qwen Code CLI 的固定中文 prompt 模板
- `templates/opencode-autofix-prompt.md`：給 OpenCode CLI 的固定中文 prompt 模板
- `templates/triage-report-template.md`：失敗後的標準報告模板

建議使用方式：

1. 先讀 `01-可行性報告.md`
2. 再依 `02-SOP.md` 建立本地流程
3. 依 `03-導入清單.md` 補齊環境與限制
4. 最後依 `templates/` 內容落地到你的專案

核心原則：

- AI 負責開發、修復、分析
- Playwright 負責判定 E2E 是否真的通過
- 外層腳本或 CI 負責控制重試上限、工件蒐集、退出條件
- 不讓 agent 自己宣告「我測過了所以算成功」
