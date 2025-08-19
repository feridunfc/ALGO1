# module_9_vae_regime_detector.py
# Simple VAE for detecting anomalous days via reconstruction error.

import torch
import torch.nn as nn
import torch.nn.functional as F

class VAE(nn.Module):
    def __init__(self, in_dim, latent_dim=8):
        super().__init__()
        self.fc1 = nn.Linear(in_dim, 32)
        self.fc_mu = nn.Linear(32, latent_dim)
        self.fc_logvar = nn.Linear(32, latent_dim)
        self.fc_dec1 = nn.Linear(latent_dim, 32)
        self.fc_out = nn.Linear(32, in_dim)

    def encode(self, x):
        h = F.relu(self.fc1(x))
        return self.fc_mu(h), self.fc_logvar(h)

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z):
        h = F.relu(self.fc_dec1(z))
        return self.fc_out(h)

    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        recon = self.decode(z)
        recon_loss = F.mse_loss(recon, x, reduction='mean')
        kld = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())
        loss = recon_loss + kld * 0.001
        return loss, recon

class MarketRegimeDetector:
    def __init__(self, in_dim, latent_dim=8, device=None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = VAE(in_dim, latent_dim).to(self.device)

    def fit(self, X, epochs=50, lr=1e-3, batch_size=64):
        X = torch.tensor(X, dtype=torch.float32).to(self.device)
        opt = torch.optim.Adam(self.model.parameters(), lr=lr)
        self.model.train()
        for ep in range(epochs):
            perm = torch.randperm(X.size(0))
            for i in range(0, X.size(0), batch_size):
                idx = perm[i:i+batch_size]
                batch = X[idx]
                loss, _ = self.model(batch)
                opt.zero_grad(); loss.backward(); opt.step()
            if (ep+1) % 10 == 0:
                print(f"Epoch {ep+1}/{epochs} - loss: {loss.item():.4f}")

    def reconstruction_error(self, X):
        self.model.eval()
        with torch.no_grad():
            X = torch.tensor(X, dtype=torch.float32).to(self.device)
            _, recon = self.model(X)
            err = torch.mean((X - recon)**2, dim=1)
        return err.cpu().numpy()

if __name__ == "__main__":
    import numpy as np
    X = np.random.randn(500, 12).astype('float32')
    detector = MarketRegimeDetector(in_dim=12)
    detector.fit(X, epochs=10)
    errs = detector.reconstruction_error(X[:5])
    print("Sample reconstruction errors:", errs)
