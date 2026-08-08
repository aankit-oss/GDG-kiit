import { BrowserRouter, Routes, Route, NavLink, Navigate, useNavigate } from "react-router-dom";
import AuditPage from "./pages/AuditPage";
import QAPage from "./pages/QAPage";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import PricingPage from "./pages/PricingPage";
import AdminPage from "./pages/AdminPage";
import { useAuthStore } from "./store/authStore";

function Navbar() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const planColors: Record<string, string> = {
    free: "plan-badge-free",
    pro: "plan-badge-pro",
    enterprise: "plan-badge-enterprise",
  };

  return (
    <header className="navbar">
      <div className="navbar-brand">
        <span className="brand-icon">⚖️</span>
        <span className="brand-name">LexAudit</span>
        <span className="brand-tagline">Indian Law Compliance</span>
      </div>

      <nav className="navbar-links">
        <NavLink to="/audit" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
          Compliance Audit
        </NavLink>
        <NavLink to="/qa" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
          Grounded Q&amp;A
          <span className="nav-badge">🌐 Multilingual</span>
        </NavLink>
        <NavLink to="/pricing" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
          Pricing
        </NavLink>
        {user?.is_admin && (
          <NavLink to="/admin" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
            Admin
          </NavLink>
        )}
      </nav>

      <div className="navbar-auth">
        {user ? (
          <>
            <span className={`plan-pill ${planColors[user.plan] ?? ""}`}>{user.plan}</span>
            <span className="nav-email" title={user.email}>
              {user.full_name || user.email}
            </span>
            <button className="btn-logout" onClick={handleLogout}>
              Sign Out
            </button>
          </>
        ) : (
          <>
            <NavLink to="/login" className="btn-nav-login">Sign In</NavLink>
            <NavLink to="/signup" className="btn-nav-signup">Get Started</NavLink>
          </>
        )}
      </div>
    </header>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Navbar />

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/audit" replace />} />
            <Route path="/audit" element={<AuditPage />} />
            <Route path="/qa" element={<QAPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </main>

        <footer className="footer">
          <p>LexAudit · DPDP 2023 &amp; Indian Contract Act 1872 · GDGoC KIIT</p>
        </footer>
      </div>
    </BrowserRouter>
  );
}
