# SQL Setup Guide - Local Development + Supabase Migration

**Date**: April 27, 2026  
**Goal**: Start with local SQL, then move to Supabase easily

---

## 🎯 Quick Overview

### Strategy:
```
Step 1: Setup Local PostgreSQL
   ↓
Step 2: Create Tables
   ↓
Step 3: Connect React App
   ↓
Step 4: Build CRUD Operations
   ↓
Step 5: Migrate to Supabase (Easy swap!)
```

**Why PostgreSQL locally?**
- ✅ Same database as Supabase (easy migration)
- ✅ No vendor lock-in during development
- ✅ Full control locally
- ✅ Free
- ✅ When ready, just change connection string

---

## 📋 What You'll Build

### Local Development (This Week)
```
Your Computer:
  ├─ PostgreSQL Database (localhost:5432)
  ├─ Node.js Backend Server (localhost:3001)
  └─ React App (localhost:5173)
```

### Production (After Testing)
```
Supabase Cloud:
  ├─ PostgreSQL Database (cloud hosted)
  ├─ API (auto-generated)
  └─ React App (connects to cloud)
```

---

## 🚀 Part 1: Setup Local PostgreSQL

### Option A: Windows (Easiest) 🪟

#### 1. Download PostgreSQL Installer
- Go to: https://www.postgresql.org/download/windows/
- Download PostgreSQL 15 or 16
- Run installer

#### 2. Installation Steps
1. Click "Next" through setup
2. **Password**: Set a password (remember it! e.g., "password123")
3. **Port**: Keep as 5432 (default)
4. **Locale**: Your language is fine
5. Click "Finish"

#### 3. Verify Installation
Open PowerShell and run:
```powershell
psql --version
```

You should see: `psql (PostgreSQL) 15.x` or higher ✅

---

### Option B: Windows (Alternative) - Using Docker

If you have Docker:
```powershell
docker run --name postgres-inventory `
  -e POSTGRES_PASSWORD=password123 `
  -e POSTGRES_DB=inventory_db `
  -p 5432:5432 `
  -d postgres:16
```

---

### Option C: Mac/Linux

**Mac (Homebrew)**:
```bash
brew install postgresql@16
brew services start postgresql@16
```

**Linux (Ubuntu)**:
```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

---

## 🗄️ Part 2: Create Database & Tables

### 1. Open PostgreSQL CLI

**Windows (PowerShell)**:
```powershell
psql -U postgres
```

When asked for password, enter the one you set during installation.

### 2. Create Database

```sql
CREATE DATABASE inventory_db;
```

Switch to it:
```sql
\c inventory_db
```

### 3. Create Tables

Copy and paste this entire script:

```sql
-- Materials Gas Table
CREATE TABLE materials_gas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  existing INT NOT NULL DEFAULT 0,
  counted INT NOT NULL DEFAULT 0,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Materials Vapor Table
CREATE TABLE materials_vapor (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  existing INT NOT NULL DEFAULT 0,
  counted INT NOT NULL DEFAULT 0,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reports Table
CREATE TABLE reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type VARCHAR(50) NOT NULL, -- 'gas' or 'vapor'
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Report Differences Table
CREATE TABLE report_differences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
  material_id UUID NOT NULL,
  material_name VARCHAR(255),
  existing INT,
  counted INT,
  difference INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert Sample Data
INSERT INTO materials_gas (name, existing, counted, description) VALUES
('Oxígeno', 100, 0, 'Gas médico para respiración asistida'),
('Nitrógeno', 50, 0, 'Gas para sistemas de enfriamiento');

INSERT INTO materials_vapor (name, existing, counted, description) VALUES
('Vapor 1', 20, 0, 'Vapor utilizado en esterilización'),
('Vapor 2', 30, 0, 'Vapor para limpieza de equipo');
```

### 4. Verify Tables

```sql
\dt
```

You should see 4 tables created ✅

---

## 🔧 Part 3: Create Node.js Backend

### 1. Create Backend Directory

```powershell
cd c:\Users\arali\OneDrive\Escritorio\Primer-app-ceye-qx
mkdir backend
cd backend
npm init -y
```

### 2. Install Dependencies

```powershell
npm install express pg cors dotenv
npm install -D nodemon
```

### 3. Create `.env` File

```env
DATABASE_URL=postgresql://postgres:password123@localhost:5432/inventory_db
PORT=3001
NODE_ENV=development
```

**Replace "password123" with your actual PostgreSQL password!**

### 4. Create `src/db.js`

```javascript
const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

pool.on('error', (err) => {
  console.error('Unexpected error on idle client', err);
});

module.exports = pool;
```

### 5. Create `src/server.js`

```javascript
const express = require('express');
const cors = require('cors');
const pool = require('./db');

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// ===== MATERIALS GAS ROUTES =====

// GET all materials gas
app.get('/api/materials/gas', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM materials_gas ORDER BY created_at');
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

// POST new material gas
app.post('/api/materials/gas', async (req, res) => {
  const { name, existing, description } = req.body;
  try {
    const result = await pool.query(
      'INSERT INTO materials_gas (name, existing, description) VALUES ($1, $2, $3) RETURNING *',
      [name, existing, description]
    );
    res.status(201).json(result.rows[0]);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

// UPDATE material gas
app.put('/api/materials/gas/:id', async (req, res) => {
  const { id } = req.params;
  const { name, existing, counted, description } = req.body;
  try {
    const result = await pool.query(
      'UPDATE materials_gas SET name=$1, existing=$2, counted=$3, description=$4, updated_at=CURRENT_TIMESTAMP WHERE id=$5 RETURNING *',
      [name, existing, counted, description, id]
    );
    res.json(result.rows[0]);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

// DELETE material gas
app.delete('/api/materials/gas/:id', async (req, res) => {
  const { id } = req.params;
  try {
    await pool.query('DELETE FROM materials_gas WHERE id=$1', [id]);
    res.json({ message: 'Deleted' });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

// ===== MATERIALS VAPOR ROUTES =====

// GET all materials vapor
app.get('/api/materials/vapor', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM materials_vapor ORDER BY created_at');
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

// POST new material vapor
app.post('/api/materials/vapor', async (req, res) => {
  const { name, existing, description } = req.body;
  try {
    const result = await pool.query(
      'INSERT INTO materials_vapor (name, existing, description) VALUES ($1, $2, $3) RETURNING *',
      [name, existing, description]
    );
    res.status(201).json(result.rows[0]);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

// UPDATE material vapor
app.put('/api/materials/vapor/:id', async (req, res) => {
  const { id } = req.params;
  const { name, existing, counted, description } = req.body;
  try {
    const result = await pool.query(
      'UPDATE materials_vapor SET name=$1, existing=$2, counted=$3, description=$4, updated_at=CURRENT_TIMESTAMP WHERE id=$5 RETURNING *',
      [name, existing, counted, description, id]
    );
    res.json(result.rows[0]);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

// DELETE material vapor
app.delete('/api/materials/vapor/:id', async (req, res) => {
  const { id } = req.params;
  try {
    await pool.query('DELETE FROM materials_vapor WHERE id=$1', [id]);
    res.json({ message: 'Deleted' });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

// ===== REPORTS ROUTES =====

// GET all reports
app.get('/api/reports', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM reports ORDER BY created_at DESC');
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

// POST new report
app.post('/api/reports', async (req, res) => {
  const { type, differences } = req.body;
  try {
    const reportResult = await pool.query(
      'INSERT INTO reports (type) VALUES ($1) RETURNING *',
      [type]
    );
    const reportId = reportResult.rows[0].id;

    // Insert differences
    for (const diff of differences) {
      await pool.query(
        'INSERT INTO report_differences (report_id, material_id, material_name, existing, counted, difference) VALUES ($1, $2, $3, $4, $5, $6)',
        [reportId, diff.id, diff.name, diff.existing, diff.counted, diff.difference]
      );
    }

    res.status(201).json(reportResult.rows[0]);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'Server is running' });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
```

### 6. Update `package.json`

Add to scripts:
```json
"scripts": {
  "start": "node src/server.js",
  "dev": "nodemon src/server.js"
}
```

### 7. Start Backend

```powershell
npm run dev
```

You should see:
```
Server running on http://localhost:3001
```

✅ Backend is running!

---

## 🔌 Part 4: Connect React to Backend

### 1. Create `src/api.ts`

```typescript
const API_URL = 'http://localhost:3001/api';

// Materials Gas
export const getMaterialsGas = async () => {
  const res = await fetch(`${API_URL}/materials/gas`);
  return res.json();
};

export const addMaterialGas = async (material: { name: string; existing: number; description: string }) => {
  const res = await fetch(`${API_URL}/materials/gas`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(material),
  });
  return res.json();
};

export const updateMaterialGas = async (id: string, material: any) => {
  const res = await fetch(`${API_URL}/materials/gas/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(material),
  });
  return res.json();
};

export const deleteMaterialGas = async (id: string) => {
  const res = await fetch(`${API_URL}/materials/gas/${id}`, {
    method: 'DELETE',
  });
  return res.json();
};

// Materials Vapor
export const getMaterialsVapor = async () => {
  const res = await fetch(`${API_URL}/materials/vapor`);
  return res.json();
};

export const addMaterialVapor = async (material: { name: string; existing: number; description: string }) => {
  const res = await fetch(`${API_URL}/materials/vapor`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(material),
  });
  return res.json();
};

export const updateMaterialVapor = async (id: string, material: any) => {
  const res = await fetch(`${API_URL}/materials/vapor/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(material),
  });
  return res.json();
};

export const deleteMaterialVapor = async (id: string) => {
  const res = await fetch(`${API_URL}/materials/vapor/${id}`, {
    method: 'DELETE',
  });
  return res.json();
};

// Reports
export const getReports = async () => {
  const res = await fetch(`${API_URL}/reports`);
  return res.json();
};

export const createReport = async (report: { type: string; differences: any[] }) => {
  const res = await fetch(`${API_URL}/reports`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(report),
  });
  return res.json();
};
```

### 2. Update `App.tsx` to Use Backend

Replace your `useState` for materials with:

```typescript
const [materialsGas, setMaterialsGas] = useState<Material[]>([]);
const [materialsVapor, setMaterialsVapor] = useState<Material[]>([]);

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

// Update addMaterial function:
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
    showNotification(`✓ Material agregado correctamente.`);
  } catch (error) {
    console.error('Error adding material:', error);
    showNotification('Error adding material', 'error');
  }
};
```

---

## 🚀 Part 5: Run Everything

### Terminal 1: PostgreSQL (Already running)

### Terminal 2: Backend Server
```powershell
cd backend
npm run dev
```

Should show: `Server running on http://localhost:3001` ✅

### Terminal 3: React App
```powershell
npm run dev
```

Should show: `Local: http://localhost:5173/` ✅

---

## ✅ Test It Works

1. Open http://localhost:5173
2. Add a material in "Gestionar Stock"
3. **Check PostgreSQL**: The data should be in the database!

```powershell
psql -U postgres -d inventory_db -c "SELECT * FROM materials_gas;"
```

You should see your new material! ✅

---

## 📊 Project Structure Now

```
Primer-app-ceye-qx/
├── src/
│   ├── App.tsx         (React UI)
│   ├── api.ts          (NEW - API calls)
│   ├── main.tsx
│   └── ...
├── backend/            (NEW - Node.js server)
│   ├── src/
│   │   ├── db.js      (Database connection)
│   │   └── server.js  (Express routes)
│   ├── .env           (Database credentials)
│   ├── package.json
│   └── ...
├── docs/
├── docker-compose.yml
└── ...
```

---

## 🔄 Part 6: Migrate to Supabase (When Ready)

When you want to move to Supabase, it's just:

### 1. Create Supabase Project
- Go to https://supabase.com
- Create account
- Create new project

### 2. Get Connection String
- In Supabase: Settings → Database → Connection string
- Copy PostgreSQL connection string

### 3. Update `.env`
```env
DATABASE_URL=postgresql://user:password@db.supabasehost.com/postgres
PORT=3001
NODE_ENV=production
```

### 4. Run Migrations
Copy your SQL schema to Supabase SQL editor:
```sql
-- Copy the same CREATE TABLE scripts
```

### 5. Deploy Backend (Options)
- **Heroku** (free tier ending soon)
- **Railway** (simple, $5/month)
- **Vercel** (serverless)
- **Render** (free tier available)

### 6. Update React API_URL
```typescript
const API_URL = 'https://your-backend.herokuapp.com/api'; // Production URL
```

**That's it!** Same code, different database! ✅

---

## 💡 Benefits of This Approach

✅ **Local Development**
- Fast iteration
- No internet needed
- Full control

✅ **Easy Testing**
- Test locally first
- Database identical to production

✅ **Simple Migration**
- PostgreSQL → PostgreSQL (Supabase)
- No schema changes needed
- Same queries work

✅ **Cost Efficient**
- Free PostgreSQL locally
- Free Supabase tier
- Pay only for production scaling

---

## 🆘 Troubleshooting

### PostgreSQL won't connect
```powershell
# Check if running
pg_isready -h localhost -p 5432

# Windows: Restart service
net stop postgresql-x64-16
net start postgresql-x64-16
```

### Backend can't connect to database
```powershell
# Check .env file has correct password
cat .env

# Check database exists
psql -U postgres -l
```

### React can't connect to backend
```
Make sure backend is running on :3001
Check Network tab in DevTools
Check CORS is enabled
```

---

## 📚 Next Steps

1. ✅ Install PostgreSQL
2. ✅ Create database & tables
3. ✅ Build Node.js backend
4. ✅ Connect React to backend
5. ✅ Test everything works
6. ⏭️ Deploy backend to cloud
7. ⏭️ Migrate to Supabase database
8. ⏭️ Deploy React app

---

## 🎓 Checklist

- [ ] PostgreSQL installed
- [ ] Database created
- [ ] Tables created
- [ ] Sample data inserted
- [ ] Backend running on :3001
- [ ] React app running on :5173
- [ ] Can add material
- [ ] Data appears in PostgreSQL
- [ ] Ready for Supabase migration!

---

*Want help with specific steps?* 🚀
