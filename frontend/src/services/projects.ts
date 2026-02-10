import api from './api'
import { Project, PaginatedResponse } from '../types'

export const projectsApi = {
  list: (params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<Project>>('/projects', { params }),
  get: (id: number) => api.get<Project>(`/projects/${id}`),
  create: (data: Partial<Project> & { skill_ids?: number[] }) => api.post<Project>('/projects', data),
  update: (id: number, data: Partial<Project> & { skill_ids?: number[] }) => api.put<Project>(`/projects/${id}`, data),
  delete: (id: number) => api.delete(`/projects/${id}`),
}
