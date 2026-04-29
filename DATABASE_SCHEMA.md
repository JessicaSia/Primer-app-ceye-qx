# Database Schema Reference

## Overview
SQLite database with 4 tables auto-created on first backend run.

## Table: `materials_gas`
Stores gas materials for inventory tracking.

```sql
CREATE TABLE IF NOT EXISTS materials_gas (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  existing INTEGER NOT NULL,
  counted INTEGER DEFAULT 0,
  description TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Columns:**
- `id`: Unique identifier (timestamp-based)
- `name`: Material name (e.g., "Oxígeno")
- `existing`: Current stock quantity
- `counted`: Counted quantity during inventory (defaults to 0)
- `description`: Material description
- `created_at`: When record was created
- `updated_at`: When record was last modified

**Example:**
```
id: "1704067200000"
name: "Oxígeno"
existing: 100
counted: 98
description: "Gas médico para respiración asistida"
created_at: "2024-01-01 10:00:00"
updated_at: "2024-01-01 10:00:00"
```

---

## Table: `materials_vapor`
Same structure as `materials_gas`, for vapor materials.

```sql
CREATE TABLE IF NOT EXISTS materials_vapor (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  existing INTEGER NOT NULL,
  counted INTEGER DEFAULT 0,
  description TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## Table: `reports`
Stores inventory count reports.

```sql
CREATE TABLE IF NOT EXISTS reports (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL CHECK(type IN ('gas', 'vapor')),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Columns:**
- `id`: Unique report identifier
- `type`: 'gas' or 'vapor'
- `created_at`: When report was created

**Example:**
```
id: "1704067300000"
type: "gas"
created_at: "2024-01-01 10:15:00"
```

---

## Table: `report_differences`
Details of counted vs existing for each material in a report.

```sql
CREATE TABLE IF NOT EXISTS report_differences (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  report_id TEXT NOT NULL,
  material_id TEXT NOT NULL,
  material_name TEXT NOT NULL,
  existing_count INTEGER NOT NULL,
  counted_count INTEGER NOT NULL,
  difference INTEGER NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
);
```

**Columns:**
- `id`: Auto-incrementing primary key
- `report_id`: Reference to reports table
- `material_id`: Which material this is for
- `material_name`: Cached material name
- `existing_count`: Expected quantity
- `counted_count`: Actual counted quantity
- `difference`: counted - existing
- `created_at`: When recorded
- **Foreign Key**: Deleting a report cascades delete to its differences

**Example:**
```
id: 1
report_id: "1704067300000"
material_id: "1704067200000"
material_name: "Oxígeno"
existing_count: 100
counted_count: 98
difference: -2  (2 less than expected)
created_at: "2024-01-01 10:15:00"
```

---

## Data Flow Example

### 1. Add Material
```
User clicks "Agregar Material"
→ Frontend: POST /api/materials/gas { name, existing, description }
→ Backend: INSERT INTO materials_gas VALUES (...)
→ Database: New row in materials_gas
→ Frontend: Updated UI with new material
```

### 2. Create Report
```
User counts inventory
→ Frontend: POST /api/reports { type, differences: [...] }
→ Backend: 
   - INSERT INTO reports (id, type)
   - INSERT INTO report_differences (for each material)
→ Database: 
   - New row in reports
   - N rows in report_differences
→ Frontend: New report appears in Reports view
```

### 3. Update Stock from Report
```
User clicks "Actualizar Stock"
→ Frontend: PUT /api/materials/gas/{id} { existing: counted, counted: 0 }
→ Backend: UPDATE materials_gas SET existing = counted, counted = 0
→ Database: Material's existing quantity updated
→ Frontend: Stock shows new count
```

---

## Sample Data

On first run, backend inserts:

**materials_gas:**
- Oxígeno (existing: 100)
- Nitrógeno (existing: 50)

**materials_vapor:**
- Vapor 1 (existing: 20)
- Vapor 2 (existing: 30)

---

## Key Design Decisions

✅ **SQLite**: Zero-setup local database, same SQL as PostgreSQL
✅ **Text IDs**: Using timestamp-based IDs (Date.now().toString())
✅ **Cascading Deletes**: Removing a report also removes its differences
✅ **Timestamps**: Auto-managed created_at and updated_at
✅ **No Authentication**: Simple local app (add auth later if needed)
✅ **Simple Schema**: 4 tables, easy to understand and migrate

---

## Querying Examples

If you want to check the database directly:

**All gas materials:**
```sql
SELECT * FROM materials_gas;
```

**All reports:**
```sql
SELECT * FROM reports;
```

**Details of a specific report:**
```sql
SELECT * FROM report_differences WHERE report_id = 'xxx';
```

**Materials with discrepancies:**
```sql
SELECT * FROM report_differences WHERE difference != 0;
```

**Reports by type:**
```sql
SELECT COUNT(*) FROM reports WHERE type = 'gas';
```

---

## Migration to PostgreSQL/Supabase

When ready to migrate:
1. Copy all CREATE TABLE statements above
2. Paste into Supabase SQL editor
3. Data types are 100% compatible
4. Change `TEXT` to `VARCHAR` if preferred
5. Add auth users table
6. Update API endpoint in `src/api.ts` to point to Supabase

No code changes needed! Same SQL, same React frontend.
