import React, { useState, useEffect } from 'react';
import { Clock, Info } from 'lucide-react';
import { motion } from 'framer-motion';

const SystemInfoPanel = () => {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const timeString = time.toLocaleTimeString('en-US', { 
    hour12: false, 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  });
  
  const dateString = time.toLocaleDateString('en-US', {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  }).toUpperCase();

  return (
    <motion.div 
      className="alpha-panel"
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
    >
      <div className="alpha-header">
        <Info size={16} />
        <span>SYSTEM INFO</span>
      </div>
      
      <div style={{ textAlign: 'center', margin: '1rem 0' }}>
        <div style={{
          fontFamily: 'var(--font-header)',
          fontSize: '2.5rem',
          color: 'var(--text-main)',
          textShadow: '0 0 15px rgba(0, 255, 255, 0.4)',
          letterSpacing: '4px'
        }}>
          {timeString}
        </div>
        <div style={{
          fontFamily: 'var(--font-mono)',
          color: 'var(--alpha-cyan)',
          letterSpacing: '2px',
          marginTop: '0.25rem',
          fontSize: '0.9rem'
        }}>
          {dateString}
        </div>
      </div>
      
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        marginTop: '1.5rem',
        paddingTop: '1rem',
        borderTop: '1px solid rgba(255,255,255,0.05)',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.8rem'
      }}>
        <div style={{ color: 'var(--text-muted)' }}>UPTIME</div>
        <div style={{ color: 'var(--alpha-cyan)' }}>12:45:02</div>
      </div>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        marginTop: '0.5rem',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.8rem'
      }}>
        <div style={{ color: 'var(--text-muted)' }}>COMMANDS_RUN</div>
        <div style={{ color: 'var(--alpha-cyan)' }}>1,248</div>
      </div>
    </motion.div>
  );
};

export default SystemInfoPanel;
