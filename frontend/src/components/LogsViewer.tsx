import { useState, useEffect } from 'react';
import { APIClient } from '../api/client';
import './Diagnostics.css';

export function LogsViewer() {
  const [logs, setLogs] = useState<string[]>([]);
  const [service, setService] = useState('backend');

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const data = await APIClient.request(`/system/logs?service=${service}&lines=50`);
        if (data.lines) setLogs(data.lines);
        else if (data.error) setLogs([`Error: ${data.error}`]);
      } catch (err) {
        setLogs(["Failed to fetch logs."]);
      }
    };
    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, [service]);

  return (
    <div className="logs-viewer">
      <div className="logs-header">
        <h3>Logs Viewer</h3>
        <select value={service} onChange={(e) => setService(e.target.value)} className="service-select">
          <option value="backend">Backend</option>
          <option value="diagnostics">Diagnostics</option>
          <option value="system">System</option>
        </select>
      </div>
      <div className="logs-container">
        {logs.length === 0 ? (
          <div className="no-logs">No logs available.</div>
        ) : (
          logs.map((log, idx) => (
            <div key={idx} className={`log-line ${log.includes('ERROR') ? 'log-error' : log.includes('WARN') ? 'log-warn' : 'log-info'}`}>
              {log}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
