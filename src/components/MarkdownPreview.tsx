import React, { useMemo } from 'react'

interface MarkdownPreviewProps {
  content: string
  className?: string
}

export const MarkdownPreview: React.FC<MarkdownPreviewProps> = ({ content, className = '' }) => {
  const processedContent = useMemo(() => {
    // 마크다운 내용 전처리
    return content
      .replace(/<!--[\s\S]*?-->/g, '') // HTML 주석 제거
      .replace(/\n{3,}/g, '\n\n') // 연속된 빈 줄을 최대 2개로 제한
      .trim()
  }, [content])

  // 간단한 마크다운 파싱 (기본 HTML 변환)
  const parseMarkdown = (text: string): string => {
    return (
      text
        // 헤더 변환
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        // 굵은 글씨
        .replace(/\*\*(.+)\*\*/g, '<strong>$1</strong>')
        // 기울임 글씨
        .replace(/\*(.+)\*/g, '<em>$1</em>')
        // 코드 블록
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        // 인라인 코드
        .replace(/`(.+?)`/g, '<code>$1</code>')
        // 링크
        .replace(
          /\[([^\]]+)\]\(([^)]+)\)/g,
          '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
        )
        // 줄바꿈
        .replace(/\n/g, '<br />')
    )
  }

  return (
    <div className={`markdown-preview ${className}`}>
      <div
        dangerouslySetInnerHTML={{ __html: parseMarkdown(processedContent) }}
        className="prose max-w-none"
      />

      {/* 스타일 오버라이드 */}
      <style>{`
        .markdown-preview {
          line-height: 1.6;
        }
        
        .markdown-preview h1 {
          font-size: 2rem;
          font-weight: bold;
          margin: 1.5rem 0 1rem 0;
          color: #1a202c;
          border-bottom: 2px solid #e2e8f0;
          padding-bottom: 0.5rem;
        }
        
        .markdown-preview h2 {
          font-size: 1.5rem;
          font-weight: 600;
          margin: 1.25rem 0 0.75rem 0;
          color: #2d3748;
        }
        
        .markdown-preview h3 {
          font-size: 1.25rem;
          font-weight: 500;
          margin: 1rem 0 0.5rem 0;
          color: #4a5568;
        }
        
        .markdown-preview p {
          margin-bottom: 1rem;
          color: #4a5568;
          line-height: 1.7;
        }
        
        .markdown-preview code {
          background-color: #f7fafc;
          padding: 0.25rem 0.5rem;
          border-radius: 0.25rem;
          font-family: ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace;
          font-size: 0.875rem;
          color: #e53e3e;
        }
        
        .markdown-preview pre {
          background-color: #1a202c;
          color: #f7fafc;
          padding: 1rem;
          border-radius: 0.5rem;
          overflow-x: auto;
          margin: 1rem 0;
        }
        
        .markdown-preview pre code {
          background-color: transparent;
          color: inherit;
          padding: 0;
        }
        
        .markdown-preview a {
          color: #3182ce;
          text-decoration: underline;
        }
        
        .markdown-preview a:hover {
          color: #2c5282;
        }
        
        .markdown-preview strong {
          font-weight: 600;
          color: #2d3748;
        }
        
        .markdown-preview em {
          font-style: italic;
          color: #4a5568;
        }
        
        .markdown-preview br {
          margin-bottom: 0.5rem;
        }
      `}</style>
    </div>
  )
}
