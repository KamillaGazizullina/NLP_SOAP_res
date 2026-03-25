from fastapi import FastAPI
from pydantic import BaseModel

from app.llm import generate_soap_llm
from app.pipeline import generate_soap
from app.database import save_log

app = FastAPI(title="SOAP Generator API")


class DialogRequest(BaseModel):
    dialog: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate")
def generate_baseline(request: DialogRequest):
    result = generate_soap(request.dialog)
    return {
        "mode": "baseline",
        "soap": result
    }


@app.post("/generate_llm")
def generate_llm(request: DialogRequest):
    result = generate_soap_llm(request.dialog)
    save_log(request.dialog, result, "llm")
    return {
        "mode": "llm",
        "soap": result
    }