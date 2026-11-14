import React, { useState, useCallback } from 'react';
import { Search, Type, Layers, RotateCcw, Clock, Sliders } from 'lucide-react';
import ImageDropzone from '../components/ImageDropzone';
import ResultCard from '../components/ResultCard';
import { searchByImage, searchByText, searchMultimodal, reverseSearch } from '../utils/api';

const API_BASE = process.env.REACT_APP_API_URL || '';

function EmptyResults({ searched }) {
  return (
    <div className="empty-state">
      <div className="empty-icon">
        <Search size={32} />
      </div>
      {searched ? (
        <>
          <h3>No results found</h3>
          <p>Try a different image or text query, or index more images in the collection first.</p>
        </>
      ) : (
        <>
          <h3>Ready to search</h3>
          <p>Upload a query image or type a description to find visually similar images from the indexed collection.</p>
        </>
      )}
    </div>
  );
}

function SearchMeta({ response }) {
  if (!response) return null;
  return (
    <div className="results-meta">
      <span>Found <strong>{response.total_results}</strong> results</span>
      <span>·</span>
      <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
        <Clock size={12} /> {response.search_time_ms}ms
      </span>
      {response.query_text && (
        <>
          <span>·</span>
          <span>Query: <strong>"{response.query_text}"</strong></span>
        </>
      )}
    </div>
  );
}

export default function SearchPage() {
  const [tab, setTab] = useState('image'); // image | text | multimodal
  const [file, setFile] = useState(null);
  const [textQuery, setTextQuery] = useState('');
  const [multiText, setMultiText] = useState('');
  const [alpha, setAlpha] = useState(0.7);
  const [topK, setTopK] = useState(5);
  const [minSim, setMinSim] = useState(0);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState('');
  const [searched, setSearched] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const handleSearch = useCallback(async () => {
    setError('');
    setLoading(true);
    setSearched(true);

    try {
      let result;
      if (tab === 'image') {
        if (!file) { setError('Please select an image.'); setLoading(false); return; }
        result = await searchByImage(file, topK, minSim);
      } else if (tab === 'text') {
        if (!textQuery.trim()) { setError('Please enter a search query.'); setLoading(false); return; }
        result = await searchByText(textQuery.trim(), topK, minSim);
      } else {
        if (!file) { setError('Please select an image for multimodal search.'); setLoading(false); return; }
        if (!multiText.trim()) { setError('Please enter a text description.'); setLoading(false); return; }
        result = await searchMultimodal(file, multiText.trim(), alpha, topK);
      }
      setResponse(result);
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  }, [tab, file, textQuery, multiText, alpha, topK, minSim]);

  const handleReverseSearch = useCallback(async (result) => {
    setLoading(true);
    setSearched(true);
    try {
      const res = await reverseSearch(result.id, topK);
      setResponse(res);
    } catch (e) {
      setError(e.response?.data?.detail || 'Reverse search failed');
    } finally {
      setLoading(false);
    }
  }, [topK]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSearch();
  };

  const tabs = [
    { id: 'image', icon: Search, label: 'Image Search' },
    { id: 'text', icon: Type, label: 'Text Search' },
    { id: 'multimodal', icon: Layers, label: 'Multi-modal' },
  ];

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Find <span>Similar Images</span></h1>
        <p className="page-subtitle">
          Powered by CLIP embeddings and ChromaDB vector search
        </p>
      </div>

      {/* Tab Bar */}
      <div className="tab-bar">
        {tabs.map(({ id, icon: Icon, label }) => (
          <button
            key={id}
            className={`tab-btn ${tab === id ? 'active' : ''}`}
            onClick={() => { setTab(id); setResponse(null); setSearched(false); }}
          >
            <Icon size={14} /> {label}
          </button>
        ))}
      </div>

      {/* Search Panel */}
      <div className="card" style={{ marginBottom: 28 }}>
        {/* Image tab */}
        {tab === 'image' && (
          <div>
            <div style={{ marginBottom: 20 }}>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)', display: 'block', marginBottom: 10 }}>
                Query Image
              </label>
              <ImageDropzone file={file} onChange={setFile} />
            </div>
          </div>
        )}

        {/* Text tab */}
        {tab === 'text' && (
          <div style={{ marginBottom: 20 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)', display: 'block', marginBottom: 10 }}>
              Text Description
            </label>
            <input
              type="text"
              placeholder="e.g. 'a red sports car on a mountain road'"
              value={textQuery}
              onChange={e => setTextQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              style={{ fontSize: 15, padding: '12px 16px' }}
            />
            <p style={{ fontSize: 12, color: 'var(--text3)', marginTop: 6 }}>
              Uses CLIP zero-shot text embeddings to find matching images.
            </p>
          </div>
        )}

        {/* Multimodal tab */}
        {tab === 'multimodal' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 20 }}>
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)', display: 'block', marginBottom: 10 }}>
                Query Image
              </label>
              <ImageDropzone file={file} onChange={setFile} compact />
            </div>
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)', display: 'block', marginBottom: 10 }}>
                Refine with Text
              </label>
              <textarea
                placeholder="e.g. 'make it red' or 'in a forest setting'"
                value={multiText}
                onChange={e => setMultiText(e.target.value)}
                rows={4}
                style={{ resize: 'vertical' }}
              />
              <div style={{ marginTop: 14 }}>
                <label style={{ fontSize: 12, color: 'var(--text2)', display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span>Image weight (α)</span>
                  <strong style={{ color: 'var(--accent2)' }}>{alpha.toFixed(1)}</strong>
                </label>
                <input type="range" min="0" max="1" step="0.1"
                  value={alpha} onChange={e => setAlpha(Number(e.target.value))} />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text3)', marginTop: 2 }}>
                  <span>Text only</span><span>Image only</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Settings */}
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16, marginBottom: 16 }}>
          <button
            className="btn btn-ghost"
            style={{ padding: '6px 12px', fontSize: 12 }}
            onClick={() => setShowSettings(v => !v)}
          >
            <Sliders size={13} /> Search Options
          </button>

          {showSettings && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginTop: 16 }}>
              <div>
                <label style={{ fontSize: 12, color: 'var(--text2)', display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span>Top K results</span>
                  <strong style={{ color: 'var(--accent2)' }}>{topK}</strong>
                </label>
                <input type="range" min="1" max="20" value={topK}
                  onChange={e => setTopK(Number(e.target.value))} />
              </div>
              <div>
                <label style={{ fontSize: 12, color: 'var(--text2)', display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span>Min similarity</span>
                  <strong style={{ color: 'var(--accent2)' }}>{Math.round(minSim * 100)}%</strong>
                </label>
                <input type="range" min="0" max="0.9" step="0.05"
                  value={minSim} onChange={e => setMinSim(Number(e.target.value))} />
              </div>
            </div>
          )}
        </div>

        {error && (
          <div style={{
            padding: '10px 14px', background: 'rgba(239,68,68,0.1)',
            border: '1px solid rgba(239,68,68,0.3)', borderRadius: 'var(--radius-sm)',
            color: '#fca5a5', fontSize: 13, marginBottom: 12
          }}>{error}</div>
        )}

        <button
          className="btn btn-primary"
          onClick={handleSearch}
          disabled={loading}
          style={{ width: '100%', justifyContent: 'center', padding: '12px' }}
        >
          {loading ? (
            <><span className="spinner" style={{ borderTopColor: 'white' }} /> Searching…</>
          ) : (
            <><Search size={16} /> Search</>
          )}
        </button>
      </div>

      {/* Results */}
      <SearchMeta response={response} />

      {response && response.results.length > 0 ? (
        <div className="results-grid">
          {response.results.map(r => (
            <ResultCard
              key={r.id}
              result={r}
              apiBase={API_BASE}
              onReverseSearch={handleReverseSearch}
            />
          ))}
        </div>
      ) : (
        <EmptyResults searched={searched} />
      )}
    </div>
  );
}
