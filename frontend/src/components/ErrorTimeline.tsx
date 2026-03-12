import { Activity } from 'lucide-react';
import { useEffect, useState } from 'react';
import { APIClient } from '../api/client';
import './Diagnostics.css';

export function ErrorTimeline() {
  const [data, setData] = useState<{ hour: number[], day: number[] } | null>(null);

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTimeline = async () => {
      try {
        const result = await APIClient.request('/system/error-timeline');
        setData(result);
      } catch (err) {
        console.error("Failed to fetch error timeline", err);
      } finally {
        setLoading(false);
      }
    };
    fetchTimeline();
    const interval = setInterval(fetchTimeline, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="error-timeline loading">Loading timeline...</div>;
  if (!data) return <div className="error-timeline no-data">Error Timeline Unavailable</div>;

  const maxHour = Math.max(...data.hour, 1);

  return (
    <div className="error-timeline">
      <div className="timeline-header">
        <Activity size={18} />
        <h4>Error Timeline (Last Hour)</h4>
      </div>
      <div className="timeline-chart">
        {data.hour.map((count, idx) => (
          <div key={idx} className="timeline-bar-wrapper">
            <div 
              className="timeline-bar" 
              style={{ 
                height: `${(count / maxHour) * 90 + 10}%`, 
                backgroundColor: count > 2 ? '#ef4444' : count > 0 ? '#eab308' : '#334155' 
              }}
              title={`${count} errors at T-${(11-idx) * 5}m`}
            ></div>
          </div>
        ))}
      </div>
      <div className="timeline-footer">
        <span className="footer-label">60m ago</span>
        <div className="footer-line"></div>
        <span className="footer-label">Now</span>
      </div>
    </div>
  );
}
