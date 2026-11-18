import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Settings, X, Cpu, ExternalLink, ShieldCheck, 
  CheckCircle2, Sparkles, Server, Zap, User 
} from 'lucide-react';

const AVAILABLE_MODELS = [
  { id: 'gemini-3.5-flash', name: 'Gemini 3.5 Flash', desc: 'Next-gen multimodal, ultra-fast & intelligent (Recommended)', tag: 'ACTIVE & VERIFIED', color: '#00ffff' },
  { id: 'gemini-3.5-flash-lite', name: 'Gemini 3.5 Flash Lite', desc: 'Ultra-low latency, instant conversational responses', tag: 'FASTEST', color: '#00ffaa' },
  { id: 'gemini-3.1-flash-lite', name: 'Gemini 3.1 Flash Lite', desc: 'Optimized intelligence with high speed & reliability', tag: 'STABLE', color: '#38bdf8' },
  { id: 'gemini-3-flash-preview', name: 'Gemini 3 Flash Preview', desc: 'Advanced next-generation reasoning engine', tag: 'PREVIEW', color: '#ffb700' },
  { id: 'ollama-local', name: 'Ollama (Local Offline AI)', desc: '100% private on-device local brain (Requires Ollama on localhost:11434)', tag: 'LOCAL OFFLINE', color: '#f43f5e' },
];

const SettingsModal = ({ isOpen, onClose, onAction, username, onEditUsername, onCheckUpdate }) => {
  const [selectedModel, setSelectedModel] = useState(
    localStorage.getItem('alpha_selected_model') || 'gemini-3.5-flash'
  );
  const [modelSaved, setModelSaved] = useState(false);

  if (!isOpen) return null;

  const handleModelChange = (modelId) => {
    setSelectedModel(modelId);
    localStorage.setItem('alpha_selected_model', modelId);
    if (onAction) {
      onAction('set_model', modelId);
    }
    setModelSaved(true);
    setTimeout(() => setModelSaved(false), 2000);
  };

  const handleActionClick = (actionName) => {
    if (onAction) {
      onAction(actionName);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0, 0, 0, 0.85)',
          backdropFilter: 'blur(12px)',
          zIndex: 10000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '1.5rem'
        }}
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, y: 20 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.9, y: 20 }}
          transition={{ type: 'spring', damping: 25 }}
          className="alpha-panel"
          style={{
            width: '640px',
            maxWidth: '95%',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: '2rem',
            border: '1px solid var(--alpha-cyan)',
            boxShadow: '0 0 35px rgba(0, 255, 255, 0.15), inset 0 0 20px rgba(0, 255, 255, 0.05)',
            background: 'rgba(10, 14, 20, 0.96)',
            borderRadius: '12px'
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(0, 255, 255, 0.2)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--alpha-cyan)' }}>
              <Settings size={22} className="cyan-glow" />
              <div>
                <h2 style={{ fontFamily: 'var(--font-header)', fontSize: '1.2rem', letterSpacing: '2px', color: '#fff', margin: 0 }}>
                  SYSTEM SETTINGS & CONFIGURATION
                </h2>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', color: 'var(--alpha-cyan)', letterSpacing: '1px', opacity: 0.8 }}>
                  A.L.P.H.A. CORE PROTOCOL v2.0
                </span>
              </div>
            </div>
            <button 
              onClick={onClose}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: 'var(--text-muted)',
                borderRadius: '6px',
                padding: '0.4rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s ease'
              }}
              onMouseOver={(e) => { e.currentTarget.style.color = '#fff'; e.currentTarget.style.borderColor = 'var(--alpha-cyan)'; }}
              onMouseOut={(e) => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)'; }}
            >
              <X size={18} />
            </button>
          </div>

          {/* OPERATOR DESIGNATION (USER CALL SIGN) */}
          <div style={{ marginBottom: '1.2rem', background: 'rgba(0, 0, 0, 0.45)', padding: '1rem 1.2rem', borderRadius: '8px', border: '1px solid rgba(0, 255, 255, 0.2)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
              <div style={{ padding: '0.6rem', background: 'rgba(0, 255, 255, 0.08)', borderRadius: '6px', border: '1px solid rgba(0, 255, 255, 0.3)', color: 'var(--alpha-cyan)' }}>
                <User size={20} />
              </div>
              <div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.68rem', color: 'var(--text-muted)', letterSpacing: '1px' }}>
                  OPERATOR CALLSIGN
                </div>
                <div style={{ fontFamily: 'var(--font-header)', fontSize: '1rem', color: '#fff', letterSpacing: '2px', marginTop: '0.15rem' }}>
                  {username ? username.toUpperCase() : 'NOT SET (ANONYMOUS)'}
                </div>
              </div>
            </div>

            <button
              onClick={onEditUsername}
              style={{
                padding: '0.55rem 1rem',
                background: 'rgba(0, 255, 255, 0.12)',
                border: '1px solid var(--alpha-cyan)',
                borderRadius: '4px',
                color: 'var(--alpha-cyan)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.72rem',
                letterSpacing: '1.5px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                fontWeight: 'bold'
              }}
              onMouseOver={(e) => { e.currentTarget.style.background = 'var(--alpha-cyan)'; e.currentTarget.style.color = '#000'; }}
              onMouseOut={(e) => { e.currentTarget.style.background = 'rgba(0, 255, 255, 0.12)'; e.currentTarget.style.color = 'var(--alpha-cyan)'; }}
            >
              CHANGE USERNAME
            </button>
          </div>

          {/* SELECT MODEL SECTION */}
          <div style={{ marginBottom: '1.5rem', background: 'rgba(0, 0, 0, 0.45)', padding: '1.2rem', borderRadius: '8px', border: '1px solid rgba(0, 255, 255, 0.2)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.9rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--alpha-cyan)', fontFamily: 'var(--font-mono)', fontSize: '0.82rem', letterSpacing: '1.5px', fontWeight: 'bold' }}>
                <Cpu size={16} />
                <span>SELECT AI MODEL ARCHITECTURE</span>
              </div>
              {modelSaved && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#00ffaa', fontFamily: 'var(--font-mono)', fontSize: '0.7rem' }}>
                  <CheckCircle2 size={13} />
                  <span>MODEL APPLIED</span>
                </div>
              )}
            </div>

            <p style={{ margin: '0 0 1rem 0', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.72rem', lineHeight: '1.4' }}>
              Choose the primary intelligence model powering ALPHA's conversational reasoning and coding engine:
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
              {AVAILABLE_MODELS.map((m) => {
                const isSelected = selectedModel === m.id;
                return (
                  <div
                    key={m.id}
                    onClick={() => handleModelChange(m.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0.75rem 1rem',
                      background: isSelected ? 'rgba(0, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.35)',
                      border: `1px solid ${isSelected ? 'var(--alpha-cyan)' : 'rgba(255, 255, 255, 0.08)'}`,
                      borderRadius: '6px',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      boxShadow: isSelected ? '0 0 15px rgba(0, 255, 255, 0.15)' : 'none',
                    }}
                    onMouseOver={(e) => {
                      if (!isSelected) {
                        e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                        e.currentTarget.style.borderColor = 'rgba(0, 255, 255, 0.3)';
                      }
                    }}
                    onMouseOut={(e) => {
                      if (!isSelected) {
                        e.currentTarget.style.background = 'rgba(0, 0, 0, 0.35)';
                        e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                      }
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <div style={{
                        width: '10px',
                        height: '10px',
                        borderRadius: '50%',
                        background: isSelected ? m.color : 'rgba(255, 255, 255, 0.2)',
                        boxShadow: isSelected ? `0 0 8px ${m.color}` : 'none'
                      }}></div>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ fontFamily: 'var(--font-header)', fontSize: '0.88rem', color: isSelected ? '#fff' : 'var(--text-main)', letterSpacing: '0.5px' }}>
                            {m.name}
                          </span>
                          <span style={{
                            fontSize: '0.55rem',
                            fontFamily: 'var(--font-mono)',
                            padding: '0.15rem 0.45rem',
                            borderRadius: '3px',
                            background: `${m.color}20`,
                            color: m.color,
                            border: `1px solid ${m.color}50`,
                            letterSpacing: '0.5px'
                          }}>
                            {m.tag}
                          </span>
                        </div>
                        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.67rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                          {m.desc}
                        </div>
                      </div>
                    </div>

                    <div style={{
                      padding: '0.35rem 0.75rem',
                      borderRadius: '4px',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.68rem',
                      letterSpacing: '1px',
                      background: isSelected ? 'var(--alpha-cyan)' : 'transparent',
                      color: isSelected ? '#000' : 'var(--text-muted)',
                      border: `1px solid ${isSelected ? 'var(--alpha-cyan)' : 'rgba(255, 255, 255, 0.15)'}`,
                      fontWeight: isSelected ? 'bold' : 'normal'
                    }}>
                      {isSelected ? 'ACTIVE' : 'SELECT'}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Windows System Settings Integration */}
          <div style={{ marginBottom: '1.5rem', background: 'rgba(0, 0, 0, 0.4)', padding: '1.2rem', borderRadius: '8px', border: '1px solid rgba(0, 255, 255, 0.15)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#fff', fontFamily: 'var(--font-header)', fontSize: '0.9rem', letterSpacing: '1px' }}>
                  <ExternalLink size={16} color="var(--alpha-cyan)" />
                  <span>WINDOWS SYSTEM SETTINGS</span>
                </div>
                <p style={{ margin: '0.3rem 0 0 0', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.7rem' }}>
                  Open native Windows 10/11 Settings panel directly from ALPHA.
                </p>
              </div>
              <button
                onClick={() => handleActionClick('open_settings')}
                style={{
                  padding: '0.6rem 1.1rem',
                  background: 'rgba(0, 255, 255, 0.1)',
                  border: '1px solid var(--alpha-cyan)',
                  borderRadius: '4px',
                  color: 'var(--alpha-cyan)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.75rem',
                  letterSpacing: '1px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  transition: 'all 0.2s ease'
                }}
                onMouseOver={(e) => e.currentTarget.style.background = 'rgba(0, 255, 255, 0.2)'}
                onMouseOut={(e) => e.currentTarget.style.background = 'rgba(0, 255, 255, 0.1)'}
              >
                <span>OPEN SETTINGS</span>
                <ExternalLink size={14} />
              </button>
            </div>
          </div>

          {/* Subsystem Diagnostics */}
          <div style={{ marginBottom: '1.5rem', padding: '1rem', background: 'rgba(0, 255, 255, 0.03)', borderRadius: '8px', border: '1px dashed rgba(0, 255, 255, 0.2)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: 'var(--alpha-cyan)', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
              <ShieldCheck size={15} />
              <span>SUBSYSTEM DIAGNOSTICS</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem', fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              <div>• ACTIVE MODEL: <span style={{ color: '#00ffaa' }}>{selectedModel}</span></div>
              <div>• BACKEND: <span style={{ color: '#fff' }}>Python 3.10 Daemon</span></div>
              <div>• WEBSOCKET: <span style={{ color: '#00ffaa' }}>ws://localhost:8765</span></div>
              <div>• CLIENT BUILD: <span style={{ color: '#ffb700' }}>v2.0</span></div>
            </div>

            <div style={{ marginTop: '0.8rem', paddingTop: '0.8rem', borderTop: '1px solid rgba(0, 255, 255, 0.1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ color: '#fff', fontSize: '0.72rem', fontWeight: 'bold', fontFamily: 'var(--font-header)' }}>CLOUD UPGRADES</div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.65rem', fontFamily: 'var(--font-mono)' }}>Check official servers for releases</div>
              </div>
              <button
                type="button"
                onClick={() => {
                  onClose();
                  if (onCheckUpdate) onCheckUpdate();
                }}
                style={{
                  padding: '0.45rem 0.9rem',
                  background: 'rgba(0, 255, 255, 0.15)',
                  border: '1px solid var(--alpha-cyan)',
                  borderRadius: '4px',
                  color: 'var(--alpha-cyan)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.7rem',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                  letterSpacing: '1px'
                }}
                onMouseOver={(e) => { e.currentTarget.style.background = 'var(--alpha-cyan)'; e.currentTarget.style.color = '#000'; }}
                onMouseOut={(e) => { e.currentTarget.style.background = 'rgba(0, 255, 255, 0.15)'; e.currentTarget.style.color = 'var(--alpha-cyan)'; }}
              >
                CHECK FOR UPDATES ↗
              </button>
            </div>
          </div>

          {/* Top-Tier Branding & Copyright Banner */}
          <div style={{
            textAlign: 'center',
            borderTop: '1px solid rgba(0, 255, 255, 0.15)',
            paddingTop: '1.2rem',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            letterSpacing: '1px'
          }}>
            <div>
              <span style={{ color: 'rgba(255, 255, 255, 0.6)' }}>Copyright © </span>
              <strong style={{ color: 'var(--alpha-cyan)', fontWeight: 'bold' }}>Swapnil shinde</strong>
              <span style={{ color: 'rgba(255, 255, 255, 0.6)' }}> in association with </span>
              <strong style={{ color: '#00ffaa', fontWeight: 'bold' }}>SSCODEHUB</strong>
            </div>
            <div style={{ fontSize: '0.65rem', color: 'rgba(255, 255, 255, 0.35)', marginTop: '0.3rem' }}>
              ALL RIGHTS RESERVED // A.L.P.H.A. ASSISTANT
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default SettingsModal;
