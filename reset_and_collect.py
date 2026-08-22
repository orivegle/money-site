from database import (
    init_db,
    delete_all_deals
)

from collector import collect_deals


print("DBを整理します...")

init_db()

deleted = delete_all_deals()

print(
    f"{deleted}件の古いデータを削除しました。"
)

print()

collect_deals()

print()
print("✅ 再収集完了")