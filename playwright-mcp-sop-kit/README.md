# Playwright MCP SOP Kit

這個資料夾整理了在封閉網路環境下，讓 AI CLI 與本機 Chrome/Chromium 協作所需的最小檔案：

- `Playwright-MCP-封閉網路-AI協作Chrome-SOP.md`
- `.mcp.json.example`
- `opencode.json.example`
- `tools/playwright-mcp.config.json.example`
- `tools/playwright-mcp.config.proxy-server.json.example`
- `tools/playwright-mcp.config.proxy-pac.json.example`

## 使用順序

1. 先看 `Playwright-MCP-封閉網路-AI協作Chrome-SOP.md`
2. 確認你本機 `@playwright/mcp` 的實際安裝位置
3. 把範本檔改成你要的正式檔名與路徑
4. 依你要用的 CLI 選擇：
   - `Claude Code` → `.mcp.json`
   - `OpenCode` → `opencode.json`

## 你要改的地方

至少要改這兩個值：

- `@playwright/mcp` 的 `cli.js` 實際路徑
- `executablePath` 的實際 Chrome/Chromium 路徑

如果你公司是靠 proxy 才能對外，另外改：

- `proxy.server`
- `proxy.bypass`
- 或 `--proxy-pac-url`

## 如果 `cli.js` 路徑不存在

先檢查：

```bash
npm ls @playwright/mcp --depth=0
find . -path '*/node_modules/@playwright/mcp/cli.js' 2>/dev/null
```

如果沒有，再安裝。

先安裝 MCP server 套件，不要只安裝 `playwright`：

```bash
npm install @playwright/mcp
```

如果這個 repo 也要寫一般 Playwright 腳本，可以：

```bash
npm install playwright @playwright/mcp
```

安裝後再確認：

```bash
find . -path '*/node_modules/@playwright/mcp/cli.js' 2>/dev/null
```

## 建議

- 要保留登入狀態時，用固定 `userDataDir`
- 要做乾淨測試時，改一個新的 `userDataDir`，或再做一份 isolated 專用設定
