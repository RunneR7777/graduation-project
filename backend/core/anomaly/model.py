import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import precision_score, recall_score, accuracy_score, roc_auc_score

# 配置参数
BATCH_SIZE = 64  # 批量大小
EPOCHS = 50  # 训练轮数
LEARNING_RATE = 0.003  # 学习率
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')  # 使用GPU（如果有的话），否则使用CPU
FEATURE_DIM = 41  # 特征维度，假设为41个特征

class LiquidTimeConstant(nn.Module):
    """液体时间常数（LTC）神经元层"""

    def __init__(self, input_dim, units):
        super(LiquidTimeConstant, self).__init__()
        self.units = units

        # 输入权重（用于将输入映射到神经元单元）
        self.w = nn.Parameter(torch.Tensor(input_dim, units))
        # 循环权重（用于将当前状态的输出传递回神经元）
        self.v = nn.Parameter(torch.Tensor(units, units))
        # 时间常数参数（控制状态更新的速度）
        self.tau = nn.Parameter(torch.ones(units))
        # 偏置
        self.b = nn.Parameter(torch.zeros(units))

        # 初始化权重
        nn.init.xavier_uniform_(self.w)  # 对输入权重进行Xavier初始化
        nn.init.orthogonal_(self.v)  # 对循环权重进行正交初始化

        # 将时间常数限制为正值，以防止不合适的训练过程
        self.tau = nn.Parameter(torch.clamp(self.tau, min=0.1, max=5.0))

    def forward(self, x, prev_state):
        """LTC神经元的前向传播"""
        # 计算状态更新（dx），使用tanh激活函数
        dx = -prev_state + torch.tanh(torch.matmul(x, self.w) + torch.matmul(prev_state, self.v) + self.b)
        # 根据时间常数更新神经元的状态
        state = prev_state + dx * (1.0 / self.tau).view(1, -1)
        return state


class LNN(nn.Module):
    """液体神经网络（LNN）"""

    def __init__(self, input_dim, hidden_dim, num_classes, max_timesteps):
        super(LNN, self).__init__()
        # 第一层LTC神经元（输入到隐藏）
        self.ltc1 = LiquidTimeConstant(input_dim, hidden_dim)
        # 第二层LTC神经元（隐藏到隐藏）
        self.ltc2 = LiquidTimeConstant(hidden_dim, hidden_dim)
        # 注意力机制（用于聚焦在输入序列的不同部分）
        self.attention = nn.Linear(hidden_dim, 1)
        # 输出层，最终将隐藏状态映射到类别
        self.fc = nn.Linear(hidden_dim, num_classes)
        # 最大时间步长
        self.max_timesteps = max_timesteps

    def forward(self, x):
        batch_size = x.size(0)
        state = torch.zeros(batch_size, self.ltc1.units).to(x.device)
        hidden_states = []  # 新增：保存每个时间步的隐藏状态
        attention_weights = []

        for t in range(self.max_timesteps):
            state = self.ltc1(x[:, t, :], state)
            state = self.ltc2(state, state)
            hidden_states.append(state)  # 保存当前时间步的state
            attention_weights.append(self.attention(state))  # 形状：(batch_size, 1)

        # 调整维度
        hidden_states = torch.stack(hidden_states, dim=1)  # 形状：(batch_size, max_timesteps, hidden_dim)
        attention_weights = torch.cat(attention_weights, dim=1)  # 形状：(batch_size, max_timesteps)
        attention_weights = torch.softmax(attention_weights, dim=1).unsqueeze(2)  # 形状：(batch_size, max_timesteps, 1)

        # 计算上下文向量
        context = torch.sum(hidden_states * attention_weights, dim=1)  # 形状：(batch_size, hidden_dim)

        out = self.fc(context)
        return out


def train_model(model, train_loader, val_loader, criterion, optimizer, epochs):
    """训练模型"""
    best_val_loss = float('inf')
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        train_preds = []  # 新增：存储训练集预测结果
        train_labels = []  # 新增：存储训练集真实标签

        for inputs, labels in train_loader:
            inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * inputs.size(0)
            # 收集训练集的预测结果和真实标签
            _, preds = torch.max(outputs, 1)
            train_preds.extend(preds.cpu().numpy())
            train_labels.extend(labels.cpu().numpy())

        # 计算训练集准确率
        train_acc = accuracy_score(train_labels, train_preds)
        train_loss = train_loss / len(train_loader.dataset)

        # 验证过程
        model.eval()
        val_loss = 0.0
        val_preds = []
        val_labels = []
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * inputs.size(0)

                _, preds = torch.max(outputs, 1)
                val_preds.extend(preds.cpu().numpy())
                val_labels.extend(labels.cpu().numpy())

        val_loss = val_loss / len(val_loader.dataset)
        val_acc = accuracy_score(val_labels, val_preds)

        # 输出训练集和验证集结果
        print(f'Epoch {epoch + 1}/{epochs} - '
              f'Train Loss: {100*train_loss:.2f}% - '
              f'Train Acc: {100*train_acc:.2f}% - '
              f'Val Loss: {100*val_loss:.2f}% - '
              f'Val Acc: {100*val_acc:.2f}%')

        # 保存最佳模型
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), '../models/model.pth')

    print('Training complete')


def evaluate_model(model, test_loader, criterion):
    """评估模型"""
    model.eval()
    test_loss = 0.0
    test_preds = []
    test_labels = []
    all_probs = []
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            test_loss += loss.item() * inputs.size(0)

            probs = torch.softmax(outputs, dim=1)
            _, preds = torch.max(outputs, 1)
            test_preds.extend(preds.cpu().numpy())
            test_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())

    test_loss = test_loss / len(test_loader.dataset)
    test_acc = accuracy_score(test_labels, test_preds)

    # 输出测试集结果
    print(f'\nTest Loss: {100*test_loss:.2f} - Test Acc: {100*test_acc:.4f}')
    return test_loss, test_acc
