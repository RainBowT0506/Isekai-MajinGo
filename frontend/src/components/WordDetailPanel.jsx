import { useEffect, useState } from 'react';

function WordDetailPanel({ word, onClose }) {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!word) return;
    
    const fetchFullDetails = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/dictionary/${encodeURIComponent(word)}`);
        const data = await res.json();
        if (data.status === 'success') {
          setDetails(data.data);
        }
      } catch (err) {
        console.error('Failed to fetch full details', err);
      } finally {
        setLoading(false);
      }
    };

    fetchFullDetails();
  }, [word]);

  if (!word) return null;

  return (
    <div className={`detail-panel glass-panel ${word ? 'open' : ''}`}>
      <div className="panel-header">
        <button className="close-btn" onClick={onClose}>×</button>
        <h2 className="panel-title">單字詳情</h2>
      </div>
      
      {loading ? (
        <div className="panel-loading">召喚知識中...</div>
      ) : details ? (
        <div className="panel-content">
          <div className="word-hero">
            <h1 className="word-text">{details.word}</h1>
            <div className="word-meta">
              <span className="word-romaji">{details.romaji}</span>
            </div>
          </div>
          
          <div className="detail-section">
            <h3>詞意解析</h3>
            <p className="meaning-text">{details.meaning_zh || details.meaning_en || '本地辭典查無解釋'}</p>
          </div>

          {details.extra_definitions && details.extra_definitions.length > 0 && (
            <div className="detail-section">
              <h3>本地辭典群庫 (聚合查詢)</h3>
              <div className="extra-definitions-list">
                {details.extra_definitions.map((ext, idx) => (
                  <div key={idx} className="extra-def-item">
                    <span className="dict-name">【{ext.dict}】</span>
                    <p className="ext-explanation">{ext.explanation}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {details.explanation && (
            <div className="detail-section">
              <h3>導師筆記 (AI)</h3>
              <p className="explanation-text">{details.explanation}</p>
            </div>
          )}
          
          <div className="detail-section">
             <h3>魔法屬性 (詞性)</h3>
             <span className="pos-tag">{details.pos || '未知'}</span>
          </div>

          <div className="detail-section">
            <h3>異世界語境 (例句)</h3>
            <div className="example-box">
              <p>「這是一個來自異世界的例句。」</p>
              <p className="example-romaji">Kore wa isekai kara no reibun desu.</p>
            </div>
          </div>
          
          <div className="panel-footer">
             <p className="footer-note">※ 來源：{details.source || '異世界魔法庫'}</p>
          </div>
        </div>
      ) : (
        <div className="panel-error">找不到單字資訊</div>
      )}
    </div>
  );
}

export default WordDetailPanel;
