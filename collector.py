import feedparser
import re

from html import unescape
from urllib.parse import quote
from datetime import datetime, timezone, timedelta

from database import (
    init_db,
    add_deal,
    delete_old_deals
)


MAX_AGE_HOURS = 72


SEARCH_KEYWORDS = [
    "Amazon セール",
    "楽天 キャンペーン",
    "コンビニ キャンペーン",
    "クーポン セール",
    "飲食店 キャンペーン",
    "ポイント還元 キャンペーン",
]


def make_rss_url(keyword):
    encoded_keyword = quote(keyword)

    return (
        "https://news.google.com/rss/search"
        f"?q={encoded_keyword}"
        "&hl=ja"
        "&gl=JP"
        "&ceid=JP:ja"
    )


def is_recent(entry):
    if not hasattr(entry, "published_parsed"):
        return False

    published = datetime(
        *entry.published_parsed[:6],
        tzinfo=timezone.utc
    )

    border = (
        datetime.now(timezone.utc)
        - timedelta(hours=MAX_AGE_HOURS)
    )

    return published >= border


def clean_description(text):
    if not text:
        return "お得なキャンペーン・セール情報です。"

    # HTMLタグ削除
    text = re.sub(r"<[^>]+>", " ", text)

    # &amp; などを通常文字へ
    text = unescape(text)

    # 空白整理
    text = " ".join(text.split())

    # 長すぎる場合
    if len(text) > 200:
        text = text[:200] + "..."

    return text


def detect_category(title):
    title_lower = title.lower()

    if "amazon" in title_lower:
        return "Amazon"

    if "楽天" in title:
        return "楽天"

    convenience_words = [
        "セブン",
        "セブンイレブン",
        "ローソン",
        "ファミマ",
        "ファミリーマート",
        "ミニストップ"
    ]

    if any(word in title for word in convenience_words):
        return "コンビニ"

    food_words = [
        "マクドナルド",
        "マック",
        "ケンタッキー",
        "kfc",
        "モスバーガー",
        "すき家",
        "吉野家",
        "松屋",
        "スタバ",
        "スターバックス",
        "サイゼリヤ",
        "ガスト",
        "ジョナサン",
        "バーガーキング",
        "ドミノ",
        "ピザハット"
    ]

    if any(
        word.lower() in title_lower
        for word in food_words
    ):
        return "飲食"

    return "その他"


def collect_deals():
    print("情報収集を開始します。")

    total_added = 0
    total_old = 0

    for keyword in SEARCH_KEYWORDS:

        print()
        print("----------------------------")
        print(f"検索中：{keyword}")

        url = make_rss_url(keyword)

        feed = feedparser.parse(url)

        print(
            f"取得件数：{len(feed.entries)}件"
        )

        for entry in feed.entries:

            if not is_recent(entry):
                total_old += 1
                continue

            title = entry.get(
                "title",
                "タイトルなし"
            )

            link = entry.get(
                "link",
                ""
            )

            if not link:
                continue

            description = clean_description(
                entry.get("summary", "")
            )

            category = detect_category(title)

            added = add_deal(
                title,
                description,
                link,
                category
            )

            if added:
                total_added += 1

                print(
                    f"追加 [{category}] {title}"
                )

    print()
    print("============================")
    print(f"新規追加：{total_added}件")
    print(f"古い情報除外：{total_old}件")
    print("============================")


if __name__ == "__main__":
    init_db()

    deleted = delete_old_deals(7)

    print(
        f"DB内の古い情報削除：{deleted}件"
    )

    collect_deals()