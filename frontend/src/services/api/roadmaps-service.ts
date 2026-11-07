import apiClient from '../apiClient';
import type {
  CreateRoadmapInput,
  RoadmapCategory,
  RoadmapDetail,
  RoadmapService,
  RoadmapSource,
  RoadmapSummary,
  RoadmapTopic,
} from '../contracts/roadmaps';

interface BackendNode {
  id: number;
  title: string;
  description?: string | null;
  order: number;
  optional: boolean;
  prerequisite_id?: number | null;
}

interface BackendRoadmap {
  id: number;
  role: string;
  description?: string | null;
  source: string;
  nodes: BackendNode[];
}

function getCategory(role: string): RoadmapCategory {
  const r = role.toLowerCase();
  if (r.includes('machine') || r.includes('ai') || r.includes('neural')) return 'Machine learning';
  if (r.includes('data') || r.includes('stat') || r.includes('analyst')) return 'Data';
  if (r.includes('business') || r.includes('product') || r.includes('market')) return 'Business';
  return 'Engineering';
}

function getColor(category: RoadmapCategory): 'purple' | 'orange' | 'green' | 'blue' {
  if (category === 'Machine learning') return 'purple';
  if (category === 'Data') return 'orange';
  if (category === 'Business') return 'blue';
  return 'green';
}

function mapToSummary(r: BackendRoadmap): RoadmapSummary {
  const category = getCategory(r.role);
  const coreTopics = r.nodes.filter((n) => !n.optional).map((n) => n.title);
  const optionalTopics = r.nodes.filter((n) => n.optional).map((n) => n.title);

  return {
    id: String(r.id),
    role: r.role,
    category,
    description: r.description || `Comprehensive path for ${r.role}.`,
    topicCount: r.nodes.length,
    coreTopics: coreTopics.length ? coreTopics : ['Core Skills'],
    optionalTopics: optionalTopics.length ? optionalTopics : ['Advanced Specialization'],
    progress: 0,
    source: (r.source === 'Curated by Study Partner' ? 'Curated by Study Partner' : 'AI-generated mock') as RoadmapSource,
    color: getColor(category),
  };
}

export const apiRoadmapService: RoadmapService = {
  async listRoadmaps(): Promise<RoadmapSummary[]> {
    try {
      const response = await apiClient.get<BackendRoadmap[]>('/roadmaps');
      return response.data.map(mapToSummary);
    } catch (err) {
      console.error('Failed to load roadmaps from backend:', err);
      return [];
    }
  },

  async getRoadmap(id: string): Promise<RoadmapDetail | undefined> {
    try {
      const response = await apiClient.get<BackendRoadmap>(`/roadmaps/${id}`);
      const r = response.data;
      const summary = mapToSummary(r);

      const topics: RoadmapTopic[] = r.nodes.map((n) => ({
        id: String(n.id),
        name: n.title,
        optional: n.optional,
        completed: false,
      }));

      return {
        ...summary,
        topics,
        note: 'Roadmap suggestions are tailored to modern industry competencies.',
      };
    } catch {
      return undefined;
    }
  },

  async createRoadmap(input: CreateRoadmapInput): Promise<RoadmapDetail> {
    const payload = {
      role: input.role,
      category: input.category,
      goal: input.goal,
    };
    const response = await apiClient.post<BackendRoadmap>('/roadmaps', payload);
    const r = response.data;
    const summary = mapToSummary(r);

    return {
      ...summary,
      topics: r.nodes.map((n) => ({
        id: String(n.id),
        name: n.title,
        optional: n.optional,
        completed: false,
      })),
      note: 'Custom generated roadmap saved to database.',
    };
  },
};
