import os
import json
import sqlite3
from tqdm import tqdm

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "dictionary.db")
EXTRACTED_DIR = os.path.join(BASE_DIR, "assets", "extracted")

def init_unified_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 建立統一的辭典表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS extra_definitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            reading TEXT,
            definition TEXT,
            dict_name TEXT,
            language TEXT
        )
    ''')
    # 建立匯入狀態追蹤表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS import_status (
            path TEXT PRIMARY KEY,
            dict_name TEXT,
            status TEXT,
            entry_count INTEGER DEFAULT 0,
            error_message TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_extra_word ON extra_definitions(word)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_extra_reading ON extra_definitions(reading)")
    conn.commit()
    return conn

def flatten_definition(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ; ".join([flatten_definition(item) for item in content])
    if isinstance(content, dict):
        if content.get("type") == "structured-content":
            return flatten_definition(content.get("content", ""))
        return str(content.get("text", ""))
    return str(content)

def import_dictionary(conn, dict_path, dict_name):
    cursor = conn.cursor()
    
    # 更新狀態為正在匯入
    cursor.execute("INSERT OR REPLACE INTO import_status (path, dict_name, status) VALUES (?, ?, ?)", (dict_path, dict_name, "importing"))
    conn.commit()

    term_banks = [f for f in os.listdir(dict_path) if f.startswith("term_bank")]
    language = "JA-JA"
    if "ZH" in dict_name.upper() or "中" in dict_name:
        language = "JA-ZH" if "JA" in dict_name.upper() or "日" in dict_name else "ZH-ZH"
    
    total_entries = 0
    entries_to_insert = []
    
    try:
        for tb in term_banks:
            with open(os.path.join(dict_path, tb), 'r', encoding='utf-8') as f:
                data = json.load(f)
                for entry in data:
                    word = entry[0]
                    reading = entry[1]
                    raw_content = entry[5]
                    definition = flatten_definition(raw_content)
                    entries_to_insert.append((word, reading, definition, dict_name, language))
                    total_entries += 1
                    
                    if len(entries_to_insert) >= 2000:
                        cursor.executemany('INSERT INTO extra_definitions (word, reading, definition, dict_name, language) VALUES (?, ?, ?, ?, ?)', entries_to_insert)
                        entries_to_insert = []
        
        if entries_to_insert:
            cursor.executemany('INSERT INTO extra_definitions (word, reading, definition, dict_name, language) VALUES (?, ?, ?, ?, ?)', entries_to_insert)
        
        # 更新狀態為成功
        cursor.execute("UPDATE import_status SET status = ?, entry_count = ?, updated_at = CURRENT_TIMESTAMP WHERE path = ?", ("success", total_entries, dict_path))
        conn.commit()
        print(f"SUCCESS: {dict_name} ({total_entries} entries)")
    except Exception as e:
        cursor.execute("UPDATE import_status SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP WHERE path = ?", ("failed", str(e), dict_path))
        conn.commit()
        print(f"FAILED: {dict_name} - {e}")

def main():
    conn = init_unified_db()
    
    # 1. 首先掃描所有資料夾，建立初步清單
    print("Scanning folders...")
    for root, dirs, files in os.walk(EXTRACTED_DIR):
        if "index.json" in files:
            with open(os.path.join(root, "index.json"), 'r', encoding='utf-8') as f:
                try:
                    meta = json.load(f)
                    dict_name = meta.get("title", os.path.basename(root))
                    conn.execute("INSERT OR IGNORE INTO import_status (path, dict_name, status) VALUES (?, ?, ?)", (root, dict_name, "pending"))
                except:
                    pass
    conn.commit()

    # 2. 開始逐一匯入 pending 的辭典
    cursor = conn.cursor()
    cursor.execute("SELECT path, dict_name FROM import_status WHERE status = 'pending' OR status = 'failed'")
    to_import = cursor.fetchall()
    
    print(f"Found {len(to_import)} dictionaries to process.")
    
    for path, name in to_import:
        import_dictionary(conn, path, name)

    conn.close()
    print("All tasks finished.")

if __name__ == "__main__":
    main()
