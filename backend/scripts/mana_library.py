import os
import json
import zipfile
import sqlite3
import shutil
import time

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "dictionary.db")
STATUS_DB_PATH = os.path.join(BASE_DIR, "status.db")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
TEMP_EXTRACT_DIR = os.path.join(ASSETS_DIR, "temp_decipher")

# 只允許純文字檔案通過，過濾掉圖檔與音頻
ALLOWED_EXTENSIONS = {'.json', '.csv', '.txt', '.xml', '.yml', '.yaml'}

class TomeStatus:
    QUEUED = "queued"
    DECIPHERING = "deciphering"
    BINDING = "binding"
    SUCCESS = "success"
    FAILED = "failed"

class SoulBinder:
    """負責將數據靈魂綁定到資料庫的核心邏輯。"""
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        
        # 詞條表 (混合模型：固定欄位 + JSON)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dictionary_terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT, reading TEXT, details TEXT, 
                dict_name TEXT, source_id TEXT
            )
        ''')
        # 漢字表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dictionary_kanji (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kanji TEXT, reading TEXT, details TEXT, 
                dict_name TEXT, source_id TEXT
            )
        ''')
        # 頻率表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dictionary_frequency (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT, rank INTEGER, 
                dict_name TEXT, source_id TEXT
            )
        ''')
        # 任務進度追蹤 (加入 full_path, parent_zip_id)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mana_tasks (
                source_id TEXT PRIMARY KEY,
                dict_name TEXT,
                full_path TEXT,
                parent_zip_id TEXT,
                status TEXT,
                progress REAL DEFAULT 0,
                entry_count INTEGER DEFAULT 0,
                preview_json TEXT,
                error_log TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS global_state (
                id INTEGER PRIMARY KEY DEFAULT 1,
                total_roots INTEGER DEFAULT 0,
                current_root_index INTEGER DEFAULT 0,
                current_root_name TEXT DEFAULT '',
                current_nested_path TEXT DEFAULT '',
                current_binding_count INTEGER DEFAULT 0,
                is_running BOOLEAN DEFAULT 0,
                total_expected_dictionaries INTEGER DEFAULT 255
            )
        ''')
        cursor.execute("INSERT OR IGNORE INTO global_state (id, is_running) VALUES (1, 0)")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_term_word ON dictionary_terms(word)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kanji_char ON dictionary_kanji(kanji)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_freq_word ON dictionary_frequency(word)")
        conn.commit()
        conn.close()

    def bind_tome(self, dict_path, dict_name, source_id, update_callback, conn=None):
        import zipfile
        import shutil
        import tempfile
        
        is_temp = False
        actual_path = dict_path
        
        if os.path.isfile(dict_path) and dict_path.endswith('.zip'):
            is_temp = True
            actual_path = tempfile.mkdtemp()
            with zipfile.ZipFile(dict_path, 'r') as zip_ref:
                zip_ref.extractall(actual_path)
            # 有時候 zip 裡面還有一層資料夾
            inner_files = os.listdir(actual_path)
            if len(inner_files) == 1 and os.path.isdir(os.path.join(actual_path, inner_files[0])):
                actual_path = os.path.join(actual_path, inner_files[0])

        if conn is None:
            conn = sqlite3.connect(self.db_path, timeout=60)
            should_close = True
        else:
            should_close = False
        cursor = conn.cursor()
        
        files = os.listdir(actual_path)
        term_banks = [f for f in files if f.startswith("term_bank")]
        kanji_banks = [f for f in files if f.startswith("kanji_bank")]
        freq_banks = [f for f in files if f.startswith("frequency_bank")]
        
        # 清理舊有的靈魂碎片
        cursor.execute("DELETE FROM dictionary_terms WHERE source_id = ?", (source_id,))
        cursor.execute("DELETE FROM dictionary_kanji WHERE source_id = ?", (source_id,))
        cursor.execute("DELETE FROM dictionary_frequency WHERE source_id = ?", (source_id,))
        
        total_entries = 0
        preview_data = []

        # 處理詞條 (Terms) - 改為儲存完整 JSON
        for tb in term_banks:
            with open(os.path.join(dict_path, tb), 'r', encoding='utf-8') as f:
                data = json.load(f)
                batch = []
                for entry in data:
                    word, reading, def_raw = entry[0], entry[1], entry[5]
                    # ★ 將不規則的 definition 結構存成 JSON 字串
                    details_json = json.dumps({"meaning": def_raw}, ensure_ascii=False)
                    batch.append((word, reading, details_json, dict_name, source_id))
                    
                    if len(preview_data) < 5: 
                        preview_str = str(def_raw)[:50] if not isinstance(def_raw, str) else def_raw[:50]
                        preview_data.append({"type":"term", "word":word, "def":preview_str})
                        
                    if len(batch) >= 1000:
                        cursor.executemany("INSERT INTO dictionary_terms (word, reading, details, dict_name, source_id) VALUES (?,?,?,?,?)", batch)
                        batch = []
                        total_entries += 1000
                        update_callback(total_entries)
                if batch: 
                    cursor.executemany("INSERT INTO dictionary_terms (word, reading, details, dict_name, source_id) VALUES (?,?,?,?,?)", batch)
                    total_entries += len(batch)

        # 處理漢字 (Kanji)
        for kb in kanji_banks:
            with open(os.path.join(dict_path, kb), 'r', encoding='utf-8') as f:
                data = json.load(f)
                batch = []
                for entry in data:
                    kanji, reading, meaning = entry[0], entry[1], entry[4]
                    details_json = json.dumps({"meaning": meaning}, ensure_ascii=False)
                    batch.append((kanji, str(reading), details_json, dict_name, source_id))
                    
                    if len(preview_data) < 10: preview_data.append({"type":"kanji", "word":kanji, "def": str(meaning)[:50]})
                    if len(batch) >= 1000:
                        cursor.executemany("INSERT INTO dictionary_kanji (kanji, reading, details, dict_name, source_id) VALUES (?,?,?,?,?)", batch)
                        total_entries += 1000
                        update_callback(total_entries)
                        batch = []
                if batch: 
                    cursor.executemany("INSERT INTO dictionary_kanji (kanji, reading, details, dict_name, source_id) VALUES (?,?,?,?,?)", batch)
                    total_entries += len(batch)
                    update_callback(total_entries)

        # 處理頻率 (Frequency)
        for fb in freq_banks:
            with open(os.path.join(dict_path, fb), 'r', encoding='utf-8') as f:
                data = json.load(f)
                batch = []
                for entry in data:
                    word, rank = entry[0], entry[1]
                    batch.append((word, rank, dict_name, source_id))
                    if len(batch) >= 1000:
                        cursor.executemany("INSERT INTO dictionary_frequency (word, rank, dict_name, source_id) VALUES (?,?,?,?)", batch)
                        total_entries += 1000
                        update_callback(total_entries)
                        batch = []
                if batch: 
                    cursor.executemany("INSERT INTO dictionary_frequency (word, rank, dict_name, source_id) VALUES (?,?,?,?)", batch)
                    total_entries += len(batch)
                    update_callback(total_entries)

        # 處理 Meta Banks
        meta_banks = [f for f in files if f.startswith("term_meta_bank") or f.startswith("kanji_meta_bank")]
        for mb in meta_banks:
            try:
                with open(os.path.join(dict_path, mb), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    total_entries += len(data)
                    update_callback(total_entries)
            except: pass

        # 處理未遵循 Yomitan 結構的原始 JSON 檔 (例如 Scriptin 原始檔)
        if not any([term_banks, kanji_banks, freq_banks, meta_banks]):
            for f_name in files:
                if f_name.endswith('.json') and f_name != 'index.json':
                    try:
                        with open(os.path.join(actual_path, f_name), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, dict):
                                # 1. 處理 Scriptin JMDict 格式
                                if "words" in data:
                                    batch = []
                                    for item in data["words"]:
                                        word = item["kanji"][0]["text"] if item["kanji"] else item["kana"][0]["text"]
                                        reading = item["kana"][0]["text"] if item["kana"] else ""
                                        details = json.dumps({"sense": item["sense"]}, ensure_ascii=False)
                                        batch.append((word, reading, details, dict_name, source_id))
                                        if len(preview_data) < 5:
                                            preview_data.append({"type":"term", "word":word, "def": str(item["sense"])[:50]})
                                        if len(batch) >= 1000:
                                            cursor.executemany("INSERT INTO dictionary_terms (word, reading, details, dict_name, source_id) VALUES (?,?,?,?,?)", batch)
                                            total_entries += len(batch)
                                            update_callback(total_entries)
                                            batch = []
                                    if batch:
                                        cursor.executemany("INSERT INTO dictionary_terms (word, reading, details, dict_name, source_id) VALUES (?,?,?,?,?)", batch)
                                        total_entries += len(batch)
                                        update_callback(total_entries)
                                
                                # 2. 處理 Scriptin Kanjidic2 格式
                                elif "characters" in data:
                                    batch = []
                                    for item in data["characters"]:
                                        kanji = item["literal"]
                                        reading = ""
                                        if "readingMeaning" in item and "groups" in item["readingMeaning"]:
                                            readings = item["readingMeaning"]["groups"][0].get("readings", [])
                                            reading = ",".join([r["value"] for r in readings if r["type"] in ["ja_on", "ja_kun"]])
                                        details = json.dumps(item, ensure_ascii=False)
                                        batch.append((kanji, reading, details, dict_name, source_id))
                                        if len(preview_data) < 5:
                                            preview_data.append({"type":"kanji", "word":kanji, "def": str(item.get("readingMeaning", ""))[:50]})
                                        if len(batch) >= 1000:
                                            cursor.executemany("INSERT INTO dictionary_kanji (kanji, reading, details, dict_name, source_id) VALUES (?,?,?,?,?)", batch)
                                            total_entries += len(batch)
                                            update_callback(total_entries)
                                            batch = []
                                    if batch:
                                        cursor.executemany("INSERT INTO dictionary_kanji (kanji, reading, details, dict_name, source_id) VALUES (?,?,?,?,?)", batch)
                                        total_entries += len(batch)
                                        update_callback(total_entries)
                    except Exception as e:
                        print(f"Failed to parse raw JSON {f_name}: {e}")

        if should_close:
            conn.commit()
            conn.close()
        return total_entries, preview_data

class LibraryMaster:
    """管理整個魔導圖書館的掃描與調度。"""
    def __init__(self):
        self.binder = SoulBinder(DB_PATH)
        # Enable WAL mode for the main process
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.close()
        # 初始化時清空所有未完成的暫存解壓縮檔
        if os.path.exists(TEMP_EXTRACT_DIR):
            shutil.rmtree(TEMP_EXTRACT_DIR)

    def scan_for_tomes(self):
        """掃描 assets 資料夾下的所有 ZIP。"""
        zips = []
        for root, dirs, files in os.walk(ASSETS_DIR):
            if TEMP_EXTRACT_DIR in root: continue
            for f in files:
                if f.endswith(".zip"):
                    zips.append(os.path.join(root, f))
        return zips

    def decipher_and_bind(self, zip_path, parent_id=None):
        # ★ 使用相對路徑作為唯一 ID，避免同名檔案衝突
        source_id = os.path.relpath(zip_path, ASSETS_DIR).replace('\\', '/')
        dict_name = os.path.basename(zip_path).replace(".zip", "")
        
        conn = sqlite3.connect(DB_PATH, timeout=60)
        
        # 1. 初始化任務狀態
        conn.execute("""
            INSERT OR REPLACE INTO mana_tasks 
            (source_id, dict_name, full_path, parent_zip_id, status) 
            VALUES (?, ?, ?, ?, ?)
        """, (source_id, dict_name, zip_path, parent_id, TomeStatus.QUEUED))
        conn.commit()

        # 為這一個 ZIP 建立專屬的暫存資料夾
        # 將斜線替換為底線，避免建立不必要的子目錄
        extract_path = os.path.join(TEMP_EXTRACT_DIR, source_id.replace('/', '_').replace(':', '_'))

        try:
            # 2. 解碼 (Unzip) - ★ 記憶體/磁碟安全模式：只解壓縮特定檔案，遇壓縮檔記錄後稍後遞迴
            conn.execute("UPDATE mana_tasks SET status = ? WHERE source_id = ?", (TomeStatus.DECIPHERING, source_id))
            conn.commit()
            
            self.update_global_state(current_nested_path=source_id)

            
            if os.path.exists(extract_path): shutil.rmtree(extract_path)
            os.makedirs(extract_path, exist_ok=True)
            
            nested_zips = []
            
            zip_extraction_errors = []
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    ext = os.path.splitext(file_info.filename)[1].lower()
                    
                    try:
                        # 遇到 ZIP，解壓縮出來放到暫存區準備遞迴處理
                        if ext == '.zip':
                            zip_ref.extract(file_info, extract_path)
                            nested_zips.append(os.path.join(extract_path, file_info.filename))
                        # ★ 只解壓縮文字檔與索引，忽略龐大的影音檔 (jpg, png, mp3, mp4)
                        elif ext in ALLOWED_EXTENSIONS or file_info.filename.endswith('index.json'):
                            zip_ref.extract(file_info, extract_path)
                    except zipfile.BadZipFile as ze:
                        # 忽略 CRC-32 等單一檔案損壞錯誤，嘗試使用系統 unzip 強制解壓縮
                        print(f"Warning: Python zipfile failed for {file_info.filename} ({ze}), attempting system unzip...")
                        try:
                            import subprocess
                            subprocess.run(['unzip', '-o', zip_path, file_info.filename, '-d', extract_path], 
                                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            print(f"Successfully recovered {file_info.filename} using unzip!")
                        except Exception as inner_e:
                            error_msg = f"Archive Corrupted: {file_info.filename}"
                            print(f"Failed to recover {file_info.filename} even with unzip.")
                            zip_extraction_errors.append(error_msg)
                    except Exception as e:
                        zip_extraction_errors.append(str(e))

            # 3. 綁定靈魂 (Import)
            conn.execute("UPDATE mana_tasks SET status = ? WHERE source_id = ?", (TomeStatus.BINDING, source_id))
            conn.commit()
            
            def update_progress(count):
                conn.execute("UPDATE mana_tasks SET entry_count = ? WHERE source_id = ?", (count, source_id))
                conn.commit()
                self.update_global_state(current_binding_count=count)

            dict_dirs = set()
            for r, d, f in os.walk(extract_path):
                # 完全忽略 macOS 的隱藏資源檔資料夾與 VSCode 資料夾
                if "__MACOSX" in r or ".vscode" in r:
                    continue
                if "index.json" in f:
                    dict_dirs.add(r)
                elif any(file.endswith('.json') for file in f):
                    dict_dirs.add(r)
            dict_dirs = list(dict_dirs)
            
            total_entries_for_this_zip = 0
            
            if dict_dirs:
                for d_dir in dict_dirs:
                    rel_path = os.path.relpath(d_dir, extract_path)
                    sub_source_id = f"{source_id}:{rel_path}" if rel_path != "." else source_id
                    sub_dict_name = f"{dict_name} ({rel_path})" if rel_path != "." else dict_name
                    
                    if sub_source_id != source_id:
                        conn.execute("""
                            INSERT OR REPLACE INTO mana_tasks 
                            (source_id, dict_name, full_path, parent_zip_id, status) 
                            VALUES (?, ?, ?, ?, ?)
                        """, (sub_source_id, sub_dict_name, d_dir, source_id, TomeStatus.BINDING))
                        conn.commit()
                    
                    try:
                        count, preview = self.binder.bind_tome(d_dir, sub_dict_name, sub_source_id, update_progress, conn=conn)
                        if sub_source_id != source_id:
                            # 若子資料夾沒有任何有效詞條，標記為 container 以在前端隱藏
                            sub_status = TomeStatus.SUCCESS if count > 0 else "container"
                            conn.execute("UPDATE mana_tasks SET status = ?, entry_count = ?, preview_json = ? WHERE source_id = ?", 
                                         (sub_status, count, json.dumps(preview), sub_source_id))
                            conn.commit()
                        total_entries_for_this_zip += count
                    except Exception as sub_e:
                        if sub_source_id != source_id:
                            conn.execute("UPDATE mana_tasks SET status = ?, error_log = ? WHERE source_id = ?", 
                                         (TomeStatus.FAILED, str(sub_e), sub_source_id))
                            conn.commit()

            # 此主壓縮檔綁定成功
            # 如果這個 ZIP 完全沒有字典資料或者詞條數為 0，我們將其標記為 container
            final_status = TomeStatus.SUCCESS
            error_log = None
            if not dict_dirs or total_entries_for_this_zip == 0:
                if zip_extraction_errors:
                    final_status = TomeStatus.FAILED
                    error_log = "; ".join(zip_extraction_errors)
                else:
                    final_status = "container"
                
            conn.execute("UPDATE mana_tasks SET status = ?, entry_count = ?, error_log = ? WHERE source_id = ?", 
                         (final_status, total_entries_for_this_zip, error_log, source_id))
            conn.commit()

            # 4. 處理嵌套的 ZIP (遞迴處理)
            for nz in nested_zips:
                self.decipher_and_bind(nz, parent_id=source_id)

        except Exception as e:
            conn.execute("UPDATE mana_tasks SET status = ?, error_log = ? WHERE source_id = ?", (TomeStatus.FAILED, str(e), source_id))
            conn.commit()
            print(f"FAILED: {dict_name} - {e}")
        finally:
            conn.close()
            # 5. ★ 最重要的一步：處理完一個 ZIP 後，立刻刪除這個 ZIP 的暫存資料夾
            # 防止磁碟爆炸！一筆一筆來，絕不囤積。
            if os.path.exists(extract_path):
                shutil.rmtree(extract_path, ignore_errors=True)

    def update_global_state(self, is_running=None, total_roots=None, current_root_index=None, current_root_name=None, current_nested_path=None, current_binding_count=None):
        # 使用獨立的 status.db 避免鎖死
        conn = sqlite3.connect(STATUS_DB_PATH, timeout=5)
        updates = []
        params = []
        if is_running is not None:
            updates.append("is_running=?")
            params.append(1 if is_running else 0)
        if total_roots is not None:
            updates.append("total_roots=?")
            params.append(total_roots)
        if current_root_index is not None:
            updates.append("current_root_index=?")
            params.append(current_root_index)
        if current_root_name is not None:
            updates.append("current_root_name=?")
            params.append(current_root_name)
        if current_nested_path is not None:
            updates.append("current_nested_path=?")
            params.append(current_nested_path)
        if current_binding_count is not None:
            updates.append("current_binding_count=?")
            params.append(current_binding_count)
            
        if updates:
            params.append(1) # for id = 1
            query = f"UPDATE global_state SET {', '.join(updates)} WHERE id = ?"
            conn.execute(query, tuple(params))
            conn.commit()
        conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=str, help="Path to specific zip file to process")
    args = parser.parse_args()

    master = LibraryMaster()
    
    if args.zip:
        print(f"Targeted binding for: {args.zip}")
        if os.path.exists(args.zip):
            master.update_global_state(is_running=True, total_roots=1, current_root_index=1, current_root_name=os.path.basename(args.zip), current_nested_path="", current_binding_count=0)
            master.decipher_and_bind(args.zip)
            master.update_global_state(is_running=False)
        else:
            print(f"Error: {args.zip} not found.")
    else:
        tomes = master.scan_for_tomes()
        print(f"Found {len(tomes)} magic tomes. Starting sequential binding...")
        master.update_global_state(is_running=True, total_roots=len(tomes), current_root_index=0, current_root_name="", current_nested_path="", current_binding_count=0)
        
        # 預先把所有的母壓縮檔寫入待處理清單，讓前端一開始就能顯示完整的 35 個大項目
        conn = sqlite3.connect(DB_PATH)
        for tome in tomes:
            source_id = os.path.relpath(tome, ASSETS_DIR).replace('\\', '/')
            dict_name = os.path.basename(tome).replace(".zip", "")
            conn.execute("""
                INSERT OR IGNORE INTO mana_tasks 
                (source_id, dict_name, full_path, status) 
                VALUES (?, ?, ?, 'queued')
            """, (source_id, dict_name, tome))
        conn.commit()
        conn.close()
        
        for idx, tome in enumerate(tomes):
            master.update_global_state(current_root_index=idx+1, current_root_name=os.path.basename(tome), current_nested_path="", current_binding_count=0)
            master.decipher_and_bind(tome)
            
        master.update_global_state(is_running=False)
