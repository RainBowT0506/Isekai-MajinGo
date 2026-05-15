import sqlite3
import os
import subprocess
import time

BASE_DIR = "/Users/linchengyi/PycharmProjects/Isekai-MajinGo/backend"
DB_PATH = os.path.join(BASE_DIR, "dictionary.db")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Only target the two items requested by the user
target_source_ids = [
    "temp_decipher/MarvNC_MarvNC)-20260508T012345Z-3-001.zip/Yomitan Dictionaries (github-MarvNC)/Japanese/[Kanji] TheKanjiMap.zip",
    "scriptin/kanjidic2-en-3.6.2+20260504132921.json.zip"
]

def get_root_zip_path(source_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    curr_id = source_id
    while True:
        cursor.execute("SELECT parent_zip_id, full_path FROM mana_tasks WHERE source_id = ?", (curr_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        parent_id, full_path = row
        if not parent_id:
            conn.close()
            return full_path
        curr_id = parent_id

# 1. Collect unique root ZIP paths and set status to queued
root_zip_paths = set()
conn = sqlite3.connect(DB_PATH)

for sid in target_source_ids:
    root_path = get_root_zip_path(sid)
    if root_path:
        root_zip_paths.add(root_path)
        # Update specific item to queued
        conn.execute("UPDATE mana_tasks SET status = 'queued', error_log = NULL, entry_count = 0 WHERE source_id = ?", (sid,))
        
        # Also ensure the root itself is queued
        root_sid = os.path.relpath(root_path, ASSETS_DIR).replace('\\', '/')
        conn.execute("UPDATE mana_tasks SET status = 'queued' WHERE source_id = ?", (root_sid,))

conn.commit()
conn.close()

print(f"Starting targeted re-processing of {len(root_zip_paths)} root ZIPs...")

# 2. Sequentially run the import script for each root ZIP
script_path = os.path.join(BASE_DIR, "scripts", "mana_library.py")

for root_path in sorted(list(root_zip_paths)):
    print(f"Processing: {root_path}")
    subprocess.run(["python3", script_path, "--zip", root_path], cwd=BASE_DIR)
    time.sleep(1)

print("Targeted items have been re-processed.")
