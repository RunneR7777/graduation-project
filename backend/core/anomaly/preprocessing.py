import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler
from torch.nn.utils.rnn import pad_sequence
from sklearn.model_selection import train_test_split

RANDOM_STATE = 42
MAX_TIMESTEPS = 10
FEATURE_DIM = 41  # 原始特征维度
GROUP_SIZE = 5  # 每个小组的大小


def load_and_process_data(csv_path):
    """加载并处理数据"""
    df = pd.read_csv(csv_path)

    # 阶段 2: 构建序列数据
    grouped = df.groupby('group_number')
    sequences = []
    labels = []

    # 初始化Scaler
    scaler = StandardScaler()
    scaler.fit(df.drop(columns=['label', 'group_number']))

    for name, group in grouped:
        features = scaler.transform(group.drop(columns=['label', 'group_number']))
        label = group['label'].iloc[0] - 1  # 转换为0-based标签
        sequences.append(torch.FloatTensor(features))
        labels.append(label)

    # 填充序列
    padded_sequences = pad_sequence(sequences, batch_first=True, padding_value=0)

    # 如果序列长度小于MAX_TIMESTEPS，进行填充
    if padded_sequences.size(1) < MAX_TIMESTEPS:
        pad = torch.zeros(padded_sequences.size(0),
                          MAX_TIMESTEPS - padded_sequences.size(1),
                          padded_sequences.size(2))
        padded_sequences = torch.cat([padded_sequences, pad], dim=1)
    # 如果序列长度大于MAX_TIMESTEPS，进行截断
    elif padded_sequences.size(1) > MAX_TIMESTEPS:
        padded_sequences = padded_sequences[:, :MAX_TIMESTEPS, :]

    # 转换标签为张量
    labels = torch.LongTensor(labels)

    return padded_sequences, labels, scaler


def split_data(X, y, test_size=0.2, random_state=42):
    """将数据集分为训练集、验证集和测试集"""
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=test_size, random_state=random_state)
    return X_train, X_val, y_train, y_val






