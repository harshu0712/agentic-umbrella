import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, Cpu, User, Filter } from 'lucide-react';
import api from '../services/api';

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchLogs();
    fetchStats();
  }, []);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const res = await api.get('/audit/logs/');
      // API returns paginated response, using results array
      setLogs(res.data.results || []);
    } catch (err) {
      console.error('Error fetching audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await api.get('/audit/logs/stats/');
      setStats(res.data);
    } catch (err) {
      console.error('Error fetching audit stats:', err);
    }
  };

  const getEventBadge = (eventType) => {
    if (eventType.includes('EXCEPTION') || eventType.includes('FAILED')) {
      return <span className="badge badge-danger badge-dot">{eventType}</span>;
    }
    if (eventType.includes('SUBMITTED') || eventType.includes('ASSIGNED')) {
      return <span className="badge badge-warning badge-dot">{eventType}</span>;
    }
    if (eventType.includes('APPROVED') || eventType.includes('RESOLVED') || eventType.includes('PASSED')) {
      return <span className="badge badge-success badge-dot">{eventType}</span>;
    }
    return <span className="badge badge-primary badge-dot">{eventType}</span>;
  };

  return (
    <div className="animate-in">
      <header className="page-header">
        <h1>Audit Trail</h1>
        <p>Immutable system event logs (Module 7)</p>
      </header>

      {/* Quick Stats */}
      {stats && (
        <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
          <div className="stat-card" style={{ padding: '16px' }}>
            <div className="stat-value" style={{ fontSize: '1.4rem' }}>{stats.total_events}</div>
            <div className="stat-label">TOTAL EVENTS (30D)</div>
          </div>
          <div className="stat-card" style={{ padding: '16px' }}>
            <div className="stat-value" style={{ fontSize: '1.4rem' }}>{stats.system_events}</div>
            <div className="stat-label">SYSTEM GENERATED</div>
          </div>
          <div className="stat-card" style={{ padding: '16px' }}>
            <div className="stat-value" style={{ fontSize: '1.4rem' }}>{stats.manual_overrides}</div>
            <div className="stat-label">MANUAL OVERRIDES</div>
          </div>
          <div className="stat-card" style={{ padding: '16px' }}>
            <div className="stat-value" style={{ fontSize: '1.4rem' }}>
              {new Date(stats.last_event_time).toLocaleTimeString([], { hour: '2-digit', minute:'2-digit' })}
            </div>
            <div className="stat-label">LAST EVENT</div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card" style={{ marginBottom: '20px', padding: '16px' }}>
        <div className="filter-bar" style={{ marginBottom: 0 }}>
          <button className="btn btn-outline">
            <Filter size={14} /> Add Filter
          </button>
          <input type="date" className="form-input" style={{ width: '150px' }} />
          <button className="btn btn-ghost" onClick={fetchLogs}>Refresh</button>
        </div>
      </div>

      {/* Table */}
      <div className="table-container">
        {loading ? (
          <div className="loading-spinner"><div className="spinner"></div></div>
        ) : logs.length === 0 ? (
          <div className="empty-state">
            <Activity />
            <h3>No audit logs found</h3>
            <p>The system is exceptionally quiet.</p>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Event Type</th>
                <th>Actor</th>
                <th>Role</th>
                <th>Metadata</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td>{getEventBadge(log.event_type)}</td>
                  <td>
                    {log.actor_email ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <User size={14} style={{ color: 'var(--primary-light)' }} />
                        {log.actor_email}
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)' }}>
                        <Cpu size={14} />
                        SYSTEM
                      </div>
                    )}
                  </td>
                  <td>
                    <span className="badge badge-muted">{log.actor_role}</span>
                  </td>
                  <td>
                    {log.metadata ? (
                      <button className="btn btn-ghost btn-sm" title={JSON.stringify(log.metadata, null, 2)}>
                        View Details
                      </button>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>-</span>
                    )}
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
