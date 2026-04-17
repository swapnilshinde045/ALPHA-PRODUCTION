import React from 'react';
import { Terminal } from 'lucide-react';
import { motion } from 'framer-motion';

const SystemLog = () => {
  return (
    <motion.div 
      className="alpha-panel"
      style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: 0.3 }}
    >
      <div className="alpha-header">
        <Terminal size={16} />
        <span>SYSTEM LOG // J.A.R.V.I.S.</span>
      </div>
      
      <div style={{
        flex: 1,
        background: 'rgba(0, 0, 0, 0.4)',
        border: '1px solid rgba(0, 255, 255, 0.1)',
        borderRadius: '4px',
        padding: '0.75rem',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.75rem',
        color: 'var(--alpha-green)',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.4rem'
      }}>
        <div>&gt; Loading boot sequence...</div>
        <div>&gt; OK</div>
        <div>&gt; Establishing link to ALPHAGUI backend...</div>
        <div>&gt; Connection refused. Working locally.</div>
        <div>&gt; Loading Ollama default model (llama3)...</div>
        <div>&gt; Model loaded successfully.</div>
        <div>&gt; Initialize WhatsApp Phantom Sender... OK</div>
        <div>&gt; Awaiting voice input...</div>
        <div className="blinking-cursor" style={{ animation: 'blink 1s step-end infinite' }}>_</div>
      </div>
      
      <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
        <input 
          type="text" 
          placeholder="MANUAL OVERRIDE..." 
          style={{
            flex: 1,
            background: 'rgba(0,0,0,0.5)',
            border: '1px solid var(--alpha-border)',
            padding: '0.5rem',
            color: 'var(--alpha-cyan)',
            fontFamily: 'var(--font-mono)',
            outline: 'none',
            borderRadius: '4px'
          }}
        />
      </div>
      <style>{`
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
      `}</style>
    </motion.div>
  );
};

export default SystemLog;
