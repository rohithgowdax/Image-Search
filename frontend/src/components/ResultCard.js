import React, { useState } from 'react';
import { RotateCcw, Trash2, ExternalLink } from 'lucide-react';

function ScoreBadge({ score }) {
  const pct = Math.round(score * 100);
  const cls = score >= 0.75 ? 'score-high' : score >= 0.5 ? 'score-med' : 'score-low';
  return <div className={`result-score-badge ${cls}`}>{pct}%</div>;
}

function SimBar({ score }) {
  const pct = Math.round(score * 100);
  const color = score >= 0.75 ? 'var(--green)' : score >= 0.5 ? 'var(--yellow)' : 'var(--accent)';
  return (
    <div className="sim-bar-wrap">
      <div className="sim-bar-bg">
        <div className="sim-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

export default function ResultCard({ result, onReverseSearch, onDelete, apiBase = '' }) {
  const [imgError, setImgError] = useState(false);
  const src = result.url.startsWith('http') ? result.url : `${apiBase}${result.url}`;

  return (
    <div className="result-card fade-in">
      <div className="result-img-wrap">
        {imgError ? (
          <div style={{
            position: 'absolute', inset: 0, display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            background: 'var(--bg3)', color: 'var(--text3)', fontSize: 12
          }}>
            No preview
          </div>
        ) : (
          <img
            src={src}
            alt={result.description || result.filename}
            onError={() => setImgError(true)}
            loading="lazy"
          />
        )}
        <ScoreBadge score={result.similarity_score} />
      </div>

      <div className="result-info">
        <div className="result-filename" title={result.filename}>
          {result.original_filename || result.filename}
        </div>
        {result.description && (
          <div className="result-desc" title={result.description}>{result.description}</div>
        )}
        <SimBar score={result.similarity_score} />
        <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 4 }}>
          {Math.round(result.similarity_score * 100)}% similar
          {result.width && ` · ${result.width}×${result.height}`}
        </div>
        {result.tags?.length > 0 && (
          <div className="result-tags" style={{ marginTop: 6 }}>
            {result.tags.slice(0, 4).map(t => <span key={t} className="tag">{t}</span>)}
          </div>
        )}
      </div>

      <div className="result-actions">
        {onReverseSearch && (
          <button className="btn btn-ghost" onClick={() => onReverseSearch(result)}
            title="Find similar to this">
            <RotateCcw size={12} /> Similar
          </button>
        )}
        <a
          href={src}
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-ghost"
          style={{ flex: 1, justifyContent: 'center' }}
          title="Open image"
        >
          <ExternalLink size={12} />
        </a>
        {onDelete && (
          <button className="btn btn-ghost" onClick={() => onDelete(result)}
            style={{ color: 'var(--red)' }} title="Delete">
            <Trash2 size={12} />
          </button>
        )}
      </div>
    </div>
  );
}
