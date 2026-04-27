import React, { useState, useEffect } from 'react';
import './App.css';

interface Material {
  id: string;
  name: string;
  existing: number;
  counted: number;
  description: string;
}

interface ReportDifference extends Material {
  difference: number;
}

interface Report {
  id: string;
  type: 'gas' | 'vapor';
  timestamp: string;
  differences: ReportDifference[];
}

const App: React.FC = () => {
  const [view, setView] = useState<'home' | 'select' | 'gas' | 'vapor' | 'stock' | 'reports'>('home');
  const defaultGas: Material[] = [
    { id: '1', name: 'Oxígeno', existing: 100, counted: 0, description: 'Gas médico para respiración asistida' },
    { id: '2', name: 'Nitrógeno', existing: 50, counted: 0, description: 'Gas para sistemas de enfriamiento' },
  ];

  const defaultVapor: Material[] = [
    { id: '1', name: 'Vapor 1', existing: 20, counted: 0, description: 'Vapor utilizado en esterilización' },
    { id: '2', name: 'Vapor 2', existing: 30, counted: 0, description: 'Vapor para limpieza de equipo' },
  ];

  const loadMaterials = (key: string, fallback: Material[]) => {
    const saved = localStorage.getItem(key);
    if (!saved) return fallback;
    try {
      return JSON.parse(saved) as Material[];
    } catch {
      return fallback;
    }
  };

  const [materialsGas, setMaterialsGas] = useState<Material[]>(() => loadMaterials('materialsGas', defaultGas));
  const [materialsVapor, setMaterialsVapor] = useState<Material[]>(() => loadMaterials('materialsVapor', defaultVapor));
  const [newMaterialName, setNewMaterialName] = useState('');
  const [newMaterialExisting, setNewMaterialExisting] = useState(0);
  const [newMaterialDescription, setNewMaterialDescription] = useState('');
  const [newMaterialType, setNewMaterialType] = useState<'gas' | 'vapor'>('gas');
  const [showDifferences, setShowDifferences] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingType, setEditingType] = useState<'gas' | 'vapor' | null>(null);
  const [editingName, setEditingName] = useState('');
  const [editingExisting, setEditingExisting] = useState(0);
  const [editingDescription, setEditingDescription] = useState('');
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [reports, setReports] = useState<Report[]>(() => {
    const saved = localStorage.getItem('reports');
    if (!saved) return [];
    try {
      return JSON.parse(saved);
    } catch {
      return [];
    }
  });

  // Guardar reportes en localStorage
  useEffect(() => {
    localStorage.setItem('reports', JSON.stringify(reports));
  }, [reports]);
  useEffect(() => {
    localStorage.setItem('materialsGas', JSON.stringify(materialsGas));
  }, [materialsGas]);

  useEffect(() => {
    localStorage.setItem('materialsVapor', JSON.stringify(materialsVapor));
  }, [materialsVapor]);

  const showNotification = (message: string, type: 'success' | 'error' = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const handleCountedChange = (id: string, counted: number, type: 'gas' | 'vapor') => {
    if (type === 'gas') {
      setMaterialsGas(materialsGas.map(m => m.id === id ? { ...m, counted } : m));
    } else {
      setMaterialsVapor(materialsVapor.map(m => m.id === id ? { ...m, counted } : m));
    }
  };

  const deleteMaterial = (id: string, type: 'gas' | 'vapor') => {
    const materialToDelete = type === 'gas' 
      ? materialsGas.find(m => m.id === id)?.name 
      : materialsVapor.find(m => m.id === id)?.name;
    
    if (type === 'gas') {
      setMaterialsGas(materialsGas.filter(m => m.id !== id));
    } else {
      setMaterialsVapor(materialsVapor.filter(m => m.id !== id));
    }
    showNotification(`✓ Material "${materialToDelete}" eliminado correctamente.`);
  };

  const startEditing = (material: Material, type: 'gas' | 'vapor') => {
    setEditingId(material.id);
    setEditingType(type);
    setEditingName(material.name);
    setEditingExisting(material.existing);
    setEditingDescription(material.description);
  };

  const saveEdit = () => {
    if (!editingId || !editingType) return;
    if (editingType === 'gas') {
      setMaterialsGas(materialsGas.map(m => m.id === editingId ? { ...m, name: editingName, existing: editingExisting, description: editingDescription } : m));
    } else {
      setMaterialsVapor(materialsVapor.map(m => m.id === editingId ? { ...m, name: editingName, existing: editingExisting, description: editingDescription } : m));
    }
    showNotification(`✓ Material "${editingName}" actualizado correctamente. Cambios guardados permanentemente.`);
    setEditingId(null);
    setEditingType(null);
    setEditingName('');
    setEditingExisting(0);
    setEditingDescription('');
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditingType(null);
    setEditingName('');
    setEditingExisting(0);
  };

  const addMaterial = (type: 'gas' | 'vapor') => {
    const newMaterial: Material = {
      id: Date.now().toString(),
      name: newMaterialName,
      existing: newMaterialExisting,
      counted: 0,
      description: newMaterialDescription,
    };
    if (type === 'gas') {
      setMaterialsGas([...materialsGas, newMaterial]);
    } else {
      setMaterialsVapor([...materialsVapor, newMaterial]);
    }
    setNewMaterialName('');
    setNewMaterialExisting(0);
    setNewMaterialDescription('');
    showNotification(`✓ Material "${newMaterial.name}" agregado correctamente. Se ha guardado permanentemente.`);
  };

  const calculateDifferences = (materials: Material[]) => {
    return materials.map(m => ({ ...m, difference: m.counted - m.existing }));
  };

  const saveReport = (type: 'gas' | 'vapor', differences: ReportDifference[]) => {
    const newReport: Report = {
      id: Date.now().toString(),
      type,
      timestamp: new Date().toLocaleString('es-ES'),
      differences,
    };
    setReports([newReport, ...reports]);
    showNotification(`✓ Reporte de ${type === 'gas' ? 'Gas' : 'Vapor'} guardado correctamente.`);
    setShowDifferences(false);
  };

  const updateReportDifference = (reportId: string, materialId: string, addedCounted: number) => {
    setReports(reports.map(report => {
      if (report.id === reportId) {
        return {
          ...report,
          differences: report.differences.map(diff => {
            if (diff.id === materialId) {
              return { ...diff, counted: diff.counted + addedCounted, difference: (diff.counted + addedCounted) - diff.existing };
            }
            return diff;
          }),
        };
      }
      return report;
    }));
    showNotification('✓ Material agregado al reporte.');
  };

  if (view === 'home') {
    return (
      <div>
        {notification && (
          <div className={`notification ${notification.type}`}>
            {notification.message}
          </div>
        )}
        <h1>App de Inventario - Ceye Quirófano</h1>
        <button onClick={() => setView('select')}>Conteo de Inventario</button>
        <button onClick={() => setView('stock')} style={{ backgroundColor: '#28a745' }}>Gestionar Stock de Materiales</button>
        <button onClick={() => setView('reports')} style={{ backgroundColor: '#ffc107' }}>Ver Reportes de Conteo</button>
      </div>
    );
  }

  if (view === 'stock') {
    return (
      <div>
        {notification && (
          <div className={`notification ${notification.type}`}>
            {notification.message}
          </div>
        )}
        <h1>Gestión de Stock - Materiales</h1>
        <button onClick={() => setView('home')}>Volver</button>
        
        <div style={{ marginTop: '30px' }}>
          <h2>Agregar Nuevo Material</h2>
          <select value={newMaterialType} onChange={(e) => setNewMaterialType(e.target.value as 'gas' | 'vapor')}>
            <option value="gas">Gas</option>
            <option value="vapor">Vapor</option>
          </select>
          <input
            type="text"
            placeholder="Nombre del material"
            value={newMaterialName}
            onChange={(e) => setNewMaterialName(e.target.value)}
          />
          <input
            type="text"
            placeholder="Descripción del material"
            value={newMaterialDescription}
            onChange={(e) => setNewMaterialDescription(e.target.value)}
          />
          <input
            type="text"
            placeholder="Descripción del material"
            value={newMaterialDescription}
            onChange={(e) => setNewMaterialDescription(e.target.value)}
          />
          <input
            type="number"
            placeholder="Cantidad en stock"
            value={newMaterialExisting}
            onChange={(e) => setNewMaterialExisting(Number(e.target.value))}
          />
          <button onClick={() => {
            if (newMaterialName.trim()) {
              addMaterial(newMaterialType);
              setNewMaterialName('');
              setNewMaterialDescription('');
              setNewMaterialExisting(0);
            }
          }}>Agregar Material</button>
        </div>

        <div style={{ marginTop: '30px' }}>
          <h2>Materiales de Gas</h2>
          <ul>
            {materialsGas.map(material => (
              <li key={material.id}>
                {editingId === material.id && editingType === 'gas' ? (
                  <div className="edit-form">
                    <input
                      type="text"
                      value={editingName}
                      onChange={(e) => setEditingName(e.target.value)}
                      placeholder="Nombre"
                    />
                    <input
                      type="text"
                      value={editingDescription}
                      onChange={(e) => setEditingDescription(e.target.value)}
                      placeholder="Descripción"
                    />
                    <input
                      type="number"
                      value={editingExisting}
                      onChange={(e) => setEditingExisting(Number(e.target.value))}
                      placeholder="Cantidad en stock"
                    />
                    <button onClick={saveEdit}>Guardar</button>
                    <button onClick={cancelEdit}>Cancelar</button>
                  </div>
                ) : (
                  <div className="material-item">
                    <span><strong>{material.name}</strong></span>
                    <span>Stock: {material.existing}</span>
                    <button onClick={() => startEditing(material, 'gas')}>Editar</button>
                    <button onClick={() => deleteMaterial(material.id, 'gas')} style={{ backgroundColor: 'red' }}>Borrar</button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>

        <div style={{ marginTop: '30px' }}>
          <h2>Materiales de Vapor</h2>
          <ul>
            {materialsVapor.map(material => (
              <li key={material.id}>
                {editingId === material.id && editingType === 'vapor' ? (
                  <div className="edit-form">
                    <input
                      type="text"
                      value={editingName}
                      onChange={(e) => setEditingName(e.target.value)}
                      placeholder="Nombre"
                    />
                    <input
                      type="text"
                      value={editingDescription}
                      onChange={(e) => setEditingDescription(e.target.value)}
                      placeholder="Descripción"
                    />
                    <input
                      type="number"
                      value={editingExisting}
                      onChange={(e) => setEditingExisting(Number(e.target.value))}
                      placeholder="Cantidad en stock"
                    />
                    <button onClick={saveEdit}>Guardar</button>
                    <button onClick={cancelEdit}>Cancelar</button>
                  </div>
                ) : (
                  <div className="material-item">
                    <span><strong>{material.name}</strong></span>
                    <span>Stock: {material.existing}</span>
                    <button onClick={() => startEditing(material, 'vapor')}>Editar</button>
                    <button onClick={() => deleteMaterial(material.id, 'vapor')} style={{ backgroundColor: 'red' }}>Borrar</button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>
    );
  }

  if (view === 'reports') {
    return (
      <div>
        {notification && (
          <div className={`notification ${notification.type}`}>
            {notification.message}
          </div>
        )}
        <h1>Reportes de Conteo</h1>
        <button onClick={() => setView('home')}>Volver</button>
        
        {reports.length === 0 ? (
          <p>No hay reportes guardados.</p>
        ) : (
          <div>
            {reports.map(report => (
              <div key={report.id} style={{ marginTop: '30px', padding: '20px', border: '1px solid #ddd', borderRadius: '5px' }}>
                <h2>{report.type === 'gas' ? 'Conteo de Gas' : 'Conteo de Vapor'} - {report.timestamp}</h2>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f5f5f5' }}>
                      <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Material</th>
                      <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Existencia</th>
                      <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Contado</th>
                      <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Diferencia</th>
                      <th style={{ border: '1px solid #ddd', padding: '8px', textAlign: 'left' }}>Agregar Material</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.differences.map(diff => (
                      <tr key={diff.id}>
                        <td style={{ border: '1px solid #ddd', padding: '8px' }}>{diff.name}</td>
                        <td style={{ border: '1px solid #ddd', padding: '8px' }}>{diff.existing}</td>
                        <td style={{ border: '1px solid #ddd', padding: '8px' }}>{diff.counted}</td>
                        <td style={{ border: '1px solid #ddd', padding: '8px', color: diff.difference !== 0 ? 'red' : 'green', fontWeight: 'bold' }}>{diff.difference}</td>
                        <td style={{ border: '1px solid #ddd', padding: '8px' }}>
                          <input
                            type="number"
                            placeholder="Cantidad"
                            min="0"
                            onKeyPress={(e) => {
                              if (e.key === 'Enter') {
                                const input = e.target as HTMLInputElement;
                                const value = Number(input.value);
                                if (value > 0) {
                                  updateReportDifference(report.id, diff.id, value);
                                  input.value = '';
                                }
                              }
                            }}
                            style={{ width: '80px' }}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }
    return (
      <div>
        {notification && (
          <div className={`notification ${notification.type}`}>
            {notification.message}
          </div>
        )}
        <h1>Seleccionar Tipo de Conteo</h1>
        <button onClick={() => setView('gas')}>Contar Gas</button>
        <button onClick={() => setView('vapor')}>Contar Vapor</button>
        <button onClick={() => setView('home')}>Volver</button>
      </div>
    );
  }

  const currentMaterials = view === 'gas' ? materialsGas : materialsVapor;
  const setCurrentMaterials = view === 'gas' ? setMaterialsGas : setMaterialsVapor;
  const type = view;

  const differences = calculateDifferences(currentMaterials);

  return (
    <div>
      {notification && (
        <div className={`notification ${notification.type}`}>
          {notification.message}
        </div>
      )}
      <h1>Contar {type === 'gas' ? 'Gas' : 'Vapor'}</h1>
      <button onClick={() => setView('select')}>Volver</button>
      <ul>
        {currentMaterials.map(material => (
          <li key={material.id}>
            <div className="material-item">
              <div>
                <span><strong>{material.name}</strong></span>
                <div className="material-description">{material.description || 'Sin descripción'}</div>
              </div>
              <span>Existente: {material.existing}</span>
              <input
                type="number"
                placeholder="Contado"
                value={material.counted}
                onChange={(e) => handleCountedChange(material.id, Number(e.target.value), type)}
              />
            </div>
          </li>
        ))}
      </ul>
      <button onClick={() => setShowDifferences(true)}>Calcular Diferencias</button>
      {showDifferences && (
        <div>
          <h2>Diferencias</h2>
          <ul>
            {differences.map(diff => (
              <li key={diff.id} style={{ color: diff.difference !== 0 ? 'red' : 'green' }}>
                {diff.name}: {diff.difference}
              </li>
            ))}
          </ul>
          <button onClick={() => saveReport(type, differences)} style={{ backgroundColor: '#17a2b8' }}>Guardar Reporte</button>
        </div>
      )}
    </div>
  );
};

export default App;