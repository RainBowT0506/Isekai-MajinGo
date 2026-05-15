import { useEffect, useState, useContext } from 'react';
import { tokenizerService } from '../utils/tokenizer';
import { AppContext } from '../App';
import TokenTooltip from './TokenTooltip';

function SubtitleCard({ sub, index, onDetailClick }) {
  const [tokens, setTokens] = useState([]);
  const [activeToken, setActiveToken] = useState(null);
  const [details, setDetails] = useState({});
  const { ignoredWords, savedWords, fetchVocabulary, showToast } = useContext(AppContext);

  useEffect(() => {
    let isMounted = true;
    const processText = async () => {
      const result = await tokenizerService.tokenize(sub.text);
      if (isMounted) setTokens(result);
    };
    processText();
    return () => { isMounted = false; };
  }, [sub.text]);

  const handleMouseEnter = async (token, e) => {
    setActiveToken(token);
    // 預加載詳情
    if (!details[token.base]) {
      const info = await tokenizerService.fetchDetails(token.base);
      if (info) {
        setDetails(prev => ({ ...prev, [token.base]: info }));
      }
    }
  };

  const handleAction = async (e, token, status) => {
    e.stopPropagation(); // 防止觸發 span 的 onClick
    
    if (status === 'saved' && savedWords.includes(token.base)) {
      showToast('這個單字已經儲存過囉！');
      return;
    }
    if (status === 'ignored' && ignoredWords.includes(token.base)) {
      showToast('這個單字已經被忽略過囉！');
      return;
    }

    try {
      const res = await fetch('/api/vocabulary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          word: token.base, 
          context: sub.text, 
          timestamp: sub.start, 
          status: status 
        })
      });
      if (!res.ok) throw new Error('操作失敗');
      showToast(status === 'saved' ? '單字已儲存 ✨' : '已忽略該單字');
      fetchVocabulary();
      setActiveToken(null);
    } catch (err) {
      console.error('Failed to update vocabulary', err);
      showToast('操作失敗，請稍後再試');
    }
  };

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="sub-card" style={{ animationDelay: `${Math.min(index * 0.03, 1)}s`, position: 'relative' }}>
      <div className="time-stamp">{formatTime(sub.start)}</div>
      <div className="sub-content">
        <div className="sub-text">
          {tokens.map((token, i) => {
            const isIgnored = ignoredWords.includes(token.base) || ignoredWords.includes(token.surface);
            const isSaved = savedWords.includes(token.base) || savedWords.includes(token.surface);
            
            return (
              <span
                key={token.id}
                className={`token-span ${isSaved ? 'saved-highlight' : ''} ${isIgnored ? 'ignored-word' : ''} ${activeToken === token ? 'active-token' : ''}`}
                onMouseEnter={(e) => !isIgnored && handleMouseEnter(token, e)}
                onMouseLeave={() => setActiveToken(null)}
              >
                {token.surface}
                
                {activeToken === token && (
                  <TokenTooltip 
                    token={token}
                    details={details[token.base]}
                    onAction={handleAction}
                    onDetailClick={onDetailClick}
                    onMouseEnter={() => setActiveToken(token)}
                  />
                )}
              </span>
            );
          })}
        </div>
        {sub.romaji && <div className="sub-romaji">{sub.romaji}</div>}
      </div>
    </div>
  );
}

export default SubtitleCard;
