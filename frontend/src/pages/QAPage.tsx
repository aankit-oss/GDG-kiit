import { useState } from 'react'
import { api, QAResponse } from '../api/client'
import FileUpload from '../components/FileUpload'
import CitationBlock from '../components/CitationBlock'

type Status = 'idle' | 'uploading' | 'uploaded' | 'asking' | 'done' | 'error'

export default function QAPage() {
  const [status, setStatus] = useState<Status>('idle')
  const [docId, setDocId] = useState<string | null>(null)
  const [filename, setFilename] = useState<string>('')
  const [question, setQuestion] = useState<string>('')
  const [response, setResponse] = useState<QAResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleUpload = async (file: File) => {
    setStatus('uploading')
    setError(null)
    setResponse(null)
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

  const handleAsk = async () => {
    if (!docId || !question.trim()) return
    setStatus('asking')
    setResponse(null)
    setError(null)
    try {
      const res = await api.askQuestion(docId, question.trim())
      setResponse(res)
      setStatus('done')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Query failed')
      setStatus('error')
    }
  }

  const isAsking = status === 'asking'
  const canAsk = (status === 'uploaded' || status === 'done') && question.trim().length > 5

  return (
    <div className="flex-col gap-lg">
      <div className="page-header">
        <h1 className="page-title">Grounded Q&amp;A</h1>
        <p className="page-subtitle">
          Ask any question about your document. Answers are grounded only in the document —
          the system will refuse rather than guess if the answer isn't there.
        </p>
      </div>

      {/* Upload */}
      <div className="card flex-col gap-md">
        <FileUpload
          onUpload={handleUpload}
          isUploading={status === 'uploading'}
          uploadedFilename={status !== 'idle' && status !== 'uploading' ? filename : undefined}
        />

        {(status === 'uploaded' || status === 'done') && (
          <div className="flex-col gap-md" style={{ marginTop: '0.5rem' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="question-input">Your Question</label>
              <textarea
                id="question-input"
                className="textarea"
                placeholder="e.g. What is the data retention period stated in this document?"
                value={question}
                onChange={e => setQuestion(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && e.metaKey) handleAsk() }}
                rows={3}
              />
              <p className="text-muted" style={{ fontSize: '0.75rem' }}>
                Press ⌘+Enter to submit
              </p>
            </div>

            <button
              id="ask-question-btn"
              className="btn btn-primary"
              onClick={handleAsk}
              disabled={!canAsk || isAsking}
            >
              {isAsking ? 'Searching document…' : '🔍 Ask Question'}
            </button>
          </div>
        )}
      </div>

      {/* Loading */}
      {status === 'asking' && (
        <div className="card loading-overlay">
          <div className="spinner" />
          <p className="loading-text">Searching document for relevant passages…</p>
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

      {/* Response */}
      {response && (
        <div className="flex-col gap-md" id="qa-response">
          <div className="card flex-col gap-md">
            <div>
              <p className="section-title">Question</p>
              <p style={{ color: 'var(--text-primary)', fontSize: '0.95rem' }}>{response.question}</p>
            </div>

            {response.refused ? (
              /* Explicit Refusal */
              <div className="refusal-banner">
                <span className="refusal-icon">🚫</span>
                <div>
                  <p className="refusal-title" id="refusal-message">
                    This information is not addressed in the provided document.
                  </p>
                  {response.refusal_reason && (
                    <p className="refusal-reason">{response.refusal_reason}</p>
                  )}
                </div>
              </div>
            ) : (
              /* Grounded Answer */
              <>
                <div className="answer-block" id="answer-block">
                  <p className="answer-label">Answer (grounded in document)</p>
                  <p className="answer-text">{response.answer}</p>
                </div>

                {response.cited_passages.length > 0 && (
                  <div className="flex-col gap-sm">
                    <p className="section-title">
                      Source Passages ({response.cited_passages.length})
                    </p>
                    {response.cited_passages.map((p, i) => (
                      <CitationBlock key={p.chunk_id} passage={p} index={i} />
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
