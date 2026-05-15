/**
 * TokenizerService - 負責日文斷詞與資料增強
 * 整合 Kuromoji (斷詞) 與後端 API (字典查詢)
 */

class TokenizerService {
  constructor() {
    this.tokenizer = null;
    this.initPromise = null;
    this.cache = new Map();
  }

  // 初始化 Kuromoji (使用 CDN 載入字典以簡化部署)
  async init() {
    if (this.initPromise) return this.initPromise;

    this.initPromise = new Promise((resolve, reject) => {
      // 確保環境中有 kuromoji (可透過 npm 或 CDN 載入)
      if (typeof window.kuromoji === 'undefined') {
        const script = document.createElement('script');
        script.src = "https://cdn.jsdelivr.net/npm/kuromoji@0.1.2/build/kuromoji.js";
        script.onload = () => this._build(resolve, reject);
        document.head.appendChild(script);
      } else {
        this._build(resolve, reject);
      }
    });

    return this.initPromise;
  }

  _build(resolve, reject) {
    window.kuromoji.builder({ 
      dicPath: "https://cdn.jsdelivr.net/npm/kuromoji@0.1.2/dict/" 
    }).build((err, _tokenizer) => {
      if (err) {
        console.error("Kuromoji initialization failed:", err);
        reject(err);
      }
      this.tokenizer = _tokenizer;
      resolve(_tokenizer);
    });
  }

  /**
   * 將一段日文切分為 Token 序列
   */
  async tokenize(text) {
    if (this.cache.has(text)) return this.cache.get(text);

    await this.init();
    const rawTokens = this.tokenizer.tokenize(text);

    // 映射為應用程式需要的格式
    const enhancedTokens = rawTokens.map((t, index) => ({
      id: `token-${index}`,
      surface: t.surface_form,
      base: t.basic_form === "*" ? t.surface_form : t.basic_form,
      reading: t.reading || "",
      pos: t.pos,
      start: t.word_position - 1,
      end: t.word_position - 1 + t.surface_form.length
    }));

    this.cache.set(text, enhancedTokens);
    return enhancedTokens;
  }

  /**
   * 向後端查詢單字的羅馬拼音與意思
   */
  async fetchDetails(word) {
    try {
      const resp = await fetch(`/api/dictionary/${encodeURIComponent(word)}`);
      const result = await resp.json();
      if (result.status === 'success') {
        return result.data;
      }
    } catch (e) {
      console.error("Failed to fetch word details", e);
    }
    return null;
  }
}

export const tokenizerService = new TokenizerService();
