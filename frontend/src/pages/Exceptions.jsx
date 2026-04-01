import React, { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, Clock, ShieldAlert } from 'lucide-react';
import api from '../services/api';

export default function Exceptions() {
  const [exceptions, setExceptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('UNRESOLVED');

  useEffect(() => {
    fetchExceptions();
  }, [activeTab]);

  const fetchExceptions = async () => {
    try {
      setLoading(true);
      // Filter based on tab
      const statusFilter = activeTab === 'UNRESOLVED' ? '' : '?status=RESOLVED';
      const res = await api.get(`/exceptions/${statusFilter}`);
      
      // If UNRESOLVED tab, filter out RESOLVED client-side just in case the API doesn't handle empty filter well
      const data = res.data.results || res.data;
      if (activeTab === 'UNRESOLVED') {
        setExceptions(data.filter(e => e.status !== 'RESOLVED'));
      } else {
        setExceptions(data.filter(e => e.status === 'RESOLVED'));
      }
    } catch (err) {
      console.error('Error fetching exceptions:', err);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'CRITICAL': return <span className="badge badge-danger badge-dot">Critical</span>;
      case 'HIGH': return <span className="badge badge-warning badge-dot" style={{ color: '#f97316' }}>High</span>;
      case 'MEDIUM': return <span className="badge badge-warning badge-dot">Medium</span>;
      case 'LOW': return <span className="badge badge-info badge-dot">Low</span>;
      default: return <span className="badge badge-muted">{severity}</span>;
    }
  };
  
  const getStatusBadge = (status) => {
    switch(status) {
      case 'RAISED': return <span className="badge badge-danger">RAISED</span>;
      case 'ASSIGNED': return <span className="badge badge-warning">ASSIGNED</span>;
      case 'IN_REVIEW': return <span className="badge badge-info">IN REVIEW</span>;
      case 'ESCALATED': return <span className="badge badge-danger">ESCALATED</span>;
      case 'RESOLVED': return <span className="badge badge-success">RESOLVED</span>;
      default: return <span className="badge badge-muted">{status}</span>;
    }
  };

  return (
    <div className="animate-in">
      <header className="page-header">
        <h1>Exception Management</h1>
        <p>Workflow blockers and anomaly resolutions (Module 7)</p>
      </header>

      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'UNRESOLVED' ? 'active' : ''}`}
          onClick={() => setActiveTab('UNRESOLVED')}
        >
          Requires Attention
        </button>
        <button 
          className={`tab ${activeTab === 'RESOLVED' ? 'active' : ''}`}
          onClick={() => setActiveTab('RESOLVED')}
        >
          Resolved
        </button>
      </div>

      <div className="table-container">
        {loading ? (
          <div className="loading-spinner"><div className="spinner"></div></div>
        ) : exceptions.length === 0 ? (
          <div className="empty-state">
            {activeTab === 'UNRESOLVED' ? (
              <>
                <CheckCircle color="var(--success)" />
                <h3>All Clear!</h3>
                <p>There are no unresolved exceptions blocking the platform.</p>
              </>
            ) : (
              <>
                <Clock color="var(--text-muted)" />
                <h3>No History</h3>
                <p>No resolved exceptions found.</p>
              </>
            )}
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Severity</th>
                <th>Title & Description</th>
                <th>Type</th>
                <th>Status</th>
                <th>SLA / Age</th>
                <th>Assignee</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {exceptions.map((exc) => (
                <tr key={exc.id}>
                  <td>{getSeverityBadge(exc.severity)}</td>
                  <td>
                    <div style={{ fontWeight: 600, marginBottom: '4px' }}>{exc.title}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {exc.description || 'No description provided'}
                    </div>
                  </td>
                  <td><span className="badge badge-muted">{exc.exception_type}</span></td>
                  <td>{getStatusBadge(exc.status)}</td>
                  <td>
                    {exc.sla_hours_elapsed > 24 ? (
                      <span className="severity-critical" style={{ fontSize: '0.8rem', fontWeight: 600 }}>
                        <ShieldAlert size={12} style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />
                        {exc.sla_hours_elapsed.toFixed(1)}h
                      </span>
                    ) : (
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {exc.sla_hours_elapsed.toFixed(1)}h
                      </span>
                    )}
                  </td>
                  <td>
                    <span style={{ fontSize: '0.8rem' }}>
                      {exc.assigned_to_email || <span style={{ color: 'var(--text-muted)' }}>Unassigned</span>}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-primary btn-sm">
                      {activeTab === 'UNRESOLVED' ? 'Resolve' : 'View'}
                    </button>
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
