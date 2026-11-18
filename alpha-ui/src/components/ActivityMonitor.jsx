import React from 'react';
import { Activity } from 'lucide-react';
import { motion } from 'framer-motion';

const ActivityMonitor = ({ logs, orbState }) => {
  // Show only the last 15 logs in the quick monitor
  const recentLogs = logs.slice(-15);

  return (
    <motion.div 
      className="alpha-panel"
      style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}
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
        {recentLogs.map(log => {
          let color = 'var(--text-muted)';
          if (log.type === 'success') color = 'var(--alpha-green)';
          if (log.type === 'warning') color = 'var(--alpha-amber)';
          if (log.type === 'error') color = 'var(--alpha-red)';
          if (log.type === 'info') color = 'var(--alpha-cyan)';
          
          return (
            <div key={log.id} style={{ display: 'flex', gap: '0.75rem' }}>
              <span style={{ color: 'rgba(255,255,255,0.3)' }}>[{log.time}]</span>
              <span style={{ color }}>
                {log.text.length > 35 ? log.text.substring(0, 35) + '...' : log.text}
              </span>
            </div>
          );
        })}
        <div style={{ 
          marginTop: 'auto', 
          borderTop: '1px solid rgba(0, 255, 255, 0.2)',
          paddingTop: '0.5rem',
          color: 'var(--alpha-cyan)'
        }}>
          &gt; STATE: {orbState.toUpperCase()}
        </div>
      </div>
    </motion.div>
  );
};

export default ActivityMonitor;
