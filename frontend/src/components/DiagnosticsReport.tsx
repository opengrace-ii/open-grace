import { useState } from 'react';
import { APIClient } from '../api/client';
import './Diagnostics.css';

export function DiagnosticsReport() {
  const [report, setReport] = useState<any>(null);
  const [results, setResults] = useState<any[]>([]);
  const [running, setRunning] = useState(false);

  const runTest = async () => {
    setRunning(true);
    try {
      const data = await APIClient.request('/system/self-test', { method: 'POST' });
      setReport(data);
      if (data.results) setResults(data.results);
    } catch (err) {
      console.error(err);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="diagnostics-report">
      <div className="report-header">
        <div className="report-title-group">
          <h3>Self-Test Engine</h3>
          {report && <span className="report-id">Report {report.report_id}</span>}
        </div>
        <div className="report-actions">
          {report && (
            <>
              <button 
                className="secondary-btn" 
                onClick={() => {
                  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(report, null, 2));
                  const downloadAnchorNode = document.createElement('a');
                  downloadAnchorNode.setAttribute("href", dataStr);
                  downloadAnchorNode.setAttribute("download", `open-grace-diagnostics-${report.report_id}.json`);
                  document.body.appendChild(downloadAnchorNode);
                  downloadAnchorNode.click();
                  downloadAnchorNode.remove();
                }}
                disabled={running}
              >
                Download JSON
              </button>
              <button 
                className="secondary-btn" 
                onClick={() => {
                  if (!report?.summary || !report?.results) {
                    alert("Report data not fully loaded yet.");
                    return;
                  }
                  
                  try {
                    const summary = `*Summary:* ${report.summary.passed}/${report.summary.total} Layers Passed (${report.summary.status})`;
                    const resultsText = report.results.map((r: any) => 
                      `${r.status === 'pass' ? '✅' : r.status === 'warning' ? '⚠️' : '❌'} *Layer ${r.layer}: ${r.name}* - ${r.details}`
                    ).join('\n');
                    
                    const shareText = `*Diagnostics Report ${report.report_id}*\n${summary}\n\n${resultsText}\n\n---\n*Open Grace TaskForge AI* | Intelligence Unleashed`;
                    
                    // Fallback for non-secure contexts (IP access)
                    if (navigator.clipboard && window.isSecureContext) {
                      navigator.clipboard.writeText(shareText).then(() => {
                        alert("Diagnostics report copied to clipboard!");
                      }).catch(err => {
                        console.error('Clipboard API failed, using fallback', err);
                        copyFallback(shareText);
                      });
                    } else {
                      copyFallback(shareText);
                    }
                  } catch (err) {
                    console.error("Failed to format or copy report", err);
                    alert("Error: Could not copy report. Check console for details.");
                  }

                  function copyFallback(text: string) {
                    const textArea = document.createElement("textarea");
                    textArea.value = text;
                    textArea.style.position = "fixed";
                    textArea.style.left = "-9999px";
                    textArea.style.top = "0";
                    document.body.appendChild(textArea);
                    textArea.focus();
                    textArea.select();
                    try {
                      document.execCommand('copy');
                      alert("Diagnostics report copied to clipboard (legacy mode)!");
                    } catch (err) {
                      console.error('Fallback copy failed', err);
                    }
                    document.body.removeChild(textArea);
                  }
                }}
                disabled={running}
              >
                Share Report
              </button>
            </>
          )}
          <button className="run-test-btn" disabled={running} onClick={runTest}>
            {running ? "Running..." : "Run Diagnostics"}
          </button>
        </div>
      </div>
      
      {report && report.summary && (
        <div className="report-summary">
          <div className="summary-stat">
            <span className="stat-label">Total</span>
            <span className="stat-value">{report.summary.total}</span>
          </div>
          <div className="summary-stat">
            <span className="stat-label">Passed</span>
            <span className="stat-value text-green">{report.summary.passed}</span>
          </div>
          <div className="summary-stat">
            <span className="stat-label">Warnings</span>
            <span className="stat-value text-yellow">{report.summary.warnings}</span>
          </div>
          <div className="summary-stat">
            <span className="stat-label">Failed</span>
            <span className="stat-value text-red">{report.summary.failed}</span>
          </div>
        </div>
      )}

      <div className="report-results">
        {results.length === 0 && !running && <p className="no-results-msg">No recent test results. Click run to execute the 7-layer check.</p>}
        {results.map((r, idx) => (
          <div key={idx} className={`report-item status-bg-${r.status === 'pass' ? 'green' : r.status === 'warning' ? 'yellow' : 'red'}`}>
            <span className="layer-badge">Layer {r.layer}</span>
            <span className="layer-name">{r.name}</span>
            <span className="layer-details">{r.details}</span>
            {r.recommendations && r.recommendations.length > 0 && (
              <div className="layer-recommendations">
                <strong>Suggested Actions:</strong>
                <ul>
                  {r.recommendations.map((rec: string, i: number) => <li key={i}>{rec}</li>)}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
