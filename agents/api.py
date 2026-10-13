"""
FastAPI REST API Server for Reynolds Risk Score.
"""
from typing import Dict, Any, List
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from risk import calculate_reynolds_risk
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Reynolds Risk Score API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


class ReynoldsRiskRequest(BaseModel):
    sex: str
    age: float
    systolic_bp: float
    total_cholesterol: float
    hdl_cholesterol: float
    hs_crp: float
    smoker: bool
    parental_mi_before_60: bool
    diabetes: bool = False
    hba1c: float | None = None


class ChatRequest(BaseModel):
    query: str


@app.post("/api/risk")
def api_risk(payload: ReynoldsRiskRequest):
    try:
        return calculate_reynolds_risk(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "reynolds-risk-score", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    from .base import SecurityException
    try:
        dossier = supervisor.process_task(payload)
    except SecurityException as exc:
        raise HTTPException(status_code=422, detail="Potential personal identifier in audit input") from exc
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


# Local deployments serve the same offline-capable frontend as GitHub Pages.
app.mount("/", StaticFiles(directory=str(Path(__file__).resolve().parent.parent / "web"), html=True), name="web")
