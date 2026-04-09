# Instagram 商業帳號發文 Token 申請摘要

## 目標

用自己的 Instagram 商業帳號拿到可發文的 access token，後續給 Python 使用。

## 先選哪條路

- 優先走：`Instagram API with Instagram Login`
- 不優先走：`Instagram API with Facebook Login`

原因：

- 你的需求是「自己的 IG 商業帳號發文」
- 先用 Instagram Login 路線比較直接
- Facebook Login 路線通常會牽涉 Facebook Page 綁定和 `page_access_token`

## 建 App 時怎麼選

### 1. 新增使用案例頁面

如果看到很多選項：

- 不要選 `行銷 API`
- 不要先選 `Facebook 登入`
- 不要先選 `Threads API`

請選：

- 最底下的 `其他 / Other`

### 2. App Type 頁面

請選：

- `Business`

## App 建好後要做什麼

1. 進 App Dashboard
2. 找 Instagram 相關產品
3. 優先找 `Instagram API with Instagram Login`
4. 不要先走 `Instagram API with Facebook Login`，除非你確定要走舊的 Facebook Page 路線

## Token 至少要有的權限

- `instagram_business_basic`
- `instagram_business_content_publish`

如果沒有這兩個，後面 Python 發文通常不會過。

## 你現在的實際操作順序

1. 建 App
2. 在使用案例頁面選最底下 `其他 / Other`
3. 在 App Type 頁面選 `Business`
4. 建立完成後進 Dashboard
5. 找 `Instagram API with Instagram Login`
6. 加入你的 Instagram 商業帳號
7. 申請或產生 token
8. 確認 token 具備：
   - `instagram_business_basic`
   - `instagram_business_content_publish`

## 如何判斷自己有沒有走錯路

### 方向正確時

- 你看到的是 Instagram Login / Instagram API 的設定
- 你拿到的是給 Instagram 用的 token
- 你是在做 IG 商業帳號授權

### 方向可能走錯時

- 系統一直要求你先接 Facebook Page
- 你最後拿到的是 `page_access_token`
- 介面重點都在 Facebook Login

這通常代表你走到 `Instagram API with Facebook Login` 那條舊路線。

## 如果你回到新 session，可以直接貼這段

我現在要做的是：

- 用自己的 Instagram 商業帳號
- 申請可發文的 access token
- 路線要走 `Instagram API with Instagram Login`
- 我目前已經在 Meta Developers 建 app
- 使用案例應選最底下 `Other`
- App Type 應選 `Business`

然後請下一個 session 直接接著帶我完成：

- 找到 Instagram 產品
- 產生 token
- 檢查 scopes
- 用 Python 發第一篇貼文
