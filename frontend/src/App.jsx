import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Users from "./pages/Users";

function App() {
  return (
    <div className="app-layout">
      
      <div className="sidebar">
        <Sidebar />
      </div>

      <div className="main-content">
        <Navbar />

        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/users" element={<Users />} />
        </Routes>

      </div>
    </div>
  );
}

export default App;