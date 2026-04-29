# Testing Checklist

After installing dependencies and starting both servers (backend and React), test these features:

## ✅ Basic CRUD Operations

### Add Material
- [ ] Go to "Gestionar Stock de Materiales"
- [ ] Select "Gas" and enter: Name="Oxígeno", Existing=50, Description="Test"
- [ ] Click "Agregar Material"
- [ ] Verify: Green notification shows + Gas material appears in list

### Edit Material
- [ ] Click "Editar" on a material
- [ ] Change name and existing quantity
- [ ] Click "Guardar"
- [ ] Verify: Notification shows + List updates

### Delete Material
- [ ] Click "Borrar" on any material
- [ ] Verify: Material removed from list + Notification shows

## ✅ Data Persistence

### Refresh Test
- [ ] Add several materials
- [ ] Refresh the browser (F5)
- [ ] Verify: All materials still appear (data loaded from database)

### Backend Persistence
- [ ] Add a material
- [ ] Stop backend server
- [ ] Restart backend server
- [ ] Refresh React app
- [ ] Verify: Material still exists (SQLite database persisted it)

## ✅ Inventory Counting

### Create Report
- [ ] Go to "Conteo de Inventario"
- [ ] Select "Gas"
- [ ] Enter counted quantity for each material (e.g., "Oxígeno counted=48")
- [ ] Click "Generar Reporte de Diferencias"
- [ ] Verify: Report shows actual counts + differences calculated

### View Reports
- [ ] Go to "Ver Reportes de Conteo"
- [ ] Verify: Created report appears
- [ ] Can see timestamp, counts, and differences

### Update Stock from Report
- [ ] In Reports view, click "Actualizar Stock" on a report
- [ ] Verify: Green notification shows
- [ ] Go back to Stock Management
- [ ] Verify: Material's "existing" quantity updated to the counted amount

## 🔍 Network Check

### Backend Running?
Open browser console (F12):
- Open Network tab
- Click any button in the app
- Verify: GET/POST requests to `localhost:3001/api`
- All responses should be HTTP 200 or 201

### Database Created?
- [ ] Go to `backend/inventory.db` folder
- [ ] File `inventory.db` should exist (SQLite database file)
- This file contains all your data

## 📊 Success Criteria

You'll know it's working when:
1. ✅ Can add/edit/delete materials
2. ✅ Materials persist after page refresh
3. ✅ Can create reports with counted quantities
4. ✅ Stock can be updated from reports
5. ✅ Network tab shows requests to localhost:3001
6. ✅ inventory.db file exists in backend folder
