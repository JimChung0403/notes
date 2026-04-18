# Qwen Code 封閉網路安裝教學

## 0. 先講結論

`Qwen Code` 可以做成 **離線安裝**，但是否能在公司內網正常使用，取決於：

- 你是用 `Qwen OAuth` 還是 `OpenAI-compatible API`
- 公司是否允許對外連線
- 是否可走 proxy
- 是否已有公司內部 LLM gateway

如果公司網路：

- **完全不能對外**

那通常只能：

- 走公司內部 gateway
- 或只完成安裝，不做實際 AI 使用

如果公司網路：

- **可走 proxy / 白名單**

那 `Qwen Code` 可以納入這套 `run-prd` workflow。

---

## 1. 適用情境

這份文件適用於：

- 你要先在外網下載 `Qwen Code`
- 再帶進公司內網
- 公司機器以 `Linux` 與 `Windows PowerShell` 為主
- 你希望它能和 `run-prd` 的本地 workflow 搭配

---

## 2. 你需要準備什麼

### 外網機器

需要：

- Node.js 20+
- npm
- 可連外網

### 內網機器

需要：

- Node.js 20+
- npm
- shell 環境
- 至少能透過 proxy / 白名單 / gateway 存取模型服務

支援建議：

- `Linux`
- `Windows PowerShell`

---

## 3. 外網機器準備安裝包

### Step 1

建立暫存目錄。

Linux:

```bash
mkdir -p ~/tmp/qwen-code-offline
cd ~/tmp/qwen-code-offline
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force "$HOME\\tmp\\qwen-code-offline" | Out-Null
Set-Location "$HOME\\tmp\\qwen-code-offline"
```

### Step 2

下載 npm 套件：

```text
npm pack @qwen-code/qwen-code@latest
```

### Step 3

建議一起打包帶進內網：

- `@qwen-code/qwen-code` 的 `.tgz`
- Node.js 安裝包
- proxy / CA / gateway 設定說明

建議再保存 SHA256：

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

先確認 Node.js 版本。

```text
node -v
npm -v
```

### Step 2

進到你帶進來的目錄。

Linux:

```bash
cd /path/to/qwen-code-offline
```

PowerShell:

```powershell
Set-Location "C:\path\to\qwen-code-offline"
```

### Step 3

安裝本地 tarball：

```text
npm install -g ./qwen-code-qwen-code-*.tgz
```

### Step 4

確認：

```text
qwen --version
qwen --help
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

PowerShell:

```powershell
$env:HTTP_PROXY="http://proxy.company.local:port"
$env:HTTPS_PROXY="http://proxy.company.local:port"
$env:NO_PROXY="localhost,127.0.0.1,.company.local"
```

### 驗證方式選擇

`Qwen Code` 有兩種常見做法：

#### 方式 A：`Qwen OAuth`

適合：

- 可打開登入頁
- 公司允許 `qwen.ai` 相關流量

啟動後可透過 `/auth` 完成登入。

#### 方式 B：`OpenAI-compatible API`

適合：

- 公司已有內部 gateway
- 或你們已有統一的 API endpoint

例如可設定：

Linux:

```bash
export OPENAI_API_KEY=...
export OPENAI_BASE_URL=...
export OPENAI_MODEL=...
```

PowerShell:

```powershell
$env:OPENAI_API_KEY="..."
$env:OPENAI_BASE_URL="..."
$env:OPENAI_MODEL="..."
```

---

## 6. 安裝後怎麼驗證有沒有 work

至少做這 6 步：

### Step 1. 驗證 CLI 已安裝

```text
qwen --version
qwen --help
```

### Step 2. 驗證互動模式能啟動

```text
qwen
```

至少要確認：

- 可以進入互動介面
- 不會一啟動就報 network / auth 錯誤

### Step 3. 驗證 auth 或 API 設定可用

如果走 `Qwen OAuth`：

- 進互動模式後執行 `/auth`
- 確認登入流程能完成

如果走 `OpenAI-compatible API`：

- 確認環境變數或 gateway 設定已生效

### Step 4. 驗證模型回覆正常

執行一個最小測試，例如：

```text
請只回一句：Qwen Code 連線正常。
```

### Step 5. 驗證本地工具鏈

```text
rg --version
mvn -v
git --version
```

### Step 6. 驗證能配合 `run-prd` 工作流

如果你準備在公司 repo 用這套流程，再確認：

- `.claude/commands/run-prd.md`
- `.claude/commands/coordinator.md`
- `.claude/commands/impact.md`
- `.claude/commands/verify-local.md`

都已放進專案。

### 最小驗收標準

滿足以下條件，就可以算可用：

- `qwen --version` 正常
- `qwen` 可啟動
- auth 或 API 設定可用
- 能得到一則正常模型回覆
- `rg` / `mvn` / `git` 都可用

---

## 7. 建議搭配的本地工具

若你要配合 `run-prd` 套件，內網至少還應有：

- `rg`
- `mvn`
- `git`

---

## 8. 常見問題

### Q1. `Qwen Code` 能完全離線使用嗎？

通常不能。  
安裝可離線搬運，但實際 AI 功能仍需要 auth 或模型 API。

### Q2. 公司內網只能走 proxy，可以用嗎？

可以，但你要先驗證：

- proxy 可用
- auth 流程可用
- 或 API endpoint 可用

### Q3. 適合拿來配 `run-prd` 嗎？

可以。  
只要它能在公司環境裡穩定完成：

- 啟動
- auth / API
- 基本回覆

就能和 `run-prd` 的本地 workflow 搭配。
