import { BookOpen, CheckCircle2, Loader2, MessageSquare, Send, Sparkles, X } from 'lucide-react'
import type { FormEvent } from 'react'
import { useEffect, useState } from 'react'
import apiClient from '../../services/apiClient'
import { Button } from '../../components/ui/Button'

type KeyConcept = {
  name: string
  description: string
}

type ExplanationData = {
  id: number
  filename: string
  resume: string
  explanation: string
  takeaways: string[]
  key_concepts: KeyConcept[]
  chunkCount: number
}

type Props = {
  courseId: string
  documentId: string
  filename: string
  open: boolean
  onClose: () => void
  onConceptsUpdated?: () => void
}

type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

export function DocumentExplanationModal({
  courseId,
  documentId,
  filename,
  open,
  onClose,
  onConceptsUpdated,
}: Props) {
  const [data, setData] = useState<ExplanationData | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'resume' | 'explanation' | 'concepts' | 'chat'>('resume')

  // Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: `Hello! I have thoroughly read and analyzed "${filename}". Ask me anything about this material or ask me to explain a specific formula, section, or concept!`,
    },
  ])
  const [inputQuestion, setInputQuestion] = useState('')
  const [chatLoading, setChatLoading] = useState(false)

  useEffect(() => {
    if (!open || !documentId) return
    let active = true
    setLoading(true)

    apiClient
      .get<ExplanationData>(`/courses/${courseId}/documents/${documentId}/explanation`)
      .then((res) => {
        if (active) {
          setData(res.data)
          setLoading(false)
          if (onConceptsUpdated) onConceptsUpdated()
        }
      })
      .catch((err) => {
        console.error('Failed to get document explanation:', err)
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [courseId, documentId, open])

  if (!open) return null

  async function handleSendQuestion(e: FormEvent) {
    e.preventDefault()
    const q = inputQuestion.trim()
    if (!q || chatLoading) return

    const newMessages: ChatMessage[] = [...chatMessages, { role: 'user', content: q }]
    setChatMessages(newMessages)
    setInputQuestion('')
    setChatLoading(true)

    try {
      const res = await apiClient.post<{ answer: string }>(
        `/courses/${courseId}/documents/${documentId}/chat`,
        { question: q }
      )
      setChatMessages([...newMessages, { role: 'assistant', content: res.data.answer }])
    } catch {
      setChatMessages([
        ...newMessages,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an issue retrieving the answer from this document. Please try again.',
        },
      ])
    } finally {
      setChatLoading(false)
    }
  }

  return (
    <div
      className="dialog-backdrop"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <section
        className="dialog document-explanation-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="doc-explanation-title"
        style={{ maxWidth: '820px', width: '92%', maxHeight: '88vh', display: 'flex', flexDirection: 'column' }}
      >
        <div className="dialog-heading">
          <div>
            <span className="eyebrow" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Sparkles size={14} style={{ color: 'var(--coral)' }} /> AI Material Reading & Explanation
            </span>
            <h2 id="doc-explanation-title" style={{ fontSize: '1.4rem', margin: '4px 0 0' }}>
              {filename}
            </h2>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        {loading ? (
          <div style={{ padding: '60px 20px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
            <Loader2 className="spin" size={36} style={{ color: 'var(--forest)' }} />
            <div>
              <strong style={{ display: 'block', fontSize: '1.1rem', marginBottom: '6px' }}>Reading and analyzing document...</strong>
              <span style={{ color: 'var(--ink-muted)', fontSize: '0.9rem' }}>
                StudyMate is parsing pages, extracting key concepts, synthesizing a resume, and preparing explanations.
              </span>
            </div>
          </div>
        ) : (
          <>
            <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--line)', padding: '0 24px', background: 'var(--paper-light)' }}>
              <button
                className={`tab-btn ${activeTab === 'resume' ? 'active' : ''}`}
                onClick={() => setActiveTab('resume')}
                style={{
                  padding: '12px 16px',
                  background: 'none',
                  border: 'none',
                  borderBottom: activeTab === 'resume' ? '2px solid var(--forest)' : '2px solid transparent',
                  fontWeight: activeTab === 'resume' ? 600 : 400,
                  color: activeTab === 'resume' ? 'var(--forest)' : 'var(--ink-muted)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <BookOpen size={16} /> Resume & Takeaways
              </button>
              <button
                className={`tab-btn ${activeTab === 'explanation' ? 'active' : ''}`}
                onClick={() => setActiveTab('explanation')}
                style={{
                  padding: '12px 16px',
                  background: 'none',
                  border: 'none',
                  borderBottom: activeTab === 'explanation' ? '2px solid var(--forest)' : '2px solid transparent',
                  fontWeight: activeTab === 'explanation' ? 600 : 400,
                  color: activeTab === 'explanation' ? 'var(--forest)' : 'var(--ink-muted)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <Sparkles size={16} /> Student Explanation
              </button>
              <button
                className={`tab-btn ${activeTab === 'concepts' ? 'active' : ''}`}
                onClick={() => setActiveTab('concepts')}
                style={{
                  padding: '12px 16px',
                  background: 'none',
                  border: 'none',
                  borderBottom: activeTab === 'concepts' ? '2px solid var(--forest)' : '2px solid transparent',
                  fontWeight: activeTab === 'concepts' ? 600 : 400,
                  color: activeTab === 'concepts' ? 'var(--forest)' : 'var(--ink-muted)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <CheckCircle2 size={16} /> Key Concepts ({data?.key_concepts?.length || 0})
              </button>
              <button
                className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
                onClick={() => setActiveTab('chat')}
                style={{
                  padding: '12px 16px',
                  background: 'none',
                  border: 'none',
                  borderBottom: activeTab === 'chat' ? '2px solid var(--forest)' : '2px solid transparent',
                  fontWeight: activeTab === 'chat' ? 600 : 400,
                  color: activeTab === 'chat' ? 'var(--forest)' : 'var(--ink-muted)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <MessageSquare size={16} /> Ask StudyMate Tutor
              </button>
            </div>

            <div style={{ padding: '24px', overflowY: 'auto', flex: 1, maxHeight: '60vh' }}>
              {activeTab === 'resume' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <div style={{ background: 'var(--paper)', border: '1px solid var(--line)', borderRadius: '12px', padding: '20px' }}>
                    <h3 style={{ fontSize: '1.15rem', color: 'var(--forest)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <BookOpen size={18} /> Document Overview & Executive Resume
                    </h3>
                    <p style={{ lineHeight: 1.7, color: 'var(--ink)', fontSize: '0.98rem', whiteSpace: 'pre-line' }}>
                      {data?.resume || 'No summary available for this file.'}
                    </p>
                  </div>

                  {data?.takeaways && data.takeaways.length > 0 && (
                    <div style={{ background: '#f5f8f5', border: '1px solid #d4e5d4', borderRadius: '12px', padding: '20px' }}>
                      <h4 style={{ fontSize: '1.05rem', color: 'var(--forest)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <CheckCircle2 size={18} style={{ color: 'var(--forest)' }} /> Core Takeaways to Remember
                      </h4>
                      <ul style={{ paddingLeft: '20px', margin: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {data.takeaways.map((point, idx) => (
                          <li key={idx} style={{ lineHeight: 1.6, color: 'var(--ink)', fontSize: '0.95rem' }}>
                            {point}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'explanation' && (
                <div style={{ background: 'var(--paper)', border: '1px solid var(--line)', borderRadius: '12px', padding: '24px' }}>
                  <h3 style={{ fontSize: '1.2rem', color: 'var(--forest)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Sparkles size={20} style={{ color: 'var(--coral)' }} /> Plain-English Concept Breakdown & Guide
                  </h3>
                  <div style={{ lineHeight: 1.8, color: 'var(--ink)', fontSize: '1rem', whiteSpace: 'pre-line' }}>
                    {data?.explanation || 'No detailed explanation generated.'}
                  </div>
                </div>
              )}

              {activeTab === 'concepts' && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
                  {data?.key_concepts?.map((kc, idx) => (
                    <div
                      key={idx}
                      style={{
                        background: 'var(--paper)',
                        border: '1px solid var(--line)',
                        borderRadius: '10px',
                        padding: '16px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '6px',
                      }}
                    >
                      <strong style={{ fontSize: '1.05rem', color: 'var(--forest)' }}>{kc.name}</strong>
                      <p style={{ margin: 0, color: 'var(--ink-muted)', fontSize: '0.9rem', lineHeight: 1.5 }}>
                        {kc.description}
                      </p>
                    </div>
                  ))}
                  {(!data?.key_concepts || data.key_concepts.length === 0) && (
                    <p style={{ color: 'var(--ink-muted)' }}>No explicit concepts found in this document.</p>
                  )}
                </div>
              )}

              {activeTab === 'chat' && (
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: '360px', gap: '12px' }}>
                  <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', paddingRight: '6px' }}>
                    {chatMessages.map((msg, index) => (
                      <div
                        key={index}
                        style={{
                          display: 'flex',
                          justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                        }}
                      >
                        <div
                          style={{
                            maxWidth: '80%',
                            padding: '12px 16px',
                            borderRadius: '14px',
                            background: msg.role === 'user' ? 'var(--forest)' : 'var(--paper)',
                            color: msg.role === 'user' ? '#fff' : 'var(--ink)',
                            border: msg.role === 'user' ? 'none' : '1px solid var(--line)',
                            fontSize: '0.94rem',
                            lineHeight: 1.6,
                            whiteSpace: 'pre-line',
                          }}
                        >
                          {msg.content}
                        </div>
                      </div>
                    ))}
                    {chatLoading && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--ink-muted)', fontSize: '0.9rem', padding: '8px' }}>
                        <Loader2 className="spin" size={16} /> StudyMate is reading the PDF and answering...
                      </div>
                    )}
                  </div>

                  <form onSubmit={handleSendQuestion} style={{ display: 'flex', gap: '10px', marginTop: 'auto' }}>
                    <input
                      style={{
                        flex: 1,
                        padding: '10px 14px',
                        borderRadius: '8px',
                        border: '1px solid var(--line)',
                        background: 'var(--paper)',
                        fontSize: '0.94rem',
                        outline: 'none',
                      }}
                      placeholder="Ask any question about this PDF..."
                      value={inputQuestion}
                      onChange={(e) => setInputQuestion(e.target.value)}
                    />
                    <Button type="submit" disabled={chatLoading || !inputQuestion.trim()}>
                      <Send size={16} /> Ask
                    </Button>
                  </form>
                </div>
              )}
            </div>

            <div style={{ padding: '16px 24px', borderTop: '1px solid var(--line)', display: 'flex', justifyContent: 'flex-end', background: 'var(--paper-light)' }}>
              <Button type="button" onClick={onClose}>
                Done
              </Button>
            </div>
          </>
        )}
      </section>
    </div>
  )
}
