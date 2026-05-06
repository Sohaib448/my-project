import torch
from transformers import ViTForImageClassification

MODEL_PATH = "model/model.pth"

def get_model():
    model = ViTForImageClassification.from_pretrained(
        "google/vit-base-patch16-224-in21k",  # better base for finetuning
        num_labels=2,
        ignore_mismatched_sizes=True
    )

    state_dict = torch.load(MODEL_PATH, map_location="cpu")
    model.load_state_dict(state_dict, strict=False)

    model.eval()
    return model 