import React, { useState, useEffect } from 'react';
import { Activity } from 'lucide-react';
import { motion } from 'framer-motion';

const ActivityMonitor = () => {
  const [logs, setLogs] = useState([
    { id: 1, time: '14:02:44', text: 'SYSTEM INITIALIZED', status: 'info' },
    { id: 2, time: '14:02:45', text: 'OLLAMA ENGINE START', status: 'success' },
    { id: 3, time: '14:02:46', text: 'WEBHOOKS CONNECTED', status: 'success' },
    { id: 4, time: '14:03:12', text: 'LISTENING...', status: 'warning' },
  ]);

  return (
    <motion.div 
      className="alpha-panel"
      style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
      initial={{ opacity: 0, x: -50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: 0.3 }}
    >
      <div className="alpha-header">
        <Activity size={16} />
        <span>ACTIVITY MONITOR</span>
      </div>
      
      <div style={{ 
        flex: 1, 
        overflowY: 'auto',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.8rem',
        marginTop: '0.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem'
      }}>
        {logs.map(log => {
          let color = 'var(--text-muted)';
          if (log.status === 'success') color = 'var(--alpha-green)';
          if (log.status === 'warning') color = 'var(--alpha-amber)';
          if (log.status === 'error') color = 'var(--alpha-red)';
          if (log.status === 'info') color = 'var(--alpha-cyan)';
          
          return (
            <div key={log.id} style={{ display: 'flex', gap: '0.75rem' }}>
              <span style={{ color: 'rgba(255,255,255,0.3)' }}>[{log.time}]</span>
              <span style={{ color }}>{log.text}</span>
            </div>
          );
        })}
        <div style={{ 
          marginTop: 'auto', 
          borderTop: '1px solid rgba(0, 255, 255, 0.2)',
          paddingTop: '0.5rem',
          color: 'var(--alpha-cyan)'
        }}>
          &gt; STATUS: IDLE
        </div>
      </div>
    </motion.div>
  );
};

export default ActivityMonitor;
