from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import json
from cascade_analysis import run_complete_cascade_analysis
from cascade_db import get_all_nodes, get_all_goals, get_all_signals, get_all_findings, add_signal, add_finding

app = FastAPI(title="Project Cascade")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/analysis/recent")
async def recent():
    signals = get_all_signals(limit=5) or []
    findings = get_all_findings(status_filter='active') or []
    return {"signals": signals[:5], "findings": findings[:5]}

@app.post("/api/analysis/run")
async def run(data: dict):
    url = data.get("url_or_topic", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="url_or_topic required")
    
    nodes = get_all_nodes()
    goals = get_all_goals()
    result = run_complete_cascade_analysis(url, nodes, goals)
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))
    
    for sig in result.get('signals', []):
        add_signal(int(sig.get('node_id', 1)), "cascade_analysis", sig.get('description', ''), sig.get('severity', 'warning'), None, url[:50])
    
    for finding in result.get('findings', []):
        add_finding(finding.get('mechanism', 'Finding'), finding.get('summary', ''), finding.get('confidence', 0)/100, json.dumps({'title': finding.get('title')}))
    
    return {"success": True, "analysis": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
