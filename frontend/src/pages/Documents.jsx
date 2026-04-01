import React, { useState, useEffect } from 'react';
import { FileText, Download, Filter } from 'lucide-react';
import api from '../services/api';

export default function Documents() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const res = await api.get('/compliance/documents/');
      setDocuments(res.data.results || res.data);
    } catch (err) {
      console.error('Error fetching documents:', err);
    } finally {
      setLoading(false);
    }
  };

  const getTypeBadge = (type) => {
    switch (type) {
      case 'PAYSLIP': return <span className="badge badge-primary">Payslip</span>;
      case 'P45': return <span className="badge badge-warning">P45 Exit</span>;
      case 'P60': return <span className="badge badge-success">P60 Annual</span>;
      default: return <span className="badge badge-muted">{type}</span>;
    }
  };

  return (
    <div className="animate-in">
      <header className="page-header">
        <h1>Statutory Documents</h1>
        <p>HMRC-compliant document generation and retention (Module 6)</p>
      </header>

      <div className="card" style={{ marginBottom: '20px', padding: '16px' }}>
        <div className="filter-bar" style={{ marginBottom: 0 }}>
          <button className="btn btn-outline" disabled>
            <Filter size={14} /> All Types
          </button>
          <select className="form-select" style={{ width: '150px' }}>
            <option>Tax Year: 2025-26</option>
            <option>Tax Year: 2024-25</option>
          </select>
        </div>
      </div>

      <div className="table-container">
        {loading ? (
          <div className="loading-spinner"><div className="spinner"></div></div>
        ) : documents.length === 0 ? (
          <div className="empty-state">
            <FileText />
            <h3>No Documents Generated</h3>
            <p>Documents will appear here after payroll completion.</p>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Generation Date</th>
                <th>Type</th>
                <th>Contractor</th>
                <th>Tax Year</th>
                <th>File Name</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id}>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    {new Date(doc.generated_at).toLocaleString()}
                  </td>
                  <td>{getTypeBadge(doc.document_type)}</td>
                  <td>{doc.contractor_email}</td>
                  <td><span className="badge badge-muted">{doc.tax_year}</span></td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <FileText size={14} color="var(--primary)" />
                      <span style={{ fontSize: '0.8rem' }}>{doc.file_name}</span>
                    </div>
                  </td>
                  <td>
                    {doc.download_url ? (
                      <a 
                        href={doc.download_url} 
                        target="_blank" 
                        rel="noreferrer"
                        className="btn btn-outline btn-sm"
                      >
                        <Download size={14} /> Download PDF
                      </a>
                    ) : (
                      <button className="btn btn-outline btn-sm" disabled>
                        Processing...
                      </button>
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
