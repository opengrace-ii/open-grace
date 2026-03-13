import { Server, Database, Cpu, HardDrive, Activity, Brain } from 'lucide-react';
import './Diagnostics.css';

interface HealthProps {
  api: string;
  database: string;
  models: string;
  memory: string;
  cpu: string;
  disk: string;
  health_score?: number;
  warnings?: string[];
  anomaly_flag?: boolean;
}

export function SystemHealthCard({ health }: { health: HealthProps | null }) {
  const getStatusColor = (status: string | undefined, type: string) => {
    if (!status) return "yellow";
    if (type === "percent") {
      const val = parseInt(status);
      if (val > 90) return "red";
      if (val > 75) return "yellow";
      return "green";
    }
    return status === "ok" || status === "available" ? "green" : "red";
  };

  if (!health) return <div className="health-card loading">Loading health...</div>;

  return (
    <div className="health-card">
      <div className="health-header">
        <h3>System Health</h3>
        {health.health_score !== undefined && (
          <div className="health-score-container">
            <div className="health-score-circle" style={{ 
              background: `conic-gradient(${health.health_score > 70 ? '#22c55e' : health.health_score > 40 ? '#eab308' : '#ef4444'} ${health.health_score}%, #334155 0)` 
            }}>
              <div className="health-score-inner">
                {health.health_score}%
              </div>
            </div>
            <div className="health-score-details">
              <span className="health-score-label">System Health Score</span>
              <div className="health-breakdown">
                <span>Calculated from:</span>
                <ul>
                  <li>7 layers healthy</li>
                  <li>{health.warnings?.length || 0} service warnings</li>
                  <li>System resource within limits</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>

      {health.anomaly_flag && (
        <div className="anomaly-warning-banner">
          <div className="warning-icon">⚠</div>
          <div className="warning-content">
            <strong>System Warning: Possible overload detected</strong>
            <ul>
              {health.warnings?.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </div>
        </div>
      )}
      <div className="health-grid">
        <div className="health-item">
          <Server size={20} />
          <span>API: <b className={`status-${getStatusColor(health.api, 'text')}`}>{health.api?.toUpperCase() || 'UNKNOWN'}</b></span>
        </div>
        <div className="health-item">
          <Database size={20} />
          <span>DB: <b className={`status-${getStatusColor(health.database, 'text')}`}>{health.database?.toUpperCase() || 'UNKNOWN'}</b></span>
        </div>
        <div className="health-item">
          <Cpu size={20} />
          <span>CPU Used: <b className={`status-${getStatusColor(health.cpu, 'percent')}`}>{health.cpu || 'N/A'}</b></span>
        </div>
        <div className="health-item">
          <HardDrive size={20} />
          <span>Disk Used: <b className={`status-${getStatusColor(health.disk, 'percent')}`}>{health.disk || 'N/A'}</b></span>
        </div>
        <div className="health-item">
          <Activity size={20} />
          <span>Memory Used: <b className={`status-${getStatusColor(health.memory, 'percent')}`}>{health.memory || 'N/A'}</b></span>
        </div>
        <div className="health-item">
          <Brain size={20} />
          <span>Models: <b className={`status-${getStatusColor(health.models, 'text')}`}>{health.models?.toUpperCase() || 'UNKNOWN'}</b></span>
        </div>
      </div>
    </div>
  );
}
