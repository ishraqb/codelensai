# CodeLensAI

**CodeLensAI** is an AI-powered web app that explains Python code and visualizes its logic as a flowchart.  
Built with **React**, **FastAPI**, **Tailwind CSS**, and **Mermaid.js**.

---

## ✨ Features

- Paste or upload Python code and get a natural-language explanation  
- View a generated **flowchart** representing your program’s logic  
- Run code with a customizable “Run after” snippet (e.g., `print(two_sum([2,7,11,15], 9))`)  
- Clean, responsive UI with **dark/light mode** toggle  
- Local-first design — works entirely on your machine  

---

## 🧰 Tech Stack

**Frontend:** React, Vite, Tailwind CSS, CodeMirror, Mermaid.js  
**Backend:** FastAPI (Python), AST parsing, Uvicorn  
**Language Support:** Python (for now)

---

## 🚀 Getting Started

### 1. Prerequisites

Make sure you have:

- **Python** 3.10+ (works best on 3.11+)  
- **Node.js** 18+ (LTS recommended)  
- **npm** or **yarn**

Works on macOS, Windows, and Linux.

---

### 2. Clone the repository

\`\`\`bash
git clone <your-repo-url>
cd codelensai
\`\`\`

---

### 3. Set up and run the backend (FastAPI)

\`\`\`bash
cd backend
python -m venv .venv

# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
\`\`\`

The backend runs on http://127.0.0.1:8000 by default.

---

### 4. Set up and run the frontend (Vite + React)

Open a new terminal window:

\`\`\`bash
cd frontend
npm install
npm run dev
\`\`\`

Open the URL printed in your terminal (usually http://localhost:5173).

---

### 5. Using the App

1. **Edit or upload Python code**  
   - Paste code directly or click **📂 Upload File**  
   - (Optional) Add a “Run after” line (e.g., `print(result)`)

2. **Explain**  
   - Click **✨ Explain** to generate a human-readable explanation  
   - View details in the **Explanation** or **Flowchart** tabs  

3. **Run**  
   - Click **▶ Run** to execute code and display results in the **Output** tab  

4. **Theme**  
   - Use the toggle to switch between dark and light modes  

> Only Python is supported at this time. Other languages will return a “not supported” message.

---

## 🧠 Troubleshooting

| Issue | Fix |
|------|-----|
| Blank page or Vite error | Stop and restart the frontend (`npm run dev`) |
| Backend port already in use | Run `uvicorn main:app --reload --port 8001` |
| Flowchart not appearing | Click **Explain** first; the backend must return a diagram |
| CORS errors | Start the backend **before** the frontend |
| Windows PowerShell can’t activate venv | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |

---

## 🧑‍💻 Author

Developed by **Ishraq Basher**  
Computer Science Major · Data Science & Mathematics Minor  
New York University Tandon School of Engineering
