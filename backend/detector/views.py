from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from PIL import Image
import torch
import torchvision.transforms as transforms
from .model_loader import get_model
import logging

logger = logging.getLogger(__name__)

# Load model ONCE
model = get_model()
model.eval()

# -------------------------
# Preprocessing (ViT standard safe version)
# -------------------------
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5],
                         std=[0.5, 0.5, 0.5])
])

def preprocess(image):
    image = transform(image)
    return image.unsqueeze(0)


# -------------------------
# HEALTH CHECK ENDPOINT (For Railway)
# -------------------------
@api_view(['GET'])
def health_check(request):
    return Response({
        'status': 'healthy',
        'model_loaded': model is not None
    })


# -------------------------
# PREDICTION API ENDPOINT
# -------------------------
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def predict_image(request):

    file = request.FILES.get('image')

    if file is None:
        return Response({
            "success": False,
            "message": "No image uploaded. Key must be 'image'."
        }, status=400)

    try:
        image = Image.open(file).convert("RGB")
        input_tensor = preprocess(image)

        with torch.no_grad():
            outputs = model(input_tensor)

            logits = outputs.logits
            probs = torch.softmax(logits, dim=1)

            confidence, pred = torch.max(probs, dim=1)

        pred_class = pred.item()
        confidence_value = float(confidence.item())

        # IMPORTANT: safer labeling logic
        label = "REAL" if pred_class == 1 else "FAKE"

        return Response({
            "success": True,
            "prediction": label,
            "confidence": round(confidence_value, 4),
            "raw_class": pred_class
        })

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return Response({
            "success": False,
            "message": str(e)
        }, status=500)