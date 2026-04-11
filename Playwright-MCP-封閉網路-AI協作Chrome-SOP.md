# Playwright MCP + AI CLI + Chrome — 封閉網路環境 SOP

> 適用情境：公司網路封閉，想讓 AI CLI 和本機 Chrome/Chromium 協作，但不依賴雲端 Browser SaaS，也不使用 `playwright install chrome`。

---

## 1. 先講結論

依你們公司的網路情境，**最穩定的方案**不是 Remote Browser，也不是需要額外對外服務的 MCP，而是：

1. **AI CLI 繼續走你們可用的模型端點**
   - `Claude Code` 走你目前已可用的 Claude/模型路徑
   - `OpenCode` 建議明確綁到公司內部 OpenAI-compatible API
2. **Playwright MCP 用本機 `stdio` server**
3. **Browser 不用 `playwright install chrome`，直接指定既有 Chromium/Chrome 的 `executablePath`**
4. **Profile 用 `userDataDir` 固定下來**
   - 讓登入狀態、cookie、內網站點 session 可以保留

這樣的資料流會是：

```text
AI CLI  <->  本機 Playwright MCP process  <->  本機 Chrome/Chromium executable
                                               <->  你公司內/外可連的網站
```

關鍵點是：**Browser automation 本身完全可以留在本機**。真正需要過網路的，通常只有：

- AI CLI 到模型 API
- Chrome 到目標網站

Playwright MCP server 本身可以是純本機程序，不需要額外連遠端 MCP。

---

## 2. 你的環境判斷

### 已知條件

- 你本地已經有 `playwright`
- 你**無法**使用 `playwright install chrome`
- 你已有一個現成 browser executable path：

```text
/home/mcchungp/Documents/project/tool/playwright2/ms-playwright/chromium-1194/chrome-linux/chrome
```

### 這代表什麼

- 你**不需要**再安裝 Playwright browser bundle
- 你應該直接把這個路徑交給 Playwright MCP 的 `executablePath`
- 你要避免所有會臨時出外網抓套件或抓 browser 的命令

---

## 3. 網路策略

### 推薦策略：完全本機化 Browser 控制

優先使用：

- `Claude Code` + local stdio MCP
- `OpenCode` + local MCP config
- `@playwright/mcp` 改成 **本機已安裝版本**
- `chromium/chrome` 改成 **固定 executablePath**

### 不推薦直接照官方範例用 `npx @latest`

官方文件常用：

```bash
npx @playwright/mcp@latest
```

但在你們情境下，這通常代表：

- 需要 npm registry 可連
- 需要即時抓最新版套件
- 版本不可控

在封閉網路內，建議改成：

1. 先把 `@playwright/mcp` 安裝到本機或內網鏡像
2. 用固定版本
3. 用 `node <實際 cli.js 路徑>` 啟動

---

## 4. 先備條件清單

正式設定前，先確認這 4 件事：

```bash
which claude
which opencode
node -v
test -x /home/mcchungp/Documents/project/tool/playwright2/ms-playwright/chromium-1194/chrome-linux/chrome && echo OK
```

你至少需要：

- `Node.js 18+`
- `claude` CLI
- `opencode` CLI
- 本機已有 `@playwright/mcp`
- 你的 Chromium/Chrome 路徑可執行

---

## 5. 建議的目錄配置

建議在專案內放這些檔案：

```text
project/
├── .mcp.json
├── opencode.json
├── tools/
│   ├── playwright-mcp.config.json
│   └── playwright/
│       └── README.md
└── .cache/
    └── playwright-mcp-profile/
```

---

## 6. Playwright MCP 設定檔

先建立：

`tools/playwright-mcp.config.json`

```json
{
  "browser": {
    "browserName": "chromium",
    "userDataDir": "./.cache/playwright-mcp-profile",
    "launchOptions": {
      "headless": false,
      "executablePath": "/home/mcchungp/Documents/project/tool/playwright2/ms-playwright/chromium-1194/chrome-linux/chrome"
    },
    "contextOptions": {
      "viewport": {
        "width": 1440,
        "height": 900
      }
    }
  }
}
```

### 這份設定的目的

- `headless: false`
  - 讓 AI 真正和可見的 Chrome/Chromium 協作
- `executablePath`
  - 明確指定你已安裝好的 browser binary
- `userDataDir`
  - 保留登入狀態與 session
- `viewport`
  - 讓畫面穩定，不要每次尺寸不同

### 什麼情況不要用 `--isolated`

如果你要：

- 保留登入狀態
- 跑公司 SSO
- 用同一組內網 cookie 持續操作

那就**不要優先用 `--isolated`**。先用 persistent profile，也就是上面的 `userDataDir`。

---

## 7. `@playwright/mcp` 套件來源策略

### 最佳做法

在封閉網路下，把 `@playwright/mcp` 視為「先佈署、後使用」的本機依賴。

可接受的來源：

1. 公司內部 npm mirror
2. 另一台可上網機器先下載 tarball，再帶入內網
3. 直接放進 repo 或共用工具目錄

### 啟動方式建議順序

#### 方式 A：repo 內已安裝

```bash
node ./node_modules/@playwright/mcp/cli.js --config ./tools/playwright-mcp.config.json
```

#### 方式 B：全域已安裝

```bash
node /usr/local/lib/node_modules/@playwright/mcp/cli.js --config ./tools/playwright-mcp.config.json
```

#### 方式 C：你們自己放在工具目錄

```bash
node /path/to/@playwright/mcp/cli.js --config ./tools/playwright-mcp.config.json
```

### 不建議

```bash
npx @playwright/mcp@latest
```

因為這對封閉網路來說太脆弱。

---

## 8. Claude Code + Playwright MCP SOP

### 推薦：專案級 `.mcp.json`

建立專案根目錄 `.mcp.json`：

```json
{
  "mcpServers": {
    "playwright-local": {
      "command": "node",
      "args": [
        "./node_modules/@playwright/mcp/cli.js",
        "--config",
        "./tools/playwright-mcp.config.json"
      ]
    }
  }
}
```

如果不是裝在 repo 內，把 `./node_modules/@playwright/mcp/cli.js` 改成實際路徑。

### 如果你偏好用 CLI 指令加入

```bash
claude mcp add --transport stdio --scope project playwright-local -- \
  node ./node_modules/@playwright/mcp/cli.js \
  --config ./tools/playwright-mcp.config.json
```

### 驗證

```bash
claude mcp list
claude mcp get playwright-local
```

進到 Claude Code 後：

```text
/mcp
```

應看到 `playwright-local` 已連上。

### Claude Code 實際操作提示詞

```text
請使用 playwright-local：
1. 開啟 https://example.com
2. 等待頁面穩定
3. 點擊登入按鈕
4. 完成後截圖
5. 告訴我目前頁面上有哪些主要區塊
```

### 更適合你們公司的使用方式

把 Claude Code 當成：

- 任務規劃者
- DOM/無障礙樹讀取者
- 互動執行者
- 截圖與驗證者

而不是單純跑 E2E 測試。

很適合做：

- 內網系統巡檢
- 回歸檢查
- 登入後流程驗證
- AI 協助點選、輸入、擷取資訊

---

## 9. OpenCode + Playwright MCP SOP

### 專案級 `opencode.json`

建立專案根目錄 `opencode.json`：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "playwright-local": {
      "type": "local",
      "command": [
        "node",
        "./node_modules/@playwright/mcp/cli.js",
        "--config",
        "./tools/playwright-mcp.config.json"
      ],
      "enabled": true
    }
  }
}
```

### 驗證

```bash
opencode mcp list
```

### OpenCode 實際操作提示詞

```text
Use the playwright-local MCP tool.
Open https://example.com, wait for the page to settle, click the login button,
and summarize the visible navigation items.
```

### OpenCode 在封閉網路的額外注意

我本機檢查時，`opencode --help` 就已經出現 `models.dev` 連線失敗訊息。這代表在你們網路環境下，**OpenCode 的模型供應端一定要事先設定好**，不要假設它能自由連外抓 provider metadata。

如果你們公司已有內部 OpenAI-compatible API，建議在 `opencode.json` 補這段：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "company-llm": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Company Internal LLM",
      "options": {
        "baseURL": "http://your-internal-llm/v1"
      },
      "models": {
        "your-model-name": {
          "name": "Your Internal Model"
        }
      }
    }
  },
  "mcp": {
    "playwright-local": {
      "type": "local",
      "command": [
        "node",
        "./node_modules/@playwright/mcp/cli.js",
        "--config",
        "./tools/playwright-mcp.config.json"
      ],
      "enabled": true
    }
  }
}
```

---

## 10. 如果你要「接手已經打開的 Chrome」

這是第二方案，不是第一方案。

Playwright MCP 支援用 browser extension 連到既有的 Chrome/Edge session。這在下列情況有價值：

- 你想接手自己手動開好的瀏覽器
- 你想沿用原本個人 profile
- 你需要和既有分頁一起工作

但在你們公司環境下，這條路通常比較麻煩，因為可能卡在：

- Chrome extension 安裝政策
- 企業瀏覽器限制
- extension 更新與版本控管

所以建議順序是：

1. **先做本機 launch 模式**
2. 只有在你真的需要「接手既有人工瀏覽器 session」時，再評估 extension 模式

---

## 11. 你公司環境下的推薦標準流程

### 第一次設定

1. 確認 `@playwright/mcp` 已放到本機可用位置
2. 建立 `tools/playwright-mcp.config.json`
3. 建立 `.mcp.json` 或 `opencode.json`
4. 驗證 Chromium 路徑可執行
5. 驗證 CLI 可看見 MCP server
6. 用簡單網站測一次開頁、點擊、截圖

### 每次使用

1. 進到專案目錄
2. 啟動 `claude` 或 `opencode`
3. 確認 MCP server 狀態正常
4. 用 prompt 指示 AI 操作 Chrome
5. 需要保留登入時，沿用相同 `userDataDir`
6. 需要乾淨測試時，改一個新的 `userDataDir`

---

## 12. 建議的實戰 Prompt

### 內網系統巡檢

```text
請使用 playwright-local：
1. 開啟公司系統首頁
2. 若尚未登入，停在登入頁等我
3. 登入後進入「報表查詢」
4. 截圖頁面
5. 列出畫面上的主要操作按鈕與篩選條件
```

### 流程驗證

```text
請使用 playwright-local 驗證以下流程：
1. 開啟系統
2. 登入
3. 建立一筆測試資料
4. 查詢剛剛建立的資料
5. 截圖每個步驟
6. 若失敗，告訴我停在哪一步與畫面訊息
```

### UI 巡檢

```text
請使用 playwright-local 開啟這個頁面，
檢查是否有明顯錯位、按鈕不可見、表格溢出或文字被截斷的情況，
並附上截圖與問題摘要。
```

---

## 13. 故障排除

### 問題 1：`browser not installed`

原因：

- AI 觸發了預設 browser install 流程
- 沒有正確吃到 `executablePath`

處理：

1. 確認 `playwright-mcp.config.json` 有 `launchOptions.executablePath`
2. 確認 CLI 啟動時真的帶了 `--config`
3. 用你提供的既有 browser 路徑，不要再跑 `playwright install chrome`

### 問題 2：`Connection closed` 或 MCP 起不來

原因：

- Claude Code 指令裡 `--` 分隔符號位置錯了
- `node` 後面的 `cli.js` 路徑不對

處理：

```bash
claude mcp add --transport stdio --scope project playwright-local -- \
  node ./node_modules/@playwright/mcp/cli.js \
  --config ./tools/playwright-mcp.config.json
```

### 問題 3：Chrome 開了，但每次都要重登

原因：

- 你用了 isolated session
- 或 `userDataDir` 每次都變

處理：

- 固定 `userDataDir`
- 不要先上 `--isolated`

### 問題 4：OpenCode 能啟動，但模型不能用

原因：

- 你們網路擋掉外部 provider / metadata

處理：

- 直接改用公司內部 OpenAI-compatible endpoint
- 把 provider 寫死在 `opencode.json`

### 問題 5：要接手我手動打開的 Chrome 分頁

原因：

- 這不是一般 launch 模式

處理：

- 改評估 Playwright MCP 的 extension 模式
- 但先確認公司是否允許安裝 browser extension

---

## 14. 最終建議

你們公司網路情境下，**最值得先落地的 SOP** 是：

1. `Claude Code` / `OpenCode` 都走 **local stdio MCP**
2. `@playwright/mcp` 用 **內網或本機固定版本**
3. Browser 用你現成的 `executablePath`
4. 用 persistent `userDataDir` 保留登入
5. 把 AI 當成「能操作 Chrome 的任務代理人」

也就是說，先不要把重點放在「怎麼安裝 Playwright 的 Chrome」，而是放在：

- **怎麼把本機已有的 browser 接上 MCP**
- **怎麼讓 AI CLI 穩定呼叫它**
- **怎麼在封閉網路下避免任何臨時連外依賴**

如果你要，我下一步可以直接幫你把這份 SOP 再落成兩套可直接貼上使用的檔案：

1. [`.mcp.json`](/Users/jim/Documents/project/ccrCode/.mcp.json) 範本
2. [`opencode.json`](/Users/jim/Documents/project/ccrCode/opencode.json) 範本

你只要把 `@playwright/mcp` 的實際安裝路徑補上就能跑。
