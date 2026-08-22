from flask import (
    Flask,
    render_template,
    request
)

from database import (
    init_db,
    get_deals
)


app = Flask(__name__)

init_db()


RAKUTEN_AFFILIATE_URL = (
    "https://hb.afl.rakuten.co.jp/hgc/"
    "1a93975d.d486e394.1a93975e.93b88581/"
    "?pc=https%3A%2F%2Fwww.rakuten.co.jp%2F"
    "&link_type=text"
    "&ut=eyJwYWdlIjoidXJsIiwidHlwZSI6InRleHQiLCJjb2wiOjF9"
)


@app.route("/")
def home():

    selected_category = request.args.get(
        "category",
        "すべて"
    )

    deals = get_deals(
        selected_category
    )

    categories = [
        "すべて",
        "Amazon",
        "楽天",
        "コンビニ",
        "飲食",
        "その他"
    ]

    return render_template(
        "index.html",
        deals=deals,
        categories=categories,
        selected_category=selected_category,
        rakuten_affiliate_url=RAKUTEN_AFFILIATE_URL
    )


if __name__ == "__main__":
    app.run(debug=True)