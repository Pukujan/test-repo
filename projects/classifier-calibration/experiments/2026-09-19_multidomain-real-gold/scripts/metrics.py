#!/usr/bin/env python3
"""Shared calibration metrics. Only committed aggregate numbers use these."""
from __future__ import annotations

import numpy as np


def softmax(z: np.ndarray, T: float = 1.0) -> np.ndarray:
    z = np.asarray(z, dtype=np.float64) / T
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def log_loss(y_index: np.ndarray, probs: np.ndarray) -> float:
    p = np.clip(probs[np.arange(len(y_index)), y_index], 1e-12, 1.0)
    return float(-np.log(p).mean())


def brier(y_index: np.ndarray, probs: np.ndarray) -> float:
    y = np.zeros_like(probs)
    y[np.arange(len(y_index)), y_index] = 1.0
    return float(((probs - y) ** 2).sum(axis=1).mean())


def expected_calibration_error(y_index: np.ndarray, probs: np.ndarray, n_bins: int = 10) -> float:
    conf = probs.max(axis=1)
    pred = probs.argmax(axis=1)
    correct = (pred == y_index).astype(np.float64)
    ece = 0.0
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (conf > lo) & (conf <= hi) if lo > 0 else (conf >= lo) & (conf <= hi)
        if mask.sum() == 0:
            continue
        ece += abs(correct[mask].mean() - conf[mask].mean()) * mask.mean()
    return float(ece)


def fit_temperature(logits: np.ndarray, y_index: np.ndarray) -> float:
    """Temperature scaling (Guo et al. 2017): minimize NLL of softmax(z/T). Golden-section 1-D search."""
    logits = np.asarray(logits, dtype=np.float64)

    def nll(T: float) -> float:
        return log_loss(y_index, softmax(logits, T))

    lo, hi = 0.05, 20.0
    gr = (np.sqrt(5) - 1) / 2
    a, b = lo, hi
    c, d = b - gr * (b - a), a + gr * (b - a)
    for _ in range(200):
        if nll(c) < nll(d):
            b, d = d, c
            c = b - gr * (b - a)
        else:
            a, c = c, d
            d = a + gr * (b - a)
        if b - a < 1e-6:
            break
    return float((a + b) / 2)


def metric_block(y_index: np.ndarray, probs: np.ndarray) -> dict:
    pred = probs.argmax(axis=1)
    acc = float((pred == y_index).mean())
    return {
        "accuracy": round(acc, 6),
        "log_loss": round(log_loss(y_index, probs), 6),
        "brier": round(brier(y_index, probs), 6),
        "ece": round(expected_calibration_error(y_index, probs), 6),
    }
