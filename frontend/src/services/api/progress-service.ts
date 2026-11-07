import apiClient from '../apiClient';
import type { ProgressData, ProgressService } from '../contracts/progress';

export const apiProgressService: ProgressService = {
  async getProgress(): Promise<ProgressData> {
    const response = await apiClient.get<ProgressData>('/progress');
    return response.data;
  },
};
