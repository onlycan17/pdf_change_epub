import React, { useCallback, useState, useRef, useEffect, useMemo } from 'react'

interface MarkdownEditorProps {
  content: string
  onChange?: (content: string) => void
  readOnly?: boolean
  className?: string
  placeholder?: string
  autoSave?: boolean
  autoSaveDelay?: number
  onSave?: (content: string) => void
}

export const MarkdownEditor: React.FC<MarkdownEditorProps> = ({
  content,
  onChange,
  readOnly = false,
  className = '',
  placeholder = '마크다운 내용을 입력하세요...',
  autoSave = false,
  autoSaveDelay = 2000,
  onSave,
}) => {
  const [localContent, setLocalContent] = useState(content)
  const [lastSaved, setLastSaved] = useState<Date | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const autoSaveTimerRef = useRef<NodeJS.Timeout | null>(null)

  // 통계 정보 계산
  const stats = useMemo(() => {
    const words = localContent
      .trim()
      .split(/\s+/)
      .filter(word => word.length > 0)
    const chars = localContent.length
    const lines = localContent.split('\n').length

    return {
      words: words.length,
      characters: chars,
      lines: lines,
      readingTime: Math.ceil(words.length / 200), // 평균 분당 200단어 읽기
    }
  }, [localContent])

  // 외부 content가 변경되면 내부 상태 업데이트
  useEffect(() => {
    if (content !== localContent) {
      setLocalContent(content)
    }
  }, [content, localContent])

  // 자동 저장 기능
  useEffect(() => {
    if (autoSave && onSave) {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current)
      }

      autoSaveTimerRef.current = setTimeout(() => {
        if (localContent !== content) {
          setIsSaving(true)
          onSave(localContent)
          setLastSaved(new Date())
          setIsSaving(false)
        }
      }, autoSaveDelay)
    }

    return () => {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current)
      }
    }
  }, [localContent, autoSave, autoSaveDelay, onSave, content])

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const newContent = e.target.value
      setLocalContent(newContent)
      onChange?.(newContent)
    },
    [onChange]
  )

  const insertMarkdown = useCallback(
    (before: string, after: string = '') => {
      if (!textareaRef.current) return

      const textarea = textareaRef.current
      const start = textarea.selectionStart
      const end = textarea.selectionEnd
      const selectedText = localContent.substring(start, end)
      const newText = before + selectedText + after

      const newContent = localContent.substring(0, start) + newText + localContent.substring(end)

      setLocalContent(newContent)
      onChange?.(newContent)

      // 커서 위치 조정
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.focus()
          textareaRef.current.setSelectionRange(
            start + before.length,
            start + before.length + selectedText.length
          )
        }
      }, 0)
    },
    [localContent, onChange]
  )

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (readOnly) return

      // 단축키 처리
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'b':
            e.preventDefault()
            insertMarkdown('**', '**')
            break
          case 'i':
            e.preventDefault()
            insertMarkdown('*', '*')
            break
          case 'k':
            e.preventDefault()
            insertMarkdown('[', '](url)')
            break
          case 's':
            e.preventDefault()
            if (onSave) {
              onSave(localContent)
              setLastSaved(new Date())
            }
            break
        }
      }
    },
    [readOnly, insertMarkdown, onSave, localContent]
  )

  const handleUndo = useCallback(() => {
    // 실행 취소 기능 (간단한 버전)
    if (textareaRef.current) {
      textareaRef.current.focus()
      document.execCommand('undo')
    }
  }, [])

  const handleRedo = useCallback(() => {
    // 다시 실행 기능 (간단한 버전)
    if (textareaRef.current) {
      textareaRef.current.focus()
      document.execCommand('redo')
    }
  }, [])

  return (
    <div className={`flex flex-col h-full border rounded-lg bg-white shadow-sm ${className}`}>
      {/* 툴바 */}
      <div className="flex items-center gap-1 p-2 border-b bg-gray-50 flex-wrap">
        <div className="flex items-center gap-1">
          <button
            onClick={() => insertMarkdown('**', '**')}
            className="px-2 py-1 text-xs font-bold bg-white border rounded hover:bg-gray-100 transition-colors"
            disabled={readOnly}
            title="굵게 (Ctrl+B)"
          >
            B
          </button>
          <button
            onClick={() => insertMarkdown('*', '*')}
            className="px-2 py-1 text-xs italic bg-white border rounded hover:bg-gray-100 transition-colors"
            disabled={readOnly}
            title="기울임 (Ctrl+I)"
          >
            I
          </button>
          <button
            onClick={() => insertMarkdown('`', '`')}
            className="px-2 py-1 text-xs bg-white border rounded hover:bg-gray-100 font-mono transition-colors"
            disabled={readOnly}
            title="코드"
          >
            코드
          </button>
          <button
            onClick={() => insertMarkdown('[', '](url)')}
            className="px-2 py-1 text-xs bg-white border rounded hover:bg-gray-100 transition-colors"
            disabled={readOnly}
            title="링크 (Ctrl+K)"
          >
            🔗
          </button>
        </div>

        <div className="border-l h-4 mx-1" />

        <div className="flex items-center gap-1">
          <button
            onClick={() => insertMarkdown('# ', '')}
            className="px-2 py-1 text-xs bg-white border rounded hover:bg-gray-100 transition-colors"
            disabled={readOnly}
            title="제목 1"
          >
            H1
          </button>
          <button
            onClick={() => insertMarkdown('## ', '')}
            className="px-2 py-1 text-xs bg-white border rounded hover:bg-gray-100 transition-colors"
            disabled={readOnly}
            title="제목 2"
          >
            H2
          </button>
          <button
            onClick={() => insertMarkdown('### ', '')}
            className="px-2 py-1 text-xs bg-white border rounded hover:bg-gray-100 transition-colors"
            disabled={readOnly}
            title="제목 3"
          >
            H3
          </button>
        </div>

        <div className="border-l h-4 mx-1" />

        <div className="flex items-center gap-1">
          <button
            onClick={() => insertMarkdown('- ', '')}
            className="px-2 py-1 text-xs bg-white border rounded hover:bg-gray-100 transition-colors"
            disabled={readOnly}
            title="목록"
          >
            •
          </button>
          <button
            onClick={() => insertMarkdown('1. ', '')}
            className="px-2 py-1 text-xs bg-white border rounded hover:bg-gray-100 transition-colors"
            disabled={readOnly}
            title="번호 목록"
          >
            1.
          </button>
          <button
            onClick={() => insertMarkdown('> ', '')}
            className="px-2 py-1 text-xs bg-white border rounded hover:bg-gray-100 transition-colors"
            disabled={readOnly}
            title="인용"
          >
            "
          </button>
        </div>

        <div className="border-l h-4 mx-1" />

        <div className="flex items-center gap-1">
          <button
            onClick={handleUndo}
            className="px-2 py-1 text-xs bg-white border rounded hover:bg-gray-100 transition-colors"
            disabled={readOnly}
            title="실행 취소 (Ctrl+Z)"
          >
            ↶
          </button>
          <button
            onClick={handleRedo}
            className="px-2 py-1 text-xs bg-white border rounded hover:bg-gray-100 transition-colors"
            disabled={readOnly}
            title="다시 실행 (Ctrl+Y)"
          >
            ↷
          </button>
        </div>

        {!readOnly && (
          <>
            <div className="border-l h-4 mx-1" />
            <button
              onClick={() => onSave?.(localContent)}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                isSaving ? 'bg-green-500 text-white' : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
              disabled={isSaving}
              title="저장 (Ctrl+S)"
            >
              {isSaving ? '저장 중...' : '저장'}
            </button>
          </>
        )}
      </div>

      {/* 텍스트 에디터 */}
      <div className="flex-1 p-4">
        <textarea
          ref={textareaRef}
          value={localContent}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          className={`w-full h-full resize-none border-none outline-none font-mono text-sm transition-colors ${
            readOnly ? 'bg-gray-50 text-gray-600' : 'bg-white'
          }`}
          placeholder={placeholder}
          disabled={readOnly}
          style={{ minHeight: '300px' }}
        />
      </div>

      {/* 상태 바 */}
      <div className="p-2 bg-gray-100 border-t text-xs text-gray-600">
        <div className="flex justify-between items-center flex-wrap gap-2">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <span className="font-medium">단어:</span>
              <span>{stats.words.toLocaleString()}</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="font-medium">문자:</span>
              <span>{stats.characters.toLocaleString()}</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="font-medium">줄:</span>
              <span>{stats.lines}</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="font-medium">예상 읽기 시간:</span>
              <span>{stats.readingTime}분</span>
            </span>
          </div>
          <div className="flex items-center gap-2">
            {autoSave && lastSaved && (
              <span className="text-green-600">마지막 저장: {lastSaved?.toLocaleTimeString()}</span>
            )}
            <span
              className={`px-2 py-1 rounded text-xs ${
                readOnly ? 'bg-gray-200 text-gray-600' : 'bg-blue-100 text-blue-800'
              }`}
            >
              {readOnly ? '읽기 전용' : '편집 가능'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
