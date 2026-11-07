import { ArrowRight, BookOpen, Check, ChevronRight, Clock3, Flame, Play, RotateCcw, Target, TrendingUp, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { EmptyState } from '../../components/feedback/EmptyState'
import { ProgressBar } from '../../components/ui/ProgressBar'
import { dashboardService } from '../../services/api-client'
import type { DashboardData } from '../../services/contracts/dashboard'
import { DashboardSkeleton } from './DashboardSkeleton'

function getDynamicDate(): string {
  const now = new Date()
  const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
  const months = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December']
  const dayName = days[now.getDay()]
  const day = now.getDate()
  const month = months[now.getMonth()]
  const startOfYear = new Date(now.getFullYear(), 0, 1)
  const weekNo = Math.ceil(((now.getTime() - startOfYear.getTime()) / 86400000 + startOfYear.getDay() + 1) / 7)
  return `${dayName}, ${day} ${month} · Week ${weekNo}`
}

function getGreeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}

export function DashboardOverview() {
  const navigate = useNavigate()
  const [data, setData] = useState<DashboardData>()
  const [loadError, setLoadError] = useState(false)
  const [recommendationVisible, setRecommendationVisible] = useState(true)

  useEffect(() => {
    let active = true
    void dashboardService.getDashboard()
      .then((dashboard) => { if (active) setData(dashboard) })
      .catch(() => { if (active) setLoadError(true) })
    return () => { active = false }
  }, [])

  if (!data && !loadError) return <DashboardSkeleton />
  if (loadError) return <EmptyState title="Your dashboard could not load" text="Please try again from the home link. No study data was changed." />
  if (!data || data.isFirstTime) return (
    <div className="page-stack">
      <EmptyState
        title={`Welcome, ${data?.greeting.name ?? 'there'}.`}
        text="Your study space is ready. Create your first course, upload a PDF, and start learning."
      />
      <div style={{ display: 'flex', justifyContent: 'center', marginTop: '8px' }}>
        <Link to="/courses" className="button"><Play size={16} fill="currentColor" /> Create your first course</Link>
      </div>
    </div>
  )

  return <DashboardContent data={data} recommendationVisible={recommendationVisible} onDismissRecommendation={() => setRecommendationVisible(false)} onOpenPractice={(conceptId) => navigate(`/study/concept-${conceptId}`)} />
}

type DashboardContentProps = {
  data: DashboardData
  recommendationVisible: boolean
  onDismissRecommendation: () => void
  onOpenPractice: (conceptId: string) => void
}

function DashboardContent({ data, recommendationVisible, onDismissRecommendation, onOpenPractice }: DashboardContentProps) {
  const maxActivity = useMemo(() => Math.max(...data.weeklyActivity.map(({ minutes }) => minutes), 1), [data.weeklyActivity])
  const totalMinutes = data.weeklyActivity.reduce((total, { minutes }) => total + minutes, 0)
  const totalHours = totalMinutes >= 60
    ? `${Math.floor(totalMinutes / 60)}h ${totalMinutes % 60}m`
    : `${totalMinutes}m`

  const firstCourse = data.courses[0]
  const studyLink = firstCourse ? `/study/${firstCourse.id}-next` : '/courses'

  return (
    <div className="home-dashboard">
      <section className="dashboard-lead">
        <div className="lead-copy">
          <span className="eyebrow">{getDynamicDate()}</span>
          <h2>{getGreeting()}, {data.greeting.name}.</h2>
          <p>Let's make your next study hour count. Your current focus is <strong>{data.greeting.focus}</strong>.</p>
          {recommendationVisible && (
            <div className="recommendation">
              <div className="recommendation-mark"><Target size={17} /></div>
              <div>
                <span className="eyebrow">Your next best step</span>
                <strong>{data.greeting.recommendation}</strong>
              </div>
              <button className="recommendation-dismiss" onClick={onDismissRecommendation} aria-label="Dismiss recommendation"><X size={15} /></button>
            </div>
          )}
          <Link to={studyLink} className="button"><Play size={16} fill="currentColor" /> Start a focused session</Link>
        </div>
        <div className="lead-note">
          <span className="lead-note-number">{String(data.streak).padStart(2, '0')}</span>
          <span className="lead-note-label">day<br />streak</span>
          <Flame size={20} />
        </div>
      </section>

      {firstCourse && (
        <section className="continue-learning">
          <div className="continue-heading">
            <div>
              <span className="eyebrow">Pick up where you left off</span>
              <h2>Continue learning</h2>
            </div>
            <Link to={`/courses/${firstCourse.id}`} className="text-link">Course details <ArrowRight size={15} /></Link>
          </div>
          <div className="continue-content">
            <div className={`continue-course-mark ${firstCourse.color}`}>{firstCourse.icon}</div>
            <div className="continue-course-copy">
              <span className="course-tag">{firstCourse.title}</span>
              <h3>{firstCourse.category}</h3>
              <ProgressBar value={firstCourse.progress} />
              <small>{firstCourse.progress}% complete</small>
            </div>
            <Link to={`/study/${firstCourse.id}-next`} className="continue-action">
              <span>Resume lesson</span>
              <ChevronRight size={19} />
            </Link>
          </div>
        </section>
      )}

      <div className="dashboard-columns">
        <div className="dashboard-main-column">
          <section className="dashboard-section recent-courses">
            <div className="section-heading">
              <div>
                <span className="eyebrow">Your active courses</span>
                <h2>Recent courses</h2>
              </div>
              <Link to="/courses" className="text-link">View all <ArrowRight size={15} /></Link>
            </div>
            <div className="editorial-course-list">
              {data.courses.length === 0
                ? <p style={{ color: 'var(--muted)', fontSize: 'var(--text-sm)' }}>No courses yet. <Link to="/courses">Create one to get started.</Link></p>
                : data.courses.map((course) => (
                    <Link to={`/courses/${course.id}`} className="editorial-course" key={course.id}>
                      <div className={`course-icon ${course.color}`}>{course.icon}</div>
                      <div className="editorial-course-body">
                        <div className="course-title">
                          <strong>{course.title}</strong>
                          <span>{course.category}</span>
                        </div>
                        <div className="course-progress">
                          <ProgressBar value={course.progress} color={course.color === 'orange' ? 'orange' : course.color === 'green' ? 'green' : 'purple'} />
                          <small>{course.progress}%</small>
                        </div>
                        <span className="last-activity">{course.lastActivity}</span>
                      </div>
                      <ChevronRight className="course-chevron" size={17} />
                    </Link>
                  ))
              }
            </div>
          </section>

          {data.concepts.length > 0 && (
            <section className="dashboard-section practice-section">
              <div className="section-heading">
                <div>
                  <span className="eyebrow">A little targeted revision</span>
                  <h2>Concepts to practice</h2>
                </div>
                <Link to="/progress" className="text-link">See progress <ArrowRight size={15} /></Link>
              </div>
              <div className="concept-list">
                {data.concepts.map((concept) => (
                  <button className="concept-row" key={concept.id} onClick={() => onOpenPractice(concept.id)}>
                    <div className={`concept-mark ${concept.color}`}><RotateCcw size={15} /></div>
                    <div>
                      <strong>{concept.title}</strong>
                      <span>{concept.reason}</span>
                      <small>{concept.course}</small>
                    </div>
                    <ChevronRight size={16} />
                  </button>
                ))}
              </div>
            </section>
          )}
        </div>

        <aside className="dashboard-side-column">
          <section className="dashboard-section streak-section">
            <div className="section-heading">
              <div>
                <span className="eyebrow">This week</span>
                <h2>Learning rhythm</h2>
              </div>
              <TrendingUp size={19} className="section-icon" />
            </div>
            <div className="weekly-chart">
              {data.weeklyActivity.map((activity) => (
                <div className="week-day" key={activity.day}>
                  <span className="bar-label">{activity.label}</span>
                  <div className="bar-track">
                    <span style={{ height: `${Math.max((activity.minutes / maxActivity) * 100, activity.minutes ? 8 : 2)}%` }} />
                  </div>
                  <small>{activity.day}</small>
                </div>
              ))}
            </div>
            <div className="weekly-total">
              <strong>{totalHours}</strong>
              <span>studied this week</span>
              {data.streak > 0 && <i><Flame size={13} /> {data.streak} day streak</i>}
            </div>
          </section>

          {data.sessions.length > 0 && (
            <section className="dashboard-section sessions-section">
              <div className="section-heading">
                <div>
                  <span className="eyebrow">Keep your notes close</span>
                  <h2>Recent sessions</h2>
                </div>
                <Clock3 size={19} className="section-icon" />
              </div>
              <div className="session-list">
                {data.sessions.map((session) => (
                  <Link to={`/exams/${session.id}/results`} className="session-row" key={session.id}>
                    <div className="session-icon"><Check size={15} /></div>
                    <div>
                      <strong>{session.title}</strong>
                      <span>{session.completedAt} · {session.duration}</span>
                    </div>
                    {session.score && <em>{session.score}</em>}
                  </Link>
                ))}
              </div>
            </section>
          )}
        </aside>
      </div>

      <section className="dashboard-bottom">
        {data.roadmap && (
          <Link to={`/roadmaps/${(data.roadmap as any).id || 'overview'}`} className="roadmap-preview">
            <div className="roadmap-preview-icon"><BookOpen size={20} /></div>
            <div className="roadmap-preview-copy">
              <span className="eyebrow">Your learning roadmap</span>
              <h2>{data.roadmap.title}</h2>
              <p>{data.roadmap.progress}% complete · {data.roadmap.modules} modules</p>
              <ProgressBar value={data.roadmap.progress} />
            </div>
            <ArrowRight size={18} />
          </Link>
        )}
        {data.nextExam && (
          <Link to={`/exams/${data.nextExam.id}`} className="practice-suggestion">
            <div>
              <span className="eyebrow">Coming up next</span>
              <h2>Try a practice exam</h2>
              <p>{data.nextExam.title} · {data.nextExam.duration}</p>
            </div>
            <div className="suggestion-arrow"><ArrowRight size={18} /></div>
          </Link>
        )}
      </section>
    </div>
  )
}
