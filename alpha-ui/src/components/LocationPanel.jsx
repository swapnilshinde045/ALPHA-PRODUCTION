import React, { useState, useEffect } from 'react';
import { MapPin, Navigation } from 'lucide-react';
import { motion } from 'framer-motion';

const LocationPanel = () => {
  return (
    <motion.div 
      className="alpha-panel"
      initial={{ opacity: 0, x: -50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
    >
      <div className="alpha-header">
        <MapPin size={16} />
        <span>LOCATION DATA</span>
      </div>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '1rem' }}>
        <div style={{
          width: '50px', 
          height: '50px', 
          borderRadius: '50%', 
          border: '2px solid var(--alpha-cyan)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'rgba(0, 255, 255, 0.1)'
        }}>
          <Navigation size={24} color="var(--alpha-cyan)" />
        </div>
        
        <div>
          <h2 style={{ 
            fontFamily: 'var(--font-header)', 
            margin: 0, 
            fontSize: '0.85rem',
            letterSpacing: '1px',
            color: 'var(--text-main)',
            maxWidth: '180px',
            lineHeight: '1.2'
          }}>CHH SAMBHAJINAGAR, IN</h2>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.8rem',
            color: 'var(--alpha-cyan)',
            marginTop: '4px'
          }}>
            LAT: 18.5204° N<br/>
            LNG: 73.8567° E
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default LocationPanel;
