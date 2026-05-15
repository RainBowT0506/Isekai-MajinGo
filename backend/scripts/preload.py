import sqlite3, os
from scripts.mana_library import LibraryMaster, DB_PATH

m = LibraryMaster()
tomes = m.scan_for_tomes()
conn = sqlite3.connect(DB_PATH)
for tome in tomes:
    source_id = os.path.relpath(tome, m.ASSETS_DIR).replace('\\', '/')
    dict_name = os.path.basename(tome).replace(".zip", "")
    conn.execute("INSERT OR IGNORE INTO mana_tasks (source_id, dict_name, full_path, status) VALUES (?, ?, ?, 'queued')", (source_id, dict_name, tome))
conn.commit()
conn.close()
