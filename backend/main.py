from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

from services import parser, explainer, graph
try:
    from services.runner import run_python
except Exception:
    run_python = None


app = FastAPI(title="CodeLensAI", version="0.5.0")

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Models ----------
class CodeRequest(BaseModel):
    code: str
    language: Optional[str] = "python"
    postlude: Optional[str] = None  # NEW


# ---------- Health ----------
@app.get("/")
def root():
    return {"message": "Welcome to CodeLensAI 🚀"}

# ---------- Explain ----------
@app.post("/explain")
def explain(req: CodeRequest):
    if (req.language or "python").lower() != "python":
        raise HTTPException(status_code=400, detail="Only Python is supported for now.")
    try:
        ir = parser.parse_python_to_ir(req.code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {e}")

    explanation = explainer.explain_ir(ir)
    diagram = None
    try:
        diagram = graph.ir_to_mermaid(ir)
    except Exception:
        pass

    return {"explanation": explanation, "ir": ir, "diagram": diagram}

@app.post("/mermaid")
def mermaid(req: CodeRequest):
    if (req.language or "python").lower() != "python":
        raise HTTPException(status_code=400, detail="Only Python is supported for now.")
    try:
        ir = parser.parse_python_to_ir(req.code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {e}")
    diagram = graph.ir_to_mermaid(ir)
    return {"mermaid": diagram}

# ---------- Run (NEW) ----------
@app.post("/run")
def run(req: CodeRequest):
    if (req.language or "python").lower() != "python":
        raise HTTPException(status_code=400, detail="Only Python is supported for now.")
    result = run_python(req.code, timeout_sec=3, postlude=req.postlude or "")
    return result

@app.post("/run-file")
async def run_file(file: UploadFile = File(...)):
    code = (await file.read()).decode("utf-8")
    result = run_python(code, timeout_sec=3)
    return result

# ---------- Combined ----------
@app.post("/analyze")
def analyze(req: CodeRequest, include_ir: bool = Query(False)):
    if (req.language or "python").lower() != "python":
        raise HTTPException(status_code=400, detail="Only Python is supported for now.")
    try:
        ir = parser.parse_python_to_ir(req.code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {e}")

    explanation = explainer.explain_ir(ir)
    diagram = None
    try:
        diagram = graph.ir_to_mermaid(ir)
    except Exception:
        pass

    payload = {"explanation": explanation, "diagram": diagram}
    if include_ir:
        payload["ir"] = ir
    return payload
