import sqlite3
import json
import os

BASE_DIR = "/Users/linchengyi/PycharmProjects/Isekai-MajinGo/backend"
DB_PATH = os.path.join(BASE_DIR, "dictionary.db")
STATUS_DB_PATH = os.path.join(BASE_DIR, "status.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. Fix TheKanjiMap
cursor.execute("SELECT count(*) FROM dictionary_kanji WHERE source_id LIKE '%TheKanjiMap%'")
count_kanji_map = cursor.fetchone()[0]
cursor.execute("SELECT kanji, reading FROM dictionary_kanji WHERE source_id LIKE '%TheKanjiMap%' LIMIT 3")
preview_kanji_map = [{"type": "kanji", "word": r[0], "def": r[1]} for r in cursor.fetchall()]

cursor.execute("""
    UPDATE mana_tasks 
    SET status = 'success', entry_count = ?, preview_json = ?, error_log = NULL 
    WHERE source_id LIKE '%TheKanjiMap%'
""", (count_kanji_map, json.dumps(preview_kanji_map)))

# 2. Fix kanjidic2
cursor.execute("SELECT count(*) FROM dictionary_kanji WHERE source_id LIKE '%kanjidic2%'")
count_kanjidic2 = cursor.fetchone()[0]
cursor.execute("SELECT kanji, reading FROM dictionary_kanji WHERE source_id LIKE '%kanjidic2%' LIMIT 3")
preview_kanjidic2 = [{"type": "kanji", "word": r[0], "def": r[1]} for r in cursor.fetchall()]

cursor.execute("""
    UPDATE mana_tasks 
    SET status = 'success', entry_count = ?, preview_json = ?, error_log = NULL 
    WHERE source_id LIKE '%kanjidic2%'
""", (count_kanjidic2, json.dumps(preview_kanjidic2)))

# 3. Stop all other running tasks
cursor.execute("UPDATE mana_tasks SET status = 'failed', error_log = 'Interrupted by user' WHERE status IN ('binding', 'deciphering', 'queued') AND source_id NOT LIKE '%TheKanjiMap%' AND source_id NOT LIKE '%kanjidic2%'")

conn.commit()
conn.close()

# 4. Update global state
conn_status = sqlite3.connect(STATUS_DB_PATH)
conn_status.execute("UPDATE global_state SET is_running = 0 WHERE id = 1")
conn_status.commit()
conn_status.close()

print(f"Fixed TheKanjiMap: {count_kanji_map} entries.")
print(f"Fixed Kanjidic2: {count_kanjidic2} entries.")
print("Global state set to stopped.")
