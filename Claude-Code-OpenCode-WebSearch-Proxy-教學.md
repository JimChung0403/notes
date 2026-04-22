# Claude Code / OpenCode 在公司 Proxy 下啟用 Web Search 教學

## 適用情境

你在公司封閉網路環境中工作。

- Chrome 瀏覽器已經透過公司 proxy 出網。
- 終端機直接 `curl` 外網會被防火牆阻擋。
- 你想讓 `claude` 與 `opencode` 的 web search 也能透過 proxy 出去。

這份文件整理目前可行的做法、設定方式、常見卡點，以及建議的導入順序。

---

## 先講結論

最優先的做法，不是先改 MCP，而是先讓 **CLI 行程本身** 走公司 proxy。

也就是先設定：

- `HTTPS_PROXY`
- `HTTP_PROXY`
- `NO_PROXY`

如果公司有 HTTPS 攔截或自簽 CA，再補：

- `NODE_EXTRA_CA_CERTS`

如果公司 proxy 不是一般帳密，而是：

- NTLM
- Kerberos
- SSO / 企業單一登入

那就不要硬拗 `username:password@proxy`，通常要改走 **LLM Gateway** 或公司內部代理服務。

---

## 工具行為差異

### Claude Code

Claude Code 官方支援標準 `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY` 環境變數。

實務上只要 Claude Code 這個 process 能透過 proxy 對外連線，內建的 web 能力通常就會恢復可用。

### OpenCode

OpenCode 也支援標準 proxy 環境變數。

但要注意一件事：

OpenCode 的 TUI 會跟本機 HTTP server 溝通，所以一定要繞過本機位址，不然可能產生 routing loop。

建議至少設定：

```bash
export NO_PROXY=localhost,127.0.0.1
```

---

## 方案一：直接用公司 Proxy

如果公司 proxy 是一般 HTTP/HTTPS proxy，而且支援 Basic Auth，先試這個。

### Bash / zsh

```bash
export HTTPS_PROXY=http://USER:PASSWORD@proxy.company.com:8080
export HTTP_PROXY=http://USER:PASSWORD@proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1
```

然後再啟動：

```bash
claude
```

或：

```bash
OPENCODE_ENABLE_EXA=1 opencode
```

### 比較安全的寫法

不要把密碼硬寫死在共用腳本裡，改成分開設定：

```bash
export PROXY_USER='your-user'
export PROXY_PASS='your-password'
export HTTPS_PROXY="http://${PROXY_USER}:${PROXY_PASS}@proxy.company.com:8080"
export HTTP_PROXY="http://${PROXY_USER}:${PROXY_PASS}@proxy.company.com:8080"
export NO_PROXY=localhost,127.0.0.1
```

---

## 方案二：把 Claude Code Proxy 設定寫進 settings.json

如果你希望每次開 `claude` 都自動帶 proxy，可以寫進：

`~/.claude/settings.json`

範例：

```json
{
  "env": {
    "HTTPS_PROXY": "http://USER:PASSWORD@proxy.company.com:8080",
    "HTTP_PROXY": "http://USER:PASSWORD@proxy.company.com:8080",
    "NO_PROXY": "localhost,127.0.0.1"
  }
}
```

建議做法：

- `settings.json` 只放在自己家目錄，不要放進 git repo。
- 如果密碼敏感，改成 shell 啟動腳本或公司密碼保管工具注入。

---

## 方案三：OpenCode 啟動腳本

OpenCode 比較適合包成一個啟動 script。

例如建立 `~/bin/opencode-corp`：

```bash
#!/usr/bin/env bash
export PROXY_USER='your-user'
export PROXY_PASS='your-password'
export HTTPS_PROXY="http://${PROXY_USER}:${PROXY_PASS}@proxy.company.com:8080"
export HTTP_PROXY="http://${PROXY_USER}:${PROXY_PASS}@proxy.company.com:8080"
export NO_PROXY=localhost,127.0.0.1
export OPENCODE_ENABLE_EXA=1

exec opencode "$@"
```

加執行權限：

```bash
chmod +x ~/bin/opencode-corp
```

之後直接執行：

```bash
opencode-corp
```

---

## 方案四：公司有 HTTPS 攔截或自簽 CA

如果你遇到這類錯誤：

- certificate verify failed
- unable to get local issuer certificate
- self signed certificate in certificate chain

通常不是 proxy 沒設好，而是 **公司 TLS 憑證沒有被 CLI 信任**。

這時候要補：

```bash
export NODE_EXTRA_CA_CERTS=/path/to/corp-ca.pem
```

然後搭配：

```bash
export HTTPS_PROXY=http://USER:PASSWORD@proxy.company.com:8080
export HTTP_PROXY=http://USER:PASSWORD@proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1
```

如果你的公司根憑證已經安裝在作業系統 trust store，某些情況下 Claude Code native binary 可能可直接工作；但若是 Node runtime 或其他 Node-based 工具，`NODE_EXTRA_CA_CERTS` 仍然很常需要補。

---

## 方案五：公司 Proxy 是 NTLM / Kerberos / SSO

如果公司 proxy 不是 Basic Auth，而是：

- NTLM
- Kerberos
- SSO 驗證

那你多半不能只靠：

```bash
export HTTPS_PROXY=http://USER:PASSWORD@proxy.company.com:8080
```

這種情況建議走以下其中一條：

### 做法 A：公司提供可用的 HTTP/HTTPS 中繼 Proxy

請 IT 提供一個你可在 CLI 直接使用的 proxy endpoint。

### 做法 B：LLM Gateway

把 Claude Code / OpenCode 指到公司內部 gateway，再由 gateway 代你處理：

- 驗證
- 路由
- 稽核
- 外連

Claude Code 可用：

```bash
export ANTHROPIC_BASE_URL=https://your-gateway.company.com
```

OpenCode 則可在 `opencode.json` 指定 provider 的 `baseURL`。

範例：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "anthropic": {
      "options": {
        "baseURL": "https://your-gateway.company.com/v1"
      }
    }
  }
}
```

這條路比較像企業正式解法。

---

## MCP 能不能解這個問題

可以，但要分清楚用途。

### MCP 不一定能修好內建 web search

如果你現在用的是工具內建的：

- Claude Code `WebSearch`
- OpenCode `websearch`

那問題通常在於：

- 主程式本身無法出網
- 主程式無法連到外部服務
- TLS / 憑證不通

這種情況先修 **process-level proxy** 才是正解。

### MCP 比較像替代方案

如果公司不允許直接連：

- Anthropic
- Exa
- 公網搜尋服務

但允許你連公司自己的：

- 內部搜尋 API
- 內部知識庫
- 內部 gateway

那你可以改接一個自己的 MCP search server，讓 agent 改走那條路。

換句話說：

- 要救內建 web search：先設 proxy / CA / gateway。
- 要替代內建 web search：再考慮 MCP。

---

## Claude Code 的 MCP 設定方向

Claude Code 可以：

- 接 remote HTTP MCP server
- 接 local stdio MCP server
- 對 local MCP 傳 `--env`
- 對 remote MCP 傳 `--header`

如果你有公司內部搜尋 MCP，可這樣加：

```bash
claude mcp add --transport http corp-search https://search.company.com/mcp \
  --header "Authorization: Bearer YOUR_TOKEN"
```

如果你是本機啟動一個 MCP server：

```bash
claude mcp add --transport stdio --env HTTPS_PROXY=http://proxy.company.com:8080 corp-search \
  -- python corp_search_mcp.py
```

適合場景：

- 公司有自己的搜尋服務。
- 你想繞過內建 web search 的限制。
- 你要把帳號密碼、header、token 控制在自己的 MCP 流程裡。

---

## OpenCode 的 MCP 設定方向

OpenCode 也支援：

- local MCP
- remote MCP
- local MCP 的 `environment`
- remote MCP 的 `headers`

所以如果內建 `websearch` 走不出去，可以改接你自己的 MCP。

概念範例：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "corp-search": {
      "type": "remote",
      "url": "https://search.company.com/mcp",
      "headers": {
        "Authorization": "Bearer {env:CORP_SEARCH_TOKEN}"
      },
      "enabled": true
    }
  }
}
```

如果是 local MCP：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "corp-search-local": {
      "type": "local",
      "command": ["python", "corp_search_mcp.py"],
      "environment": {
        "HTTPS_PROXY": "http://proxy.company.com:8080",
        "HTTP_PROXY": "http://proxy.company.com:8080",
        "NO_PROXY": "localhost,127.0.0.1"
      },
      "enabled": true
    }
  }
}
```

---

## 建議的導入順序

### 最簡單版

1. 先設 `HTTPS_PROXY` / `HTTP_PROXY` / `NO_PROXY`
2. 再測 `claude` / `opencode`
3. 若 TLS 錯誤，再補 `NODE_EXTRA_CA_CERTS`

### 企業穩定版

1. 跟 IT 確認 proxy 類型是 Basic、NTLM、Kerberos 還是 SSO
2. Basic Auth 才直接用 proxy URL
3. 非 Basic Auth 就改走 LLM Gateway
4. 若內建 web search 還是不通，再評估公司內部 MCP search

---

## 快速排錯清單

### 症狀：CLI 完全不能出網

先檢查：

- `HTTPS_PROXY` 是否有設
- proxy host / port 是否正確
- 帳密是否正確
- 公司防火牆是否允許這台機器走該 proxy

### 症狀：有走 proxy 但 TLS 失敗

先檢查：

- 公司 CA 是否已安裝
- `NODE_EXTRA_CA_CERTS` 是否指到正確憑證
- 憑證是否 PEM 格式

### 症狀：OpenCode 啟動怪怪的、web 模式或 TUI 連不上本機

先檢查：

- `NO_PROXY=localhost,127.0.0.1` 是否有設

### 症狀：公司 proxy 是 NTLM / Kerberos

先不要浪費時間在 `username:password@proxy`。

直接問 IT：

- 有沒有提供 CLI 可用的 proxy endpoint
- 有沒有公司內部 LLM gateway
- 有沒有統一的 outbound gateway / API gateway

---

## 建議你現在就先做的事

如果你要最快驗證，先試這組：

```bash
export HTTPS_PROXY=http://USER:PASSWORD@proxy.company.com:8080
export HTTP_PROXY=http://USER:PASSWORD@proxy.company.com:8080
export NO_PROXY=localhost,127.0.0.1
export NODE_EXTRA_CA_CERTS=/path/to/corp-ca.pem
```

然後：

```bash
claude
```

以及：

```bash
OPENCODE_ENABLE_EXA=1 opencode
```

如果這樣還不通，再把問題分類成下面三種：

1. Proxy 驗證問題
2. TLS / CA 問題
3. 外部服務被公司策略阻擋

第三種通常就要改走公司 gateway 或自建 MCP 搜尋服務。

---

## 最後建議

真正可長期維護的順序通常是：

1. 先讓 CLI process 能走公司 proxy
2. 再補公司 CA
3. 再決定是否要上 LLM gateway
4. 最後才考慮 MCP 當替代搜尋方案

如果你只是想「讓它先能用」，先不要一開始就把問題做複雜。大多數情況先把 `HTTPS_PROXY`、`NO_PROXY`、`NODE_EXTRA_CA_CERTS` 設對，就已經能解掉一大半問題。
