import { mockStudyService } from './mock/study-service';
import { apiDashboardService } from './api/dashboard-service';
import { apiCourseService } from './api/courses-service';
import { apiDocumentService } from './api/documents-service';
import { mockStudySessionService } from './mock/sessions-service';
import { apiProgressService } from './api/progress-service';
import { apiRoadmapService } from './api/roadmaps-service';
import { apiExamService } from './api/exams-service';

export const studyService = mockStudyService;
export const dashboardService = apiDashboardService;
export const courseService = apiCourseService;
export const documentService = apiDocumentService;
export const studySessionService = mockStudySessionService;
export const progressService = apiProgressService;
export const roadmapService = apiRoadmapService;
export const examService = apiExamService;
