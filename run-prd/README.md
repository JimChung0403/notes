# run-prd 套件

這個資料夾是給公司直接帶去用的第一版組合拳。

## 內容

- `codex_AI_dev.md`
  - 主文件
  - 說明整體方法、角色分工、流程、升級點
- `.claude/commands/run-prd.md`
  - PRD-driven 主入口
- `.claude/commands/coordinator.md`
  - 流程路由器
- `.claude/commands/impact.md`
  - 影響面分析
- `.claude/commands/verify-local.md`
  - 本地驗證清單
- `templates/feature-brief.template.md`
  - 單次需求的準備文件模板

## 建議用法

### 1. 第一次接手專案

先跑：

```text
/gsd:map-codebase
/gsd:new-project
/gsd:create-roadmap
```

### 2. 收到 PM 的 PRD 後

主入口：

```text
/run-prd docs/prd/XXX.md
```

建議每次都落一份：

```text
docs/feature-briefs/<PRD-ID>.md
```

這份是交給 `Superpowers` 開始實作前的正式準備文件。

### 3. 中途只想做局部工作

只查 impact：

```text
/impact <需求或變更描述>
```

只整理本地驗證：

```text
/verify-local
```

不確定下一步：

```text
/coordinator <目前狀態或需求描述>
```

## 這套組合拳

```text
GSD
-> 先做 codebase mapping、PRD 對齊、feature brief

Superpowers
-> 把 feature brief 轉成 implementation plan
-> TDD
-> implementation discipline

Local Verification Stack
-> rg
-> mvn test-compile / gradlew testClasses
-> targeted tests
-> /review
```

## 使用前建議確認

- 公司是否使用 `Claude Code`
- 公司 repo 是否能使用 `GSD`
- 公司 repo 是否能使用 `Superpowers`
- 專案主要是 `Maven` 還是 `Gradle`
- PRD 是否固定放在 repo 內，例如 `docs/prd/`
- 公司是否接受每個 PRD 都落一份 `docs/feature-briefs/<PRD-ID>.md`
