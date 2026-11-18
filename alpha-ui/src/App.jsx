import React, { useState, useEffect, useRef, Suspense } from 'react';
import Navbar from './components/Navbar';
import LocationPanel from './components/LocationPanel';
import SystemStatusPanel from './components/SystemStatusPanel';
import ActivityMonitor from './components/ActivityMonitor';
import SystemInfoPanel from './components/SystemInfoPanel';
import StatusPanel from './components/StatusPanel';
import GreetingBanner from './components/GreetingBanner';
import SystemLog from './components/SystemLog';
import AvatarScene from './components/AvatarScene';
import ActionControls from './components/ActionControls';
import UsernameModal from './components/UsernameModal';
import SettingsModal from './components/SettingsModal';
import UpdateNotification from './components/UpdateNotification';
import './App.css';

function App() {
  const [username, setUsername] = useState(localStorage.getItem('alpha_username') || '');
  const [showSettings, setShowSettings] = useState(false);
  const [showUsernameModal, setShowUsernameModal] = useState(false);
  const [updateInfo, setUpdateInfo] = useState(null);
  const [orbState, setOrbState] = useState('idle');
  const [waveformLevel, setWaveformLevel] = useState(0);
  const [waveformActive, setWaveformActive] = useState(false);
  const [waveformStamp, setWaveformStamp] = useState(0);
  const [logs, setLogs] = useState([{ id: 0, text: 'SYSTEM INITIALIZED. WAITING FOR BACKEND...', type: 'warning', time: new Date().toLocaleTimeString() }]);
  const [backendConnected, setBackendConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    const connectWS = () => {
      const ws = new WebSocket('ws://localhost:8765');
      wsRef.current = ws;
      
      ws.onopen = () => {
        setBackendConnected(true);
        addLog('BACKEND CONNECTION ESTABLISHED.', 'success');
        
        // Sync name immediately if we already have it in localStorage
        const savedName = localStorage.getItem('alpha_username');
        if (savedName) {
          ws.send(JSON.stringify({ type: 'action', action: 'set_username', value: savedName }));
        }
      };
      
      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.type === 'log') {
            addLog(data.text, 'info');
          } else if (data.type === 'state') {
            setOrbState(data.state);
          } else if (data.type === 'waveform') {
            setWaveformLevel(typeof data.level === 'number' ? data.level : 0);
            setWaveformActive(Boolean(data.active));
            setWaveformStamp(Date.now());
          } else if (data.type === 'update_available') {
            setUpdateInfo(data);
            addLog(`UPDATE AVAILABLE: ${data.display_name || data.version}`, 'warning');
          }
        } catch (err) {}
      };
      
      ws.onclose = () => {
        setBackendConnected(false);
        addLog('BACKEND DISCONNECTED. RETRYING...', 'error');
        setTimeout(connectWS, 3000);
      };
    };
    connectWS();
    return () => { if (wsRef.current) wsRef.current.close(); };
  }, []);

  const checkForCloudUpdate = () => {
    fetch('https://alphadesktopassistant.web.app/version.json?t=' + Date.now(), { cache: 'no-store' })
      .then(res => res.json())
      .then(data => {
        const installedVersionCode = 2;
        if (data && Number(data.version_code) > installedVersionCode) {
          setUpdateInfo(data);
          addLog(`NEW BUILD DETECTED ON CLOUD: ${data.display_name}`, 'warning');
        }
      })
      .catch(err => {
        console.warn('Update check probe error:', err);
      });
  };

  useEffect(() => {
    checkForCloudUpdate();
    const t = setTimeout(checkForCloudUpdate, 2500);
    return () => clearTimeout(t);
  }, []);

  const addLog = (text, type = 'info') => {
    setLogs(prev => [...prev, { id: Date.now() + Math.random(), text, type, time: new Date().toLocaleTimeString() }].slice(-50));
  };

  const sendCommand = (text) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'command', text }));
      addLog(`MANUAL CMD: ${text}`, 'warning');
    } else {
      addLog('CANNOT SEND COMMAND. BACKEND OFFLINE.', 'error');
    }
  };

  const sendAction = (action, value = null) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const payload = value ? { type: 'action', action, value } : { type: 'action', action };
      wsRef.current.send(JSON.stringify(payload));
      addLog(`ACTION DEPLOYED: ${action}${value ? ` (${value})` : ''}`, 'success');
    } else {
      addLog('CANNOT SEND ACTION. BACKEND OFFLINE.', 'error');
    }
  };

  const handleNameSubmit = (name) => {
    localStorage.setItem('alpha_username', name);
    setUsername(name);
    addLog(`IDENTITY VERIFIED: ${name.toUpperCase()}`, 'success');
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'action', action: 'set_username', value: name }));
    }
  };

  return (
    <>
      <UpdateNotification 
        updateInfo={updateInfo} 
        onDismiss={() => setUpdateInfo(null)} 
        onAction={sendAction} 
      />
      {(!username || showUsernameModal) && (
        <UsernameModal 
          initialName={username}
          onClose={username ? () => setShowUsernameModal(false) : null}
          onSubmit={(name) => {
            handleNameSubmit(name);
            setShowUsernameModal(false);
          }} 
        />
      )}
      <SettingsModal 
        isOpen={showSettings} 
        onClose={() => setShowSettings(false)} 
        onAction={sendAction}
        username={username}
        onEditUsername={() => {
          setShowSettings(false);
          setShowUsernameModal(true);
        }}
        onCheckUpdate={checkForCloudUpdate}
      />
      <div className="alpha-dashboard">
        <Navbar 
          connected={backendConnected} 
          onOpenSettings={() => setShowSettings(true)} 
          updateAvailable={Boolean(updateInfo)}
          onOpenUpdate={() => setUpdateInfo(updateInfo)}
        />
      
      <main className="dashboard-grid">
        <div className="side-col left-col">
          <LocationPanel />
          <SystemStatusPanel />
          <ActionControls onAction={sendAction} />
          <ActivityMonitor logs={logs} orbState={orbState} />
        </div>

        <div className="center-col">
          <div className="orb-container">
            <Suspense fallback={<div style={{color: 'rgba(0, 255, 255, 0.5)', textAlign: 'center', marginTop: '40%', fontFamily: 'var(--font-mono)', letterSpacing: '2px', animation: 'pulse 2s infinite'}}>INITIALIZING NEURAL AVATAR...</div>}>
              <AvatarScene orbState={orbState} waveformLevel={waveformLevel} waveformActive={waveformActive} waveformStamp={waveformStamp} />
            </Suspense>
          </div>
          <GreetingBanner />
        </div>

        <div className="side-col right-col">
          <SystemInfoPanel />
          <StatusPanel connected={backendConnected} />
          <SystemLog logs={logs} onSendCommand={sendCommand} />
        </div>
      </main>
    </div>
    </>
  );
}

export default App;
