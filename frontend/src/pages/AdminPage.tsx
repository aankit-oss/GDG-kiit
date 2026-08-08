import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import { API_BASE } from "../api/client";

interface Stats {
  total_users: number;
  active_users: number;
  free_users: number;
  pro_users: number;
  enterprise_users: number;
  total_audits_this_month: number;
  total_qa_this_month: number;
}

interface UserRow {
  user_id: number;
  email: string;
  full_name: string;
  plan: string;
  is_active: boolean;
  is_admin: boolean;
  audits_this_month: number;
  qa_this_month: number;
  joined: string;
}

export default function AdminPage() {
  const navigate = useNavigate();
  const { token, user } = useAuthStore();
  const [stats, setStats] = useState<Stats | null>(null);
  const [users, setUsers] = useState<UserRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState("");

  useEffect(() => {
    if (!user?.is_admin) {
      navigate("/audit");
      return;
    }
    fetchAll();
  }, []);

  async function fetchAll() {
    setLoading(true);
    const headers = { Authorization: `Bearer ${token}` };
    const [statsRes, usersRes] = await Promise.all([
      fetch(`${API_BASE}/api/admin/stats`, { headers }),
      fetch(`${API_BASE}/api/admin/users`, { headers }),
    ]);
    if (statsRes.ok) setStats(await statsRes.json());
    if (usersRes.ok) setUsers(await usersRes.json());
    setLoading(false);
  }

  async function updatePlan(userId: number, plan: string) {
    const res = await fetch(`${API_BASE}/api/admin/users/${userId}/plan?plan=${plan}`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      setActionMsg(`Updated user ${userId} to ${plan}`);
      fetchAll();
    }
  }

  async function deactivateUser(userId: number) {
    if (!confirm("Deactivate this user?")) return;
    const res = await fetch(`${API_BASE}/api/admin/users/${userId}/deactivate`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      setActionMsg(`User ${userId} deactivated`);
      fetchAll();
    }
  }

  if (loading) return <div className="loading-spinner">Loading admin dashboard…</div>;

  return (
    <div className="admin-page">
      <h1 className="admin-title">🛡️ Admin Dashboard</h1>
      {actionMsg && <div className="admin-msg">{actionMsg}</div>}

      {/* Stats grid */}
      {stats && (
        <div className="stats-grid">
          {[
            { label: "Total Users", value: stats.total_users },
            { label: "Active Users", value: stats.active_users },
            { label: "Free Plan", value: stats.free_users },
            { label: "Pro Plan", value: stats.pro_users },
            { label: "Enterprise", value: stats.enterprise_users },
            { label: "Audits This Month", value: stats.total_audits_this_month },
            { label: "Q&A This Month", value: stats.total_qa_this_month },
          ].map((s) => (
            <div key={s.label} className="stat-card">
              <div className="stat-value">{s.value}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Users table */}
      <div className="admin-section">
        <h2>Users ({users.length})</h2>
        <div className="table-wrapper">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Email</th>
                <th>Name</th>
                <th>Plan</th>
                <th>Audits</th>
                <th>Q&A</th>
                <th>Joined</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.user_id} className={!u.is_active ? "row-inactive" : ""}>
                  <td>{u.user_id}</td>
                  <td>{u.email}</td>
                  <td>{u.full_name || "—"}</td>
                  <td>
                    <span className={`plan-badge plan-${u.plan}`}>{u.plan}</span>
                  </td>
                  <td>{u.audits_this_month}</td>
                  <td>{u.qa_this_month}</td>
                  <td>{u.joined}</td>
                  <td>{u.is_active ? "Active" : "Inactive"}</td>
                  <td className="action-cell">
                    <select
                      value={u.plan}
                      onChange={(e) => updatePlan(u.user_id, e.target.value)}
                      className="plan-select"
                    >
                      <option value="free">Free</option>
                      <option value="pro">Pro</option>
                      <option value="enterprise">Enterprise</option>
                    </select>
                    {u.is_active && !u.is_admin && (
                      <button
                        className="btn-danger-sm"
                        onClick={() => deactivateUser(u.user_id)}
                      >
                        Deactivate
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
