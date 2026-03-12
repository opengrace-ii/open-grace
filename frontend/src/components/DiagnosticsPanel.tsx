import { useState, useEffect } from 'react';
import { SystemHealthCard } from './SystemHealthCard';
import { LogsViewer } from './LogsViewer';
import { DiagnosticsReport } from './DiagnosticsReport';
import { ErrorTimeline } from './ErrorTimeline';
import { CrashHistory } from './CrashHistory';
import { APIClient } from '../api/client';
import './Diagnostics.css';

export function DiagnosticsPanel() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await APIClient.request('/system/health');
        setHealth(data);
      } catch (err) {
        console.error("Health check failed", err);
      }
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="diagnostics-panel">
      <SystemHealthCard health={health} />
      <ErrorTimeline />
      <CrashHistory />
      <DiagnosticsReport />
      <LogsViewer />
    </div>
  );
}
