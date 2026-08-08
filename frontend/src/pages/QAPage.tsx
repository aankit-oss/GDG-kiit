import { useState } from 'react'
import { api, QAResponse } from '../api/client'
import FileUpload from '../components/FileUpload'
import CitationBlock from '../components/CitationBlock'

type Status = 'idle' | 'uploading' | 'describing' | 'uploaded' | 'asking' | 'done' | 'error'

interface DocDescription {
  doc_id: string
  filename: string
  chunk_count: number
  summary: string
  topics: string[]
  suggested_questions: string[]
}

export default function QAPage() {
  const [status, setStatus] = useState<Status>('idle')
  const [docId, setDocId] = useState<string | null>(null)
  const [filename, setFilename] = useState<string>('')
  const [question, setQuestion] = useState<string>('')
  const [response, setResponse] = useState<QAResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [description, setDescription] = useState<DocDescription | null>(null)

  const handleUpload = async (file: File) => {
    setStatus('uploading')
    setError(null)
    setResponse(null)
    setDescription(null)
    try {
      const res = await api.uploadDocument(file)
      setDocId(res.doc_id)
      setFilename(res.filename)

      // Auto-describe the document after upload
      setStatus('describing')
      try {
        const desc = await fetch(`/api/qa/describe/${res.doc_id}`)
        if (desc.ok) {
          setDescription(await desc.json())
        }
      } catch {
        // Description is optional — don't block Q&A if it fails
      }

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

  const useSuggested = (q: string) => {
    setQuestion(q)
  }

  const isAsking = status === 'asking'
  const canAsk = (status === 'uploaded' || status === 'done') && question.trim().length > 3

  return (
    <div className="flex-col gap-lg">
      <div className="page-header">
        <h1 className="page-title">Grounded Q&amp;A</h1>
        <p className="page-subtitle">
          Ask any question about your document — in any language.
          Answers are grounded only in the document; the system will refuse rather than guess.
        </p>
      </div>

      {/* Upload */}
      <div className="card flex-col gap-md">
        <FileUpload
          onUpload={handleUpload}
          isUploading={status === 'uploading'}
          uploadedFilename={status !== 'idle' && status !== 'uploading' ? filename : undefined}
        />

        {/* Describing spinner */}
        {status === 'describing' && (
          <div className="doc-describing">
            <div className="spinner-sm" />
            <span>Analysing document structure…</span>
          </div>
        )}

        {/* Document description card */}
        {description && (status === 'uploaded' || status === 'done' || status === 'asking') && (
          <div className="doc-description-card">
            <div className="doc-desc-header">
              <span className="doc-desc-icon">📄</span>
              <div>
                <p className="doc-desc-title">{description.filename}</p>
                <p className="doc-desc-chunks">{description.chunk_count} passages indexed</p>
              </div>
            </div>

            <p className="doc-desc-summary">{description.summary}</p>

            {description.topics.length > 0 && (
              <div className="doc-topics">
                {description.topics.map(t => (
                  <span key={t} className="topic-chip">{t}</span>
                ))}
              </div>
            )}

            {description.suggested_questions.length > 0 && (
              <div className="suggested-questions">
                <p className="suggested-label">💡 Suggested questions — click to use:</p>
                <div className="suggested-list">
                  {description.suggested_questions.map((q, i) => (
                    <button
                      key={i}
                      className="suggested-btn"
                      onClick={() => useSuggested(q)}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Q&A input */}
        {(status === 'uploaded' || status === 'done') && (
          <div className="flex-col gap-md" style={{ marginTop: '0.5rem' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="question-input">
                Your Question
                <span className="multilingual-hint">🌐 Any language</span>
              </label>
              <textarea
                id="question-input"
                className="textarea"
                placeholder="e.g. What is the data retention period? / डेटा रिटेंशन अवधि क्या है?"
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
                  {description && description.suggested_questions.length > 0 && (
                    <div className="refusal-suggestions">
                      <p className="suggested-label" style={{ marginTop: '0.75rem' }}>
                        Try one of these instead:
                      </p>
                      {description.suggested_questions.map((q, i) => (
                        <button key={i} className="suggested-btn" onClick={() => useSuggested(q)}>
                          {q}
                        </button>
                      ))}
                    </div>
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
