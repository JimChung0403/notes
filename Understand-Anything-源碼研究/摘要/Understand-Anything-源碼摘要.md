# Understand-Anything 源碼摘要

## 先講結論

`Understand-Anything` 不是把整個 repo 一次丟給模型，然後要模型「憑感覺看懂」。

它真正做的事情是：

1. 先做 deterministic 掃描，產生完整 file inventory、語言、框架、`importMap`。
2. 再把檔案分 batch，平行 dispatch `file-analyzer`。
3. 每個 batch 先用腳本做結構抽取，再由 agent 依照 schema 產出 `nodes` 和 `edges`。
4. 合併 graph 後，再跑 architecture layer 與 guided tour。
5. 最後做 validation、normalization、repair，才保存成 `.understand-anything/knowledge-graph.json`。

所以它的關鍵能力不是「超強單次理解」，而是「把理解 repo 這件事拆成可重跑的 agent pipeline」。

---

## 我實際看了哪些源碼

這份摘要不是只根據 README，而是根據下列檔案整理：

- `understand-anything-plugin/skills/understand/SKILL.md`
- `understand-anything-plugin/skills/understand/project-scanner-prompt.md`
- `understand-anything-plugin/skills/understand/file-analyzer-prompt.md`
- `understand-anything-plugin/skills/understand/architecture-analyzer-prompt.md`
- `understand-anything-plugin/skills/understand/tour-builder-prompt.md`
- `understand-anything-plugin/packages/core/src/analyzer/graph-builder.ts`
- `understand-anything-plugin/packages/core/src/analyzer/tour-generator.ts`
- `understand-anything-plugin/packages/core/src/fingerprint.ts`
- `understand-anything-plugin/packages/core/src/analyzer/llm-analyzer.ts`

---

## 實際流程，不是宣傳版流程

## Phase 0: Pre-flight

`SKILL.md` 先判斷這次是：

- full rebuild
- incremental update
- review-only

它會先讀既有的：

- `.understand-anything/knowledge-graph.json`
- `.understand-anything/meta.json`

再用 git commit hash 決定是否需要重跑。

這代表它不是每次都全量重建，而是有「狀態感知」。

---

## Phase 1: project-scanner

這個 agent 的 prompt 很關鍵。

它不是要模型直接掃 repo，而是明確要求：

- 先寫並執行 discovery script
- 掃出所有 project files
- 保留 non-code files
- 做 language detection
- 做 fileCategory detection
- 做 line counting
- 做 framework detection
- 解析 project-internal imports，輸出 `importMap`

重點：

1. 它強調 `description` 以外的結構資訊要相信腳本結果，不要靠模型腦補。
2. 它把 non-code 檔案也保留下來，包含 docs、config、infra、data。
3. 它把 import resolution 前置化，之後的 file-analyzer 直接使用 `batchImportData`，不重算 imports。

所以 repo 變成圖的第一步，其實是把 repo 先變成 deterministic inventory。

---

## Phase 2: file-analyzer

這是核心 phase。

`SKILL.md` 規定：

- 每批約 20-30 個檔案
- 最多 5 個 subagents concurrently
- related non-code files 要盡量被放在同一 batch

而 `file-analyzer-prompt.md` 明確規定這個 agent 也分兩段：

### 第一步：先寫腳本做 structural extraction

腳本會抽出：

- functions
- classes
- exports
- 各種 non-code 結構

例如：

- docker-compose 的 service 名稱
- Terraform resource
- CI pipeline stages/jobs
- SQL tables
- GraphQL / Protobuf schema
- OpenAPI endpoints

### 第二步：再做 semantic analysis

這一段才由 agent 根據抽取結果去產生：

- file node
- function/class node
- edge
- summary
- tags
- complexity
- languageNotes

這裡有一個非常重要的 source-based 觀察：

`file-analyzer` prompt 明文要求「不要再從 source 重解 imports」，而是直接吃 `batchImportData`。也就是：

- import 解析是 scanner 的職責
- graph node/edge 生成是 analyzer 的職責

這種責任切分做得很清楚。

---

## Graph 是怎麼真的建出來的

不是只有 prompt 這樣說，`graph-builder.ts` 也真的把這些結構轉成 graph。

### 1. code files

`GraphBuilder.addFileWithAnalysis()` 會：

- 建 `file:<path>` node
- 為每個 function 建 `function:<file>:<name>` node
- 為每個 class 建 `class:<file>:<name>` node
- 用 `contains` edge 把 file 連到 function / class

同時還有：

- `addImportEdge()` 建 `imports`
- `addCallEdge()` 建 `calls`

### 2. non-code files

`GraphBuilder.addNonCodeFileWithAnalysis()` 會把非程式碼檔案也轉成 graph 結點與子節點，例如：

- `service`
- `endpoint`
- `pipeline`
- `resource`
- `table`
- `schema`

如果 definition kind 無法辨識，還會 fallback 成 `concept`。

這意味著它畫的不是單純 code call graph，而是比較接近「整個 repo 的知識圖」。

---

## 它分析的是哪些關係

`file-analyzer-prompt.md` 對 edge type 定義得很細。

### code edges

- `contains`
- `imports`
- `calls`
- `inherits`
- `implements`
- `exports`
- `depends_on`
- `tested_by`

### non-code edges

- `configures`
- `documents`
- `deploys`
- `migrates`
- `triggers`
- `defines_schema`
- `serves`
- `provisions`
- `routes`
- `related`
- `depends_on`

這個設計很重要，因為它讓 README、Dockerfile、CI、SQL、Terraform 也進入同一張圖。

所以它回答的不只是：

> 哪個 function call 哪個 function？

而是也能回答：

> 哪個 config 影響哪段 code？
> 哪個 schema 定義哪個 API？
> 哪個 Dockerfile/Workflow 在部署哪個應用？

---

## Phase 4: architecture-analyzer

這個 agent 不是只看 import graph，而是做兩層工作：

1. 先寫 script 算 structural patterns
2. 再用這些 pattern 做 semantic layer assignment

它要求每個 file-level node 必須被分到且只分到一個 layer。

而且它特別把 non-code 檔案也納入分層：

- `config` -> config/root layer
- `document` -> documentation layer
- `service` / `resource` -> infrastructure layer
- `pipeline` -> CI/CD 或 infrastructure
- `table` / `schema` / `endpoint` -> data layer

所以最終 `layers` 不是裝飾，而是知識圖的第二層抽象。

---

## Phase 5: tour-builder

這邊也不是直接讓模型自由發揮。

`tour-builder-prompt.md` 要求：

1. 先寫 Node.js script 分析 graph topology
2. 算 fan-in、fan-out、entry point 候選、BFS traversal、clusters、layers
3. 再根據這些結果設計教學式 tour

也就是說，guided tour 的基礎不是隨機選幾個檔案，而是根據：

- 哪些 node 最常被依賴
- 哪些 node 是入口
- graph 的自然閱讀順序
- 哪些檔案彼此形成 cluster

另外 `packages/core/src/analyzer/tour-generator.ts` 還提供 heuristic fallback：

- 先把 code nodes 建 adjacency
- 用 Kahn's algorithm 做 topological sort
- 若有 layers，就依 layer 順序組 tour
- 若沒有 layers，就每 3 個 node 一組
- 最後再補 concept nodes

這代表 tour 並不是 100% 綁死在 LLM 上，core 也有 deterministic 備援方案。

---

## Phase 6: review 與 validation

這個專案很重視「輸出品質」。

`SKILL.md` 在 assemble 後還會：

- 檢查 `layers` schema
- 檢查 `tour` schema
- 檢查 dangling refs
- 檢查 file nodes 是否都被分配到某個 layer
- 檢查 orphan nodes

預設走 inline deterministic validation。

若使用 `--review`，則再 dispatch `graph-reviewer` 做更完整的 LLM 審查。

如果發現問題，還會嘗試：

- 移除 dangling edges
- 補 `tags`
- 補 `summary`
- 移除 invalid type nodes

所以它不是「生圖」，而是「生圖後還會修圖」。

---

## incremental update 為什麼成立

關鍵在 `fingerprint.ts`。

它不是只算 content hash，而是盡量用 tree-sitter 分析出 structural fingerprint：

- functions
- classes
- imports
- exports
- line count

然後把變更分成三種：

- `NONE`
- `COSMETIC`
- `STRUCTURAL`

判定方式是：

- 內容完全相同 -> `NONE`
- 內容變了，但 function/class/import/export signature 沒變 -> `COSMETIC`
- 只要 signature 有差異，或沒有 structural analysis 能力 -> `STRUCTURAL`

這個設計的意義是：

- 小改註解或內部實作，不一定要重建整張圖
- 一旦結構有變，就保守地重跑

另外它也清楚寫出：

- 若某語言沒有 tree-sitter support，就退回 content-hash-only fingerprint
- 這種情況下只要檔案改了，就保守視為 structural change

這點很務實。

---

## 我對這個專案的實際判讀

## 判讀 1：真正的核心是 orchestration，不是單一 AST parser

單看 `graph-builder.ts`、`fingerprint.ts`、`tour-generator.ts`，你會發現它不是某個單點演算法特別神，而是整體工作流被拆得很好：

- scanner 專責 inventory 和 imports
- analyzer 專責節點/邊建模
- architecture 專責 layer
- tour 專責理解順序
- review 專責輸出品質

這才是它能處理陌生 repo 的主因。

## 判讀 2：它真的有把 non-code 資產當一級公民

很多 repo analysis 工具只看 `.ts`、`.py`、`.go`。

但這個專案從 prompt 到 graph builder 都在做：

- docs
- config
- Docker / K8s / Terraform
- CI/CD
- SQL / GraphQL / Protobuf / OpenAPI

這讓它更像「系統理解工具」，而不是單純 code browser。

## 判讀 3：它仍然是以靜態分析為主，不是 runtime truth

它擅長的是：

- 看結構
- 看依賴
- 看分層
- 看 onboarding 順序

但它不等於：

- 真正執行時呼叫鏈
- 真實執行流量
- 動態依賴載入全貌

因此它給的是 architectural understanding，不是 production tracing。

## 判讀 4：JS/TS 路線目前看起來最成熟

從 core package 依賴與 fingerprint 設計看，tree-sitter 結構分析顯然是重要基礎。

這意味著：

- 有支援的語言，能做較細的 structural fingerprint
- 沒有支援的語言，仍能分析，但精度更依賴 heuristic 與 LLM 補語意

所以它是多語言可用，但不同語言的分析深度不一定完全對稱。

---

## 直接回答你的原始問題

## 它是透過哪些 agent skill 步驟，把沒看過的 repo 變成圖？

最準確的回答是：

1. `/understand` 先做 pre-flight，判斷 full / incremental / review-only
2. `project-scanner` 寫 script 掃 repo，建立 file inventory、framework、`importMap`
3. `file-analyzer` 依 batch 平行處理，每批先做 structural extraction，再產出 nodes/edges
4. 系統把 batch 結果 assemble 成單一 knowledge graph
5. `architecture-analyzer` 把所有 file-level nodes 分配到 layers
6. `tour-builder` 根據 graph topology 產生 guided tour
7. reviewer / validator 檢查 graph，一致性修補後保存
8. dashboard 只是讀 `knowledge-graph.json` 做視覺化，不是生成圖的核心

## 它是怎麼分析邏輯的？

它同時做三層邏輯：

1. 結構邏輯：imports、contains、calls、inherits、implements
2. 架構邏輯：API / service / data / infra / docs / config 等 layers
3. 教學邏輯：根據 entry point、fan-in、BFS、clusters 排出 onboarding 順序

---

## 最後一句話

`Understand-Anything` 的本質不是「請 AI 幫我看 repo」。

它更接近：

> 先用腳本把 repo 壓縮成可計算的結構，再讓多個 agent 在不同 phase 補上語意、分層、導覽與驗證，最後產生一張可視化知識圖。
