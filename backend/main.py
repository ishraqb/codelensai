from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from backend.services import parser, explainer, graph

app = FastAPI(title="CodeLensAI", version="0.2.0")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- Models --------
class CodeRequest(BaseModel):
    code: str

# -------- Health --------
@app.get("/")
def root():
    return {"message": "Welcome to CodeLensAI 🚀"}

# -------- JSON endpoints --------
@app.post("/explain")
def explain(req: CodeRequest):
    try:
        ir = parser.parse_python_to_ir(req.code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {e}")
    rows = explainer.explain_ir(ir)  # list[{line, indent, text}]
    return {"explanation": rows, "ir": ir}

@app.post("/mermaid")
def mermaid(req: CodeRequest):
    try:
        ir = parser.parse_python_to_ir(req.code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {e}")
    diagram = graph.ir_to_mermaid(ir)
    return {"mermaid": diagram}

# -------- File upload endpoints --------
@app.post("/explain-file")
async def explain_file(file: UploadFile = File(...)):
    try:
        code = (await file.read()).decode("utf-8")
        ir = parser.parse_python_to_ir(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {e}")
    rows = explainer.explain_ir(ir)
    return {"explanation": rows, "ir": ir}

@app.post("/mermaid-file")
async def mermaid_file(file: UploadFile = File(...)):
    try:
        code = (await file.read()).decode("utf-8")
        ir = parser.parse_python_to_ir(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {e}")
    diagram = graph.ir_to_mermaid(ir)
    return {"mermaid": diagram}

# -------- Combined endpoint (best for UI) --------
@app.post("/analyze")
def analyze(req: CodeRequest, include_ir: bool = Query(False)):
    ir = parser.parse_python_to_ir(req.code)
    rows = explainer.explain_ir(ir)   # list of {line, indent, text}
    diagram = graph.ir_to_mermaid(ir)
    payload = {"explanation": rows, "mermaid": diagram}
    if include_ir: payload["ir"] = ir
    return payload


@app.post("/analyze-file")
async def analyze_file(
    file: UploadFile = File(...),
    include_ir: bool = Query(False, description="Include raw IR in the response"),
):
    """
    Same as /analyze but accepts a .py upload.
    """
    try:
        code = (await file.read()).decode("utf-8")
        ir = parser.parse_python_to_ir(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {e}")

    rows = explainer.explain_ir(ir)
    diagram = graph.ir_to_mermaid(ir)

    payload = {
        "explanation": rows,
        "mermaid": diagram,
    }
    if include_ir:
        payload["ir"] = ir
    return payload
