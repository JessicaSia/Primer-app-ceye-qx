# Data Persistence Guide - localStorage vs Cookies

**Date**: April 27, 2026  
**Status**: How to keep data without losing it on page refresh

---

## 🎯 Quick Answer

Your app is **ALREADY using localStorage** which is the best method for your needs! ✅

No data is lost on refresh because:
1. Data is saved to browser storage
2. When page reloads, it reads from storage
3. Even if browser closes, data persists (unlike cookies with expiry)

---

## 📊 Comparison: localStorage vs Cookies vs Other Methods

| Feature | localStorage | Cookies | sessionStorage | Database |
|---------|--------------|---------|----------------|----------|
| **Capacity** | 5-10 MB | 4 KB | 5-10 MB | Unlimited |
| **Persistence** | Until manually deleted | Until expiry | Until tab closes | Permanent |
| **Sent with requests** | No | Yes (slows requests) | No | N/A |
| **Easy to use** | ✅ Yes | ❌ Complex | ✅ Yes | ⚠️ Requires server |
| **Client-side only** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ Needs server |
| **Your use case** | ✅✅✅ PERFECT | ⚠️ Slower | ❌ Loses on close | 🎯 Future upgrade |

---

## 🔍 Current Implementation in Your App

### How Your App Saves Data

```typescript
// SAVING DATA - When something changes
useEffect(() => {
  localStorage.setItem('reports', JSON.stringify(reports));
}, [reports]); // Runs whenever 'reports' changes

useEffect(() => {
  localStorage.setItem('materialsGas', JSON.stringify(materialsGas));
}, [materialsGas]); // Runs whenever 'materialsGas' changes

useEffect(() => {
  localStorage.setItem('materialsVapor', JSON.stringify(materialsVapor));
}, [materialsVapor]); // Runs whenever 'materialsVapor' changes
```

### How Your App Loads Data

```typescript
// LOADING DATA - On first app load
const loadMaterials = (key: string, fallback: Material[]) => {
  const saved = localStorage.getItem(key); // Get from storage
  if (!saved) return fallback; // If empty, use default values
  try {
    return JSON.parse(saved); // Convert JSON string to object
  } catch {
    return fallback; // If error, use default values
  }
};

// Usage on component mount:
const [materialsGas, setMaterialsGas] = useState<Material[]>(() => 
  loadMaterials('materialsGas', defaultGas)
);

const [reports, setReports] = useState<Report[]>(() => {
  const saved = localStorage.getItem('reports');
  if (!saved) return [];
  try {
    return JSON.parse(saved);
  } catch {
    return [];
  }
});
```

---

## 📝 Data Flow Diagram

```
User Action (Add/Edit/Delete Material)
    ↓
React State Updates (setMaterialsGas, etc.)
    ↓
useEffect Detects Change
    ↓
localStorage.setItem() Saves to Browser
    ↓
Data Saved! ✅

---

Page Refresh or Browser Close/Open
    ↓
App Component Mounts
    ↓
useState initializer function runs
    ↓
loadMaterials() or similar function called
    ↓
localStorage.getItem() Retrieves Data
    ↓
Data Restored! ✅
```

---

## 🛠️ How to Verify localStorage is Working

### 1. Open Browser DevTools
- Press `F12` or Right-click → Inspect
- Go to `Application` or `Storage` tab

### 2. Find localStorage
- Click `Local Storage` (or `Local Storage` → `http://localhost:5173`)

### 3. You'll see your data like this:

```
Key                  | Value
---------------------|-------
materialsGas         | [{"id":"1","name":"Oxígeno",...}]
materialsVapor       | [{"id":"1","name":"Vapor 1",...}]
reports              | [{"id":"1234567890","type":"gas",...}]
updatedReports       | ["1234567890"]
```

### 4. Test it works:
1. Open DevTools (F12)
2. Add a new material in your app
3. Check localStorage - new data appears
4. Refresh page (F5) - data still there! ✅
5. Close browser and reopen - data still there! ✅

---

## 💾 Complete Storage System Explained

Your app uses **3 types of storage**:

### 1. **Materials Gas & Vapor** (Primary Data)
```typescript
localStorage.setItem('materialsGas', JSON.stringify(materialsGas));
localStorage.setItem('materialsVapor', JSON.stringify(materialsVapor));
```
- Stores the inventory items
- Updates automatically via useEffect
- Restored on app start

### 2. **Reports** (Historical Data)
```typescript
localStorage.setItem('reports', JSON.stringify(reports));
```
- Stores all inventory count reports
- Includes timestamp and differences
- Persists across sessions

### 3. **Updated Reports** (UI State - NOT PERSISTED)
```typescript
const [updatedReports, setUpdatedReports] = useState<string[]>([]);
```
- ⚠️ This one is **NOT** saved to localStorage
- Resets when page refreshes
- Used only for showing summary UI

---

## ⚠️ Important: Updated Reports Not Persisting

**Issue**: When you refresh, the "Actualización de Stock Completada" summary disappears

**Reason**: `updatedReports` state is not saved to localStorage

**Solution**: Add persistence for `updatedReports`:

```typescript
// Load on app start
const [updatedReports, setUpdatedReports] = useState<string[]>(() => {
  const saved = localStorage.getItem('updatedReports');
  if (!saved) return [];
  try {
    return JSON.parse(saved);
  } catch {
    return [];
  }
});

// Save whenever it changes
useEffect(() => {
  localStorage.setItem('updatedReports', JSON.stringify(updatedReports));
}, [updatedReports]);
```

---

## 🎯 localStorage Methods You Can Use

### Save Data
```typescript
localStorage.setItem('key', 'value');
localStorage.setItem('myData', JSON.stringify({name: 'John', age: 30}));
```

### Retrieve Data
```typescript
const value = localStorage.getItem('key');
const data = JSON.parse(localStorage.getItem('myData'));
```

### Delete Specific Item
```typescript
localStorage.removeItem('myData');
```

### Delete Everything
```typescript
localStorage.clear();
```

### Get All Keys
```typescript
const keys = Object.keys(localStorage);
for (let key of keys) {
  console.log(key, localStorage.getItem(key));
}
```

---

## 📱 What Each Storage Type is Best For

### ✅ localStorage - Use When:
- Data needs to persist long-term
- No server/database available
- You need 5-10 MB storage (your case!)
- User wants offline access
- Shopping cart, preferences, drafts

### ✅ sessionStorage - Use When:
- Data only needed during session
- Tab-specific data
- Temporary UI state
- Sensitive data (auto-deletes on close)

### ✅ Cookies - Use When:
- Need to send data to server
- Need expiration time
- Need cross-domain access
- Login tokens, tracking

### ✅ IndexedDB - Use When:
- Need massive storage (> 50 MB)
- Complex queries needed
- Real-time sync with server
- Advanced database features

---

## 🔐 Security Notes for localStorage

### ⚠️ localStorage is NOT Secure for:
- Passwords
- API tokens
- Credit card info
- Sensitive secrets

**Why?** Anyone can read it via DevTools or JavaScript

### ✅ localStorage IS Safe for:
- User preferences
- UI state
- Inventory data (your use case!)
- Non-sensitive user data
- Caches of public data

### 🛡️ For Sensitive Data, Use:
- HTTP-only cookies (server can't access via JS)
- SessionStorage with expiry
- Encrypted values
- Server-side sessions

---

## 📋 Your App's Current Data Structure

### Gas Materials
```json
{
  "id": "1",
  "name": "Oxígeno",
  "existing": 100,
  "counted": 0,
  "description": "Gas médico para respiración asistida"
}
```

### Vapor Materials
```json
{
  "id": "1",
  "name": "Vapor 1",
  "existing": 20,
  "counted": 0,
  "description": "Vapor utilizado en esterilización"
}
```

### Reports
```json
{
  "id": "1234567890",
  "type": "gas",
  "timestamp": "27/4/2026, 10:30:45",
  "differences": [
    {
      "id": "1",
      "name": "Oxígeno",
      "existing": 100,
      "counted": 95,
      "description": "...",
      "difference": -5
    }
  ]
}
```

All stored as JSON strings in localStorage automatically! ✅

---

## 🚀 Advanced: Auto-Save on Every Change

Your app already does this via useEffect! Here's how:

```typescript
// Pattern 1: Dependency array triggers save
useEffect(() => {
  localStorage.setItem('materialsGas', JSON.stringify(materialsGas));
}, [materialsGas]); // Runs whenever materialsGas changes

// This means:
// ✅ Add material → auto-saved
// ✅ Edit material → auto-saved
// ✅ Delete material → auto-saved
// ✅ Update counts → auto-saved
```

---

## ❌ Common Mistakes to Avoid

1. **❌ Don't save non-serializable data**
   ```typescript
   // WRONG: Functions can't be saved
   localStorage.setItem('func', myFunction);
   
   // RIGHT: Save only data
   localStorage.setItem('data', JSON.stringify({name: 'value'}));
   ```

2. **❌ Don't store huge objects**
   ```typescript
   // WRONG: Images, videos, etc.
   localStorage.setItem('largeFile', fileContent);
   
   // RIGHT: Use File API or IndexedDB
   ```

3. **❌ Don't forget JSON.stringify**
   ```typescript
   // WRONG
   localStorage.setItem('data', {name: 'John'});
   
   // RIGHT
   localStorage.setItem('data', JSON.stringify({name: 'John'}));
   ```

4. **❌ Don't forget JSON.parse**
   ```typescript
   // WRONG
   const data = localStorage.getItem('data'); // Returns string
   console.log(data.name); // undefined!
   
   // RIGHT
   const data = JSON.parse(localStorage.getItem('data'));
   console.log(data.name); // 'John'
   ```

---

## ✅ Checklist for Your App

- [x] Data saved automatically on change
- [x] Data loaded on app start
- [x] Reports persist across sessions
- [x] Material inventory persists
- [x] Error handling for corrupted data
- [ ] Updated reports UI state persisting (OPTIONAL - can be added)
- [ ] Clear data button for users (OPTIONAL)
- [ ] Data export feature (OPTIONAL)

---

## 📊 Your Storage Current Sizes

Check your storage usage:

```typescript
// Add this to your app to see sizes
function getStorageSize() {
  let totalSize = 0;
  for (let key in localStorage) {
    if (localStorage.hasOwnProperty(key)) {
      const itemSize = localStorage[key].length + key.length;
      console.log(`${key}: ${(itemSize / 1024).toFixed(2)} KB`);
      totalSize += itemSize;
    }
  }
  console.log(`Total: ${(totalSize / 1024).toFixed(2)} KB / 5000 KB max`);
}
```

Your app will never exceed limits with inventory data! ✅

---

## 🎓 Conclusion

**Your app is perfectly set up!** ✨

- ✅ Uses localStorage (5-10 MB capacity - plenty!)
- ✅ Auto-saves on every change
- ✅ Auto-loads on app start
- ✅ Handles errors gracefully
- ✅ No data loss on refresh
- ✅ No data loss on browser close/open
- ✅ No server needed
- ✅ Works offline

**Like cookies but better!** 🍪➡️💾

---

*Questions? See the localStorage MDN docs:*
https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage
