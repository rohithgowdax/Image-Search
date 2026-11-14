import React, { useState, useEffect, useCallback } from 'react';
import { Grid, Trash2, RotateCcw, RefreshCw, Search, AlertTriangle } from 'lucide-react';
import { listImages, getStats, deleteImage, clearCollection, reverseSearch } from '../utils/api';
import ResultCard from '../components/ResultCard';
import { useNavigate } from 'react-router-dom';

const API_BASE = process.env.REACT_APP_API_URL || '';
const PAGE_SIZE = 24;

export default function CollectionPage() {
  const [images, setImages] = useState([]);
  const [total, setTotal] = useState(0);
  const [stats, setStats] = useState(null);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [clearConfirm, setClearConfirm] = useState(false);
  const navigate = useNavigate();

  const load = useCallback(async (off = 0) => {
    setLoading(true);
    try {
      const [col, st] = await Promise.all([
        listImages(PAGE_SIZE, off),
        getStats(),
      ]);
      setImages(col.images);
      setTotal(col.total);
      setStats(st);
      setOffset(off);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(0); }, [load]);

  const handleDelete = async (result) => {
    if (!window.confirm(`Delete "${result.filename}"?`)) return;
    try {
      await deleteImage(result.id);
      load(offset);
    } catch (e) {
      alert(e.response?.data?.detail || 'Delete failed');
    }
  };

  const handleReverseSearch = (result) => {
    navigate(`/?reverse=${result.id}`);
  };

  const handleClear = async () => {
    try {
      await clearCollection();
      setClearConfirm(false);
      load(0);
    } catch (e) {
      alert('Clear failed');
    }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Image <span>Collection</span></h1>
        <p className="page-subtitle">Browse and manage all indexed images</p>
      </div>

      {/* Stats */}
      {stats && (
        <div className="stats-bar">
          <div className="stat-card">
            <div className="stat-value">{stats.total_images}</div>
            <div className="stat-label">Total Images</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.embedding_dim}</div>
            <div className="stat-label">Embedding Dims</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ fontSize: 14 }}>CLIP</div>
            <div className="stat-label">Embedding Model</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ fontSize: 14 }}>Chroma</div>
            <div className="stat-label">Vector Store</div>
          </div>
        </div>
      )}

      {/* Toolbar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <span style={{ fontSize: 14, color: 'var(--text2)' }}>
          {total > 0 ? `Showing ${offset + 1}–${Math.min(offset + PAGE_SIZE, total)} of ${total}` : ''}
        </span>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-ghost" onClick={() => load(offset)} style={{ padding: '7px 12px', fontSize: 13 }}>
            <RefreshCw size={13} /> Refresh
          </button>
          {total > 0 && (
            <button
              className="btn btn-ghost"
              style={{ color: 'var(--red)', fontSize: 13, padding: '7px 12px' }}
              onClick={() => setClearConfirm(true)}
            >
              <Trash2 size={13} /> Clear All
            </button>
          )}
        </div>
      </div>

      {/* Clear confirm dialog */}
      {clearConfirm && (
        <div style={{
          padding: '16px 20px',
          background: 'rgba(239,68,68,0.08)',
          border: '1px solid rgba(239,68,68,0.3)',
          borderRadius: 'var(--radius)',
          marginBottom: 20,
          display: 'flex', alignItems: 'center', gap: 12,
        }}>
          <AlertTriangle size={18} color="var(--red)" />
          <span style={{ flex: 1, fontSize: 14 }}>
            This will permanently delete all {total} indexed images. This cannot be undone.
          </span>
          <button className="btn btn-danger" onClick={handleClear}>Confirm Clear</button>
          <button className="btn btn-ghost" onClick={() => setClearConfirm(false)}>Cancel</button>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text2)' }}>
          <div className="spinner" style={{ margin: '0 auto 12px' }} />
          Loading collection…
        </div>
      )}

      {/* Empty */}
      {!loading && images.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon"><Grid size={32} /></div>
          <h3>No images indexed yet</h3>
          <p>Upload images to start building your searchable collection.</p>
          <button
            className="btn btn-primary"
            style={{ margin: '16px auto 0', display: 'flex' }}
            onClick={() => navigate('/upload')}
          >
            <Search size={14} /> Go to Upload
          </button>
        </div>
      )}

      {/* Grid */}
      {!loading && images.length > 0 && (
        <>
          <div className="results-grid">
            {images.map(img => (
              <ResultCard
                key={img.id}
                result={{
                  id: img.id,
                  filename: img.filename,
                  original_filename: img.original_filename,
                  url: img.url,
                  similarity_score: 1,
                  distance: 0,
                  width: img.width,
                  height: img.height,
                  format: img.format,
                  description: img.description,
                  tags: img.tags,
                  metadata: {},
                }}
                apiBase={API_BASE}
                onReverseSearch={handleReverseSearch}
                onDelete={handleDelete}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 32 }}>
              <button
                className="btn btn-ghost"
                disabled={offset === 0}
                onClick={() => load(Math.max(0, offset - PAGE_SIZE))}
              >
                ← Prev
              </button>
              <span style={{ padding: '8px 16px', fontSize: 14, color: 'var(--text2)' }}>
                Page {currentPage} of {totalPages}
              </span>
              <button
                className="btn btn-ghost"
                disabled={offset + PAGE_SIZE >= total}
                onClick={() => load(offset + PAGE_SIZE)}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
