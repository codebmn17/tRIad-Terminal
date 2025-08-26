from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
from typing import List, Dict, Any, Optional

# ---- load model JSON ----
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
MODEL_PATH = (HERE / ".." / ".." / "agents" / "learning" / "unstoppable_iris_model.json").resolve()

with open(MODEL_PATH, "r", encoding="utf-8") as f:
    MODEL = json.load(f)

FEATURE_NAMES: List[str] = MODEL.get("feature_names") or []
CLASSES: List[str] = MODEL.get("classes") or []
TREE = MODEL["tree"]  # nested dict: {feature:int, threshold:float, left:node, right:node, value:[counts...]}

# ---- traversal ----
def predict_from_tree(x_by_idx: List[float]) -> Dict[str, Any]:
    node = TREE
    while "value" not in node:
        feat_idx = node["feature"]
        thr = node["threshold"]
        node = node["left"] if x_by_idx[feat_idx] <= thr else node["right"]
    counts = node["value"]  # e.g. [n_setosa, n_versicolor, n_virginica]
    total = max(sum(counts), 1)
    probs = [c / total for c in counts]
    pred_idx = int(max(range(len(probs)), key=lambda i: probs[i]))
    return {
        "class_index": pred_idx,
        "class_label": CLASSES[pred_idx] if CLASSES else str(pred_idx),
        "probs": { (CLASSES[i] if i < len(CLASSES) else str(i)): probs[i] for i in range(len(probs)) },
        "leaf_counts": counts,
    }

# ---- API ----
class PredictBody(BaseModel):
    # Either send "features" as an ordered list matching feature_names,
    # OR send "by_name" as a dict {feature_name: value}
    features: Optional[List[float]] = None
    by_name: Optional[Dict[str, float]] = None

app = FastAPI(title="Iris Model API", version="1.0")

@app.get("/meta")
def meta():
    return {
        "model_type": MODEL.get("model_type", "tree"),
        "feature_names": FEATURE_NAMES,
        "classes": CLASSES,
    }

@app.post("/predict")
def predict(body: PredictBody):
    if body.by_name:
        if not FEATURE_NAMES:
            raise HTTPException(400, "Model lacks feature_names; use 'features' array instead.")
        x = [float(body.by_name.get(name, 0.0)) for name in FEATURE_NAMES]
    elif body.features:
        x = list(map(float, body.features))
    else:
        raise HTTPException(400, "Provide 'features' (array) or 'by_name' (dict).")

    res = predict_from_tree(x)
    return {"ok": True, "prediction": res}
