from database import init_db, add_deal

init_db()

add_deal(
    "Amazonタイムセール",
    "Amazonでタイムセール開催中！",
    "https://www.amazon.co.jp/"
)

add_deal(
    "楽天市場キャンペーン",
    "楽天市場のお得なキャンペーン情報です。",
    "https://www.rakuten.co.jp/"
)

print("登録完了！")