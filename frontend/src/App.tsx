import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom'
import AuditPage from './pages/AuditPage'
import QAPage from './pages/QAPage'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <header className="navbar">
          <div className="navbar-brand">
            <span className="brand-icon">⚖️</span>
            <span className="brand-name">LexAudit</span>
            <span className="brand-tagline">Indian Law Compliance</span>
          </div>
          <nav className="navbar-links">
            <NavLink
              to="/audit"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              Compliance Audit
            </NavLink>
            <NavLink
              to="/qa"
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              Grounded Q&amp;A
            </NavLink>
          </nav>
        </header>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/audit" replace />} />
            <Route path="/audit" element={<AuditPage />} />
            <Route path="/qa" element={<QAPage />} />
          </Routes>
        </main>

        <footer className="footer">
          <p>LexAudit · DPDP 2023 &amp; Indian Contract Act 1872 · GDGoC KIIT Hackathon</p>
        </footer>
      </div>
    </BrowserRouter>
  )
}
