"""教学用排序模型：3 个特征 -> 1 个分数的小型 MLP（CPU 即可，毫秒级推理）。"""
from __future__ import annotations

import torch
from torch import nn

FEATURES = 3


class Ranker(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(FEATURES, 8), nn.Tanh(), nn.Linear(8, 1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # (N, 3) -> (N,)
        return self.net(x).squeeze(-1)


def load_ranker(path: str) -> Ranker:
    model = Ranker()
    model.load_state_dict(torch.load(path, map_location="cpu", weights_only=True))
    model.eval()
    return model
