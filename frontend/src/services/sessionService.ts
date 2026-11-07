import apiClient from './apiClient';

export interface Concept {
  id: number;
  course_id: number;
  name: string;
  description?: string | null;
  domain_type?: string | null;
}

export interface SessionCreatePayload {
  course_id: number;
  goal?: string | null;
  knowledge_mode?: string;
}

export interface Activity {
  id: number;
  session_id: number;
  concept_id?: number | null;
  type: string;
  difficulty: string;
  prompt: string;
  mode: string;
}

export interface SessionResponse {
  id: number;
  course_id: number;
  goal?: string | null;
  status: string;
  knowledge_mode: string;
  created_at: string;
  activities: Activity[];
}

export interface NextActivityPayload {
  answer: string;
  hint_count?: number;
}

export interface AttemptPayload {
  answer: string;
  hint_count?: number;
}

export interface EvaluationResponse {
  id: number;
  attempt_id: number;
  verdict: string;
  rubric_score: number;
  feedback: string;
  confidence: string;
  concept_progress_status?: string | null;
  concept_progress_estimate?: number | null;
}

export const getConcepts = async (courseId: number | string): Promise<Concept[]> => {
  const response = await apiClient.get<Concept[]>(`/courses/${courseId}/concepts`);
  return response.data;
};

export const createSession = async (data: SessionCreatePayload): Promise<SessionResponse> => {
  const response = await apiClient.post<SessionResponse>('/sessions', data);
  return response.data;
};

export const nextActivity = async (
  sessionId: number | string,
  data: NextActivityPayload
): Promise<Activity> => {
  const response = await apiClient.post<Activity>(`/sessions/${sessionId}/next`, data);
  return response.data;
};

export const submitAttempt = async (
  activityId: number | string,
  data: AttemptPayload
): Promise<EvaluationResponse> => {
  const response = await apiClient.post<EvaluationResponse>(`/activities/${activityId}/attempts`, data);
  return response.data;
};

export default {
  getConcepts,
  createSession,
  nextActivity,
  submitAttempt,
};
