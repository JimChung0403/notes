# opencode 封閉網路安裝教學

## 0. 先講結論

`opencode` 可以比較容易做成 **離線安裝**，因為它本身是 CLI 工具。  
但它是否能在你公司內網正常使用，仍取決於：

- 你選的模型提供者
- 公司是否允許對該模型提供者連線
- 或公司是否有內部模型 gateway

另外要注意：

- `opencode-ai/opencode` 官方 GitHub repo 已經封存
- 專案後續已移轉到 `Crush`

如果你公司要追求長期可維護性，之後應評估是否直接改用新專案。

---

## 1. 適用情境

這份文件適用於：

- 你要先在外網下載 `opencode`
- 再帶進公司內網
- 並透過公司允許的模型連線方式使用
- 公司機器以 `Linux` 與 `Windows PowerShell` 為主

---

## 2. 安裝方式選擇

`opencode` 官方常見安裝方式有：

- install script
- Homebrew
- Go install

對封閉網路最實際的做法是：

- **外網先編譯或下載 binary**
- **內網直接放可執行檔**

不要依賴：

- install script 即時下載
- 內網直接 `go install`

---

## 3. 外網機器準備 binary

### 方式 A：直接下載 release binary

如果你們公司允許這種方式，外網機器先下載對應平台 binary。

下載後請一起保存：

- binary
- 版本資訊
- SHA256

### 方式 B：自己編譯

如果你想更可控：

Linux:

```bash
git clone <opencode repo>
cd opencode
go build -o opencode .
```

PowerShell:

```powershell
git clone <opencode repo>
Set-Location .\opencode
go build -o opencode.exe .
```

然後保存：

- `opencode`
- `opencode --version` 輸出
- `shasum -a 256 opencode`

---

## 4. 內網機器安裝

### Step 1

把 binary 放到可執行路徑。

Linux:

```bash
mkdir -p ~/bin
cp opencode ~/bin/
chmod +x ~/bin/opencode
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force "$HOME\\bin" | Out-Null
Copy-Item .\opencode.exe "$HOME\\bin\\opencode.exe" -Force
```

### Step 2

把安裝路徑放到 PATH。

Linux:

```bash
export PATH="$HOME/bin:$PATH"
```

建議寫進：

- `~/.bashrc`
- 或 `~/.zshrc`

PowerShell:

```powershell
$env:Path="$HOME\bin;$env:Path"
[Environment]::SetEnvironmentVariable("Path", "$HOME\bin;$([Environment]::GetEnvironmentVariable('Path','User'))", "User")
```

### Step 3

確認：

```text
opencode --help
```

---

## 5. 設定檔位置

`opencode` 會找這些設定檔位置：

- `$HOME/.opencode.json`
- `$XDG_CONFIG_HOME/opencode/.opencode.json`
- `./.opencode.json`

對公司環境，我建議：

- 個人機器放 `$HOME/.opencode.json`
- 專案級設定放 repo 裡的 `./.opencode.json`

---

## 6. 最小設定

你至少要提供模型提供者設定與金鑰來源。

常見做法：

- 直接環境變數
- 或設定檔指定 provider

例如若走 Anthropic：

Linux:

```bash
export ANTHROPIC_API_KEY=...
```

PowerShell:

```powershell
$env:ANTHROPIC_API_KEY="..."
```

如果公司不允許直接對外，則要改成：

- 公司 proxy
- 公司 gateway
- 公司統一發的 provider endpoint

---

## 7. 公司封閉網路下的使用建議

### 情境 A：公司可白名單特定模型供應商

這時可直接：

- 設定 API key
- 設定 proxy
- 啟動 `opencode`

proxy 例子：

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

### 情境 B：公司有內部 LLM gateway

這時要確認：

- `opencode` 是否能對接你們的 gateway
- provider / endpoint / auth 方式怎麼配

### 情境 C：公司完全不能對外

那 `opencode` 只有安裝能完成，AI 功能本身仍無法正常用。

---

## 8. 建議搭配的本地工具

若你要配合 `run-prd` 套件，內網還應至少有：

- `rg`
- `mvn`
- `git`

確認：

```text
rg --version
mvn -v
git --version
```

---

## 9. 建議如何放進公司環境

最穩的方式是：

1. 外網機器產出 binary
2. 產出 SHA256
3. 經公司檔案審核流程帶入
4. 內網機器放入 `~/bin`
5. 設定 provider / proxy / gateway

---

## 10. 常見問題

### Q1. 為什麼不直接用 install script？

因為封閉網路通常不能即時下載。

### Q2. `opencode` 能不能完全離線使用？

安裝可以離線搬運，  
AI 能力是否可用，仍取決於模型連線方式。

### Q3. 我公司如果要長期用，還建議選 opencode 嗎？

短期可行。  
長期則要再評估專案已封存這件事。

## 11. 你公司目前假設的推薦落地

依你目前提供的條件：

- 機器有 `Linux`
- 機器有 `Windows PowerShell`
- 內網可走 `proxy`
- 要同時準備 `Claude Code` 與 `opencode`

建議：

1. 把 `opencode` 先做成外網編譯 / 下載後帶入的 binary 包
2. 在 `Linux` 和 `PowerShell` 都測試一次 `PATH` 與 proxy
3. 再確認 `opencode` 對你們公司允許的模型 provider 是否能通
