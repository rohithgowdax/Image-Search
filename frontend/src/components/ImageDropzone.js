import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Image, X } from 'lucide-react';

export default function ImageDropzone({ file, onChange, label = 'Drop an image here or click to browse', compact = false }) {
  const onDrop = useCallback(accepted => {
    if (accepted.length > 0) onChange(accepted[0]);
  }, [onChange]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'] },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
  });

  if (file) {
    const src = URL.createObjectURL(file);
    return (
      <div style={{ display: 'inline-block' }}>
        <div className="preview-wrap">
          <img src={src} alt="Preview" style={{ maxHeight: compact ? 180 : 300 }} />
          <button className="preview-remove" onClick={() => onChange(null)}>
            <X size={14} />
          </button>
        </div>
        <div style={{ marginTop: 6, fontSize: 12, color: 'var(--text2)' }}>
          {file.name} · {(file.size / 1024).toFixed(0)} KB
        </div>
      </div>
    );
  }

  return (
    <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}
      style={{ padding: compact ? '28px 20px' : undefined }}>
      <input {...getInputProps()} />
      <div className="dropzone-icon">
        {isDragActive ? <Image size={24} /> : <Upload size={24} />}
      </div>
      <div className="dropzone-title">
        {isDragActive ? 'Release to select' : label}
      </div>
      <div className="dropzone-sub">JPG, PNG, GIF, WebP · Max 10 MB</div>
    </div>
  );
}
