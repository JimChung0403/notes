# Engineering Handbook(0→1 專案技術默契)

> 0→1 專案 kickoff 時技術主管帶團隊對齊用的清單。
>
> 技術棧:**後端 Java(Spring Boot) + 強制 ORM(Spring Data JPA / Hibernate)** / **前端 GraphQL 為主 + REST 並存**(REST 用於對外 webhook、第三方整合、檔案上傳、admin 工具等)。
>
> 文件分四大塊:
> - **Part A — 共通契約**:前後端都要遵守,前後端工程師都要看
> - **Part B — 後端規範**:BE only,FE 可略過
> - **Part C — 前端規範**:FE only,BE 可略過
> - **Part D — 共通流程 & 工程文化**:全團隊適用(git / CI / 測試 / 觀測 / ADR)
>
> 每題都附「**建議作法**」,可直接採用或微調。原則:**能用工具/規範擋的,絕不靠人記**。

---

# Part A — 共通契約(前後端必看)

## A1. GraphQL Schema 主導權
- **議題**:Schema-first vs Code-first?誰主寫?新欄位 review 流程?
- **建議作法**:**Schema-first**。BE 主寫 SDL,FE 在 PR review 時參與。Schema 檔放獨立 repo 或 monorepo 共用 package,兩邊都靠它做 codegen。

## A2. GraphQL Nullability
- **議題**:GraphQL 預設 nullable,何時加 `!`?
- **建議作法**:**預設 nullable,只有 PK / enum / 業務上「不可能 null」才加 `!`**。Resolver 拋錯 non-null field 會把 null 往上 bubble,blast radius 大,寧可保守。

## A3. GraphQL Error Handling 模型
- **議題**:用 GraphQL top-level `errors[]` 還是 errors-as-data union?
- **建議作法**:**雙軌制**——
  - 系統錯誤(DB 掛、timeout、unauthorized)走 `errors[]`
  - 業務錯誤走 union result:`type CreateOrderPayload = OrderCreated | InsufficientStock | InvalidPromoCode`
  - Mutation **一律**回 Payload union,query 視情況

## A4. 命名規範(camelCase 統一)
- **議題**:API response / URL / DB 各層命名?
- **建議作法**:**全 camelCase**(GraphQL 場景無爭議,REST JSON body 也跟著用 camelCase 保持兩邊一致)。
  ```
  GraphQL
  - Field / argument / variable: camelCase            (userName, createdAt)
  - Type / Interface / Union / Enum 名稱: PascalCase   (User, OrderStatus)
  - Enum value: SCREAMING_SNAKE_CASE                  (PENDING_PAYMENT)
  - Mutation: 動詞開頭 camelCase                       (createUser, cancelOrder)
  - Input type: 後綴 Input                             (CreateUserInput)
  - Payload type: 後綴 Payload                         (CreateUserPayload)
  - Boolean field: is/has/can 開頭                     (isActive, hasPermission)

  REST
  - URL path: kebab-case + 複數                        (/api/v1/order-items/{id})
  - Query param: camelCase                             (?pageSize=100&sortBy=createdAt)
  - JSON body: camelCase(對齊 GraphQL,Spring Boot 預設)
  - HTTP header: Kebab-Case                            (X-Request-Id)

  DB(BE 內部)
  - Table / column: snake_case
  - 由 JPA `@Column(name = "user_name")` 對映 Java camelCase
  ```

## A5. GraphQL Mutation 設計
- **議題**:Input / Payload 怎麼包?
- **建議作法**:
  - 每個 mutation 一個 `*Input` type(就算只有一個欄位),未來加欄位不破壞契約
  - 每個 mutation 一個 `*Payload` union(見 A3)
  - 命名動詞優先:`createUser` 不寫 `userCreate`

## A6. 分頁規範(預設 100,GraphQL/REST 一致)
- **議題**:list query 怎麼分頁?
- **建議作法**:
  - **預設 pageSize = 100**,**上限 500**(一般)/ 1000(後台 admin)
  - **GraphQL — Relay Connection**:
    ```
    禁: users: [User!]!
    必: users(first: Int, after: String): UserConnection!
    必回 pageInfo { hasNextPage, hasPreviousPage, startCursor, endCursor }
    ```
  - **REST — cursor-based**:
    ```
    GET /orders?pageSize=100&cursor=<opaque>&sortBy=createdAt&sortDir=desc
    Response: { data: [...], pageInfo: { nextCursor, hasNextPage, pageSize } }
    ```
  - **cursor-based 為主**,offset 只給 admin 工具(允許跳頁)
  - Cursor = opaque base64(包 sort_key + id),client 不准解析
  - **totalCount 預設不回**,要顯示總數才另加(避免 `SELECT COUNT(*)` 拖慢)
  - 排序欄位白名單(`sortBy=createdAt|updatedAt|id`),禁任意欄位

## A7. 時間 / 時區
- **議題**:DB / API / FE 時區處理
- **建議作法**:
  - **DB 一律存 UTC**(`TIMESTAMP WITH TIME ZONE` / `TIMESTAMPTZ`),**不要存 +8**
  - **API 線傳 ISO 8601 UTC**:`2026-04-27T10:00:00Z`(Z 結尾,不帶 offset)
  - **FE 依 user timezone render**(瀏覽器自動 / user setting)
  - GraphQL 用 custom scalar `DateTime`(string),Java 端對映 `Instant`(不是 `LocalDateTime`)
  - 「日期」(生日、報表日)用 `Date` scalar 對映 `LocalDate`,**不需時區**

## A8. 金額 / 數字精度
- **議題**:錢怎麼傳?
- **建議作法**:
  - **線傳用 string**:`"10.50"`(不是 number)
  - GraphQL custom scalar `Money` 或 `Decimal`,Java 端 `BigDecimal`,DB `NUMERIC(p,s)`
  - **禁 `double` / `float`**
  - p/s 看幣別(USD/TWD: `NUMERIC(19,4)`,JPY: `NUMERIC(19,0)`)
  - Money 物件包 `{ amount: "10.50", currency: "TWD" }` 兩欄位

## A9. ID 策略
- **議題**:UUID / ULID / bigint snowflake?
- **建議作法**:**ULID 或 UUIDv7**(time-sortable + 全域唯一)。
  - 比 UUIDv4 對 DB index 友好(時間有序,B-tree 不亂)
  - GraphQL `ID` scalar 對 client 是 opaque string,後端可彈性換
  - **ID 由 BE 生成**(見 B12),FE 不生 ID(除非離線場景)

## A10. Enum
- **議題**:string 還是 int code?
- **建議作法**:**全用 string enum,SCREAMING_SNAKE_CASE**(`PENDING_PAYMENT`)。Java enum 名稱直接對齊 GraphQL enum,**禁 int code**。

## A11. Boolean 命名
- **議題**:`active` / `isActive` / `enabled`?
- **建議作法**:**統一 `is/has/can` 前綴**:`isActive`、`hasPermission`、`canEdit`。

## A12. 空值語意
- **議題**:`null` vs `""` vs 缺欄位
- **建議作法**:
  - `null` = 「明確沒有值」
  - `""` = 「使用者輸入空字串」(若不允許,validation 擋)
  - GraphQL 缺欄位 = 「不更新」(partial update mutation,搭 `JsonNullable`)
  - **不要用 `""` 代表 null**

## A13. Error Code 表(共同維護)
- **議題**:錯誤訊息誰寫?
- **建議作法**:**BE 只回 stable error code**(`USER_NOT_FOUND`、`ORDER_INVALID_STATE`),**FE 持有翻譯字典決定文案**。
  - error code 表共同維護一份(`docs/error-codes.md`),新增 code 必須兩邊 review
  - code 命名 SCREAMING_SNAKE,**禁 `err001` 流水號**
  - 錯誤回應結構統一:`{ code, message, params, traceId }`,FE 用 `code` 查字典,套 `params`

## A14. trace_id 傳遞
- **議題**:跨服務 / FE→BE 怎麼串?
- **建議作法**:**用 W3C `traceparent` header**(OpenTelemetry 標準)。
  - FE 發第一個 request 生成 traceId,後續 mutation chain 沿用
  - BE 收到塞進 MDC,所有 log 自動帶
  - error response **必含** `traceId`,FE 顯示在錯誤畫面或 toast

## A15. 認證 Token
- **議題**:JWT vs session
- **建議作法**:
  - **MVP / 單體**:**session + Redis**(可即時 revoke)
  - **多服務 / 微服務**:JWT(短效 access token 15 min + refresh token)
  - **一旦選定中途不換**
  - Token 存放見 §C3

## A16. URL / Endpoint 設計(GraphQL vs REST 分開)

### A16.1 GraphQL Endpoint 設計
- **議題**:GraphQL 怎麼組 endpoint?
- **建議作法**:
  - **單一 endpoint**:`POST /graphql`(所有 query / mutation 都走它)
  - **Subscription**:`WS /graphql/subscriptions`(WebSocket / SSE)
  - **不分版本走 URL**(版本見 §A17,GraphQL 用 schema deprecation 取代多版本)
  - **HTTP method 永遠 POST**(GET 雖然 spec 允許,但 query 太長會超 URL 限制 + cache 麻煩,**統一用 POST**)
  - **HTTP status code 永遠 200**(就算有 errors,也回 200 + `errors[]`,這是 GraphQL spec)
    - 例外:401(未認證)、429(限流)、5xx(系統錯)可用 HTTP status
    - 業務錯誤 / 找不到資源**不用** 4xx,用 errors-as-data union(見 §A3)
  - **動詞表達在 schema 內**:
    ```graphql
    type Query {
      user(id: ID!): User           # 對應 REST GET /users/{id}
      users(first: Int): UserConn   # 對應 REST GET /users
    }
    type Mutation {
      createUser(input: CreateUserInput!): CreateUserPayload    # POST /users
      cancelOrder(id: ID!): CancelOrderPayload                  # POST /orders/{id}/cancel
    }
    ```
  - **命名遵循 §A4**:Query 用名詞 / Mutation 用動詞開頭 camelCase
  - **避免命名碰撞**:多模組可加前綴(`adminCancelOrder` / `customerCancelOrder`)或在 schema federation 切 subgraph

### A16.2 REST URL 設計
- **議題**:REST endpoint 怎麼組?
- **建議作法**:
  - **資源命名**:**複數名詞**(`/users` 不是 `/user`)
  - **路徑風格**:**kebab-case**(`/order-items` 不是 `/orderItems` / `/order_items`)
  - **巢狀最多兩層**:`/users/{id}/orders` 可,`/users/{id}/orders/{oid}/items/{iid}` 過深 → 改 top-level + filter `/items?orderId=xxx`
  - **動詞少用**,真要走 sub-resource:`POST /orders/{id}/cancel`、`POST /orders/{id}/refunds`(**不寫** `POST /cancelOrder`)
  - **不帶副檔名**:`/users/{id}` 不是 `/users/{id}.json`(用 Accept header)
  - **版本在 URL**:`/api/v1/...`(見 §A17)
  - **HTTP method 守規矩**:
    | Method | 用途 | Idempotent | Safe |
    |--------|------|-----------|------|
    | `GET` | 查詢 | ✅ | ✅ |
    | `POST` | 建立 / 不適合其他 method 的動作 | ❌ | ❌ |
    | `PUT` | 完整替換資源 | ✅ | ❌ |
    | `PATCH` | 部分更新 | ❌ | ❌ |
    | `DELETE` | 刪除 | ✅ | ❌ |
  - **禁 GET 帶 body**(部分 client / proxy 會丟掉)
  - **禁用 POST 做查詢**,除非參數真的太大塞不進 query string
  - **HTTP status code 用 4xx 不用 200 + `success: false`**:
    | Code | 用途 |
    |------|------|
    | 200 | 成功 |
    | 201 | Created(POST,`Location` header 帶新資源 URL) |
    | 204 | No Content(DELETE / PUT 不回 body) |
    | 400 | Bad Request(格式錯) |
    | 401 / 403 | 未認證 / 無權限 |
    | 404 | 找不到 |
    | 409 | 業務狀態衝突 |
    | 422 | 業務 validation 失敗 |
    | 429 | 限流 |
    | 5xx | 後端問題 |

### A16.3 GraphQL vs REST 對照表
| 面向 | GraphQL | REST |
|------|---------|------|
| Endpoint 數量 | 單一 `/graphql` | 多個 `/users`、`/orders` ... |
| HTTP method | 永遠 POST(query/mutation 都走 POST) | GET / POST / PUT / PATCH / DELETE 各司其職 |
| HTTP status | 永遠 200(系統錯例外) | 200 / 201 / 4xx / 5xx 對應業務語意 |
| 錯誤回傳 | `errors[]` + errors-as-data union | RFC 9457 `application/problem+json` + 4xx |
| 動詞表達位置 | Schema 裡的 mutation 名(`createUser`) | URL + HTTP method(`POST /users`) |
| 版本控制 | Schema deprecation(`@deprecated`) | URL path(`/api/v1/`、`/api/v2/`) |
| Cache | Apollo / urql client cache,`@cacheControl` directive | HTTP cache(`Cache-Control` / `ETag`)|
| 適用情境 | **內部前後端為主**(複雜資料圖、強類型) | **對外 webhook / 第三方整合 / 檔案上傳 / admin 工具** |

## A17. REST 版本控制
- **議題**:REST 版本放哪?
- **建議作法**:**URL path 版本**(`/api/v1/...`)。
  - Major version 才升(v1→v2 = breaking),non-breaking 加新欄位即可
  - v1 / v2 並存最少 6 個月,期間 v1 在 response header 加 `Sunset: <date>` + `Deprecation: true`

## A18. RFC 9457 錯誤格式(REST)
- **議題**:REST 錯誤 body 長怎樣?
- **建議作法**:**遵循 RFC 9457 `application/problem+json`**:
  ```json
  {
    "type": "https://api.example.com/errors/order-invalid-state",
    "title": "Order is not in a cancellable state",
    "status": 409,
    "detail": "Order #123 is already shipped",
    "instance": "/api/v1/orders/123/cancel",
    "code": "ORDER_INVALID_STATE",
    "traceId": "abc123",
    "errors": [{ "field": "amount", "code": "MIN_VALUE", "message": "must be >= 1" }]
  }
  ```

## A19. Idempotency-Key
- **議題**:重試會不會重複建立?
- **建議作法**:**所有 `POST` 寫入 endpoint 必須支援 `Idempotency-Key` header**(對外 webhook、付款、下單尤其關鍵)。
  - Client 帶 UUID,Server 用 Redis 存 key → response 24h
  - 同 key 再來 → 直接回上次 response,不重複執行

## A20. Rate Limiting
- **議題**:防濫用 / 配額
- **建議作法**:Response header **必回**:
  ```
  X-RateLimit-Limit: 1000
  X-RateLimit-Remaining: 873
  X-RateLimit-Reset: 1714200000
  ```
  超量回 `429 Too Many Requests` + `Retry-After: 60`(秒)

## A21. Webhook 設計(對外推送)
- **議題**:推 event 給 client
- **建議作法**:
  - 簽章:body 用 HMAC-SHA256 簽,放 header `X-Signature`
  - **at-least-once + Idempotency-Key**(client 自行去重)
  - 失敗重試:exponential backoff(1m → 5m → 30m → 2h → 12h),上限 24h
  - 提供 dashboard 可重發 / 看歷史

## A22. 文件
- **議題**:API 文件怎麼產?
- **建議作法**:
  - **REST**:`springdoc-openapi` code-first 自動產,UI 走 `/swagger-ui`,**禁手寫 yaml**
  - **GraphQL**:SDL 即文件,加上 `@description`,FE 用 GraphiQL / Apollo Studio 探索
  - 兩邊文件 URL 寫進 README,onboard 新人第一站

---

# Part B — 後端規範(BE only)

## B1. ORM 強制(Spring Data JPA + Hibernate)
- **議題**:資料存取統一 vs 各自為政
- **建議作法**:**全專案強制用 Spring Data JPA + Hibernate**。
  - **禁直接 `JdbcTemplate` / 手寫 `Connection`**,例外場景需 ADR 紀錄(如:批次 `INSERT` 100K 筆走 JDBC batch、複雜分析查詢效能要求)
  - Repository 一律 `extends JpaRepository<Entity, IdType>`
  - Native query 用 `@Query(value = "...", nativeQuery = true)` 包,**禁裸 `entityManager.createNativeQuery()` 散在 service**
  - 連線設定統一從 `application.yml` 讀,**禁 hard code**
- **延伸規則**:
  - **Entity 不外洩**:Controller / Resolver 一律回 DTO / Record,**禁直接回 Entity**(避免 lazy load、序列化死循環、欄位外洩)
  - **Entity 改值要落地**:從 DB 載出的 Entity 改欄位後**必須呼叫 `repository.save()`**,不要靠 dirty checking 偷偷 UPDATE
  - **Fetch 策略**:關聯預設 `FetchType.LAZY` + 查詢明標 `JOIN FETCH` 或 `@EntityGraph`,**禁靠 lazy proxy 跨 transaction 取值**
  - **IN 子句綁 Collection 必先檢查空集合**(空集合 SQL 會炸),項目數 > 1000 標 `MANUAL_REVIEW`
  - **大結果集標記**:`SELECT` 無 WHERE 等值條件 / 缺分頁 / cursor 全表掃 → 加註解 `[LARGE_RESULT_SET]`,DAO 結尾 `em.clear()`

## B2. Service / Repository / Controller 分層
- **議題**:業務邏輯放哪?
- **建議作法**:
  - `@RestController` / GraphQL Resolver:只接參數 + call service,**禁業務邏輯**
  - `@Service`:**業務邏輯都在這**,`@Transactional` 標在這層
  - `@Repository` (`extends JpaRepository`):只放 query,**禁業務判斷**
  - Controller 收 `@Validated` DTO,Service 內部用 Domain Object,Repository 對 Entity
  - **禁 Service 之間互相 inject 形成迴圈**

## B3. `@Transactional` 規則
- **議題**:transaction 邊界
- **建議作法**:
  - 標在 `@Service` public method 上,**不標 Repository / Controller**
  - **唯讀方法必標 `@Transactional(readOnly = true)`**(包括 DAO 的 find 系列)
  - 同類別內部方法互呼觸發 `@Transactional` 會失效(Spring proxy)→ **拆兩個 Service 類別**
  - `AUTONOMOUS_TRANSACTION` 用 `@Transactional(propagation = REQUIRES_NEW)`,巢狀 > 2 層標 `MANUAL_REVIEW`(HikariCP 死鎖風險)

## B4. Bean Validation
- **議題**:輸入驗證
- **建議作法**:
  - DTO 用 `@NotBlank` / `@Size` / `@Email` / `@Pattern` 等 Bean Validation annotation
  - Controller 參數加 `@Validated` / `@Valid` 觸發
  - 自訂規則寫 `ConstraintValidator`
  - **強制必做 BE validation**,不能因為 FE 已驗就省

## B5. N+1 / DataLoader 強制
- **議題**:GraphQL 跨關聯 resolver
- **建議作法**:**強制 DataLoader**(`java-dataloader` library)。
  - 任何跨關聯 field resolver 用 `BatchLoader`
  - **raw `repository.findById` 在 non-root resolver 直接 review reject**
  - DataLoader 註冊在 `DataFetchingEnvironment`,per-request scope

## B6. GraphQL Query Depth / Complexity
- **議題**:防 client 打爆
- **建議作法**:graphql-java instrumentation:**max depth = 10,max complexity = 1000**,超過 400。

## B7. GraphQL Authz Directive
- **議題**:授權檢查放哪?
- **建議作法**:**用 directive `@auth(role: ADMIN)` 標在 schema 上**,Java 用 `SchemaDirectiveWiring` 統一處理。
  - **禁 resolver 內手寫 if-else 檢查角色**
  - Field-level 也用同樣 directive,敏感欄位拿不到回 `null` + errors,**不要整個 query 拒絕**

## B8. DB Schema 設計

### B8.1 Soft Delete
- **議題**:全表軟刪除還是分情況?
- **建議作法**:**user-facing 業務表用 `deleted_at TIMESTAMPTZ NULL`**(NULL = 未刪)。log / audit / 中介表用 hard delete。
  - JPA `@SQLRestriction("deleted_at IS NULL")` 自動過濾
  - 唯一 index 包 `deleted_at`(`UNIQUE (email, deleted_at)`)否則無法重新註冊

### B8.2 Audit Fields
- **議題**:created/updated 誰填?
- **建議作法**:**全表必有 `created_at`、`updated_at`、`created_by`、`updated_by`**。
  - JPA `@EntityListeners(AuditingEntityListener.class)` 自動填,禁手動傳
  - `created_by` 從 `SecurityContextHolder` 抓
  - 配合 `@EnableJpaAuditing`

### B8.3 命名
- **建議作法**:
  - Table:**單數**(`user`、`order`,SQL 標準)
  - Column:`snake_case`
  - Index:`idx_{table}_{col1}_{col2}`
  - Unique:`uq_{table}_{col}`
  - Foreign key:`fk_{table}_{ref_table}`

### B8.4 Migration(Flyway)
- **建議作法**:**Flyway**(SQL-based)。
  - migration **forward-only**,production 禁 rollback script
  - 命名 `V{yyyyMMddHHmm}__{description}.sql`(時間戳避免 PR 撞號)
  - 一個 PR 一個 migration 檔
  - **migration 必須向後相容上一版 app**(rolling deploy 安全)

## B9. Connection Pool
- **議題**:HikariCP 設定
- **建議作法**:`maximumPoolSize` = (CPU cores × 2) + 1,監控 `pending threads`,超過告警。

## B10. ID 生成
- **議題**:ULID 在哪生?
- **建議作法**:**Service 層生成**,`UlidCreator.getMonotonicUlid().toString()`,塞進 Entity 後 save。**不靠 DB sequence / `@GeneratedValue(IDENTITY)`**(分散式不友好)。

## B11. Tenant Id
- **議題**:多租戶設計
- **建議作法**:**0→1 階段先設計 `tenant_id` 欄位**(現在只有一個租戶也要)。
  - 業務表全加 `tenant_id`
  - **Hibernate filter 自動 inject**(`@FilterDef` + `@Filter`),禁手動傳 where
  - 從 token claim 取,**不從 header**(防偽造)

## B12. Log Mask / PII Redaction
- **議題**:敏感資料寫 log
- **建議作法**:**禁寫身分證、手機、email 全文、信用卡、密碼、token**。Logback 加 mask filter,寫之前自動遮罩(`a***@gmail.com`、`0912***678`)。

## B13. WHEN OTHERS / Exception 策略
- **議題**:從 Oracle SP 翻過來的 exception swallow 怎處理?
- **建議作法**:**策略 B**:主流程 `throw` 讓 `@Transactional` rollback,catch 內開 `REQUIRES_NEW` 寫 errors 持久化。**禁「catch + commit + swallow」**。

## B14. 業務 Exception
- **議題**:checked vs unchecked
- **建議作法**:**業務 exception `extends RuntimeException`**(unchecked),Spring `@Transactional` 才會自動 rollback。**禁 `extends Exception`**。

## B15. 檔案上傳
- **議題**:大檔案怎處理?
- **建議作法**:
  - 小檔(<10MB):`multipart/form-data` 直傳,Spring `@RequestPart`
  - 大檔:**走 pre-signed URL 直接上 S3 / GCS**,後端只簽 URL 不過流量
  - 一律檢查 MIME + magic bytes(不只看副檔名)
  - size limit 在 `spring.servlet.multipart.max-file-size` + nginx `client_max_body_size` 兩層擋

## B16. Idempotency 實作
- **議題**:`Idempotency-Key` server 端怎麼存?
- **建議作法**:Redis `SETNX` 存 key + response 24h TTL。Filter 層攔截,中間件統一處理,**不寫進每個 controller**。

## B17. BE 測試
- **議題**:單元 vs 整合
- **建議作法**:
  - Unit ~70%:Service / Domain logic,Mockito mock Repository
  - Integration ~20%:`@SpringBootTest` + **Testcontainers 起真 DB**(對應 production DB 引擎)
  - **禁用 H2 mock Postgres / Oracle**(SQL 方言不一致,測過的 production 還是炸)
  - Test data:**Test Data Builder pattern**(`UserBuilder.aUser().withEmail(...).build()`),不寫共用 fixture

## B18. CORS / CSRF
- **建議作法**:
  - GraphQL / REST endpoint 只允許白名單 origin(`spring.security.cors.allowed-origins`)
  - Cookie:`Secure; HttpOnly; SameSite=Lax`
  - CSRF token 給有 cookie auth 的場景,純 token auth 可關

## B19. BOLA / 物件層授權(OWASP API #1)
- **議題**:role 對了不代表這筆資料是你的——`GET /orders/{id}` 改個 id 就拖庫,~40% API 攻擊走這條
- **建議作法**:**Service 層強制三鍵檢查** `where id = ? AND tenant_id = ? AND owner_id = ?`,**不靠 controller / resolver 自覺**
  - Spring Security `@PostAuthorize("returnObject.ownerId == authentication.principal.id")` 統一處理,resolver 內**禁手寫 if-else 比對 userId**
  - 對外 ID 一律 ULID / UUID(對齊 §A9),**禁自增 PK 暴露給 client**(自增 = 鼓勵爬)
  - **必寫一條跨 user / 跨 tenant 整合測試**:用 user A 的 token 查 user B 的 order,斷言必 403,**這條測試是必收 PR**
  - 與 GraphQL `@auth` directive(§B7,role-based)互補,**不能互相取代**:role 管「能不能進這個 mutation」,BOLA 管「能不能碰這筆資料」

## B20. Mass Assignment 防護(OWASP API #3)
- **議題**:`@RequestBody Entity` 直綁,client 多塞 `{"role":"ADMIN","tenantId":"x","approvedBy":"god"}` 就提權
- **建議作法**:**Controller / Resolver 一律收 DTO,禁直接綁 JPA Entity**(對齊 §B1 Entity 不外洩,但 input 方向也要明訂)
  - Jackson 開 `spring.jackson.deserialization.fail-on-unknown-properties=true`,多塞欄位直接 400,**不靜默忽略**
  - DTO → Entity 用 **MapStruct 顯式映射**,禁 `BeanUtils.copyProperties()` 反射 copy
  - **server-only 欄位**(`role` / `price` / `tenantId` / `status` / `approvedBy` / `createdBy` / `createdAt`)只能在 Service 層 server-side 寫入,**DTO 不收**,review reject
  - `tenantId` 從 token claim 取(對齊 §B11),**不收 client 傳的**

## B21. SSRF 防護
- **議題**:任何接收 URL 的功能(webhook callback、圖片代抓、PDF render、OAuth `redirect_uri`、SVG icon、URL preview unfurl)都能打 `169.254.169.254` 偷 IAM credential
- **建議作法**:
  - **出站 URL 走 domain allowlist**,禁任意 URL fetch
  - DNS 解析後比對 RFC1918(`10/8`、`172.16/12`、`192.168/16`) / link-local(`169.254/16`) / loopback(`127/8`、`::1`) / 雲端 metadata 段,中了直接拒
  - **禁 follow redirect**,或 redirect 後對新 URL 重新跑一次 allowlist + IP 檢查
  - EC2 / GCP 強制 **IMDSv2**(token 模式),IMDSv1 關掉
  - K8s NetworkPolicy / SecurityGroup egress 收斂到必要 domain,**不開 `0.0.0.0/0` 出站**
  - OAuth `redirect_uri` 必走 server allowlist,**禁 wildcard 比對**

## B22. Transactional Outbox(雙寫一致性)
- **議題**:`@Transactional` 內 `repository.save()` + `kafka.send()` / `webhook.post()` 是雙寫,DB commit 後 broker 連線失敗 → 訂單落地但下游收不到 event,事後 reconcile 成本爆炸
- **建議作法**:**有 event publish / webhook 派送一律走 Outbox**
  - 同一 transaction 內寫 `outbox` 表(`id, aggregate_id, event_type, payload, created_at, published_at`),**不直接打 broker**
  - 獨立 publisher 把 row 推到 broker:**首選 Debezium CDC**(讀 WAL,延遲低、無 polling 負擔),次選 polling(每秒掃 `published_at IS NULL`)
  - 推完更新 `published_at`,**failure 不更新讓它自然重推**,搭配 broker at-least-once
  - 消費端必 idempotent:`processed_events(event_id PK)` 表去重(對齊 §A19 Idempotency-Key 思路)
  - **禁在 `@Transactional` 內直接 `kafka.send()` / `webhookClient.post()` / `restTemplate.exchange()` 寫入動作**,review reject

---

# Part C — 前端規範(FE only)

## C1. GraphQL Codegen
- **議題**:類型 / hook 從哪來?
- **建議作法**:**`graphql-codegen` 強制**。
  - 從 schema 自動產 TypeScript types + Apollo / urql hooks
  - Operation 寫成 `.graphql` 檔(不寫在 component 裡),fragment colocation
  - **禁手刻 type / 用 `any`**
  - codegen 接 CI:schema 變了沒 regen 直接 fail

## C2. Persisted Queries
- **議題**:正式環境是否強制?
- **建議作法**:**MVP 不強制,上線前接 Apollo Persisted Queries**。
  - Build 時把 query 註冊到後端 hash 表
  - 上線後 client 只能跑註冊過的 query(白名單防 injection、砍 payload)

## C3. Token 存放
- **議題**:JWT / session token 放 localStorage / cookie / memory?
- **建議作法**:
  - **首選**:`HttpOnly + Secure + SameSite=Lax` cookie(BE 設,FE 看不到 → XSS 偷不到)
  - **次選**:Access token 放 memory(closure / Apollo link),refresh token 放 HttpOnly cookie
  - **禁 localStorage 存 token**(XSS 直接帶走)

## C4. 時區 Render
- **議題**:UTC 收進來,怎麼顯示?
- **建議作法**:
  - 收到 ISO 8601 UTC,**用 `date-fns-tz` / `luxon` 轉 user timezone**
  - User timezone 來源:user setting > `Intl.DateTimeFormat().resolvedOptions().timeZone`
  - **禁用原生 `new Date()` 做時區計算**(行為不一致)
  - 顯示格式統一:絕對時間 `2026-04-27 18:30 (GMT+8)`,相對時間 `3 hours ago`

## C5. 翻譯字典(i18next)
- **議題**:多語怎麼管?
- **建議作法**:
  - 用 `i18next` + `react-i18next`(或 Vue 對應 plugin)
  - 字典放 FE repo,namespace 切分(`common` / `errors` / `pages/{page}`)
  - 翻譯流程接外部翻譯平台(Crowdin / Lokalise),**避免工程師手 key**
  - **error code → 文案**也走字典(對齊 §A13)

## C6. UX Validation
- **議題**:FE validation 從哪來?
- **建議作法**:**從 GraphQL schema 衍生**。
  - BE 在 input type 加 `@constraint(minLength: 3, maxLength: 50)` directive
  - FE codegen 時順便產 `zod` / `yup` schema 給 form 用(`react-hook-form` + `@hookform/resolvers`)
  - **禁手寫兩套規則**,BE 改 FE 自動跟

## C7. Error Code → 文案映射
- **議題**:BE 回 code 怎麼變使用者訊息?
- **建議作法**:
  - error code 表(對齊 §A13)放 `i18n/errors/*.json`
  - GraphQL Apollo error link 統一處理:抽 `extensions.code` → 查字典 → toast / inline
  - **禁 component 自己寫 `if (err.code === '...')` 顯示中文字串**

## C8. State Management
- **議題**:Apollo cache?Redux?Zustand?
- **建議作法**:
  - **Server state 用 Apollo Client cache**(GraphQL 自帶,不要再包一層)
  - **Client state**(UI state、表單 draft):輕量用 `useState` / `useContext`,複雜用 **Zustand**(不選 Redux,boilerplate 太多)
  - **禁 Apollo cache 與 Redux 重複存**同一份資料

## C9. trace_id 生成
- **議題**:FE 端怎麼起 trace
- **建議作法**:每次 user action 起頭時生 `traceId`(uuid),透過 Apollo link / fetch interceptor 加 `traceparent` header。錯誤時顯示 traceId,客服回報直接帶。

## C10. Router & 權限
- **議題**:頁面權限怎麼擋?
- **建議作法**:
  - Router 層擋(React Router `loader` / Next.js middleware):未登入 redirect login
  - 角色權限走 wrapper component(`<RequireRole role="ADMIN">`)
  - **FE 擋是體驗,真正權限以 BE 為準**(BE 一定要再檢查,見 §B7)

## C11. CSP / XSS 防護
- **議題**:script injection
- **建議作法**:
  - **CSP header 嚴格**:`default-src 'self'`,inline script 必須 nonce
  - 動態 HTML 一律走 `DOMPurify` 清洗
  - **禁 `dangerouslySetInnerHTML`** 沒過 sanitize

## C12. Bundle / 效能
- **議題**:首屏速度
- **建議作法**:
  - Route-level code splitting(`React.lazy` / Next.js 自動)
  - 圖片 `next/image` 或 `<img loading="lazy">` + 響應式 srcset
  - 設定 bundle size budget(CI 擋,如 main.js < 300KB gzipped)
  - Lighthouse CI 跑分,門檻 90+

## C13. FE 測試
- **議題**:測哪些?
- **建議作法**:
  - **Component test**:Vitest / Jest + Testing Library,測互動行為,**不測 implementation detail**
  - **E2E**:Playwright(優於 Cypress,跨瀏覽器、平行快),**只測關鍵 user flow**(登入、下單、付款),不追求 100%
  - **Mock GraphQL**:用 `msw` 攔網路層,**不要 mock Apollo Client**(測不到真實行為)

## C14. a11y / 無障礙(WCAG 2.2 AA 為基準)
- **議題**:歐盟 EAA 2025/06 強制、ADA Title II 2026 已生效;後期補 = component 重寫;0→1 不訂,日後合規與大客戶投標都會炸
- **建議作法**:**驗收基準 WCAG 2.2 AA**,寫進 Done 定義(對齊 §D 開發完成定義)
  - **CI 自動化**:`@axe-core/playwright` E2E 加 a11y 斷言、`eslint-plugin-jsx-a11y` PR block(自動化只抓 30-40%,但能擋低級錯)
  - **Component 紀律**:semantic HTML 為主,**禁 `<div onClick>` 模擬 button**;互動元素必鍵盤可達(`Tab` / `Enter` / `Space` / `Esc`);**focus indicator 不可移除**(`outline: none` 必有替代 style)
  - **顏色對比**:text 4.5:1、large text / icon 3:1,用 design token 統一,**禁設計師個案決定**
  - **Touch target ≥ 24×24 px**(WCAG 2.2 新增 2.5.8),mobile 建議 44×44
  - **手動測試**:每 sprint 一次 NVDA(Win)或 VoiceOver(Mac)screen reader 過關鍵 flow(登入 / 下單 / 付款)
  - PR template 加 a11y checklist:keyboard / SR / 對比 / focus order

## C15. i18n 深層(ICU + Intl API,超越字串字典)
- **議題**:§C5 只到字串字典。複數規則(英文 1/many、阿拉伯文 6 形)、貨幣 / 數字 / 日期 locale 格式、RTL 排版會在「字典 OK 但畫面爛」時集中出事
- **建議作法**:
  - **訊息層用 ICU MessageFormat**(FormatJS / `react-intl` / `format-message`),**禁單純 `{count} 則訊息` 插值**:
    ```
    "{count, plural, =0 {沒有訊息} one {# 則訊息} other {# 則訊息}}"
    ```
  - **數字 / 貨幣 / 日期** 一律 `Intl.NumberFormat` / `Intl.DateTimeFormat` / `Intl.RelativeTimeFormat`,**禁手寫 `.toFixed()` + 字串拼接 + 寫死貨幣符號**
  - **排序** 用 `Intl.Collator`(中文 / 德文 / 瑞典文排序規則不同),**禁 `Array.sort()` 預設**
  - **RTL 準備**:CSS 一律用 logical properties(`margin-inline-start` 不寫 `margin-left`、`padding-inline-end` 不寫 `padding-right`)+ `dir="rtl"` 切換。**0→1 不上 RTL 也要先做這個習慣**,日後不用全面 refactor
  - ICU formatter 必 try/catch fallback,壞 placeholder **不能整頁炸**

---

# Part D — 共通流程 & 工程文化(全團隊)

## D1. Branch Naming
- **建議作法**:
  ```
  feature/{ticket-id}-{short-desc}    e.g. feature/PROJ-123-add-payment
  fix/{ticket-id}-{short-desc}        e.g. fix/PROJ-456-null-cart
  hotfix/{ticket-id}-{short-desc}
  chore/{short-desc}                   e.g. chore/upgrade-spring-boot
  ```
  全 kebab-case,禁人名前綴。

## D2. Commit Message(Conventional Commits)
- **建議作法**:
  ```
  feat(order): add discount calculation
  fix(auth): handle null token in refresh flow
  chore: upgrade spring-boot to 3.3.0
  ```
  `commitlint` + husky pre-commit hook 強制檢查。

## D3. PR 規範
- **建議作法**:
  - Title 同 commit message 格式
  - Description 必填三段:**What / Why / How to test**
  - **`.github/CODEOWNERS` 按 path 指派 team owner**(`/backend/order/* @team-order`),跨 ownership 的檔案 auto-request review,**branch protection 強制 owner approval 才能 merge**
  - 至少 1 reviewer + CI 全綠才能 merge
  - **Review 語意明訂**(避免文化模糊):
    - `Approve` = 我願意對這份 code 負連帶責任,可以 merge
    - `Request changes` = block,有具體必改項,改完要重 review
    - `Comment` = 建議 / 提問,**不 block merge**
  - **Review SLA**:首 review 4h、follow-up 2h、複雜 PR(> 400 行)24h,超過自動 reassign
  - **禁 force push to main / develop**
  - PR 大小目標 < 400 行(超過拆),超大 PR(> 1000 行)review reject 要求拆分

## D4. Linter / Formatter
- **建議作法**:**禁人工辯論縮排 / 引號**,工具決定一切。
  - **Java**:Spotless + google-java-format,pre-commit 自動格式化
  - **FE**:ESLint + Prettier,pre-commit 自動格式化
  - **GraphQL**:`graphql-eslint` + `prettier-plugin-graphql`
  - **SQL migration**:sqlfluff 檢查

## D5. 測試策略
- **建議作法**:
  - 金字塔:Unit ~70% / Integration ~20% / E2E ~10%
  - **新代碼覆蓋率 80%**(JaCoCo for BE / Vitest coverage for FE),**舊代碼不退步**(diff coverage)
  - **不追求 100%**(getter/setter 不算)

## D6. Schema Contract Check
- **建議作法**:
  - GraphQL:CI 跑 `graphql-inspector diff`,breaking change 強制 reviewer +2 + ADR
  - REST:CI 跑 `openapi-diff`,breaking 同上
  - Schema 變更:codegen 自動更新 FE,**FE 沒更新 CI 直接 fail**

## D7. CI/CD 環境分級
- **建議作法**:**dev / staging / prod 三層**。
  - dev:每次 merge 自動部署
  - staging:每天定時 / 手動,跑完整 E2E
  - prod:手動 + approval

## D8. Migration 部署順序
- **建議作法**:**先跑 migration,再 deploy app**。**migration 必須向後相容上一版 app**(加欄位先,刪欄位後),否則 rolling deploy 會炸。

## D9. Feature Flag
- **建議作法**:**MVP 不用**(過度工程)。**Phase 2 接 Unleash / LaunchDarkly**,半成品 feature 包 flag,不靠 long-lived branch。

## D10. Secret 管理
- **建議作法**:
  - **`.env` 禁進 repo**(`.gitignore` 第一條)
  - dev:`.env.local`(本機)
  - staging / prod:雲端 secret manager(AWS Secrets Manager / GCP Secret Manager / Vault)
  - Spring 用 `@ConfigurationProperties` + `spring.config.import=aws-secretsmanager:`

## D11. Logging 標準
- **建議作法**:**全 JSON structured log**。
  - Java:Logback + `logstash-logback-encoder`
  - FE:錯誤上報走 Sentry / Datadog Browser RUM,**不在 console.log production**
  - 共同 fields:`timestamp, level, service, traceId, spanId, userId, tenantId, message`
  - **Log level 標準**:
    - `ERROR`:需要工程師處理
    - `WARN`:異常但已處理
    - `INFO`:重要業務事件(下單、登入)
    - `DEBUG`:開發用,production 關掉
    - **使用者輸入錯誤 / 權限不足 = `INFO` 不是 `ERROR`**(否則 alert 噴爆)

## D12. Observability(OpenTelemetry)
- **建議作法**:**0→1 第一週就接 OpenTelemetry**(廠商中立)。
  - exporter 看預算選 Datadog / Grafana Tempo / Jaeger
  - BE 自動 instrument(spring-boot-starter + otel agent)
  - FE 接 Sentry / Datadog RUM
  - **晚期接成本 10x**,不是誇飾

## D13. ADR(Architecture Decision Record)
- **建議作法**:**每個重大選擇寫一份 ADR**,放 `docs/adr/`。模板:
  ```
  # ADR-001: Use ULID instead of UUIDv4 as primary key
  ## Status: Accepted (2026-04-27)
  ## Context: ...
  ## Decision: ...
  ## Consequences: ...
  ## When to revisit: ...
  ```

## D14. CONTRIBUTING.md
- **建議作法**:repo 根目錄一份,涵蓋:branch / commit / PR 規範、本機跑起來步驟、常見 troubleshooting。**新人第一份讀物**。

## D15. On-call / Runbook
- **建議作法**:**上線前先寫好** `docs/runbook/`:
  - 服務掛了第一步看哪個 dashboard
  - 常見 incident 處理步驟(DB pool 爆、外部 API timeout)
  - 升級流程(誰打給誰)
  - Post-mortem 模板(blameless,聚焦系統不是人)

## D16. SLO / SLI / Error Budget Policy
- **議題**:沒量化目標,後期「快還是穩」之爭無止境;0→1 雖無真實流量,SLO 應寫進文件作為 release gate 觸發條件
- **建議作法**:
  - **核心 API 起點 99.5% availability**(每月 ~3.6h budget),**latency SLI 用 p95 / p99 不用平均**(平均會把 long tail 平均掉)
  - **Error Budget Policy**(寫進 `docs/slo.md`):
    - burn 50% → 暫停 feature release,優先修穩定性
    - burn > 100% → 凍結除 P0 / security 外所有變更,直到下個月重置
  - **Incident Severity 分級**(對齊 §D15 runbook):
    - SEV1 = 核心服務不可用 / 資料風險,10 min 未 ack 自動 escalate,開戰情室 + 指定 Incident Commander(single decider)
    - SEV2 = 主功能受損但有 workaround,30 min escalate
    - SEV3 = 走 ticket
  - 每季 review 一次 SLO 數字,**不一開始追 99.99%**(過度工程,人力撐不住)

## D17. 備份 / RPO / RTO / Restore Drill
- **議題**:文件有 migration 規範但 0 提備份。AWS Well-Architected REL9 明訂「**未測試的備份等於沒備份**」——真出事才發現 dump 損毀已晚
- **建議作法**:
  - **寫進 ADR**:RPO ≤ 15 min(PITR / Point-in-Time Recovery 啟用)、RTO ≤ 4h
  - **每季一次 Restore Drill**:把備份還原到 isolated staging,跑 smoke test、驗 row count、驗關鍵 query,**結果寫 report 上傳 wiki**
  - 備份必**跨 region** + **KMS CMK 加密**,DB dump、S3 backup 都要
  - Restore 流程寫進 runbook,**新人 onboard 必跟一次**(光看文件不夠)
  - **0→1 不做 multi-region active-active**(過度工程,需 conflict-free data model),先把 single-region multi-AZ + PITR + cross-region backup 做扎實

## D18. IaC 紀律 + State 治理 + Drift Detection
- **議題**:0→1 一旦有人手動點 cloud console,半年後 prod 完全無法重建,drift 永遠收不齊
- **建議作法**:**Terraform**(或 Pulumi),**禁手動點 console 改 prod**
  - **State backend**:S3 / GCS remote backend + KMS 加密 + native locking(DynamoDB / GCS),**禁 local state、禁 commit `.tfstate` 進 git**
  - **每 env 獨立 workspace / folder**(dev / staging / prod 隔離,不共用 state)
  - PR 必跑 `terraform plan` 並把結果貼上 PR comment,merge 後 CI 跑 `apply`
  - **每週 cron 跑 `terraform plan -refresh-only`** 偵測 drift,有 diff 自動開 issue
  - **IAM policy 強制 console read-only**,寫操作只能透過 CI runner 角色(human 走 break-glass 流程,需另一人簽核)
  - 0→1 範圍小可先 monorepo 一份 Terraform,> 5 services 再切

---

# 執行建議

1. **kickoff 開三次會議**:
   - **第一次(全員)**:過 Part A 共通契約 — 命名、分頁、時區、金額、ID、錯誤、auth — 兩邊必須對齊
   - **第二次(BE only)**:過 Part B 後端規範 — ORM、分層、DataLoader、DB、tenant
   - **第三次(FE only)**:過 Part C 前端規範 — codegen、token 存放、validation、state management
   - 第四次(全員)收尾:Part D 流程 / 工程文化
2. **每題逼出明確 yes/no**,**不留「之後再說」**
3. **本檔當 living document**,有改動寫 PR,有爭議開 ADR
4. **CI 強制**:能用 lint / hook / inspector 擋的全部用工具擋
5. **第一個月 review 一次**,有些選擇真的會錯,早改成本低

# 最容易被低估的十個地方

1. **時區**(DB 存 +8 → 半年後出國上線地獄)
2. **金額精度**(用 double → 報表對不起來)
3. **Error Code 表共同維護**(沒設計 → FE 寫死 if-else 比對中文錯誤訊息)
4. **N+1 / DataLoader 紀律**(沒從第一天強制 → 後期重構成本爆炸)
5. **ORM 統一 + Entity 不外洩**(沒從第一天訂死 → 半年後 service 一半 JPA、一半 JdbcTemplate,審查惡夢)
6. **BOLA / 物件層授權**(只查 role 不查 ownership → 改個 id 就拖庫,OWASP API #1,占 ~40% API 攻擊)
7. **Mass Assignment**(直綁 entity → client 多塞 `role: ADMIN` 提權)
8. **Restore Drill**(備份從沒驗證 = 沒備份;真要還原時才發現 dump 損毀已晚)
9. **a11y 從第一天做**(後期補 = component 重寫,且歐盟 EAA 已強制)
10. **IaC + 禁手動 console**(一旦失控,prod 永遠無法重建,drift 收不齊)
