import { useState, useEffect, createContext } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Home from './pages/Home';
import Vocabulary from './pages/Vocabulary';
import CMS from './pages/CMS';

export const AppContext = createContext();

function App() {
  const [ignoredWords, setIgnoredWords] = useState([]);
  const [savedWords, setSavedWords] = useState([]);
  const [toastMessage, setToastMessage] = useState('');

  const fetchVocabulary = async () => {
    try {
      const resp = await fetch('/api/vocabulary');
      const result = await resp.json();
      if (result.status === 'success') {
        const ignored = result.data.filter(v => v.status === 'ignored').map(v => v.word);
        const saved = result.data.filter(v => v.status === 'saved').map(v => v.word);
        setIgnoredWords([...new Set(ignored)]);
        setSavedWords([...new Set(saved)]);
      }
    } catch (e) {
      console.error("Failed to fetch vocabulary", e);
    }
  };

  const showToast = (message) => {
    setToastMessage(message);
    setTimeout(() => setToastMessage(''), 3000);
  };

  useEffect(() => {
    fetchVocabulary();
  }, []);

  return (
    <AppContext.Provider value={{ ignoredWords, savedWords, fetchVocabulary, showToast }}>
      <div className="particle-bg" id="particles"></div>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/vocabulary" element={<Vocabulary />} />
        <Route path="/cms" element={<CMS />} />
        <Route path="/vocabulary.html" element={<Navigate to="/vocabulary" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      {toastMessage && (
        <div id="toast-notification" className="toast" style={{ animation: 'toastSlideUp 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards' }}>
          {toastMessage}
        </div>
      )}
    </AppContext.Provider>
  );
}

export default App;
