from __future__ import annotations

from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from fastapi.middleware.cors import CORSMiddleware

from models import predict_knn, predict_forest

app = FastAPI(title="Triad Learning API", version="1.0.0")

# Allow browser tests from a file:// page and any local app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dev-friendly. Lock down later if needed.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FeaturesIn(BaseModel):
    features: List[float] = Field(..., description="Four numeric values [sepal_length, sepal_width, petal_length, petal_width]")

    @validator("features")
    def check_len_and_numbers(cls, v):
        if len(v) != 4:
            raise ValueError("features must be a list of exactly 4 numbers")
        try:
            [float(x) for x in v]
        except Exception as e:
            raise ValueError("features must be numeric") from e
        return v

@app.get("/")
def root():
    return {"ok": True, "message": "Triad Learning API is running", "endpoints": ["/predict/knn", "/predict/forest"]}

@app.post("/predict/knn")
def predict_knn_endpoint(inp: FeaturesIn):
    try:
        return predict_knn(inp.features)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/predict/forest")
def predict_forest_endpoint(inp: FeaturesIn):
    try:
        return predict_forest(inp.features)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
