import React from 'react';
import Navbar from './components/Navbar';
import LocationPanel from './components/LocationPanel';
import SystemStatusPanel from './components/SystemStatusPanel';
import ActivityMonitor from './components/ActivityMonitor';
import SystemInfoPanel from './components/SystemInfoPanel';
import StatusPanel from './components/StatusPanel';
import GreetingBanner from './components/GreetingBanner';
import SystemLog from './components/SystemLog';
import OrbScene from './components/OrbScene';
import './App.css';

function App() {
  return (
    <div className="alpha-dashboard">
      <Navbar />
      
      <main className="dashboard-grid">
        {/* Left Column */}
        <div className="side-col left-col">
          <LocationPanel />
          <SystemStatusPanel />
          <ActivityMonitor />
        </div>

        {/* Center Hero/Orb Area */}
        <div className="center-col">
          <div className="orb-container">
            <OrbScene />
          </div>
          <GreetingBanner />
        </div>

        {/* Right Column */}
        <div className="side-col right-col">
          <SystemInfoPanel />
          <StatusPanel />
          <SystemLog />
        </div>
      </main>
    </div>
  );
}

export default App;
