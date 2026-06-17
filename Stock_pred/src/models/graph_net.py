import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv
import numpy as np

class RelationalGraphNet(nn.Module):
    """
    Graph Neural Network for Multi-Ticker Correlation Aware Prediction.
    Nodes: Tickers (e.g., RELIANCE, INFY)
    Edges: Sectoral or Correlation dependencies.
    """
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(RelationalGraphNet, self).__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, out_channels)
        
    def forward(self, x, edge_index):
        # x: [num_nodes, in_channels]
        # edge_index: [2, num_edges]
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=0.2, training=self.training)
        x = self.conv2(x, edge_index)
        return x

def build_market_graph(tickers: list[str]) -> torch.Tensor:
    """
    Build edge_index based on ticker correlations.
    For simplicity, we connect all nodes initially (Fully Connected Meta-Graph).
    """
    num_nodes = len(tickers)
    edges = []
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i != j:
                edges.append([i, j])
                
    return torch.tensor(edges, dtype=torch.long).t().contiguous()

def train_graph_net(ticker_features: dict[str, np.ndarray], targets: dict[str, np.ndarray]):
    """
    Trains the Relational Graph Network on a batch of multi-ticker features.
    Ensures input is 2D [num_nodes, num_features].
    """
    tickers = list(ticker_features.keys())
    
    # Use only the last timestamp for graph nodes to ensure 2D [num_tickers, num_features]
    X_list = []
    Y_list = []
    for t in tickers:
        X_list.append(ticker_features[t][-1]) # Take latest features
        Y_list.append(targets[t][-1])         # Take latest target
        
    X = torch.tensor(np.stack(X_list), dtype=torch.float32)
    Y = torch.tensor(np.stack(Y_list), dtype=torch.float32).view(-1, 1)
    
    edge_index = build_market_graph(tickers)
    
    num_features = X.shape[1]
    model = RelationalGraphNet(in_channels=num_features, hidden_channels=64, out_channels=1)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    
    model.train()
    for _ in range(50):
        optimizer.zero_grad()
        out = model(X, edge_index)
        loss = F.mse_loss(out, Y)
        loss.backward()
        optimizer.step()
        
    return model, edge_index

