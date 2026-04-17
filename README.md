# Smart Placement Intelligence System

## Tech Stack
| Layer     | Technology       | Subject |
|-----------|-----------------|---------|
| Frontend  | HTML, CSS, JS, Chart.js | WT |
| Backend   | Python Flask, REST API | WT + AI |
| ML Model  | Random Forest (scikit-learn) | AI + DSBDA |
| Database  | MySQL           | DSBDA |
| Auth      | Sessions + bcrypt hash | WT |

---

## Setup Steps

### Step 1 — Install Python packages
```bash
pip install -r requirements.txt
```

### Step 2 — Setup MySQL Database
Open MySQL Workbench or terminal and run:
```bash
mysql -u root -p < setup.sql
```

### Step 3 — Configure DB password
Open `db.py` and change `password="yourpassword"` to your actual MySQL password.

### Step 4 — Train the ML model
```bash
python model.py
```
This creates `placement_model.pkl` and (if missing) generates `dataset.csv`.

### Step 5 — Run the app
```bash
python app.py
```

### Step 6 — Open browser
Go to: http://localhost:5000

---

## File Structure
```
placement_advanced/
├── app.py           ← Flask app (all routes + API)
├── model.py         ← Train ML model (run once)
├── db.py            ← Database connection
├── setup.sql        ← Create MySQL tables (run once)
├── requirements.txt ← Python packages
├── placement_model.pkl  ← Saved ML model (after running model.py)
├── dataset.csv          ← Training data
├── templates/
│   ├── login.html
│   ├── register.html
│   └── dashboard.html
└── static/
    ├── style.css
    └── script.js
```

---

## API Endpoints
| Method | URL        | Purpose |
|--------|-----------|---------|
| GET    | /login    | Show login form |
| POST   | /login    | Authenticate user |
| GET    | /register | Show register form |
| POST   | /register | Create account |
| GET    | /dashboard| Main dashboard |
| POST   | /predict  | ML prediction (JSON) |
| GET    | /api/stats| Aggregate stats (JSON) |
| GET    | /logout   | Clear session |

---

## Viva Points
- **Why Random Forest?** → Ensemble of 100 trees, majority vote, higher accuracy than single tree
- **Why hashed passwords?** → Plain text storage is a security risk; bcrypt hash is irreversible
- **What is REST API?** → Stateless HTTP interface; /predict accepts POST, returns JSON
- **How does AJAX work?** → fetch() sends request without page reload; parses JSON response
- **What data is stored?** → Each prediction saved with user_id, inputs, result, suggestion, timestamp
