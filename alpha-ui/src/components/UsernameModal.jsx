import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Terminal, X } from 'lucide-react';

const UsernameModal = ({ onSubmit, onClose, initialName = '' }) => {
  const [name, setName] = useState(initialName);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && name.trim()) {
      onSubmit(name.trim());
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
          backdropFilter: 'blur(10px)',
          zIndex: 10001,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
        onClick={onClose || undefined}
      >
        <motion.div
          initial={{ scale: 0.9, y: 20 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.9, y: 20 }}
          transition={{ type: 'spring', damping: 20 }}
          className="alpha-panel"
          style={{
            position: 'relative',
            width: '400px',
            maxWidth: '90%',
            padding: '2rem',
            border: '1px solid var(--alpha-cyan)',
            boxShadow: '0 0 30px rgba(0, 255, 255, 0.1), inset 0 0 20px rgba(0, 255, 255, 0.05)',
            textAlign: 'center'
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {onClose && (
            <button
              onClick={onClose}
              style={{
                position: 'absolute',
                top: '12px',
                right: '12px',
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: '4px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: '4px'
              }}
              onMouseOver={(e) => e.currentTarget.style.color = '#fff'}
              onMouseOut={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
            >
              <X size={18} />
            </button>
          )}
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem', color: 'var(--alpha-cyan)' }}>
            <User size={48} />
          </div>
          
          <h2 style={{ 
            fontFamily: 'var(--font-primary)', 
            color: '#fff', 
            letterSpacing: '3px',
            marginBottom: '0.5rem',
            fontSize: '1.2rem'
          }}>
            IDENTIFICATION REQUIRED
          </h2>
          <p style={{ 
            color: 'var(--text-muted)', 
            fontFamily: 'var(--font-mono)', 
            fontSize: '0.8rem',
            marginBottom: '2rem'
          }}>
            ENTER DESIGNATION // A.L.P.H.A CORE
          </p>

          <div style={{ position: 'relative' }}>
            <Terminal size={16} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--alpha-cyan)' }} />
            <input
              autoFocus
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="WHAT SHOULD I CALL YOU?"
              style={{
                width: '100%',
                background: 'rgba(0, 0, 0, 0.5)',
                border: '1px solid rgba(0, 255, 255, 0.3)',
                borderRadius: '4px',
                padding: '1rem 1rem 1rem 2.8rem',
                color: 'var(--alpha-cyan)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.9rem',
                outline: 'none',
                transition: 'all 0.3s ease',
              }}
              onFocus={(e) => e.target.style.boxShadow = '0 0 15px rgba(0,255,255,0.2)'}
              onBlur={(e) => e.target.style.boxShadow = 'none'}
            />
          </div>

          <button
            onClick={() => name.trim() && onSubmit(name.trim())}
            style={{
              marginTop: '1.5rem',
              width: '100%',
              padding: '0.8rem',
              background: 'transparent',
              border: '1px solid var(--alpha-cyan)',
              color: 'var(--alpha-cyan)',
              fontFamily: 'var(--font-mono)',
              letterSpacing: '2px',
              cursor: name.trim() ? 'pointer' : 'not-allowed',
              opacity: name.trim() ? 1 : 0.5,
              transition: 'all 0.2s ease',
              borderRadius: '4px',
            }}
            onMouseOver={(e) => { if(name.trim()) { e.currentTarget.style.background = 'rgba(0,255,255,0.1)'; } }}
            onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
          >
            AUTHORIZE
          </button>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default UsernameModal;
