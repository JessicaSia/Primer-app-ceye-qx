const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export interface MaterialPayload {
  name: string;
  existing: number;
  counted?: number;
  description: string;
}

async function request<T = any>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options?.headers || {}) },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || body.error || 'API request failed');
  }

  return response.json();
}

export const getMaterialsGas = () => request('/materials/gas');
export const getMaterialsVapor = () => request('/materials/vapor');

export const addMaterialGas = (material: MaterialPayload) =>
  request('/materials/gas', {
    method: 'POST',
    body: JSON.stringify({ id: Date.now().toString(), ...material }),
  });

export const addMaterialVapor = (material: MaterialPayload) =>
  request('/materials/vapor', {
    method: 'POST',
    body: JSON.stringify({ id: Date.now().toString(), ...material }),
  });

export const updateMaterialGas = (id: string, material: MaterialPayload) =>
  request(`/materials/gas/${id}`, {
    method: 'PUT',
    body: JSON.stringify(material),
  });

export const updateMaterialVapor = (id: string, material: MaterialPayload) =>
  request(`/materials/vapor/${id}`, {
    method: 'PUT',
    body: JSON.stringify(material),
  });

export const deleteMaterialGas = (id: string) =>
  request(`/materials/gas/${id}`, { method: 'DELETE' });

export const deleteMaterialVapor = (id: string) =>
  request(`/materials/vapor/${id}`, { method: 'DELETE' });

export const getReports = () => request('/reports');

export interface ReportPayload {
  type: string;
  user_name: string;
  shift: string;
  differences: unknown[];
}

export const createReport = (report: ReportPayload) =>
  request('/reports', {
    method: 'POST',
    body: JSON.stringify({ id: Date.now().toString(), ...report }),
  });

export const updateReport = (id: string, report: ReportPayload) =>
  request(`/reports/${id}`, {
    method: 'PUT',
    body: JSON.stringify(report),
  });
