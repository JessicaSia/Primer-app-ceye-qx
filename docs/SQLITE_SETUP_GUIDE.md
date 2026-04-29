# SQLite Setup Guide - Easy Local Testing + Supabase Migration

**Date**: April 27, 2026  
**Goal**: Quick SQLite setup for testing, then easy move to Supabase

---

## 🎯 Why SQLite is Perfect for You

```
✅ No PostgreSQL installation needed
✅ Just a file in your project
✅ Works immediately
✅ Perfect for testing
✅ Easy to migrate to Supabase later
✅ Zero server setup
✅ Super lightweight
```

---

## 🚀 Quick Overview

### Timeline:
```
TODAY: SQLite Setup (30 minutes)
  ↓
TESTING: Build features locally (1-2 weeks)
  ↓
READY: Migrate to Supabase (1 hour)
```

---

## 📋 Part 1: Setup SQLite Backend

### 1. Create Backend Directory

```powershell
cd c:\Users\arali\OneDrive\Escritorio\Primer-app-ceye-qx
mkdir backend
cd backend
npm init -y
```

### 2. Install Dependencies

```powershell
npm install express sqlite3 cors dotenv body-parser
npm install -D nodemon
```

### 3. Create Database File

SQLite will create the database automatically, but let's set it up properly:

Create `src/database.js`:

```javascript
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// Database file location
const dbPath = path.join(__dirname, '../inventory.db');

// Create or open database
const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('Error opening database:', err);
  } else {
    console.log('Connected to SQLite database at:', dbPath);
    initializeDatabase();
  }
});

// Initialize tables
function initializeDatabase() {
  db.serialize(() => {
    // Materials Gas Table
    db.run(`
      CREATE TABLE IF NOT EXISTS materials_gas (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        existing INTEGER DEFAULT 0,
        counted INTEGER DEFAULT 0,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `, (err) => {
      if (err) console.error('Error creating materials_gas:', err);
      else console.log('✓ materials_gas table ready');
    });

    // Materials Vapor Table
    db.run(`
      CREATE TABLE IF NOT EXISTS materials_vapor (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        existing INTEGER DEFAULT 0,
        counted INTEGER DEFAULT 0,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `, (err) => {
      if (err) console.error('Error creating materials_vapor:', err);
      else console.log('✓ materials_vapor table ready');
    });

    // Reports Table
    db.run(`
      CREATE TABLE IF NOT EXISTS reports (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `, (err) => {
      if (err) console.error('Error creating reports:', err);
      else console.log('✓ reports table ready');
    });

    // Report Differences Table
    db.run(`
      CREATE TABLE IF NOT EXISTS report_differences (
        id TEXT PRIMARY KEY,
        report_id TEXT NOT NULL,
        material_id TEXT NOT NULL,
        material_name TEXT,
        existing INTEGER,
        counted INTEGER,
        difference INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
      )
    `, (err) => {
      if (err) console.error('Error creating report_differences:', err);
      else console.log('✓ report_differences table ready');
    });

    // Insert sample data
    insertSampleData();
  });
}

function insertSampleData() {
  // Check if data already exists
  db.get('SELECT COUNT(*) as count FROM materials_gas', (err, row) => {
    if (err) {
      console.error('Error checking data:', err);
      return;
    }

    if (row.count === 0) {
      // Insert sample materials
      db.run(
        `INSERT INTO materials_gas (id, name, existing, description) 
         VALUES (?, ?, ?, ?)`,
        ['gas-1', 'Oxígeno', 100, 'Gas médico para respiración asistida'],
        (err) => {
          if (err) console.error('Error inserting sample data:', err);
          else console.log('✓ Sample data inserted');
        }
      );

      db.run(
        `INSERT INTO materials_gas (id, name, existing, description) 
         VALUES (?, ?, ?, ?)`,
        ['gas-2', 'Nitrógeno', 50, 'Gas para sistemas de enfriamiento']
      );

      db.run(
        `INSERT INTO materials_vapor (id, name, existing, description) 
         VALUES (?, ?, ?, ?)`,
        ['vapor-1', 'Vapor 1', 20, 'Vapor utilizado en esterilización']
      );

      db.run(
        `INSERT INTO materials_vapor (id, name, existing, description) 
         VALUES (?, ?, ?, ?)`,
        ['vapor-2', 'Vapor 2', 30, 'Vapor para limpieza de equipo']
      );
    }
  });
}

module.exports = db;
```

### 4. Create Main Server File

Create `src/server.js`:

```javascript
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
require('dotenv').config();
const db = require('./database');

const app = express();

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// ===== MATERIALS GAS ROUTES =====

// GET all materials gas
app.get('/api/materials/gas', (req, res) => {
  db.all('SELECT * FROM materials_gas ORDER BY created_at', [], (err, rows) => {
    if (err) {
      console.error(err);
      res.status(500).json({ error: 'Server error' });
    } else {
      res.json(rows || []);
    }
  });
});

// POST new material gas
app.post('/api/materials/gas', (req, res) => {
  const { id, name, existing, description } = req.body;
  const newId = id || Date.now().toString();

  db.run(
    `INSERT INTO materials_gas (id, name, existing, description) 
     VALUES (?, ?, ?, ?)`,
    [newId, name, existing || 0, description || ''],
    function(err) {
      if (err) {
        console.error(err);
        res.status(500).json({ error: 'Server error' });
      } else {
        res.status(201).json({
          id: newId,
          name,
          existing: existing || 0,
          counted: 0,
          description: description || '',
          created_at: new Date().toISOString()
        });
      }
    }
  );
});

// PUT update material gas
app.put('/api/materials/gas/:id', (req, res) => {
  const { id } = req.params;
  const { name, existing, counted, description } = req.body;

  db.run(
    `UPDATE materials_gas 
     SET name = ?, existing = ?, counted = ?, description = ?, updated_at = CURRENT_TIMESTAMP
     WHERE id = ?`,
    [name, existing, counted, description, id],
    function(err) {
      if (err) {
        console.error(err);
        res.status(500).json({ error: 'Server error' });
      } else {
        res.json({
          id,
          name,
          existing,
          counted,
          description,
          updated_at: new Date().toISOString()
        });
      }
    }
  );
});

// DELETE material gas
app.delete('/api/materials/gas/:id', (req, res) => {
  const { id } = req.params;

  db.run(`DELETE FROM materials_gas WHERE id = ?`, [id], function(err) {
    if (err) {
      console.error(err);
      res.status(500).json({ error: 'Server error' });
    } else {
      res.json({ message: 'Deleted', id });
    }
  });
});

// ===== MATERIALS VAPOR ROUTES =====

// GET all materials vapor
app.get('/api/materials/vapor', (req, res) => {
  db.all('SELECT * FROM materials_vapor ORDER BY created_at', [], (err, rows) => {
    if (err) {
      console.error(err);
      res.status(500).json({ error: 'Server error' });
    } else {
      res.json(rows || []);
    }
  });
});

// POST new material vapor
app.post('/api/materials/vapor', (req, res) => {
  const { id, name, existing, description } = req.body;
  const newId = id || Date.now().toString();

  db.run(
    `INSERT INTO materials_vapor (id, name, existing, description) 
     VALUES (?, ?, ?, ?)`,
    [newId, name, existing || 0, description || ''],
    function(err) {
      if (err) {
        console.error(err);
        res.status(500).json({ error: 'Server error' });
      } else {
        res.status(201).json({
          id: newId,
          name,
          existing: existing || 0,
          counted: 0,
          description: description || '',
          created_at: new Date().toISOString()
        });
      }
    }
  );
});

// PUT update material vapor
app.put('/api/materials/vapor/:id', (req, res) => {
  const { id } = req.params;
  const { name, existing, counted, description } = req.body;

  db.run(
    `UPDATE materials_vapor 
     SET name = ?, existing = ?, counted = ?, description = ?, updated_at = CURRENT_TIMESTAMP
     WHERE id = ?`,
    [name, existing, counted, description, id],
    function(err) {
      if (err) {
        console.error(err);
        res.status(500).json({ error: 'Server error' });
      } else {
        res.json({
          id,
          name,
          existing,
          counted,
          description,
          updated_at: new Date().toISOString()
        });
      }
    }
  );
});

// DELETE material vapor
app.delete('/api/materials/vapor/:id', (req, res) => {
  const { id } = req.params;

  db.run(`DELETE FROM materials_vapor WHERE id = ?`, [id], function(err) {
    if (err) {
      console.error(err);
      res.status(500).json({ error: 'Server error' });
    } else {
      res.json({ message: 'Deleted', id });
    }
  });
});

// ===== REPORTS ROUTES =====

// GET all reports
app.get('/api/reports', (req, res) => {
  db.all('SELECT * FROM reports ORDER BY created_at DESC', [], (err, rows) => {
    if (err) {
      console.error(err);
      res.status(500).json({ error: 'Server error' });
    } else {
      res.json(rows || []);
    }
  });
});

// POST new report
app.post('/api/reports', (req, res) => {
  const { id, type, differences } = req.body;
  const newId = id || Date.now().toString();

  db.run(
    `INSERT INTO reports (id, type) VALUES (?, ?)`,
    [newId, type],
    function(err) {
      if (err) {
        console.error(err);
        res.status(500).json({ error: 'Server error' });
        return;
      }

      // Insert differences
      let inserted = 0;
      differences.forEach((diff) => {
        const diffId = Date.now().toString() + Math.random();
        db.run(
          `INSERT INTO report_differences 
           (id, report_id, material_id, material_name, existing, counted, difference)
           VALUES (?, ?, ?, ?, ?, ?, ?)`,
          [diffId, newId, diff.id, diff.name, diff.existing, diff.counted, diff.difference],
          (err) => {
            if (err) console.error(err);
            inserted++;
            if (inserted === differences.length) {
              res.status(201).json({
                id: newId,
                type,
                timestamp: new Date().toISOString(),
                differences
              });
            }
          }
        );
      });
    }
  );
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'Server is running', database: 'SQLite' });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`🚀 Server running on http://localhost:${PORT}`);
  console.log(`📊 Using SQLite database`);
});
```

### 5. Create `.env` File

Create `backend/.env`:

```env
PORT=3001
NODE_ENV=development
```

*Note: For SQLite, you don't need DATABASE_URL since it uses a local file!*

### 6. Update `package.json`

Add to `scripts`:
```json
"scripts": {
  "start": "node src/server.js",
  "dev": "nodemon src/server.js"
}
```

### 7. Create `.gitignore` in Backend

Create `backend/.gitignore`:
```
node_modules/
inventory.db
.env
.env.local
```

### 8. Start Backend

```powershell
cd backend
npm run dev
```

You should see:
```
🚀 Server running on http://localhost:3001
📊 Using SQLite database
✓ materials_gas table ready
✓ materials_vapor table ready
✓ reports table ready
✓ report_differences table ready
✓ Sample data inserted
```

✅ Backend with SQLite is running!

---

## 🔌 Part 2: Connect React to Backend

### 1. Create `src/api.ts`

```typescript
const API_URL = 'http://localhost:3001/api';

// Materials Gas
export const getMaterialsGas = async () => {
  const res = await fetch(`${API_URL}/materials/gas`);
  if (!res.ok) throw new Error('Failed to fetch materials');
  return res.json();
};

export const addMaterialGas = async (material: {
  name: string;
  existing: number;
  description: string;
}) => {
  const res = await fetch(`${API_URL}/materials/gas`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      id: Date.now().toString(),
      ...material,
    }),
  });
  if (!res.ok) throw new Error('Failed to add material');
  return res.json();
};

export const updateMaterialGas = async (
  id: string,
  material: {
    name: string;
    existing: number;
    counted: number;
    description: string;
  }
) => {
  const res = await fetch(`${API_URL}/materials/gas/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(material),
  });
  if (!res.ok) throw new Error('Failed to update material');
  return res.json();
};

export const deleteMaterialGas = async (id: string) => {
  const res = await fetch(`${API_URL}/materials/gas/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete material');
  return res.json();
};

// Materials Vapor (same pattern)
export const getMaterialsVapor = async () => {
  const res = await fetch(`${API_URL}/materials/vapor`);
  if (!res.ok) throw new Error('Failed to fetch materials');
  return res.json();
};

export const addMaterialVapor = async (material: {
  name: string;
  existing: number;
  description: string;
}) => {
  const res = await fetch(`${API_URL}/materials/vapor`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      id: Date.now().toString(),
      ...material,
    }),
  });
  if (!res.ok) throw new Error('Failed to add material');
  return res.json();
};

export const updateMaterialVapor = async (
  id: string,
  material: {
    name: string;
    existing: number;
    counted: number;
    description: string;
  }
) => {
  const res = await fetch(`${API_URL}/materials/vapor/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(material),
  });
  if (!res.ok) throw new Error('Failed to update material');
  return res.json();
};

export const deleteMaterialVapor = async (id: string) => {
  const res = await fetch(`${API_URL}/materials/vapor/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete material');
  return res.json();
};

// Reports
export const getReports = async () => {
  const res = await fetch(`${API_URL}/reports`);
  if (!res.ok) throw new Error('Failed to fetch reports');
  return res.json();
};

export const createReport = async (report: {
  type: string;
  differences: any[];
}) => {
  const res = await fetch(`${API_URL}/reports`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      id: Date.now().toString(),
      ...report,
    }),
  });
  if (!res.ok) throw new Error('Failed to create report');
  return res.json();
};
```

### 2. Update `src/App.tsx`

Replace your localStorage code with database calls. Add this useEffect:

```typescript
import {
  getMaterialsGas,
  getMaterialsVapor,
  addMaterialGas,
  updateMaterialGas,
  deleteMaterialGas,
  addMaterialVapor,
  updateMaterialVapor,
  deleteMaterialVapor,
  getReports,
  createReport,
} from './api';

// Load materials on mount
useEffect(() => {
  loadMaterials();
}, []);

const loadMaterials = async () => {
  try {
    const [gasData, vaporData] = await Promise.all([
      getMaterialsGas(),
      getMaterialsVapor(),
    ]);
    setMaterialsGas(gasData);
    setMaterialsVapor(vaporData);
  } catch (error) {
    console.error('Error loading materials:', error);
    showNotification('Error loading materials', 'error');
  }
};

// Update addMaterial function
const addMaterial = async (type: 'gas' | 'vapor') => {
  if (!newMaterialName.trim()) return;

  try {
    const newMaterial = {
      name: newMaterialName,
      existing: newMaterialExisting,
      description: newMaterialDescription,
    };

    if (type === 'gas') {
      const result = await addMaterialGas(newMaterial);
      setMaterialsGas([...materialsGas, result]);
    } else {
      const result = await addMaterialVapor(newMaterial);
      setMaterialsVapor([...materialsVapor, result]);
    }

    setNewMaterialName('');
    setNewMaterialExisting(0);
    setNewMaterialDescription('');
    showNotification('✓ Material agregado correctamente.');
  } catch (error) {
    console.error('Error:', error);
    showNotification('Error agregando material', 'error');
  }
};

// Update deleteMaterial function
const deleteMaterial = async (id: string, type: 'gas' | 'vapor') => {
  try {
    if (type === 'gas') {
      await deleteMaterialGas(id);
      setMaterialsGas(materialsGas.filter(m => m.id !== id));
    } else {
      await deleteMaterialVapor(id);
      setMaterialsVapor(materialsVapor.filter(m => m.id !== id));
    }
    showNotification('✓ Material eliminado correctamente.');
  } catch (error) {
    console.error('Error:', error);
    showNotification('Error eliminando material', 'error');
  }
};

// And similar updates for saveEdit, saveReport, etc.
```

---

## ✅ Part 3: Run Everything

### Terminal 1: Backend
```powershell
cd backend
npm run dev
```

Should show:
```
🚀 Server running on http://localhost:3001
```

### Terminal 2: React
```powershell
npm run dev
```

Should show:
```
Local: http://localhost:5173/
```

✅ Both running!

---

## 🧪 Testing

1. Open http://localhost:5173
2. Add a new material
3. **SQLite file created!** Check `backend/inventory.db` exists ✅
4. Refresh page - data is still there! ✅
5. Add report - data saved! ✅

---

## 📊 File Structure

```
Primer-app-ceye-qx/
├── src/
│   ├── App.tsx
│   ├── api.ts          (NEW - API calls)
│   ├── main.tsx
│   └── ...
├── backend/            (NEW)
│   ├── src/
│   │   ├── database.js (Creates SQLite)
│   │   └── server.js   (Express server)
│   ├── inventory.db    (SQLite file - created automatically)
│   ├── .env
│   ├── .gitignore
│   ├── package.json
│   └── ...
├── docs/
└── ...
```

---

## 🔄 Part 4: Migrate to Supabase (When Ready)

When you're ready to move to Supabase, it's super easy:

### Option 1: Keep Same Backend (Just Change Connection)

```javascript
// Change database.js to use Supabase
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_KEY
);

// Then change the routes to use Supabase
```

### Option 2: Use Supabase Directly

Stop using your backend entirely and use Supabase REST API:

```typescript
// Remove backend, use Supabase directly
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(url, key);

// Then use Supabase in api.ts
export const getMaterialsGas = async () => {
  const { data, error } = await supabase
    .from('materials_gas')
    .select('*');
  return data;
};
```

### Migration Steps:
1. Copy your SQLite schema to Supabase
2. Export SQLite data to CSV
3. Import into Supabase
4. Update `api.ts` to call Supabase instead of backend
5. Done! ✅

---

## 💡 Benefits of SQLite

✅ **Zero Setup**
- No server installation
- Just a file
- Works immediately

✅ **Perfect for Development**
- Fast iteration
- Local testing
- Full control

✅ **Easy Migration**
- Same SQL works in Supabase
- Easy export/import
- No architecture change needed

✅ **Learning Friendly**
- See SQL working locally
- Understand your data
- Debug easily

---

## 🆘 Troubleshooting

### Backend won't start
```powershell
# Check Node.js installed
node --version

# Check packages installed
npm list

# Try again
npm run dev
```

### Can't connect to backend
```
Check backend is running on :3001
Check CORS is enabled (it is!)
Check React is on :5173
```

### Database corrupted
```powershell
# Just delete the file and start over
Remove-Item backend/inventory.db

# Backend will recreate it with sample data
```

---

## 📚 Next Steps

1. ✅ Create backend directory
2. ✅ Install Node.js packages
3. ✅ Create database.js
4. ✅ Create server.js
5. ✅ Create api.ts
6. ✅ Update App.tsx
7. ✅ Run backend and React
8. ✅ Test everything works
9. ⏭️ When ready: Migrate to Supabase (1 hour)

---

## 🎓 Key Points

| Aspect | SQLite | Later: Supabase |
|--------|--------|-----------------|
| **Setup** | 30 min | 1 hour |
| **Database File** | `inventory.db` | Cloud hosted |
| **Code Change** | No changes needed | Update `api.ts` |
| **Teams** | Single user | Multi-user |
| **Backup** | Copy `inventory.db` | Automatic |

---

*Ready to start? Go build!* 🚀
