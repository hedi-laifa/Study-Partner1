import apiClient from './apiClient';

export interface StreakInfo {
  current_streak: number;
  longest_streak: number;
}

export interface ConceptSummary {
  concept_id: number;
  name: string;
  status: string;
  estimate: number;
}

export interface RoadmapSummary {
  user_roadmap_id: number;
  roadmap_id: number;
  role: string;
  total_nodes: number;
  completed_nodes: number;
  progress_pct: number;
}

export interface ExamSummary {
  attempt_id: number;
  exam_title: string;
  submitted_at: string;
  total_questions: number;
  correct: number;
  score_pct: number;
}

export interface DashboardData {
  streak: StreakInfo;
  concepts: ConceptSummary[];
  roadmaps: RoadmapSummary[];
  recent_exams: ExamSummary[];
}

export interface ActivityDay {
  date: string;
  activities_completed: number;
  questions_answered: number;
}

export const getDashboard = async (params?: { tz?: string }): Promise<DashboardData> => {
  const response = await apiClient.get<DashboardData>('/dashboard', { params });
  return response.data;
};

export const getActivity = async (params?: {
  days?: number;
  tz?: string;
}): Promise<ActivityDay[]> => {
  const response = await apiClient.get<ActivityDay[]>('/dashboard/activity', { params });
  return response.data;
};

export default {
  getDashboard,
  getActivity,
};
