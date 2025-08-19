# module_4_contrastive_feature_extractor.py
# Minimal SimCLR-style contrastive feature extractor for generic tabular/time-series.
# NOTE: This is a pedagogical skeleton; for production use, add strong augmentations and a proper projector.

import torch
import torch.nn as nn
import torch.nn.functional as F

class TinyEncoder(nn.Module):
    def __init__(self, in_dim, hidden=128, out_dim=64):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, out_dim),
        )
    def forward(self, x):
        return self.net(x)

class ProjectionHead(nn.Module):
    def __init__(self, in_dim, proj_dim=64):
        super().__init__()
        self.proj = nn.Sequential(
            nn.Linear(in_dim, in_dim),
            nn.ReLU(),
            nn.Linear(in_dim, proj_dim),
        )
    def forward(self, x):
        return self.proj(x)

class ContrastiveFeatureExtractor(nn.Module):
    def __init__(self, in_dim, hidden=128, feat_dim=64, temperature=0.2):
        super().__init__()
        self.encoder = TinyEncoder(in_dim, hidden, feat_dim)
        self.projector = ProjectionHead(feat_dim, feat_dim)
        self.temperature = temperature

    def info_nce_loss(self, z1, z2):
        z1 = F.normalize(z1, dim=-1)
        z2 = F.normalize(z2, dim=-1)
        logits = z1 @ z2.T / self.temperature
        labels = torch.arange(z1.size(0), device=z1.device)
        return F.cross_entropy(logits, labels)

    def forward(self, x1, x2):
        h1, h2 = self.encoder(x1), self.encoder(x2)
        z1, z2 = self.projector(h1), self.projector(h2)
        loss = self.info_nce_loss(z1, z2)
        return loss, h1.detach()

def simple_augment(x, noise_std=0.01):
    return x + noise_std * torch.randn_like(x)

if __name__ == "__main__":
    # Toy demo
    bsz, in_dim = 32, 20
    x = torch.randn(bsz, in_dim)
    x1, x2 = simple_augment(x), simple_augment(x)
    model = ContrastiveFeatureExtractor(in_dim)
    loss, feats = model(x1, x2)
    print("Contrastive loss:", float(loss), " | Feature shape:", tuple(feats.shape))
