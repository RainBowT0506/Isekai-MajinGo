import React from 'react';

function TokenTooltip({ token, details, onAction, onDetailClick, onMouseEnter }) {
  return (
    <div className="token-tooltip" onMouseEnter={onMouseEnter}>
      <div className="tooltip-header">
        <span className="tooltip-surface">{token.surface}</span>
        <span className="tooltip-reading">[{token.reading}]</span>
      </div>
      <div className="tooltip-romaji">{details?.romaji || '...'}</div>
      <div className="tooltip-divider" />
      <div 
        className="tooltip-meaning clickable" 
        onClick={(e) => {
          e.stopPropagation();
          onDetailClick && onDetailClick(token.base);
        }}
      >
        {details?.meaning_zh || '查無結果'}
      </div>
      <div className="tooltip-actions">
        <button 
          className="tooltip-btn save-btn" 
          onClick={(e) => onAction(e, token, 'saved')}
        >
          儲存
        </button>
        <button 
          className="tooltip-btn ignore-btn" 
          onClick={(e) => onAction(e, token, 'ignored')}
        >
          忽略
        </button>
      </div>
      <div className="tooltip-pos">{token.pos}</div>
    </div>
  );
}

export default TokenTooltip;
