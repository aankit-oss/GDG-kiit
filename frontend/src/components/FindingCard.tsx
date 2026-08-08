import { useState } from 'react'
import { Finding, Verdict } from '../api/client'

interface Props {
  finding: Finding
}

const VERDICT_LABEL: Record<Verdict, string> = {
  PASS: '✓ Pass',
  FAIL: '✗ Fail',
  NOT_ADDRESSED: '— Not Addressed',
}
const VERDICT_CLASS: Record<Verdict, string> = {
  PASS: 'pass',
  FAIL: 'fail',
  NOT_ADDRESSED: 'na',
}
const BADGE_CLASS: Record<Verdict, string> = {
  PASS: 'badge-pass',
  FAIL: 'badge-fail',
  NOT_ADDRESSED: 'badge-na',
}

export default function FindingCard({ finding }: Props) {
  const [expanded, setExpanded] = useState(finding.verdict === 'FAIL')
  const cls = VERDICT_CLASS[finding.verdict]

  return (
    <div className={`finding-card ${cls}`} id={`finding-${finding.rule_id}`}>
      <div
        className="finding-header"
        onClick={() => setExpanded(v => !v)}
        role="button"
        tabIndex={0}
        aria-expanded={expanded}
        onKeyDown={e => e.key === 'Enter' && setExpanded(v => !v)}
      >
        <div className="flex-col gap-sm" style={{ flex: 1 }}>
          <div className="finding-meta">
            <span className="finding-id">{finding.rule_id}</span>
            <span className={`badge ${BADGE_CLASS[finding.verdict]}`}>
              {VERDICT_LABEL[finding.verdict]}
            </span>
            <span className={`badge badge-${finding.severity.toLowerCase()}`}>
              {finding.severity}
            </span>
          </div>
          <span className="finding-title">{finding.rule_title}</span>
        </div>
        <span className={`chevron ${expanded ? 'open' : ''}`} aria-hidden="true">▾</span>
      </div>

      {expanded && (
        <div className="finding-body">
          {finding.evidence_text ? (
            <div className="evidence-block">
              <div className="evidence-label">Evidence from document</div>
              {finding.evidence_text}
            </div>
          ) : (
            <div className="text-muted mt-sm">No relevant clause found in the document.</div>
          )}
          {finding.reasoning && (
            <p className="reasoning-text">
              <strong style={{ color: 'var(--text-secondary)' }}>Reasoning: </strong>
              {finding.reasoning}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
