import os
import logging
from typing import Dict, Any, Tuple
import numpy as np
from backend.app.config import settings

logger = logging.getLogger(__name__)

# Conditional imports for PyTorch and PIL
try:
    import torch
    import torch.nn as nn
    from PIL import Image
    import io
except ImportError:
    torch = None
    logger.warning("PyTorch or PIL not installed. Falling back to heuristic/mock wear analysis.")

# 1. Re-declare model architecture for inference
if torch is not None:
    class OdoWearCNN(nn.Module):
        def __init__(self):
            super(OdoWearCNN, self).__init__()
            self.features = nn.Sequential(
                nn.Conv2d(3, 16, kernel_size=3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2, 2),
                nn.Conv2d(16, 32, kernel_size=3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2, 2),
                nn.Conv2d(32, 64, kernel_size=3, padding=1),
                nn.ReLU(),
                nn.MaxPool2d(2, 2)
            )
            self.classifier = nn.Sequential(
                nn.Linear(64 * 8 * 8, 128),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(128, 3)
            )
            
        def forward(self, x):
            x = self.features(x)
            x = x.view(x.size(0), -1)
            x = self.classifier(x)
            return x
else:
    OdoWearCNN = None

class WearCnnService:
    _model = None
    _model_loaded = False
    
    @classmethod
    def load_model(cls) -> bool:
        """
        Loads the PyTorch wear classifier model weights.
        """
        if cls._model_loaded:
            return True
            
        if torch is None or OdoWearCNN is None:
            return False
            
        model_path = os.path.join(settings.MODEL_DIR, "wear_cnn.pth")
        if not os.path.exists(model_path):
            logger.warning(f"CNN model weights not found at {model_path}. Will use mock inference.")
            return False
            
        try:
            cls._model = OdoWearCNN()
            # Load state dict map to CPU to support non-GPU systems
            cls._model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
            cls._model.eval()
            cls._model_loaded = True
            logger.info("Wear CNN model successfully loaded.")
            return True
        except Exception as e:
            logger.error(f"Error loading Wear CNN: {e}")
            return False
            
    @classmethod
    def analyze_component_wear(cls, file_bytes: bytes, component_name: str) -> Dict[str, Any]:
        """
        Runs wear classification on uploaded image bytes for a specific component.
        """
        if cls.load_model() and cls._model is not None:
            try:
                # Preprocess image
                image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
                image = image.resize((64, 64))
                
                # Convert to Tensor [1, 3, 64, 64]
                img_array = np.array(image, dtype=np.float32) / 255.0
                img_tensor = torch.tensor(img_array).permute(2, 0, 1).unsqueeze(0)
                
                # Run inference
                with torch.no_grad():
                    outputs = cls._model(img_tensor)
                    probabilities = torch.softmax(outputs, dim=1).squeeze(0).tolist()
                    
                # Class mapping: 0=LOW, 1=MEDIUM, 2=HIGH
                p_low, p_medium, p_high = probabilities
                
                # Expectation calculation (continuous 0-10 score)
                # LOW maps around 1.5, MEDIUM around 5.0, HIGH around 8.5
                wear_score = float(p_low * 1.5 + p_medium * 5.0 + p_high * 8.5)
                wear_score = round(min(10.0, max(0.0, wear_score)), 2)
                
                # Assign wear level string
                if wear_score < 3.5:
                    wear_level = "LOW"
                elif wear_score < 7.0:
                    wear_level = "MEDIUM"
                else:
                    wear_level = "HIGH"
                    
                return {
                    "component": component_name,
                    "wear_score": wear_score,
                    "wear_level": wear_level,
                    "probabilities": {
                        "LOW": round(p_low, 3),
                        "MEDIUM": round(p_medium, 3),
                        "HIGH": round(p_high, 3)
                    },
                    "analyzed_by": "PyTorch CNN (OdoWearCNN)"
                }
                
            except Exception as e:
                logger.error(f"Error in CNN inference for {component_name}: {e}. Falling back to mock wear scoring.")
                
        # Mock/fallback scorer using filename/size hash or simple mock randomness
        # Let's seed based on the component name + length of file bytes to make it deterministic
        seed = sum(file_bytes[:100]) if len(file_bytes) > 0 else 0
        np.random.seed(seed)
        
        # Draw mock probabilities
        p_low = np.random.uniform(0.1, 0.9)
        p_medium = np.random.uniform(0.0, 1.0 - p_low)
        p_high = max(0.0, 1.0 - p_low - p_medium)
        
        # Soft expectation
        wear_score = float(p_low * 1.5 + p_medium * 5.0 + p_high * 8.5)
        wear_score = round(min(10.0, max(0.0, wear_score)), 2)
        
        if wear_score < 3.5:
            wear_level = "LOW"
        elif wear_score < 7.0:
            wear_level = "MEDIUM"
        else:
            wear_level = "HIGH"
            
        return {
            "component": component_name,
            "wear_score": wear_score,
            "wear_level": wear_level,
            "probabilities": {
                "LOW": round(p_low, 3),
                "MEDIUM": round(p_medium, 3),
                "HIGH": round(p_high, 3)
            },
            "analyzed_by": "Heuristic Mock Classifier"
        }
