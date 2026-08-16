<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue';
import {
  addMaterialGas,
  addMaterialVapor,
  addCustomMaterial,
  clearAuthToken,
  changeMaterialType,
  createArea,
  createOrganization,
  createMaterialList,
  createReport,
  createUser,
  deleteCustomMaterial,
  deleteMaterialGas,
  deleteMaterialVapor,
  deleteUser,
  getAuthToken,
  getActiveContext,
  getAreas,
  getMaterialLists,
  getMaterialsGas,
  getMaterialsVapor,
  getMe,
  getOrganizations,
  getReports,
  getUsers,
  login,
  logout,
  moveCustomMaterial,
  setActiveContext,
  setAuthToken,
  type Area,
  type AuthUser,
  type Organization,
  type UserRole,
  updateMaterialOrder,
  updateReport,
  updateUser,
  updateCustomMaterial,
  updateCustomMaterialOrder,
  updateMaterialGas,
  updateMaterialVapor,
} from './api';

type View = 'home' | 'select' | 'gas' | 'vapor' | 'custom-count' | 'stock' | 'reports' | 'users';
type MaterialType = 'gas' | 'vapor';
type CountTarget = MaterialType | string;

interface Material {
  id: string;
  name: string;
  existing: number;
  counted: number;
  description: string;
  order_index?: number;
}

interface CustomMaterialList {
  id: string;
  name: string;
  materials: Material[];
}

interface ReportDifference extends Material {
  difference: number;
  room_count?: number;
  process_count?: number;
}

interface Report {
  id: string;
  type: string;
  user_name: string;
  shift: string;
  timestamp: string;
  duration_seconds?: number;
  differences: ReportDifference[];
}

interface CountAdditions {
  room: number;
  process: number;
}

const view = ref<View>('home');
const currentUser = ref<AuthUser | null>(null);
const loginUsername = ref('');
const loginPassword = ref('');
const loginLoading = ref(false);
const usersList = ref<AuthUser[]>([]);
const areasList = ref<Area[]>([]);
const organizationsList = ref<Organization[]>([]);
const selectedOrganizationId = ref(getActiveContext().organizationId);
const selectedAreaId = ref(getActiveContext().areaId);
const usersLoading = ref(false);
const newOrganizationName = ref('');
const newUserName = ref('');
const newUsername = ref('');
const newUserPassword = ref('');
const newUserRole = ref<UserRole>('nurse');
const newUserOrganizationId = ref('');
const newUserAreaId = ref('');
const newAreaName = ref('');
const editingUserId = ref<string | null>(null);
const editingUserName = ref('');
const editingUsername = ref('');
const editingUserRole = ref<UserRole>('nurse');
const editingUserOrganizationId = ref('');
const editingUserAreaId = ref('');
const editingUserPassword = ref('');
const materialsGas = ref<Material[]>([]);
const materialsVapor = ref<Material[]>([]);
const customMaterialLists = ref<CustomMaterialList[]>([]);
const reports = ref<Report[]>([]);
const showDifferences = ref(false);
const newMaterialName = ref('');
const newMaterialExisting = ref(0);
const newMaterialDescription = ref('');
const newMaterialType = ref('gas');
const activeCustomListId = ref<string | null>(null);
const showNewListForm = ref(false);
const newListName = ref('');
const editingId = ref<string | null>(null);
const editingType = ref<MaterialType | null>(null);
const editingTargetType = ref<CountTarget>('gas');
const editingName = ref('');
const editingExisting = ref(0);
const editingDescription = ref('');
const notification = ref<{ message: string; type: 'success' | 'error' } | null>(null);
const countAdditions = ref<Record<string, CountAdditions>>({});
const reportUserName = ref('');
const reportShift = ref('');
const editingReportId = ref<string | null>(null);
const editReportUserName = ref('');
const editReportShift = ref('');
const editReportDifferences = ref<ReportDifference[]>([]);
const editReportMaterialSearch = ref('');
const showReportSearch = ref(false);
const reportSearchDate = ref('');
const highlightedReportId = ref<string | null>(null);
const printingReportId = ref<string | null>(null);
const selectedReportId = ref<string | null>(null);
const stockMaterialSearch = ref('');
const showStockGasMaterials = ref(false);
const showStockVaporMaterials = ref(false);
const shownCustomStockLists = ref<Record<string, boolean>>({});
const editingCustomListId = ref<string | null>(null);
const reportTimeZone = 'America/Mexico_City';
const draggingMaterial = ref<{ id: string; type: MaterialType } | null>(null);
const draggingCustomMaterial = ref<{ id: string; listId: string } | null>(null);
const countStartedAt = ref<number | null>(null);
const countElapsedSeconds = ref(0);
let countTimer: ReturnType<typeof window.setInterval> | null = null;

const activeCustomList = computed(() =>
  customMaterialLists.value.find((list) => list.id === activeCustomListId.value) || null
);
const currentType = computed<CountTarget>(() => {
  if (view.value === 'gas') return 'gas';
  if (view.value === 'vapor') return 'vapor';
  return activeCustomListId.value || 'gas';
});
const currentMaterials = computed(() => {
  if (currentType.value === 'gas') return materialsGas.value;
  if (currentType.value === 'vapor') return materialsVapor.value;
  return activeCustomList.value?.materials || [];
});
const currentCountTitle = computed(() => getReportTypeLabel(currentType.value));
const materialListOptions = computed(() => [
  { id: 'gas', name: 'Gas' },
  { id: 'vapor', name: 'Vapor' },
  ...customMaterialLists.value.map((list) => ({ id: list.id, name: list.name })),
]);
const differences = computed(() =>
  currentMaterials.value.map((material) => ({
    ...material,
    difference: material.counted - material.existing,
  }))
);
const adjustedDifferences = computed(() =>
  differences.value.map((diff) => {
    const additions = countAdditions.value[diff.id] || { room: 0, process: 0 };
    const counted = diff.counted + additions.room + additions.process;
    return {
      ...diff,
      counted,
      room_count: additions.room,
      process_count: additions.process,
      difference: counted - diff.existing,
    };
  })
);
const filteredEditReportDifferences = computed(() => {
  const search = normalizeSearchText(editReportMaterialSearch.value);
  if (!search) return editReportDifferences.value;

  return editReportDifferences.value.filter((diff) =>
    normalizeSearchText(diff.name).includes(search)
  );
});
const filteredStockMaterialsGas = computed(() => filterMaterialsByName(materialsGas.value, stockMaterialSearch.value));
const filteredStockMaterialsVapor = computed(() =>
  filterMaterialsByName(materialsVapor.value, stockMaterialSearch.value)
);
const filteredCustomMaterialLists = computed(() =>
  customMaterialLists.value.map((list) => ({
    ...list,
    materials: filterMaterialsByName(list.materials, stockMaterialSearch.value),
  }))
);
const filteredStockMaterialCount = computed(
  () =>
    filteredStockMaterialsGas.value.length +
    filteredStockMaterialsVapor.value.length +
    filteredCustomMaterialLists.value.reduce((count, list) => count + list.materials.length, 0)
);
const stockMaterialCount = computed(
  () =>
    materialsGas.value.length +
    materialsVapor.value.length +
    customMaterialLists.value.reduce((count, list) => count + list.materials.length, 0)
);
const customMaterialCount = computed(() =>
  customMaterialLists.value.reduce((count, list) => count + list.materials.length, 0)
);
const latestReport = computed(() => reports.value[0] || null);
const dashboardStats = computed(() => [
  { label: 'Materiales', value: stockMaterialCount.value, detail: 'en inventario' },
  { label: 'Gas', value: materialsGas.value.length, detail: 'materiales registrados' },
  { label: 'Vapor', value: materialsVapor.value.length, detail: 'materiales registrados' },
  { label: 'Reportes', value: reports.value.length, detail: 'conteos guardados' },
]);
const inventoryChartData = computed(() => {
  const values = [
    { label: 'Gas', value: materialsGas.value.length, color: 'blue' },
    { label: 'Vapor', value: materialsVapor.value.length, color: 'green' },
    { label: 'Personalizados', value: customMaterialCount.value, color: 'blue-soft' },
  ];
  const maxValue = Math.max(...values.map((item) => item.value), 1);

  return values.map((item) => ({
    ...item,
    percent: Math.max(6, Math.round((item.value / maxValue) * 100)),
  }));
});
const reportChartData = computed(() => {
  const reportCounts = reports.value.reduce<Record<string, number>>((acc, report) => {
    const label = getReportTypeLabel(report.type);
    acc[label] = (acc[label] || 0) + 1;
    return acc;
  }, {});
  const values = Object.entries(reportCounts)
    .map(([label, value], index) => ({
      label,
      value,
      color: index % 2 === 0 ? 'blue' : 'green',
    }))
    .slice(0, 6);
  const maxValue = Math.max(...values.map((item) => item.value), 1);

  return values.map((item) => ({
    ...item,
    percent: Math.max(6, Math.round((item.value / maxValue) * 100)),
  }));
});
const reportPieData = computed(() => {
  const total = reportChartData.value.reduce((sum, item) => sum + item.value, 0);
  return reportChartData.value.map((item) => ({
    ...item,
    share: total > 0 ? Math.round((item.value / total) * 100) : 0,
  }));
});
const reportPieStyle = computed(() => {
  const colors: Record<string, string> = {
    blue: 'var(--brand-blue)',
    green: 'var(--brand-green)',
    'blue-soft': 'var(--brand-blue-dark)',
  };
  const total = reportChartData.value.reduce((sum, item) => sum + item.value, 0);
  if (!total) return { background: 'var(--brand-blue-soft)' };

  let start = 0;
  const segments = reportChartData.value.map((item) => {
    const end = start + (item.value / total) * 100;
    const segment = `${colors[item.color]} ${start}% ${end}%`;
    start = end;
    return segment;
  });

  return { background: `conic-gradient(${segments.join(', ')})` };
});
const filteredReports = computed(() => {
  if (!reportSearchDate.value) return reports.value;
  return reports.value.filter((report) => getReportDateKey(report.timestamp) === reportSearchDate.value);
});
const selectedReport = computed(() =>
  filteredReports.value.find((report) => report.id === selectedReportId.value) || null
);
const roleOptions: Array<{ value: UserRole; label: string }> = [
  { value: 'owner', label: 'Creador' },
  { value: 'admin', label: 'Administrador' },
  { value: 'nurse', label: 'Enfermeria' },
  { value: 'supervisor', label: 'Supervisor/jefatura' },
  { value: 'readonly', label: 'Solo lectura' },
];
const assignableRoleOptions = computed(() => roleOptions.filter((option) => option.value !== 'owner'));
const isOwner = computed(() => currentUser.value?.role === 'owner');
const currentOrganizationId = computed(() => (isOwner.value ? selectedOrganizationId.value : currentUser.value?.organization_id || ''));
const currentAreaId = computed(() => (isOwner.value ? selectedAreaId.value : currentUser.value?.area_id || ''));
const filteredAreasList = computed(() =>
  areasList.value.filter((area) => !currentOrganizationId.value || area.organization_id === currentOrganizationId.value)
);
const canManageUsers = computed(() => currentUser.value?.role === 'admin' || isOwner.value);
const canManageStock = computed(() =>
  isOwner.value || currentUser.value?.role === 'admin' || currentUser.value?.role === 'supervisor'
);
const canDeleteData = computed(() => isOwner.value || currentUser.value?.role === 'admin');
const canSaveReports = computed(() =>
  ['owner', 'admin', 'supervisor', 'nurse'].includes(currentUser.value?.role || '')
);
const reportEditWindowMs = 12 * 60 * 60 * 1000;
const currentOrganizationName = computed(() => organizationLabel(currentOrganizationId.value));
const currentAreaName = computed(() => areaLabel(currentAreaId.value));

onMounted(() => {
  loadSession();
});

onUnmounted(() => {
  stopCountTimer();
});

async function loadData() {
  try {
    const [organizationData, areaData] = await Promise.all([getOrganizations(), getAreas()]);
    organizationsList.value = organizationData;
    areasList.value = areaData;
    ensureOwnerContext();
  } catch (error) {
    console.error(error);
    showNotification(getErrorMessage(error, 'Error cargando hospital y areas'), 'error');
  }

  try {
    const [gasData, vaporData, customListData, reportData] = await Promise.all([
      getMaterialsGas(),
      getMaterialsVapor(),
      getMaterialLists(),
      getReports(),
    ]);
    materialsGas.value = gasData;
    materialsVapor.value = vaporData;
    customMaterialLists.value = customListData;
    reports.value = reportData;
  } catch (error) {
    console.error(error);
    showNotification(getErrorMessage(error, 'Error cargando datos'), 'error');
  }
}

async function loadSession() {
  if (!getAuthToken()) {
    return;
  }

  try {
    currentUser.value = await getMe();
    await loadData();
  } catch (error) {
    console.error(error);
    clearAuthToken();
    currentUser.value = null;
  }
}

async function handleLogin() {
  if (!loginUsername.value.trim() || !loginPassword.value) {
    showNotification('Escribe tu usuario y contrasena.', 'error');
    return;
  }

  loginLoading.value = true;
  try {
    const session = await login(loginUsername.value, loginPassword.value);
    setAuthToken(session.token);
    currentUser.value = session.user;
    loginPassword.value = '';
    await loadData();
    showNotification(`Bienvenida, ${session.user.name}.`);
  } catch (error) {
    console.error(error);
    showNotification(getErrorMessage(error, 'No se pudo iniciar sesion'), 'error');
  } finally {
    loginLoading.value = false;
  }
}

async function handleLogout() {
  const token = getAuthToken();
  clearAuthToken();
  currentUser.value = null;
  view.value = 'home';
  resetCountTimer();
  materialsGas.value = [];
  materialsVapor.value = [];
  customMaterialLists.value = [];
  reports.value = [];
  areasList.value = [];

  try {
    if (token) {
      await logout(token);
    }
  } catch (error) {
    console.error(error);
  }
}

function showNotification(message: string, type: 'success' | 'error' = 'success') {
  notification.value = { message, type };
  window.setTimeout(() => {
    notification.value = null;
  }, 3000);
}

function isCountingView(nextView: View) {
  return nextView === 'gas' || nextView === 'vapor' || nextView === 'custom-count';
}

function updateCountElapsed() {
  if (!countStartedAt.value) {
    countElapsedSeconds.value = 0;
    return;
  }
  countElapsedSeconds.value = Math.max(0, Math.floor((Date.now() - countStartedAt.value) / 1000));
}

function startCountTimer() {
  countStartedAt.value = Date.now();
  countElapsedSeconds.value = 0;
  if (countTimer) {
    window.clearInterval(countTimer);
  }
  countTimer = window.setInterval(updateCountElapsed, 1000);
}

function stopCountTimer() {
  if (countTimer) {
    window.clearInterval(countTimer);
    countTimer = null;
  }
}

function resetCountTimer() {
  stopCountTimer();
  countStartedAt.value = null;
  countElapsedSeconds.value = 0;
}

function formatDuration(totalSeconds = 0) {
  const safeSeconds = Math.max(0, Math.floor(totalSeconds || 0));
  const hours = Math.floor(safeSeconds / 3600);
  const minutes = Math.floor((safeSeconds % 3600) / 60);
  const seconds = safeSeconds % 60;
  return [hours, minutes, seconds].map((value) => String(value).padStart(2, '0')).join(':');
}

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

function setView(nextView: View) {
  if (nextView === 'stock' && !canManageStock.value) {
    showNotification('Tu rol no permite modificar stock.', 'error');
    return;
  }
  if (nextView === 'select' && !canSaveReports.value) {
    showNotification('Tu rol es de solo lectura.', 'error');
    return;
  }
  if (nextView === 'users' && !canManageUsers.value) {
    showNotification('Solo administracion puede gestionar usuarios.', 'error');
    return;
  }
  if (isCountingView(nextView)) {
    startCountTimer();
  } else if (isCountingView(view.value)) {
    resetCountTimer();
  }

  view.value = nextView;
  showDifferences.value = false;
  countAdditions.value = {};
  if (nextView !== 'custom-count') {
    activeCustomListId.value = null;
  }
  if (nextView !== 'reports') {
    showReportSearch.value = false;
    reportSearchDate.value = '';
    highlightedReportId.value = null;
    selectedReportId.value = null;
  }
  if (nextView !== 'stock') {
    stockMaterialSearch.value = '';
    showStockGasMaterials.value = false;
    showStockVaporMaterials.value = false;
    shownCustomStockLists.value = {};
  }
  if (nextView === 'users') {
    loadUsersList();
  }
}

async function loadUsersList() {
  if (!canManageUsers.value) return;
  usersLoading.value = true;
  try {
    usersList.value = await getUsers();
    try {
      areasList.value = await getAreas();
    } catch (areaError) {
      console.error(areaError);
      showNotification(getErrorMessage(areaError, 'Error cargando areas'), 'error');
    }
    if (isOwner.value) {
      newUserOrganizationId.value = newUserOrganizationId.value || selectedOrganizationId.value;
      const availableAreas = areasList.value.filter((area) => area.organization_id === newUserOrganizationId.value);
      if (!newUserAreaId.value && availableAreas[0]) {
        newUserAreaId.value = availableAreas[0].id;
      }
    } else if (!newUserAreaId.value && areasList.value[0]) {
      newUserAreaId.value = areasList.value[0].id;
    }
  } catch (error) {
    console.error(error);
    showNotification(getErrorMessage(error, 'Error cargando usuarios.'), 'error');
  } finally {
    usersLoading.value = false;
  }
}

function roleLabel(role: UserRole) {
  return roleOptions.find((option) => option.value === role)?.label || role;
}

function organizationLabel(organizationId?: string) {
  return organizationsList.value.find((organization) => organization.id === organizationId)?.name || 'Sin hospital';
}

function areaLabel(areaId?: string) {
  if (isOwner.value && !areaId) return 'Todas las sedes';
  return areasList.value.find((area) => area.id === areaId)?.name || 'Sin area';
}

function ensureOwnerContext() {
  if (!isOwner.value) return;

  if (!selectedOrganizationId.value && organizationsList.value[0]) {
    selectedOrganizationId.value = organizationsList.value[0].id;
  }
  const availableAreas = areasList.value.filter((area) => area.organization_id === selectedOrganizationId.value);
  if (selectedAreaId.value && !availableAreas.some((area) => area.id === selectedAreaId.value)) {
    selectedAreaId.value = '';
  }
  setActiveContext(selectedOrganizationId.value, selectedAreaId.value);
}

async function changeOwnerContext() {
  if (!isOwner.value) return;
  const availableAreas = areasList.value.filter((area) => area.organization_id === selectedOrganizationId.value);
  if (selectedAreaId.value && !availableAreas.some((area) => area.id === selectedAreaId.value)) {
    selectedAreaId.value = '';
  }
  setActiveContext(selectedOrganizationId.value, selectedAreaId.value);
  await loadData();
  if (view.value === 'users') {
    await loadUsersList();
  }
}

async function createAppOrganization() {
  const name = newOrganizationName.value.trim();
  if (!name) {
    showNotification('Escribe el nombre del hospital.', 'error');
    return;
  }

  try {
    const organization = await createOrganization(name);
    organizationsList.value = [...organizationsList.value, organization];
    newUserOrganizationId.value = organization.id;
    newOrganizationName.value = '';
    showNotification(`Hospital "${organization.name}" creado correctamente. Tu vista actual no cambio.`);
  } catch (error) {
    console.error(error);
    showNotification(getErrorMessage(error, 'Error creando hospital'), 'error');
  }
}

async function createAppArea() {
  const name = newAreaName.value.trim();
  if (!name) {
    showNotification('Escribe el nombre del area.', 'error');
    return;
  }
  if (isOwner.value && !selectedOrganizationId.value) {
    showNotification('Selecciona un hospital antes de crear una sede.', 'error');
    return;
  }

  try {
    const organizationId = isOwner.value ? selectedOrganizationId.value : undefined;
    const area = await createArea(name, organizationId);
    areasList.value = [...areasList.value, area];
    selectedAreaId.value = area.id;
    setActiveContext(selectedOrganizationId.value, selectedAreaId.value);
    newUserAreaId.value = area.id;
    newAreaName.value = '';
    showNotification(`Area "${area.name}" creada correctamente.`);
  } catch (error) {
    console.error(error);
    showNotification(getErrorMessage(error, 'Error creando area'), 'error');
  }
}

async function createAppUser() {
  if (!newUserName.value.trim() || !newUsername.value.trim() || !newUserPassword.value) {
    showNotification('Completa nombre, usuario y contrasena.', 'error');
    return;
  }

  try {
    const created = await createUser({
      name: newUserName.value.trim(),
      username: newUsername.value.trim(),
      password: newUserPassword.value,
      role: newUserRole.value,
      organization_id: isOwner.value ? newUserOrganizationId.value || selectedOrganizationId.value : undefined,
      area_id: newUserAreaId.value || undefined,
    });
    usersList.value = [...usersList.value, created];
    newUserName.value = '';
    newUsername.value = '';
    newUserPassword.value = '';
    newUserRole.value = 'nurse';
    newUserOrganizationId.value = isOwner.value ? selectedOrganizationId.value : '';
    showNotification(`Usuario "${created.name}" creado correctamente.`);
  } catch (error) {
    console.error(error);
    showNotification(getErrorMessage(error, 'Error creando usuario'), 'error');
  }
}

function startUserEdit(user: AuthUser) {
  editingUserId.value = user.id;
  editingUserName.value = user.name;
  editingUsername.value = user.username;
  editingUserRole.value = user.role;
  editingUserOrganizationId.value = user.organization_id;
  editingUserAreaId.value = user.area_id;
  editingUserPassword.value = '';
}

function cancelUserEdit() {
  editingUserId.value = null;
  editingUserName.value = '';
  editingUsername.value = '';
  editingUserPassword.value = '';
  editingUserRole.value = 'nurse';
  editingUserOrganizationId.value = '';
  editingUserAreaId.value = '';
}

async function saveUserEdit(userId: string) {
  try {
    const payload: Partial<{ name: string; username: string; password: string; role: UserRole; organization_id: string; area_id: string }> = {
      name: editingUserName.value.trim(),
      username: editingUsername.value.trim(),
      role: editingUserRole.value,
      organization_id: isOwner.value ? editingUserOrganizationId.value : undefined,
      area_id: editingUserAreaId.value,
    };
    if (editingUserPassword.value) {
      payload.password = editingUserPassword.value;
    }
    const updated = await updateUser(userId, payload);
    usersList.value = usersList.value.map((user) => (user.id === userId ? updated : user));
    if (currentUser.value?.id === userId) {
      currentUser.value = updated;
    }
    cancelUserEdit();
    showNotification('Usuario actualizado correctamente.');
  } catch (error) {
    console.error(error);
    showNotification(getErrorMessage(error, 'Error actualizando usuario'), 'error');
  }
}

async function removeUser(user: AuthUser) {
  try {
    await deleteUser(user.id);
    usersList.value = usersList.value.filter((item) => item.id !== user.id);
    showNotification(`Usuario "${user.name}" eliminado correctamente.`);
  } catch (error) {
    console.error(error);
    showNotification(getErrorMessage(error, 'Error eliminando usuario'), 'error');
  }
}

function startCustomCount(listId: string) {
  activeCustomListId.value = listId;
  setView('custom-count');
}

function updateCustomListMaterials(listId: string, updater: (materials: Material[]) => Material[]) {
  customMaterialLists.value = customMaterialLists.value.map((list) =>
    list.id === listId ? { ...list, materials: updater(list.materials) } : list
  );
}

function getReportTypeLabel(type: string) {
  if (type === 'gas') return 'Gas';
  if (type === 'vapor') return 'Vapor';
  return customMaterialLists.value.find((list) => list.id === type)?.name || 'Lista personalizada';
}

function handleCountedChange(id: string, counted: number, type: CountTarget) {
  if (type === 'gas' || type === 'vapor') {
    const collection = type === 'gas' ? materialsGas : materialsVapor;
    collection.value = collection.value.map((material) =>
      material.id === id ? { ...material, counted } : material
    );
    return;
  }

  updateCustomListMaterials(type, (materials) =>
    materials.map((material) => (material.id === id ? { ...material, counted } : material))
  );
}

function showCalculatedDifferences() {
  countAdditions.value = currentMaterials.value.reduce<Record<string, CountAdditions>>((acc, material) => {
    acc[material.id] = countAdditions.value[material.id] || { room: 0, process: 0 };
    return acc;
  }, {});
  showDifferences.value = true;
}

function updateCountAddition(materialId: string, field: keyof CountAdditions, value: number) {
  const current = countAdditions.value[materialId] || { room: 0, process: 0 };
  countAdditions.value = {
    ...countAdditions.value,
    [materialId]: {
      ...current,
      [field]: Math.max(0, Number(value) || 0),
    },
  };
}

function handleAdditionInput(event: Event, materialId: string, field: keyof CountAdditions) {
  const input = event.target as HTMLInputElement;
  updateCountAddition(materialId, field, Number(input.value));
}

function reportBaseCount(diff: ReportDifference) {
  return diff.counted - (diff.room_count || 0) - (diff.process_count || 0);
}

function formatDifference(value: number) {
  return value > 0 ? `+${value}` : String(value);
}

function normalizeSearchText(value: string) {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase();
}

function filterMaterialsByName(materials: Material[], searchValue: string) {
  const search = normalizeSearchText(searchValue);
  if (!search) return materials;

  return materials.filter((material) => normalizeSearchText(material.name).includes(search));
}

function handleStockMaterialSearch(event: Event) {
  const input = event.target as HTMLInputElement;
  if (!input.value.trim()) {
    showStockGasMaterials.value = false;
    showStockVaporMaterials.value = false;
    shownCustomStockLists.value = {};
    return;
  }

  showStockGasMaterials.value = filterMaterialsByName(materialsGas.value, input.value).length > 0;
  showStockVaporMaterials.value = filterMaterialsByName(materialsVapor.value, input.value).length > 0;
  shownCustomStockLists.value = Object.fromEntries(
    customMaterialLists.value.map((list) => [
      list.id,
      filterMaterialsByName(list.materials, input.value).length > 0,
    ])
  );
}

function clearStockMaterialSearch() {
  stockMaterialSearch.value = '';
  showStockGasMaterials.value = false;
  showStockVaporMaterials.value = false;
  shownCustomStockLists.value = {};
}

function getReportDate(timestamp: string) {
  const date = new Date(timestamp);
  return Number.isNaN(date.getTime()) ? null : date;
}

function isReportInNurseEditWindow(report: Report) {
  const reportDate = getReportDate(report.timestamp);
  if (!reportDate) return false;

  const age = Date.now() - reportDate.getTime();
  return age >= 0 && age <= reportEditWindowMs;
}

function canEditReport(report: Report) {
  if (currentUser.value?.role === 'admin' || currentUser.value?.role === 'supervisor') {
    return true;
  }
  return currentUser.value?.role === 'nurse' && isReportInNurseEditWindow(report);
}

function formatReportTimestamp(timestamp: string) {
  const date = getReportDate(timestamp);
  if (!date) return timestamp;

  return new Intl.DateTimeFormat('es-MX', {
    timeZone: reportTimeZone,
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date);
}

function getReportDateKey(timestamp: string) {
  const date = getReportDate(timestamp);
  if (!date) return timestamp.slice(0, 10);

  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: reportTimeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(date);

  const year = parts.find((part) => part.type === 'year')?.value;
  const month = parts.find((part) => part.type === 'month')?.value;
  const day = parts.find((part) => part.type === 'day')?.value;

  return year && month && day ? `${year}-${month}-${day}` : timestamp.slice(0, 10);
}

function handleDifferenceCountInput(event: Event, materialId: string) {
  const input = event.target as HTMLInputElement;
  handleCountedChange(materialId, Number(input.value), currentType.value);
}

function resetCountingPage(type: CountTarget) {
  if (type === 'gas' || type === 'vapor') {
    const collection = type === 'gas' ? materialsGas : materialsVapor;
    collection.value = collection.value.map((material) => ({ ...material, counted: 0 }));
  } else {
    updateCustomListMaterials(type, (materials) =>
      materials.map((material) => ({ ...material, counted: 0 }))
    );
  }
  showDifferences.value = false;
  countAdditions.value = {};
  reportUserName.value = '';
  reportShift.value = '';
  resetCountTimer();
}

async function createNewMaterialList() {
  const name = newListName.value.trim();
  if (!name) {
    showNotification('Escribe el nombre de la nueva lista.', 'error');
    return;
  }

  try {
    const addedList = await createMaterialList(name);
    customMaterialLists.value = [...customMaterialLists.value, addedList];
    newMaterialType.value = addedList.id;
    shownCustomStockLists.value = { ...shownCustomStockLists.value, [addedList.id]: true };
    showNewListForm.value = false;
    newListName.value = '';
    showNotification(`Lista "${addedList.name}" creada correctamente.`);
  } catch (error) {
    console.error(error);
    showNotification('Error creando la nueva lista.', 'error');
  }
}

async function addMaterial(destination: string) {
  if (!newMaterialName.value.trim()) return;

  const payload = {
    name: newMaterialName.value.trim(),
    existing: newMaterialExisting.value,
    counted: 0,
    description: newMaterialDescription.value,
  };

  try {
    if (destination === 'gas') {
      const addedMaterial = await addMaterialGas(payload);
      materialsGas.value = [...materialsGas.value, addedMaterial];
    } else if (destination === 'vapor') {
      const addedMaterial = await addMaterialVapor(payload);
      materialsVapor.value = [...materialsVapor.value, addedMaterial];
    } else {
      const addedMaterial = await addCustomMaterial(destination, payload);
      customMaterialLists.value = customMaterialLists.value.map((list) =>
        list.id === destination ? { ...list, materials: [...list.materials, addedMaterial] } : list
      );
      shownCustomStockLists.value = { ...shownCustomStockLists.value, [destination]: true };
    }
    showNotification(`Material "${payload.name}" agregado correctamente.`);
    newMaterialName.value = '';
    newMaterialExisting.value = 0;
    newMaterialDescription.value = '';
  } catch (error) {
    console.error(error);
    showNotification('Error agregando material', 'error');
  }
}

async function deleteMaterial(id: string, type: MaterialType) {
  const collection = type === 'gas' ? materialsGas : materialsVapor;
  const materialName = collection.value.find((material) => material.id === id)?.name || 'Material';

  try {
    if (type === 'gas') {
      await deleteMaterialGas(id);
    } else {
      await deleteMaterialVapor(id);
    }
    collection.value = collection.value.filter((material) => material.id !== id);
    showNotification(`Material "${materialName}" eliminado correctamente.`);
  } catch (error) {
    console.error(error);
    showNotification('Error eliminando material', 'error');
  }
}

function startEditing(material: Material, type: MaterialType) {
  editingCustomListId.value = null;
  editingId.value = material.id;
  editingType.value = type;
  editingTargetType.value = type;
  editingName.value = material.name;
  editingExisting.value = material.existing;
  editingDescription.value = material.description;
}

function cancelEdit() {
  editingId.value = null;
  editingType.value = null;
  editingCustomListId.value = null;
  editingTargetType.value = 'gas';
  editingName.value = '';
  editingExisting.value = 0;
  editingDescription.value = '';
}

async function saveEdit() {
  if (!editingId.value || !editingType.value) return;

  const collection = editingType.value === 'gas' ? materialsGas : materialsVapor;
  const currentMaterial = collection.value.find((material) => material.id === editingId.value);
  const payload = {
    id: editingId.value,
    name: editingName.value.trim(),
    existing: editingExisting.value,
    counted: currentMaterial?.counted || 0,
    description: editingDescription.value,
  };

  try {
    if (editingTargetType.value === editingType.value) {
      const updatedMaterial =
        editingType.value === 'gas'
          ? await updateMaterialGas(editingId.value, payload)
          : await updateMaterialVapor(editingId.value, payload);

      collection.value = collection.value.map((material) =>
        material.id === editingId.value ? updatedMaterial : material
      );
    } else if (editingTargetType.value === 'gas' || editingTargetType.value === 'vapor') {
      const movedMaterial = await changeMaterialType(editingType.value, editingId.value, {
        ...payload,
        type: editingTargetType.value,
      });
      collection.value = collection.value.filter((material) => material.id !== editingId.value);
      const targetCollection = editingTargetType.value === 'gas' ? materialsGas : materialsVapor;
      targetCollection.value = [...targetCollection.value, movedMaterial];
    } else {
      const movedMaterial = await addCustomMaterial(editingTargetType.value, payload);
      if (editingType.value === 'gas') {
        await deleteMaterialGas(editingId.value);
      } else {
        await deleteMaterialVapor(editingId.value);
      }
      collection.value = collection.value.filter((material) => material.id !== editingId.value);
      customMaterialLists.value = customMaterialLists.value.map((list) =>
        list.id === editingTargetType.value
          ? { ...list, materials: [...list.materials, movedMaterial] }
          : list
      );
      shownCustomStockLists.value = { ...shownCustomStockLists.value, [editingTargetType.value]: true };
    }
    showNotification(`Material "${payload.name}" actualizado correctamente.`);
    cancelEdit();
  } catch (error) {
    console.error(error);
    showNotification(getErrorMessage(error, 'Error actualizando material'), 'error');
  }
}

function startCustomMaterialEditing(material: Material, listId: string) {
  editingId.value = material.id;
  editingType.value = null;
  editingCustomListId.value = listId;
  editingTargetType.value = listId;
  editingName.value = material.name;
  editingExisting.value = material.existing;
  editingDescription.value = material.description;
}

async function saveCustomMaterialEdit(listId: string) {
  if (!editingId.value || editingCustomListId.value !== listId) return;
  const list = customMaterialLists.value.find((item) => item.id === listId);
  const currentMaterial = list?.materials.find((material) => material.id === editingId.value);
  const payload = {
    id: editingId.value,
    name: editingName.value.trim(),
    existing: editingExisting.value,
    counted: currentMaterial?.counted || 0,
    description: editingDescription.value,
  };

  try {
    if (editingTargetType.value === listId) {
      const updatedMaterial = await updateCustomMaterial(listId, editingId.value, payload);
      customMaterialLists.value = customMaterialLists.value.map((item) =>
        item.id === listId
          ? {
              ...item,
              materials: item.materials.map((material) =>
                material.id === editingId.value ? updatedMaterial : material
              ),
            }
          : item
      );
    } else if (editingTargetType.value === 'gas' || editingTargetType.value === 'vapor') {
      const movedMaterial =
        editingTargetType.value === 'gas'
          ? await addMaterialGas(payload)
          : await addMaterialVapor(payload);
      await deleteCustomMaterial(listId, editingId.value);
      customMaterialLists.value = customMaterialLists.value.map((item) =>
        item.id === listId
          ? { ...item, materials: item.materials.filter((material) => material.id !== editingId.value) }
          : item
      );
      const targetCollection = editingTargetType.value === 'gas' ? materialsGas : materialsVapor;
      targetCollection.value = [...targetCollection.value, movedMaterial];
    } else {
      const movedMaterial = await moveCustomMaterial(
        listId,
        editingId.value,
        editingTargetType.value,
        payload
      );
      customMaterialLists.value = customMaterialLists.value.map((item) => {
        if (item.id === listId) {
          return { ...item, materials: item.materials.filter((material) => material.id !== editingId.value) };
        }
        if (item.id === editingTargetType.value) {
          return { ...item, materials: [...item.materials, movedMaterial] };
        }
        return item;
      });
      shownCustomStockLists.value = { ...shownCustomStockLists.value, [editingTargetType.value]: true };
    }
    showNotification(`Material "${payload.name}" actualizado correctamente.`);
    cancelEdit();
  } catch (error) {
    console.error(error);
    showNotification(getErrorMessage(error, 'Error actualizando material'), 'error');
  }
}

async function removeCustomMaterial(listId: string, material: Material) {
  try {
    await deleteCustomMaterial(listId, material.id);
    customMaterialLists.value = customMaterialLists.value.map((list) =>
      list.id === listId
        ? { ...list, materials: list.materials.filter((item) => item.id !== material.id) }
        : list
    );
    showNotification(`Material "${material.name}" eliminado correctamente.`);
  } catch (error) {
    console.error(error);
    showNotification('Error eliminando material', 'error');
  }
}

async function saveReport(type: CountTarget, reportDifferences: ReportDifference[]) {
  const userName = reportUserName.value.trim();
  const shift = reportShift.value.trim();
  if (!userName || !shift) {
    showNotification('Agrega nombre de usuario y turno antes de guardar el reporte.', 'error');
    return;
  }

  try {
    updateCountElapsed();
    const durationSeconds = countElapsedSeconds.value;
    const newReport = await createReport({
      type,
      user_name: userName,
      shift,
      duration_seconds: durationSeconds,
      differences: reportDifferences.map((diff) => ({
        material_id: diff.id,
        material_name: diff.name,
        existing_count: diff.existing,
        counted_count: diff.counted,
        room_count: diff.room_count || 0,
        process_count: diff.process_count || 0,
        difference: diff.difference,
      })),
    });
    reports.value = [newReport, ...reports.value];
    resetCountingPage(type);
    reportSearchDate.value = '';
    showReportSearch.value = false;
    highlightedReportId.value = newReport.id;
    selectedReportId.value = newReport.id;
    view.value = 'reports';
    showNotification(`Reporte de ${getReportTypeLabel(type)} guardado correctamente.`);
  } catch (error) {
    console.error(error);
    showNotification('Error guardando reporte', 'error');
  }
}

function startReportEdit(report: Report) {
  editingReportId.value = report.id;
  editReportUserName.value = report.user_name || '';
  editReportShift.value = report.shift || '';
  editReportDifferences.value = report.differences.map((diff) => ({ ...diff }));
  editReportMaterialSearch.value = '';
}

function cancelReportEdit() {
  editingReportId.value = null;
  editReportUserName.value = '';
  editReportShift.value = '';
  editReportDifferences.value = [];
  editReportMaterialSearch.value = '';
}

function updateEditReportField(
  materialId: string,
  field: 'base' | 'room_count' | 'process_count',
  value: number
) {
  editReportDifferences.value = editReportDifferences.value.map((diff) => {
    if (diff.id !== materialId) return diff;

    const roomCount = field === 'room_count' ? Math.max(0, value || 0) : diff.room_count || 0;
    const processCount =
      field === 'process_count' ? Math.max(0, value || 0) : diff.process_count || 0;
    const baseCount =
      field === 'base' ? Math.max(0, value || 0) : reportBaseCount(diff);
    const counted = baseCount + roomCount + processCount;

    return {
      ...diff,
      counted,
      room_count: roomCount,
      process_count: processCount,
      difference: counted - diff.existing,
    };
  });
}

function handleEditReportInput(
  event: Event,
  materialId: string,
  field: 'base' | 'room_count' | 'process_count'
) {
  const input = event.target as HTMLInputElement;
  updateEditReportField(materialId, field, Number(input.value));
}

async function saveReportEdit(report: Report) {
  const userName = editReportUserName.value.trim();
  const shift = editReportShift.value.trim();
  if (!userName || !shift) {
    showNotification('Agrega nombre de usuario y turno antes de guardar el reporte.', 'error');
    return;
  }

  try {
    const updatedReport = await updateReport(report.id, {
      type: report.type,
      user_name: userName,
      shift,
      duration_seconds: report.duration_seconds || 0,
      differences: editReportDifferences.value.map((diff) => ({
        material_id: diff.id,
        material_name: diff.name,
        existing_count: diff.existing,
        counted_count: diff.counted,
        room_count: diff.room_count || 0,
        process_count: diff.process_count || 0,
        difference: diff.difference,
      })),
    });
    reports.value = reports.value.map((item) => (item.id === report.id ? updatedReport : item));
    cancelReportEdit();
    showNotification('Reporte actualizado correctamente.');
  } catch (error) {
    console.error(error);
    showNotification('Error actualizando reporte', 'error');
  }
}

function handleCountInput(event: Event, materialId: string, type: CountTarget) {
  const input = event.target as HTMLInputElement;
  handleCountedChange(materialId, Number(input.value), type);
}

function focusNextCountInput(event: KeyboardEvent) {
  const input = event.currentTarget as HTMLInputElement;
  const currentItem = input.closest('li');
  const nextInput = currentItem?.nextElementSibling?.querySelector<HTMLInputElement>('.count-input');

  if (nextInput) {
    nextInput.focus();
    nextInput.select();
    nextInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
    return;
  }

  const calculateButton = document.querySelector<HTMLButtonElement>('.calculate-differences-button');
  calculateButton?.focus();
  calculateButton?.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function markMaterialComplete(material: Material, type: CountTarget) {
  handleCountedChange(material.id, material.existing, type);
}

function reorderMaterials(collection: Material[], draggedId: string, targetId: string) {
  const draggedIndex = collection.findIndex((material) => material.id === draggedId);
  const targetIndex = collection.findIndex((material) => material.id === targetId);
  if (draggedIndex === -1 || targetIndex === -1 || draggedIndex === targetIndex) return collection;

  const reordered = [...collection];
  const [dragged] = reordered.splice(draggedIndex, 1);
  reordered.splice(targetIndex, 0, dragged);
  return reordered;
}

function handleMaterialDragStart(material: Material, type: MaterialType) {
  draggingMaterial.value = { id: material.id, type };
}

function handleMaterialDragEnd() {
  draggingMaterial.value = null;
}

async function handleMaterialDrop(targetMaterial: Material, targetType: MaterialType) {
  const dragged = draggingMaterial.value;
  draggingMaterial.value = null;
  if (!dragged || dragged.type !== targetType || dragged.id === targetMaterial.id) return;

  const collection = targetType === 'gas' ? materialsGas : materialsVapor;
  const previousOrder = collection.value;
  const reordered = reorderMaterials(collection.value, dragged.id, targetMaterial.id);
  if (reordered === previousOrder) return;

  collection.value = reordered;

  try {
    const savedOrder = await updateMaterialOrder(targetType, reordered.map((material) => material.id));
    collection.value = savedOrder;
    showNotification('Orden de materiales actualizado correctamente.');
  } catch (error) {
    console.error(error);
    collection.value = previousOrder;
    showNotification(getErrorMessage(error, 'Error actualizando el orden de materiales'), 'error');
  }
}

function handleCustomMaterialDragStart(material: Material, listId: string) {
  draggingCustomMaterial.value = { id: material.id, listId };
}

function handleCustomMaterialDragEnd() {
  draggingCustomMaterial.value = null;
}

async function handleCustomMaterialDrop(targetMaterial: Material, listId: string) {
  const dragged = draggingCustomMaterial.value;
  draggingCustomMaterial.value = null;
  if (!dragged || dragged.listId !== listId || dragged.id === targetMaterial.id) return;

  const list = customMaterialLists.value.find((item) => item.id === listId);
  if (!list) return;
  const previousOrder = list.materials;
  const reordered = reorderMaterials(list.materials, dragged.id, targetMaterial.id);
  if (reordered === previousOrder) return;

  customMaterialLists.value = customMaterialLists.value.map((item) =>
    item.id === listId ? { ...item, materials: reordered } : item
  );

  try {
    const savedOrder = await updateCustomMaterialOrder(listId, reordered.map((material) => material.id));
    customMaterialLists.value = customMaterialLists.value.map((item) =>
      item.id === listId ? { ...item, materials: savedOrder } : item
    );
    showNotification('Orden de materiales actualizado correctamente.');
  } catch (error) {
    console.error(error);
    customMaterialLists.value = customMaterialLists.value.map((item) =>
      item.id === listId ? { ...item, materials: previousOrder } : item
    );
    showNotification(getErrorMessage(error, 'Error actualizando el orden de materiales'), 'error');
  }
}

function toggleReportSearch() {
  showReportSearch.value = !showReportSearch.value;
}

function clearReportSearch() {
  reportSearchDate.value = '';
  selectedReportId.value = null;
}

function selectReport(reportId: string) {
  selectedReportId.value = reportId;
}

function closeSelectedReport() {
  selectedReportId.value = null;
}

async function printReport(reportId: string) {
  printingReportId.value = reportId;
  document.body.classList.add('printing-report');
  await nextTick();

  const finishPrinting = () => {
    printingReportId.value = null;
    document.body.classList.remove('printing-report');
    window.removeEventListener('afterprint', finishPrinting);
  };

  window.addEventListener('afterprint', finishPrinting);
  window.print();
}

</script>

<template>
  <section v-if="!currentUser" class="login-page">
    <div class="login-rain" aria-hidden="true">
      <span v-for="index in 28" :key="index" class="rain-item">
        <svg v-if="index % 4 === 0" viewBox="0 0 48 48">
          <path d="M14 36h20" />
          <path d="M18 14v20" />
          <path d="M14 14h8" />
          <path d="M31 13 24 35" />
          <path d="M34 13 41 35" />
        </svg>
        <svg v-else-if="index % 4 === 1" viewBox="0 0 48 48">
          <path d="M10 36h28" />
          <path d="M14 30h4v6h-4z" />
          <path d="M22 22h4v14h-4z" />
          <path d="M30 15h4v21h-4z" />
        </svg>
        <svg v-else-if="index % 4 === 2" viewBox="0 0 48 48">
          <path d="M24 10v28" />
          <path d="M10 24h28" />
          <circle cx="24" cy="24" r="14" />
        </svg>
        <svg v-else viewBox="0 0 48 48">
          <path d="M12 30c7-7 17-7 24 0" />
          <path d="M15 21c5-5 13-5 18 0" />
          <path d="M20 15c3-3 5-3 8 0" />
          <path d="M24 30v8" />
        </svg>
      </span>
    </div>
    <div v-if="notification" :class="['notification', notification.type]">
      {{ notification.message }}
    </div>
    <form class="login-card" @submit.prevent="handleLogin">
      <span class="eyebrow">Acceso seguro</span>
      <h1>HyunSia</h1>
      <p>Inicia sesion con tu cuenta.</p>
      <input
        v-model="loginUsername"
        type="text"
        autocomplete="username"
        inputmode="text"
        pattern="[A-Za-z0-9]+"
        placeholder="Nombre de usuario"
      />
      <input
        v-model="loginPassword"
        type="password"
        autocomplete="current-password"
        placeholder="Contrasena"
      />
      <button class="success-button" type="submit" :disabled="loginLoading">
        {{ loginLoading ? 'Ingresando...' : 'Ingresar' }}
      </button>
    </form>
  </section>

  <main v-else>
    <aside class="sidebar no-print">
      <div class="sidebar-brand">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 64 64" role="img">
            <rect x="10" y="39" width="44" height="10" rx="3" fill="none" stroke="currentColor" stroke-width="4" />
            <path d="M14 39h36" fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="4" />
            <path d="M19 16v20" fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="4" />
            <path d="M15 16h8" fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="4" />
            <path d="M33 15 26 36" fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="4" />
            <path d="M37 15 44 36" fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="4" />
            <path d="M32 15h6" fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="4" />
          </svg>
        </span>
        <div>
          <strong>Ceye Qx</strong>
          <span>Inventario</span>
        </div>
      </div>
      <nav class="sidebar-nav" aria-label="Navegacion principal">
        <button :class="{ active: view === 'home' }" @click="setView('home')">Inicio</button>
        <button
          v-if="canSaveReports"
          :class="{ active: view === 'select' || view === 'gas' || view === 'vapor' || view === 'custom-count' }"
          @click="setView('select')"
        >
          Conteo
        </button>
        <button v-if="canManageStock" :class="{ active: view === 'stock' }" @click="setView('stock')">Stock</button>
        <button :class="{ active: view === 'reports' }" @click="setView('reports')">Reportes</button>
        <button v-if="canManageUsers" :class="{ active: view === 'users' }" @click="setView('users')">Usuarios</button>
      </nav>
      <div class="sidebar-status">
        <span>{{ stockMaterialCount }}</span>
        <small>materiales activos</small>
      </div>
      <div class="sidebar-user">
        <strong>{{ currentUser.name }}</strong>
        <span>{{ roleLabel(currentUser.role) }}</span>
        <span>{{ currentOrganizationName }}</span>
        <span>{{ currentAreaName }}</span>
        <button type="button" class="ghost-button" @click.stop="handleLogout">Salir</button>
      </div>
    </aside>

    <div class="app-shell">
      <div v-if="notification" :class="['notification', notification.type]">
        {{ notification.message }}
      </div>

      <section v-if="view === 'home'" class="dashboard">
        <div v-if="isOwner" class="section-block owner-context-panel">
          <h2>Vista global del creador</h2>
          <select v-model="selectedOrganizationId" @change="changeOwnerContext">
            <option v-for="organization in organizationsList" :key="organization.id" :value="organization.id">
              {{ organization.name }}
            </option>
          </select>
          <select v-model="selectedAreaId" @change="changeOwnerContext">
            <option value="">Todas las sedes</option>
            <option v-for="area in filteredAreasList" :key="area.id" :value="area.id">
              {{ area.name }}
            </option>
          </select>
        </div>

        <div class="dashboard-hero">
          <div class="dashboard-identity">
            <span class="eyebrow">Panel principal</span>
            <h1>{{ currentOrganizationName }}</h1>
            <div class="dashboard-location-card">
              <span>Nombre de sede</span>
              <strong>{{ currentAreaName }}</strong>
            </div>
            <p>Inventario, conteos y reportes operativos del área asignada.</p>
          </div>
          <div class="dashboard-actions">
            <button v-if="canSaveReports" @click="setView('select')">Nuevo Conteo</button>
            <button v-if="canManageStock" class="success-button" @click="setView('stock')">Gestionar Stock</button>
            <button class="warning-button" @click="setView('reports')">Ver Reportes</button>
          </div>
        </div>

        <div class="dashboard-stats">
          <article v-for="stat in dashboardStats" :key="stat.label" class="stat-card">
            <span>{{ stat.label }}</span>
            <strong>{{ stat.value }}</strong>
            <small>{{ stat.detail }}</small>
          </article>
        </div>

        <div class="chart-grid">
          <section class="dashboard-panel chart-panel">
            <h2>Materiales por categoria</h2>
            <div class="bar-chart">
              <div v-for="item in inventoryChartData" :key="item.label" class="chart-row">
                <div class="chart-row-label">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.value }}</strong>
                </div>
                <div class="chart-track">
                  <div :class="['chart-bar', item.color]" :style="{ width: `${item.percent}%` }"></div>
                </div>
              </div>
            </div>
          </section>

          <section class="dashboard-panel chart-panel">
            <h2>Reportes por tipo</h2>
            <div v-if="reportPieData.length" class="pie-chart-layout">
              <div class="pie-chart" :style="reportPieStyle">
                <span>{{ reports.length }}</span>
              </div>
              <div class="pie-legend">
                <div v-for="item in reportPieData" :key="item.label" class="pie-legend-item">
                  <span :class="['legend-dot', item.color]"></span>
                  <div>
                    <strong>{{ item.label }}</strong>
                    <small>{{ item.value }} reportes - {{ item.share }}%</small>
                  </div>
                </div>
              </div>
            </div>
            <p v-else class="empty-search-result">No hay reportes para graficar.</p>
          </section>
        </div>

        <div class="dashboard-grid">
          <section class="dashboard-panel">
            <h2>Accesos rapidos</h2>
            <div class="quick-actions">
              <button v-if="canSaveReports" @click="setView('select')">Conteo de Inventario</button>
              <button v-if="canManageStock" class="success-button" @click="setView('stock')">Gestionar Stock</button>
              <button class="warning-button" @click="setView('reports')">Ver Reportes</button>
              <button v-if="canManageUsers" class="info-button" @click="setView('users')">Usuarios</button>
            </div>
          </section>

          <section class="dashboard-panel">
            <h2>Distribucion</h2>
            <div class="inventory-breakdown">
              <div>
                <span>Gas</span>
                <strong>{{ materialsGas.length }}</strong>
              </div>
              <div>
                <span>Vapor</span>
                <strong>{{ materialsVapor.length }}</strong>
              </div>
              <div>
                <span>Personalizados</span>
                <strong>{{ customMaterialCount }}</strong>
              </div>
            </div>
          </section>

          <section class="dashboard-panel dashboard-panel-wide">
            <h2>Ultimo reporte</h2>
            <div v-if="latestReport" class="latest-report">
              <div>
                <strong>Conteo de {{ getReportTypeLabel(latestReport.type) }}</strong>
                <span>{{ formatReportTimestamp(latestReport.timestamp) }}</span>
              </div>
              <button class="info-button" @click="setView('reports')">Abrir Reportes</button>
            </div>
            <p v-else class="empty-search-result">No hay reportes guardados.</p>
          </section>
        </div>
      </section>

      <section v-else-if="view === 'select'">
      <h1>Seleccionar Tipo de Conteo</h1>
      <div class="count-selection-actions">
        <button @click="setView('gas')">Contar Gas</button>
        <button @click="setView('vapor')">Contar Vapor</button>
        <button
          v-for="list in customMaterialLists"
          :key="list.id"
          @click="startCustomCount(list.id)"
        >
          Contar {{ list.name }}
        </button>
        <button @click="setView('home')">Volver</button>
      </div>
    </section>

    <section v-else-if="view === 'stock'">
      <h1>Gestion de Stock - Materiales</h1>
      <button @click="setView('home')">Volver</button>

      <div v-if="!canManageStock" class="stock-lock-panel">
        <strong>Sin permiso para modificar stock</strong>
        <span>Tu cuenta puede consultar informacion, pero no administrar materiales.</span>
      </div>

      <div v-else class="section-block">
        <h2>Agregar Nuevo Material</h2>
        <select v-model="newMaterialType">
          <option v-for="option in materialListOptions" :key="option.id" :value="option.id">
            {{ option.name }}
          </option>
        </select>
        <input v-model="newMaterialName" type="text" placeholder="Nombre del material" />
        <input v-model="newMaterialDescription" type="text" placeholder="Descripcion del material" />
        <input v-model.number="newMaterialExisting" type="number" placeholder="Cantidad en stock" />
        <button @click="addMaterial(newMaterialType)">Agregar Material</button>
        <button class="info-button" @click="showNewListForm = !showNewListForm">
          {{ showNewListForm ? 'Cancelar nueva lista' : 'Agregar Nueva Lista' }}
        </button>
        <div v-if="showNewListForm" class="new-list-form">
          <input
            v-model="newListName"
            type="text"
            placeholder="Nombre de la nueva lista"
            @keyup.enter="createNewMaterialList"
          />
          <button class="success-button" @click="createNewMaterialList">Crear Lista</button>
        </div>
      </div>

      <div v-if="canManageStock" class="section-block stock-material-search">
        <h2>Buscar Material para Editar</h2>
        <div class="stock-search-controls">
          <input
            v-model="stockMaterialSearch"
            type="search"
            aria-label="Buscar material en stock"
            placeholder="Escribe el nombre del material..."
            @input="handleStockMaterialSearch"
          />
          <span>
            {{ filteredStockMaterialCount }} de {{ stockMaterialCount }} materiales
          </span>
          <button v-if="stockMaterialSearch" @click="clearStockMaterialSearch">Limpiar</button>
        </div>
      </div>

      <div v-if="canManageStock" class="section-block">
        <div class="stock-list-header">
          <h2>Materiales de Gas</h2>
          <button class="info-button" @click="showStockGasMaterials = !showStockGasMaterials">
            {{ showStockGasMaterials ? 'Ocultar lista' : 'Mostrar lista' }}
          </button>
        </div>
        <p v-if="showStockGasMaterials && filteredStockMaterialsGas.length === 0" class="empty-search-result">
          No se encontraron materiales de gas con ese nombre.
        </p>
        <ul v-if="showStockGasMaterials">
          <li
            v-for="material in filteredStockMaterialsGas"
            :key="material.id"
            class="draggable-material"
            draggable="true"
            @dragstart="handleMaterialDragStart(material, 'gas')"
            @dragend="handleMaterialDragEnd"
            @dragover.prevent
            @drop="handleMaterialDrop(material, 'gas')"
          >
            <div v-if="editingId === material.id && editingType === 'gas'" class="edit-form">
              <select v-model="editingTargetType" :disabled="!canDeleteData">
                <option v-for="option in materialListOptions" :key="option.id" :value="option.id">
                  {{ option.name }}
                </option>
              </select>
              <input v-model="editingName" type="text" placeholder="Nombre" />
              <input v-model="editingDescription" type="text" placeholder="Descripcion" />
              <input v-model.number="editingExisting" type="number" placeholder="Cantidad en stock" />
              <button @click="saveEdit">Guardar</button>
              <button @click="cancelEdit">Cancelar</button>
            </div>
            <div v-else class="material-item">
              <span><strong>{{ material.name }}</strong></span>
              <span>Stock: {{ material.existing }}</span>
              <button @click="startEditing(material, 'gas')">Editar</button>
              <button v-if="canDeleteData" class="danger-button" @click="deleteMaterial(material.id, 'gas')">Borrar</button>
            </div>
          </li>
        </ul>
      </div>

      <div v-if="canManageStock" class="section-block">
        <div class="stock-list-header">
          <h2>Materiales de Vapor</h2>
          <button class="info-button" @click="showStockVaporMaterials = !showStockVaporMaterials">
            {{ showStockVaporMaterials ? 'Ocultar lista' : 'Mostrar lista' }}
          </button>
        </div>
        <p v-if="showStockVaporMaterials && filteredStockMaterialsVapor.length === 0" class="empty-search-result">
          No se encontraron materiales de vapor con ese nombre.
        </p>
        <ul v-if="showStockVaporMaterials">
          <li
            v-for="material in filteredStockMaterialsVapor"
            :key="material.id"
            class="draggable-material"
            draggable="true"
            @dragstart="handleMaterialDragStart(material, 'vapor')"
            @dragend="handleMaterialDragEnd"
            @dragover.prevent
            @drop="handleMaterialDrop(material, 'vapor')"
          >
            <div v-if="editingId === material.id && editingType === 'vapor'" class="edit-form">
              <select v-model="editingTargetType" :disabled="!canDeleteData">
                <option v-for="option in materialListOptions" :key="option.id" :value="option.id">
                  {{ option.name }}
                </option>
              </select>
              <input v-model="editingName" type="text" placeholder="Nombre" />
              <input v-model="editingDescription" type="text" placeholder="Descripcion" />
              <input v-model.number="editingExisting" type="number" placeholder="Cantidad en stock" />
              <button @click="saveEdit">Guardar</button>
              <button @click="cancelEdit">Cancelar</button>
            </div>
            <div v-else class="material-item">
              <span><strong>{{ material.name }}</strong></span>
              <span>Stock: {{ material.existing }}</span>
              <button @click="startEditing(material, 'vapor')">Editar</button>
              <button v-if="canDeleteData" class="danger-button" @click="deleteMaterial(material.id, 'vapor')">Borrar</button>
            </div>
          </li>
        </ul>
      </div>

      <template v-if="canManageStock">
        <div
          v-for="list in filteredCustomMaterialLists"
          :key="list.id"
          class="section-block"
        >
          <div class="stock-list-header">
            <h2>{{ list.name }}</h2>
            <div class="stock-list-actions">
              <button class="info-button" @click="shownCustomStockLists[list.id] = !shownCustomStockLists[list.id]">
                {{ shownCustomStockLists[list.id] ? 'Ocultar lista' : 'Mostrar lista' }}
              </button>
            </div>
          </div>
          <p v-if="shownCustomStockLists[list.id] && list.materials.length === 0" class="empty-search-result">
            No se encontraron materiales en esta lista.
          </p>
          <ul v-if="shownCustomStockLists[list.id]">
            <li
              v-for="material in list.materials"
              :key="material.id"
              class="draggable-material"
              draggable="true"
              @dragstart="handleCustomMaterialDragStart(material, list.id)"
              @dragend="handleCustomMaterialDragEnd"
              @dragover.prevent
              @drop="handleCustomMaterialDrop(material, list.id)"
            >
              <div v-if="editingId === material.id && editingCustomListId === list.id" class="edit-form">
                <select v-model="editingTargetType" :disabled="!canDeleteData">
                  <option v-for="option in materialListOptions" :key="option.id" :value="option.id">
                    {{ option.name }}
                  </option>
                </select>
                <input v-model="editingName" type="text" placeholder="Nombre" />
                <input v-model="editingDescription" type="text" placeholder="Descripcion" />
                <input v-model.number="editingExisting" type="number" placeholder="Cantidad en stock" />
                <button @click="saveCustomMaterialEdit(list.id)">Guardar</button>
                <button @click="cancelEdit">Cancelar</button>
              </div>
              <div v-else class="material-item">
                <span><strong>{{ material.name }}</strong></span>
                <span>Stock: {{ material.existing }}</span>
                <button @click="startCustomMaterialEditing(material, list.id)">Editar</button>
                <button v-if="canDeleteData" class="danger-button" @click="removeCustomMaterial(list.id, material)">Borrar</button>
              </div>
            </li>
          </ul>
        </div>
      </template>
    </section>

    <section v-else-if="view === 'users'" class="users-page">
      <h1>Usuarios y roles</h1>
      <button @click="setView('home')">Volver</button>

      <div class="section-block user-form">
        <h2>Hospitales y sedes</h2>
        <template v-if="isOwner">
          <input v-model="newOrganizationName" type="text" placeholder="Nuevo hospital" @keyup.enter="createAppOrganization" />
          <button class="success-button" @click="createAppOrganization">Crear Hospital</button>
          <select v-model="selectedOrganizationId" @change="changeOwnerContext">
            <option v-for="organization in organizationsList" :key="organization.id" :value="organization.id">
              {{ organization.name }}
            </option>
          </select>
          <select v-model="selectedAreaId" @change="changeOwnerContext">
            <option value="">Todas las sedes</option>
            <option v-for="area in filteredAreasList" :key="area.id" :value="area.id">
              {{ area.name }}
            </option>
          </select>
        </template>
        <input v-model="newAreaName" type="text" placeholder="Nueva area" @keyup.enter="createAppArea" />
        <button class="info-button" @click="createAppArea">Crear Area</button>
      </div>

      <div class="section-block user-form">
        <h2>Crear cuenta</h2>
        <input v-model="newUserName" type="text" placeholder="Nombre completo" />
        <input
          v-model="newUsername"
          type="text"
          pattern="[A-Za-z0-9]+"
          placeholder="Nombre de usuario"
        />
        <input v-model="newUserPassword" type="password" placeholder="Contrasena temporal" />
        <select v-model="newUserRole">
          <option v-for="option in assignableRoleOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
        <select v-if="isOwner" v-model="newUserOrganizationId" @change="newUserAreaId = ''">
          <option v-for="organization in organizationsList" :key="organization.id" :value="organization.id">
            {{ organization.name }}
          </option>
        </select>
        <select v-model="newUserAreaId">
          <option
            v-for="area in areasList.filter((item) => !isOwner || item.organization_id === (newUserOrganizationId || selectedOrganizationId))"
            :key="area.id"
            :value="area.id"
          >
            {{ area.name }}
          </option>
        </select>
        <button class="success-button" @click="createAppUser">Crear Usuario</button>
      </div>

      <div class="section-block">
        <div class="stock-list-header">
          <h2>Cuentas activas</h2>
          <button class="info-button" @click="loadUsersList">
            {{ usersLoading ? 'Cargando...' : 'Actualizar' }}
          </button>
        </div>
        <div class="user-list">
          <article v-for="user in usersList" :key="user.id" class="user-card">
            <div v-if="editingUserId === user.id" class="edit-form user-edit-form">
              <input v-model="editingUserName" type="text" placeholder="Nombre" />
              <input
                v-model="editingUsername"
                type="text"
                pattern="[A-Za-z0-9]+"
                placeholder="Nombre de usuario"
              />
              <select v-model="editingUserRole">
                <option v-for="option in assignableRoleOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <select v-if="isOwner" v-model="editingUserOrganizationId" @change="editingUserAreaId = ''">
                <option v-for="organization in organizationsList" :key="organization.id" :value="organization.id">
                  {{ organization.name }}
                </option>
              </select>
              <select v-model="editingUserAreaId">
                <option
                  v-for="area in areasList.filter((item) => !isOwner || item.organization_id === editingUserOrganizationId)"
                  :key="area.id"
                  :value="area.id"
                >
                  {{ area.name }}
                </option>
              </select>
              <input v-model="editingUserPassword" type="password" placeholder="Nueva contrasena opcional" />
              <button class="success-button" @click="saveUserEdit(user.id)">Guardar</button>
              <button @click="cancelUserEdit">Cancelar</button>
            </div>
            <div v-else class="user-card-content">
              <div>
                <strong>{{ user.name }}</strong>
                <span>@{{ user.username }}</span>
              </div>
              <span class="role-pill">{{ roleLabel(user.role) }}</span>
              <span v-if="isOwner" class="role-pill">{{ organizationLabel(user.organization_id) }}</span>
              <span class="role-pill">{{ areaLabel(user.area_id) }}</span>
              <button v-if="user.role === 'owner'" class="info-button" disabled>Cuenta creadora</button>
              <button v-else class="info-button" @click="startUserEdit(user)">Editar</button>
              <button
                v-if="currentUser?.id !== user.id && user.role !== 'owner'"
                class="danger-button"
                @click="removeUser(user)"
              >
                Borrar
              </button>
            </div>
          </article>
        </div>
      </div>
    </section>

    <section v-else-if="view === 'reports'">
      <div class="reports-toolbar no-print">
        <button class="info-button" @click="toggleReportSearch">
          Buscar Reporte por Fecha
        </button>
      </div>
      <h1>Reportes de Conteo</h1>
      <button class="no-print" @click="setView('home')">Volver</button>

      <div v-if="showReportSearch" class="report-search-panel no-print">
        <input v-model="reportSearchDate" type="date" @change="selectedReportId = null" />
        <button @click="clearReportSearch">Limpiar Busqueda</button>
      </div>

      <p v-if="reports.length === 0">No hay reportes guardados.</p>
      <p v-else-if="filteredReports.length === 0">No hay reportes para la fecha seleccionada.</p>
      <div v-else-if="!selectedReport" class="report-card-grid">
        <article
          v-for="report in filteredReports"
          :key="report.id"
          :class="['report-card', { 'current-report': highlightedReportId === report.id }]"
        >
          <div v-if="highlightedReportId === report.id" class="current-report-label">
            Reporte guardado actualmente
          </div>
          <h2>Conteo de {{ getReportTypeLabel(report.type) }}</h2>
          <div class="report-card-meta">
            <span><strong>Fecha:</strong> {{ formatReportTimestamp(report.timestamp) }}</span>
            <span><strong>Usuario:</strong> {{ report.user_name || 'Sin usuario' }}</span>
            <span><strong>Turno:</strong> {{ report.shift || 'Sin turno' }}</span>
            <span><strong>Duracion:</strong> {{ formatDuration(report.duration_seconds || 0) }}</span>
            <span>
              <strong>Diferencias:</strong>
              {{ report.differences.filter((diff) => diff.difference !== 0).length }}
            </span>
          </div>
          <button class="info-button" @click="selectReport(report.id)">
            Visualizar Reporte
          </button>
        </article>
      </div>
      <div v-else>
        <div class="report-detail-toolbar no-print">
          <button @click="closeSelectedReport">Ver lista de reportes</button>
          <div class="report-detail-actions">
            <button
              v-if="editingReportId !== selectedReport.id && canEditReport(selectedReport)"
              class="info-button"
              @click="startReportEdit(selectedReport)"
            >
              Editar Reporte
            </button>
            <button
              v-if="editingReportId !== selectedReport.id"
              class="warning-button"
              @click="printReport(selectedReport.id)"
            >
              Imprimir Reporte
            </button>
            <button
              v-if="editingReportId === selectedReport.id"
              class="success-button"
              @click="saveReportEdit(selectedReport)"
            >
              Guardar Cambios del Reporte
            </button>
            <button v-if="editingReportId === selectedReport.id" @click="cancelReportEdit">
              Cancelar
            </button>
          </div>
        </div>
        <article
          :key="selectedReport.id"
          :class="[
            'report-block',
            {
              'current-report': highlightedReportId === selectedReport.id,
              'report-print-target': printingReportId === selectedReport.id,
            },
          ]"
        >
          <div v-if="highlightedReportId === selectedReport.id" class="current-report-label no-print">
            Reporte guardado actualmente
          </div>
          <h2>
            Conteo de {{ getReportTypeLabel(selectedReport.type) }}
            - {{ formatReportTimestamp(selectedReport.timestamp) }}
          </h2>
          <div v-if="editingReportId === selectedReport.id" class="report-meta edit-form">
            <input v-model="editReportUserName" type="text" placeholder="Nombre de usuario" />
            <input v-model="editReportShift" type="text" placeholder="Turno" />
          </div>
          <div v-else class="report-meta">
            <span><strong>Usuario:</strong> {{ selectedReport.user_name || 'Sin usuario' }}</span>
            <span><strong>Turno:</strong> {{ selectedReport.shift || 'Sin turno' }}</span>
            <span><strong>Duracion:</strong> {{ formatDuration(selectedReport.duration_seconds || 0) }}</span>
          </div>
          <div
            v-if="editingReportId === selectedReport.id"
            class="report-material-search no-print"
          >
            <input
              v-model="editReportMaterialSearch"
              type="search"
              aria-label="Buscar material para editar"
              placeholder="Buscar material por nombre..."
              autofocus
            />
            <span>
              {{ filteredEditReportDifferences.length }} de {{ editReportDifferences.length }} materiales
            </span>
            <button v-if="editReportMaterialSearch" @click="editReportMaterialSearch = ''">
              Limpiar
            </button>
          </div>
          <table class="report-differences-table">
            <thead>
              <tr>
                <th>Material</th>
                <th>Existencia</th>
                <th>Contado</th>
                <th>Material en sala</th>
                <th>Cargas en proceso</th>
                <th>Total contado</th>
                <th>Diferencia</th>
              </tr>
            </thead>
            <tbody v-if="editingReportId === selectedReport.id">
              <tr
                v-for="diff in filteredEditReportDifferences"
                :key="diff.id"
                :class="{ 'print-hide-no-difference': diff.difference === 0 }"
              >
                <td>{{ diff.name }}</td>
                <td>{{ diff.existing }}</td>
                <td>
                  <input
                    type="number"
                    min="0"
                    class="small-input"
                    :value="reportBaseCount(diff)"
                    @input="handleEditReportInput($event, diff.id, 'base')"
                  />
                </td>
                <td>
                  <input
                    type="number"
                    min="0"
                    class="small-input"
                    :value="diff.room_count || 0"
                    @input="handleEditReportInput($event, diff.id, 'room_count')"
                  />
                </td>
                <td>
                  <input
                    type="number"
                    min="0"
                    class="small-input"
                    :value="diff.process_count || 0"
                    @input="handleEditReportInput($event, diff.id, 'process_count')"
                  />
                </td>
                <td>{{ diff.counted }}</td>
                <td :class="diff.difference !== 0 ? 'difference-alert' : 'difference-ok'">
                  {{ formatDifference(diff.difference) }}
                </td>
              </tr>
              <tr v-if="filteredEditReportDifferences.length === 0">
                <td colspan="7" class="empty-search-result">
                  No se encontro ningun material con ese nombre.
                </td>
              </tr>
            </tbody>
            <tbody v-else>
              <tr
                v-for="diff in selectedReport.differences"
                :key="diff.id"
                :class="{ 'print-hide-no-difference': diff.difference === 0 }"
              >
                <td>{{ diff.name }}</td>
                <td>{{ diff.existing }}</td>
                <td>{{ reportBaseCount(diff) }}</td>
                <td>{{ diff.room_count || 0 }}</td>
                <td>{{ diff.process_count || 0 }}</td>
                <td>{{ diff.counted }}</td>
                <td :class="diff.difference !== 0 ? 'difference-alert' : 'difference-ok'">
                  {{ formatDifference(diff.difference) }}
                </td>
              </tr>
            </tbody>
          </table>
        </article>
      </div>
    </section>

    <section v-else>
      <h1>Contar {{ currentCountTitle }}</h1>
      <div class="count-page-toolbar">
        <button @click="setView('select')">Volver</button>
        <div class="count-timer-card" aria-live="polite">
          <span>Tiempo de conteo</span>
          <strong>{{ formatDuration(countElapsedSeconds) }}</strong>
        </div>
      </div>

      <ul>
        <li v-for="material in currentMaterials" :key="material.id">
          <div class="material-item">
            <div>
              <span><strong>{{ material.name }}</strong></span>
              <div class="material-description">{{ material.description || 'Sin descripcion' }}</div>
            </div>
            <span>Existente: {{ material.existing }}</span>
            <input
              class="count-input"
              type="number"
              placeholder="Contado"
              :value="material.counted"
              @input="handleCountInput($event, material.id, currentType)"
              @keydown.enter.prevent="focusNextCountInput"
            />
            <button class="success-button" @click="markMaterialComplete(material, currentType)">
              Completo
            </button>
          </div>
        </li>
      </ul>
      <button class="calculate-differences-button" @click="showCalculatedDifferences">
        Calcular Diferencias
      </button>

      <div v-if="showDifferences">
        <h2>Diferencias</h2>
        <div class="report-required-fields">
          <input v-model="reportUserName" type="text" placeholder="Nombre de usuario" required />
          <input v-model="reportShift" type="text" placeholder="Turno" required />
          <button
            v-if="canSaveReports"
            class="info-button save-report-button"
            @click="saveReport(currentType, adjustedDifferences)"
          >
            Guardar Reporte
          </button>
        </div>
        <table class="differences-table">
          <thead>
            <tr>
              <th>Material</th>
              <th>Existente</th>
              <th>Contado</th>
              <th>Material en sala</th>
              <th>Cargas en proceso</th>
              <th>Total contado</th>
              <th>Nueva diferencia</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="diff in adjustedDifferences" :key="diff.id">
              <td>{{ diff.name }}</td>
              <td>{{ diff.existing }}</td>
              <td>
                <input
                  type="number"
                  min="0"
                  class="small-input"
                  :value="reportBaseCount(diff)"
                  @input="handleDifferenceCountInput($event, diff.id)"
                />
              </td>
              <td>
                <input
                  type="number"
                  min="0"
                  class="small-input"
                  :value="diff.room_count || 0"
                  @input="handleAdditionInput($event, diff.id, 'room')"
                />
              </td>
              <td>
                <input
                  type="number"
                  min="0"
                  class="small-input"
                  :value="diff.process_count || 0"
                  @input="handleAdditionInput($event, diff.id, 'process')"
                />
              </td>
              <td>{{ diff.counted }}</td>
              <td :class="diff.difference !== 0 ? 'difference-alert' : 'difference-ok'">
                {{ formatDifference(diff.difference) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
    </div>
  </main>
</template>
