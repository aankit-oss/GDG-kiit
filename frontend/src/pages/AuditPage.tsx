import { useState } from 'react'
import { api, AuditReport, RuleSet } from '../api/client'
import FileUpload from '../components/FileUpload'
import FindingCard from '../components/FindingCard'

const RULESETS: { id: RuleSet; label: string; description: string }[] = [
  {
    id: 'dpdp_2023',
    label: 'DPDP 2023',
    description: 'Digital Personal Data Protection Act, 2023 — 15 rules',
  },
  {
    id: 'contract_act_1872',
    label: 'Contract Act 1872',
    description: 'Indian Contract Act, 1872 — validity rules',
  },
]

type Status = 'idle' | 'uploading' | 'uploaded' | 'auditing' | 'done' | 'error'

export default function AuditPage() {
  const [status, setStatus] = useState<Status>('idle')
  const [docId, setDocId] = useState<string | null>(null)
  const [filename, setFilename] = useState<string>('')
  const [ruleset, setRuleset] = useState<RuleSet>('dpdp_2023')
  const [report, setReport] = useState<AuditReport | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleUpload = async (file: File) => {
    setStatus('uploading')
    setError(null)
    try {
      const res = await api.uploadDocument(file)
      setDocId(res.doc_id)
      setFilename(res.filename)
      setStatus('uploaded')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed')
      setStatus('error')
    }
  }

  const handleAudit = async () => {
    if (!docId) return
    setStatus('auditing')
    setReport(null)
    setError(null)
    try {
      const r = await api.runAudit(docId, ruleset)
      setReport(r)
      setStatus('done')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Audit failed')
      setStatus('error')
    }
  }

  const isAuditing = status === 'auditing'

  return (
    <div className="flex-col gap-lg">
      <div className="page-header">
        <h1 className="page-title">Compliance Audit</h1>
        <p className="page-subtitle">
          Upload a document and check it clause-by-clause against Indian law.
          Every finding includes verbatim evidence from your document.
        </p>
      </div>

      {/* Upload + Config */}
      <div className="card flex-col gap-md">
        <FileUpload
          onUpload={handleUpload}
          isUploading={status === 'uploading'}
          uploadedFilename={status !== 'idle' && status !== 'uploading' ? filename : undefined}
        />

        {(status === 'uploaded' || status === 'done') && (
          <div className="flex-col gap-md" style={{ marginTop: '0.5rem' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="ruleset-select">Rule Set</label>
              <select
                id="ruleset-select"
                className="select"
                value={ruleset}
                onChange={e => setRuleset(e.target.value as RuleSet)}
              >
                {RULESETS.map(rs => (
                  <option key={rs.id} value={rs.id}>
                    {rs.label} — {rs.description}
                  </option>
                ))}
              </select>
            </div>

            <button
              id="run-audit-btn"
              className="btn btn-primary"
              onClick={handleAudit}
              disabled={!docId || isAuditing}
            >
              {isAuditing ? 'Running audit…' : '▶ Run Compliance Audit'}
            </button>
          </div>
        )}
      </div>

      {/* Loading */}
      {status === 'auditing' && (
        <div className="card loading-overlay">
          <div className="spinner" />
          <p className="loading-text">
            Evaluating each clause against the rule library…
          </p>
          <p className="text-muted" style={{ fontSize: '0.8rem' }}>
            This may take up to 60 seconds for large documents.
          </p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="refusal-banner">
          <span className="refusal-icon">⚠️</span>
          <div>
            <p className="refusal-title">Error</p>
            <p className="refusal-reason">{error}</p>
          </div>
        </div>
      )}

      {/* Report */}
      {report && (
        <div className="flex-col gap-md" id="audit-report">
          {/* Summary */}
          <div>
            <p className="section-title">Audit Report — {report.filename}</p>
            <div className="summary-bar">
              <div className="summary-stat pass">
                <div className="number">{report.findings.filter(f => f.verdict === 'PASS').length}</div>
                <div className="label">Passed</div>
              </div>
              <div className="summary-stat fail">
                <div className="number">{report.findings.filter(f => f.verdict === 'FAIL').length}</div>
                <div className="label">Failed</div>
              </div>
              <div className="summary-stat na">
                <div className="number">{report.findings.filter(f => f.verdict === 'NOT_ADDRESSED').length}</div>
                <div className="label">Not Addressed</div>
              </div>
            </div>
          </div>

          {/* Findings */}
          <div className="flex-col gap-sm">
            <p className="section-title">Findings ({report.findings.length} rules evaluated)</p>
            {report.findings.map(f => (
              <FindingCard key={f.finding_id} finding={f} />
            ))}
          </div>

          <p className="text-muted" style={{ fontSize: '0.75rem' }}>
            Report ID: <code style={{ fontFamily: 'JetBrains Mono', fontSize: '0.75rem' }}>{report.report_id}</code> ·{' '}
            Generated: {new Date(report.generated_at).toLocaleString()}
          </p>
        </div>
      )}
    </div>
  )
}
