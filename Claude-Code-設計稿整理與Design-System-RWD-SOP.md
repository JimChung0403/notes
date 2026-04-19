# Claude Code 設計稿整理與 Design System / RWD SOP

這份文件是給在 Claude Code 中搭配設計 MCP 使用時的實作流程。

目標：

1. 讓 MCP 先正確讀懂設計稿
2. 把可重複元素整理成 reusable components
3. 把元件集中到 Design System
4. 安全地做出 `1440 / 768 / 390` 三個尺寸
5. 避免一次改太多導致畫面壞掉

## 核心原則

不要一次下這種 prompt：

```text
讀我設計稿，全部做成 component，整理到 design system，並 resize 1440/768/390
```

這種做法很容易把以下 3 件事混在一起：

1. 頁面結構整理
2. 元件抽象化
3. 響應式版型重排

正確做法是拆成 4 個階段：

1. 先分析設計稿
2. 先建立 Design System
3. 一類一類替換成 component instances
4. 最後才做 `1440 / 768 / 390`

這個順序的核心，不是保守，而是配合設計工具本身的工作模型：

1. 先辨識重複模式
2. 再建立可重用規則
3. 再讓頁面吃 instance
4. 最後才驗證不同寬度

---

## 為什麼這套流程可以 work

這套流程不是憑感覺排的，背後邏輯和目前主流設計工具、Design System、Responsive Layout 的官方能力是對齊的：

1. Claude Code 官方支援透過 MCP 連接外部工具，設計工具整合本來就是 Claude Code + MCP 的典型用法之一
2. Figma 官方把 Auto Layout 定義為讓設計可隨內容與容器變化而自動調整，是 responsive 設計的核心能力
3. Figma 官方的 components / instances / variants 模型，本來就是先定義主元件，再在頁面中重複使用
4. Figma 官方的 variables 明確可作為 design tokens 來源，用來管理 color、spacing、dimensions 等可重用值
5. 主流 responsive grid 的做法，是在不同 breakpoint 重排，而不是把 Desktop 畫面等比縮小

所以你的目標應該理解成：

1. 先把稿整理成可被系統理解的結構
2. 再讓 MCP 協助你抽象成 system
3. 最後再做跨尺寸重排

而不是：

1. 丟一張還沒整理好的畫面
2. 要 AI 一次幫你抽元件、建設計系統、做 RWD
3. 期待它完全不壞

---

## 使用前提

這套方法可行，但前提要成立：

1. 原稿至少要能被正確讀取
2. 畫面主要結構最好已經是 frame，不要全部都是 group
3. 重複元件需要真的有規律，不是表面很像其實細節都不同
4. 你要接受它是分階段整理，不是一鍵轉換

如果原稿高度依賴絕對定位、手工對齊、沒有明確 frame 結構，失敗率就會高很多。

---

## Figma 連結占位符

下面所有 prompt 範例，預設都用這個占位符：

```text
{figma_node_url}
```

你要把它替換成實際的 Figma frame 或 layer 連結，例如：

```text
https://www.figma.com/design/FILE_ID/FILE_NAME?node-id=1234-5678
```

建議做法：

1. 先在 Figma 選到你要處理的 frame 或 layer
2. 複製該 node 的連結
3. 貼進 Claude Code 的 prompt

如果一次只處理一個畫板或一個 section，穩定度通常比較高。

---

## Step 1：先打開設計稿

先在設計工具中打開你要整理的稿，確認 Claude Code 已經能透過 MCP 存取該檔案。

接著請在 Figma 選到你要整理的 frame 或 layer，複製它的連結，後面所有 prompt 都用這個連結作為目標。

這一步先不要要求它修改畫面。

---

## Step 2：先測試 Figma MCP 有沒有真的 work

在正式整理設計稿之前，先做一次最小測試。

### 測試 A：先確認 Claude Code 看得到 MCP

在終端機先跑：

```bash
claude mcp list
```

你要看到 Figma 相關的 MCP server 已經存在。

如果你是在 Claude Code 互動介面裡，也可以輸入：

```text
/mcp
```

你要確認：

1. Figma MCP server 有出現在清單中
2. 狀態不是 failed
3. 如果需要登入或授權，先完成授權

### 測試 B：用一個 Figma node 連結做讀取測試

先在 Figma 選一個最簡單的 frame，例如一個首頁畫板或單一 card，複製它的 node 連結。

然後把下面這段貼進 Claude Code：

```text
請用 Figma MCP 讀取這個節點，只做回報不要修改：
{figma_node_url}

請告訴我：
1. 這是一個什麼類型的畫面或元件
2. 你是否成功讀到其中的主要結構
3. 你目前看到的主要子區塊有哪些
如果讀不到，請直接說明卡在哪一步。
```

### 測試 C：再做一個較細的結構測試

如果上一步成功，再測一次比較細的：

```text
請用 Figma MCP 讀取這個節點，只做分析不要修改：
{figma_node_url}

請列出：
1. 最外層 frame 名稱
2. 主要子區塊數量
3. 你辨識到的重複元件
4. 你是否看得到按鈕、輸入框、卡片這類 UI 模式
```

### 什麼叫做測試成功

符合下面幾點，就代表大致可用：

1. Claude Code 能回應這個 node 是什麼畫面或元件
2. 能列出幾個主要區塊，而不是只回「我看不到」
3. 能辨識至少部分 UI 結構，例如 button、card、form
4. 不需要你把整張畫面截圖貼進聊天

### 什麼叫做測試失敗

如果出現下面情況，先不要開始做 Design System：

1. Claude Code 說找不到 Figma MCP server
2. Claude Code 說無法讀取該連結或 node
3. Claude Code 只能回非常空泛的內容，看不出真的有讀到結構
4. Claude Code 一貼連結就直接開始改設計，而不是先回報讀取結果

### 測試失敗時怎麼補救

先用這段：

```text
請不要修改設計稿。
請先確認你是否真的透過 Figma MCP 讀到這個 node：
{figma_node_url}

如果有讀到，請回傳節點名稱、主要區塊名稱、以及你看到的第一層結構。
如果沒讀到，請直接告訴我缺少的是 MCP 連線、權限、還是 node 存取。
```

如果還是不行，先回頭檢查三件事：

1. Figma MCP server 是否已連上
2. 你貼的是不是 node 連結，不是只有檔案首頁連結
3. Claude Code 目前所在環境是否已完成 Figma 授權

只有測試 A、B、C 至少通過兩個，再進入後面的設計稿整理流程。

---

## Step 3：先做分析，不修改畫面

把下面這段貼進 Claude Code：

```text
Figma 目標：{figma_node_url}

請先用 MCP 讀取我目前打開的設計稿，只做分析，不要修改任何內容。
請輸出：
1. 重複出現 3 次以上的 UI 元件
2. 可抽成 design token 的顏色、字級、間距
3. 哪些 frame 適合做 responsive
4. 哪些區塊如果直接 resize 會壞掉
```

這一步預期結果：

1. 列出哪些東西重複出現
2. 列出哪些樣式可以抽成 token
3. 指出哪些畫面區塊一縮就容易壞

如果它開始直接動稿，代表這一步 prompt 還不夠嚴格，要補一句：

```text
Figma 目標：{figma_node_url}

不要新增、刪除、移動任何圖層，只輸出分析結果。
```

失敗徵兆：

1. 它開始新建元件或新建畫板
2. 它沒有分出 tokens / components / layout 風險
3. 它只回一句「可以做」但沒有具體清單

補救 prompt：

```text
Figma 目標：{figma_node_url}

請停止修改，只回傳分析結果。
請把結果拆成 tokens、base components、complex components、responsive risk 四類。
```

---

## Step 4：整理元件拆分清單

分析完後，不要立刻做 component。先要一份清單。

貼這段：

```text
Figma 目標：{figma_node_url}

請根據剛剛的分析，幫我整理一份元件拆分清單。
請分成：
1. Design tokens
2. Base components
3. Complex components
4. 不建議 component 化的區塊
先列清單，不要開始修改。
```

理想輸出應該像這樣：

1. Design tokens：color / typography / spacing / radius / shadow
2. Base components：button / input / select / tag / checkbox / radio
3. Complex components：card / modal / navbar / tabs / table row
4. 不建議 component 化：只出現一次的活動 banner、裝飾型區塊

這一步的目的，是先把「系統性元件」跟「一次性視覺區塊」分開。

失敗徵兆：

1. 它把只出現一次的 hero / banner 也列成 base component
2. 它把整個 section 當成第一批 component
3. 它完全沒提到不建議 component 化的區塊

補救 prompt：

```text
Figma 目標：{figma_node_url}

請重新整理清單，優先保留可跨頁複用的基礎元件。
請把只出現一次或高度客製的區塊移到「不建議 component 化」。
```

---

## Step 5：建立 Design System，不碰原畫面

現在才開始修改，但只建立 Design System，不要改既有頁面。

貼這段：

```text
Figma 來源：{figma_node_url}

請不要修改現有頁面。
請另外建立一個 Design System 區塊，先建立可重複使用的基礎樣式與元件：
1. Colors
2. Typography
3. Spacing
4. Button
5. Input
6. Select / Dropdown
請先做最小可用版本，整理成 reusable components。
```

這一步結束後要檢查：

1. 是否有獨立的 Design System 區塊
2. Button / Input / Select 是否已經是 reusable component
3. 顏色與字級是否有規則，不是每個都各自獨立

失敗徵兆：

1. 它直接改動原頁面而不是建立獨立區塊
2. 它只複製了幾個元件，但沒有主元件與可重用結構
3. 它建立太多大元件，卻沒有基礎元件

補救 prompt：

```text
Figma 來源：{figma_node_url}

請停止修改現有頁面。
請只在新的 Design System 區塊建立主元件，優先完成 Button、Input、Select 這三類基礎元件。
```

---

## Step 6：補齊最基本的 Design Tokens

如果剛剛只做了元件，沒有把 token 整理好，再補一次：

```text
Figma 來源：{figma_node_url}

請把 Design System 裡的樣式整理成一致規則。
請統一：
1. 主色、灰階、狀態色
2. H1 / H2 / H3 / Body / Caption
3. 4 / 8 / 12 / 16 / 24 / 32 / 48 的 spacing 規則
4. 常用圓角與邊框規則
不要修改現有頁面，只整理 Design System。
```

最少建議要有：

1. Color：Primary / Neutral / Success / Warning / Danger
2. Type：H1 / H2 / H3 / Body / Caption
3. Spacing：4 / 8 / 12 / 16 / 24 / 32 / 48
4. Radius：4 / 8 / 12 / 16

失敗徵兆：

1. 顏色還是散落在各元件裡，沒有統一規則
2. 字級看起來接近，但名稱與層級不一致
3. 間距數值太多，沒有收斂

補救 prompt：

```text
Figma 來源：{figma_node_url}

請先不要新增更多元件。
請先把顏色、字級、間距、圓角收斂成少量可重用 tokens，再讓既有元件引用這些規則。
```

---

## Step 7：先替換一種類型的元件

不要一次把整份頁面全部替換成 component instances。

先從 Button 開始：

```text
Figma 目標：{figma_node_url}

請只處理 Button。
把目前頁面中外觀一致的按鈕，替換成 Design System 裡的 Button component instance。
不要改版面結構，不要 resize，不要碰其他元件。
```

確認沒壞之後，再處理 Input / Select：

```text
Figma 目標：{figma_node_url}

請只處理 Input、Select、Dropdown。
把頁面中對應元素替換成 Design System 裡的 component instances。
不要改 layout，不要 resize。
```

建議順序：

1. Button
2. Input / Select / Dropdown
3. Tag / Checkbox / Radio
4. Card
5. Modal / Dialog
6. Header / Nav / Tabs

不要一開始就抽整個 section 或整塊頁面。

失敗徵兆：

1. 換完 Button 之後 layout 跑掉
2. 換完元件後 instance 和原始外觀差很多
3. 它順手改了其他沒要求的區塊

補救 prompt：

```text
Figma 目標：{figma_node_url}

請回到只處理 Button 的範圍。
不要改其他元件，不要重排版面，只把外觀一致的按鈕替換成 instance。
```

---

## Step 8：每做完一輪都先檢查

每替換完一類元件，都先檢查，不要急著繼續。

貼這段：

```text
Figma 檢查目標：{figma_node_url}

請檢查目前畫面是否有以下問題，只列出問題，不要直接大改：
1. 重疊
2. 被裁切
3. 文字溢出
4. 元件 instance 與 design system 不一致
5. Auto layout 異常
```

如果它列出問題，再下：

```text
Figma 檢查目標：{figma_node_url}

請只修正剛剛列出的問題，不要改動其他區塊。
```

這一步很重要，因為很多設計稿不是在 component 化時壞掉，而是在 component 化之後沒有做局部檢查。

失敗徵兆：

1. 它沒有列問題，直接大改整頁
2. 它修一個地方，另一個地方也一起被改壞
3. 它列的不是 layout 問題，而是開始重做設計

補救 prompt：

```text
Figma 檢查目標：{figma_node_url}

請只做檢查，不要重設計。
請用「問題位置 / 問題類型 / 可能原因」格式列出問題。
```

---

## Step 9：先確認 Desktop 已經穩定

在做 `768` 和 `390` 之前，先確保 Desktop 版本已經乾淨。

貼這段：

```text
Figma 檢查目標：{figma_node_url}

請確認目前 Desktop 畫板已經完成以下事項：
1. 主要重複元件已替換成 instances
2. Design System 已存在
3. 沒有明顯 overflow / clipping / overlap
請只列出未完成項目。
```

如果這一步還有缺漏，就不要急著做 responsive。

失敗徵兆：

1. Desktop 還有 overflow / clipping
2. 主要元件還不是 instance
3. Design System 還只是一些視覺樣本，不是真正可重用元件

補救 prompt：

```text
Figma 檢查目標：{figma_node_url}

在開始 Tablet 和 Mobile 前，請先補齊 Desktop 未完成項目。
不要建立新尺寸畫板，先把 Desktop 整理乾淨。
```

---

## Step 10：複製出 768 Tablet 版本

注意：這一步不是縮放，是重排。

貼這段：

```text
Figma Desktop 來源：{figma_node_url}

請以目前 Desktop 畫板為基礎，複製出一個 Tablet 畫板，寬度設定為 768。
注意：
1. 不要等比例縮放整個畫面
2. 優先調整 auto layout、padding、gap、stack direction
3. 元件優先沿用 Design System component
4. 必要時建立元件尺寸 variant
```

完成後檢查：

```text
Figma Tablet 檢查目標：{figma_node_url}

請檢查 768 畫板是否有：
1. 橫向內容擠壓
2. 卡片過窄
3. 文字換行異常
4. 按鈕或表單元件尺寸不合理
只列問題。
```

Tablet 重點不是把所有東西變小，而是把桌面上的多欄排版重新分配。

失敗徵兆：

1. 畫面只是整體縮小
2. 多欄沒有重排，內容被擠扁
3. 元件被壓縮到不可用，但還維持原結構

補救 prompt：

```text
Figma Tablet 目標：{figma_node_url}

請不要縮放整個畫板。
請改用重新排版：優先調整欄位數、stack direction、padding、gap，必要時改成上下堆疊。
```

---

## Step 11：複製出 390 Mobile 版本

Mobile 也不要用縮放，應該直接改成單欄思維。

貼這段：

```text
Figma Desktop 或 Tablet 來源：{figma_node_url}

請以目前 Desktop 或 Tablet 畫板為基礎，複製出一個 Mobile 畫板，寬度設定為 390。
注意：
1. 不要等比例縮放
2. 優先改成單欄排版
3. 視需要縮小 padding、gap、字級與元件尺寸
4. 保留 Design System component 的一致性
```

完成後檢查：

```text
Figma Mobile 檢查目標：{figma_node_url}

請檢查 390 畫板是否有：
1. 文字被擠爆
2. 元件超出畫面
3. 點擊區太小
4. 區塊間距混亂
只列問題，不要直接大改。
```

Mobile 常見調整：

1. 雙欄改單欄
2. 橫向卡片改垂直堆疊
3. padding / gap 減少
4. Button / Input 改成較小尺寸 variant

失敗徵兆：

1. 文字超出畫面
2. 仍保留 Desktop 的多欄結構
3. 元件可視上縮小了，但點擊區過小

補救 prompt：

```text
Figma Mobile 目標：{figma_node_url}

請把 Mobile 版改成單欄優先。
請保留元件系統一致性，但重新安排內容順序與堆疊方式，不要做整體縮小。
```

---

## Step 12：最後才整理 Variants

三個尺寸都穩定之後，再回頭補齊 variants。

貼這段：

```text
Figma Design System 目標：{figma_node_url}

請整理 Design System 裡需要的 variants，至少包含：
1. Button：Primary / Secondary / Ghost
2. Button size：L / M / S
3. Input size：L / M / S
4. Select size：L / M / S
請讓 1440 / 768 / 390 都優先使用同一套元件系統，而不是三套獨立元件。
```

不要一開始就做很多 variant，否則元件系統會先失控。

失敗徵兆：

1. 一開始就做出大量 variant 組合
2. 變體命名不一致
3. 同一種元件在三個尺寸變成三套不同元件

補救 prompt：

```text
Figma Design System 目標：{figma_node_url}

請收斂 variants。
先保留最必要的 type、size、state，不要為每個頁面例外建立獨立元件。
```

---

## 每次都照這個執行順序

1. 先分析，不修改
2. 先測試 Figma MCP
3. 先列元件清單，不修改
4. 建 Design System
5. 建 tokens
6. 一類一類替換元件
7. 每一輪先檢查
8. 先穩住 Desktop
9. 複製做 768
10. 複製做 390
11. 最後補 variants

---

## 絕對不要做的事

1. 不要一次下「全部 component 化 + design system + resize 1440/768/390」
2. 不要先做 mobile 再回頭抽 component
3. 不要用 scale 把 Desktop 縮成 Tablet 或 Mobile
4. 不要一開始就抽整個 section 當 component
5. 不要還沒檢查 Desktop 就直接做 `768 / 390`

---

## 可直接照貼的 Prompt 集合

### Prompt 1：分析

```text
Figma 目標：{figma_node_url}

請先用 MCP 讀取我目前打開的設計稿，只做分析，不要修改任何內容。
請輸出：
1. 重複出現 3 次以上的 UI 元件
2. 可抽成 design token 的顏色、字級、間距
3. 哪些 frame 適合做 responsive
4. 哪些區塊如果直接 resize 會壞掉
```

### Prompt 2：元件清單

```text
Figma 目標：{figma_node_url}

請根據剛剛的分析，幫我整理一份元件拆分清單。
請分成：
1. Design tokens
2. Base components
3. Complex components
4. 不建議 component 化的區塊
先列清單，不要開始修改。
```

### Prompt 3：建立 Design System

```text
Figma 來源：{figma_node_url}

請不要修改現有頁面。
請另外建立一個 Design System 區塊，先建立可重複使用的基礎樣式與元件：
1. Colors
2. Typography
3. Spacing
4. Button
5. Input
6. Select / Dropdown
請先做最小可用版本，整理成 reusable components。
```

### Prompt 4：替換 Button

```text
Figma 目標：{figma_node_url}

請只處理 Button。
把目前頁面中外觀一致的按鈕，替換成 Design System 裡的 Button component instance。
不要改版面結構，不要 resize，不要碰其他元件。
```

### Prompt 5：做 Tablet

```text
Figma Desktop 來源：{figma_node_url}

請以目前 Desktop 畫板為基礎，複製出一個 Tablet 畫板，寬度設定為 768。
不要等比例縮放整個畫面，請改用重新排版方式處理。
```

### Prompt 6：做 Mobile

```text
Figma Desktop 或 Tablet 來源：{figma_node_url}

請以目前 Desktop 或 Tablet 畫板為基礎，複製出一個 Mobile 畫板，寬度設定為 390。
不要等比例縮放，請改用單欄排版、縮小 padding/gap、保留 design system components。
```

---

## 問題排查

這一段是做壞時的判斷邏輯。先判斷壞在哪一層，再補 prompt，不要直接重來。

### 情況 1：一做 component 就壞版

可能原因：

1. 元件內外層 auto layout 沒整理
2. 原本只是看起來一樣，其實尺寸規則不同
3. 抽成 component 時把局部例外也硬塞進同一套

處理方式：

1. 先只抽最穩定的基礎元件
2. 把例外樣式保留在頁面，不要硬抽
3. 必要時做 variant，但不要過量

### 情況 2：一 resize 就壞

可能原因：

1. 用了 scale 而不是重排
2. 橫向結構沒有改成直向堆疊
3. 字級、間距、元件尺寸沒有跟著調整

處理方式：

1. 複製畫板，不縮放
2. 先改 layout direction
3. 再調整 padding / gap / component size

### 情況 3：Design System 做出來但頁面沒辦法套

可能原因：

1. 元件定義太理想化，跟現有頁面差太遠
2. 一開始就做太大的複合元件
3. 沒有先把 tokens 規格定乾淨

處理方式：

1. 先從 button / input / select 這類穩定元件開始
2. 先讓頁面吃得到基礎元件
3. 複合元件之後再補

### 情況 4：Claude Code 一次改太多

可能原因：

1. prompt 範圍太大
2. 沒有限制只處理某一類元件
3. 沒要求「先列問題，不要直接改」

處理方式：

1. 把任務縮成單一類型
2. 指定不要碰其他區塊
3. 先讓它列出修改計畫或問題點，再讓它修

可直接貼：

```text
Figma 目標：{figma_node_url}

請縮小本次修改範圍，只處理我指定的元件類型。
不要修改其他區塊，不要順手重排版面。
先列出你準備修改的目標，再開始動手。
```

### 情況 5：MCP 有讀到稿，但判斷結果很亂

可能原因：

1. 原稿命名混亂
2. frame 結構不清楚
3. 相同元件外觀差異太大

處理方式：

1. 先整理圖層命名
2. 先把明顯的 group 改成 frame
3. 先針對最乾淨的一頁做 component 化，不要整份稿同時開始

可直接貼：

```text
Figma 目標：{figma_node_url}

請先不要做 Design System。
請先分析目前檔案中命名混亂、frame 結構不清楚、無法穩定抽象成元件的區塊，只列清單與原因。
```

---

## 官方依據對照

如果你要向團隊解釋為什麼這樣做，可以直接用下面這套說法：

1. Claude Code 可透過 MCP 連到設計工具，所以「先讀設計稿再執行步驟化整理」在工具能力上成立
2. Auto Layout 的官方定位就是讓設計隨內容與容器變動而調整，因此 responsive 的核心是重排，不是縮放
3. Components / Instances / Variants 的官方模型就是先建立主元件，再讓頁面使用實例，不適合把所有差異都做成獨立元件
4. Variables 官方就是拿來做 design tokens 與多種 mode/context 管理
5. 主流 responsive grid 都強調 breakpoint 下的重排與測試，不主張把 Desktop 直接縮成 Mobile

---

## 建議執行方式

如果是第一次做，建議一天只完成下面這個範圍：

1. 分析設計稿
2. 整理元件清單
3. 建立 Design System
4. 完成 Button / Input / Select component 化

第二輪再做：

1. Card / Header / Tabs
2. Desktop 完整檢查
3. 768
4. 390

這樣穩很多。
