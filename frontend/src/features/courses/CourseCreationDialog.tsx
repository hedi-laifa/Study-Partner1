import { X } from 'lucide-react'
import type { FormEvent } from 'react'
import { useState } from 'react'
import type { CourseLevel, CourseSubject, CreateCourseInput } from '../../services/contracts/courses'
import { Button } from '../../components/ui/Button'

type Props = {
  open: boolean
  onClose: () => void
  onSubmit: (input: CreateCourseInput) => void
}

const levels: CourseLevel[] = ['Beginner', 'Intermediate', 'Advanced']

const suggestedSubjects = [
  'Computer Science',
  'Deep Learning',
  'Data Science & AI',
  'Statistics',
  'Mathematics',
  'Physics',
  'Biology',
  'Medicine & Health',
  'Engineering',
  'Economics',
  'Business Fundamentals',
  'Psychology',
  'Philosophy',
  'Law',
  'History',
  'Literature',
]

export function CourseCreationDialog({ open, onClose, onSubmit }: Props) {
  const [title, setTitle] = useState('')
  const [subject, setSubject] = useState<CourseSubject>('')
  const [level, setLevel] = useState<CourseLevel>('Beginner')
  const [description, setDescription] = useState('')
  const [error, setError] = useState('')

  if (!open) return null

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (title.trim().length < 3) {
      setError('Give your course a title with at least 3 characters.')
      return
    }
    const finalSubject = subject.trim() || 'General Studies'
    onSubmit({ title: title.trim(), subject: finalSubject, level, description: description.trim() })
    setTitle('')
    setSubject('')
    setDescription('')
    setError('')
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}>
      <section className="dialog course-dialog" role="dialog" aria-modal="true" aria-labelledby="create-course-title">
        <div className="dialog-heading">
          <div>
            <span className="eyebrow">Build your own study path</span>
            <h2 id="create-course-title">Create a course</h2>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close dialog">
            <X size={18} />
          </button>
        </div>
        <form className="course-form" onSubmit={submit}>
          <label>
            Course title
            <input
              autoFocus
              value={title}
              onChange={(event) => { setTitle(event.target.value); setError('') }}
              placeholder="e.g. Distributed Systems & Cloud Infrastructure"
            />
          </label>
          <div className="form-grid">
            <label>
              Field of study
              <input
                list="subject-suggestions"
                value={subject}
                onChange={(event) => setSubject(event.target.value)}
                placeholder="Type any field (e.g. Neuroscience, Law...)"
              />
              <datalist id="subject-suggestions">
                {suggestedSubjects.map((s) => (
                  <option key={s} value={s} />
                ))}
              </datalist>
            </label>
            <label>
              Level
              <select value={level} onChange={(event) => setLevel(event.target.value as CourseLevel)}>
                {levels.map((option) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </label>
          </div>
          <label>
            Optional description
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="What core concepts or topics would you like to master?"
              rows={3}
            />
          </label>
          {error && <p className="form-error" role="alert">{error}</p>}
          <div className="dialog-actions">
            <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
            <Button type="submit">Create course</Button>
          </div>
        </form>
      </section>
    </div>
  )
}
