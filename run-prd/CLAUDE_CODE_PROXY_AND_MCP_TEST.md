# Claude Code Proxy 與外部整合測試教學

這份文件的目的不是安裝 `Claude Code`，而是回答兩件事：

1. 怎麼在公司環境替 `Claude Code` 設定 proxy
2. 怎麼在公司環境驗證：`Claude Code` 能不能抓到外部整合能力

## 先講清楚

在官方文件裡，`Claude Code` 對外部工具與服務的正式擴充方式，主要是：

- `MCP servers`
- 外部整合

如果你公司內部平常說的「marketplace / 插件」，在 `Claude Code` 官方語境裡，最接近的通常就是：

- `MCP`
- 或 repo / user scope 的 commands、agents、settings

所以這份文件會把測試目標定義成：

- 驗證 `Claude Code` 能不能透過 proxy 正常對外
- 驗證能不能新增或存取外部 `MCP servers`

---

## 1. PowerShell 設定 proxy

### 臨時設定

在目前 PowerShell session：

```powershell
$env:HTTP_PROXY="http://proxy.company.local:port"
$env:HTTPS_PROXY="http://proxy.company.local:port"
```

如果公司 proxy 需要 basic auth：

```powershell
$env:HTTPS_PROXY="http://username:password@proxy.company.local:port"
```

### 長期設定

寫進 PowerShell profile：

```powershell
if (!(Test-Path $PROFILE)) { New-Item -ItemType File -Force $PROFILE | Out-Null }
Add-Content $PROFILE '$env:HTTP_PROXY="http://proxy.company.local:port"'
Add-Content $PROFILE '$env:HTTPS_PROXY="http://proxy.company.local:port"'
```

重新開一個 PowerShell，或執行：

```powershell
. $PROFILE
```

---

## 2. 如果公司有自簽 CA

若你們公司的 proxy 會攔 HTTPS，常見還要補：

```powershell
$env:SSL_CERT_FILE="C:\path\to\company-ca-bundle.crt"
$env:NODE_EXTRA_CA_CERTS="C:\path\to\company-ca-bundle.crt"
```

如果沒有這兩個設定，常見症狀會是：

- `certificate signed by unknown authority`
- TLS / SSL handshake 失敗

---

## 3. 先驗證 Claude Code 本體能不能走 proxy

### Step 1. 驗證 CLI

```powershell
claude --version
claude doctor
```

### Step 2. 驗證登入

```powershell
claude
```

你至少要確認：

- 可以正常啟動
- 可以進到互動介面
- 不會一開始就報 network / auth error

### Step 3. 驗證模型連線

進互動模式後，先跑一個最小測試：

```text
請只回一句：Claude Code proxy 測試正常。
```

如果這一步能正常回覆，代表：

- proxy 對 Claude 基本連線是通的
- authentication 流程大致可用

---

## 4. 測試外部整合能力

## 測試方式 A：列出目前 MCP 狀態

先在 shell 執行：

```powershell
claude mcp list
```

這一步的目的不是驗證外部連線，而是確認：

- `Claude Code` 的 `mcp` 子命令可用
- 目前環境沒有被公司策略鎖死

---

## 測試方式 B：新增一個公開 remote HTTP MCP server

這是最接近「能不能抓到外部 marketplace / 插件」的官方可測方式。

例如新增官方文件裡常見的 remote MCP：

```powershell
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp
```

或：

```powershell
claude mcp add --transport http notion https://mcp.notion.com/mcp
```

如果公司 proxy 能讓 `Claude Code` 連到外部 MCP 端點，這一步就應該成功。

成功後再驗證：

```powershell
claude mcp list
claude mcp get sentry
```

你要確認：

- server 有被寫進設定
- `claude mcp get <name>` 能看到設定內容

---

## 測試方式 C：測 OAuth 型 remote MCP

如果對方 server 需要 OAuth，可以進互動模式後執行：

```text
/mcp
```

然後照畫面指示做登入。

你要觀察：

- 是否能成功開啟登入流程
- 是否能完成 browser auth
- 是否能把 token 寫回本機設定

如果這一步被卡住，常見原因是：

- proxy 沒放行 OAuth 端點
- browser callback 被公司政策阻擋

---

## 5. 推薦的公司測試順序

建議按這個順序測：

### Level 1：Claude 本體

```powershell
claude --version
claude doctor
claude
```

### Level 2：模型服務

在互動模式裡問一句最小 prompt。

### Level 3：MCP 管理能力

```powershell
claude mcp list
```

### Level 4：外部 remote MCP

```powershell
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp
claude mcp get sentry
```

### Level 5：需要登入的整合

```text
/mcp
```

---

## 6. 什麼叫「測試通過」

如果你要判斷「公司環境能不能抓到外部 marketplace / 插件能力」，最低標準可以定成：

### 基本通過

- `Claude Code` 可正常啟動
- 可正常登入
- 可正常取得模型回覆

### 進階通過

- `claude mcp list` 可正常執行
- 可成功新增至少一個 remote MCP server
- 可透過 `claude mcp get <name>` 讀到設定

### 完整通過

- 可完成 `/mcp` OAuth 流程
- 可在互動模式中實際使用外部整合

---

## 7. 常見失敗點

### 1. Proxy 有設，但 Claude 還是連不上

先檢查：

- `HTTP_PROXY`
- `HTTPS_PROXY`
- 是否需要 company CA

### 2. `claude` 本體可用，但 `mcp add` 失敗

通常代表：

- 模型服務可通
- 但外部 MCP host 沒有被 proxy / firewall 放行

### 3. `mcp add` 成功，但 `/mcp` OAuth 卡住

通常代表：

- OAuth 網頁或 callback 被擋
- 公司瀏覽器政策或白名單不完整

### 4. Windows PowerShell 下 `npx` 型 local MCP 啟不起來

官方文件對 native Windows 有特別提醒：如果 local MCP 是用 `npx` 啟動，要加 `cmd /c` 包一層。

例如：

```powershell
claude mcp add my-server -- cmd /c npx -y @some/package
```

---

## 8. 建議你在公司怎麼實測

如果你的目標只是先回答：

> 公司環境到底能不能讓 Claude Code 用到外部整合？

最小測試流程就是：

1. 設好 proxy
2. 跑 `claude doctor`
3. 問一個最小 prompt
4. 跑 `claude mcp list`
5. 用 `claude mcp add --transport http ...` 加一個公開 remote MCP
6. 用 `claude mcp get <name>` 確認

如果 1 到 6 都通，基本可以判斷：

- `Claude Code` 的對外 proxy 沒問題
- 外部 MCP / integration 能力大致可用

---

## 9. 如果公司不能碰外部整合怎麼辦

那就不要把期待放在「抓 marketplace」。

你仍然可以用：

- `Claude Code` 本體
- repo 內的 `.claude/commands/*.md`
- `run-prd` 這套 workflow
- 公司內部自己的 `.mcp.json`

也就是說，即使外部整合被封，你這套本地流程仍然可以成立。
