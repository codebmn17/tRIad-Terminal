from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from predictors.knn import predict as predict_knn
from predictors.forest import predict as predict_forest


app = FastAPI(title="Iris Predictor API")


class PredictRequest(BaseModel):
    x: List[float] = Field(..., description="List of 4 features: [sepal_length, sepal_width, petal_length, petal_width]")


@app.post("/predict/knn")
def post_predict_knn(payload: PredictRequest):
    try:
        return predict_knn(payload.x)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


@app.post("/predict/forest")
def post_predict_forest(payload: PredictRequest):
    try:
        return predict_forest(payload.x)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
