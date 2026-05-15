import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

function Vocabulary() {
  const [activeTab, setActiveTab] = useState('saved');
  const [vocabData, setVocabData] = useState({ saved: [], ignored: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newWord, setNewWord] = useState('');

  const fetchVocab = async () => {
    setLoading(true);
    setError('');
    try {
      const resp = await fetch('/api/vocabulary');
      const result = await resp.json();
      
      if (result.status === 'success') {
        setVocabData({
          saved: result.data.filter(v => v.status === 'saved'),
          ignored: result.data.filter(v => v.status === 'ignored')
        });
      } else {
        throw new Error(result.message || '載入失敗');
      }
    } catch (e) {
      setError(`錯誤: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVocab();
  }, []);

  const formatTime = (seconds) => {
    if (seconds === undefined || seconds === null) return '';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString) => {
    const d = new Date(dateString);
    return `${d.getFullYear()}/${(d.getMonth() + 1).toString().padStart(2, '0')}/${d.getDate().toString().padStart(2, '0')} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    // 移除 confirm 以方便測試與操作
    try {
      const resp = await fetch(`/api/vocabulary/${id}`, { method: 'DELETE' });
      const result = await resp.json();
      if (result.status === 'success') {
        fetchVocab();
      }
    } catch (err) {
      console.error("Delete failed", err);
      alert("刪除失敗");
    }
  };

  const handleAddWord = async (e) => {
    e.preventDefault();
    if (!newWord.trim()) return;

    try {
      const resp = await fetch('/api/vocabulary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          word: newWord.trim(), 
          status: 'saved',
          context: '手動新增'
        })
      });
      const result = await resp.json();
      if (result.status === 'success') {
        setNewWord('');
        fetchVocab();
      }
    } catch (err) {
      console.error("Add failed", err);
      alert("新增失敗");
    }
  };

  const renderCard = (item, idx) => {
    let highlightedContext = item.context;
    if (item.context) {
      // Highlight the word
      const parts = item.context.split(item.word);
      highlightedContext = parts.reduce((acc, part, i) => {
        if (i === 0) return [part];
        return [...acc, <span key={i} style={{ color: 'var(--primary-color)', fontWeight: 'bold', background: 'rgba(139, 92, 246, 0.2)', padding: '0 2px', borderRadius: '4px' }}>{item.word}</span>, part];
      }, []);
    }

    return (
      <div key={item.id} className="vocab-card glass-panel" style={{ animationDelay: `${Math.min(idx * 0.05, 0.5)}s`, position: 'relative' }}>
        <button 
          className="delete-btn" 
          onClick={(e) => handleDelete(e, item.id)}
          style={{
            position: 'absolute',
            top: '10px',
            right: '10px',
            background: 'rgba(239, 68, 68, 0.1)',
            border: 'none',
            color: '#ef4444',
            borderRadius: '50%',
            width: '24px',
            height: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            fontSize: '14px',
            transition: 'all 0.2s',
            zIndex: 10
          }}
          title="刪除"
        >
          ✕
        </button>
        <div className="vocab-word-header">
          <div className="vocab-word">{item.word}</div>
          <div className="vocab-romaji">{item.romaji}</div>
        </div>
        <div className="vocab-meaning">{item.meaning}</div>
        {item.context && <div className="vocab-context">{highlightedContext}</div>}
        <div className="vocab-meta">
          <span>{item.timestamp > 0 ? `🎬 ${formatTime(item.timestamp)}` : ''}</span>
          <span>📅 {formatDate(item.created_at)}</span>
        </div>
      </div>
    );
  };

  return (
    <div className="container" style={{ maxWidth: '1000px' }}>
      <header className="header">
        <h1 className="glow-text">📖 魔法單字庫</h1>
        <p className="subtitle">檢視你收集與忽略的詠唱詞彙</p>
      </header>

      <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'center' }}>
        <form onSubmit={handleAddWord} className="glass-panel" style={{ display: 'flex', gap: '0.5rem', padding: '0.75rem 1.25rem', borderRadius: '12px' }}>
          <input 
            type="text" 
            placeholder="新增手動單字..." 
            value={newWord}
            onChange={(e) => setNewWord(e.target.value)}
            style={{ 
              background: 'transparent', 
              border: 'none', 
              color: 'white', 
              outline: 'none',
              fontSize: '1rem',
              width: '200px'
            }}
          />
          <button type="submit" className="action-btn" style={{ padding: '0.4rem 1rem', borderRadius: '8px' }}>
            ＋ 新增
          </button>
        </form>
      </div>

      <div className="tabs" style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', justifyContent: 'center' }}>
        <button 
          className={`tab-btn ${activeTab === 'saved' ? 'active' : ''}`} 
          onClick={() => setActiveTab('saved')}
        >
          ✨ 儲存的單字 ({vocabData.saved.length})
        </button>
        <button 
          className={`tab-btn ${activeTab === 'ignored' ? 'active' : ''}`} 
          onClick={() => setActiveTab('ignored')}
        >
          ❌ 忽略的單字 ({vocabData.ignored.length})
        </button>
      </div>

      <div className="results-layout" id="vocab-container">
        {loading && (
          <div id="loading">
            <div className="spinner"></div>
            <p>正在載入記憶體...</p>
          </div>
        )}
        
        {error && <div className="error">{error}</div>}

        {!loading && !error && (
          <div className="vocab-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.25rem' }}>
            {vocabData[activeTab].map((item, idx) => renderCard(item, idx))}
            
            {vocabData[activeTab].length === 0 && (
              <div style={{ color: 'var(--text-muted)', textAlign: 'center', gridColumn: '1 / -1', padding: '3rem', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px dashed rgba(255,255,255,0.1)' }}>
                {activeTab === 'saved' ? '尚無儲存的單字，快去解析影片收集吧！✨' : '尚無忽略的單字。'}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="nav-links" style={{ textAlign: 'center', marginTop: '2.5rem' }}>
        <Link to="/" className="back-link" style={{ color: 'var(--primary-color)', textDecoration: 'none', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
          ← 返回詠唱解析
        </Link>
      </div>
    </div>
  );
}

export default Vocabulary;
