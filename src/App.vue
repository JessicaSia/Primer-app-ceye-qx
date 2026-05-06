<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import {
  addMaterialGas,
  addMaterialVapor,
  createReport,
  deleteMaterialGas,
  deleteMaterialVapor,
  getMaterialsGas,
  getMaterialsVapor,
  getReports,
  summarizeGasInventory,
  updateReport,
  updateMaterialGas,
  updateMaterialVapor,
} from './api';

type View = 'home' | 'select' | 'gas' | 'vapor' | 'stock' | 'reports';
type MaterialType = 'gas' | 'vapor';

interface Material {
  id: string;
  name: string;
  existing: number;
  counted: number;
  description: string;
}

interface ReportDifference extends Material {
  difference: number;
  room_count?: number;
  process_count?: number;
}

interface Report {
  id: string;
  type: MaterialType;
  user_name: string;
  shift: string;
  timestamp: string;
  differences: ReportDifference[];
}

interface CountAdditions {
  room: number;
  process: number;
}

const view = ref<View>('home');
const materialsGas = ref<Material[]>([]);
const materialsVapor = ref<Material[]>([]);
const reports = ref<Report[]>([]);
const updatedReports = ref<string[]>([]);
const showDifferences = ref(false);
const newMaterialName = ref('');
const newMaterialExisting = ref(0);
const newMaterialDescription = ref('');
const newMaterialType = ref<MaterialType>('gas');
const editingId = ref<string | null>(null);
const editingType = ref<MaterialType | null>(null);
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
const showReportSearch = ref(false);
const reportSearchDate = ref('');
const highlightedReportId = ref<string | null>(null);
const stockPassword = ref('');
const stockAuthenticated = ref(false);
const gasSummary = ref('');
const gasSummaryLoading = ref(false);
const gasSummaryError = ref('');

const currentType = computed<MaterialType>(() => (view.value === 'gas' ? 'gas' : 'vapor'));
const currentMaterials = computed(() => (currentType.value === 'gas' ? materialsGas.value : materialsVapor.value));
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
const filteredReports = computed(() => {
  if (!reportSearchDate.value) return reports.value;
  return reports.value.filter((report) => report.timestamp.slice(0, 10) === reportSearchDate.value);
});

onMounted(() => {
  loadData();
});

async function loadData() {
  try {
    const [gasData, vaporData, reportData] = await Promise.all([
      getMaterialsGas(),
      getMaterialsVapor(),
      getReports(),
    ]);
    materialsGas.value = gasData;
    materialsVapor.value = vaporData;
    reports.value = reportData;
  } catch (error) {
    console.error(error);
    showNotification('Error cargando datos', 'error');
  }
}

function showNotification(message: string, type: 'success' | 'error' = 'success') {
  notification.value = { message, type };
  window.setTimeout(() => {
    notification.value = null;
  }, 3000);
}

function setView(nextView: View) {
  view.value = nextView;
  showDifferences.value = false;
  countAdditions.value = {};
  if (nextView !== 'gas') {
    gasSummary.value = '';
    gasSummaryError.value = '';
  }
  if (nextView !== 'reports') {
    showReportSearch.value = false;
    reportSearchDate.value = '';
    highlightedReportId.value = null;
  }
}

function handleCountedChange(id: string, counted: number, type: MaterialType) {
  const collection = type === 'gas' ? materialsGas : materialsVapor;
  collection.value = collection.value.map((material) =>
    material.id === id ? { ...material, counted } : material
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

async function generateGasSummary() {
  gasSummaryLoading.value = true;
  gasSummaryError.value = '';

  try {
    const response = await summarizeGasInventory(materialsGas.value);
    gasSummary.value = response.summary;
  } catch (error) {
    console.error(error);
    gasSummaryError.value = error instanceof Error ? error.message : 'Error generando resumen AI';
  } finally {
    gasSummaryLoading.value = false;
  }
}

function handleDifferenceCountInput(event: Event, materialId: string) {
  const input = event.target as HTMLInputElement;
  handleCountedChange(materialId, Number(input.value), currentType.value);
}

function resetCountingPage(type: MaterialType) {
  const collection = type === 'gas' ? materialsGas : materialsVapor;
  collection.value = collection.value.map((material) => ({ ...material, counted: 0 }));
  showDifferences.value = false;
  countAdditions.value = {};
  reportUserName.value = '';
  reportShift.value = '';
}

async function addMaterial(type: MaterialType) {
  if (!newMaterialName.value.trim()) return;

  const payload = {
    name: newMaterialName.value.trim(),
    existing: newMaterialExisting.value,
    counted: 0,
    description: newMaterialDescription.value,
  };

  try {
    const addedMaterial =
      type === 'gas' ? await addMaterialGas(payload) : await addMaterialVapor(payload);
    if (type === 'gas') {
      materialsGas.value = [...materialsGas.value, addedMaterial];
    } else {
      materialsVapor.value = [...materialsVapor.value, addedMaterial];
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
  editingId.value = material.id;
  editingType.value = type;
  editingName.value = material.name;
  editingExisting.value = material.existing;
  editingDescription.value = material.description;
}

function cancelEdit() {
  editingId.value = null;
  editingType.value = null;
  editingName.value = '';
  editingExisting.value = 0;
  editingDescription.value = '';
}

async function saveEdit() {
  if (!editingId.value || !editingType.value) return;

  const collection = editingType.value === 'gas' ? materialsGas : materialsVapor;
  const currentMaterial = collection.value.find((material) => material.id === editingId.value);
  const payload = {
    name: editingName.value.trim(),
    existing: editingExisting.value,
    counted: currentMaterial?.counted || 0,
    description: editingDescription.value,
  };

  try {
    const updatedMaterial =
      editingType.value === 'gas'
        ? await updateMaterialGas(editingId.value, payload)
        : await updateMaterialVapor(editingId.value, payload);

    collection.value = collection.value.map((material) =>
      material.id === editingId.value ? updatedMaterial : material
    );
    showNotification(`Material "${payload.name}" actualizado correctamente.`);
    cancelEdit();
  } catch (error) {
    console.error(error);
    showNotification('Error actualizando material', 'error');
  }
}

async function saveReport(type: MaterialType, reportDifferences: ReportDifference[]) {
  const userName = reportUserName.value.trim();
  const shift = reportShift.value.trim();
  if (!userName || !shift) {
    showNotification('Agrega nombre de usuario y turno antes de guardar el reporte.', 'error');
    return;
  }

  try {
    const newReport = await createReport({
      type,
      user_name: userName,
      shift,
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
    view.value = 'reports';
    showNotification(`Reporte de ${type === 'gas' ? 'Gas' : 'Vapor'} guardado correctamente.`);
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
}

function cancelReportEdit() {
  editingReportId.value = null;
  editReportUserName.value = '';
  editReportShift.value = '';
  editReportDifferences.value = [];
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

async function saveStockUpdate(report: Report) {
  const collection = report.type === 'gas' ? materialsGas : materialsVapor;

  try {
    for (const difference of report.differences) {
      const material = collection.value.find((item) => item.id === difference.id);
      if (!material) continue;
      const payload = {
        name: material.name,
        existing: difference.counted,
        counted: 0,
        description: material.description,
      };
      if (report.type === 'gas') {
        await updateMaterialGas(material.id, payload);
      } else {
        await updateMaterialVapor(material.id, payload);
      }
    }

    collection.value = collection.value.map((material) => {
      const reportDiff = report.differences.find((diff) => diff.id === material.id);
      return reportDiff ? { ...material, existing: reportDiff.counted, counted: 0 } : material;
    });
    updatedReports.value = [...updatedReports.value, report.id];
    showNotification(`Stock de ${report.type === 'gas' ? 'Gas' : 'Vapor'} actualizado correctamente.`);
  } catch (error) {
    console.error(error);
    showNotification('Error actualizando stock', 'error');
  }
}

function handleCountInput(event: Event, materialId: string, type: MaterialType) {
  const input = event.target as HTMLInputElement;
  handleCountedChange(materialId, Number(input.value), type);
}

function markMaterialComplete(material: Material, type: MaterialType) {
  handleCountedChange(material.id, material.existing, type);
}

function toggleReportSearch() {
  showReportSearch.value = !showReportSearch.value;
}

function clearReportSearch() {
  reportSearchDate.value = '';
}

function unlockStockPage() {
  if (stockPassword.value === 'PrimerappJESSI9') {
    stockAuthenticated.value = true;
    stockPassword.value = '';
    showNotification('Acceso autorizado.');
    return;
  }

  showNotification('Contraseña incorrecta.', 'error');
}
</script>

<template>
  <main>
    <div v-if="notification" :class="['notification', notification.type]">
      {{ notification.message }}
    </div>

    <section v-if="view === 'home'">
      <h1>App de Inventario - Ceye Quirofano</h1>
      <button @click="setView('select')">Conteo de Inventario</button>
      <button class="success-button" @click="setView('stock')">Gestionar Stock de Materiales</button>
      <button class="warning-button" @click="setView('reports')">Ver Reportes de Conteo</button>
    </section>

    <section v-else-if="view === 'select'">
      <h1>Seleccionar Tipo de Conteo</h1>
      <button @click="setView('gas')">Contar Gas</button>
      <button @click="setView('vapor')">Contar Vapor</button>
      <button @click="setView('home')">Volver</button>
    </section>

    <section v-else-if="view === 'stock'">
      <h1>Gestion de Stock - Materiales</h1>
      <button @click="setView('home')">Volver</button>

      <div v-if="!stockAuthenticated" class="stock-lock-panel">
        <input
          v-model="stockPassword"
          type="password"
          placeholder="Contraseña"
          @keyup.enter="unlockStockPage"
        />
        <button class="success-button" @click="unlockStockPage">Ingresar</button>
      </div>

      <div v-else class="section-block">
        <h2>Agregar Nuevo Material</h2>
        <select v-model="newMaterialType">
          <option value="gas">Gas</option>
          <option value="vapor">Vapor</option>
        </select>
        <input v-model="newMaterialName" type="text" placeholder="Nombre del material" />
        <input v-model="newMaterialDescription" type="text" placeholder="Descripcion del material" />
        <input v-model.number="newMaterialExisting" type="number" placeholder="Cantidad en stock" />
        <button @click="addMaterial(newMaterialType)">Agregar Material</button>
      </div>

      <div v-if="stockAuthenticated" class="section-block">
        <h2>Materiales de Gas</h2>
        <ul>
          <li v-for="material in materialsGas" :key="material.id">
            <div v-if="editingId === material.id && editingType === 'gas'" class="edit-form">
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
              <button class="danger-button" @click="deleteMaterial(material.id, 'gas')">Borrar</button>
            </div>
          </li>
        </ul>
      </div>

      <div v-if="stockAuthenticated" class="section-block">
        <h2>Materiales de Vapor</h2>
        <ul>
          <li v-for="material in materialsVapor" :key="material.id">
            <div v-if="editingId === material.id && editingType === 'vapor'" class="edit-form">
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
              <button class="danger-button" @click="deleteMaterial(material.id, 'vapor')">Borrar</button>
            </div>
          </li>
        </ul>
      </div>
    </section>

    <section v-else-if="view === 'reports'">
      <div class="reports-toolbar">
        <button class="info-button" @click="toggleReportSearch">
          Buscar Reporte por Fecha
        </button>
      </div>
      <h1>Reportes de Conteo</h1>
      <button @click="setView('home')">Volver</button>

      <div v-if="showReportSearch" class="report-search-panel">
        <input v-model="reportSearchDate" type="date" />
        <button @click="clearReportSearch">Limpiar Busqueda</button>
      </div>

      <p v-if="reports.length === 0">No hay reportes guardados.</p>
      <p v-else-if="filteredReports.length === 0">No hay reportes para la fecha seleccionada.</p>
      <div v-else>
        <article
          v-for="report in filteredReports"
          :key="report.id"
          :class="['report-block', { 'current-report': highlightedReportId === report.id }]"
        >
          <div v-if="highlightedReportId === report.id" class="current-report-label">
            Reporte guardado actualmente
          </div>
          <h2>{{ report.type === 'gas' ? 'Conteo de Gas' : 'Conteo de Vapor' }} - {{ report.timestamp }}</h2>
          <div v-if="editingReportId === report.id" class="report-meta edit-form">
            <input v-model="editReportUserName" type="text" placeholder="Nombre de usuario" />
            <input v-model="editReportShift" type="text" placeholder="Turno" />
          </div>
          <div v-else class="report-meta">
            <span><strong>Usuario:</strong> {{ report.user_name || 'Sin usuario' }}</span>
            <span><strong>Turno:</strong> {{ report.shift || 'Sin turno' }}</span>
          </div>
          <table>
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
            <tbody v-if="editingReportId === report.id">
              <tr v-for="diff in editReportDifferences" :key="diff.id">
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
            </tbody>
            <tbody v-else>
              <tr v-for="diff in report.differences" :key="diff.id">
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
          <button
            v-if="editingReportId !== report.id"
            class="info-button"
            @click="startReportEdit(report)"
          >
            Editar Reporte
          </button>
          <button
            v-if="editingReportId === report.id"
            class="success-button"
            @click="saveReportEdit(report)"
          >
            Guardar Cambios del Reporte
          </button>
          <button v-if="editingReportId === report.id" @click="cancelReportEdit">
            Cancelar
          </button>
          <button
            v-if="editingReportId !== report.id"
            class="success-button"
            @click="saveStockUpdate(report)"
          >
            Guardar Actualizacion de Stock
          </button>

          <div v-if="updatedReports.includes(report.id)" class="stock-summary">
            <h3>Actualizacion de Stock Completada</h3>
            <table>
              <thead>
                <tr>
                  <th>Material</th>
                  <th>Stock Anterior</th>
                  <th>Nuevo Stock</th>
                  <th>Cambio</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="diff in report.differences" :key="diff.id">
                  <td><strong>{{ diff.name }}</strong></td>
                  <td>{{ diff.existing }}</td>
                  <td>{{ diff.counted }}</td>
                  <td>{{ formatDifference(diff.difference) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </article>
      </div>
    </section>

    <section v-else>
      <h1>Contar {{ currentType === 'gas' ? 'Gas' : 'Vapor' }}</h1>
      <button @click="setView('select')">Volver</button>

      <div v-if="currentType === 'gas'" class="ai-summary-panel">
        <div class="ai-summary-header">
          <h2>Resumen AI de Gas</h2>
          <button class="info-button" :disabled="gasSummaryLoading" @click="generateGasSummary">
            {{ gasSummaryLoading ? 'Generando...' : 'Generar Resumen AI' }}
          </button>
        </div>
        <p v-if="gasSummaryError" class="ai-summary-error">{{ gasSummaryError }}</p>
        <p v-else-if="gasSummary" class="ai-summary-text">{{ gasSummary }}</p>
        <p v-else class="ai-summary-muted">Genera un resumen rapido del conteo actual de gas.</p>
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
              type="number"
              placeholder="Contado"
              :value="material.counted"
              @input="handleCountInput($event, material.id, currentType)"
            />
            <button class="success-button" @click="markMaterialComplete(material, currentType)">
              Completo
            </button>
          </div>
        </li>
      </ul>
      <button @click="showCalculatedDifferences">Calcular Diferencias</button>

      <div v-if="showDifferences">
        <h2>Diferencias</h2>
        <div class="report-required-fields">
          <input v-model="reportUserName" type="text" placeholder="Nombre de usuario" required />
          <input v-model="reportShift" type="text" placeholder="Turno" required />
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
        <button class="info-button" @click="saveReport(currentType, adjustedDifferences)">
          Guardar Reporte
        </button>
      </div>
    </section>
  </main>
</template>
