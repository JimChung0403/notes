# Java CLI AI 開發流程報告

## 1. 結論先講

如果你的情境是：

- `Java`
- `CLI 開發`
- 想用 `AI coding`
- 在意 `AI 到底知不知道該改哪裡`
- 在意 `改完之後怎麼驗證別的地方沒爆`

那 **更合理的第一版** 應該是：

- `GSD`
  - 先做 codebase mapping
- `Superpowers`
  - 做 implementation discipline
- `Local Verification Stack`
  - `rg`
  - `mvn test-compile + targeted tests`
  - `Claude Code /review`

一句話版本：

```text
先用 GSD 把專案看懂
-> 再用 Superpowers 做有紀律的實作
-> 最後用本地 verification stack 驗證改動沒漏掉別的地方
```

這份文件的定位不是「最輕 toy project 流程」，  
而是 **適合中大型 / 老舊 / 真實 Java 專案的第一版 AI 開發流程**。

---

## 2. 分級

### 2.1 必須要用

這些是第一版主流程核心，不建議省略。

#### `GSD`

用途：

- codebase mapping
- 專案上下文
- roadmap / phase / state
- feature 開始前的背景整理
- feature 結束後的知識回寫

為什麼必須：

- 沒有 codebase mapping，`Superpowers` 很難穩定知道該改哪裡
- 對老舊或中大型專案，AI 只靠當前 prompt 探索 repo，品質不穩

不使用的缺點：

- AI 容易只看到局部，不知道真正該下刀的位置
- 每次都要重講背景
- phase / state 無法沉澱

#### `Superpowers`

用途：

- brainstorm
- implementation planning
- task breakdown
- TDD
- implementation discipline
- implementation review

為什麼必須：

- `GSD` 讓 AI 知道大致該改哪裡
- `Superpowers` 讓 AI 知道怎麼有紀律地改

不使用的缺點：

- 任務拆解不穩
- AI 太快開始寫 code
- 缺少固定 TDD / implementation review 節奏

#### `Local Verification Stack`

用途：

- pre-change impact analysis
- post-change impact verification
- compile / test-compile
- targeted tests
- local AI review

這一版的最小組成：

- `rg`
- `mvn test-compile` 或 `./gradlew testClasses`
- targeted tests
- `Claude Code /review`

為什麼必須：

- 你要的是本地 change safety
- 改完之後一定要有安全網

不使用的缺點：

- 改了 A 不知道哪裡沒改到
- compile / tests 太晚才爆
- 本地沒有 verification gate

---

### 2.2 建議要用

#### `Coordinator Skill / Slash Command`

用途：

- 判斷現在在哪個階段
- 決定下一步該交給 `GSD`、`Superpowers`、還是 `Local Verification Stack`
- 檢查交接物是否齊全

為什麼建議用：

- 這套流程已經開始有明確分工
- 有一個薄的 coordinator 會讓流程更穩

不使用的缺點：

- 流程仍可運作
- 但要靠人腦記住什麼時候該切換工具

---

### 2.3 可選

#### `Greptile`

用途：

- 未來進入 GitHub / GitLab PR 流程後的 remote review gate

為什麼現在列可選：

- 你目前要的是本地開發流程
- `Greptile` 的主場是 remote PR review

不使用的缺點：

- 未來少一層 remote whole-repo graph review
- 但不影響你現在的本地主流程

---

## 3. 每一個元件怎麼使用

### 3.0 使用入口怎麼選

這一段是日常使用時最容易混淆的地方。

#### 3.0.1 有 PRD、要啟動一整個 feature

用：

```text
/run-prd docs/prd/<PRD-ID>.md
```

適合情境：

- PM 給了正式 PRD
- 你要從 PRD 對齊一路跑到 implementation handoff
- 你希望流程從一開始就帶上 GSD context

一句話：

- `/run-prd` = **PRD-driven feature 開發的主入口**

#### 3.0.2 feature brief 已存在，兩天後回來續做

用：

```text
/coordinator 我要繼續 <PRD-ID>，請讀 docs/feature-briefs/<PRD-ID>.md，並判斷下一步
```

適合情境：

- 已經有 `docs/feature-briefs/<PRD-ID>.md`
- 做到一半中斷後回來
- 不確定現在該進 `Superpowers` 還是 `Local Verification Stack`

一句話：

- `/coordinator` = **流程導航器 / 路由器**

#### 3.0.3 只想查影響面

用：

```text
/impact <需求或變更描述>
```

適合情境：

- 想知道改 A 可能還會影響哪裡
- 改完後想查還有沒有漏改點

#### 3.0.4 只想整理本地驗證

用：

```text
/verify-local
```

適合情境：

- code 已經改完
- 想知道 compile、targeted tests、/review 該怎麼跑

#### 3.0.5 只想看最近改動的 review

用：

```text
/review
```

適合情境：

- 已經有 code changes
- 想用 AI reviewer 看最近改動

### 3.0 需求拆分：你、GSD、Superpowers、Coordinator Skill 各自做什麼

這一段很重要。  
當你同時有多個需求時，不要直接把它們全部丟給 `Superpowers` 做 implementation。

正確順序是：

```text
你提供原始需求
-> GSD 幫你做業務需求拆分
-> Coordinator Skill 判斷下一步交給誰
-> Superpowers 只接單一、已整理好的 feature brief
```

### 3.0.1 你做什麼

你負責提供：

- 原始需求
- 商業目標
- 優先順序
- 不可動的限制
- 哪些事情一定要做 / 不要做

你不是要直接幫 AI 拆成 implementation tasks，  
你只需要把「你真正想達成什麼」說清楚。

### 3.0.2 GSD 做什麼

`GSD` 負責：

- 把模糊需求整理成業務需求卡
- 切 scope
- 分 phase
- 整理依賴關係
- 辨識 assumptions
- 產出 feature brief

換句話說，`GSD` 回答的是：

- 我們到底要做哪幾件事？
- 這幾件事應該怎麼切成 feature？
- 哪些需求有先後依賴？
- 哪些需求應該延後？

這屬於 **spec-driven development 的前半段**。

### 3.0.3 Superpowers 做什麼

`Superpowers` 不負責做第一輪業務需求拆分。  
它負責的是：

- 接一個已經整理好的 feature brief
- 把它轉成 implementation plan
- 把它拆成 engineering tasks
- 決定先補哪些測試
- 決定先改哪些檔案

換句話說，`Superpowers` 回答的是：

- 這一個 feature 具體要怎麼做？
- 先改哪幾個 class / method / test？
- 這個 implementation 怎麼拆成可以穩定執行的小步驟？

所以：

- `GSD` 規劃的是 `what / why / phase`
- `Superpowers` 規劃的是 `how`

### 3.0.4 Coordinator Skill 做什麼

`Coordinator Skill` 不負責重新定義需求，  
它負責的是：

- 判斷目前是在 `需求拆分`、`implementation planning`、還是 `verification`
- 把任務路由到正確工具
- 檢查交接物是否齊全

在需求拆分這一段，它主要負責：

- 確保還沒整理成 feature brief 的需求，不要直接送進 `Superpowers`
- 確保先由 `GSD` 產出 feature brief
- 再把單一 feature brief handoff 給 `Superpowers`

### 3.0.5 一個最簡單的分工圖

```text
你
-> 提供原始需求與商業目標

GSD
-> 拆成業務需求卡 / feature brief / phase / dependencies

Coordinator Skill
-> 判斷現在是否已可交給實作

Superpowers
-> 將單一 feature brief 轉成 implementation plan
```

### 3.0.6 為什麼不能一開始就丟給 Superpowers

因為 `Superpowers` 雖然能做規劃，  
但它更擅長的是 **implementation-level planning**，不是 **業務需求拆分 / spec-level planning**。

如果一開始就把多個模糊需求直接丟給它，常見風險是：

- 太快進入 implementation thinking
- 把還沒釐清的需求當成已確定需求
- 規劃會偏工程細節，而不是先切清楚 feature 邊界

所以：

- **先由 `GSD` 做需求拆分**
- **再由 `Superpowers` 做工程規劃**

### 3.1 GSD 怎麼用

#### 用途

- 先把專案看懂
- 建立 AI 可重用的專案上下文
- feature 前做分析
- feature 後做回寫

#### 什麼時候用

- 專案剛開始
- 接手老舊專案時
- 每個 feature 開始前
- 每個 feature 結束後

#### 怎麼用

##### 老舊 / 中大型專案

第一步就先：

```text
/gsd:map-codebase
```

然後：

```text
/gsd:new-project
/gsd:create-roadmap
/gsd:progress
```

做 feature 分析：

```text
/gsd:discuss-phase 1
/gsd:research-phase 1
/gsd:list-phase-assumptions 1
/gsd:plan-phase 1
```

feature 完成後回寫：

```text
/gsd:verify-work 1
/gsd:progress
/gsd:complete-milestone
```

#### 會產出什麼

- `PROJECT.md`
- `ROADMAP.md`
- `STATE.md`
- `.planning/codebase/`
  - `STACK.md`
  - `ARCHITECTURE.md`
  - `STRUCTURE.md`
  - `CONVENTIONS.md`
  - `TESTING.md`
  - `INTEGRATIONS.md`
  - `CONCERNS.md`
- 單次需求建議另外落一份：
  - `docs/feature-briefs/<PRD-ID>.md`

#### 它在流程中的角色

`GSD` 負責先回答：

- 這個專案怎麼分層？
- 哪些地方 fragile？
- 哪裡才是合理的修改區域？
- 這個 feature 在整體 roadmap / phase 裡的位置是什麼？
- 這次 PRD 對齊後，真正交給 `Superpowers` 的 feature brief 長什麼樣？

#### 單次需求文件建議

除了長期文件外，建議每次 PRD 再落一份：

- `docs/feature-briefs/<PRD-ID>.md`

這份文件由 `GSD` 主責整理，內容至少應包含：

- feature brief
- PRD 對齊結果
- actual change scope
- constraints
- acceptance criteria
- context files
- open questions

#### `docs/feature-briefs/<PRD-ID>.md` 是什麼

它是：

- 把 PM 的 PRD 轉成 **工程可執行需求摘要** 的中介文件

它不是：

- 完整 PRD
- implementation plan
- 最終測試報告

它的用途是：

- 讓 `Superpowers` 不直接吃原始 PRD
- 而是吃一份已經和 codebase 對齊過的工程版摘要

內容至少要包含：

- feature brief
- business goal
- actual change scope
- constraints
- acceptance criteria
- context files
- alignment report summary
- open questions

#### `docs/feature-briefs/<PRD-ID>.md` 誰負責

概念上：

- 內容主責是 `GSD`

實作上：

- 由 `/run-prd` 幫你把 GSD 整理好的內容正式寫成檔案

一句話：

- **內容 owner = `GSD`**
- **落檔執行 = `/run-prd`**

---

### 3.2 Superpowers 怎麼用

#### 用途

- 把需求變成 engineering plan
- 把 plan 拆成可執行 task
- 落實 TDD
- 做 implementation review

#### 什麼時候用

- `GSD` 已經把背景整理好之後
- 已經知道 feature 要做什麼之後
- 準備設計 / 實作時

#### 怎麼用

設計與拆任務：

- `brainstorming`
- `writing-plans`

實作：

- `using-git-worktrees`
- `subagent-driven-development`
- `executing-plans`

測試與 review：

- `test-driven-development`
- `requesting-code-review`
- `finishing-a-development-branch`

建議節奏：

```text
1. brainstorming
2. writing-plans
3. test-driven-development
4. subagent-driven-development
5. requesting-code-review
```

#### 它在流程中的角色

`Superpowers` 負責回答：

- 在 GSD 提供的上下文下，現在應該先改哪幾個檔案？
- 先補哪些測試？
- 怎麼把這個 feature 拆成可穩定執行的小步驟？

---

### 3.3 Local Verification Stack 怎麼用

#### 用途

- 在本地驗證「還有哪裡沒改到」
- 在本地驗證 compile / tests / review

#### 什麼時候用

- 開發前：做 pre-change impact analysis
- 開發後：做 post-change impact verification

#### 這一版的組成

- `rg`
- `mvn test-compile` 或 `./gradlew testClasses`
- targeted tests
- `Claude Code /review`

#### A. pre-change impact analysis

目的：

- 在開始寫之前先知道該改哪裡
- 找 usages、caller、可能漏改點

```bash
rg "ClassName|methodName|InterfaceName|DTOName" src test
```

如果需要補強 Java 依賴分析，可選再加：

```bash
jdeps -verbose:class path/to/jar-or-classes
```

#### B. post-change impact verification

目的：

- 檢查實際改動後，還有沒有其他地方應該一起改

```bash
git diff --name-only
rg "ChangedClass|ChangedMethod|ChangedInterface" src test
```

如果需要補強：

```bash
jdeps -summary path/to/jar-or-classes
```

#### C. compile / test-compile

Maven：

```bash
mvn test-compile
```

Gradle：

```bash
./gradlew testClasses
```

#### D. targeted tests

Maven unit test：

```bash
mvn -Dtest=MyServiceTest test
```

Maven integration test：

```bash
mvn -Dit.test=MyServiceIT verify
```

Gradle：

```bash
./gradlew test --tests "com.example.MyServiceTest"
```

#### E. local AI review

```text
/review
```

#### 什麼情境下要用 `rg`

`rg` 不是每一步都要用，但只要你要回答：

- 誰在用它？
- 哪裡還有它？
- 我是不是漏改了？

就應該叫 `rg` 出來。

最常見情境：

1. PRD 提到某個 class / method / DTO，想先驗證它真的存在  
2. 準備改 method signature / interface / DTO 欄位，怕漏改 caller  
3. 改完 code 後，想確認還有沒有殘留舊寫法  
4. 不知道該跑哪些 targeted tests，想先找相關 test 類別  
5. PM 提到的名稱可能過時，想驗證現有 codebase 裡是不是同一個東西  

最常見的用法：

```bash
rg "OrderService|findOrders|OrderDto" src test
rg "UserProfileManager|ProfileService" src test
rg "OrderServiceTest|OrderControllerIT" src test
```

#### 它在流程中的角色

`Local Verification Stack` 負責回答：

- 我是不是漏改了哪裡？
- compile 有沒有壞？
- 直接相關的 tests 有沒有過？
- 這次改動還有哪些看起來不對勁的地方？

---

### 3.4 Coordinator Skill 怎麼用

#### 用途

- 判斷現在在哪個階段
- 路由給正確的 owner
- 檢查交接物

#### 什麼時候用

- 每個 feature 開始時
- 每個階段切換時
- code changes 已存在、準備進 verification 時

#### 放在哪裡

建議做成 project command：

- `.claude/commands/coordinator.md`

這樣你可以直接用：

```text
/coordinator
```

或帶參數：

```text
/coordinator <需求描述或階段提示>
```

#### routing 規則

- 需求不清 / 需要背景 / 需要 state -> `GSD`
- 已有 feature brief / 需要設計 / 需要 implementation -> `Superpowers`
- 已有 code changes / 需要 impact / compile / tests / review -> `Local Verification Stack`

#### GSD -> Superpowers handoff 規則

這一版採用 **做法 3**：

- `Coordinator Skill` 不假設 `Superpowers` 會自動找到 GSD 的輸出
- 每次從 `GSD` 交接到 `Superpowers` 時，必須明確帶上 `context_files`
- `context_files` 以 GSD 產出的靜態檔案為主

GSD 的主要輸出位置：

- `PROJECT.md`
- `ROADMAP.md`
- `STATE.md`
- `.planning/codebase/`

標準 handoff 應包含：

```yaml
feature_brief: <summary from GSD>
feature_brief_file: docs/feature-briefs/<PRD-ID>.md
context_files:
  - PROJECT.md
  - ROADMAP.md
  - STATE.md
  - .planning/codebase/STACK.md
  - .planning/codebase/ARCHITECTURE.md
  - .planning/codebase/STRUCTURE.md
  - .planning/codebase/CONVENTIONS.md
  - .planning/codebase/TESTING.md
  - .planning/codebase/INTEGRATIONS.md
  - .planning/codebase/CONCERNS.md
constraints:
  - <constraint 1>
  - <constraint 2>
expected_output:
  - implementation_plan
  - task_list
  - test_strategy
```

Coordinator 在交接給 `Superpowers` 時，應明確要求：

```text
Before planning or implementation, read all context_files first.
Use GSD files as the source of truth for architecture, conventions,
testing approach, integrations, and known concerns.
Do not start implementation planning until these files are read.
```

這樣 `Superpowers` 的角色就很清楚：

- 不負責自己猜 repo 規則
- 不負責自己重新建立專案脈絡
- 只負責在 GSD 提供的上下文上做 implementation discipline

所以：

- `Superpowers` 不會天然知道去哪裡讀文件
- 是 `/run-prd` 或 `/coordinator` 在 handoff 裡明確指定：
  - `feature_brief_file`
  - `context_files`

#### 最小輸出格式

```yaml
current_stage: local_verification
chosen_tool: Local Verification Stack
why_this_tool: code changes exist and verification artifacts are missing
missing_artifacts:
  - targeted_test_result
next_action: run compile, targeted tests, and local review
```

如果是要交給 `Superpowers` 的版本，建議輸出格式如下：

```yaml
current_stage: implementation_planning
chosen_tool: Superpowers
why_this_tool: feature brief exists and GSD context is ready
missing_artifacts:
  - none
next_action: read context_files and produce implementation plan
handoff_payload:
  feature_brief: ...
  context_files:
    - PROJECT.md
    - ROADMAP.md
    - STATE.md
    - .planning/codebase/STACK.md
    - .planning/codebase/ARCHITECTURE.md
    - .planning/codebase/STRUCTURE.md
    - .planning/codebase/CONVENTIONS.md
    - .planning/codebase/TESTING.md
    - .planning/codebase/INTEGRATIONS.md
    - .planning/codebase/CONCERNS.md
  constraints:
    - ...
  expected_output:
    - implementation_plan
    - task_list
    - test_strategy
```

---

## 4. 第一版主流程

這是你現在要的主流程。

### Stage 0：先做 codebase mapping

目標：

- 讓 AI 先知道專案怎麼分層、哪裡 fragile、哪裡是合理的修改區域

必須要用：

- `GSD`

做法：

```text
/gsd:map-codebase
/gsd:new-project
/gsd:create-roadmap
/gsd:progress
```

---

### Stage 1：feature 分析

目標：

- 把需求變成清楚的 feature brief
- 知道影響範圍與限制

必須要用：

- `GSD`

可搭配：

- `rg`

做法：

```text
/gsd:discuss-phase 1
/gsd:research-phase 1
/gsd:list-phase-assumptions 1
/gsd:plan-phase 1
```

然後整理成單次需求文件：

```text
docs/feature-briefs/<PRD-ID>.md
```

如果要補查：

```bash
rg "TargetClass|TargetMethod|TargetDto" src test
```

---

### Stage 2：implementation planning

目標：

- 把 feature brief 變成 implementation plan

必須要用：

- `Superpowers`

做法：

```text
brainstorming
writing-plans
```

輸入來源優先順序：

1. `docs/feature-briefs/<PRD-ID>.md`
2. `PROJECT.md`
3. `ROADMAP.md`
4. `STATE.md`
5. `.planning/codebase/*.md`

---

### Stage 3：實作

目標：

- 用有紀律的方式修改 code

必須要用：

- `Superpowers`

做法：

```text
test-driven-development
subagent-driven-development
requesting-code-review
```

---

### Stage 4：本地 verification

目標：

- 確認改動沒漏掉直接相關的地方

必須要用：

- `Local Verification Stack`

做法：

```bash
git diff --name-only
rg "ChangedClass|ChangedMethod|ChangedInterface" src test
mvn test-compile
mvn -Dtest=MyServiceTest test
```

然後：

```text
/review
```

---

### Stage 5：回寫

目標：

- 把這次 feature 的知識留下來

必須要用：

- `GSD`

做法：

```text
/gsd:verify-work 1
/gsd:progress
/gsd:complete-milestone
```

#### 什麼時候呼叫 `/gsd:progress`

當這些條件成立時，就可以考慮呼叫：

- 功能已經做完
- compile / test-compile 已過
- targeted tests 已過
- `/review` 已看完
- 目前沒有打算立刻再修的問題
- 你準備把這次工作當成一個可收尾的階段

如果只是完成一個 feature，但整個 milestone 還沒結束：

```text
/gsd:progress
```

#### 什麼時候呼叫 `/gsd:complete-milestone`

當這次工作已經不只是單一 feature 收尾，而是：

- 一個 milestone 完成
- 一個 phase 完成
- 你準備正式切到下一階段

才接著呼叫：

```text
/gsd:complete-milestone
```

#### 這兩個指令是誰呼叫的

目前這套流程裡：

- 主責還是你在收尾時手動呼叫

因為：

- `Superpowers` 不負責更新 project state
- `Local Verification Stack` 只負責驗證
- `Coordinator Skill` 最多只是提醒你「現在該回寫了」

#### `STATE.md` 是誰的責任

主責 owner 是：

- `GSD`

`STATE.md` 應該只保留：

- active work
- current phase
- open blockers
- next actions

它不是：

- 永久歷史日誌
- 從古到今的完整紀錄庫

#### `STATE.md` 什麼時候有價值

當你開始出現以下情境時，`STATE.md` 會很有價值：

- 同時有多個 PRD 在跑
- 一個 feature 會做很多天
- 有 phase / milestone 概念
- 你常常中斷又回來
- 你想知道：
  - 現在做到哪
  - 下一步是什麼
  - 哪些 blocker 還沒解
- 團隊不只你一個人要看

#### `STATE.md` 什麼時候可以先不用強制管理

如果你目前是：

- 單人開發
- PRD-driven
- 以單次 feature 為主
- 已經有 `docs/feature-briefs/<PRD-ID>.md`

那第一版可以先不強制使用 `STATE.md` 作為主要恢復入口。  
這種情況下，`feature brief` 通常比 `STATE.md` 更重要。

#### `STATE.md` 什麼時候要清掉內容

不是整份刪掉，而是：

- 只保留目前有效狀態
- 已完成的詳細內容要移出或收斂

適合清理的時間點：

- 一個 feature 完成後
- 一個 milestone 完成後
- 一個 phase 切換時

建議移出去的內容：

- 已完成 feature 的詳細執行狀態
- 已解決的 blocker
- 舊 phase 的細節

建議保留的內容：

- active work
- current blockers
- next actions

---

## 5. 新專案 vs 老舊專案

### 5.1 新專案(有框架)

例如：

- Spring Boot
- Quarkus
- Micronaut

這種情況：

- `GSD` 仍然值得用
- 但 mapping 成本比較低
- `Superpowers` 和 `Local Verification Stack` 會更常被用到

建議重心：

- `GSD`：中度
- `Superpowers`：重度
- `Local Verification Stack`：重度

### 5.2 老舊專案

這種情況：

- `GSD` 幾乎是第一步必要
- 因為要先把 codebase mapping 做出來
- 不然 `Superpowers` 很難穩定知道該改哪裡

建議重心：

- `GSD`：重度
- `Superpowers`：中到重度
- `Local Verification Stack`：重度

---

## 6. 什麼時候再升級流程

### 加 `Coordinator Skill / Slash Command`

當你開始覺得：

- 流程步驟變多
- 需要有人決定現在應該先 `GSD`、`Superpowers`、還是 `verification`

### 加 `Greptile`

當你開始覺得：

- 已經有正式 GitHub / GitLab PR 流程
- 想要 remote graph-based PR review

---

## 7. 最後建議

如果你現在要的是 **真正適合 Java CLI 真實專案的第一版**，就先記住這句：

**不是先追求最少工具，而是先讓 AI 知道該改哪裡，再讓 AI 有紀律地改，最後再把本地驗證做完整。**

也就是：

```text
GSD -> Superpowers -> Local Verification Stack
```

這比單純：

```text
rg -> compile -> targeted tests -> /review
```

更符合你現在的實際場景。

如果你是 PRD-driven 日常開發，最實用的入口規則是：

- 有新的 PRD，要啟動完整流程 -> `/run-prd`
- feature brief 已存在、只是回來續做 -> `/coordinator`
- 只查 impact -> `/impact`
- 只整理本地驗證 -> `/verify-local`
- 只看最近改動 review -> `/review`

## 參考連結

- GSD 官方網站：<https://gsd.build/>
- GSD 官方 GitHub：<https://github.com/glittercowboy/get-shit-done>
- Superpowers 官方 GitHub：<https://github.com/obra/superpowers>
- ripgrep GitHub：<https://github.com/BurntSushi/ripgrep>
- Maven Surefire GitHub：<https://github.com/apache/maven-surefire>
- Maven GitHub：<https://github.com/apache/maven>
- Gradle Java Testing：<https://docs.gradle.org/current/userguide/java_testing.html>
- Oracle `jdeps`：<https://docs.oracle.com/en/java/javase/11/tools/jdeps.html>
- Claude Code Slash Commands：<https://docs.claude.com/en/docs/claude-code/slash-commands>
