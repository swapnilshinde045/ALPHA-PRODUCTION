import React from 'react';
import { Target, CheckCircle2, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';

const StatusPanel = () => {
  const StatRow = ({ label, active }) => (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.8rem' }}>
      <span style={{ fontSize: '0.8rem', letterSpacing: '1px', color: 'var(--text-muted)' }}>{label}</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ 
          fontFamily: 'var(--font-mono)', 
          fontSize: '0.75rem', 
          color: active ? 'var(--alpha-green)' : 'var(--alpha-red)' 
        }}>
          {active ? 'ONLINE' : 'OFFLINE'}
        </span>
        {active ? 
          <CheckCircle2 size={14} color="var(--alpha-green)" /> : 
          <AlertCircle size={14} color="var(--alpha-red)" />
        }
      </div>
    </div>
  );

  return (
    <motion.div 
      className="alpha-panel"
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      <div className="alpha-header">
        <Target size={16} />
        <span>MODULE STATUS</span>
      </div>
      
      <div style={{ marginTop: '1rem' }}>
        <StatRow label="ALPHA CORE" active={true} />
        <StatRow label="MIC SENSOR" active={true} />
        <StatRow label="OLLAMA ENGINE" active={true} />
        <StatRow label="GEMINI API" active={true} />
        <StatRow label="WHATSAPP SYS" active={true} />
        <StatRow label="VISION MOD" active={false} />
      </div>
    </motion.div>
  );
};

export default StatusPanel;
