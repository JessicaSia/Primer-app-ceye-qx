import React, { useState } from 'react';
import './App.css';

interface Material {
  id: string;
  name: string;
  existing: number;
  counted: number;
}

const App: React.FC = () => {
  const [view, setView] = useState<'home' | 'select' | 'gas' | 'vapor'>('home');
  const [materialsGas, setMaterialsGas] = useState<Material[]>([
    { id: '1', name: 'Oxígeno', existing: 100, counted: 0 },
    { id: '2', name: 'Nitrógeno', existing: 50, counted: 0 },
  ]);
  const [materialsVapor, setMaterialsVapor] = useState<Material[]>([
    { id: '1', name: 'Vapor 1', existing: 20, counted: 0 },
    { id: '2', name: 'Vapor 2', existing: 30, counted: 0 },
  ]);
  const [newMaterialName, setNewMaterialName] = useState('');
  const [newMaterialExisting, setNewMaterialExisting] = useState(0);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showDifferences, setShowDifferences] = useState(false);

  const handleCountedChange = (id: string, counted: number, type: 'gas' | 'vapor') => {
    if (type === 'gas') {
      setMaterialsGas(materialsGas.map(m => m.id === id ? { ...m, counted } : m));
    } else {
      setMaterialsVapor(materialsVapor.map(m => m.id === id ? { ...m, counted } : m));
    }
  };

  const addMaterial = (type: 'gas' | 'vapor') => {
    const newMaterial: Material = {
      id: Date.now().toString(),
      name: newMaterialName,
      existing: newMaterialExisting,
      counted: 0,
    };
    if (type === 'gas') {
      setMaterialsGas([...materialsGas, newMaterial]);
    } else {
      setMaterialsVapor([...materialsVapor, newMaterial]);
    }
    setNewMaterialName('');
    setNewMaterialExisting(0);
    setShowAddForm(false);
  };

  const calculateDifferences = (materials: Material[]) => {
    return materials.map(m => ({ ...m, difference: m.counted - m.existing }));
  };

  if (view === 'home') {
    return (
      <div>
        <h1>App de Inventario - Ceye Quirófano</h1>
        <button onClick={() => setView('select')}>Conteo de Inventario</button>
      </div>
    );
  }

  if (view === 'select') {
    return (
      <div>
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
      <h1>Contar {type === 'gas' ? 'Gas' : 'Vapor'}</h1>
      <button onClick={() => setView('select')}>Volver</button>
      <button onClick={() => setShowAddForm(!showAddForm)}>Agregar Material</button>
      {showAddForm && (
        <div>
          <input
            type="text"
            placeholder="Nombre del material"
            value={newMaterialName}
            onChange={(e) => setNewMaterialName(e.target.value)}
          />
          <input
            type="number"
            placeholder="Cantidad existente"
            value={newMaterialExisting}
            onChange={(e) => setNewMaterialExisting(Number(e.target.value))}
          />
          <button onClick={() => addMaterial(type)}>Agregar</button>
        </div>
      )}
      <ul>
        {currentMaterials.map(material => (
          <li key={material.id}>
            <span>{material.name}</span>
            <span>Existente: {material.existing}</span>
            <input
              type="number"
              placeholder="Contado"
              value={material.counted}
              onChange={(e) => handleCountedChange(material.id, Number(e.target.value), type)}
            />
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
        </div>
      )}
    </div>
  );
};

export default App;