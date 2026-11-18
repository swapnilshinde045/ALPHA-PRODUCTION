import React from 'react';
import { motion } from 'framer-motion';
import { Power, Mic, Brain, SkipForward, Ear, Trash2, Settings2 } from 'lucide-react';

const ActionControls = ({ onAction }) => {
  const ActionBtn = ({ icon: Icon, label, action, color }) => (
    <button 
      onClick={() => onAction(action)}
      className="action-btn"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.4rem',
        background: 'rgba(0, 0, 0, 0.4)',
        border: `1px solid var(--alpha-${color})`,
        borderRadius: '6px',
        padding: '0.8rem 0.5rem',
        color: `var(--alpha-${color})`,
        fontFamily: 'var(--font-mono)',
        fontSize: '0.65rem',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        boxShadow: `inset 0 0 10px rgba(0,0,0,0.5)`,
      }}
      onMouseOver={(e) => {
        e.currentTarget.style.background = `rgba(0, 255, 255, 0.1)`;
        e.currentTarget.style.boxShadow = `0 0 10px var(--alpha-${color})`;
      }}
      onMouseOut={(e) => {
        e.currentTarget.style.background = 'rgba(0, 0, 0, 0.4)';
        e.currentTarget.style.boxShadow = `inset 0 0 10px rgba(0,0,0,0.5)`;
      }}
      onMouseDown={(e) => e.currentTarget.style.transform = 'scale(0.95)'}
      onMouseUp={(e) => e.currentTarget.style.transform = 'scale(1)'}
    >
      <Icon size={18} />
      <span>{label}</span>
    </button>
  );

  return (
    <motion.div 
      className="alpha-panel"
      initial={{ opacity: 0, x: -50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: 0.4 }}
    >
      <div className="alpha-header">
        <Settings2 size={16} />
        <span>SYSTEM CONTROLS</span>
      </div>
      
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: '1fr 1fr', 
        gap: '0.75rem', 
        marginTop: '1rem' 
      }}>
        <ActionBtn icon={Power} label="TOGGLE CORE" action="toggle_ALPHA" color="cyan" />
        <ActionBtn icon={Brain} label="TOGGLE AI" action="toggle_ai" color="amber" />
        
        <ActionBtn icon={Mic} label="TOGGLE MIC" action="toggle_mic" color="green" />
        <ActionBtn icon={Ear} label="FORCE LISTEN" action="manual_listen" color="cyan" />
        
        <ActionBtn icon={SkipForward} label="SKIP VOICE" action="skip_current_output" color="amber" />
        <ActionBtn icon={Trash2} label="CLEAR LOGS" action="clear_log" color="red" />
      </div>
    </motion.div>
  );
};

export default ActionControls;
