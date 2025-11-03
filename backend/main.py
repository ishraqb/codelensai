from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

from services import parser, explainer, graph
from services import parser_js
try:
    from services.runner import run_python
except Exception:
    run_python = None
try:
    from services.runner_js import run_javascript, run_typescript
except Exception:
    run_javascript = None
    run_typescript = None


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
    lang = (req.language or "python").lower()
    try:
        if lang == "python":
            ir = parser.parse_python_to_ir(req.code)
        elif lang in ("javascript", "typescript"):
            ir = parser_js.parse_jsts_to_ir(req.code)
        else:
            raise HTTPException(status_code=400, detail=f"Language not supported: {lang}")
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
    lang = (req.language or "python").lower()
    try:
        if lang == "python":
            ir = parser.parse_python_to_ir(req.code)
        elif lang in ("javascript", "typescript"):
            ir = parser_js.parse_jsts_to_ir(req.code)
        else:
            raise HTTPException(status_code=400, detail=f"Language not supported: {lang}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {e}")
    diagram = graph.ir_to_mermaid(ir)
    return {"mermaid": diagram}

# ---------- Run (NEW) ----------
@app.post("/run")
def run(req: CodeRequest):
    lang = (req.language or "python").lower()
    if lang == "python":
        if run_python is None:
            raise HTTPException(status_code=503, detail="Python runner unavailable on server.")
        result = run_python(req.code, timeout_sec=3, postlude=req.postlude or "")
    elif lang == "javascript":
        if run_javascript is None:
            raise HTTPException(status_code=503, detail="Node runner unavailable on server.")
        result = run_javascript(req.code, timeout_sec=3, postlude=req.postlude or "")
    elif lang == "typescript":
        if run_typescript is None:
            raise HTTPException(status_code=503, detail="TS runner unavailable on server.")
        result = run_typescript(req.code, timeout_sec=3, postlude=req.postlude or "")
    else:
        raise HTTPException(status_code=400, detail=f"Language not supported: {lang}")
    return result

@app.post("/run-file")
async def run_file(file: UploadFile = File(...)):
    code = (await file.read()).decode("utf-8")
    # Default to python behavior for run-file
    if run_python is None:
        raise HTTPException(status_code=503, detail="Python runner unavailable on server.")
    return run_python(code, timeout_sec=3)

# ---------- Combined ----------
@app.post("/analyze")
def analyze(req: CodeRequest, include_ir: bool = Query(False)):
    lang = (req.language or "python").lower()
    try:
        if lang == "python":
            ir = parser.parse_python_to_ir(req.code)
        elif lang in ("javascript", "typescript"):
            ir = parser_js.parse_jsts_to_ir(req.code)
        else:
            raise HTTPException(status_code=400, detail=f"Language not supported: {lang}")
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
