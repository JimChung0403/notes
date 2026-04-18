# Claude Code 封閉網路安裝教學

## 0. 先講結論

`Claude Code` 可以做成 **離線安裝**，但**不能做成完全離線使用**。

原因：

- 安裝檔可以先在外網打包，再帶進公司內網安裝
- 但 `Claude Code` 官方要求：
  - 需要帳號登入
  - 需要網路做 authentication
  - 需要網路和模型服務互動

所以如果你公司網路是：

- **完全無法對外連線**

那 `Claude Code` 本身就**無法正常使用**。  
這種情況只能：

- 爭取有限白名單連線
- 走公司 proxy
- 或改用公司允許的模型閘道

如果你公司網路是：

- **平常封閉，但可開特定白名單 / proxy**

那就可以用這份 SOP。

---

## 1. 適用情境

這份文件適用於：

- 內網機器不能直接 `npm install`
- 但可從外部機器先下載套件
- 內網機器之後至少能透過白名單 / proxy 使用 Claude 服務
- 公司機器以 `Linux` 與 `Windows PowerShell` 為主

---

## 2. 你需要準備什麼

### 外網機器

用來先下載安裝包。

需要：

- Node.js 18+
- npm
- 可連外網

### 內網機器

用來真正使用 Claude Code。

需要：

- Node.js 18+
- npm
- shell 環境
- 至少能走公司允許的外連方式完成登入與 API 存取

支援建議：

- `Linux`
- `Windows PowerShell`

Windows 建議直接標準化在 `PowerShell 7` 或公司允許的 PowerShell 環境。

---

## 3. 外網機器準備安裝包

### Step 1

建立暫存目錄。

Linux:

```bash
mkdir -p ~/tmp/claude-code-offline
cd ~/tmp/claude-code-offline
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force "$HOME\\tmp\\claude-code-offline" | Out-Null
Set-Location "$HOME\\tmp\\claude-code-offline"
```

### Step 2

下載 Claude Code npm 套件：

```bash
npm pack @anthropic-ai/claude-code
```

這會產生一個 `.tgz` 檔。

### Step 3

把下面這些一起打包帶進內網：

- `@anthropic-ai/claude-code` 的 `.tgz`
- Node.js 安裝包
- 你們公司若需要的 CA / proxy 設定說明

建議再順手準備：

Linux:

```bash
shasum -a 256 *.tgz > SHA256SUMS.txt
```

PowerShell:

```powershell
Get-FileHash .\*.tgz -Algorithm SHA256 | Format-Table -AutoSize | Out-File .\SHA256SUMS.txt
```

---

## 4. 內網機器安裝

### Step 1

先安裝 Node.js 18+。

確認：

```bash
node -v
npm -v
```

### Step 2

進到你帶進來的目錄。

Linux:

```bash
cd /path/to/claude-code-offline
```

PowerShell:

```powershell
Set-Location "C:\path\to\claude-code-offline"
```

### Step 3

安裝本地 tarball：

```bash
npm install -g ./anthropic-ai-claude-code-*.tgz
```

### Step 4

確認：

```bash
claude --version
claude doctor
```

---

## 5. 內網使用前設定

### 如果公司走 HTTP/HTTPS proxy

Linux:

```bash
export HTTP_PROXY=http://proxy.company.local:port
export HTTPS_PROXY=http://proxy.company.local:port
export NO_PROXY=localhost,127.0.0.1,.company.local
```

如果要長期使用，就寫進：

- `~/.bashrc`
- 或 `~/.zshrc`

PowerShell:

```powershell
$env:HTTP_PROXY="http://proxy.company.local:port"
$env:HTTPS_PROXY="http://proxy.company.local:port"
$env:NO_PROXY="localhost,127.0.0.1,.company.local"
```

如果要長期使用，建議寫進 PowerShell profile：

```powershell
if (!(Test-Path $PROFILE)) { New-Item -ItemType File -Force $PROFILE | Out-Null }
Add-Content $PROFILE '$env:HTTP_PROXY="http://proxy.company.local:port"'
Add-Content $PROFILE '$env:HTTPS_PROXY="http://proxy.company.local:port"'
Add-Content $PROFILE '$env:NO_PROXY="localhost,127.0.0.1,.company.local"'
```

### 如果公司有自簽 CA

Node / npm 可能需要額外信任公司 CA。

這通常需要你們公司內部提供：

- CA 憑證檔
- 安裝方式

---

## 6. 第一次登入

### Step 1

啟動：

```bash
claude
```

### Step 2

依官方流程登入。

如果公司不能打開登入頁：

- 先確認 proxy / 白名單
- 再確認公司是否允許 `claude.ai` 相關流量

---

## 7. 建議順手安裝的本地工具

你這套 `run-prd` 會用到：

- `rg`
- `mvn`
- `git`

建議確認：

```bash
rg --version
mvn -v
git --version
```

---

## 8. 建議放進 repo 的 command

如果要配合這份 `run-prd` 套件，請把這些檔案放到專案：

- `.claude/commands/run-prd.md`
- `.claude/commands/coordinator.md`
- `.claude/commands/impact.md`
- `.claude/commands/verify-local.md`

使用時：

```text
/run-prd docs/prd/<PRD-ID>.md
```

---

## 9. 常見問題

### Q1. 能不能完全離線使用？

不能。  
安裝可以離線搬運，但使用時仍需要登入與模型連線。

### Q2. 內網不能連 `npm`，還能安裝嗎？

可以，只要你先在外網把 tarball 打包好。

### Q3. 什麼情況下不適合推 Claude Code？

如果公司完全不允許任何對外白名單 / proxy / gateway，  
那 `Claude Code` 不是合適方案。

---

## 10. 內部落地建議

如果你要帶去公司，我建議先確認這 4 件事：

1. 公司是否允許對模型服務做白名單
2. 公司是否已有 proxy
3. 公司是否允許 npm tarball 離線安裝
4. 公司是否能接受把 `.claude/commands/` 放進 repo

## 11. 你公司目前假設的推薦落地

依你目前提供的條件：

- 機器有 `Linux`
- 機器有 `Windows PowerShell`
- 內網可走 `proxy`
- 需要同時準備 `Claude Code` 與 `opencode`

建議公司版優先順序：

1. 先在 `Linux / PowerShell` 上標準化 CLI 環境
2. 先驗證 proxy 對 `Claude Code` 可用
3. 再補 `opencode` binary 版本
4. 再把 `run-prd/.claude/commands/` 放進公司 repo
