import React, { useState, useCallback } from 'react';
import { Upload, CheckCircle, XCircle, Plus, Trash2, Tag, FileText } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { uploadImage, bulkUpload } from '../utils/api';

function UploadResult({ result }) {
  if (!result) return null;
  const ok = result.indexed;
  return (
    <div style={{
      padding: '14px 16px',
      borderRadius: 'var(--radius-sm)',
      border: `1px solid ${ok ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
      background: ok ? 'rgba(34,197,94,0.07)' : 'rgba(239,68,68,0.07)',
      display: 'flex', alignItems: 'flex-start', gap: 12, marginTop: 16,
    }}>
      {ok
        ? <CheckCircle size={18} color="var(--green)" style={{ flexShrink: 0, marginTop: 1 }} />
        : <XCircle size={18} color="var(--red)" style={{ flexShrink: 0, marginTop: 1 }} />
      }
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>
          {ok ? 'Image indexed successfully!' : 'Upload failed'}
        </div>
        {ok && (
          <div style={{ fontSize: 12, color: 'var(--text2)', display: 'flex', flexDirection: 'column', gap: 2 }}>
            <span>ID: <code style={{ color: 'var(--accent2)' }}>{result.id}</code></span>
            <span>Size: {result.width}×{result.height} · {(result.file_size / 1024).toFixed(0)} KB</span>
            <span>Embedding: {result.embedding_dim}-dim vector</span>
            <span>{result.message}</span>
          </div>
        )}
      </div>
    </div>
  );
}

function BulkFileItem({ file, status }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      padding: '8px 12px', borderRadius: 8,
      background: 'var(--bg3)', border: '1px solid var(--border)',
    }}>
      <div style={{
        width: 36, height: 36, borderRadius: 6, overflow: 'hidden',
        background: 'var(--bg)', flexShrink: 0,
      }}>
        <img
          src={URL.createObjectURL(file)}
          alt={file.name}
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 12, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {file.name}
        </div>
        <div style={{ fontSize: 11, color: 'var(--text2)' }}>
          {(file.size / 1024).toFixed(0)} KB
        </div>
      </div>
      {status === 'success' && <CheckCircle size={14} color="var(--green)" />}
      {status === 'failed' && <XCircle size={14} color="var(--red)" />}
      {status === 'pending' && <div className="spinner" style={{ width: 14, height: 14 }} />}
    </div>
  );
}

export default function UploadPage() {
  const [tab, setTab] = useState('single');

  // Single upload state
  const [file, setFile] = useState(null);
  const [tags, setTags] = useState('');
  const [desc, setDesc] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  // Bulk upload state
  const [bulkFiles, setBulkFiles] = useState([]);
  const [bulkStatuses, setBulkStatuses] = useState({});
  const [bulkLoading, setBulkLoading] = useState(false);
  const [bulkResult, setBulkResult] = useState(null);

  const onDrop = useCallback(accepted => {
    if (accepted[0]) {
      setFile(accepted[0]);
      setResult(null);
      setError('');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': [] },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
  });

  const handleSingleUpload = async () => {
    if (!file) { setError('Please select an image.'); return; }
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const r = await uploadImage(file, tags, desc);
      setResult(r);
      setFile(null);
      setTags('');
      setDesc('');
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const onBulkDrop = useCallback(accepted => {
    setBulkFiles(prev => {
      const existing = new Set(prev.map(f => f.name));
      const newFiles = accepted.filter(f => !existing.has(f.name));
      return [...prev, ...newFiles].slice(0, 20);
    });
    setBulkResult(null);
  }, []);

  const { getRootProps: getBulkRootProps, getInputProps: getBulkInputProps } = useDropzone({
    onDrop: onBulkDrop,
    accept: { 'image/*': [] },
    maxFiles: 20,
    maxSize: 10 * 1024 * 1024,
  });

  const handleBulkUpload = async () => {
    if (bulkFiles.length === 0) return;
    setBulkLoading(true);
    setBulkStatuses({});
    setBulkResult(null);

    // Show pending status
    const pending = {};
    bulkFiles.forEach(f => { pending[f.name] = 'pending'; });
    setBulkStatuses(pending);

    try {
      const r = await bulkUpload(bulkFiles);
      setBulkResult(r);
      const statuses = {};
      r.results.forEach(res => { statuses[res.filename] = res.status; });
      setBulkStatuses(statuses);
    } catch (e) {
      const failed = {};
      bulkFiles.forEach(f => { failed[f.name] = 'failed'; });
      setBulkStatuses(failed);
    } finally {
      setBulkLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Upload & <span>Index Images</span></h1>
        <p className="page-subtitle">Add images to the search collection</p>
      </div>

      <div className="tab-bar">
        <button className={`tab-btn ${tab === 'single' ? 'active' : ''}`} onClick={() => setTab('single')}>
          <Upload size={14} /> Single Upload
        </button>
        <button className={`tab-btn ${tab === 'bulk' ? 'active' : ''}`} onClick={() => setTab('bulk')}>
          <Plus size={14} /> Bulk Upload
        </button>
      </div>

      {/* ── Single Upload ── */}
      {tab === 'single' && (
        <div className="card">
          <div style={{ marginBottom: 20 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)', display: 'block', marginBottom: 10 }}>
              Image
            </label>
            {file ? (
              <div className="preview-wrap" style={{ display: 'block' }}>
                <img
                  src={URL.createObjectURL(file)}
                  alt="Preview"
                  style={{ maxHeight: 240, width: '100%', objectFit: 'contain', background: 'var(--bg3)' }}
                />
                <button className="preview-remove" onClick={() => setFile(null)}>
                  <Trash2 size={14} />
                </button>
              </div>
            ) : (
              <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
                <input {...getInputProps()} />
                <div className="dropzone-icon"><Upload size={24} /></div>
                <div className="dropzone-title">Drop image or click to browse</div>
                <div className="dropzone-sub">JPG, PNG, GIF, WebP · Max 10 MB</div>
              </div>
            )}
          </div>

          <div style={{ display: 'grid', gap: 16, marginBottom: 20 }}>
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)', display: 'flex', gap: 6, marginBottom: 6 }}>
                <Tag size={13} /> Tags <span style={{ color: 'var(--text3)' }}>(optional)</span>
              </label>
              <input
                type="text"
                placeholder="car, red, sports, ferrari"
                value={tags}
                onChange={e => setTags(e.target.value)}
              />
            </div>
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)', display: 'flex', gap: 6, marginBottom: 6 }}>
                <FileText size={13} /> Description <span style={{ color: 'var(--text3)' }}>(optional)</span>
              </label>
              <input
                type="text"
                placeholder="A red Ferrari F40 on a mountain road"
                value={desc}
                onChange={e => setDesc(e.target.value)}
              />
            </div>
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
            onClick={handleSingleUpload}
            disabled={loading || !file}
            style={{ width: '100%', justifyContent: 'center', padding: '12px' }}
          >
            {loading
              ? <><span className="spinner" style={{ borderTopColor: 'white' }} /> Indexing…</>
              : <><Upload size={16} /> Upload & Index</>
            }
          </button>

          <UploadResult result={result} />
        </div>
      )}

      {/* ── Bulk Upload ── */}
      {tab === 'bulk' && (
        <div className="card">
          <div {...getBulkRootProps()} className="dropzone" style={{ marginBottom: 20 }}>
            <input {...getBulkInputProps()} />
            <div className="dropzone-icon"><Plus size={24} /></div>
            <div className="dropzone-title">Drop multiple images or click to browse</div>
            <div className="dropzone-sub">Up to 20 images · Max 10 MB each</div>
          </div>

          {bulkFiles.length > 0 && (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>{bulkFiles.length} files selected</span>
                <button className="btn btn-ghost" style={{ padding: '5px 10px', fontSize: 12 }}
                  onClick={() => { setBulkFiles([]); setBulkStatuses({}); setBulkResult(null); }}>
                  <Trash2 size={12} /> Clear all
                </button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 8, marginBottom: 20 }}>
                {bulkFiles.map(f => (
                  <BulkFileItem key={f.name} file={f} status={bulkStatuses[f.name]} />
                ))}
              </div>

              {bulkResult && (
                <div style={{
                  padding: '12px 16px', borderRadius: 'var(--radius-sm)', marginBottom: 16,
                  background: 'rgba(34,197,94,0.07)', border: '1px solid rgba(34,197,94,0.3)',
                  fontSize: 13, display: 'flex', gap: 16
                }}>
                  <span><CheckCircle size={14} color="var(--green)" style={{ verticalAlign: 'middle', marginRight: 4 }} />
                    {bulkResult.successful} indexed
                  </span>
                  {bulkResult.failed > 0 && (
                    <span style={{ color: 'var(--red)' }}>
                      <XCircle size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />
                      {bulkResult.failed} failed
                    </span>
                  )}
                </div>
              )}

              <button
                className="btn btn-primary"
                onClick={handleBulkUpload}
                disabled={bulkLoading || bulkFiles.length === 0}
                style={{ width: '100%', justifyContent: 'center', padding: '12px' }}
              >
                {bulkLoading
                  ? <><span className="spinner" style={{ borderTopColor: 'white' }} /> Indexing {bulkFiles.length} images…</>
                  : <><Upload size={16} /> Index {bulkFiles.length} Images</>
                }
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
