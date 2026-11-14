import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import { Search, Upload, Grid, Activity, Menu, X, Zap, AlertTriangle } from 'lucide-react';
import SearchPage from './pages/SearchPage';
import UploadPage from './pages/UploadPage';
import CollectionPage from './pages/CollectionPage';
import { getHealth } from './utils/api';
import './App.css';

function Nav({ health }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  const links = [
    { to: '/', icon: Search, label: 'Search' },
    { to: '/upload', icon: Upload, label: 'Upload' },
    { to: '/collection', icon: Grid, label: 'Collection' },
  ];

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <div className="navbar-brand">
          <div className="brand-icon"><Zap size={18} /></div>
          <span className="brand-name">VisualSearch</span>
          <span className="brand-tag">AI</span>
        </div>

        <div className={`navbar-links ${mobileOpen ? 'open' : ''}`}>
          {links.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              onClick={() => setMobileOpen(false)}
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </div>

        <div className="navbar-right">
          {health ? (
            <div className="health-badge">
              <span className={`health-dot ${health.status === 'healthy' ? 'green' : 'red'}`} />
              <span className="health-count">{health.collection_count} indexed</span>
            </div>
          ) : (
            <div className="health-badge" style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)' }}>
              <span className="health-dot red" />
              <span className="health-count" style={{ color: '#fca5a5' }}>Backend Offline</span>
            </div>
          )}
          <button className="menu-toggle" onClick={() => setMobileOpen(v => !v)}>
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>
    </nav>
  );
}

function AppContent() {
  const [health, setHealth] = useState(null);
  const [backendOnline, setBackendOnline] = useState(true);
  const location = useLocation();

  useEffect(() => {
    const check = () => getHealth()
      .then(data => { setHealth(data); setBackendOnline(true); })
      .catch(() => { setHealth(null); setBackendOnline(false); });
    check();
    const id = setInterval(check, 10000);
    return () => clearInterval(id);
  }, []);

  // Refresh health after navigation
  useEffect(() => {
    getHealth()
      .then(data => { setHealth(data); setBackendOnline(true); })
      .catch(() => { setHealth(null); setBackendOnline(false); });
  }, [location]);

  return (
    <div className="app">
      <Nav health={health} />
      {!backendOnline && (
        <div style={{
          background: 'rgba(239,68,68,0.12)',
          borderBottom: '1px solid rgba(239,68,68,0.3)',
          padding: '10px 24px',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          fontSize: 13,
          color: '#fca5a5',
        }}>
          <AlertTriangle size={15} />
          <strong>Backend is offline.</strong>&nbsp;Run <code style={{ background: 'rgba(0,0,0,0.3)', padding: '2px 6px', borderRadius: 4 }}>start-app.bat</code> to start the backend server (port 8000).
        </div>
      )}
      <main className="main-content">
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/collection" element={<CollectionPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}
