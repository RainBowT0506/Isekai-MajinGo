import gzip
import xml.etree.ElementTree as ET
import sqlite3
import csv
import requests
import os

# --- Path Configurations ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Target the backend root (one level up from scripts/)
BACKEND_ROOT = os.path.dirname(BASE_DIR)
DB_PATH = os.path.join(BACKEND_ROOT, "dictionary.db")
JMDICT_GZ_PATH = os.path.join(BACKEND_ROOT, "JMdict.gz")
CSV_PATH = os.path.join(BACKEND_ROOT, "dictionary.csv")

def download_jmdict():
    url = "http://ftp.edrdg.org/pub/Nihongo/JMdict.gz"
    if not os.path.exists(JMDICT_GZ_PATH):
        print(f"📥 Downloading JMdict from {url}...")
        response = requests.get(url, stream=True, verify=False)
        with open(JMDICT_GZ_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    return JMDICT_GZ_PATH

def parse_and_import(gz_path):
    print(f"🚀 Parsing JMdict into {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # ... (rest of the SQL creation remains same)
    
    cursor.executescript('''
        DROP TABLE IF EXISTS entries;
        DROP TABLE IF EXISTS kanji_elements;
        DROP TABLE IF EXISTS reading_elements;
        DROP TABLE IF EXISTS senses;

        CREATE TABLE entries (
            ent_seq INTEGER PRIMARY KEY,
            pos TEXT,
            priority TEXT
        );

        CREATE TABLE kanji_elements (
            ent_seq INTEGER,
            keb TEXT
        );

        CREATE TABLE reading_elements (
            ent_seq INTEGER,
            reb TEXT
        );

        CREATE TABLE senses (
            ent_seq INTEGER,
            gloss_zh TEXT,
            gloss_en TEXT
        );
        
        CREATE INDEX idx_keb ON kanji_elements(keb);
        CREATE INDEX idx_reb ON reading_elements(reb);
    ''')
    
    count = 0
    with gzip.open(gz_path, 'rb') as f:
        context = ET.iterparse(f, events=('end',))
        
        entries_batch = []
        kanji_batch = []
        reading_batch = []
        senses_batch = []
        
        for event, elem in context:
            if elem.tag == 'entry':
                ent_seq = int(elem.find('ent_seq').text)
                
                # Kanji & Reading Elements
                kanjis = [k.text for k in elem.findall('k_ele/keb')]
                readings = [r.text for r in elem.findall('r_ele/reb')]
                priorities = [p.text for p in elem.findall('k_ele/ke_pri')] + [p.text for p in elem.findall('r_ele/re_pri')]
                
                for k in kanjis:
                    kanji_batch.append((ent_seq, k))
                for r in readings:
                    reading_batch.append((ent_seq, r))
                
                # Senses
                pos_list = []
                zh_glosses = []
                en_glosses = []
                
                for sense in elem.findall('sense'):
                    for pos in sense.findall('pos'):
                        pos_list.append(pos.text.strip('&;'))
                    
                    for gloss in sense.findall('gloss'):
                        lang = gloss.get('{http://www.w3.org/XML/1998/namespace}lang')
                        if lang in ['chi', 'zho']:
                            zh_glosses.append(gloss.text)
                        elif lang is None or lang == 'eng':
                            en_glosses.append(gloss.text)
                
                pos_str = "/".join(set(pos_list))
                pri_str = ",".join(set(priorities))
                zh_str = "；".join(zh_glosses)
                en_str = "；".join(en_glosses)
                
                entries_batch.append((ent_seq, pos_str, pri_str))
                senses_batch.append((ent_seq, zh_str, en_str))
                
                count += 1
                if count % 2000 == 0:
                    cursor.executemany('INSERT INTO entries VALUES (?, ?, ?)', entries_batch)
                    cursor.executemany('INSERT INTO kanji_elements VALUES (?, ?)', kanji_batch)
                    cursor.executemany('INSERT INTO reading_elements VALUES (?, ?)', reading_batch)
                    cursor.executemany('INSERT INTO senses VALUES (?, ?, ?)', senses_batch)
                    entries_batch, kanji_batch, reading_batch, senses_batch = [], [], [], []
                    print(f"已解析 {count} 條條目...")
                
                elem.clear()
        
        # Insert remaining
        if entries_batch:
            cursor.executemany('INSERT INTO entries VALUES (?, ?, ?)', entries_batch)
            cursor.executemany('INSERT INTO kanji_elements VALUES (?, ?)', kanji_batch)
            cursor.executemany('INSERT INTO reading_elements VALUES (?, ?)', reading_batch)
            cursor.executemany('INSERT INTO senses VALUES (?, ?, ?)', senses_batch)
            
    conn.commit()
    conn.close()
    print(f"✨ Successfully imported {count} entries into dictionary.db")

def export_to_csv():
    """
    Export a flat view for visualization/debugging.
    """
    print(f"📊 Exporting to {CSV_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.ent_seq, 
               (SELECT GROUP_CONCAT(keb, '、') FROM kanji_elements WHERE ent_seq = e.ent_seq),
               (SELECT GROUP_CONCAT(reb, '、') FROM reading_elements WHERE ent_seq = e.ent_seq),
               e.pos, s.gloss_zh, s.gloss_en, e.priority
        FROM entries e
        JOIN senses s ON e.ent_seq = s.ent_seq
    ''')
    rows = cursor.fetchall()
    
    with open(CSV_PATH, "w", newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(["ent_seq", "kanji", "reading", "pos", "meaning_zh", "meaning_en", "priority"])
        writer.writerows(rows)
    
    conn.close()
    print("✅ Exported to dictionary.csv")

if __name__ == "__main__":
    gz_file = download_jmdict()
    parse_and_import(gz_file)
    export_to_csv()

