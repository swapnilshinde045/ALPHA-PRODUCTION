import React, { useRef, useEffect, useState } from 'react';
import { Terminal } from 'lucide-react';
import { motion } from 'framer-motion';

const SystemLog = ({ logs, onSendCommand }) => {
  const [inputVal, setInputVal] = useState('');
  const logEndRef = useRef(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && inputVal.trim() !== '') {
      onSendCommand(inputVal);
      setInputVal('');
    }
  };

  return (
    <motion.div 
      className="alpha-panel"
      style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}
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
        {logs.map(log => (
          <div key={log.id} style={{ 
            color: log.type === 'error' ? 'var(--alpha-red)' : log.type === 'warning' ? 'var(--alpha-amber)' : 'var(--alpha-green)' 
          }}>
            <span style={{opacity: 0.5}}>[{log.time}]</span> &gt; {log.text}
          </div>
        ))}
        <div ref={logEndRef} className="blinking-cursor" style={{ animation: 'blink 1s step-end infinite' }}>_</div>
      </div>
      
      <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
        <input 
          type="text" 
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          onKeyDown={handleKeyDown}
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
