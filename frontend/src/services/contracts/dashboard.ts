import type { DashboardCourse, PracticeConcept, Roadmap, StudySession, WeeklyActivity } from '../../types'

export type DashboardData = {
  greeting: { name: string; focus: string; recommendation: string }
  streak: number
  courses: DashboardCourse[]
  concepts: PracticeConcept[]
  sessions: StudySession[]
  weeklyActivity: WeeklyActivity[]
  roadmap: Roadmap | null
  nextExam: { id: string; title: string; duration: string } | null
  isFirstTime: boolean
}

export interface DashboardService {
  getDashboard(): Promise<DashboardData>
}
