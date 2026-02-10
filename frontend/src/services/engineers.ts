import api from './api'
import { Engineer, PaginatedResponse } from '../types'

export const engineersApi = {
  list: (params?: Record<string, string | number>) =>
    api.get<PaginatedResponse<Engineer>>('/engineers', { params }),
  get: (id: number) => api.get<Engineer>(`/engineers/${id}`),
  create: (data: Partial<Engineer> & { skill_ids?: number[] }) => api.post<Engineer>('/engineers', data),
  update: (id: number, data: Partial<Engineer> & { skill_ids?: number[] }) => api.put<Engineer>(`/engineers/${id}`, data),
  delete: (id: number) => api.delete(`/engineers/${id}`),
}
