import { useRef, useState } from 'react'

interface Props {
  onUpload: (file: File) => void
  isUploading: boolean
  uploadedFilename?: string
}

export default function FileUpload({ onUpload, isUploading, uploadedFilename }: Props) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase()
    if (!['pdf', 'docx', 'doc'].includes(ext ?? '')) {
      alert('Only PDF and DOCX files are supported.')
      return
    }
    onUpload(file)
  }

  return (
    <div>
      <div
        id="file-upload-zone"
        className={`upload-zone ${dragging ? 'dragging' : ''}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={e => {
          e.preventDefault()
          setDragging(false)
          const file = e.dataTransfer.files[0]
          if (file) handleFile(file)
        }}
        role="button"
        tabIndex={0}
        aria-label="Upload document"
        onKeyDown={e => e.key === 'Enter' && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.doc"
          className="upload-input"
          onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f) }}
          aria-hidden="true"
        />
        {isUploading ? (
          <>
            <div className="spinner" style={{ margin: '0 auto 1rem' }} />
            <p className="upload-title">Parsing document…</p>
            <p className="upload-hint">Extracting text chunks with metadata</p>
          </>
        ) : (
          <>
            <div className="upload-icon">📄</div>
            <p className="upload-title">Drop your document here or click to browse</p>
            <p className="upload-hint">Supports PDF and DOCX · Max 10MB</p>
          </>
        )}
      </div>

      {uploadedFilename && !isUploading && (
        <div className="upload-success">
          <span>✅</span>
          <span>
            <strong>{uploadedFilename}</strong> — ready for analysis
          </span>
        </div>
      )}
    </div>
  )
}
