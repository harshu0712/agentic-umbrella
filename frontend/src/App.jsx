import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-dom';
import api from './services/api';

// Components
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AuditLogs from './pages/AuditLogs';
import Exceptions from './pages/Exceptions';
import Compliance from './pages/Compliance';
import Documents from './pages/Documents';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      setIsAuthenticated(true);
    }
    setIsLoading(false);
  }, []);

  if (isLoading) {
    return (
      <div className="loading-spinner">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        <Route 
          path="/login" 
          element={
            !isAuthenticated ? 
              <Login setAuth={setIsAuthenticated} /> : 
              <Navigate to="/" replace />
          } 
        />
        
        <Route 
          path="/" 
          element={
            isAuthenticated ? 
              <Layout setAuth={setIsAuthenticated} /> : 
              <Navigate to="/login" replace />
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="audit" element={<AuditLogs />} />
          <Route path="exceptions" element={<Exceptions />} />
          <Route path="compliance" element={<Compliance />} />
          <Route path="documents" element={<Documents />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
