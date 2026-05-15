import os
import sqlite3
import json
import sys

# Add parent dir to path to import mana_library
sys.path.append(os.path.join(os.getcwd(), "backend/scripts"))
from mana_library import SoulBinder

BASE_DIR = "backend"
DB_PATH = os.path.join(BASE_DIR, "dictionary.db")

def fix_ignored_items():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 找到所有的 container 或 entry_count=0 的項目
    cursor.execute("SELECT source_id, dict_name, full_path FROM mana_tasks WHERE status = 'container' OR (status = 'success' AND entry_count = 0)")
    items = cursor.fetchall()
    
    binder = SoulBinder(DB_PATH)
    
    print(f"Found {len(items)} items to fix...")
    
    for source_id, dict_name, full_path in items:
        # 如果是 scriptin 的原始 JSON，它通常在 assets/scriptin 下
        # 如果是 TheKanjiMap，它在 temp_decipher 下 (但可能已經被刪除了，我們需要重新解壓)
        
        print(f"Processing: {dict_name} ({source_id})")
        
        # 這裡我們只處理目前還在磁碟上的檔案 (scriptin)
        # 對於 temp_decipher 裡的，建議使用者手動對該 ZIP 點擊「重試」
        if os.path.exists(full_path):
            def dummy_callback(count): pass
            count, preview = binder.bind_tome(full_path, dict_name, source_id, dummy_callback)
            
            status = "success" if count > 0 else "container"
            cursor.execute("UPDATE mana_tasks SET status = ?, entry_count = ?, preview_json = ? WHERE source_id = ?", 
                          (status, count, json.dumps(preview), source_id))
            print(f"  -> Fixed! New count: {count}, Status: {status}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_ignored_items()
