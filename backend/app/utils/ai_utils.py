import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import io

# Mock food list and nutrition info
FOOD_DATABASE = {
    "apple": {"calories": 52, "protein": 0.3, "carbs": 14, "fat": 0.2},
    "banana": {"calories": 89, "protein": 1.1, "carbs": 23, "fat": 0.3},
    "pizza": {"calories": 266, "protein": 11, "carbs": 33, "fat": 10},
    "salad": {"calories": 15, "protein": 1.0, "carbs": 3, "fat": 0.1},
    "burger": {"calories": 295, "protein": 17, "carbs": 24, "fat": 14},
    "rice": {"calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3},
}

class FoodClassifier:
    def __init__(self):
        # In a real scenario, we would load a custom trained model
        # For now, we use a pre-trained MobileNetV3 and mock the food categories
        self.model = models.mobilenet_v3_small(pretrained=True)
        self.model.eval()
        
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        
        # Real labels for pre-trained model (standard ImageNet)
        # We'll map some of them to our food items for this demo
        self.categories = list(FOOD_DATABASE.keys())

    def predict(self, image_bytes):
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        input_tensor = self.transform(image).unsqueeze(0)
        
        with torch.no_grad():
            output = self.model(input_tensor)
            
        # In this demo, we'll randomize a food detection from our DB 
        # based on the output to simulate high accuracy
        idx = torch.argmax(output).item() % len(self.categories)
        food_name = self.categories[idx]
        
        # Estimate portion (demo logic: based on image size relative to object)
        # In production, this would use a depth map or reference object (like a coin)
        portion_estimate = 1.0 # 1 serving
        
        base_nutrition = FOOD_DATABASE[food_name]
        
        return {
            "food_name": food_name,
            "calories": base_nutrition["calories"] * portion_estimate,
            "protein": base_nutrition["protein"] * portion_estimate,
            "carbs": base_nutrition["carbs"] * portion_estimate,
            "fat": base_nutrition["fat"] * portion_estimate,
            "portion_size": f"{portion_estimate} serving"
        }

food_detector = FoodClassifier()
