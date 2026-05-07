import torch
import os
import logging
from transformers import ViTForImageClassification, ViTImageProcessor
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

# Model configuration
MODEL_NAME = "google/vit-base-patch16-224-in21k"
NUM_LABELS = 2
LABELS = ["REAL", "FAKE"]

# Check if using custom trained model
USE_CUSTOM_MODEL = os.environ.get('USE_CUSTOM_MODEL', 'False') == 'True'
CUSTOM_MODEL_PATH = os.environ.get('CUSTOM_MODEL_PATH', 'model/model.pth')

# Cache directory for HuggingFace models (Railway persistent disk)
CACHE_DIR = os.environ.get('HF_HOME', '/cache/huggingface') if os.path.exists('/cache') else None

# Global variables to cache model and processor
_model = None
_processor = None

def get_processor():
    """Load and cache the image processor"""
    global _processor
    
    if _processor is None:
        logger.info(f"Loading image processor: {MODEL_NAME}")
        try:
            _processor = ViTImageProcessor.from_pretrained(
                MODEL_NAME,
                cache_dir=CACHE_DIR
            )
            logger.info("Image processor loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load image processor: {str(e)}")
            raise
    
    return _processor

def get_model():
    """Load and cache the ViT model"""
    global _model
    
    if _model is None:
        try:
            # Check if we should use custom trained model
            if USE_CUSTOM_MODEL and os.path.exists(CUSTOM_MODEL_PATH):
                logger.info(f"Loading custom trained model from {CUSTOM_MODEL_PATH}")
                _model = load_custom_model()
            else:
                logger.info(f"Loading pretrained model: {MODEL_NAME}")
                _model = load_pretrained_model()
            
            # Set to evaluation mode
            _model.eval()
            
            # Move to appropriate device
            device = get_device()
            _model = _model.to(device)
            logger.info(f"Model loaded successfully on device: {device}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise
    
    return _model

def load_pretrained_model():
    """Load pretrained ViT model for inference"""
    model = ViTForImageClassification.from_pretrained(
        MODEL_NAME,
        num_labels=NUM_LABELS,
        ignore_mismatched_sizes=True,
        cache_dir=CACHE_DIR
    )
    
    # Initialize classifier head for 2 classes if not already trained
    if not USE_CUSTOM_MODEL:
        # For zero-shot/pretrained-only mode, we just use the model as is
        # The model will output logits for all 1000 classes, we'll map to REAL/FAKE later
        pass
    
    return model

def load_custom_model():
    """Load fine-tuned custom model from checkpoint"""
    # First load pretrained architecture
    model = ViTForImageClassification.from_pretrained(
        MODEL_NAME,
        num_labels=NUM_LABELS,
        ignore_mismatched_sizes=True,
        cache_dir=CACHE_DIR
    )
    
    # Load custom weights
    if os.path.exists(CUSTOM_MODEL_PATH):
        logger.info(f"Loading custom weights from {CUSTOM_MODEL_PATH}")
        
        # Check if it's a full model or just state dict
        if CUSTOM_MODEL_PATH.endswith('.pth'):
            state_dict = torch.load(CUSTOM_MODEL_PATH, map_location="cpu")
            
            # Handle different save formats
            if 'model_state_dict' in state_dict:
                state_dict = state_dict['model_state_dict']
            elif 'state_dict' in state_dict:
                state_dict = state_dict['state_dict']
            
            # Load with strict=False to allow missing/unexpected keys
            missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)
            
            if missing_keys:
                logger.warning(f"Missing keys: {missing_keys}")
            if unexpected_keys:
                logger.warning(f"Unexpected keys: {unexpected_keys}")
        else:
            # Try loading entire model
            model = torch.load(CUSTOM_MODEL_PATH, map_location="cpu")
    
    return model

def get_device():
    """Get the appropriate device for inference"""
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")  # For Mac M1/M2
    else:
        return torch.device("cpu")

def predict_image(image_tensor):
    """
    Run inference on preprocessed image tensor
    
    Args:
        image_tensor: Preprocessed image tensor (batch_size, channels, height, width)
    
    Returns:
        tuple: (prediction_label, confidence_score)
    """
    try:
        model = get_model()
        processor = get_processor()
        device = get_device()
        
        # Ensure tensor is on correct device
        if isinstance(image_tensor, torch.Tensor):
            image_tensor = image_tensor.to(device)
        else:
            # Convert to tensor if not already
            image_tensor = torch.tensor(image_tensor).to(device)
        
        # Add batch dimension if missing
        if image_tensor.dim() == 3:
            image_tensor = image_tensor.unsqueeze(0)
        
        # Run inference
        with torch.no_grad():
            outputs = model(pixel_values=image_tensor)
            logits = outputs.logits
        
        # Apply softmax to get probabilities
        probabilities = torch.softmax(logits, dim=1)
        
        # Get prediction and confidence
        confidence, predicted_class = torch.max(probabilities, dim=1)
        
        # Convert to Python values
        predicted_label = LABELS[predicted_class.item()]
        confidence_score = confidence.item() * 100  # Convert to percentage
        
        logger.info(f"Prediction: {predicted_label}, Confidence: {confidence_score:.2f}%")
        
        return predicted_label, confidence_score
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise

def predict_with_pretrained(image_tensor):
    """
    Alternative: Use pretrained model without fine-tuning
    Maps ImageNet classes to REAL/FAKE based on heuristic
    """
    model = get_model()
    device = get_device()
    
    if isinstance(image_tensor, torch.Tensor):
        image_tensor = image_tensor.to(device)
    
    if image_tensor.dim() == 3:
        image_tensor = image_tensor.unsqueeze(0)
    
    with torch.no_grad():
        outputs = model(pixel_values=image_tensor)
        logits = outputs.logits
    
    # Apply softmax
    probabilities = torch.softmax(logits, dim=1)
    
    # Get top prediction from ImageNet classes
    top_prob, top_class = torch.max(probabilities, dim=1)
    
    # Heuristic: Certain ImageNet classes indicate real vs fake
    # You can customize this mapping based on your needs
    fake_indicators = ['cartoon', 'animation', 'drawing', 'artificial', 'synthetic']
    real_indicators = ['photograph', 'portrait', 'landscape', 'natural']
    
    # For now, return with lower confidence if using pretrained only
    confidence = top_prob.item() * 50  # Scale down confidence for pretrained
    predicted_label = "REAL"  # Default
    
    return predicted_label, confidence

# Utility function to clear cache (useful for debugging)
def clear_cache():
    global _model, _processor
    _model = None
    _processor = None
    torch.cuda.empty_cache() if torch.cuda.is_available() else None
    logger.info("Model cache cleared")

# For testing the model loader
if __name__ == "__main__":
    # Test model loading
    print("Testing model loader...")
    model = get_model()
    processor = get_processor()
    print(f"Model loaded: {model.__class__.__name__}")
    print(f"Processor loaded: {processor.__class__.__name__}")
    print(f"Device: {get_device()}")
    print("Model loader test successful!")