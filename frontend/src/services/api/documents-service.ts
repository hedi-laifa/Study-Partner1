import apiClient from '../apiClient';
import type { DocumentService, StudyDocument } from '../contracts/documents';

export const apiDocumentService: DocumentService = {
  async listDocuments(courseId: string): Promise<StudyDocument[]> {
    try {
      const response = await apiClient.get<StudyDocument[]>(`/courses/${courseId}/documents`);
      return response.data;
    } catch {
      return [];
    }
  },

  async queueDocument(courseId: string, fileName: string, sizeBytes: number): Promise<StudyDocument> {
    return {
      id: `doc-${Date.now()}`,
      courseId,
      fileName,
      sizeBytes,
      status: 'Ready',
      addedAt: 'Just now',
    };
  },

  async removeDocument(documentId: string): Promise<void> {
    try {
      await apiClient.delete(`/courses/0/documents/${documentId}`);
    } catch {
      // ignore
    }
  },

  async retryDocument(documentId: string): Promise<StudyDocument | undefined> {
    return {
      id: documentId,
      courseId: '0',
      fileName: 'document.pdf',
      sizeBytes: 1024 * 1024,
      status: 'Ready',
      addedAt: 'Just now',
    };
  },
};
