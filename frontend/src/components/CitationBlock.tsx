import { CitedPassage } from '../api/client'

interface Props {
  passage: CitedPassage
  index: number
}

export default function CitationBlock({ passage, index }: Props) {
  return (
    <div className="citation-block">
      <div className="citation-meta">
        <span className="citation-tag">Source {index + 1}</span>
        {passage.page_number != null && (
          <span className="citation-tag">Page {passage.page_number}</span>
        )}
        {passage.section_title && (
          <span className="citation-tag">{passage.section_title}</span>
        )}
        <span className="citation-tag" style={{ opacity: 0.7 }}>
          {(passage.relevance_score * 100).toFixed(0)}% match
        </span>
      </div>
      <blockquote className="citation-text">{passage.text}</blockquote>
    </div>
  )
}
