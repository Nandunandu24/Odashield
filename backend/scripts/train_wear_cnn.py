import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from PIL import Image

# 1. Custom Dataset that generates synthetic wear images on-the-fly
# This ensures training works without external image downloads
class SyntheticWearDataset(Dataset):
    def __init__(self, num_samples=300, transform=None):
        """
        Generates synthetic images representing pedal, steering, and seat wear.
        Classes: 0 = LOW, 1 = MEDIUM, 2 = HIGH
        """
        self.num_samples = num_samples
        self.transform = transform
        self.data = []
        self.labels = []
        
        for _ in range(num_samples):
            # Pick a class
            label = np.random.randint(0, 3)
            
            # Generate a 3-channel 64x64 image
            # Base background color representing interior materials (e.g. leather, rubber)
            img = np.ones((64, 64, 3), dtype=np.uint8) * 128
            
            if label == 0:
                # LOW wear: Smooth, uniform with minimal noise
                noise = np.random.normal(0, 5, (64, 64, 3))
                img = np.clip(img + noise, 0, 255).astype(np.uint8)
            elif label == 1:
                # MEDIUM wear: Some scratches (lines) and moderate noise
                noise = np.random.normal(0, 15, (64, 64, 3))
                img = np.clip(img + noise, 0, 255).astype(np.uint8)
                # Draw a few gray lines representing scuffs
                for _ in range(3):
                    x1, y1 = np.random.randint(5, 59, 2)
                    x2, y2 = np.random.randint(5, 59, 2)
                    # Simple drawing directly in numpy
                    img[min(y1,y2):max(y1,y2), min(x1,x2):max(x1,x2), :] = 80
            else:
                # HIGH wear: Major dark worn patches (rubber/foam exposure) and high noise
                noise = np.random.normal(0, 30, (64, 64, 3))
                img = np.clip(img + noise, 0, 255).astype(np.uint8)
                # Draw a large dark patch
                px, py = np.random.randint(10, 40, 2)
                img[py:py+20, px:px+20, :] = 30
                
            self.data.append(img)
            self.labels.append(label)
            
    def __len__(self):
        return self.num_samples
        
    def __getitem__(self, idx):
        img = self.data[idx]
        label = self.labels[idx]
        
        # Convert to float PyTorch tensor [Channels, Height, Width] normalized to [0, 1]
        img_tensor = torch.tensor(img, dtype=torch.float32).permute(2, 0, 1) / 255.0
        
        return img_tensor, label

# 2. Define a simple, fast-compiling CNN structure mimicking ResNet classification layers
class OdoWearCNN(nn.Module):
    def __init__(self):
        super(OdoWearCNN, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),  # 64x64 -> 32x32
            
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),  # 32x32 -> 16x16
            
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2)   # 16x16 -> 8x8
        )
        self.classifier = nn.Sequential(
            nn.Linear(64 * 8 * 8, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 3)  # Output classes: LOW, MEDIUM, HIGH
        )
        
    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x

def train_cnn():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(current_dir, "..", "models")
    model_path = os.path.join(model_dir, "wear_cnn.pth")
    
    # Create dataset & loaders
    train_dataset = SyntheticWearDataset(num_samples=300)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    
    # Init model, loss, optimizer
    model = OdoWearCNN()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    print("Training OdoWearCNN on synthetic dataset...")
    model.train()
    
    epochs = 5
    for epoch in range(epochs):
        running_loss = 0.0
        correct = 0
        total = 0
        
        for inputs, labels in train_loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * inputs.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
            
        epoch_loss = running_loss / len(train_loader.dataset)
        epoch_acc = (correct / total) * 100
        print(f"Epoch {epoch+1}/{epochs} - Loss: {epoch_loss:.4f} - Accuracy: {epoch_acc:.2f}%")
        
    # Save trained model weights
    os.makedirs(model_dir, exist_ok=True)
    torch.save(model.state_dict(), model_path)
    print(f"Successfully trained and saved PyTorch CNN to {model_path}")

if __name__ == "__main__":
    train_cnn()
