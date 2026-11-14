import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || '';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
});

// Intercept network errors and give clear messages
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      // Network error — backend is likely not running
      error.message =
        'Cannot connect to backend. Please make sure the backend server is running on port 8000. Run start-app.bat to start everything.';
    }
    return Promise.reject(error);
  }
);

// ── Health ──────────────────────────────────────────────────────────
export const getHealth = () => api.get('/api/health').then(r => r.data);

// ── Upload ───────────────────────────────────────────────────────────
export const uploadImage = (file, tags = '', description = '') => {
  const form = new FormData();
  form.append('file', file);
  if (tags) form.append('tags', tags);
  if (description) form.append('description', description);
  return api.post('/api/upload', form).then(r => r.data);
};

export const bulkUpload = (files) => {
  const form = new FormData();
  files.forEach(f => form.append('files', f));
  return api.post('/api/upload/bulk', form).then(r => r.data);
};

export const deleteImage = (id) =>
  api.delete(`/api/images/${id}`).then(r => r.data);

// ── Search ───────────────────────────────────────────────────────────
export const searchByImage = (file, topK = 5, minSimilarity = 0) => {
  const form = new FormData();
  form.append('file', file);
  form.append('top_k', topK);
  form.append('min_similarity', minSimilarity);
  return api.post('/api/search/image', form).then(r => r.data);
};

export const searchByText = (q, topK = 5, minSimilarity = 0) =>
  api.get('/api/search/text', { params: { q, top_k: topK, min_similarity: minSimilarity } })
     .then(r => r.data);

export const searchMultimodal = (file, text, alpha = 0.7, topK = 5) => {
  const form = new FormData();
  form.append('file', file);
  form.append('text', text);
  form.append('alpha', alpha);
  form.append('top_k', topK);
  return api.post('/api/search/multimodal', form).then(r => r.data);
};

export const reverseSearch = (imageId, topK = 5) =>
  api.get(`/api/search/reverse/${imageId}`, { params: { top_k: topK } })
     .then(r => r.data);

// ── Collection ───────────────────────────────────────────────────────
export const getStats = () => api.get('/api/collection/stats').then(r => r.data);

export const listImages = (limit = 20, offset = 0) =>
  api.get('/api/collection/images', { params: { limit, offset } }).then(r => r.data);

export const getImage = (id) =>
  api.get(`/api/collection/images/${id}`).then(r => r.data);

export const clearCollection = () =>
  api.delete('/api/collection/clear').then(r => r.data);
