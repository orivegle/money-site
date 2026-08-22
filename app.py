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
        selected_category=selected_category
    )


if __name__ == "__main__":
    app.run(debug=True)