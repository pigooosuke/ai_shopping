# About
AIショッピングアシスタントの作り方 - PAY.JPとLLMで実現する新しい購買体験  
URLを貼る

## 使い方

```sh
# envファイルに自身が持つ各種API KEYを設定する
cp .env.example .env
# テスト用PAY.JP顧客データを作成
sh pay.jp-setup.sh
# AIアシスタントサービスを立ち上げる
docker compose up
# http://localhost:8001 にアクセスしてください
```
