# About
AIショッピングアシスタントの作り方 - PAY.JPとLLMで実現する新しい購買体験  
https://qiita.com/pigooosuke/items/5a7173e5ee1c5a95a938

## 使い方
### required
- docker compose
- jq

### setup
```sh
# envファイルに自身が持つ各種API KEYを設定する
cp .env.example .env
# テスト用PAY.JP顧客データを作成
sh payjp-setup.sh
# AIアシスタントサービスを立ち上げる
docker compose up
# http://localhost:8001 にアクセスしてください
```
