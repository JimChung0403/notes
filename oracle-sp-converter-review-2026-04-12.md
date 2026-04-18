# Oracle SP Converter 深度 Review

日期: 2026-04-12

目標目錄: `/Users/jim/Documents/project/A-Team/teams/oracle-sp-converter/.claude`

## 總評

這套 Oracle SP 轉 Java agent skill 的方向是對的: 有明確的 skill、converter、tester、risk checklist，並且知道要把「未知即標記」與「平行比對測試」納入流程。這比只寫一份轉換 prompt 成熟很多。

但目前它最大的問題不是「缺少條目」，而是「承諾的品質高於實際可執行能力」。文件裡宣稱能做到精準轉換、等價驗收、平行比對測試，但 tester 的實作骨架、映射規則的語意精度、以及依賴工具鏈都還撐不起這個承諾。以文件成熟度來看不差；以可落地的 agent system 來看，仍然偏早期。

整體分數: **5.1 / 10**

## 分項分數

| 面向 | 分數 | 評語 |
|---|---:|---|
| 架構拆分 | 7.5 | skill / converter / tester / rule 的分工清楚 |
| 規則完整度 | 5.5 | 有主架構，但大量 Oracle 細節仍未被正確建模 |
| 語意正確性 | 4.0 | 多個 mapping 會導出錯誤或不等價的 Java |
| 測試可信度 | 3.0 | tester 目前無法證明「行為完全一致」 |
| 可編譯/可執行性 | 4.5 | 規則引用了不存在的 helper / dependency / wiring |
| 風險控管 | 6.0 | 知道要標風險，但停損條件不夠嚴格 |
| 維運性 | 5.0 | 結構簡潔，但缺少可機械驗證的契約 |

## 先講結論

這套設計**可以當第一版知識庫**，但**還不能當高可信 conversion pipeline**。如果你真的要拿它做 production 級 Oracle SP migration，我會先把它定位成:

1. `converter`: 產生「初稿 + 風險報告」
2. `tester`: 產生「人工輔助驗證腳手架」
3. 不要對外宣稱「自動證明完全等價」

不然最危險的地方不是轉不出來，而是**看起來有驗證，實際上驗證不到**。

## 主要優點

1. 有明確要求未知特性標記 `MANUAL_REVIEW`，這個方向正確。證據: [SKILL.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/SKILL.md) 第 99-105 行、[risk-checklist.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/risk-checklist.md) 第 31-40 行。
2. 把 schema 取得模式獨立成連線 / DDL / 盲寫 / BLOCKED 四種模式，對實務場景有幫助。證據: [SKILL.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/SKILL.md) 第 30-82 行。
3. 有把測試模板拆出來，不只是口頭說要測。證據: [CLAUDE.md](../A-Team/teams/oracle-sp-converter/CLAUDE.md) 第 13-24 行、[ParallelTestRunner.java](../A-Team/teams/oracle-sp-converter/template/sp-test-runner/src/main/java/com/sptest/runner/ParallelTestRunner.java)。

## 關鍵問題

### P0: tester 目前不能證明「完全等價」

文件聲稱 `conversion-tester` 可以「證明轉換結果與原始 SP 行為完全一致」，而且比對規則包含錯誤碼、DB 寫入資料、交易行為等。[conversion-tester.md](../A-Team/teams/oracle-sp-converter/.claude/agents/conversion/conversion-tester.md) 第 11 行、第 66-77 行。

但模板實作實際上做不到:

- 只要 SP 與 Java **都有丟 exception 就直接視為 matched**，根本沒比對錯誤碼或型別。[ParallelTestRunner.java](../A-Team/teams/oracle-sp-converter/template/sp-test-runner/src/main/java/com/sptest/runner/ParallelTestRunner.java) 第 119-123 行。
- `compareResults()` 只比對單一物件值，完全沒比對 DB side effects、資料列內容、rollback 結果。[ParallelTestRunner.java](../A-Team/teams/oracle-sp-converter/template/sp-test-runner/src/main/java/com/sptest/runner/ParallelTestRunner.java) 第 156-163 行。
- `expectedSpResult` 欄位存在但完全沒被用到，代表測試契約尚未完成。[ParallelTestRunner.java](../A-Team/teams/oracle-sp-converter/template/sp-test-runner/src/main/java/com/sptest/runner/ParallelTestRunner.java) 第 32 行。

這不是小瑕疵，這是 tester 的核心價值落空。

### P0: `@Transactional` 在 runner 裡面大概率不生效，交易測試不可信

`run()` 在同一個 bean 內直接呼叫 `callOriginalSp()` 與 `callJavaMethod()`。[ParallelTestRunner.java](../A-Team/teams/oracle-sp-converter/template/sp-test-runner/src/main/java/com/sptest/runner/ParallelTestRunner.java) 第 104-115 行。這兩個方法雖然標了 `@Transactional`，但因為是同類內部呼叫，不會經過 Spring proxy，transaction advice 通常不會生效。

結果:

- 文件說可以比對 commit/rollback 行為，但 runner 可能根本沒有獨立 transaction boundary。
- 對 `REQUIRES_NEW`、rollback-only、exception propagation 的測試都會失真。

如果 tester 連交易邊界都不可靠，那很多 SP 最敏感的行為其實沒有被驗證到。

### P0: 測試流程會互相污染資料庫狀態

目前每個案例是先呼叫原始 SP，再呼叫 Java 方法，而且兩者都是對同一個資料庫直接執行。[ParallelTestRunner.java](../A-Team/teams/oracle-sp-converter/template/sp-test-runner/src/main/java/com/sptest/runner/ParallelTestRunner.java) 第 104-125 行。

這會造成三個問題:

1. SP 已先修改資料，Java 看到的是修改後狀態，不是同一起始狀態。
2. 沒有 fixture reset / savepoint rollback / schema sandbox，案例彼此互相污染。
3. 即使結果相同，也無法說明兩者在同樣輸入與同樣初始資料下等價。

這直接推翻了「平行比對」這個說法。它現在其實是**序列執行、共享狀態、無隔離的比較**。

### P0: tester 測到的是「重寫版 Java」，不是實際轉換產物

文件要求 `callJavaMethod()` 把「轉換後的 Java 邏輯內嵌」進 runner。[conversion-tester.md](../A-Team/teams/oracle-sp-converter/.claude/agents/conversion/conversion-tester.md) 第 52-54 行、第 114-117 行。模板註解也明說是把 Service 邏輯內嵌進來。[ParallelTestRunner.java](../A-Team/teams/oracle-sp-converter/template/sp-test-runner/src/main/java/com/sptest/runner/ParallelTestRunner.java) 第 68-69 行。

這會導致:

- tester 不是在測 converter 輸出的 service class
- agent 需要再「重寫一次」相同邏輯，容易二次偏差
- 若 converter 與 tester 同時犯一樣的錯，測試會假陽性

正確做法應該是 runner **直接注入並呼叫 converter 產生的 service**，而不是複製邏輯。

### P1: 規則宣稱「禁止用 Object 偷懶」，但文件自己又示範 `Object`

[SKILL.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/SKILL.md) 第 95-97 行寫明禁止使用 `Object` 作為偷懶替代；但 [type-mapping.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/type-mapping.md) 第 47-49 行在 `%TYPE` 不可推斷時直接示範 `Object vName;`。

這會造成 agent 行為不穩定:

- 一份規則說不准
- 另一份規則提供了合法範例

最後 model 很可能挑比較省事的那個。

### P1: 多個 mapping 規則在 Oracle 語意上不夠精準，會生成錯誤 Java

這份 skill 最大的深層問題，是它不是單純「少幾個條目」，而是**已有條目中有不少是語意不保真的簡化**。

例子:

- `SUBSTR(s, pos, len)` 只給 `substring(pos - 1, pos - 1 + len)`，沒處理 Oracle 對 `pos <= 0`、負索引、省略 `len` 的語意。[function-mapping.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/function-mapping.md) 第 7 行。
- `INSTR` 只處理兩參數版本，沒處理起始位置與 occurrence。[function-mapping.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/function-mapping.md) 第 8 行。
- `TRIM/LTRIM/RTRIM` 直接對應 `strip*`，但 Oracle 與 Java 對 trim 的字元集合與語意不同。[function-mapping.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/function-mapping.md) 第 10-14 行。
- `LENGTH(s)` 直接對 `s.length()`，若 `s == null` 會 NPE；Oracle `LENGTH(NULL)` 回傳 `NULL`。[function-mapping.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/function-mapping.md) 第 20 行。
- `SYSDATE` → `LocalDateTime.now()`，這是 app server 時鐘，不是 DB server 時鐘。[function-mapping.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/function-mapping.md) 第 46 行。前面 skill 又主張 SQL 盡量原樣保留，兩者理念衝突。[SKILL.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/SKILL.md) 第 88-93 行。
- `MONTHS_BETWEEN` 被簡化成 `ChronoUnit.MONTHS.between`，Oracle 會有小數月份語意，這不是等價轉換。[function-mapping.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/function-mapping.md) 第 49 行。
- `NVL` / `NVL2` / `COALESCE` 只檢查 Java `null`，沒有把 Oracle 空字串當 `NULL` 一併補償。[function-mapping.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/function-mapping.md) 第 87-90 行，與 [type-mapping.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/type-mapping.md) 第 52-64 行不一致。
- `DECODE` 用 `Map.of(...).getOrDefault(...)` 是危險簡化，既不支援 Oracle 的多型別比較規則，也可能遇到 `null` value/key 問題。[function-mapping.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/function-mapping.md) 第 91 行。

這類 mapping 如果不改，agent 產出的 Java 很容易「長得像對，但語意錯」。

### P1: 語法對照表中也存在不等價或高風險建議

例子:

- `RETURNING INTO` 被建議改成先取 sequence 再 insert。[syntax-mapping.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/syntax-mapping.md) 第 85-95 行。這只適用非常特定情境，對 trigger、default expression、multi-row returning 都不等價。
- `EXECUTE IMMEDIATE` 的範例不是拒絕轉換，而是直接示範字符串拼接 SQL，只加一個 `MANUAL_REVIEW` 註解。[syntax-mapping.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/syntax-mapping.md) 第 104-111 行。這在實務上很容易被 model 當成「可以這樣轉」。
- Collection 對照把 `col.FIRST` 簡化成 `0`、`LAST` 簡化成 `list.size() - 1`。[syntax-mapping.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/syntax-mapping.md) 第 242-251 行。這不符合 PL/SQL collection 尤其是 sparse collection、associative array 的語意。
- `同一 Service 內` 直接呼叫方法，[syntax-mapping.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/syntax-mapping.md) 第 255-258 行，若牽涉 transaction propagation / AOP，同樣有 proxy bypass 風險。

### P1: 文件引用了多個不存在的 helper / dependency，生成碼可能不會 compile

規則大量引用但專案未提供:

- `OracleStringUtils.ltrim/rtrim` [function-mapping.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/function-mapping.md) 第 13-14 行
- `StringUtils.leftPad/rightPad` 與 `WordUtils.capitalizeFully` [function-mapping.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/function-mapping.md) 第 17-19 行
- `convertFmt(fmt)` [function-mapping.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/function-mapping.md) 第 54-55 行、第 81 行
- `transactionManager`、`DefaultTransactionDefinition`、`Propagation` [syntax-mapping.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/syntax-mapping.md) 第 200-227 行

但模板 `pom.xml` 只有 `spring-boot-starter-data-jpa` 與 `ojdbc11`，沒有 Apache Commons、沒有任何 shared utility module。[pom.xml](../A-Team/teams/oracle-sp-converter/template/sp-test-runner/pom.xml) 第 22-31 行。

也就是說，規則庫目前會引導 agent 生成**無法直接編譯**的程式。

### P1: `sp-converter` 的範例本身就違反自己的交易規則

`sp-converter` 範例把 DML 包在 `try/catch` 內，catch 後直接 `return -1`。[sp-converter.md](../A-Team/teams/oracle-sp-converter/.claude/agents/conversion/sp-converter.md) 第 171-180 行。

但在 Spring 裡，這樣通常不會 rollback，因為 exception 被吞掉了。這和它前面宣稱的:

- `ROLLBACK` 依賴 `@Transactional` 的異常自動 rollback
- 要做 transaction boundary 等價

是直接互相衝突的。[conversion-quality.md](../A-Team/teams/oracle-sp-converter/.claude/rules/conversion-quality.md) 第 22-25 行、[syntax-mapping.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/syntax-mapping.md) 第 196-202 行。

也就是說，agent 最容易學到的範例，恰好是錯的。

### P2: schema 模式設計有概念，但缺少真正可操作的契約

目前只寫「透過 `sqlplus` 或腳本查詢」data dictionary。[SKILL.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/SKILL.md) 第 43-58 行。

缺的東西包括:

- 連線字串格式契約
- schema owner / synonym / package 所屬解析規則
- 查詢 SQL 範本
- 查到多個同名 table 時怎麼 disambiguate
- 如何把 schema 查詢結果變成結構化 context 給 agent 使用

這部分目前比較像作業說明，不像可執行協議。

### P2: 風險清單有方向，但 coverage 仍然不足

目前 risk checklist 已經抓到不少高風險特性，這點是好的。[risk-checklist.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/ref/risk-checklist.md) 第 5-29 行。

但仍少幾類在 SP migration 很常踩到的東西:

- `%FOUND` / `%NOTFOUND` / `%ISOPEN`
- `SQL%BULK_ROWCOUNT` / `SQL%BULK_EXCEPTIONS`
- `NOCOPY`
- package cursor
- `BFILE`
- `ROWID` / `UROWID`
- synonym / editioning / invoker-rights (`AUTHID CURRENT_USER`)
- trigger side effects 對 SP 行為的影響

不一定要全轉，但至少該在 risk checklist 裡明確列為 blocked 或 manual-review。

## 建議修補順序

### 第一階段: 先把「錯的承諾」收斂成「對的承諾」

1. 把 tester 的宣稱從「證明完全一致」改成「產生可執行比對腳手架 + 報告差異」。
2. 明確標註目前 tester 只保證:
   - OUT / return 值比對
   - exception 類型與 error code 比對
   - 可選的資料列快照比對
3. 對無法隔離 DB state 的案例，直接輸出 `TEST_LIMITATION`，不要假裝 PASS 有意義。

### 第二階段: 修 tester 的方法學

1. 不要把 Java 邏輯內嵌進 runner，改成直接注入 converter 產出的 service。
2. 每個案例要在**相同初始資料**下跑 SP 與 Java。
3. 實作 reset 機制，選一種:
   - 每案例前載入 fixture SQL
   - 每案例包在 transaction + rollback
   - 每案例使用獨立 schema / test container database clone
4. exception 比對要至少比:
   - exception class
   - Oracle error code / BusinessException errorCode
   - message pattern
5. DB side effect 比對要有明確 contract:
   - 受影響表名
   - 驗證 SQL
   - case 前後 snapshot

### 第三階段: 把 mapping 從「語法對應」提升到「語意對應」

1. 把高風險 function mapping 拆成:
   - `safe direct mapping`
   - `helper required`
   - `manual review required`
2. 不要再把 `SUBSTR`、`INSTR`、`MONTHS_BETWEEN`、`DECODE` 這類複雜函式寫成一行簡化版。
3. 把 Oracle 空字串 = NULL 規則抽成統一 helper，而不是零散寫在不同章節。
4. 對 `RETURNING INTO`、`EXECUTE IMMEDIATE`、collection methods 重新分級:
   - 能保真才自動轉
   - 否則一律 blocked / manual review

### 第四階段: 補齊可編譯依賴

1. 提供 shared helper library，例如:
   - `OracleStringSemantics`
   - `OracleDateFormatConverter`
   - `OracleExceptionMapper`
2. 在模板或主專案明確加入需要的 dependencies。
3. 把「首次轉換時一併產生的基礎類別」明確列成固定檔案清單，不要只放在文字描述中。[SKILL.md](../A-Team/teams/oracle-sp-converter/.claude/skills/oracle-sp-to-java/SKILL.md) 第 154-167 行。

### 第五階段: 定義 machine-checkable 契約

建議讓 converter 每次輸出固定 artifact:

1. `converted-service.java`
2. `conversion-report.json`
3. `risk-report.json`
4. `schema-context.json`
5. `test-plan.json`

這樣 tester 就不用重新從自由文本理解一次，可以直接吃結構化輸出。

## 我會怎麼重定義這個系統

### converter 的責任

- 把 SP 拆成 AST-like 結構或至少區塊化 IR
- 產出 Java 初稿
- 產出 risk report
- 產出 dependency report
- 產出 required helper list

### tester 的責任

- 只測 converter 產物，不重寫邏輯
- 建 fixture / reset / snapshot
- 比對 return / exception / DB delta
- 產出 failure diff

### rule 的責任

- 每條規則都標記等級:
  - `EXACT`
  - `APPROXIMATE`
  - `MANUAL_REVIEW_REQUIRED`
  - `BLOCKED`

目前最大的缺點是這些等級沒有被明確建模，導致很多「近似規則」被包裝成「精確轉換」。

## 最值得先修的 8 件事

1. 修 `ParallelTestRunner` 的 transaction 與比對邏輯，不要再把「雙方都有 exception」直接算 PASS。
2. 改 tester，直接呼叫 converter 產出的 service，不要內嵌重寫 Java 邏輯。
3. 建立案例 reset / fixture 機制，否則測試結果不可信。
4. 把所有高風險 mapping 改成 helper 或 `MANUAL_REVIEW`，尤其是 `SUBSTR`、`INSTR`、`DECODE`、`MONTHS_BETWEEN`、`RETURNING INTO`。
5. 消除規則互相矛盾的地方，例如「禁止 Object」卻示範 `Object`。
6. 把 compile-time dependencies 與 helper class 補齊，不要只在文件提名稱。
7. 把 `sp-converter` 範例中的錯誤交易模式拿掉，避免 model 學壞。
8. 把輸出改成結構化 artifact，讓 converter 和 tester 之間不是靠自然語言接力。

## 最後判斷

如果目標是:

- **做 PoC / 內部研究**: 可以繼續疊代，底子不算差。
- **做實際 conversion factory**: 現在還不夠，尤其 tester 這一層會給人錯誤安全感。
- **做高風險 SP migration**: 必須先補 transaction isolation、DB delta 驗證、helper library、structured artifacts，否則我不會信它的驗收報告。

一句話總結:

**這套設計有骨架，但目前最需要補的是「可驗證性」與「語意保真」，不是再多加幾條 mapping 表。**
