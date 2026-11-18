import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowUpCircle, ExternalLink, X, Sparkles, ShieldAlert } from 'lucide-react';

const UpdateNotification = ({ updateInfo, onDismiss, onAction }) => {
  if (!updateInfo) return null;

  const handleDownload = () => {
    if (onAction) {
      onAction('open_update_url', updateInfo.download_url);
    } else {
      window.open(updateInfo.download_url, '_blank');
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -50, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -30, scale: 0.95 }}
        transition={{ type: 'spring', damping: 20 }}
        style={{
          position: 'fixed',
          top: '24px',
          right: '24px',
          zIndex: 10002,
          width: '420px',
          maxWidth: 'calc(100vw - 48px)',
          background: 'rgba(10, 14, 22, 0.96)',
          backdropFilter: 'blur(16px)',
          border: '1px solid #00ffff',
          borderRadius: '10px',
          boxShadow: '0 0 35px rgba(0, 255, 255, 0.25), inset 0 0 15px rgba(0, 255, 255, 0.05)',
          padding: '1.25rem',
          color: '#fff',
          fontFamily: 'var(--font-mono)'
        }}
      >
        {/* Top Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.85rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <div style={{
              background: 'rgba(0, 255, 255, 0.15)',
              border: '1px solid #00ffff',
              borderRadius: '6px',
              padding: '0.45rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#00ffff'
            }}>
              <ArrowUpCircle size={22} className="pulsing" />
            </div>
            <div>
              <div style={{
                fontSize: '0.65rem',
                letterSpacing: '1.5px',
                color: '#00ffff',
                fontWeight: 'bold'
              }}>
                SYSTEM UPGRADE DETECTED
              </div>
              <div style={{
                fontFamily: 'var(--font-header)',
                fontSize: '1rem',
                letterSpacing: '1px',
                color: '#fff',
                marginTop: '0.15rem'
              }}>
                {updateInfo.display_name || 'ALPHA v.alpha.03'}
              </div>
            </div>
          </div>

          <button
            onClick={onDismiss}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              padding: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            onMouseOver={(e) => e.currentTarget.style.color = '#fff'}
            onMouseOut={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
          >
            <X size={16} />
          </button>
        </div>

        {/* Version Matrix */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '0.5rem',
          background: 'rgba(0, 0, 0, 0.45)',
          padding: '0.65rem 0.85rem',
          borderRadius: '6px',
          border: '1px solid rgba(0, 255, 255, 0.15)',
          marginBottom: '0.85rem',
          fontSize: '0.7rem'
        }}>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>CURRENT BUILD: </span>
            <span style={{ color: '#ffb700', fontWeight: 'bold' }}>v.alpha.02</span>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>CLOUD BUILD: </span>
            <span style={{ color: '#00ffaa', fontWeight: 'bold' }}>{updateInfo.version || 'v.alpha.03'}</span>
          </div>
        </div>

        {/* Change Notes */}
        {updateInfo.notes && (
          <p style={{
            fontSize: '0.72rem',
            color: 'var(--text-muted)',
            lineHeight: '1.4',
            margin: '0 0 1rem 0',
            borderLeft: '2px solid #00ffff',
            paddingLeft: '0.6rem'
          }}>
            {updateInfo.notes}
          </p>
        )}

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '0.65rem' }}>
          <button
            onClick={handleDownload}
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.45rem',
              background: '#00ffff',
              color: '#000',
              border: 'none',
              borderRadius: '5px',
              padding: '0.65rem 1rem',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.78rem',
              fontWeight: 'bold',
              letterSpacing: '1px',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: '0 0 15px rgba(0, 255, 255, 0.3)'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = '#33ffff';
              e.currentTarget.style.boxShadow = '0 0 22px rgba(0, 255, 255, 0.5)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = '#00ffff';
              e.currentTarget.style.boxShadow = '0 0 15px rgba(0, 255, 255, 0.3)';
            }}
          >
            <span>UPDATE NOW</span>
            <ExternalLink size={14} />
          </button>

          <button
            onClick={onDismiss}
            style={{
              padding: '0.65rem 0.9rem',
              background: 'transparent',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '5px',
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.72rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.5)';
              e.currentTarget.style.color = '#fff';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.2)';
              e.currentTarget.style.color = 'var(--text-muted)';
            }}
          >
            LATER
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default UpdateNotification;
