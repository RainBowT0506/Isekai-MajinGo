# Isekai MajinGo 後端 API 文件

本文件記錄了 Isekai MajinGo 的後端介面 (FastAPI) 及其功能。

## 📍 基礎資訊
- **服務網址**: `http://localhost:8001`
- **前端代理**: Vite 已設定 `/api` -> `http://localhost:8001`

---

## 🛠️ API 列表

### 1. 辭典查詢 (Dictionary Lookup)
- **路徑**: `GET /api/dictionary/{word}`
- **功能**: 查詢日文或中文單字。
- **邏輯**:
    - 優先嘗試本地 SQLite (`dictionary.db`) 匹配。
    - 若本地無繁體中文結果，自動調用本地 Ollama AI (Qwen2.5) 生成高品質解析。
    - 支援「中日模式」：若輸入為純漢字，自動翻譯為日文單字。
- **回傳範例**:
  ```json
  {
    "status": "success",
    "source": "static/ai",
    "data": {
      "word": "反応",
      "romaji": "hannou",
      "meaning_zh": "反應",
      "pos": "名詞",
      "explanation": "..."
    }
  }
  ```

### 2. 影片字幕提取 (YouTube Extract)
- **路徑**: `POST /api/extract`
- **功能**: 提取 YouTube 影片的日文字幕。
- **參數**:
  ```json
  { "url": "https://www.youtube.com/watch?v=..." }
  ```

### 3. 單字庫管理 (Vocabulary Management)
- **獲取清單**: `GET /api/vocabulary`
- **儲存單字**: `POST /api/vocabulary`
  - 參數: `{ "word": "...", "status": "saved/ignored", "context": "..." }`
- **刪除單字**: `DELETE /api/vocabulary/{id}`

### 4. 辭典匯入狀態 (Import Status)
- **路徑**: `GET /api/import/status`
- **功能**: 監看本地 200+ 門辭典的匯入進度與成功/失敗狀態。
- **回傳範例**:
  ```json
  {
    "status": "success",
    "data": [
      { "dict_name": "大辭林", "status": "success", "entry_count": 250000 },
      { "dict_name": "新明解", "status": "importing", "entry_count": 0 }
    ]
  }
  ```

### 5. 斷詞解析 (Text Analysis)

---

## 🗄️ 資料庫結構
1. **`dictionary.db`**: 
   - `kanji_elements`: 漢字
   - `reading_elements`: 讀音
   - `senses`: 中英文解釋
2. **`vocab.db`**: 
   - `vocabulary`: 使用者學習記錄 (已儲存/已忽略)

---
*更新日期: 2026-05-13*
