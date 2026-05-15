from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
from pydantic import BaseModel
from youtube_extractor import fetch_subtitles
import sqlite3
import pykakasi
from contextlib import asynccontextmanager
import os
import requests
import json
import subprocess

# --- Path Configurations ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "dictionary.db")
STATUS_DB_PATH = os.path.join(BASE_DIR, "status.db")
VOCAB_DB_PATH = os.path.join(BASE_DIR, "vocab.db")
FRONTEND_DIR = os.path.normpath(os.path.join(BASE_DIR, "../frontend/dist"))

def init_db():
    conn = sqlite3.connect(VOCAB_DB_PATH, timeout=30)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            context TEXT,
            timestamp REAL,
            status TEXT DEFAULT 'saved',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Isekai MajinGo API", lifespan=lifespan)
kks = pykakasi.kakasi()

# --- Dictionary Lookup Logic (Mana Library) ---

def get_static_definition(word: str):
    """從新的 Mana Library 架構查詢詞條。"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT word, reading, details, dict_name, source_id
            FROM dictionary_terms
            WHERE word = ? OR reading = ?
            LIMIT 10
        ''', (word, word))
        rows = cursor.fetchall()
        conn.close()
        if rows:
            results = []
            for r in rows:
                try:
                    details_dict = json.loads(r[2]) if r[2] else {}
                except:
                    details_dict = {"meaning": str(r[2])}
                
                results.append({
                    "word": r[0], "romaji": r[1], 
                    "meaning_zh": details_dict.get("meaning", ""),
                    "details": details_dict,
                    "dict": r[3], "source_id": r[4]
                })
            return results
    except: pass
    return []

def get_kanji_details(text: str):
    """拆解單字中的漢字並查詢其細節。"""
    kanjis = [char for char in text if '\u4e00' <= char <= '\u9fff']
    results = []
    if not kanjis: return results
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        cursor = conn.cursor()
        for k in kanjis:
            cursor.execute('SELECT kanji, reading, details FROM dictionary_kanji WHERE kanji = ? LIMIT 1', (k,))
            row = cursor.fetchone()
            if row:
                try:
                    details_dict = json.loads(row[2]) if row[2] else {}
                    meaning = details_dict.get("meaning", "")
                except:
                    meaning = str(row[2])
                results.append({"kanji": row[0], "reading": row[1], "meaning": meaning})
        conn.close()
    except: pass
    return results

@app.get("/api/dictionary/{word}")
async def lookup_word(word: str):
    try:
        terms = get_static_definition(word)
        kanji_info = get_kanji_details(word)
        
        if terms or kanji_info:
            main_term = terms[0] if terms else {"word": word, "romaji": "", "meaning_zh": "暫無解釋", "dict": "系統"}
            return {
                "status": "success",
                "source": "mana_library",
                "data": {
                    "word": main_term["word"],
                    "romaji": main_term["romaji"],
                    "meaning_zh": main_term["meaning_zh"],
                    "extra_definitions": terms,
                    "kanji_details": kanji_info,
                    "source": main_term["dict"]
                }
            }
        
        result = kks.convert(word)
        romaji = "".join([r['hepburn'] for r in result])
        return {"status": "success", "data": {"word": word, "romaji": romaji, "meaning_zh": "（圖書館未收藏此詞）"}}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Library Management APIs ---

@app.get("/api/library/global_state")
async def get_library_global_state():
    try:
        # 改為讀取獨立的 status.db
        conn = sqlite3.connect(STATUS_DB_PATH, timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT total_roots, current_root_index, current_root_name, current_nested_path, current_binding_count, is_running, total_expected_dictionaries FROM global_state WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "status": "success",
                "data": {
                    "total_roots": row[0],
                    "current_root_index": row[1],
                    "current_root_name": row[2],
                    "current_nested_path": row[3],
                    "current_binding_count": row[4],
                    "is_running": bool(row[5]),
                    "total_expected_dictionaries": row[6] or 255
                }
            }
        return {"status": "success", "data": {"is_running": False}}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/library/status")
async def get_library_status():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        cursor = conn.cursor()
        cursor.execute("SELECT source_id, dict_name, status, entry_count, preview_json, error_log, full_path, parent_zip_id FROM mana_tasks ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return {
            "status": "success", 
            "data": [{
                "source_id": r[0],
                "name": r[1], "status": r[2], "count": r[3], 
                "preview": json.loads(r[4] if r[4] else "[]"),
                "error": r[5],
                "full_path": r[6],
                "parent_zip_id": r[7]
            } for r in rows]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/library/start")
async def start_import():
    script_path = os.path.join(BASE_DIR, "scripts", "mana_library.py")
    subprocess.Popen(["python3", script_path], cwd=BASE_DIR)
    return {"status": "success", "message": "靈魂綁定儀式已啟動"}

def get_root_zip_path(source_id: str):
    conn = sqlite3.connect(DB_PATH, timeout=30)
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

@app.post("/api/library/retry/{source_id:path}")
async def retry_import(source_id: str):
    try:
        root_zip_path = get_root_zip_path(source_id)
        if not root_zip_path:
            return {"status": "error", "message": "找不到原始檔案路徑"}
            
        conn = sqlite3.connect(DB_PATH, timeout=30)
        # 設定目標 source_id 為排隊中
        conn.execute("UPDATE mana_tasks SET status = 'queued', error_log = NULL, entry_count = 0 WHERE source_id = ?", (source_id,))
        
        # 設定根壓縮檔為排隊中 (如果不同的話)，這樣重新解壓時狀態才會更新
        root_source_id = os.path.relpath(root_zip_path, ASSETS_DIR).replace('\\', '/')
        if root_source_id != source_id:
            conn.execute("UPDATE mana_tasks SET status = 'queued' WHERE source_id = ?", (root_source_id,))
            
        conn.commit()
        conn.close()
        
        # 啟動腳本來處理指定的根壓縮檔
        script_path = os.path.join(BASE_DIR, "scripts", "mana_library.py")
        subprocess.Popen(["python3", script_path, "--zip", root_zip_path], cwd=BASE_DIR)
        return {"status": "success", "message": "已重新加入隊列"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Subtitles & Vocabulary ---

class ExtractRequest(BaseModel):
    url: str

class VocabularyRequest(BaseModel):
    word: str
    context: str = ""
    timestamp: float = 0.0
    status: str = "saved"

@app.post("/api/extract")
async def extract_api(req: ExtractRequest):
    try:
        subs = fetch_subtitles(req.url)
        return {"status": "success", "data": subs}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/vocabulary")
async def save_vocabulary(req: VocabularyRequest):
    try:
        conn = sqlite3.connect(VOCAB_DB_PATH, timeout=30)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO vocabulary (word, context, timestamp, status) VALUES (?, ?, ?, ?)', 
                       (req.word, req.context, req.timestamp, req.status))
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"Vocabulary {req.status} successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vocabulary")
async def get_vocabulary():
    try:
        conn = sqlite3.connect(VOCAB_DB_PATH, timeout=30)
        cursor = conn.cursor()
        cursor.execute("SELECT id, word, context, timestamp, status, created_at FROM vocabulary ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return {"status": "success", "data": [{"id": r[0], "word": r[1], "context": r[2], "status": r[4]} for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/vocabulary/{vocab_id}")
async def delete_vocabulary(vocab_id: int):
    try:
        conn = sqlite3.connect(VOCAB_DB_PATH, timeout=30)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vocabulary WHERE id = ?", (vocab_id,))
        conn.commit()
        conn.close()
        return {"status": "success", "message": "Vocabulary deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Serve React App ---
if os.path.exists(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    file_path = os.path.join(FRONTEND_DIR, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
