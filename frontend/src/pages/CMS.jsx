import { useState, useEffect } from 'react';
import './CMS.css';

function CMS() {
  const [importStatus, setImportStatus] = useState([]);
  const [globalState, setGlobalState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('success'); // 'success' or 'issues'

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const resp = await fetch(`/api/library/status?t=${Date.now()}`);
      if (resp.ok) {
        const result = await resp.json();
        if (result.status === 'success') {
          setImportStatus(result.data);
        }
      }
      
      const globalResp = await fetch(`/api/library/global_state?t=${Date.now()}`);
      if (globalResp.ok) {
        const globalResult = await globalResp.json();
        if (globalResult.status === 'success') {
          setGlobalState(globalResult.data);
        }
      }
    } catch (e) {
      console.warn("CMS Polling Warning (likely DB locked):", e);
    } finally {
      setLoading(false);
    }
  };

  const retryImport = async (source_id) => {
    try {
      await fetch(`/api/library/retry/${encodeURIComponent(source_id)}`, { method: 'POST' });
      fetchStatus();
    } catch (e) {
      alert("重試失敗: " + e.message);
    }
  };

  const triggerImport = async () => {
    try {
      await fetch('/api/library/start', { method: 'POST' });
      fetchStatus();
    } catch (e) {
      alert("啟動失敗: " + e.message);
    }
  };

  const isActuallyRunning = (globalState && globalState.is_running) || 
                            importStatus.some(d => ['deciphering', 'binding'].includes(d.status));

  const stats = {
    // 只有在運行中或已經有資料時才顯示總數，否則清零
    total: isActuallyRunning
      ? (globalState?.total_expected_dictionaries || 255) 
      : importStatus.length,
    success: importStatus.filter(d => d.status === 'success' && d.count > 0).length,
    issues: importStatus.filter(d => d.status === 'failed' || d.status === 'container' || (d.status === 'success' && d.count === 0)).length,
    processing: importStatus.filter(d => ['deciphering', 'binding', 'queued'].includes(d.status)).length,
    totalEntries: importStatus.reduce((acc, curr) => acc + (curr.count || 0), 0)
  };

  const pendingCount = isActuallyRunning 
    ? (stats.total - stats.success) 
    : (stats.issues + stats.processing);

  const filteredData = importStatus.filter(d => {
    // 移除之前的 container 阻擋邏輯，讓容器可以顯示在 Pending 標籤下
    // if (d.status === 'container') return false; 
    
    if (activeTab === 'success') {
      return d.status === 'success' && d.count > 0;
    } else {
      // 顯示失敗、空值、處理中或容器類型的項目
      return d.status === 'failed' || d.count === 0 || ['deciphering', 'binding', 'queued', 'container'].includes(d.status);
    }
  });

  return (
    <div className="cms-container">
      <header className="cms-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1>魔導圖書館 <span>CMS v3.0</span></h1>
          
          <button 
            className={`magic-btn ${globalState && globalState.is_running ? 'running' : ''}`}
            onClick={triggerImport}
            disabled={globalState && globalState.is_running}
            style={{ padding: '10px 24px', fontSize: '1.1rem' }}
          >
            {globalState && globalState.is_running ? '⚡ 詠唱進行中...' : '🚀 開始全盤匯入'}
          </button>
        </div>
        <div className="cms-stats-bar">
          <div className="stat-card" style={{ borderColor: '#666', color: '#fff' }}>
            <label>{isActuallyRunning ? '總目標 (Target)' : '總計 (Total)'}</label>
            <div className="value">{isActuallyRunning ? `~${stats.total}` : stats.total}</div>
          </div>
          <div className="stat-card success">
            <label>已成功綁定</label>
            <div className="value">{stats.success}</div>
          </div>
          <div className="stat-card danger">
            <label>{isActuallyRunning ? '待處理 (Pending)' : '異常/空值'}</label>
            <div className="value">{pendingCount}</div>
          </div>
          <div className="stat-card glow">
            <label>全知詞條量</label>
            <div className="value">{(stats.totalEntries / 10000).toFixed(1)}萬</div>
          </div>
        </div>
      </header>

      {isActuallyRunning && (
        <div className="magic-core-status">
          <div className="core-header">
            <span className="core-title">🔮 靈魂綁定詠唱中...</span>
            <span className="core-progress">
              [ 第 {globalState?.current_root_index || '?'} 卷 / 共 {globalState?.total_roots || '?'} 卷大師典籍 ]
            </span>
          </div>
          
          <div className="core-bar-bg">
            <div 
              className="core-bar-fill" 
              style={{ width: `${Math.max(5, ((globalState?.current_root_index || 0) / Math.max(1, globalState?.total_roots || 35)) * 100)}%` }}
            ></div>
          </div>
          
          <div className="core-details">
            <div className="core-path">
              📜 <b>解析階層：</b> 
              {globalState?.current_root_name || '探索中...'} 
              {globalState?.current_nested_path && globalState.current_nested_path !== globalState.current_root_name && (
                <span> ➔ {globalState.current_nested_path}</span>
              )}
            </div>
            <div className="core-binding">
              ⚡ <b>靈魂注入：</b> 
              <span className="binding-count">{(globalState?.current_binding_count || 0).toLocaleString()}</span> 詞條處理中...
            </div>
          </div>
        </div>
      )}

      <nav className="cms-nav">
        <button
          className={activeTab === 'success' ? 'active' : ''}
          onClick={() => setActiveTab('success')}
        >
          ✅ 已收藏 ({stats.success})
        </button>
        <button
          className={activeTab === 'issues' ? 'active' : ''}
          onClick={() => setActiveTab('issues')}
        >
          ⚠️ 異常/待處理 ({pendingCount})
        </button>
      </nav>

      <main className="cms-content">
        {loading ? (
          <div className="loading">正在感應圖書館狀態...</div>
        ) : (
          <div className="dict-table-container">
            <table className="cms-table">
              <thead>
                <tr>
                  <th>路徑與狀態 (Path & Status)</th>
                  <th>詞條數</th>
                  <th>數據顯影 (Preview)</th>
                </tr>
              </thead>
              <tbody>
                {filteredData.map((dict, i) => (
                  <tr key={i} className={`dict-row-${dict.status}`}>
                    <td>
                      <div className="dict-path">{dict.source_id}</div>
                      <div className="dict-name">{dict.name}</div>
                      <div className="status-row">
                        {dict.status === 'success' && <span className="status-badge success">已收藏</span>}
                        {dict.status === 'failed' && <span className="status-badge failed">異常</span>}
                        {dict.status === 'queued' && <span className="status-badge pending">排隊中</span>}
                        {dict.status === 'deciphering' && <span className="status-badge pending">解碼中</span>}
                        {dict.status === 'binding' && <span className="status-badge pending">綁定中</span>}
                        {dict.status === 'container' && <span className="status-badge container">📦 外層容器</span>}
                        {(dict.status === 'failed' || (dict.status === 'success' && dict.count === 0)) && (
                          <button className="retry-btn" onClick={() => retryImport(dict.source_id)}>重試</button>
                        )}
                      </div>
                      {dict.error && <div className="error-log">{dict.error}</div>}
                    </td>
                    <td>{dict.count?.toLocaleString()}</td>
                    <td className="preview-cell">
                      {dict.preview && dict.preview.length > 0 ? (
                        <div className="mini-previews">
                          {dict.preview.slice(0, 3).map((p, j) => (
                            <span key={j} title={p.def}>{p.word}</span>
                          ))}
                        </div>
                      ) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}

export default CMS;
