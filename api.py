from typing import Any, Dict, Optional

from fastapi import FastAPI, Body, Query
from fastapi.middleware.cors import CORSMiddleware

from eto_client import modresult, modsearch, search_tours

app = FastAPI(title="eto-tours-mcp")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True}


@app.post("/modsearch")
def modsearch_api(payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    return modsearch(payload)


@app.get("/modresult")
def modresult_api(requestid: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    if not requestid:
        return {"success": False, "error": "requestid обязателен"}
    return modresult(requestid)


@app.post("/modresult")
def modresult_api_post(payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    requestid = payload.get("requestid") or payload.get("search_id")
    if not requestid:
        return {"success": False, "error": "requestid обязателен"}
    return modresult(requestid)


@app.post("/search")
def search(payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    return modsearch(payload)


@app.post("/search_tours")
def search_tours_api(payload: Dict[str, Any] = Body(default_factory=dict)) -> Dict[str, Any]:
    return search_tours(payload)


@app.get("/result")
def result(requestid: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    if not requestid:
        return {"success": False, "error": "requestid обязателен"}
    return modresult(requestid)
