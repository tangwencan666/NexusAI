import { apiGet } from './client'
import type { HealthResponse } from '../types/api'

export const getHealth = (signal?: AbortSignal) =>
  apiGet<HealthResponse>('/api/v1/health', signal)
