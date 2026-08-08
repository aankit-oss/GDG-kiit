/**
 * Typed API client for LexAudit backend.
 * All calls go through /api (proxied by Vite to localhost:8000).
 */

const BASE = '/api'

/** Base URL for direct fetch calls (e.g. auth, payments). Empty = same origin. */
export const API_BASE = ''

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `Request failed: ${res.status}`)
  }
  return res.json() as Promise<T>
}

// ── Types ────────────────────────────────────────────────────────────────────

export interface UploadResponse {
  doc_id: string
  filename: string
  total_chunks: number
  message: string
}

export interface Document {
  doc_id: string
  filename: string
  file_type: string
  uploaded_at: string
  total_chunks: number
}

export type Verdict = 'PASS' | 'FAIL' | 'NOT_ADDRESSED'
export type Severity = 'HIGH' | 'MEDIUM' | 'LOW'
export type RuleSet = 'dpdp_2023' | 'contract_act_1872'

export interface Finding {
  finding_id: string
  doc_id: string
  rule_id: string
  rule_title: string
  chunk_id: string | null
  verdict: Verdict
  evidence_text: string | null
  reasoning: string
  severity: Severity
  evaluated_at: string
}

export interface AuditReport {
  report_id: string
  doc_id: string
  filename: string
  ruleset: RuleSet
  findings: Finding[]
  generated_at: string
}

export interface CitedPassage {
  chunk_id: string
  text: string
  page_number: number | null
  section_title: string | null
  relevance_score: number
}

export interface QAResponse {
  response_id: string
  doc_id: string
  question: string
  answer: string | null
  cited_passages: CitedPassage[]
  refused: boolean
  refusal_reason: string | null
  answered_at: string
}

export interface RuleSetMeta {
  id: string
  act: string
  act_short: string
  rule_count: number
}

// ── API Calls ────────────────────────────────────────────────────────────────

export const api = {
  /** Upload a PDF/DOCX file and get back a doc_id. */
  uploadDocument(file: File): Promise<UploadResponse> {
    const form = new FormData()
    form.append('file', file)
    return request<UploadResponse>('/documents/upload', { method: 'POST', body: form })
  },

  /** List all uploaded documents. */
  listDocuments(): Promise<Document[]> {
    return request<Document[]>('/documents/')
  },

  /** Run a compliance audit on an uploaded document. */
  runAudit(doc_id: string, ruleset: RuleSet): Promise<AuditReport> {
    return request<AuditReport>('/audit/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ doc_id, ruleset }),
    })
  },

  /** Retrieve a stored audit report. */
  getReport(report_id: string): Promise<AuditReport> {
    return request<AuditReport>(`/audit/${report_id}`)
  },

  /** Ask a grounded question about an uploaded document. */
  askQuestion(doc_id: string, question: string): Promise<QAResponse> {
    return request<QAResponse>('/qa/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ doc_id, question }),
    })
  },

  /** List available rule sets. */
  listRulesets(): Promise<RuleSetMeta[]> {
    return request<RuleSetMeta[]>('/qa/rulesets')
  },
}
