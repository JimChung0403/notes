# Claude Code LSP 離線/封閉網路環境使用 SOP

> 適用情境：公司網路封閉，無法直接連接 Anthropic API，透過 Claude Code Router + OpenAI Compatible API 使用 Claude Code CLI，但插件市場無法存取。

---

## 目錄

1. [背景與架構說明](#1-背景與架構說明)
2. [核心觀念釐清](#2-核心觀念釐清)
3. [方案總覽](#3-方案總覽)
4. [方案 A：本地 Marketplace（推薦）](#4-方案-a本地-marketplace推薦)
5. [方案 B：cclsp MCP Bridge（最簡單）](#5-方案-bcclsp-mcp-bridge最簡單)
6. [方案 C：--plugin-dir 直接載入](#6-方案-c--plugin-dir-直接載入)
7. [語言伺服器安裝指引](#7-語言伺服器安裝指引)
8. [驗證與除錯](#8-驗證與除錯)
9. [常見問題 FAQ](#9-常見問題-faq)

---

## 1. 背景與架構說明

### 你目前的環境

```
┌─────────────────────────────────────────────────────┐
│  公司封閉網路                                         │
│                                                     │
│  Claude Code CLI                                    │
│       │                                             │
│       ▼                                             │
│  Claude Code Router (本地代理)                       │
│       │                                             │
│       ▼                                             │
│  OpenAI Compatible API (公司內部 LLM)                │
│                                                     │
│  ✗ 無法連接 api.anthropic.com                        │
│  ✗ 無法連接 GitHub（插件市場不可用）                    │
└─────────────────────────────────────────────────────┘
```

### LSP 加入後的架構

```
┌─────────────────────────────────────────────────────┐
│  Claude Code CLI                                    │
│       │                                             │
│       ├── LLM API ──► Claude Code Router ──► 內部LLM │
│       │                                             │
│       └── LSP Plugin（本地）                          │
│              │                                      │
│              ▼                                      │
│         Language Server（本地進程，不需網路）           │
│         例：typescript-language-server               │
│             pyright-langserver                       │
│             gopls                                   │
└─────────────────────────────────────────────────────┘
```

---

## 2. 核心觀念釐清

### LSP 與 LLM API 是完全獨立的兩個系統

| 項目 | LLM API（大腦） | LSP（代碼分析） |
|------|-----------------|----------------|
| 用途 | AI 對話、生成代碼 | 語法檢查、跳轉定義、找引用 |
| 需要網路？ | 是（連接 LLM） | **否（純本地進程）** |
| 你的現況 | ✅ 已透過 Router 解決 | ❌ 需要解決安裝問題 |

### LSP 能提供什麼？

一旦啟用 LSP，Claude Code 將獲得：

- **自動診斷**：每次編輯後，語言伺服器自動回報型別錯誤、缺少 import 等問題
- **程式碼導航**：跳轉到定義、查找引用、符號搜尋（毫秒級，比 grep 快數十倍）
- **重構支援**：跨檔案重新命名符號
- **Hover 文檔**：查看函數簽名和文檔

### 為什麼插件市場不能用？

Claude Code 的官方插件市場 (`claude-plugins-official`) 託管在 GitHub 上。封閉網路無法存取 GitHub，因此：
- `/plugin` 指令的 Discover 頁籤無法載入
- 線上安裝插件會失敗

**解決方案**：在本地建立插件結構，完全繞過線上市場。

---

## 3. 方案總覽

| 方案 | 難度 | 適合場景 | 需要修改 |
|------|------|---------|---------|
| **A：本地 Marketplace** | ⭐⭐ 中等 | 團隊共用、多語言支援 | 建立目錄結構 + 註冊 marketplace |
| **B：cclsp MCP Bridge** | ⭐ 最簡單 | 個人使用、快速上手 | 安裝 cclsp + 設定 MCP |
| **C：--plugin-dir** | ⭐⭐ 中等 | 臨時測試、單一插件 | 建立插件目錄 + 啟動參數 |

**推薦**：
- 個人快速上手 → 選方案 B
- 團隊標準化部署 → 選方案 A

---

## 4. 方案 A：本地 Marketplace（推薦）

### 步驟 1：建立本地 Marketplace 目錄結構

```bash
# 在專案或共享位置建立 marketplace
mkdir -p ~/.claude-local-marketplace/.claude-plugin
mkdir -p ~/.claude-local-marketplace/plugins/typescript-lsp
mkdir -p ~/.claude-local-marketplace/plugins/pyright-lsp
```

### 步驟 2：建立 marketplace.json

建立檔案 `~/.claude-local-marketplace/.claude-plugin/marketplace.json`：

```json
{
  "name": "local-lsp-plugins",
  "owner": {
    "name": "Local Team"
  },
  "plugins": [
    {
      "name": "typescript-lsp",
      "description": "TypeScript/JavaScript LSP support",
      "version": "1.0.0",
      "source": "./plugins/typescript-lsp",
      "strict": false,
      "lspServers": {
        "typescript": {
          "command": "typescript-language-server",
          "args": ["--stdio"],
          "extensionToLanguage": {
            ".ts": "typescript",
            ".tsx": "typescriptreact",
            ".js": "javascript",
            ".jsx": "javascriptreact"
          }
        }
      }
    },
    {
      "name": "pyright-lsp",
      "description": "Python LSP support (Pyright)",
      "version": "1.0.0",
      "source": "./plugins/pyright-lsp",
      "strict": false,
      "lspServers": {
        "pyright": {
          "command": "pyright-langserver",
          "args": ["--stdio"],
          "extensionToLanguage": {
            ".py": "python"
          }
        }
      }
    }
  ]
}
```

### 步驟 3：建立插件目錄（每個插件需要一個 README.md）

```bash
# TypeScript LSP
cat > ~/.claude-local-marketplace/plugins/typescript-lsp/README.md << 'EOF'
# TypeScript LSP Plugin
Provides TypeScript/JavaScript language server support for Claude Code.
EOF

# Python LSP
cat > ~/.claude-local-marketplace/plugins/pyright-lsp/README.md << 'EOF'
# Pyright LSP Plugin
Provides Python language server support for Claude Code.
EOF
```

### 步驟 4：安裝語言伺服器二進位檔

```bash
# TypeScript（使用公司內部 npm registry）
npm install -g typescript-language-server typescript \
  --registry=https://your-internal-npm-registry.company.com

# Python
pip install pyright \
  --index-url=https://your-internal-pypi.company.com/simple

# 驗證安裝
which typescript-language-server  # 應該有輸出
which pyright-langserver          # 應該有輸出
```

> **如果公司沒有內部 registry**：在有網路的電腦上下載 npm 包（`npm pack`），用 USB 或其他方式傳入，再 `npm install -g <tarball>`。

### 步驟 5：註冊本地 Marketplace

在 Claude Code CLI 中執行：

```
/plugin marketplace add ~/.claude-local-marketplace
```

或者手動編輯 `~/.claude/settings.json`：

```json
{
  "extraKnownMarketplaces": {
    "local-lsp-plugins": {
      "source": {
        "source": "local",
        "path": "/Users/你的用戶名/.claude-local-marketplace"
      }
    }
  }
}
```

### 步驟 6：安裝插件

在 Claude Code CLI 中：

```
/plugin install typescript-lsp@local-lsp-plugins
/plugin install pyright-lsp@local-lsp-plugins
```

### 步驟 7：啟用並重載

```bash
# 確保 settings.json 中有啟用
# ~/.claude/settings.json
{
  "env": {
    "ENABLE_LSP_TOOL": "1"
  },
  "enabledPlugins": {
    "typescript-lsp@local-lsp-plugins": true,
    "pyright-lsp@local-lsp-plugins": true
  }
}
```

在 Claude Code 中重載插件：

```
/reload-plugins
```

---

## 5. 方案 B：cclsp MCP Bridge（最簡單）

> cclsp 是一個獨立的 MCP Server，完全繞過 Claude Code 的插件系統，直接透過 MCP 協議橋接 LSP 功能。

### 步驟 1：安裝 cclsp

```bash
# 使用內部 npm registry
npm install -g cclsp \
  --registry=https://your-internal-npm-registry.company.com

# 或者離線安裝：在有網路的電腦上
npm pack cclsp        # 產生 cclsp-x.x.x.tgz
# 傳入公司電腦後
npm install -g cclsp-x.x.x.tgz
```

### 步驟 2：安裝語言伺服器

```bash
# 同方案 A 步驟 4
npm install -g typescript-language-server typescript
pip install pyright
# 或其他你需要的語言伺服器
```

### 步驟 3：建立 cclsp 設定檔

建立檔案 `~/.config/cclsp/cclsp.json`（或專案根目錄下 `cclsp.json`）：

```json
{
  "servers": [
    {
      "extensions": ["ts", "js", "tsx", "jsx"],
      "command": ["typescript-language-server", "--stdio"],
      "rootDir": "."
    },
    {
      "extensions": ["py"],
      "command": ["pyright-langserver", "--stdio"],
      "rootDir": "."
    },
    {
      "extensions": ["go"],
      "command": ["gopls", "serve"],
      "rootDir": "."
    },
    {
      "extensions": ["rs"],
      "command": ["rust-analyzer"],
      "rootDir": "."
    }
  ]
}
```

### 步驟 4：註冊為 MCP Server

編輯 `~/.claude/settings.json`（全域生效）或專案的 `.claude/settings.json`：

```json
{
  "mcpServers": {
    "cclsp": {
      "command": "cclsp",
      "args": [],
      "env": {
        "CCLSP_CONFIG_PATH": "/Users/你的用戶名/.config/cclsp/cclsp.json"
      }
    }
  }
}
```

### 步驟 5：重啟 Claude Code

```bash
# 退出再重新啟動
claude
```

### cclsp 提供的工具

啟用後，Claude Code 會獲得以下 MCP 工具：

| 工具名稱 | 功能 |
|----------|------|
| `find_definition` | 跳轉到函數/符號定義 |
| `find_references` | 查找所有引用 |
| `rename_symbol` | 跨檔案重新命名（支援 dry-run） |
| `get_diagnostics` | 取得語法錯誤/警告 |
| `restart_server` | 重啟語言伺服器 |

> **cclsp 的優勢**：它會自動處理 LLM 回傳位置不精確的問題，嘗試多種位置組合來找到正確的符號，對 AI 輔助開發更友善。

---

## 6. 方案 C：--plugin-dir 直接載入

> 適合臨時測試或只需要一個 LSP 插件的場景。

### 步驟 1：建立插件目錄

```bash
mkdir -p ~/claude-plugins/typescript-lsp/.claude-plugin
```

### 步驟 2：建立 plugin.json

`~/claude-plugins/typescript-lsp/.claude-plugin/plugin.json`：

```json
{
  "name": "typescript-lsp",
  "version": "1.0.0",
  "description": "TypeScript LSP for Claude Code"
}
```

### 步驟 3：建立 .lsp.json

`~/claude-plugins/typescript-lsp/.lsp.json`：

```json
{
  "typescript": {
    "command": "typescript-language-server",
    "args": ["--stdio"],
    "extensionToLanguage": {
      ".ts": "typescript",
      ".tsx": "typescriptreact",
      ".js": "javascript",
      ".jsx": "javascriptreact"
    }
  }
}
```

### 步驟 4：啟動 Claude Code 時指定插件目錄

```bash
claude --plugin-dir ~/claude-plugins/typescript-lsp
```

> 注意：每次啟動都需要加 `--plugin-dir` 參數。如果需要多個插件，可以多次指定：
> ```bash
> claude --plugin-dir ~/claude-plugins/typescript-lsp \
>        --plugin-dir ~/claude-plugins/pyright-lsp
> ```

---

## 7. 語言伺服器安裝指引

### 各語言的語言伺服器安裝方式

| 語言 | 伺服器名稱 | 安裝指令 | 二進位名稱 |
|------|-----------|---------|-----------|
| TypeScript/JS | typescript-language-server | `npm i -g typescript-language-server typescript` | `typescript-language-server` |
| Python | Pyright | `pip install pyright` | `pyright-langserver` |
| Python | pylsp | `pip install python-lsp-server` | `pylsp` |
| Go | gopls | `go install golang.org/x/tools/gopls@latest` | `gopls` |
| Rust | rust-analyzer | `rustup component add rust-analyzer` | `rust-analyzer` |
| C/C++ | clangd | 隨 LLVM 安裝 | `clangd` |
| Java | jdtls | 需手動下載 Eclipse JDT LS | `jdtls` |
| C# | csharp-ls | `dotnet tool install -g csharp-ls` | `csharp-ls` |
| PHP | Intelephense | `npm i -g intelephense` | `intelephense` |
| Kotlin | kotlin-language-server | 需從 GitHub Release 下載 | `kotlin-language-server` |
| Lua | lua-language-server | 需從 GitHub Release 下載 | `lua-language-server` |
| Swift | sourcekit-lsp | 隨 Xcode 安裝 | `sourcekit-lsp` |

### 離線安裝策略

如果公司完全沒有內部 registry：

```bash
# === 在有網路的電腦上操作 ===

# 1. npm 套件：打包為 tarball
npm pack typescript-language-server
npm pack typescript
# 會產生 typescript-language-server-x.x.x.tgz 和 typescript-x.x.x.tgz

# 2. pip 套件：下載 wheel
pip download pyright -d ./pyright-wheels/

# 3. Go 套件：交叉編譯
GOOS=darwin GOARCH=arm64 go install golang.org/x/tools/gopls@latest
# 二進位檔在 $GOPATH/bin/ 下

# === 傳入公司電腦後 ===

# npm tarball 安裝
npm install -g typescript-language-server-x.x.x.tgz typescript-x.x.x.tgz

# pip wheel 安裝
pip install --no-index --find-links=./pyright-wheels/ pyright

# Go 直接複製二進位到 PATH
cp gopls /usr/local/bin/
```

---

## 8. 驗證與除錯

### 驗證 LSP 是否正常運作

#### 方法 1：確認語言伺服器可執行

```bash
# 應該回傳版本號或啟動提示
typescript-language-server --version
pyright-langserver --version
gopls version
```

#### 方法 2：在 Claude Code 中測試

啟動 Claude Code 後，開啟一個有型別錯誤的檔案，詢問 Claude：

```
請幫我檢查這個檔案有沒有型別錯誤
```

如果 LSP 正常運作，Claude 會**自動**從語言伺服器獲取診斷資訊，而不需要執行編譯器。

#### 方法 3：檢查插件載入狀態

```
/plugin list
```

應該能看到你安裝的 LSP 插件狀態為 enabled。

#### 方法 4（cclsp 方案）：確認 MCP 工具可用

在 Claude Code 中輸入：

```
你有哪些 MCP 工具可以用？
```

應該能看到 `find_definition`、`find_references`、`get_diagnostics` 等工具。

### 常見錯誤排查

| 問題 | 可能原因 | 解決方式 |
|------|---------|---------|
| 找不到語言伺服器 | 二進位不在 PATH 中 | `which typescript-language-server` 確認，或在 .lsp.json 中使用絕對路徑 |
| 插件未載入 | settings.json 格式錯誤 | 用 `cat ~/.claude/settings.json \| python -m json.tool` 驗證 JSON |
| LSP 工具未出現 | 未設定 ENABLE_LSP_TOOL | 在 settings.json 的 env 中加入 `"ENABLE_LSP_TOOL": "1"` |
| cclsp 無回應 | 設定路徑錯誤 | 確認 CCLSP_CONFIG_PATH 指向正確的 cclsp.json |
| 市場註冊失敗 | 路徑格式問題 | 使用絕對路徑，確認 marketplace.json 存在 |

### 使用絕對路徑（推薦用於封閉環境）

如果語言伺服器不在系統 PATH 中，可以在設定中使用絕對路徑：

```json
{
  "typescript": {
    "command": "/usr/local/bin/typescript-language-server",
    "args": ["--stdio"],
    "extensionToLanguage": {
      ".ts": "typescript"
    }
  }
}
```

---

## 9. 常見問題 FAQ

### Q1：LSP 功能需要網路嗎？

**不需要。** LSP 是純本地功能。語言伺服器作為本地進程運行，分析的是本機磁碟上的代碼。唯一需要網路的環節是**安裝**語言伺服器二進位檔，這可以透過離線方式完成。

### Q2：方案 A 和方案 B 可以同時使用嗎？

**可以。** 它們走不同的通道（A 走插件系統，B 走 MCP），互不衝突。但建議選一種即可，避免同一個語言被兩個 LSP 同時處理。

### Q3：Claude Code Router 會影響 LSP 嗎？

**不會。** Router 只負責轉發 LLM API 請求，與 LSP 完全無關。

### Q4：哪個方案效能最好？

方案 A（本地 Marketplace）使用 Claude Code 原生的 LSP 整合，**診斷是自動觸發**的（每次檔案編輯後自動執行）。方案 B（cclsp）需要 Claude 主動調用 MCP 工具才能獲取診斷。原生整合在自動化程度上更好。

### Q5：如何新增其他語言的 LSP 支援？

在 marketplace.json（方案 A）或 cclsp.json（方案 B）中新增對應設定即可，格式參照已有的語言設定。關鍵是：
1. 安裝該語言的語言伺服器二進位
2. 在設定中註冊 command、args 和副檔名對映

### Q6：團隊共用怎麼做？

推薦方案 A。將本地 marketplace 目錄放入版本控制（Git），團隊成員 clone 後執行：

```bash
/plugin marketplace add /path/to/shared-marketplace
/plugin install typescript-lsp@local-lsp-plugins
```

或將 marketplace 路徑寫入專案的 `.claude/settings.json`，所有人自動生效。

---

## 快速開始 Checklist

### 最快路徑（方案 B，5 分鐘搞定）

- [ ] 1. 安裝 cclsp：`npm install -g cclsp`
- [ ] 2. 安裝語言伺服器：`npm install -g typescript-language-server typescript`
- [ ] 3. 建立 `~/.config/cclsp/cclsp.json`（見方案 B 步驟 3）
- [ ] 4. 編輯 `~/.claude/settings.json` 註冊 MCP（見方案 B 步驟 4）
- [ ] 5. 重啟 Claude Code
- [ ] 6. 測試：請 Claude 找某個函數的定義

### 團隊標準化路徑（方案 A）

- [ ] 1. 建立 marketplace 目錄結構
- [ ] 2. 編寫 marketplace.json
- [ ] 3. 安裝所有需要的語言伺服器二進位
- [ ] 4. 註冊本地 marketplace
- [ ] 5. 安裝並啟用插件
- [ ] 6. 設定 `ENABLE_LSP_TOOL=1`
- [ ] 7. 提交 marketplace 目錄到版本控制供團隊使用
