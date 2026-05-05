#!/usr/bin/env python3
"""Simple simulation comparing SM-2 (approx), FSRS (approx) and Multi-FSRS.
Generates CSV outputs and two PNGs in `report2_images/`:
- simulation_results.png  (reviews per day + mean predicted retrievability)
- schedule_trace.png     (example stability trace for one sample concept)

Usage: python scripts/simulate_multifsrs.py
Requires: numpy, matplotlib, pandas, networkx
"""
import os
import math
import random
from collections import defaultdict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx


OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'report2_images')
os.makedirs(OUT_DIR, exist_ok=True)


def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))


def make_graph(n_items, p_edge=0.03):
    G = nx.gnp_random_graph(n_items, p_edge, directed=True)
    # assign random expert/data/semantic weights
    for u, v in G.edges():
        G[u][v]['w_e'] = random.uniform(0.3, 0.9)
        G[u][v]['w_d'] = random.uniform(0.0, 0.5)
        G[u][v]['w_s'] = random.uniform(0.0, 0.5)
    return G


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def run_simulation(seed=1, N=200, DAYS=60):
    random.seed(seed)
    np.random.seed(seed)

    # initial stability per item (FSRS-like)
    S0 = np.random.uniform(0.6, 1.2, size=N)
    graph = make_graph(N)

    # common params
    S_min = 0.2
    alpha, beta, gamma = 0.6, 0.3, 0.1
    p_fail = 0.15
    p_pass = 0.05

    strategies = ['SM2', 'FSRS', 'MultiFSRS']
    results = {}

    for strat in strategies:
        # copy initial state
        S = S0.copy()
        next_review = np.zeros(N, dtype=int)  # day index when next due
        reviews_per_day = np.zeros(DAYS, dtype=int)
        mean_pred = np.zeros(DAYS)
        # store trace for item 0
        trace_S0 = []

        for day in range(DAYS):
            due = np.where(next_review <= day)[0]
            reviews_per_day[day] = len(due)

            # review each due item
            for i in due:
                # predicted recall probability roughly sigmoid(S - 1.0)
                prec = sigmoid(S[i] - 1.0)
                outcome = random.random() < prec

                # update rules (very simplified):
                if strat == 'SM2':
                    # SM2 uses repetition count -> longer intervals; model as multiplicative
                    if outcome:
                        S[i] = S[i] * 1.18
                        next_review[i] = day + int(max(1, round(1.5 * (S[i]))))
                    else:
                        S[i] = max(S_min, S[i] * 0.6)
                        next_review[i] = day + 1

                elif strat == 'FSRS':
                    if outcome:
                        S[i] = S[i] * 1.25
                        next_review[i] = day + int(max(1, round(2.0 * (S[i]))))
                    else:
                        S[i] = max(S_min, S[i] * 0.55)
                        next_review[i] = day + 1

                elif strat == 'MultiFSRS':
                    # apply FSRS update for base
                    if outcome:
                        delta = S[i] * 0.25
                        S[i] = S[i] * 1.25
                        next_review[i] = day + int(max(1, round(2.0 * (S[i]))))
                    else:
                        delta = S[i] * -0.45
                        S[i] = max(S_min, S[i] * 0.55)
                        next_review[i] = day + 1

                    # propagate to direct neighbors (one-hop) with small p_q
                    p_q = p_fail if not outcome else p_pass
                    for _, k in graph.out_edges(i):
                        # edge composition
                        e = graph[i][k]
                        w = clamp(alpha * e['w_e'] + beta * e['w_d'] + gamma * e['w_s'])
                        Delta_S_k = w * delta * p_q
                        S[k] = max(S_min, S[k] + Delta_S_k)

            mean_pred[day] = float(np.mean([sigmoid(x - 1.0) for x in S]))
            trace_S0.append(float(S[0]))

        results[strat] = {
            'reviews_per_day': reviews_per_day,
            'mean_pred': mean_pred,
            'trace_S0': trace_S0,
        }

    # save CSV
    df_rows = []
    for strat in strategies:
        for d in range(DAYS):
            df_rows.append({'strategy': strat, 'day': d, 'reviews': int(results[strat]['reviews_per_day'][d]), 'mean_pred': float(results[strat]['mean_pred'][d])})
    df = pd.DataFrame(df_rows)
    df.to_csv(os.path.join(OUT_DIR, 'simulation_results.csv'), index=False)

    # plot reviews/day and mean_pred in a single figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    for strat in strategies:
        ax1.plot(results[strat]['reviews_per_day'], label=strat)
        ax2.plot(results[strat]['mean_pred'], label=strat)
    ax1.set_title('Reviews per day')
    ax1.set_ylabel('Num reviews')
    ax1.legend()
    ax2.set_title('Mean predicted retrievability')
    ax2.set_ylabel('Mean P(recall)')
    ax2.set_xlabel('Day')
    ax2.legend()
    plt.tight_layout()
    fig_path = os.path.join(OUT_DIR, 'simulation_results.png')
    plt.savefig(fig_path, dpi=150)
    plt.close(fig)

    # save schedule trace for item 0
    plt.figure(figsize=(8, 3))
    for strat in strategies:
        plt.plot(results[strat]['trace_S0'], label=strat)
    plt.title('Stability trace for sample item (ID 0)')
    plt.ylabel('Stability S')
    plt.xlabel('Day')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, 'schedule_trace.png'), dpi=150)
    print('Saved simulation outputs to', OUT_DIR)


if __name__ == '__main__':
    run_simulation()
