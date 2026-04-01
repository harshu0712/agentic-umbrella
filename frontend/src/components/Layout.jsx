import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Activity, 
  AlertTriangle, 
  ShieldCheck, 
  FileText,
  LogOut
} from 'lucide-react';

export default function Layout({ setAuth }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setAuth(false);
    navigate('/login');
  };

  return (
    <div className="app-layout">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>Agentic Umbrella</h1>
          <span>Platform OS</span>
        </div>

        <nav className="sidebar-section">
          <div className="sidebar-section-title">Core Modules</div>
          
          <NavLink to="/" end className={({isActive}) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <LayoutDashboard />
            Overview
          </NavLink>
          
          <NavLink to="/audit" className={({isActive}) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <Activity />
            Audit Logs
          </NavLink>
          
          <NavLink to="/exceptions" className={({isActive}) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <AlertTriangle />
            Exceptions
          </NavLink>
          
          <NavLink to="/compliance" className={({isActive}) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <ShieldCheck />
            Compliance Checks
          </NavLink>

          <NavLink to="/documents" className={({isActive}) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <FileText />
            Statutory Documents
          </NavLink>
        </nav>

        {/* User / Settings Footer (placeholder) */}
        <div style={{ marginTop: 'auto', padding: '12px' }}>
          <button 
            type="button" 
            className="sidebar-link" 
            style={{ width: '100%', border: 'none', background: 'transparent', textAlign: 'left' }}
            onClick={handleLogout}
          >
            <LogOut color="var(--danger)" />
            <span style={{ color: 'var(--danger)' }}>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
