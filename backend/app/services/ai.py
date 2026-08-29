from pathlib import Path
import json

MODEL_DIR = Path(__file__).resolve().parents[3] / "models"
MODEL_PATH = MODEL_DIR / "freshfusion_mobilenet_v1.pt"
LABELS_PATH = MODEL_DIR / "labels.json"
_model = None
_labels = None


def predict_image(path: Path) -> dict:
    global _model, _labels
    if not MODEL_PATH.exists() or not LABELS_PATH.exists():
        return {"status": "model_not_trained", "prediction": None, "confidence": None, "probabilities": {}}
    try:
        import torch
        from PIL import Image
        from torchvision import transforms
        if _model is None:
            _model = torch.jit.load(str(MODEL_PATH), map_location="cpu").eval()
            _labels = json.loads(LABELS_PATH.read_text())
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225]),
        ])
        tensor = transform(Image.open(path).convert("RGB")).unsqueeze(0)
        with torch.no_grad():
            probs = torch.softmax(_model(tensor), dim=1)[0].cpu().tolist()
        pairs = {label: round(float(probs[i])*100, 2) for i, label in enumerate(_labels)}
        idx = max(range(len(probs)), key=probs.__getitem__)
        return {"status":"ready", "prediction":_labels[idx], "confidence":round(float(probs[idx])*100,2), "probabilities":pairs}
    except Exception as exc:
        return {"status":"model_error", "prediction":None, "confidence":None, "probabilities":{}, "error":str(exc)}
