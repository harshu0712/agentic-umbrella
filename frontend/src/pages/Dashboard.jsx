import React, { useState, useEffect } from 'react';
import { 
  Users, 
  FileCheck, 
  AlertOctagon, 
  Banknote,
  Activity
} from 'lucide-react';
import api from '../services/api';

export default function Dashboard() {
  const [stats, setStats] = useState({
    audit_total: 0,
    exceptions_active: 0,
    compliance_passed: 0,
    rti_pending: 0
  });

  const [loading, setLoading] = useState(true);

  // ✅ Fetch data from Django API
  useEffect(() => {
    api.get("/api/dashboard/")
      .then(res => {
        setStats(res.data);
      })
      .catch(err => {
        console.error("API Error:", err);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  // ✅ Loading UI
  if (loading) {
    return (
      <div className="loading-spinner">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="animate-in">
      
      {/* Header */}
      <header className="page-header">
        <h1>Overview</h1>
        <p>Agentic Umbrella Platform Activity</p>
      </header>

      {/* Stats Cards */}
      <div className="stats-grid">
        
        <div className="stat-card">
          <div className="stat-icon info">
            <Activity />
          </div>
          <div className="stat-value">
            {stats.audit_total.toLocaleString()}
          </div>
          <div className="stat-label">AUDIT EVENTS LOGGED</div>
        </div>

        <div className="stat-card">
          <div className="stat-icon danger">
            <AlertOctagon />
          </div>
          <div className="stat-value">
            {stats.exceptions_active}
          </div>
          <div className="stat-label">BLOCKING EXCEPTIONS</div>
        </div>

        <div className="stat-card">
          <div className="stat-icon success">
            <FileCheck />
          </div>
          <div className="stat-value">
            {stats.compliance_passed}%
          </div>
          <div className="stat-label">COMPLIANCE PASS RATE</div>
        </div>

        <div className="stat-card">
          <div className="stat-icon warning">
            <Banknote />
          </div>
          <div className="stat-value">
            {stats.rti_pending}
          </div>
          <div className="stat-label">PENDING RTI SUBMISSIONS</div>
        </div>

      </div>

      {/* Bottom Section */}
      <div className="grid-2">
        
        {/* Recent Activity */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Recent Activity</h3>
          </div>

          <div className="empty-state">
            <Activity />
            <h3>Activity feed coming soon</h3>
            <p>Recent events will be displayed here.</p>
          </div>
        </div>

        {/* Pending Tasks */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Pending Tasks</h3>
          </div>

          <div className="empty-state">
            <Users />
            <h3>All caught up</h3>
            <p>No pending approvals or exceptions.</p>
          </div>
        </div>

      </div>

    </div>
  );
}