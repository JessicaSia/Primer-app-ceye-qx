const configuredApiUrl = import.meta.env.VITE_API_URL?.trim();
const isLocalBrowser =
  typeof window !== 'undefined' &&
  ['localhost', '127.0.0.1'].includes(window.location.hostname);
const API_URL = configuredApiUrl || (isLocalBrowser ? 'http://localhost:8000/api' : '');
const AUTH_TOKEN_KEY = 'ceyeAuthToken';

export type UserRole = 'admin' | 'nurse' | 'supervisor' | 'readonly';

export interface AuthUser {
  id: string;
  organization_id: string;
  area_id: string;
  name: string;
  username: string;
  email?: string;
  role: UserRole;
  role_label: string;
}

export interface Area {
  id: string;
  organization_id: string;
  name: string;
}

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
  const token = getAuthToken();
  try {
    response = await fetch(`${API_URL.replace(/\/$/, '')}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options?.headers || {}),
      },
      ...options,
    });
  } catch (error) {
    throw new Error(
      `No se pudo conectar con el backend en ${API_URL}. Revisa VITE_API_URL y CORS/FRONTEND_ORIGINS.`
    );
  }

  if (!response.ok) {
    if (response.status === 401) {
      clearAuthToken();
    }
    const body = await response.json().catch(() => ({}));
    throw new Error(getApiErrorMessage(body));
  }

  return response.json();
}

function getApiErrorMessage(body: any) {
  if (typeof body?.detail === 'string') {
    return body.detail;
  }

  if (Array.isArray(body?.detail)) {
    const stillNeedsEmail = body.detail.some((item: any) => item?.loc?.includes?.('email'));
    if (stillNeedsEmail) {
      return 'El backend aun no esta actualizado para entrar con nombre de usuario. Despliega el backend en Render y vuelve a intentar.';
    }

    return body.detail
      .map((item: any) => item?.msg || item?.message || 'Datos invalidos')
      .join('. ');
  }

  if (body?.detail && typeof body.detail === 'object') {
    return body.detail.message || JSON.stringify(body.detail);
  }

  if (typeof body?.error === 'string') {
    return body.error;
  }

  return 'No se pudo completar la solicitud.';
}

export function getAuthToken() {
  return typeof window === 'undefined' ? null : window.localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setAuthToken(token: string) {
  window.localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function clearAuthToken() {
  if (typeof window !== 'undefined') {
    window.localStorage.removeItem(AUTH_TOKEN_KEY);
  }
}

export const login = (username: string, password: string) =>
  request<{ token: string; user: AuthUser }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });

export const getMe = () => request<AuthUser>('/auth/me');

export const logout = (token?: string) =>
  request('/auth/logout', {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });

export const getUsers = () => request<AuthUser[]>('/users');
export const getAreas = () => request<Area[]>('/areas');
export const createArea = (name: string) =>
  request<Area>('/areas', {
    method: 'POST',
    body: JSON.stringify({ name }),
  });

export const createUser = (payload: {
  name: string;
  username: string;
  password: string;
  role: UserRole;
  area_id?: string;
}) =>
  request<AuthUser>('/users', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const updateUser = (
  id: string,
  payload: Partial<{ name: string; username: string; password: string; role: UserRole; area_id: string }>
) =>
  request<AuthUser>(`/users/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });

export const deleteUser = (id: string) => request(`/users/${id}`, { method: 'DELETE' });

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
  duration_seconds?: number;
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
