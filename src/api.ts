const configuredApiUrl = import.meta.env.VITE_API_URL?.trim();
const isLocalBrowser =
  typeof window !== 'undefined' &&
  ['localhost', '127.0.0.1'].includes(window.location.hostname);
const API_URL = configuredApiUrl || (isLocalBrowser ? 'http://localhost:8000/api' : '');

export interface MaterialPayload {
  id?: string;
  name: string;
  existing: number;
  counted?: number;
  description: string;
}

export type MaterialType = 'gas' | 'vapor';

export interface MaterialList {
  id: string;
  name: string;
  materials: Array<MaterialPayload & { id: string; counted: number; order_index?: number }>;
}

async function request<T = any>(path: string, options?: RequestInit): Promise<T> {
  if (!API_URL) {
    throw new Error(
      'Falta configurar VITE_API_URL en Vercel con la URL del backend, por ejemplo https://tu-backend.onrender.com/api'
    );
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL.replace(/\/$/, '')}${path}`, {
      headers: { 'Content-Type': 'application/json', ...(options?.headers || {}) },
      ...options,
    });
  } catch (error) {
    throw new Error(
      `No se pudo conectar con el backend en ${API_URL}. Revisa VITE_API_URL y CORS/FRONTEND_ORIGINS.`
    );
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || body.error || 'API request failed');
  }

  return response.json();
}

export const getMaterialsGas = () => request('/materials/gas');
export const getMaterialsVapor = () => request('/materials/vapor');
export const getMaterialLists = () => request<MaterialList[]>('/material-lists');

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

export const changeMaterialType = (
  currentType: MaterialType,
  id: string,
  material: MaterialPayload & { type: MaterialType }
) =>
  request(`/materials/${currentType}/${id}/type`, {
    method: 'PUT',
    body: JSON.stringify(material),
  });

export const updateMaterialOrder = (type: MaterialType, ids: string[]) =>
  request(`/materials/${type}/order`, {
    method: 'PUT',
    body: JSON.stringify({ ids }),
  });

export const deleteMaterialGas = (id: string) =>
  request(`/materials/gas/${id}`, { method: 'DELETE' });

export const deleteMaterialVapor = (id: string) =>
  request(`/materials/vapor/${id}`, { method: 'DELETE' });

export const createMaterialList = (name: string) =>
  request<MaterialList>('/material-lists', {
    method: 'POST',
    body: JSON.stringify({ name }),
  });

export const deleteMaterialList = (id: string) =>
  request(`/material-lists/${id}`, { method: 'DELETE' });

export const addCustomMaterial = (listId: string, material: MaterialPayload) =>
  request(`/material-lists/${listId}/materials`, {
    method: 'POST',
    body: JSON.stringify({ id: Date.now().toString(), ...material }),
  });

export const updateCustomMaterial = (listId: string, id: string, material: MaterialPayload) =>
  request(`/material-lists/${listId}/materials/${id}`, {
    method: 'PUT',
    body: JSON.stringify(material),
  });

export const moveCustomMaterial = (
  listId: string,
  id: string,
  targetListId: string,
  material: MaterialPayload
) =>
  request(`/material-lists/${listId}/materials/${id}/list`, {
    method: 'PUT',
    body: JSON.stringify({ ...material, target_list_id: targetListId }),
  });

export const deleteCustomMaterial = (listId: string, id: string) =>
  request(`/material-lists/${listId}/materials/${id}`, { method: 'DELETE' });

export const updateCustomMaterialOrder = (listId: string, ids: string[]) =>
  request(`/material-lists/${listId}/materials/order`, {
    method: 'PUT',
    body: JSON.stringify({ ids }),
  });

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
