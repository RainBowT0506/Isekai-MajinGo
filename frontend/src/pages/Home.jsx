import { useState, useContext, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AppContext } from '../App';
import SubtitleCard from '../components/SubtitleCard';
import WordDetailPanel from '../components/WordDetailPanel';
import { MOCK_DATA } from '../mockData';

function Home() {
  const { ignoredWords, savedWords } = useContext(AppContext);
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [subs, setSubs] = useState([]);
  const [videoId, setVideoId] = useState('');
  const [selectedWord, setSelectedWord] = useState(null);

  useEffect(() => {
    const cachedData = localStorage.getItem('isekai_subs_data');
    if (cachedData) {
      try {
        const parsed = JSON.parse(cachedData);
        setSubs(parsed);
        setVideoId(localStorage.getItem('isekai_subs_vid') || 'Cached Video');
      } catch (e) {}
    } else {
      setSubs(MOCK_DATA);
      setVideoId('Target: Mock Data (無職轉生)');
    }
  }, []);

  const handleExtract = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setError('');
    setSubs([]);

    try {
      const res = await fetch('/api/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim() })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to fetch subtitles');

      setSubs(data.data);
      
      let dummyId = 'Video';
      try {
        const match = url.match(/(?:v=|\/v\/|embed\/|youtu\.be\/)([^&\n?#]+)/);
        if (match) dummyId = match[1];
        else if (url.length === 11) dummyId = url;
      } catch (e) {}

      const vidText = `Target: ${dummyId}`;
      setVideoId(vidText);
      localStorage.setItem('isekai_subs_data', JSON.stringify(data.data));
      localStorage.setItem('isekai_subs_vid', vidText);
    } catch (err) {
      setError(`系統錯誤: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <header className="header" style={{ position: 'relative' }}>
        <div style={{ position: 'absolute', right: 0, top: 0, display: 'flex', gap: '10px' }}>
          <Link to="/cms" className="magic-btn" style={{ textDecoration: 'none', display: 'inline-block', padding: '0.5rem 1rem', fontSize: '0.9rem', background: 'rgba(168, 85, 247, 0.2)' }}>⚙️ 管理中心</Link>
          <Link to="/vocabulary" className="magic-btn" style={{ textDecoration: 'none', display: 'inline-block', padding: '0.5rem 1rem', fontSize: '0.9rem' }}>📖 單字庫</Link>
        </div>
        <h1 className="glow-text">✨ Isekai MajinGo</h1>
        <p className="subtitle">真實在語境中轉生，解析 YouTube 魔法詠唱</p>
      </header>

      <div className="input-section glass-panel">
        <input 
          type="text" 
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="輸入 YouTube 或魔法水晶連結..." 
        />
        <button onClick={handleExtract} disabled={loading} className="magic-btn">
          詠唱解析
        </button>
      </div>

      {loading && (
        <div id="loading">
          <div className="spinner"></div>
          <p>正在從異世界中提取文字...</p>
        </div>
      )}

      {error && <div className="error">{error}</div>}

      {subs.length > 0 && !loading && (
        <div className="results-layout" id="results-container">
          <div className="stats-panel glass-panel">
            <span id="video-id-display">{videoId}</span>
            <span className="badge" id="lines-count-display">{subs.length} 句詠唱</span>
          </div>
          <div className="subs-container" id="subs-list">
            {subs.map((sub, idx) => (
              <SubtitleCard 
                key={idx} 
                sub={sub} 
                index={idx} 
                onDetailClick={(word) => setSelectedWord(word)}
              />
            ))}
          </div>
        </div>
      )}
      
      <WordDetailPanel 
        word={selectedWord} 
        onClose={() => setSelectedWord(null)} 
      />
    </div>
  );
}

export default Home;
