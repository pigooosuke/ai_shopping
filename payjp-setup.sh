#!/bin/bash

# .envファイルから環境変数を読み込む
source .env

# カードトークンを生成
response=$(curl https://api.pay.jp/v1/tokens \
    -u ${PAYJP_API_KEY}: \
    -H "X-Payjp-Direct-Token-Generate: true" \
    -d "card[number]=4242424242424242" \
    -d "card[cvc]=123" \
    -d "card[exp_month]=02" \
    -d "card[exp_year]=2099" \
    -d "card[email]=liveaccount@example.com")

# card_token_idを取得
card_token_id=$(echo $response | jq -r '.id')

# customer登録
response=$(curl -s https://api.pay.jp/v1/customers \
    -u ${PAYJP_API_KEY}: \
    -d description=test
    )

# customer_idを取得
customer_id=$(echo $response | jq -r '.id')

# customerにカードを登録
response=$(curl -s https://api.pay.jp/v1/customers/${customer_id}/cards \
    -u ${PAYJP_API_KEY}: \
    -d "card=$card_token_id"
    )

# 生成したcustomer_idをjsonファイルに保存
echo "{\"customer_id\": \"$customer_id\"}" > app/test_customer.json
echo "Saved to test customer to app/test_customer.json"