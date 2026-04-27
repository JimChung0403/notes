# 0到1 專案技術契約對齊清單

用途：這份文件用來在專案 kickoff 前，先把跨前後端、GraphQL、RESTful API、資料庫與開發流程的技術默契講清楚。

適用範圍：
- 前端 Web / App
- 後端 API
- GraphQL
- RESTful API
- DB 與資料處理
- 團隊開發流程

本文件的目標不是追求理論完整，而是先把容易造成返工、扯皮、事故的邊界先定義好。

---

## 一、共通契約

### 1. API 契約來源
問題：
- 前後端各自猜欄位、型別、nullable、default、enum、錯誤格式。

要討論的事項：
- 誰是 API 的單一真相來源。
- 契約變更要不要走 review。
- 契約沒更新是否允許 merge。

建議作法：
- REST：以 OpenAPI 為單一真相來源。
- GraphQL：以 schema SDL / schema registry 為單一真相來源。
- API 變更必須先更新契約，再進入實作。
- PR 若影響 API 契約，必須附 schema diff 或 OpenAPI diff。

### 2. 命名規則
問題：
- API 命名不一致，前端 mapping 成本高，資料模型容易混亂。

要討論的事項：
- 對外 API 欄位命名。
- DB 欄位命名是否可以不同。
- GraphQL 型別、欄位、enum 的命名規範。

建議作法：
- 對外 API 欄位一律使用 `camelCase`。
- DB 欄位可使用 `snake_case`，但不要外漏到 API。
- GraphQL：
  - field / argument：`camelCase`
  - type / input / enum type：`PascalCase`
  - enum value：`SCREAMING_SNAKE_CASE`
- REST path 使用名詞，不使用動詞。

### 3. 時間與時區
問題：
- 時間欄位最容易在前後端、DB、報表、排程、通知上產生誤差。

要討論的事項：
- 哪些欄位是瞬時時間。
- 哪些欄位是本地商業時間。
- 哪些欄位只是日期，不包含時間。
- 前端送後端與後端回前端的時間格式。

建議作法：
- 跨邊界傳輸一律使用 RFC 3339 字串，必須帶 `Z` 或 offset。
- 不接受沒有時區資訊的 datetime 字串。
- 瞬時時間例如 `createdAt`、`updatedAt`、`paidAt`：一律以 UTC 儲存。
- 本地商業時間例如營業時間、排班時間、出發時間：另外保存 local datetime 與 timezone ID。
- 純日期例如生日、會計日、出貨日：使用 date-only，不偷塞 `00:00:00`。

### 4. 金額、精度與四捨五入
問題：
- 不同層各自 round，帳會對不起來。

要討論的事項：
- 金額型別。
- 匯率、折扣、稅額精度。
- 四捨五入規則與時機。

建議作法：
- 金額不用 binary float。
- 統一使用 decimal / fixed-point。
- 先定最小單位，例如分、厘。
- 先定 rounding rule，例如四捨五入、無條件捨去、銀行家捨入。
- 報表、付款、退款、發票使用同一套規則。

### 5. 驗證責任
問題：
- 只做前端驗證無法當安全邊界。
- 只做型別驗證不等於通過商業規則驗證。

要討論的事項：
- syntax validation 在哪層。
- semantic validation 在哪層。
- rich text / HTML / 檔案上傳怎麼處理。

建議作法：
- 前端驗證：只負責 UX 與即時提示。
- 後端驗證：負責最終裁決。
- 驗證拆成兩層：
  - 結構與格式驗證
  - 商業規則驗證
- 驗證以 allowlist 為主，不靠 denylist。

### 6. 授權與資料 ownership
問題：
- 欄位由誰決定沒講清楚，之後一定出現權限問題與資料覆寫問題。

要討論的事項：
- 哪些欄位 client 可提交。
- 哪些欄位只能由後端設定。
- 哪些欄位是 server source of truth。

建議作法：
- `status`、`role`、`price`、`isAdmin`、`approvedBy` 類欄位由後端決定。
- 前端只傳使用者真正可輸入的欄位。
- request model 不直接綁 domain model。

### 7. 錯誤模型
問題：
- 每支 API 回錯誤格式不同，前端無法統一處理。

要討論的事項：
- 驗證錯誤格式。
- 商業錯誤格式。
- 系統錯誤格式。
- 是否需要穩定的 machine-readable error code。

建議作法：
- REST：統一使用 Problem Details 格式。
- GraphQL：
  - 系統錯誤走 top-level `errors`
  - 可預期商業錯誤盡量做 typed response
- 所有錯誤都要有穩定 error code。
- 人類可讀訊息只用來顯示，不用來判斷流程。

### 8. 冪等、重試與重複提交
問題：
- 斷線重送、使用者雙擊、SDK retry 容易造成重複下單或重複扣款。

要討論的事項：
- 哪些操作允許 retry。
- 哪些操作需要 idempotency key。
- 重送視窗多久。

建議作法：
- 有副作用的建立、提交、付款、發送類操作，都要支援 idempotency key。
- `PUT` / `DELETE` 類操作保持 idempotent。
- 前端按鈕層也要避免重複提交。

### 9. 分頁、排序、過濾
問題：
- 清單 API 不先定，資料一多就會全面返工。

要討論的事項：
- 預設排序。
- 最大 page size。
- 是否允許無界 list。
- 查詢條件格式。

建議作法：
- 不提供無界大清單。
- REST 一開始就定 query 參數格式。
- GraphQL 大 list 一律走 pagination。
- 所有 list API 都要有穩定排序。

### 10. 觀測性
問題：
- 出事時無法從前端一路追到後端、DB、第三方服務。

要討論的事項：
- request ID、trace ID、user ID 的紀錄方式。
- 哪些欄位禁止進 log。
- error code 與告警規則。

建議作法：
- 所有 HTTP request 帶 trace / request identifiers。
- 服務、工作排程、非同步任務沿用同一套 trace context。
- PII、token、密碼、身分證字號等敏感資料不得直接進 log。

### 11. Null、空字串、缺欄位
問題：
- `null`、空字串、空陣列、欄位缺省常被混為一談。

要討論的事項：
- create / update / patch 時三者語意。
- 清除欄位要傳什麼。

建議作法：
- 文件明訂每個欄位：
  - 是否可省略
  - 是否可為 `null`
  - 空字串是否合法
- PATCH 行為必須定義清楚，不准靠實作者自行猜測。

### 12. 版本與 breaking change
問題：
- 小改動就可能讓另一端壞掉。

要討論的事項：
- breaking change 的定義。
- deprecate 與移除流程。
- 相容期多久。

建議作法：
- REST：breaking change 才升版本。
- GraphQL：優先新增欄位與 deprecate，避免直接刪欄位。
- 所有 breaking change 必須在 PR、release note、consumer 通知中明示。

---

## 二、後端

### 後端總原則
- 後端一律使用 ORM。
- 但 ORM 是預設工具，不是免思考工具。
- ORM 不代表可以忽略 SQL、索引、交易邊界、查詢成本與 roundtrip 數量。

### 1. ORM 使用邊界
問題：
- 團隊容易誤以為用了 ORM 就不需要關心 DB 與查詢效能。

要討論的事項：
- 哪些場景一律 ORM。
- 哪些場景允許 raw SQL。
- raw SQL 的 review 規則。

建議作法：
- 一般 CRUD 與業務查詢走 ORM。
- 複雜報表、大量聚合、批次更新、效能瓶頸明確的查詢，允許受控 raw SQL。
- raw SQL 必須經 code review，並附用途說明。

### 2. Entity 與 API Model 分離
問題：
- 直接把 ORM entity 當 request/response model，後面很容易出 mass assignment、欄位外漏、耦合 DB schema。

要討論的事項：
- 是否使用 DTO / input model / response model。
- entity 是否可直接序列化回前端。

建議作法：
- ORM entity 不直接暴露給 API。
- request 進 DTO。
- response 出 response model / view model。
- 不允許 controller / resolver 直接吃 entity 當 input。

### 3. 載入策略
問題：
- ORM 最常在關聯資料上產生 N+1 與隱性 roundtrip。

要討論的事項：
- eager loading、explicit loading、lazy loading 的預設策略。
- 如何觀測 SQL 次數。

建議作法：
- 預設不開 lazy loading。
- 關聯查詢優先使用 eager loading 或 projection。
- 開發與測試環境要能看到 SQL 與 query 次數。
- 對熱門 API 建立 query 數與 latency 基準。

### 4. Query 與索引責任
問題：
- ORM 會把 SQL 隱藏起來，但 DB 效能問題不會消失。

要討論的事項：
- 誰負責看 SQL 與 index。
- API 上線前是否檢查 explain plan。

建議作法：
- 熱門查詢必須觀測實際 SQL。
- 查詢條件、排序欄位、join 欄位要對應 index。
- ORM query 寫法若會產出低效 SQL，必須允許改寫。

### 5. Transaction 邊界
問題：
- transaction 散在各層，之後一定亂。

要討論的事項：
- transaction 放在哪一層。
- 一個 use case 是否只能有一個交易邊界。

建議作法：
- transaction 邊界放在 service / use case layer。
- repository 不自己偷偷開大 transaction。
- controller / resolver 不處理 transaction 細節。

### 6. GraphQL 後端規則
問題：
- GraphQL 只有一個 endpoint，但 schema、resolver、service 邊界很容易混亂。

要討論的事項：
- schema 命名規範。
- resolver 是否允許商業邏輯。
- partial response 與 top-level errors 的策略。

建議作法：
- Query field 用名詞，不用 `get`、`list` 前綴。
- Mutation field 用動詞開頭。
- resolver 只做 orchestration，不承擔商業邏輯與授權決策。
- 權限與商業規則放 business layer。

### 7. GraphQL 安全與查詢成本
問題：
- GraphQL 很容易被深層查詢、超大清單、alias、批次操作拖垮。

要討論的事項：
- depth limit。
- breadth limit。
- list size 上限。
- trusted documents / persisted queries。

建議作法：
- 所有可能很大的 list 都要分頁。
- 加 depth / breadth / rate limit。
- 第一方 client 優先使用 trusted documents。

### 8. REST 後端規則
問題：
- REST 如果沒有 method semantics 與 status code 一致性，前端和整合方會很痛苦。

要討論的事項：
- URI 命名。
- `POST` / `PUT` / `PATCH` / `DELETE` 語意。
- status code 對應。

建議作法：
- URI 使用名詞與集合。
- `POST` 用於建立或提交處理。
- `PUT` 用於完整替換，並保持 idempotent。
- `PATCH` 用於局部更新。
- 回正確的 2xx / 4xx / 5xx。

### 9. 非同步作業
問題：
- 匯入、匯出、批次重算這類操作常超時。

要討論的事項：
- 哪些操作要 async。
- client 如何查詢進度。

建議作法：
- 長任務不要同步硬等。
- 提供 job / task status API。
- 任務要可追蹤、可取消、可重試。

### 10. Migration 與 schema 變更
問題：
- 多人同時改 schema 容易互撞，也容易造成破壞式變更。

要討論的事項：
- migration 命名規範。
- backward-compatible 策略。
- rollback 方式。

建議作法：
- migration 視為正式變更物。
- 先 expand，再 contract。
- 不直接做破壞式欄位刪除。

---

## 三、前端

### 1. 前端驗證邊界
問題：
- 前端常誤把自己當最終裁判。

要討論的事項：
- 哪些驗證是 UX。
- 哪些欄位送出前要先做格式檢查。

建議作法：
- 前端驗證只負責 UX。
- 前端仍要完整接住後端 validation error 與 business error。
- 表單欄位錯誤與頁面級錯誤要分開處理。

### 2. 型別來源
問題：
- 手刻型別與 API 漂移後，很快出 runtime bug。

要討論的事項：
- 型別是否自動生成。
- API client 是否自動生成。

建議作法：
- REST：從 OpenAPI 產型別與 client。
- GraphQL：從 schema + operation 產型別。
- 禁止手刻與契約重複的核心型別。

### 3. 時間顯示與提交
問題：
- 前端最常把 server time、browser local time、user business time 混在一起。

要討論的事項：
- UI 顯示時區。
- 使用者輸入時間如何轉換。
- 日期控件與 datetime 控件的處理方式。

建議作法：
- 顯示層才做 timezone 轉換。
- 傳回後端的 datetime 必須帶 offset，或由前端明確附帶 timezone context。
- `date-only` 欄位不可被當成 datetime。

### 4. GraphQL 查詢紀律
問題：
- GraphQL 太自由，前端容易過度擴張 query。

要討論的事項：
- query ownership。
- fragment 管理。
- 是否允許臨時在頁面上亂加欄位。

建議作法：
- 一個頁面或 feature 要有明確 query owner。
- 只拿 UI 真的要用的欄位。
- connection 型清單一律遵守分頁規格。

### 5. GraphQL 錯誤處理
問題：
- GraphQL 可能同時回 `data` 與 `errors`，前端若沒 policy 容易誤判。

要討論的事項：
- partial data 是否允許 render。
- 哪些情況顯示局部資料。
- 哪些情況整頁 fail-fast。

建議作法：
- 先定 global error policy。
- 系統錯誤與商業錯誤分開處理。
- 有 partial data 時，UI 要有明確降級策略。

### 6. REST 錯誤處理
問題：
- 每支 API 若錯誤結構不同，前端無法共用處理邏輯。

要討論的事項：
- field error 如何映射到表單。
- 頁面級錯誤如何呈現。

建議作法：
- 前端依 `errorCode` 或 problem type 來判斷流程。
- 不解析自由文字訊息做邏輯分支。

### 7. 重複提交與 UX 防呆
問題：
- 使用者雙擊、切頁返回、弱網路重送都會造成重複操作。

要討論的事項：
- 提交按鈕 disable 規則。
- loading、retry、undo 的交互。

建議作法：
- 有副作用的提交操作要 disable button 或顯示 processing state。
- 與後端的 idempotency key 設計一起配合。

### 8. Null 與空狀態 UI
問題：
- UI 對 `null`、空陣列、缺欄位沒有一致處理，容易出 runtime error 或爛 UX。

要討論的事項：
- 空狀態文案。
- skeleton / empty state / error state 區分。

建議作法：
- 頁面層先定義：
  - loading state
  - empty state
  - partial state
  - error state
- component 不自行發明各種 fallback。

---

## 四、共通流程

### 1. Kickoff 流程
問題：
- 大家以為講過，其實沒寫下來。

要討論的事項：
- kickoff 時必須拍板哪些技術契約。

建議作法：
- kickoff 前先過這份文件。
- 未拍板的議題要有 owner 與 deadline。

### 2. API / Schema 變更流程
問題：
- 變更沒同步 consumer，很容易出 production 問題。

要討論的事項：
- schema diff 檢查。
- breaking change 審查。

建議作法：
- REST 做 OpenAPI diff。
- GraphQL 做 schema diff。
- 破壞性變更必須走顯式審查。

### 3. 測試責任分工
問題：
- 大家都做一點，但沒有人真的對契約負責。

要討論的事項：
- unit test、integration test、contract test、E2E test 的責任分界。

建議作法：
- 後端負責 contract test、integration test、migration test。
- 前端負責關鍵流程 E2E 與畫面狀態驗證。
- 共用 mock / fixture 要有 owner。

### 4. 開發完成定義
問題：
- 功能「寫完」與「可交付」常不是同一件事。

要討論的事項：
- Done 的定義。

建議作法：
- 至少包含：
  - 契約已更新
  - 測試已補
  - 錯誤處理已定義
  - 觀測欄位已補
  - 權限與驗證已確認
  - 文件已更新

### 5. 上線與回滾
問題：
- 0到1 專案最怕第一次上線就沒有回滾計畫。

要討論的事項：
- feature flag。
- rollback 條件。
- DB migration rollback 策略。

建議作法：
- 高風險功能優先走 feature flag。
- API 與 schema 變更避免一次性破壞式切換。
- 上線前要有 rollback runbook。

### 6. 事故追查流程
問題：
- 沒有共同的 trace / error code / log 欄位，事故會變成人肉排查。

要討論的事項：
- 發生錯誤時第一時間看哪裡。
- 誰負責初判。

建議作法：
- 用同一組 trace ID 串接前端、API、job、第三方服務。
- 所有事故單都記錄 error code、trace ID、發生時間與影響範圍。

---

## 五、建議最先拍板的 12 題

如果時間有限，至少先把下面 12 題定掉：

1. API 契約的單一真相來源是什麼。
2. 對外欄位命名是否一律 `camelCase`。
3. GraphQL 命名規範是否全面統一。
4. 前端驗證與後端驗證的責任切分。
5. datetime 是否強制帶時區。
6. DB 是否以 UTC 儲存瞬時時間。
7. 金額是否一律使用 decimal / fixed-point。
8. 錯誤格式是否統一。
9. 有副作用操作是否強制 idempotency key。
10. 後端 ORM 的例外使用邊界。
11. GraphQL 大清單是否強制分頁。
12. API / schema 變更是否強制 diff 與 review。

---

## 六、待拍板紀錄

| 議題 | Owner | 預計拍板日期 | 最終決議 |
|---|---|---|---|
| API 契約來源 |  |  |  |
| 命名規則 |  |  |  |
| 時間與時區 |  |  |  |
| 金額與精度 |  |  |  |
| 驗證責任 |  |  |  |
| 錯誤模型 |  |  |  |
| 冪等與重試 |  |  |  |
| GraphQL 分頁與限制 |  |  |  |
| ORM 邊界 |  |  |  |
| 測試責任分工 |  |  |  |

