import { useContext } from 'react';
import { AppContext } from '../App';

function SelectionMenu({ selectionData, onClose }) {
  const { ignoredWords, savedWords, fetchVocabulary, showToast } = useContext(AppContext);

  if (!selectionData) return null;

  const { text, context, timestamp, rect, range } = selectionData;

  const handleIgnore = async () => {
    if (ignoredWords.includes(text)) {
      showToast('這個單字已經被忽略過囉！');
      onClose();
      return;
    }

    onClose();
    
    try {
      await fetch('/api/vocabulary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ word: text, context, timestamp, status: 'ignored' })
      });
      fetchVocabulary();
    } catch (err) {
      console.error('Failed to save ignored word', err);
    }
  };

  const handleSave = async () => {
    if (savedWords.includes(text)) {
      showToast('這個單字已經儲存過囉！');
      onClose();
      return;
    }

    onClose();
    try {
      const res = await fetch('/api/vocabulary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ word: text, context, timestamp, status: 'saved' })
      });
      if (!res.ok) throw new Error('儲存失敗');
      showToast('單字已儲存 ✨');
      fetchVocabulary();
    } catch (err) {
      console.error('Failed to save word', err);
    }
  };

  return (
    <div 
      className="floating-menu glass-panel"
      style={{
        top: window.scrollY + rect.top,
        left: rect.left + rect.width / 2,
        position: 'absolute'
      }}
    >
      <button onClick={handleSave} className="menu-btn save-btn">儲存</button>
      <button onClick={handleIgnore} className="menu-btn ignore-btn">忽略</button>
    </div>
  );
}

export default SelectionMenu;
