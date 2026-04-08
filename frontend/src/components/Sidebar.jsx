import { Link } from "react-router-dom";

export default function Sidebar() {
  return (
    <div>
      <div className="sidebar-brand">
        <h1>Umbrella</h1>
        <span>Platform</span>
      </div>

      <div className="sidebar-section">
        <div className="sidebar-section-title">MAIN</div>

        <Link to="/" className="sidebar-link">
          Dashboard 🚀
        </Link>

        <Link to="/users" className="sidebar-link">
          Users 👤
        </Link>
      </div>
    </div>
  );
}