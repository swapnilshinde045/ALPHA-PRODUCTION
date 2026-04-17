import React from 'react';
import { Cpu, Wifi, Battery, Bluetooth, HardDrive } from 'lucide-react';
import { motion } from 'framer-motion';

const SystemStatusPanel = () => {
  
  const StatusItem = ({ icon: Icon, label, value, color }) => (
    <div style={{ 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'space-between',
      padding: '0.6rem 0',
      borderBottom: '1px solid rgba(255,255,255,0.05)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--text-muted)' }}>
        <Icon size={16} />
        <span style={{ fontSize: '0.85rem', letterSpacing: '1px' }}>{label}</span>
      </div>
      <div style={{ 
        fontFamily: 'var(--font-mono)', 
        color: `var(--alpha-${color})`,
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem'
      }}>
        {value}
        <div style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: `var(--alpha-${color})`,
          boxShadow: `0 0 5px var(--alpha-${color})`
        }}></div>
      </div>
    </div>
  );

  return (
    <motion.div 
      className="alpha-panel"
      initial={{ opacity: 0, x: -50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      <div className="alpha-header">
        <Cpu size={16} />
        <span>HARDWARE STATUS</span>
      </div>
      
      <div style={{ marginTop: '0.5rem' }}>
        <StatusItem icon={Battery} label="POWER" value="100% AC" color="green" />
        <StatusItem icon={Wifi} label="NETWORK" value="CONNECTED" color="cyan" />
        <StatusItem icon={Bluetooth} label="BLUETOOTH" value="ACTIVE" color="cyan" />
        <StatusItem icon={HardDrive} label="MEMORY" value="32 GB" color="cyan" />
        <StatusItem icon={Cpu} label="CPU TEMP" value="42°C" color="amber" />
      </div>
    </motion.div>
  );
};

export default SystemStatusPanel;
