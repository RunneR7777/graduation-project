import torch
import torch.nn as nn
import os

# 创建一个简单的权重文件用于测试
def create_dummy_model():
    """创建一个简单模型权重文件用于测试"""
    
    # 创建一个简单的模型结构
    class SimpleModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc1 = nn.Linear(41, 128)
            self.fc2 = nn.Linear(128, 64)
            self.fc3 = nn.Linear(64, 8)
        
        def forward(self, x):
            x = torch.relu(self.fc1(x.view(x.size(0), -1)))
            x = torch.relu(self.fc2(x))
            x = self.fc3(x)
            return x
    
    model = SimpleModel()
    
    # 保存模型权重
    model_path = os.path.join(os.path.dirname(__file__), 'anomaly_model.pth')
    torch.save(model.state_dict(), model_path)
    
    print(f"虚拟模型已保存到: {model_path}")

if __name__ == '__main__':
    create_dummy_model()






