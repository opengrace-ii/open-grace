import { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, RotateCcw, ChevronDown, ChevronUp, Terminal } from 'lucide-react';
import { APIClient } from '../api/client';
import './Diagnostics.css';

interface CrashReport {
  id: string;
  timestamp: string;
  url: string;
  method: string;
  error: string;
  traceback: string;
  request_body?: string;
  system_state?: any;
}

export function CrashHistory() {
  const [reports, setReports] = useState<CrashReport[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [replayingId, setReplayingId] = useState<string | null>(null);

  const fetchReports = async () => {
    try {
      const data = await APIClient.request('/system/crash-reports');
      setReports(data || []);
    } catch (err) {
      console.error("Failed to fetch crash reports", err);
    }
  };

  useEffect(() => {
    fetchReports();
    const interval = setInterval(fetchReports, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleReplay = async (id: string) => {
    setReplayingId(id);
    try {
      const result = await APIClient.request(`/system/crash-reports/${id}/replay`, { method: 'POST' });
      alert(result.message || "Replay initiated");
    } catch (err) {
      alert("Failed to replay crash");
    } finally {
      setReplayingId(null);
    }
  };

  return (
    <div className="crash-history-section">
      <div className="section-header">
        <AlertCircle size={20} className={reports.length > 0 ? "status-red" : "status-green"} />
        <h3>Crash History (Auto-Captured)</h3>
      </div>
      
      <div className="crash-list">
        {reports.length === 0 ? (
          <div className="no-crashes-msg">
            <CheckCircle size={16} className="status-green" />
            <span>No recent system crashes detected. System is stable.</span>
          </div>
        ) : (
          reports.map((report) => (
            <div key={report.id} className={`crash-item ${expandedId === report.id ? 'expanded' : ''}`}>
              <div className="crash-summary" onClick={() => setExpandedId(expandedId === report.id ? null : report.id)}>
                <div className="crash-meta">
                  <span className="crash-id">#{report.id}</span>
                  <span className="crash-time">{new Date(report.timestamp).toLocaleTimeString()}</span>
                  <span className="crash-method">{report.method}</span>
                  <span className="crash-url">{report.url}</span>
                </div>
                <div className="crash-error-text">{report.error}</div>
                <div className="crash-actions">
                  <button 
                    className="replay-btn" 
                    onClick={(e) => { e.stopPropagation(); handleReplay(report.id); }}
                    disabled={replayingId === report.id}
                  >
                    <RotateCcw size={14} className={replayingId === report.id ? 'spinning' : ''} />
                    {replayingId === report.id ? 'Replaying...' : 'Replay'}
                  </button>
                  {expandedId === report.id ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </div>
              </div>
              
              {expandedId === report.id && (
                <div className="crash-details">
                  <div className="detail-block">
                    <div className="block-label"><Terminal size={14} /> Error Stacktrace</div>
                    <pre className="stacktrace">{report.traceback}</pre>
                  </div>
                  
                  {report.request_body && (
                    <div className="detail-block">
                      <div className="block-label">Request Body</div>
                      <pre className="data-block">{report.request_body}</pre>
                    </div>
                  )}
                  
                  {report.system_state && (
                    <div className="detail-block">
                      <div className="block-label">System State at Crash</div>
                      <div className="state-grid">
                        <span>CPU: {report.system_state.cpu}</span>
                        <span>MEM: {report.system_state.memory}</span>
                        <span>API: {report.system_state.api}</span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
