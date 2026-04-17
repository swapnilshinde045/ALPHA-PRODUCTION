import React from 'react';
import { Shield, Settings, Activity, Home, Cpu } from 'lucide-react';
import './Navbar.css';

const Navbar = () => {
  return (
    <nav className="alpha-navbar">
      <div className="navbar-brand">
        <div className="logo-icon">
          <Cpu size={24} className="cyan-glow" />
        </div>
        <div className="logo-text">
          <h1>A.L.P.H.A.</h1>
          <span className="subtitle">ARTIFICIAL LINGUISTIC PREDICTIVE HEURISTIC ALGORITHM</span>
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
        <a href="#" className="nav-item">
          <Settings size={18} />
          <span>SETTINGS</span>
        </a>
      </div>
      
      <div className="navbar-status">
        <div className="status-dot pulsing"></div>
        <span>SYSTEM ONLINE</span>
      </div>
    </nav>
  );
};

export default Navbar;
