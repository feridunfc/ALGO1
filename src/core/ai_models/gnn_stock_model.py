# module_3_gnn_stock_model.py
# pip install torch torch-geometric numpy scikit-learn

import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv
from torch_geometric.data import Data
import numpy as np

class StockGNN(torch.nn.Module):
    """A Graph Neural Network to model inter-stock relationships."""
    def __init__(self, num_node_features, num_classes):
        super().__init__()
        self.conv1 = GCNConv(num_node_features, 64)
        self.conv2 = GCNConv(64, 32)
        self.out = torch.nn.Linear(32, num_classes)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=0.5, training=self.training)
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = self.out(x)
        return F.log_softmax(x, dim=1)

class GNNTrainer:
    def __init__(self, graph_data, num_node_features, num_classes):
        self.data = graph_data
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = StockGNN(num_node_features, num_classes).to(self.device)
        self.data = self.data.to(self.device)

    def fit(self, num_epochs=50):
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)
        self.model.train()
        print("Starting GNN training...")
        for epoch in range(num_epochs):
            optimizer.zero_grad()
            out = self.model(self.data.x, self.data.edge_index)
            loss = F.nll_loss(out[self.data.train_mask], self.data.y[self.data.train_mask])
            loss.backward()
            optimizer.step()
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{num_epochs}, Loss: {loss.item():.4f}")
        print("GNN training complete.")
    
    def predict(self):
        self.model.eval()
        with torch.no_grad():
            out = self.model(self.data.x, self.data.edge_index)
            preds = out.argmax(dim=1)
        return preds.cpu().numpy()

if __name__ == "__main__":
    num_stocks = 50
    num_features_per_stock = 10
    x = torch.randn(num_stocks, num_features_per_stock)

    # Build a toy correlation-based graph
    corr_matrix = np.random.rand(num_stocks, num_stocks)
    edge_list = np.argwhere(corr_matrix > 0.7)
    if edge_list.size == 0:
        # ensure at least a few edges for demo
        edge_list = np.array([[0,1],[1,2],[2,3],[3,4],[4,0]])
    edge_index = torch.tensor(edge_list.T, dtype=torch.long)

    y = torch.randint(0, 3, (num_stocks,))
    train_mask = torch.zeros(num_stocks, dtype=torch.bool)
    train_mask[:int(0.7 * num_stocks)] = True

    graph_data = Data(x=x, edge_index=edge_index, y=y, train_mask=train_mask)
    trainer = GNNTrainer(graph_data, num_features_per_stock, num_classes=3)
    trainer.fit(num_epochs=20)
    predictions = trainer.predict()
    print("Sample predictions (first 10):", predictions[:10])
