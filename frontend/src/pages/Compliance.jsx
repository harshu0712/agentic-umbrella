import React, { useState, useEffect } from 'react';
import { ShieldCheck, FileKey, CheckCircle2, XCircle } from 'lucide-react';
import api from '../services/api';

export default function Compliance() {
  const [checks, setChecks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchComplianceChecks();
  }, []);

  const fetchComplianceChecks = async () => {
    try {
      setLoading(true);
      const res = await api.get('/compliance/checks/');
      setChecks(res.data.results || res.data);
    } catch (err) {
      console.error('Error fetching compliance checks:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-in">
      <header className="page-header">
        <h1>Compliance Engine</h1>
        <p>Pre-payroll validation and HMRC strictness checks (Module 6)</p>
      </header>

      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <h3 className="card-title">
            <ShieldCheck color="var(--primary-light)" />
            Run Validation Validation
          </h3>
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '16px' }}>
          Manually trigger a compliance check for a specific Work Record before executing payroll.
        </p>
        <div style={{ display: 'flex', gap: '10px' }}>
          <input 
            type="text" 
            className="form-input" 
            placeholder="Work Record UUID..." 
            style={{ maxWidth: '300px' }}
          />
          <button className="btn btn-primary">Run Suite</button>
        </div>
      </div>

      <div className="table-container">
        <div className="table-header">
          <h3>Recent Validations</h3>
        </div>
        
        {loading ? (
          <div className="loading-spinner"><div className="spinner"></div></div>
        ) : checks.length === 0 ? (
          <div className="empty-state">
            <FileKey />
            <h3>No compliance checks yet</h3>
            <p>Runs automatically before payroll dispersement.</p>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Work Record</th>
                <th>Contractor</th>
                <th>Issues</th>
                <th>Result</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {checks.map((check) => (
                <tr key={check.id}>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    {new Date(check.checked_at).toLocaleDateString()}
                  </td>
                  <td><span style={{ fontFamily: 'monospace' }}>{check.work_record_display}</span></td>
                  <td>{check.contractor_email}</td>
                  <td>
                    {check.failed_checks_count > 0 ? (
                      <span className="badge badge-danger">{check.failed_checks_count} Failed</span>
                    ) : (
                      <span className="badge badge-muted">0</span>
                    )}
                  </td>
                  <td>
                    {check.all_passed ? (
                      <span className="badge badge-success"><CheckCircle2 size={12} /> PASSED</span>
                    ) : (
                      <span className="badge badge-danger"><XCircle size={12} /> BLOCKED</span>
                    )}
                  </td>
                  <td>
                    <button className="btn btn-ghost btn-sm">Report</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
