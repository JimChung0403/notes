# Figma 轉前端代碼 — 封閉網路環境 SOP

> 適用情境：公司網路封閉，無法使用第三方 AI 工具（Locofy、Anima、Builder.io 等），需要將 Figma 設計稿轉為前端代碼。

---

## 目錄

1. [兩種情境總覽](#1-兩種情境總覽)
2. [情境一：純瀏覽器操作（無 MCP）](#2-情境一純瀏覽器操作無-mcp)
   - [方法 A：Dev Mode + Copy CSS（最基礎）](#方法-adev-mode--copy-css最基礎)
   - [方法 B：Figma REST API 自動化提取（最推薦）](#方法-bfigma-rest-api-自動化提取最推薦)
   - [方法 C：截圖 + AI 視覺辨識](#方法-c截圖--ai-視覺辨識)
   - [方法 D：Figma 插件匯出 Design Tokens](#方法-dfigma-插件匯出-design-tokens)
   - [綜合工作流](#情境一綜合工作流)
3. [情境二：可使用 Figma MCP](#3-情境二可使用-figma-mcp)
   - [Figma MCP 是什麼](#figma-mcp-是什麼)
   - [Remote Server 設定（推薦）](#remote-server-設定推薦)
   - [Desktop Server 設定](#desktop-server-設定)
   - [第三方替代：Figma-Context-MCP](#第三方替代figma-context-mcp)
   - [MCP 工作流](#情境二-mcp-工作流)
4. [各情境效率比較](#4-各情境效率比較)
5. [附錄：語言伺服器安裝 / Design Token 格式](#5-附錄)

---

## 1. 兩種情境總覽

| | 情境一：純瀏覽器 | 情境二：有 Figma MCP |
|---|---|---|
| **能用什麼** | Figma 網頁版、瀏覽器 Dev Mode、curl/終端機 | 同左 + Figma MCP Server |
| **不能用什麼** | 第三方網站、第三方 AI 插件、Figma MCP | 第三方網站 |
| **核心策略** | 手動提取 CSS + REST API 抓 JSON + 截圖餵 AI | 一個 prompt 自動拿設計數據、自動生成代碼 |
| **效率預估** | 一個元件約 10-20 分鐘 | 一個元件約 2-5 分鐘 |
| **代碼準確度** | 70-85%（需人工微調） | 85-95%（結構化數據更精準） |

---

## 2. 情境一：純瀏覽器操作（無 MCP）

### 方法 A：Dev Mode + Copy CSS（最基礎）

> 前提：需要 Figma 付費方案（Pro/Organization/Enterprise）的 Dev 或 Full 座位。

#### 步驟 1：進入 Dev Mode

在 Figma 網頁版中按 `Shift+D`，或點擊工具列的 Dev Mode 切換開關。

#### 步驟 2：逐元素複製 CSS

選取任意元素，右側 Inspect 面板會自動產生 CSS：

```css
/* 選取一個 Auto Layout Frame 得到的 CSS */
display: flex;
flex-direction: column;
align-items: flex-start;
padding: 24px;
gap: 16px;
width: 320px;
height: 480px;
background: #FFFFFF;
border-radius: 12px;
box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.08);
```

**可複製的屬性完整清單：**

| 類別 | 屬性 |
|------|------|
| 佈局 | `display: flex/grid`, `flex-direction`, `justify-content`, `align-items`, `gap`, `padding`（四邊獨立）, `width`, `height`, `overflow` |
| 文字 | `font-family`, `font-size`, `font-weight`, `line-height`, `letter-spacing`, `text-align`, `text-decoration`, `color` |
| 視覺 | `background-color`, `background`（漸層）, `border`, `border-radius`（可逐角）, `box-shadow`, `opacity`, `filter: blur()`, `backdrop-filter`, `mix-blend-mode` |
| 效果 | Drop Shadow → `box-shadow`, Inner Shadow → `box-shadow inset`, Layer Blur → `filter: blur()` |

**操作方式：**
- 選取元素 → Inspect 面板 → Code 區塊 → 點右上角 **Copy** 按鈕
- 或右鍵元素 → **Copy/Paste as** → **Copy as CSS**
- 可切換輸出語言：CSS / iOS (Swift) / Android (XML)
- 可切換單位：px / rem（在 Code 區塊底部的下拉選單）

#### 步驟 3：匯出素材

- 選取元素 → 右側 Export 面板 → 設定格式和倍率
- 圖示/向量圖：匯出為 **SVG**
- 圖片素材：匯出為 **PNG @2x**
- 插圖：匯出為 **SVG** 或 **PDF**

#### 步驟 4：餵給 Claude Code

```
我從 Figma 複製了以下 CSS，請幫我用 React + Tailwind 實作這個元件：

[貼上 CSS]

元件功能描述：這是一個使用者卡片，包含頭像、姓名和操作按鈕。
```

#### 優缺點

- ✅ 零門檻，只要有 Dev Mode 就能用
- ✅ CSS 精確度高（直接從 Figma 產生）
- ❌ 手動逐元素複製，效率低
- ❌ 拿不到元件階層結構，只有扁平 CSS

---

### 方法 B：Figma REST API 自動化提取（最推薦）

> **關鍵前提**：如果你的瀏覽器能開 `figma.com`，那 `api.figma.com` 幾乎一定也通（同一基礎設施）。

#### 步驟 1：產生 Personal Access Token

1. 開啟 `https://www.figma.com/settings`
2. 點 **Security** 分頁
3. 捲到 **Personal access tokens**
4. 點 **Generate new token**
5. 命名（例如 `cli-export`）
6. 選擇 Scope：
   - `file_content:read` — 讀取檔案結構和屬性（必選）
   - `file_metadata:read` — 讀取檔案 metadata
   - `file_variables:read` — 讀取變數/Design Tokens
7. 按 Enter，**立刻複製 Token**（只顯示一次）
8. Token 最長 90 天到期，需定期重新產生

#### 步驟 2：取得 File Key 和 Node ID

從 Figma URL 中提取：

```
https://www.figma.com/design/ABC123xyz/My-Design?node-id=456-789
                               ^^^^^^^^^^^              ^^^^^^^
                               FILE_KEY                 NODE_ID
```

#### 步驟 3：用 curl 提取設計數據

```bash
# === 設定環境變數 ===
export FIGMA_TOKEN="figd_xxxxxxxxxxxxxxxxxx"
export FILE_KEY="ABC123xyz"

# === 1. 取得整個檔案結構（depth 限制避免資料過大）===
curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/files/$FILE_KEY?depth=3" \
  > figma_file.json

# === 2. 取得特定 Frame/Component 的詳細資料（推薦）===
curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/files/$FILE_KEY/nodes?ids=456-789" \
  > figma_nodes.json

# === 3. 匯出 Frame 為 SVG ===
curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/images/$FILE_KEY?ids=456-789&format=svg&svg_include_id=true" \
  > figma_svg_urls.json
# 回傳的 JSON 包含 SVG 的下載 URL，再用 curl 下載即可

# === 4. 匯出 Frame 為 PNG @2x ===
curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/images/$FILE_KEY?ids=456-789&format=png&scale=2" \
  > figma_png_urls.json

# === 5. 取得 Design Tokens（變數）===
curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/files/$FILE_KEY/variables/local" \
  > figma_variables.json

# === 6. 取得已發佈的 Styles ===
curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/files/$FILE_KEY/styles" \
  > figma_styles.json
```

#### 步驟 4：API 回傳的 JSON 包含什麼

```
figma_nodes.json 結構簡化示意：
{
  "nodes": {
    "456:789": {
      "document": {
        "id": "456:789",
        "name": "UserCard",
        "type": "FRAME",
        "layoutMode": "VERTICAL",        ← Auto Layout 方向
        "primaryAxisAlignItems": "MIN",   ← justify-content
        "counterAxisAlignItems": "MIN",   ← align-items
        "paddingLeft": 24,                ← padding
        "paddingRight": 24,
        "paddingTop": 24,
        "paddingBottom": 24,
        "itemSpacing": 16,                ← gap
        "fills": [{"type":"SOLID","color":{"r":1,"g":1,"b":1}}],
        "cornerRadius": 12,
        "effects": [{"type":"DROP_SHADOW","offset":{"x":0,"y":4},...}],
        "children": [
          {
            "type": "TEXT",
            "characters": "John Doe",     ← 實際文字內容
            "style": {
              "fontFamily": "Inter",
              "fontSize": 18,
              "fontWeight": 600,
              "lineHeightPx": 24
            }
          },
          ...更多子節點
        ]
      }
    }
  }
}
```

#### 步驟 5：餵給 Claude Code 生成代碼

```bash
# 在 Claude Code 中
請讀取 ./figma_nodes.json 和 ./figma_variables.json，
根據 Figma 設計數據生成 React + Tailwind CSS 元件。

要求：
- 使用語義化 HTML
- 顏色使用 CSS 變數（從 variables 檔案提取）
- 間距使用 Tailwind 的 spacing scale
- 產生響應式佈局
```

#### 步驟 6（進階）：寫一個自動化腳本

```bash
#!/bin/bash
# figma-extract.sh — 一鍵提取 Figma 設計數據

FIGMA_TOKEN="${FIGMA_TOKEN:?請設定 FIGMA_TOKEN 環境變數}"
FILE_KEY="$1"
NODE_IDS="$2"
OUTPUT_DIR="${3:-./figma-export}"

if [ -z "$FILE_KEY" ] || [ -z "$NODE_IDS" ]; then
  echo "用法: ./figma-extract.sh <FILE_KEY> <NODE_IDS> [OUTPUT_DIR]"
  echo "範例: ./figma-extract.sh ABC123xyz '456-789,012-345' ./output"
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "📦 提取節點資料..."
curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/files/$FILE_KEY/nodes?ids=$NODE_IDS" \
  > "$OUTPUT_DIR/nodes.json"

echo "🎨 提取 Design Tokens..."
curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/files/$FILE_KEY/variables/local" \
  > "$OUTPUT_DIR/variables.json"

echo "🖼  匯出 PNG @2x..."
RESPONSE=$(curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/images/$FILE_KEY?ids=$NODE_IDS&format=png&scale=2")
echo "$RESPONSE" > "$OUTPUT_DIR/image_urls.json"

echo "🖼  匯出 SVG..."
RESPONSE_SVG=$(curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/images/$FILE_KEY?ids=$NODE_IDS&format=svg")
echo "$RESPONSE_SVG" > "$OUTPUT_DIR/svg_urls.json"

echo "✅ 完成！檔案儲存在 $OUTPUT_DIR/"
echo ""
echo "下一步：在 Claude Code 中執行"
echo "  請讀取 $OUTPUT_DIR/nodes.json 和 $OUTPUT_DIR/variables.json，生成前端元件代碼"
```

#### 優缺點

- ✅ 自動化程度最高，可重複執行
- ✅ 拿到完整的元件階層結構、Auto Layout 設定、Design Tokens
- ✅ JSON 結構化數據讓 AI 生成的代碼最精準
- ❌ 需要產生 Personal Access Token（90 天到期）
- ❌ 初次設定需花 15-20 分鐘

---

### 方法 C：截圖 + AI 視覺辨識

> 最低門檻方案，不需要 Dev Mode 付費座位，不需要 API Token。

#### 截圖最佳實踐

1. **Figma 中縮放到 100%** 再截圖（避免模糊）
2. **逐元件截圖**，不要截整頁
3. **在 Dev Mode 中 hover 顯示間距**後再截圖（如果有 Dev Mode）
4. **同時截 Inspect 面板**，讓 AI 看到視覺 + CSS 雙重資訊
5. **分層截圖**：
   - 整體頁面佈局一張
   - 每個主要區塊各一張
   - 獨立元件（按鈕、卡片、表單）各一張
   - 色彩系統/文字樣式面板各一張

#### 餵給 Claude Code

```
# 方式 1：直接貼圖
Cmd+V 把截圖貼到 Claude Code

# 方式 2：指定檔案路徑
請讀取 ./screenshots/user-card.png，
用 React + Tailwind 實作這個元件。

# 方式 3：截圖 + CSS 合併（效果最好）
請看這張截圖 ./screenshots/user-card.png，
搭配以下從 Figma Copy 出來的 CSS：
[貼上 CSS]
生成 React + Tailwind 元件。
```

#### 迭代修正工作流

```
1. 截圖 Figma 設計 → 餵 Claude Code → 生成代碼
2. 用瀏覽器開啟生成結果 → 截圖實際渲染效果
3. 同時貼上 Figma 原稿截圖 + 實際渲染截圖
4. 「請對比這兩張圖，修正差異」
5. 重複 2-4 直到滿意
```

#### 準確度預估

| 項目 | 純截圖 | 截圖 + CSS |
|------|--------|-----------|
| 佈局結構 | 80-90% | 90-95% |
| 顏色 | 70-80% | 95%+ |
| 文字樣式 | 60-70% | 90%+ |
| 間距/尺寸 | 50-60% | 85-90% |
| 響應式 | 需手動指定 | 需手動指定 |

#### 優缺點

- ✅ 零門檻，免費方案也能用
- ✅ 快速上手，不需要設定任何東西
- ❌ 精確度最低，需要較多來回修正
- ❌ 拿不到設計變數/Token，需手動指定

---

### 方法 D：Figma 插件匯出 Design Tokens

> Figma 插件在 Figma 網頁/桌面版內部運行，不需要額外網路存取。

#### 推薦插件

| 插件名稱 | 功能 | 匯出格式 |
|----------|------|---------|
| **Tokens Studio** | 完整 Design Token 管理 | W3C DTCG JSON、CSS Variables、SASS |
| **Figma Token Exporter** | 匯出 Figma Variables | CSS、SASS、JSON |
| **CSS Variables Import/Export** | 直接匯出為 CSS Custom Properties | CSS |
| **Design Tokens** | 多格式 Token 匯出 | JSON、YAML、CSS |

#### 操作步驟（以 Tokens Studio 為例）

1. 在 Figma 中開啟 **Plugins** → 搜尋 **Tokens Studio** → 安裝
2. 開啟插件面板
3. 它會自動讀取檔案中的 Variables 和 Styles
4. 點 **Export** → 選擇格式（推薦 CSS Variables）
5. 下載匯出的檔案
6. 將 Token 檔案放入專案，餵給 Claude Code 作為生成的參考

#### 匯出範例

```css
/* tokens.css — 從 Figma 匯出 */
:root {
  /* Colors */
  --color-primary: #2563EB;
  --color-primary-hover: #1D4ED8;
  --color-secondary: #64748B;
  --color-background: #FFFFFF;
  --color-surface: #F8FAFC;
  --color-text-primary: #0F172A;
  --color-text-secondary: #475569;
  --color-border: #E2E8F0;

  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;

  /* Typography */
  --font-family-primary: 'Inter', sans-serif;
  --font-size-sm: 14px;
  --font-size-base: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 24px;
  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-bold: 700;

  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;
}
```

---

### 情境一：綜合工作流

**最高效的組合方式（推薦順序）：**

```
第一次設定（約 20 分鐘，只需做一次）：
  1. 產生 Figma Personal Access Token
  2. 寫好 figma-extract.sh 提取腳本
  3. 安裝 Tokens Studio 插件，匯出 Design Tokens

每個元件的轉換流程（約 10-15 分鐘）：
  1. Figma 中選取目標 Frame → 複製 URL 取得 FILE_KEY 和 NODE_ID
  2. 執行 ./figma-extract.sh <FILE_KEY> <NODE_IDS>
  3. 在 Dev Mode 中 Copy 關鍵元素的 CSS（補充用）
  4. 截一張元件的完整截圖

  5. 在 Claude Code 中：
     ┌──────────────────────────────────────────────┐
     │ 請讀取以下檔案：                                │
     │   - ./figma-export/nodes.json（設計結構）       │
     │   - ./figma-export/variables.json（變數）       │
     │   - ./tokens.css（Design Tokens）              │
     │   - ./screenshots/component.png（視覺參考）     │
     │                                                │
     │ 根據 Figma 設計生成 React + Tailwind 元件。     │
     │ 使用 tokens.css 中的 CSS 變數。                 │
     │ 元件需要支援響應式。                             │
     └──────────────────────────────────────────────┘

  6. 渲染結果 → 截圖 → 與 Figma 原稿對比修正
```

---

## 3. 情境二：可使用 Figma MCP

### Figma MCP 是什麼

Figma MCP Server 是 Figma 官方推出的 Model Context Protocol 整合，讓 AI 編碼工具（Claude Code、Cursor 等）**直接存取 Figma 的設計數據**，不需要手動複製 CSS 或截圖。

### 兩種 Server 架構

| | Remote Server（推薦） | Desktop Server |
|---|---|---|
| **端點** | `https://mcp.figma.com/mcp` | `http://127.0.0.1:3845/mcp` |
| **需要桌面版 App？** | 否 | 是 |
| **功能完整度** | 全部 16 個工具 | 部分工具 |
| **認證方式** | OAuth（瀏覽器跳轉）| 桌面版 App 本地認證 |
| **需要網路？** | 是（到 Figma 雲端）| 是（桌面版仍連雲端）|
| **可寫入畫布？** | 是 | 否 |
| **方案要求** | 所有方案（有用量限制）| 付費方案的 Dev/Full 座位 |

> **封閉網路注意**：兩種 Server 都需要連接 Figma 雲端。如果你的瀏覽器能開 `figma.com`，MCP 也應該能通，因為它走同一個網路通道。如果公司防火牆允許 `figma.com` 但封鎖了 `mcp.figma.com`，需要請 IT 加白名單。

### Remote Server 設定（推薦）

#### 步驟 1：註冊 MCP Server

```bash
# 方式 1：透過 Claude Code 官方插件（如果市場可用）
claude plugin install figma@claude-plugins-official

# 方式 2：手動添加（推薦，不依賴插件市場）
# 專案範圍
claude mcp add --transport http figma https://mcp.figma.com/mcp

# 全域範圍（所有專案通用）
claude mcp add --transport http --scope user figma https://mcp.figma.com/mcp
```

#### 步驟 2：認證

1. 啟動 Claude Code
2. 輸入 `/mcp` 指令
3. 選擇 `figma`
4. 選擇 **Authenticate**
5. 瀏覽器會跳出 Figma OAuth 授權頁面 → 點同意
6. 回到 Claude Code → 連接確認

#### 步驟 3：驗證

```bash
# 在 Claude Code 中
/mcp
# 應看到 figma 狀態為 connected
```

### Desktop Server 設定

#### 步驟 1：啟用 Desktop Server

1. 開啟 Figma **桌面版 App**（需最新版）
2. 開啟一個 Design 檔案
3. 切換到 Dev Mode（`Shift+D`）
4. 在 Inspect 面板找到 MCP Server 區塊
5. 點 **Enable desktop MCP server**

#### 步驟 2：設定 Claude Code

```bash
claude mcp add --transport http figma-desktop http://127.0.0.1:3845/mcp
```

或手動編輯 `~/.claude/settings.json`：

```json
{
  "mcpServers": {
    "figma-desktop": {
      "url": "http://127.0.0.1:3845/mcp"
    }
  }
}
```

### 第三方替代：Figma-Context-MCP

> 如果官方 MCP 有問題，可以用社群版替代方案（~5000 GitHub Stars）。

```json
// .claude/settings.json 或 .mcp.json
{
  "mcpServers": {
    "figma-context": {
      "command": "npx",
      "args": [
        "-y",
        "figma-developer-mcp",
        "--figma-api-key=YOUR_PERSONAL_ACCESS_TOKEN",
        "--stdio"
      ]
    }
  }
}
```

**差異：**
- 使用 Personal Access Token 而非 OAuth
- 本地 Node.js 進程（npx 啟動）
- 回傳數據比官方精簡 99.5%（只保留佈局和樣式資訊）
- 適合對 API 速率限制敏感的場景
- GitHub：[GLips/Figma-Context-MCP](https://github.com/GLips/Figma-Context-MCP)

### Figma MCP 完整工具列表（16 個）

| 工具 | 功能 | 可用性 |
|------|------|--------|
| `get_design_context` | 取得選取圖層的結構化設計資訊，預設輸出 React + Tailwind 格式 | 兩者皆可 |
| `get_metadata` | 取得圖層 ID、名稱、類型、位置、尺寸（精簡 XML） | 兩者皆可 |
| `get_variable_defs` | 取得使用到的 Variables 和 Styles（Design Tokens） | 兩者皆可 |
| `get_screenshot` | 取得目前選取範圍的截圖 | 兩者皆可 |
| `get_code_connect_map` | 取得 Figma 節點與程式碼元件的對映關係 | 兩者皆可 |
| `add_code_connect_map` | 新增 Figma 節點與程式碼元件的對映 | 兩者皆可 |
| `get_code_connect_suggestions` | 自動偵測建議的 Figma-to-Code 元件對映 | 兩者皆可 |
| `send_code_connect_mappings` | 確認 Code Connect 對映 | 兩者皆可 |
| `search_design_system` | 搜尋設計庫中的元件、變數和樣式 | 兩者皆可 |
| `create_design_system_rules` | 建立規則檔，為設計轉代碼提供上下文 | 兩者皆可 |
| `use_figma` | 通用工具：建立、編輯、檢視任何 Figma 物件 | 僅 Remote |
| `generate_figma_design` | 從介面描述生成設計圖層 | 僅 Remote |
| `create_new_file` | 在草稿中建立新的 Design/FigJam 檔案 | 僅 Remote |
| `whoami` | 取得已認證使用者的身份資訊 | 僅 Remote |
| `get_figjam` | 取得 FigJam 的 metadata 和截圖 | 兩者皆可 |
| `generate_diagram` | 將 Mermaid 語法轉換為 FigJam 圖表 | 兩者皆可 |

### API 速率限制

| 方案 | 每日上限 | 每分鐘上限 |
|------|---------|-----------|
| Enterprise | 600 次/天 | 20 次/分 |
| Pro / Organization（Full/Dev 座位） | 200 次/天 | 15 次/分 |
| Starter / View / Collab 座位 | 6 次/月 | 10 次/分 |

### 情境二：MCP 工作流

#### 基本用法：一個 Prompt 搞定

```
在 Figma 中選取目標 Frame → 複製 URL

然後在 Claude Code 中：
┌──────────────────────────────────────────────────┐
│ 請實作這個 Figma 設計為 React + Tailwind 元件：    │
│ https://www.figma.com/design/ABC123/My-App        │
│   ?node-id=456-789                                │
│                                                    │
│ 使用 src/components/ui/ 下的現有元件。              │
│ 顏色使用 CSS 變數。                                 │
└──────────────────────────────────────────────────┘
```

Claude Code 會自動：
1. 呼叫 `get_design_context` 取得結構化設計描述
2. 呼叫 `get_variable_defs` 取得 Design Tokens
3. 呼叫 `get_screenshot` 取得視覺參考
4. 生成對應的前端代碼

#### 進階用法：Code Connect

Code Connect 讓 Figma 元件與你的程式碼元件建立對映，生成更精準的代碼：

```
# 1. 自動偵測建議的對映
Claude 會呼叫 get_code_connect_suggestions

# 2. 確認對映
Claude 會呼叫 send_code_connect_mappings

# 3. 之後每次轉換，都會優先使用你現有的元件
```

#### 進階用法：Design System Rules

```
請幫我建立 design system rules，
讓之後所有的 Figma 轉代碼都使用：
- React 18 + TypeScript
- Tailwind CSS v4
- 我們的 Button、Card、Input 元件（在 src/components/ui/）
- 顏色使用 --color-* CSS 變數
- 間距使用 Tailwind 的 spacing scale
```

Claude Code 會呼叫 `create_design_system_rules` 建立規則檔，之後的轉換都會遵循。

#### 完整標準流程

```
第一次設定（約 10 分鐘，只需做一次）：
  1. 設定 Figma MCP（上面的步驟）
  2. 認證 OAuth
  3. 建立 Design System Rules

每個元件/頁面的轉換流程（約 2-5 分鐘）：
  1. Figma 中選取目標 Frame
  2. 複製 URL
  3. 在 Claude Code 中貼上 URL + 指定需求
  4. 自動生成代碼
  5. 渲染檢查 → 要求修正（通常 1-2 輪即可）
```

---

## 4. 各情境效率比較

### 轉換一個中等複雜度元件（例如帶表單的 Card）

| 方法 | 設定時間 | 單次轉換時間 | 準確度 | 自動化程度 |
|------|---------|-------------|--------|-----------|
| Dev Mode Copy CSS | 0 | 15-20 分鐘 | 75% | 低（全手動）|
| REST API + 截圖 | 20 分鐘（首次） | 10-15 分鐘 | 85% | 中（腳本化）|
| 純截圖 | 0 | 10 分鐘 + 多輪修正 | 65% | 低 |
| **Figma MCP** | **10 分鐘（首次）** | **2-5 分鐘** | **90%** | **高（全自動）** |

### 轉換一整頁（5-8 個元件）

| 方法 | 預估總時間 |
|------|-----------|
| Dev Mode Copy CSS | 2-3 小時 |
| REST API + 截圖 | 1-2 小時 |
| 純截圖 | 2-4 小時（修正時間多）|
| **Figma MCP** | **20-40 分鐘** |

### 決策建議

```
能用 Figma MCP 嗎？
  ├── 是 → 情境二：直接用 MCP（效率最高）
  │         └── mcp.figma.com 被封？
  │               ├── 請 IT 加白名單
  │               └── 改用 Figma-Context-MCP（走 api.figma.com）
  │
  └── 否 → 情境一：
            ├── api.figma.com 能連嗎？
            │     ├── 能 → 方法 B：REST API（最推薦）
            │     └── 不能 → 方法 A + C 組合
            │
            └── 有 Dev Mode 座位嗎？
                  ├── 有 → 方法 A + C（Copy CSS + 截圖）
                  └── 沒有 → 方法 C + D（截圖 + 插件匯出 Token）
```

---

## 5. 附錄

### Figma REST API 主要端點速查

| 端點 | 方法 | 說明 |
|------|------|------|
| `/v1/files/:key` | GET | 取得完整檔案結構 |
| `/v1/files/:key/nodes?ids=` | GET | 取得指定節點子樹（推薦，資料量小） |
| `/v1/images/:key?ids=&format=` | GET | 匯出節點為圖片（png/jpg/svg/pdf） |
| `/v1/files/:key/images` | GET | 取得檔案中上傳圖片的 URL |
| `/v1/files/:key/variables/local` | GET | 取得本地變數（Design Tokens） |
| `/v1/files/:key/styles` | GET | 取得已發佈的 Styles |
| `/v1/files/:key/meta` | GET | 取得檔案 metadata |

### MCP 相關網路端點（給 IT 加白名單用）

如果需要請 IT 開放 MCP 相關存取：

| 端點 | 用途 |
|------|------|
| `mcp.figma.com` | Figma 官方 MCP Remote Server |
| `api.figma.com` | Figma REST API（Figma-Context-MCP 用） |
| `www.figma.com` | Figma 網頁版（應已開放） |
| `127.0.0.1:3845` | Figma Desktop MCP Server（純本地） |

### 檔案結構建議

```
project/
├── figma-export/           ← REST API 匯出的數據
│   ├── nodes.json
│   ├── variables.json
│   └── image_urls.json
├── screenshots/            ← Figma 截圖
│   ├── page-overview.png
│   ├── user-card.png
│   └── login-form.png
├── tokens/                 ← Design Tokens
│   ├── tokens.css
│   └── tokens.json
├── src/
│   └── components/         ← 生成的元件
├── figma-extract.sh        ← 提取腳本
└── .mcp.json               ← MCP 設定（情境二）
```
