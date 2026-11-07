import apiClient from '../apiClient';
import type { DashboardService, DashboardData } from '../contracts/dashboard';
import type { DashboardCourse, PracticeConcept, StudySession, WeeklyActivity } from '../../types';

function getColor(subject: string | null | undefined): string {
  if (!subject) return 'purple';
  const s = subject.toLowerCase();
  if (s.includes('stat') || s.includes('math') || s.includes('data') || s.includes('econ')) return 'orange';
  if (s.includes('bio') || s.includes('med') || s.includes('health') || s.includes('chem')) return 'green';
  return 'purple';
}

function getIcon(subject: string | null | undefined): string {
  if (!subject) return '📖';
  const s = subject.toLowerCase();
  if (s.includes('deep') || s.includes('neural') || s.includes('ai') || s.includes('code') || s.includes('comp')) return '∿';
  if (s.includes('stat') || s.includes('math')) return 'σ';
  if (s.includes('bio') || s.includes('med')) return '✣';
  if (s.includes('business') || s.includes('econ')) return '↗';
  return '📖';
}

const DAYS_OF_WEEK = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export const apiDashboardService: DashboardService = {
  async getDashboard(): Promise<DashboardData> {
    const email = localStorage.getItem('userEmail') || '';
    const name = email ? email.split('@')[0] : 'there';

    try {
      const [dashRes, actRes, coursesRes, examsRes] = await Promise.all([
        apiClient.get<any>('/dashboard'),
        apiClient.get<any[]>('/dashboard/activity?days=7'),
        apiClient.get<any[]>('/courses'),
        apiClient.get<any[]>('/exams').catch(() => ({ data: [] })),
      ]);

      const dash = dashRes.data;
      const acts: any[] = actRes.data || [];
      const courses: any[] = coursesRes.data || [];
      const exams: any[] = examsRes.data || [];

      const isFirstTime = courses.length === 0;

      const dashboardCourses: DashboardCourse[] = courses.map((c) => ({
        id: String(c.id),
        title: c.title,
        category: c.subject || 'General Study',
        progress: 0,
        lessons: 10,
        completed: 0,
        lastActivity: 'Recently active',
        nextLesson: 'Core Concepts',
        color: getColor(c.subject),
        icon: getIcon(c.subject),
      }));

      const concepts: PracticeConcept[] = (dash.concepts || []).map((cp: any) => ({
        id: String(cp.concept_id),
        title: cp.name,
        course: courses[0]?.title || 'Your course',
        reason: cp.status === 'good-evidence' ? 'Doing well — keep it up' : cp.status === 'needs-practice' ? 'Needs more practice' : 'Review this concept',
        color: cp.status === 'good-evidence' ? 'green' : cp.status === 'needs-practice' ? 'orange' : 'purple',
      }));

      const sessions: StudySession[] = (dash.recent_exams || []).map((ex: any) => ({
        id: String(ex.attempt_id),
        title: ex.exam_title,
        course: courses[0]?.title || 'Practice Exam',
        completedAt: ex.submitted_at ? new Date(ex.submitted_at).toLocaleDateString() : 'Recent',
        duration: `${ex.total_questions || 5} questions`,
        score: `${Math.round(ex.score_pct)}%`,
      }));

      // Build weekly activity from real data — zero for days with no activity
      const actByDate: Record<string, number> = {};
      for (const a of acts) {
        const d = new Date(a.date);
        const dayName = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][d.getDay()];
        actByDate[dayName] = (actByDate[dayName] || 0) + a.activities_completed * 15;
      }
      const weeklyActivity: WeeklyActivity[] = DAYS_OF_WEEK.map((day) => {
        const mins = actByDate[day] || 0;
        return { day, minutes: mins, label: mins > 0 ? `${mins}m` : '0m' };
      });

      // Roadmap from backend
      const roadmapRaw = dash.roadmaps?.[0];
      const roadmap = roadmapRaw
        ? {
            title: roadmapRaw.role || 'Learning Path',
            description: 'Your personalised study roadmap',
            progress: Math.round(roadmapRaw.progress_pct || 0),
            modules: roadmapRaw.total_nodes || 0,
            color: 'purple',
            id: String(roadmapRaw.roadmap_id),
          }
        : null;

      // Next available exam
      const nextExamRaw = exams.find((e: any) => e.status === 'ready') || exams[0];
      const nextExam = nextExamRaw
        ? {
            id: String(nextExamRaw.id),
            title: nextExamRaw.title,
            duration: `${nextExamRaw.time_limit_minutes || 20} minutes`,
          }
        : null;

      const streak = dash.streak?.current_streak ?? 0;

      return {
        greeting: {
          name,
          focus: courses[0]?.title || 'your studies',
          recommendation: isFirstTime
            ? 'Create your first course to begin learning'
            : concepts.length > 0
            ? `Practice "${concepts[0].title}" to strengthen your understanding`
            : `Keep going with ${courses[0]?.title || 'your courses'}`,
        },
        streak,
        courses: dashboardCourses,
        concepts,
        sessions,
        weeklyActivity,
        roadmap,
        nextExam,
        isFirstTime,
      };
    } catch (err) {
      console.error('Dashboard load failed:', err);
      return {
        greeting: {
          name,
          focus: 'getting started',
          recommendation: 'Create your first course to begin learning',
        },
        streak: 0,
        courses: [],
        concepts: [],
        sessions: [],
        weeklyActivity: DAYS_OF_WEEK.map((day) => ({ day, minutes: 0, label: '0m' })),
        roadmap: null,
        nextExam: null,
        isFirstTime: true,
      };
    }
  },
};
