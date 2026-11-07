import apiClient from '../apiClient';
import type {
  CourseDetail,
  CourseLevel,
  CourseService,
  CourseSubject,
  CourseSummary,
  CreateCourseInput,
} from '../contracts/courses';

interface BackendCourse {
  id: number;
  user_id: number;
  title: string;
  subject?: string | null;
  domain_type?: string | null;
}

interface BackendConcept {
  id: number;
  course_id: number;
  name: string;
  description?: string | null;
  domain_type?: string | null;
}

function getColor(subject: string | null | undefined): 'forest' | 'coral' | 'sage' | 'lilac' {
  if (!subject) return 'forest';
  const s = subject.toLowerCase();
  if (s.includes('deep') || s.includes('learning') || s.includes('neural') || s.includes('ai') || s.includes('tech')) return 'forest';
  if (s.includes('stat') || s.includes('math') || s.includes('data') || s.includes('econ') || s.includes('phys')) return 'coral';
  if (s.includes('bio') || s.includes('cell') || s.includes('med') || s.includes('chem') || s.includes('health')) return 'sage';
  return 'lilac';
}

function getIcon(subject: string | null | undefined): string {
  if (!subject) return '∿';
  const s = subject.toLowerCase();
  if (s.includes('deep') || s.includes('learning') || s.includes('code') || s.includes('comp')) return '∿';
  if (s.includes('stat') || s.includes('math')) return 'σ';
  if (s.includes('bio') || s.includes('med') || s.includes('health')) return '✣';
  if (s.includes('business') || s.includes('econ')) return '↗';
  return '✦';
}

export const apiCourseService: CourseService = {
  async listCourses(): Promise<CourseSummary[]> {
    try {
      const response = await apiClient.get<BackendCourse[]>('/courses');
      return response.data.map((c) => ({
        id: String(c.id),
        title: c.title,
        subject: (c.subject as CourseSubject) || 'General Studies',
        level: (c.domain_type as CourseLevel) || 'Intermediate',
        description: `Active course with automated grounding and concept tracking.`,
        lastStudied: 'Recently updated',
        progress: 0,
        completedMaterials: 0,
        materialCount: 0,
        color: getColor(c.subject),
        icon: getIcon(c.subject),
      }));
    } catch (err) {
      console.error('Failed to list courses from backend:', err);
      return [];
    }
  },

  async createCourse(input: CreateCourseInput): Promise<CourseSummary> {
    const payload = {
      title: input.title.trim(),
      subject: input.subject.trim(),
      domain_type: input.level,
    };

    const response = await apiClient.post<BackendCourse>('/courses', payload);
    const c = response.data;

    return {
      id: String(c.id),
      title: c.title,
      subject: (c.subject as CourseSubject) || input.subject,
      level: input.level,
      description: input.description.trim() || `Course grounded in your uploaded materials.`,
      lastStudied: 'Just created',
      progress: 0,
      completedMaterials: 0,
      materialCount: 0,
      color: getColor(c.subject),
      icon: getIcon(c.subject),
    };
  },

  async getCourse(courseId: string): Promise<CourseDetail | undefined> {
    try {
      const courseRes = await apiClient.get<BackendCourse>(`/courses/${courseId}`);
      const c = courseRes.data;

      // Get real concepts from backend
      let concepts: Array<{ id: string; title: string; progress: number; status: 'Strong' | 'In progress' | 'Needs review' }> = [];
      try {
        const conceptsRes = await apiClient.get<BackendConcept[]>(`/courses/${courseId}/concepts`);
        concepts = conceptsRes.data.map((item) => ({
          id: String(item.id),
          title: item.name,
          progress: 50,
          status: 'In progress',
        }));
      } catch {
        concepts = [];
      }

      return {
        id: String(c.id),
        title: c.title,
        subject: (c.subject as CourseSubject) || 'General Studies',
        level: (c.domain_type as CourseLevel) || 'Intermediate',
        description: `Course grounded in your study documents.`,
        lastStudied: 'Active now',
        progress: concepts.length > 0 ? 50 : 0,
        completedMaterials: 0,
        materialCount: 0,
        color: getColor(c.subject),
        icon: getIcon(c.subject),
        concepts,
        sessions: [],
      };
    } catch (err) {
      console.error(`Failed to fetch course #${courseId}:`, err);
      return undefined;
    }
  },
};
