import sqlite3
import os

def init_dictionary():
    db_path = "dictionary.db"
    
    # 如果已經存在，先刪除以進行乾淨的初始化（僅限開發階段）
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 建立辭典表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            reading TEXT,
            meaning_zh TEXT,
            pos TEXT,
            level TEXT,
            source TEXT DEFAULT '權威辭典'
        )
    ''')
    
    # 建立索引以提升查詢速度
    cursor.execute('CREATE INDEX idx_word ON entries(word)')
    cursor.execute('CREATE INDEX idx_reading ON entries(reading)')
    
    # 示範數據：N5 - N1 核心單字
    sample_data = [
        # N5
        ("食べる", "たべる", "吃", "動詞", "N5"),
        ("行く", "いく", "去", "動詞", "N5"),
        ("学生", "がくせい", "學生", "名詞", "N5"),
        ("先生", "せんせい", "老師", "名詞", "N5"),
        ("日本", "にっぽん", "日本", "名詞", "N5"),
        
        # N4
        ("準備", "じゅんび", "準備", "名詞/動詞", "N4"),
        ("昨日", "きのう", "昨天", "名詞", "N4"),
        ("説明", "せつめい", "說明", "名詞/動詞", "N4"),
        
        # N3
        ("意識", "いしき", "意識", "名詞", "N3"),
        ("解決", "かいけつ", "解決", "名詞/動詞", "N3"),
        ("結構", "けっこう", "相當地；很好", "副詞/形容動詞", "N3"),
        
        # N2
        ("影響", "えいきょう", "影響", "名詞/動詞", "N2"),
        ("關鍵", "かんぜん", "完全", "形容動詞", "N2"),
        ("技術", "ぎじゅつ", "技術", "名詞", "N2"),
        
        # N1
        ("矛盾", "むじゅん", "矛盾", "名詞/動詞", "N1"),
        ("考慮", "こうりょ", "考慮", "名詞/動詞", "N1"),
        ("把握", "はあく", "掌握；理解", "名詞/動詞", "N1"),
        
        # 動漫常用詞
        ("魔法", "まほう", "魔法", "名詞", "Anime"),
        ("世界", "せかい", "世界", "名詞", "Core"),
        ("力", "ちから", "力量", "名詞", "Core"),
        ("反応", "はんのう", "反應", "名詞/動詞", "N2"),
    ]
    
    cursor.executemany('''
        INSERT INTO entries (word, reading, meaning_zh, pos, level)
        VALUES (?, ?, ?, ?, ?)
    ''', sample_data)
    
    conn.commit()
    conn.close()
    print(f"✅ Dictionary initialized with {len(sample_data)} entries at {db_path}")

if __name__ == "__main__":
    init_dictionary()
