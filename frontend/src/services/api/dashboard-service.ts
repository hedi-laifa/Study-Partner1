import apiClient from '../apiClient';
import type { DashboardService, DashboardData } from '../contracts/dashboard';
import type { DashboardCourse, PracticeConcept, StudySession, WeeklyActivity, Roadmap } from '../../types';

export const apiDashboardService: DashboardService = {
  async getDashboard(): Promise<DashboardData> {
    try {
      const [dashRes, actRes, coursesRes] = await Promise.all([
        apiClient.get<any>('/dashboard'),
        apiClient.get<any[]>('/dashboard/activity'),
        apiClient.get<any[]>('/courses'),
      ]);

      const dash = dashRes.data;
      const acts = actRes.data || [];
      const courses = coursesRes.data || [];

      const email = localStorage.getItem('userEmail') || 'Alex';
      const name = email.split('@')[0];

      const dashboardCourses: DashboardCourse[] = courses.map((c) => ({
        id: String(c.id),
        title: c.title,
        category: c.subject || 'General Study',
        progress: 0,
        lessons: 10,
        completed: 0,
        lastActivity: 'Recently active',
        nextLesson: 'Core Concepts',
        color: (c.subject?.toLowerCase().includes('stat') ? 'orange' : c.subject?.toLowerCase().includes('bio') ? 'green' : 'purple'),
        icon: '📖',
      }));

      const concepts: PracticeConcept[] = (dash.concepts || []).map((cp: any) => ({
        id: String(cp.concept_id),
        title: cp.name,
        course: courses[0]?.title || 'Enrolled Course',
        reason: `Status: ${cp.status}`,
        color: (cp.status === 'good-evidence' ? 'green' : cp.status === 'needs-practice' ? 'orange' : 'purple'),
      }));

      const sessions: StudySession[] = (dash.recent_exams || []).map((ex: any) => ({
        id: String(ex.attempt_id),
        title: ex.exam_title,
        course: courses[0]?.title || 'Practice Exam',
        completedAt: ex.submitted_at || 'Recent',
        duration: `${ex.total_questions || 5} questions`,
        score: `${Math.round(ex.score_pct)}%`,
      }));

      const daysOfWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
      const weeklyActivity: WeeklyActivity[] = daysOfWeek.map((day) => {
        const found = acts.find((a: any) => a.day === day);
        const mins = found ? found.activities_completed * 15 : 20;
        return {
          day,
          minutes: mins,
          label: `${mins}m`,
        };
      });

      const roadmap: Roadmap = {
        title: dash.roadmaps?.[0]?.role || 'Full-Stack & Machine Learning',
        description: 'Comprehensive engineering roadmap',
        progress: Math.round(dash.roadmaps?.[0]?.progress_pct || 25),
        modules: dash.roadmaps?.[0]?.total_nodes || 12,
        color: 'purple',
      };

      return {
        greeting: {
          name,
          focus: courses[0]?.title || 'Structured Learning',
          recommendation: courses.length > 0 ? `Review recent concepts in ${courses[0].title}` : 'Create your first course to begin learning',
        },
        courses: dashboardCourses,
        concepts: concepts.length ? concepts : [
          { id: '1', title: 'Core Principles', course: courses[0]?.title || 'Study Path', reason: 'Review key mental models', color: 'purple' },
        ],
        sessions,
        weeklyActivity,
        roadmap,
        isFirstTime: false,
      };
    } catch (err) {
      console.error('Failed to load dashboard from backend:', err);
      const email = localStorage.getItem('userEmail') || 'Alex';
      return {
        greeting: {
          name: email.split('@')[0],
          focus: 'Getting Started',
          recommendation: 'Add your first study materials',
        },
        courses: [],
        concepts: [],
        sessions: [],
        weeklyActivity: [
          { day: 'Mon', minutes: 0, label: '0m' },
          { day: 'Tue', minutes: 0, label: '0m' },
          { day: 'Wed', minutes: 0, label: '0m' },
          { day: 'Thu', minutes: 0, label: '0m' },
          { day: 'Fri', minutes: 0, label: '0m' },
          { day: 'Sat', minutes: 0, label: '0m' },
          { day: 'Sun', minutes: 0, label: '0m' },
        ],
        roadmap: {
          title: 'Learning Path',
          description: 'Explore tailored courses',
          progress: 0,
          modules: 10,
          color: 'purple',
        },
        isFirstTime: false,
      };
    }
  },
};
