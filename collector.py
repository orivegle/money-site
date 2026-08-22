import feedparser
import re

from html import unescape
from urllib.parse import quote
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher

from database import (
    init_db,
    add_deal,
    delete_old_deals,
    get_deals
)


# 直近何時間の記事を対象にするか
MAX_AGE_HOURS = 72


# 検索するキーワード
SEARCH_KEYWORDS = [
    "Amazon セール",
    "Amazon キャンペーン",
    "楽天 セール",
    "楽天 キャンペーン",
    "楽天 ポイント還元",
    "ローソン キャンペーン",
    "ファミマ キャンペーン",
    "セブンイレブン キャンペーン",
    "コンビニ 無料 クーポン",
    "マクドナルド クーポン",
    "飲食店 半額 キャンペーン",
    "ポイント還元 セール",
    "期間限定 クーポン",
]


# 「お得情報」と判断する単語
GOOD_WORDS = [
    "セール",
    "キャンペーン",
    "クーポン",
    "割引",
    "半額",
    "無料",
    "還元",
    "ポイント",
    "増量",
    "値下げ",
    "タイムセール",
    "プレゼント",
    "OFF",
    "オフ",
    "お得",
    "特価",
]


# 今回のサイトには載せたくない情報
NG_WORDS = [
    "競馬",
    "競輪",
    "競艇",
    "パチンコ",
    "パチスロ",
    "ウマ娘",
    "ゲーム内",
    "オンラインゲーム",
    "自治体キャンペーン",
    "選挙",
    "投票率",
    "ふるさと納税",
]


def make_rss_url(keyword):
    encoded = quote(keyword)

    return (
        "https://news.google.com/rss/search"
        f"?q={encoded}"
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
        return "お得なセール・キャンペーン情報です。"

    # HTML削除
    text = re.sub(r"<[^>]+>", " ", text)

    # HTML特殊文字を戻す
    text = unescape(text)

    # 空白整理
    text = " ".join(text.split())

    # 余計なGoogle News系の文字列を整理
    text = text.replace("Google ニュース", "")

    if len(text) > 180:
        text = text[:180] + "..."

    return text


def normalize_title(title):
    """
    重複判定用にタイトルを単純化
    """

    title = title.lower()

    # 「 - PR TIMES」など記事媒体名を削除
    if " - " in title:
        title = title.split(" - ")[0]

    # 記号削除
    title = re.sub(
        r"[【】\[\]（）()『』「」!！?？・,，。:：|｜]",
        "",
        title
    )

    # 空白削除
    title = re.sub(r"\s+", "", title)

    return title


def titles_are_similar(title1, title2):
    a = normalize_title(title1)
    b = normalize_title(title2)

    if a == b:
        return True

    ratio = SequenceMatcher(
        None,
        a,
        b
    ).ratio()

    return ratio >= 0.82


def is_good_deal(title, description):
    text = f"{title} {description}"

    # NGワードがあれば除外
    for word in NG_WORDS:
        if word.lower() in text.lower():
            return False

    # お得ワードが1つ以上必要
    for word in GOOD_WORDS:
        if word.lower() in text.lower():
            return True

    return False


def detect_category(title):
    text = title.lower()

    if "amazon" in text:
        return "Amazon"

    if "楽天" in title:
        return "楽天"

    convenience_words = [
        "セブン",
        "セブンイレブン",
        "ローソン",
        "ファミマ",
        "ファミリーマート",
        "ミニストップ",
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
        "スターバックス",
        "スタバ",
        "サイゼリヤ",
        "ガスト",
        "ジョナサン",
        "バーガーキング",
        "ドミノ",
        "ピザハット",
        "コメダ",
    ]

    if any(
        word.lower() in text
        for word in food_words
    ):
        return "飲食"

    return "その他"


def collect_deals():
    print("================================")
    print("🔥 お得情報の収集を開始")
    print("================================")

    total_added = 0
    total_old = 0
    total_ng = 0
    total_duplicate = 0

    # DBにすでに存在するタイトル
    existing_deals = get_deals()

    known_titles = [
        deal[1]
        for deal in existing_deals
    ]

    for keyword in SEARCH_KEYWORDS:

        print()
        print(f"🔎 検索中：{keyword}")

        feed = feedparser.parse(
            make_rss_url(keyword)
        )

        print(
            f"取得：{len(feed.entries)}件"
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

            # お得情報じゃなければ捨てる
            if not is_good_deal(
                title,
                description
            ):
                total_ng += 1
                continue

            # タイトルが似ていたら重複と判断
            duplicate = False

            for known_title in known_titles:

                if titles_are_similar(
                    title,
                    known_title
                ):
                    duplicate = True
                    break

            if duplicate:
                total_duplicate += 1
                continue

            category = detect_category(title)

            added = add_deal(
                title,
                description,
                link,
                category
            )

            if added:
                total_added += 1

                known_titles.append(title)

                print(
                    f"✅ [{category}] {title}"
                )

    print()
    print("================================")
    print(f"✅ 新規追加      ：{total_added}件")
    print(f"🕐 古い記事除外  ：{total_old}件")
    print(f"🚫 不要記事除外  ：{total_ng}件")
    print(f"♻️ 重複記事除外  ：{total_duplicate}件")
    print("================================")


if __name__ == "__main__":

    init_db()

    # 7日以上前に登録した情報を削除
    deleted = delete_old_deals(7)

    print(
        f"🗑 古いDBデータ削除：{deleted}件"
    )

    collect_deals()