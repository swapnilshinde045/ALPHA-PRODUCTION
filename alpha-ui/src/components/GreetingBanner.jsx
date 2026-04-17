import React from 'react';
import { motion } from 'framer-motion';

const GreetingBanner = () => {
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'GOOD MORNING';
    if (hour < 18) return 'GOOD AFTERNOON';
    return 'GOOD EVENING';
  };

  return (
    <motion.div 
      className="alpha-panel"
      style={{
        position: 'absolute',
        bottom: '20px',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '80%',
        textAlign: 'center',
        background: 'rgba(0, 0, 0, 0.6)',
        borderTop: '2px solid var(--alpha-cyan)',
        backdropFilter: 'blur(20px)'
      }}
      initial={{ opacity: 0, y: 50, x: '-50%' }}
      animate={{ opacity: 1, y: 0, x: '-50%' }}
      transition={{ duration: 0.8, delay: 0.5 }}
    >
      <h2 style={{ 
        fontFamily: 'var(--font-header)',
        letterSpacing: '5px',
        margin: 0,
        fontSize: '1.8rem',
        textShadow: '0 0 10px var(--alpha-cyan)'
      }}>
        {getGreeting()}, SIR.
      </h2>
      <div style={{
        fontFamily: 'var(--font-mono)',
        color: 'var(--alpha-cyan)',
        letterSpacing: '2px',
        marginTop: '0.5rem',
        fontSize: '0.9rem',
        opacity: 0.8
      }}>
        ALL SYSTEMS ONLINE AND MONITORING. AWAITING YOUR COMMAND.
      </div>
    </motion.div>
  );
};

export default GreetingBanner;
