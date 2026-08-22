from flask import (
    Flask,
    render_template,
    request,
    Response,
    abort,
    url_for
)

from database import (
    init_db,
    get_deals,
    get_deal_by_id
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


@app.route("/deal/<int:deal_id>")
def deal_detail(deal_id):

    deal = get_deal_by_id(deal_id)

    if deal is None:
        abort(404)

    return render_template(
        "deal.html",
        deal=deal,
        rakuten_affiliate_url=RAKUTEN_AFFILIATE_URL
    )


@app.route("/sitemap.xml")
def sitemap():

    deals = get_deals()

    urls = []

    urls.append(
        url_for(
            "home",
            _external=True
        )
    )

    for deal in deals:

        urls.append(
            url_for(
                "deal_detail",
                deal_id=deal[0],
                _external=True
            )
        )

    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]

    for url in urls:

        xml.append("<url>")
        xml.append(f"<loc>{url}</loc>")
        xml.append("</url>")

    xml.append("</urlset>")

    return Response(
        "\n".join(xml),
        mimetype="application/xml"
    )


@app.route("/robots.txt")
def robots():

    content = """
User-agent: *
Allow: /

Sitemap: https://money-site.onrender.com/sitemap.xml
""".strip()

    return Response(
        content,
        mimetype="text/plain"
    )


if __name__ == "__main__":
    app.run(debug=True)