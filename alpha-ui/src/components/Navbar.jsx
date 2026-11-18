import React from 'react';
import { Shield, Settings, Activity, Home, Cpu, ArrowUpCircle } from 'lucide-react';
import './Navbar.css';

const Navbar = ({ connected = true, onOpenSettings, updateAvailable = false, onOpenUpdate }) => {
  return (
    <header className="alpha-header-wrapper">
      {/* Top Cyber Branding Banner */}
      <div className="alpha-top-branding">
        <div className="branding-glow-dot"></div>
        <div className="branding-content">
          <span className="branding-prefix">Copyright by </span>
          <strong className="branding-author">Swapnil shinde</strong>
          <span className="branding-sep"> in association with </span>
          <strong className="branding-org">SSCODEHUB</strong>
        </div>
        <div className="branding-glow-dot"></div>
      </div>

      <nav className="alpha-navbar">
        <div className="navbar-brand">
          <div className="logo-icon">
            <Cpu size={24} className="cyan-glow" />
          </div>
          <div className="logo-text">
            <h1>A.L.P.H.A.</h1>
            <span className="subtitle">ADVANCE LEARNING PROCESSING HUB ASSISTANT</span>
          </div>
        </div>
        
        <div className="navbar-links">
          <a href="#" className="nav-item active">
            <Home size={18} />
            <span>DASHBOARD</span>
          </a>
          <a href="#" className="nav-item">
            <Activity size={18} />
            <span>ACTIVITY</span>
          </a>
          <a href="#" className="nav-item">
            <Shield size={18} />
            <span>SECURITY</span>
          </a>
          {updateAvailable && (
            <button
              type="button"
              onClick={onOpenUpdate}
              className="nav-item nav-button-reset"
              style={{
                background: 'rgba(0, 255, 255, 0.15)',
                border: '1px solid #00ffff',
                color: '#00ffff',
                borderRadius: '6px',
                padding: '0.35rem 0.75rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                cursor: 'pointer',
                boxShadow: '0 0 12px rgba(0, 255, 255, 0.3)'
              }}
            >
              <ArrowUpCircle size={15} className="pulsing" />
              <span style={{ fontWeight: 'bold', fontSize: '0.75rem' }}>UPDATE v4.0 ↗</span>
            </button>
          )}
          <button 
            type="button"
            onClick={onOpenSettings} 
            className="nav-item nav-button-reset"
            title="Open System Settings"
          >
            <Settings size={18} />
            <span>SETTINGS</span>
          </button>
        </div>
        
        <div className="navbar-status">
          <div className={`status-dot ${connected ? 'pulsing' : ''}`}></div>
          <span>{connected ? 'SYSTEM ONLINE' : 'OFFLINE'}</span>
        </div>
      </nav>
    </header>
  );
};

export default Navbar;

