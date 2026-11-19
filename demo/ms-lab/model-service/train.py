#!/usr/bin/env python3
"""训练教学用排序模型并保存为 state_dict。

ranker_v1 / ranker_v2 拟合两套不同的线性目标权重（对应讲义 §11.3 的两种排序配方）。
改 --seed 重新训练同名模型即可模拟「线上发布了新版本权重」，用于演示热加载（§9.2.2）。

用法：
  python train.py --out /models                       # 训练 v1 + v2
  python train.py --out /models --names ranker_v2 --seed 7
"""
from __future__ import annotations

import argparse
from pathlib import Path

import torch
from torch import nn

from ranker import FEATURES, Ranker

TARGETS = {
    "ranker_v1": [0.5, 0.3, 0.2],
    "ranker_v2": [0.8, 0.15, 0.05],
}


def train(name: str, seed: int, steps: int) -> Ranker:
    torch.manual_seed(seed)
    w = torch.tensor(TARGETS[name], dtype=torch.float32)
    x = torch.rand(512, FEATURES)
    y = x @ w
    model = Ranker()
    opt = torch.optim.Adam(model.parameters(), lr=0.02)
    loss_fn = nn.MSELoss()
    for _ in range(steps):
        opt.zero_grad()
        loss = loss_fn(model(x), y)
        loss.backward()
        opt.step()
    model.eval()
    print(f"{name}: seed={seed} steps={steps} final_mse={loss.item():.6f}", flush=True)
    return model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--names", nargs="*", default=list(TARGETS))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--steps", type=int, default=400)
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name in args.names:
        if name not in TARGETS:
            raise SystemExit(f"unknown model {name}; choices: {list(TARGETS)}")
        model = train(name, args.seed, args.steps)
        tmp = out / f".{name}.pt.tmp"
        torch.save(model.state_dict(), tmp)
        tmp.replace(out / f"{name}.pt")  # 原子替换，避免热加载读到半个文件
        print(f"saved {out / (name + '.pt')}", flush=True)


if __name__ == "__main__":
    main()
