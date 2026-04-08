import React, { useEffect, useState } from "react";
import api from "../services/api";

export default function Users() {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    api.get("/api/users/")
      .then((res) => {
        setUsers(res.data);
      })
      .catch((err) => {
        console.error("Error:", err);
      });
  }, []);

  return (
    <div className="animate-in">
      <h1 style={{ color: "white", marginBottom: "20px" }}>Users</h1>

      <div className="card">
        <table style={{ width: "100%", color: "white" }}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Email</th>
            </tr>
          </thead>

          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.id}</td>
                <td>{user.username}</td>
                <td>{user.email}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}