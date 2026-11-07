import apiClient from '../apiClient';
import type {
  ExamAttempt,
  ExamCourseOption,
  ExamQuestion,
  ExamResult,
  ExamService,
  ExamSetup,
  PracticeExam,
} from '../contracts/exams';

interface BackendExamQuestion {
  id: number;
  type: string;
  prompt: string;
  options?: string[] | null;
  order: number;
}

interface BackendExam {
  id: number;
  course_id: number;
  title: string;
  time_limit_minutes: number;
  question_count: number;
  status: string;
}

function mapResultData(data: any, id: string): ExamResult {
  const answers: any[] = data.answers || [];
  const correctCount = answers.filter((a) => a.verdict === 'Correct').length;
  const partialCount = answers.filter((a) => a.verdict === 'Partially correct').length;
  const incorrectCount = answers.filter((a) => a.verdict === 'Incorrect').length;
  const insufficientCount = answers.filter((a) => a.verdict === 'Insufficient evidence').length;

  const total = answers.length || 1;
  const scorePercent = Math.round(((correctCount + partialCount * 0.5) / total) * 100);

  return {
    examId: String(data.exam_id || id),
    title: data.title || 'Completed Practice Exam',
    course: data.course || 'Verified Course',
    courseId: String(data.exam_id || id),
    completedQuestions: answers.filter((a) => a.answer_text && a.answer_text.trim()).length,
    totalQuestions: total,
    timeUsed: 'Completed',
    scoreLabel: `${scorePercent}%`,
    counts: {
      Correct: correctCount,
      'Partially correct': partialCount,
      Incorrect: incorrectCount,
      'Insufficient evidence': insufficientCount,
    },
    questionResults: answers.map((a: any) => ({
      question: {
        id: String(a.question_id),
        prompt: a.prompt,
        type: a.options ? 'multiple-choice' : 'short-answer',
        concept: 'Knowledge Check',
      },
      answer: a.answer_text || '(No answer provided)',
      correctAnswer: a.correct_answer || (a.verdict === 'Correct' ? a.answer_text : undefined),
      verdict: (a.verdict as any) || 'Incorrect',
      expectedIdeas: a.correct_answer ? [a.correct_answer] : ['Verified conceptual mechanism'],
      strengths: a.verdict === 'Correct' ? ['Accurate understanding and terminology'] : [],
      gaps: a.verdict !== 'Correct' ? [a.feedback || 'Review lecture notes on this concept'] : [],
      confidence: a.verdict === 'Correct' ? 'High' : 'Medium',
    })),
    concepts: [
      {
        concept: 'Core Syllabus Competencies',
        correct: correctCount,
        total,
        summary: `${correctCount} of ${total} questions answered correctly.`,
        nextAction: scorePercent >= 70 ? 'Proceed to advanced study blocks.' : 'Review core lecture notes and retake.',
      },
    ],
  };
}

export const apiExamService: ExamService = {
  async getOptions(): Promise<ExamCourseOption[]> {
    try {
      const coursesRes = await apiClient.get<Array<{ id: number; title: string }>>('/courses');
      const courses = coursesRes.data;

      const options: ExamCourseOption[] = [];
      for (const c of courses) {
        let concepts: Array<{ id: string; title: string }> = [];
        try {
          const conceptsRes = await apiClient.get<Array<{ id: number; name: string }>>(`/courses/${c.id}/concepts`);
          concepts = conceptsRes.data.map((item) => ({ id: String(item.id), title: item.name }));
        } catch {
          concepts = [];
        }
        options.push({
          id: String(c.id),
          title: c.title,
          concepts: concepts.length ? concepts : [{ id: 'core', title: `${c.title} Core Principles` }],
        });
      }
      return options;
    } catch {
      return [];
    }
  },

  async listAttempts(): Promise<ExamAttempt[]> {
    try {
      const res = await apiClient.get<ExamAttempt[]>('/exam-attempts');
      return res.data;
    } catch {
      return [];
    }
  },

  async createExam(setup: ExamSetup): Promise<PracticeExam> {
    const payload = {
      course_id: Number(setup.courseId) || 1,
      title: `Practice Check-in (${setup.questionCount} Questions)`,
      time_limit_minutes: setup.timeLimit || 30,
      question_count: setup.questionCount || 8,
      concept_names: setup.topicIds,
    };

    const res = await apiClient.post<BackendExam>('/exams', payload);
    const exam = res.data;

    let questions: ExamQuestion[] = [];
    try {
      const startRes = await apiClient.post<{ attempt_id: number; questions: BackendExamQuestion[] }>(
        `/exams/${exam.id}/start`
      );
      questions = startRes.data.questions.map((q) => ({
        id: String(q.id),
        prompt: q.prompt,
        type: q.type === 'multiple-choice' ? 'multiple-choice' : 'short-answer',
        options: q.options || undefined,
        concept: 'Verified Knowledge',
      }));
    } catch {
      questions = [
        {
          id: 'q1',
          prompt: 'Explain the fundamental mechanism tested in this exam.',
          type: 'short-answer',
          concept: 'Core Competency',
        },
      ];
    }

    return {
      ...setup,
      id: String(exam.id),
      title: exam.title,
      course: 'Selected Course',
      topicTitles: setup.topicIds,
      questions,
    };
  },

  async getExam(id: string): Promise<PracticeExam | undefined> {
    try {
      const examRes = await apiClient.get<BackendExam>(`/exams/${id}`);
      const exam = examRes.data;

      const startRes = await apiClient.post<{ attempt_id: number; questions: BackendExamQuestion[] }>(
        `/exams/${id}/start`
      );

      return {
        id: String(exam.id),
        courseId: String(exam.course_id),
        title: exam.title,
        course: 'Practice Exam',
        topicIds: [],
        topicTitles: ['Course Material'],
        questionCount: exam.question_count,
        timeLimit: exam.time_limit_minutes,
        questions: startRes.data.questions.map((q) => ({
          id: String(q.id),
          prompt: q.prompt,
          type: q.type === 'multiple-choice' ? 'multiple-choice' : 'short-answer',
          options: q.options || undefined,
          concept: 'Exam Concept',
        })),
      };
    } catch {
      return undefined;
    }
  },

  async submitExam(id: string, answers: Record<string, string>): Promise<ExamResult | undefined> {
    try {
      const res = await apiClient.post<any>(`/exams/${id}/submit`, { answers });
      return mapResultData(res.data, id);
    } catch (err) {
      console.error('Failed to submit exam:', err);
      return undefined;
    }
  },

  async getResult(id: string): Promise<ExamResult | undefined> {
    try {
      const res = await apiClient.get<any>(`/exams/${id}/results`);
      return mapResultData(res.data, id);
    } catch {
      try {
        const fallbackRes = await apiClient.get<any>(`/exam-attempts/${id}/results`);
        return mapResultData(fallbackRes.data, id);
      } catch {
        return undefined;
      }
    }
  },
};
