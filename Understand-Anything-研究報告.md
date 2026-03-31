# Understand-Anything 研究報告

## 研究目標

本報告研究 GitHub 專案 `Lum1104/Understand-Anything`，回答一個核心問題：

> 它是透過哪些 agent skill 步驟，把一個完全沒看過的 repository，轉成可視化知識圖，並進一步分析其邏輯與架構？

---

## 一句話結論

`Understand-Anything` 的核心不是「一次把整個 repo 丟給模型」，而是把理解流程拆成一條多階段、多子代理（multi-agent）的工作鏈：

1. 先做 deterministic 掃描，建立檔案清單、語言、框架與 import map。
2. 再把檔案切 batch，平行分析每一批檔案中的 function、class、import 與關係。
3. 把每批結果合併成知識圖節點與邊。
4. 針對整體圖做 layer 分層與 guided tour。
5. 最後驗證、修補、保存成 `.understand-anything/knowledge-graph.json`，再由 dashboard 顯示成互動式圖。

換句話說，它是「靜態分析 + LLM 補語意 + 後處理正規化 + 視覺化」的組合式流程，而不是單一步驟。

---

## 專案是什麼

`Understand-Anything` 的 README 將它定義為：把任何 codebase 轉成可探索、可搜尋、可提問的 interactive knowledge graph。主流程命令是 `/understand`，輸出知識圖到 `.understand-anything/knowledge-graph.json`；再用 `/understand-dashboard` 打開互動式圖形介面。這個 repo 同時支援 Claude Code、Codex、OpenCode、OpenClaw、Cursor、VS Code + GitHub Copilot、Gemini CLI、Pi Agent 等多平台。

對 Codex 而言，安裝方式不是 npm 套件，而是把 repo clone 到 `~/.codex/understand-anything`，再把多個 skill 目錄建立 symlink 到 `~/.agents/skills/`，讓 Codex 可以直接呼叫這些 skills。

---

## 這個專案真正靠哪些 skill / agent 在運作

README 在 `Under the Hood` 區段明確寫出 `/understand` 會協調 5 個 specialized agents：

1. `project-scanner`
2. `file-analyzer`
3. `architecture-analyzer`
4. `tour-builder`
5. `graph-reviewer`

其中 `/understand` 本身是總控 skill，真正的工作分工如下：

### 1. `project-scanner`

用途：先建立 repo 的「總目錄認知」。

它負責：

- 掃描專案檔案
- 偵測語言與框架
- 統計檔案數與複雜度
- 建立 file list
- 建立 import map

也就是說，它不是直接分析程式邏輯，而是先回答「這個 repo 有哪些檔案、主要技術棧是什麼、哪些檔案值得後續分析」。

### 2. `file-analyzer`

用途：逐批把檔案轉成 graph node / edge。

它會從檔案內抽出：

- functions / methods
- classes / interfaces / types
- imports
- 其他結構線索

然後產生：

- GraphNode
- GraphEdge

這一層才是把原始 code 映射成圖資料的核心。

### 3. `architecture-analyzer`

用途：把 node/edge 進一步整理成「架構層」。

它不只看 import edge，還會把所有 file-level node 與 cross-category edge 一起考慮，輸出 `layers.json`，最後變成 knowledge graph 裡的 `layers` 欄位。

### 4. `tour-builder`

用途：不是畫圖，而是建立「理解順序」。

它會依據 README、entry point、layers、graph topology 產生 guided learning tour，幫新加入的人知道先看哪裡、再看哪裡。

### 5. `graph-reviewer`

用途：最後品質把關。

它會檢查：

- graph 是否完整
- node / edge 是否互相對得上
- layer / tour 是否引用不存在的 node
- 是否有漏掉掃描到的檔案

這一步的目標不是新增理解，而是降低圖壞掉、斷邊、缺節點的機率。

---

## `/understand` skill 的完整執行步驟

真正把陌生 repo 變成圖的，不只是 5 個子代理名稱，而是 `understand-anything-plugin/skills/understand/SKILL.md` 裡定義的 7 個 phase。

以下是完整流程。

### Phase 0: Pre-flight

這一步先做執行策略判斷。

它會：

- 設定 `PROJECT_ROOT`
- 取得 git commit hash
- 建立 `.understand-anything/intermediate` 與 `.understand-anything/tmp`
- 看既有 `knowledge-graph.json` / `meta.json` 是否已存在
- 判斷要做 full rebuild、incremental update，還是 review-only

這一步很重要，因為它避免每次都從零分析整個 repo。

如果 repo 沒變，它可以直接跳過；如果只改了少數檔案，它只重跑 changed files；如果只想做品質檢查，可以走 `--review`。

### Phase 1: Scan

這一步 dispatch `project-scanner`。

它先讀：

- `README`
- package manifest（如 `package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod`）
- top-level directory tree
- 常見 entry point 路徑

接著要求 `project-scanner` 產出：

- project name / description
- languages / frameworks
- file list
- complexity
- `importMap`

重點是：這一步已經把 repo 從「完全未知」變成「有結構化 inventory 的專案」。

### Phase 2: Analyze

這一步 dispatch `file-analyzer`，而且是批次平行。

規則大致是：

- 一批約 20 到 30 個檔案
- 最多 5 個 subagents concurrently
- 每批都會拿到該批檔案的 pre-resolved import data

這裡是整條流程的核心轉換：

- 檔案 -> file node
- function/class -> child nodes
- import / call / contains 等 -> edges

也就是說，知識圖不是由 dashboard 臨時畫出來，而是在這個 phase 就已經被建模成 nodes/edges 了。

### Phase 3: Assemble

把每個 batch 輸出的 nodes / edges 合併。

並做基本清理：

- 移除 dangling edge
- 移除重複 node ID
- 記錄錯誤與警告

這一步等於把分散式平行分析收斂成單一 graph。

### Phase 4: Architecture

這一步 dispatch `architecture-analyzer`。

它會把 Phase 2/3 的圖資料再做一層抽象，輸出 architecture layers。

特點是它不只看 code file，也把：

- config
- document
- service
- pipeline
- table
- schema
- resource
- endpoint

這些 file-level node 一起納入分層。

所以最終不是只有「程式碼呼叫圖」，而是比較接近「專案結構圖」。

### Phase 5: Tour

這一步 dispatch `tour-builder`。

它根據：

- README
- entry point
- 全部 file-level nodes
- layers
- all edges

產生一條 guided tour。

意思是，系統不只把 repo 畫成圖，還會決定「先看哪個 node 最能理解整體」。

這就是它能做 onboarding 的原因。

### Phase 6: Review

這一步組裝最終 `KnowledgeGraph` JSON 結構，然後做 validation。

預設路徑會跑 inline deterministic validation；如果加 `--review`，則會 dispatch `graph-reviewer` 做更完整的 LLM 審查。

它檢查的重點包括：

- `nodes` / `edges` 是否有效
- `layers` / `tour` 欄位是否符合 schema
- layer 與 tour 引用的 node 是否存在
- file node 是否有被分配到 layer
- 是否存在 orphan node

### Phase 7: Save

最後儲存：

- `.understand-anything/knowledge-graph.json`
- `.understand-anything/meta.json`
- `.understand-anything/fingerprints.json`

並在驗證成功時，才自動啟動 `/understand-dashboard`。

---

## 它到底怎麼把 repo 變成「圖」

這個問題可以拆成四個層次回答。

### 1. 先定義圖的資料模型

`SKILL.md` 的 schema 區段已經定義 knowledge graph 的主要元素：

- node types：`file`, `function`, `class`, `module`, `concept`, `config`, `document`, `service`, `table`, `endpoint`, `pipeline`, `schema`, `resource`
- edge types：`imports`, `contains`, `calls`, `depends_on`, `configures`, `routes`, `documents`, `deploys`, `triggers` 等

所以它不是把 AST 原封不動畫出來，而是先投影到一個「對理解 codebase 有用」的圖模型。

### 2. 用結構抽取把 code 映射成 node / edge

`file-analyzer` prompt 明確要求先寫腳本做 structural extraction，再用這些結果當基礎做分析。它會抽：

- function / method
- class / interface / type
- import

而 core 裡的 `graph-builder.ts` 也顯示了這種映射方式：

- 每個檔案變成 `file:<path>`
- 每個 function 變成 `function:<file>:<name>`
- 每個 class 變成 `class:<file>:<name>`
- file -> function / class 之間用 `contains`
- file -> file 之間可用 `imports`
- function -> function 之間可用 `calls`

這就是「repo 變成圖」的資料層答案。

### 3. 用 LLM 補上圖裡沒有的語意

只靠靜態分析，最多知道「誰 import 誰、誰包含誰」，但不知道「這個檔案為什麼存在」。

`llm-analyzer.ts` 顯示它會要求模型為每個檔案補上：

- `fileSummary`
- `tags`
- `complexity`
- `functionSummaries`
- `classSummaries`
- `languageNotes`

所以知識圖不只是結構圖，也是語意圖。

這也是為什麼 dashboard 裡可以點 node 看 plain-English explanation。

### 4. 再把圖整理成更適合人理解的高層表示

完成 node / edge 後，系統還會多做兩層加工：

- `layers`: 架構分層
- `tour`: 觀看順序

`tour-generator.ts` 甚至有 heuristic 路徑，會根據 graph topology 找 entry points、做 topological sort，再依 layer 組裝 tour steps。

也就是說，它不是只畫出一張靜態網狀圖，而是進一步把圖變成「可閱讀的理解流程」。

---

## 它到底怎麼分析「邏輯」

如果把「分析邏輯」拆開來看，這個專案其實同時做了三種層次的邏輯分析。

### 第一層：結構邏輯

這是最穩定的一層。

它分析：

- 哪些檔案是入口
- 哪些檔案 import 彼此
- 哪些檔案包含哪些 function/class
- 哪些 function 呼叫哪些 function

這屬於程式結構邏輯。

### 第二層：架構邏輯

這一層回答的是：

- 哪些東西屬於 API Layer
- 哪些是 Service Layer
- 哪些是 Data Layer
- 哪些是 UI Layer
- 哪些是 Utility / Middleware / Config / Test

也就是從單點依賴關係，提升到整體架構理解。

### 第三層：敘事邏輯

這一層不是 code correctness，而是「理解順序邏輯」。

系統用 README、entry point、layer、graph topology 組合出 guided tour，讓使用者按順序理解：

- 先看專案目的
- 再看入口
- 再看核心流程
- 再看資料層 / 周邊模組

這讓它不只是 code map，而像是半自動的 onboarding 教材。

---

## 為什麼它能處理「沒看過的 repo」

因為它沒有假設 repo 必須先被人類整理好，而是先強制建立下列中介資料：

1. file inventory
2. language / framework detection
3. import map
4. structural extraction result
5. merged graph
6. layers
7. tour

這些中介層讓模型不需要一口氣吃完整個 repo。

它是先把 repo 壓縮成多份結構化中間產物，再在每一層增加理解深度。

這是它能處理大 repo 的主要原因。

---

## 這套方法的關鍵設計亮點

### 1. 不是只靠 LLM，而是先 deterministic 再 semantic

`project-scanner` 和 `file-analyzer` prompt 都要求先寫腳本做可驗證的抽取，再把結果交給模型補語意。這樣可以降低 LLM 亂編檔案、亂編函式關係的風險。

### 2. 平行 batch 分析

README 與 `/understand` skill 都提到 file analyzers 會平行執行，最多 5 個 concurrent，且每批大約 20 到 30 個檔案。這避免單次 prompt 太大，也讓大型 repo 可拆分處理。

### 3. 有 incremental update

它不要求每次全量重建，而是根據 git commit / changed files / fingerprints 決定只重跑變更檔案。這是實務上能持續用的關鍵，不然圖很快就會過期。

### 4. 有 review / normalization / repair

這套流程很重視「最後輸出的 graph 是否可用」。它不是生成完就算，而是會：

- normalize layer 與 tour 欄位
- 移除 dangling refs
- 填補缺欄位
- 必要時保存 partial result 並附 warning

這讓 dashboard 不會太容易因壞資料直接失效。

---

## 我對這個專案的實作判讀

下面這幾點不是 README 直接明講，而是根據 repo 內容做的技術判讀。

### 判讀 1：它的核心方法論是對的

把陌生 repo 理解問題拆成：

- 掃描
- 抽結構
- 組圖
- 分層
- 導覽
- 驗證

這個拆法是合理的，也明顯比「直接問模型這個 repo 在幹嘛」更穩。

### 判讀 2：它最強的地方不是 AST 精度，而是工作流設計

從 `SKILL.md` 來看，真正強的是 orchestration：

- 分 phase
- 分 agent
- 有 batch
- 有 intermediate artifacts
- 有 validation

也就是說，它最有價值的地方是「把 repo 理解任務產品化」。

### 判讀 3：目前最強的 AST/結構支援看起來偏向 JS/TS

這是我基於 repo 的技術推論：

- `@understand-anything/core` 依賴裡明確列出 `web-tree-sitter`、`tree-sitter-javascript`、`tree-sitter-typescript`
- `fingerprint.ts` 會呼叫 registry 的 structural analysis 來抽 function/class/import/export fingerprint

因此可以合理推論：目前最成熟、最穩定的結構分析能力，很可能集中在 JavaScript / TypeScript 路線。其他語言雖然在 prompt 層與掃描層有支援，但深度可能更依賴 heuristics、腳本抽取與 LLM 補語意，而不是同等成熟的 AST plugin。

這不代表它不能分析其他語言，而是代表「不同語言的分析深度可能不完全對稱」。

### 判讀 4：它輸出的其實不是純 call graph，而是 knowledge graph

這點很重要。

一般 call graph 只會描述：

- function A call function B

但 Understand-Anything 額外納入：

- docs
- config
- schema
- infra
- pipeline
- service
- endpoint

因此更準確的說法是：

它產生的是「repo understanding graph」，不是單純的程式呼叫圖。

---

## 如果你要用一句流程圖來描述它

可以把整體流程寫成：

```text
陌生 repo
  -> Phase 0 Pre-flight
  -> Phase 1 Scan 專案全貌
  -> Phase 2 Analyze 各批檔案
  -> Phase 3 Assemble 合併成 nodes/edges
  -> Phase 4 Architecture 分層
  -> Phase 5 Tour 排出閱讀順序
  -> Phase 6 Review 驗證/修補
  -> Phase 7 Save 輸出 knowledge-graph.json
  -> Dashboard 視覺化 + Chat / Explain / Diff / Onboard
```

---

## 直接回答你的問題

### 問題 1：它是透過 agent skill 的哪一些步驟，把沒看過的 repo 變成圖？

直接答案是：

1. `/understand` 先做 Pre-flight，決定 full rebuild / incremental / review-only
2. `project-scanner` 掃出 file inventory、語言、框架、import map
3. `file-analyzer` 分批平行抽出 function/class/import 等結構
4. 系統把結果組裝成 graph nodes / edges
5. `architecture-analyzer` 為 graph 補 layer
6. `tour-builder` 為 graph 補 guided walkthrough
7. `graph-reviewer` 或 inline validator 檢查圖的一致性
8. 最終輸出 `knowledge-graph.json`，dashboard 再把它視覺化

### 問題 2：它怎麼分析邏輯？

直接答案是：

- 用靜態結構抽取分析「誰包含誰、誰依賴誰、誰呼叫誰」
- 用 architecture analysis 分析「哪些模組屬於哪一層」
- 用 LLM summaries 分析「每個檔案/函式大致在做什麼」
- 用 guided tour 分析「應該按什麼順序理解整個系統」

所以它分析的不是 runtime correctness，而是 codebase understanding logic。

---

## 實務價值

這個專案最適合的使用情境有三種：

1. 新加入團隊，要快速建立對大型 repo 的整體認知
2. 要在陌生 codebase 中找到某功能大概分佈在哪些檔案
3. 要把 architecture / onboarding / code reading 任務交給 AI workflow 加速

它不會取代完整 code review，也不會取代真正的執行期 tracing，但很適合當「第一層理解基礎設施」。

---

## 最終總結

`Understand-Anything` 能把陌生 repo 轉成圖，關鍵不在於它有一個超強模型，而在於它把「理解 repo」拆成了可執行的 agent pipeline：

- 先掃描
- 再抽結構
- 再組裝成知識圖
- 再補架構分層
- 再補閱讀導覽
- 最後驗證與持久化

因此它輸出的不是單一觀點，而是一套多層次理解介面：

- graph 給你看關係
- layer 給你看架構
- summary 給你看語意
- tour 給你看閱讀順序
- chat / explain / diff / onboard 給你看不同使用情境

如果只用一句最精準的話來形容它：

> 它把「讀陌生 repo」這件事，從人工探索流程，重構成可重跑、可增量更新、可視覺化的 multi-agent knowledge graph pipeline。

---

## 參考來源

- GitHub Repo: https://github.com/Lum1104/Understand-Anything
- README: https://raw.githubusercontent.com/Lum1104/Understand-Anything/main/README.md
- Codex 安裝說明: https://raw.githubusercontent.com/Lum1104/Understand-Anything/main/.codex/INSTALL.md
- `/understand` skill: https://raw.githubusercontent.com/Lum1104/Understand-Anything/main/understand-anything-plugin/skills/understand/SKILL.md
- `project-scanner` prompt: https://raw.githubusercontent.com/Lum1104/Understand-Anything/main/understand-anything-plugin/skills/understand/project-scanner-prompt.md
- `file-analyzer` prompt: https://raw.githubusercontent.com/Lum1104/Understand-Anything/main/understand-anything-plugin/skills/understand/file-analyzer-prompt.md
- core package metadata: https://github.com/Lum1104/Understand-Anything/blob/main/understand-anything-plugin/packages/core/package.json
- `graph-builder.ts`: https://github.com/Lum1104/Understand-Anything/blob/main/understand-anything-plugin/packages/core/src/analyzer/graph-builder.ts
- `llm-analyzer.ts`: https://github.com/Lum1104/Understand-Anything/blob/main/understand-anything-plugin/packages/core/src/analyzer/llm-analyzer.ts
- `tour-generator.ts`: https://github.com/Lum1104/Understand-Anything/blob/main/understand-anything-plugin/packages/core/src/analyzer/tour-generator.ts
- `fingerprint.ts`: https://github.com/Lum1104/Understand-Anything/blob/main/understand-anything-plugin/packages/core/src/fingerprint.ts
