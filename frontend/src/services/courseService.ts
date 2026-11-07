import apiClient from './apiClient';

export interface Course {
  id: number;
  user_id: number;
  title: string;
  subject?: string | null;
  domain_type?: string | null;
}

export interface CourseCreate {
  title: string;
  subject?: string | null;
  domain_type?: string | null;
}

export interface DocumentUploadResponse {
  id: number;
  status: string;
  chunks: number;
  [key: string]: unknown;
}

export const getCourses = async (): Promise<Course[]> => {
  const response = await apiClient.get<Course[]>('/courses');
  return response.data;
};

export const getCourse = async (id: number | string): Promise<Course> => {
  const response = await apiClient.get<Course>(`/courses/${id}`);
  return response.data;
};

export const createCourse = async (data: CourseCreate): Promise<Course> => {
  const response = await apiClient.post<Course>('/courses', data);
  return response.data;
};

export const uploadDocument = async (
  id: number | string,
  file: File
): Promise<DocumentUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<DocumentUploadResponse>(
    `/courses/${id}/documents`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
};

export default {
  getCourses,
  getCourse,
  createCourse,
  uploadDocument,
};
