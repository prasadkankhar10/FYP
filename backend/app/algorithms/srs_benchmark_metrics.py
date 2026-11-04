"""
app/algorithms/srs_benchmark_metrics.py — SRS Benchmark Evaluation Metrics

Implements the official evaluation metrics used by open-spaced-repetition/srs-benchmark:
  1. Log Loss (Binary Cross-Entropy)
  2. Binned RMSE (20 Bins calibration metric)
  3. AUC-ROC (Area Under the Receiver Operating Characteristic curve)
  4. Pearson Correlation / Calibration details
"""
import math
from typing import List, Tuple, Dict, Any


def compute_log_loss(y_true: List[int], y_pred: List[float], eps: float = 1e-15) -> float:
    """
    Computes binary cross-entropy / log loss.
    y_true: list of 0 (forgotten/again) or 1 (remembered/passed)
    y_pred: list of predicted probabilities in [0.0, 1.0]
    """
    if not y_true or len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must be non-empty lists of the same length.")

    total_loss = 0.0
    n = len(y_true)
    for yt, yp in zip(y_true, y_pred):
        p = max(eps, min(1.0 - eps, float(yp)))
        if yt == 1:
            total_loss -= math.log(p)
        else:
            total_loss -= math.log(1.0 - p)

    return total_loss / n


def compute_rmse_bins(
    y_true: List[int], y_pred: List[float], num_bins: int = 20
) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Computes binned Root Mean Square Error (RMSE) across 20 retention bins,
    matching open-spaced-repetition/srs-benchmark methodology.

    Returns:
        weighted_rmse: float
        bin_details: list of dicts containing bin statistics (for plotting calibration curves)
    """
    if not y_true or len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must be non-empty lists of the same length.")

    n = len(y_true)
    bin_width = 1.0 / num_bins
    bins_data = [
        {"count": 0, "sum_pred": 0.0, "sum_true": 0, "bin_min": i * bin_width, "bin_max": (i + 1) * bin_width}
        for i in range(num_bins)
    ]

    for yt, yp in zip(y_true, y_pred):
        p = max(0.0, min(1.0, float(yp)))
        bin_idx = int(p / bin_width)
        if bin_idx >= num_bins:
            bin_idx = num_bins - 1
        bins_data[bin_idx]["count"] += 1
        bins_data[bin_idx]["sum_pred"] += p
        bins_data[bin_idx]["sum_true"] += yt

    weighted_sq_err_sum = 0.0
    active_bins_details = []

    for idx, b in enumerate(bins_data):
        cnt = b["count"]
        bin_center = (b["bin_min"] + b["bin_max"]) / 2.0
        if cnt > 0:
            mean_pred = b["sum_pred"] / cnt
            mean_true = b["sum_true"] / cnt
            sq_err = (mean_pred - mean_true) ** 2
            weight = cnt / n
            weighted_sq_err_sum += weight * sq_err

            active_bins_details.append({
                "bin_idx": idx,
                "bin_center": bin_center,
                "count": cnt,
                "mean_pred": mean_pred,
                "mean_true": mean_true,
                "error": mean_pred - mean_true
            })
        else:
            active_bins_details.append({
                "bin_idx": idx,
                "bin_center": bin_center,
                "count": 0,
                "mean_pred": bin_center,
                "mean_true": bin_center,
                "error": 0.0
            })

    weighted_rmse = math.sqrt(weighted_sq_err_sum)
    return weighted_rmse, active_bins_details


def compute_auc(y_true: List[int], y_pred: List[float]) -> float:
    """
    Computes Wilcoxon-Mann-Whitney Area Under the ROC Curve (AUC).
    Handles tied prediction values without requiring external heavy dependencies.
    """
    if not y_true or len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must be non-empty lists of the same length.")

    n_pos = sum(1 for y in y_true if y == 1)
    n_neg = len(y_true) - n_pos

    if n_pos == 0 or n_neg == 0:
        return 0.5  # Degenerate case when all labels are identical

    # Pair and sort by predicted probability ascending
    paired = sorted(zip(y_pred, y_true), key=lambda x: x[0])

    # Assign ranks (handling ties with average rank)
    ranks = [0.0] * len(paired)
    i = 0
    while i < len(paired):
        j = i
        while j < len(paired) and paired[j][0] == paired[i][0]:
            j += 1
        # Rank is 1-based, average rank for ties
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[k] = avg_rank
        i = j

    # Sum of ranks for positive class
    sum_ranks_pos = sum(rank for rank, (_, yt) in zip(ranks, paired) if yt == 1)

    # Mann-Whitney U statistic
    u = sum_ranks_pos - (n_pos * (n_pos + 1)) / 2.0
    auc = u / (n_pos * n_neg)
    return float(auc)


def evaluate_all_metrics(y_true: List[int], y_pred: List[float]) -> Dict[str, Any]:
    """
    Evaluates all standard SRS benchmark metrics in a single pass.
    """
    loss = compute_log_loss(y_true, y_pred)
    rmse_bins, bin_details = compute_rmse_bins(y_true, y_pred, num_bins=20)
    auc = compute_auc(y_true, y_pred)

    return {
        "log_loss": round(loss, 4),
        "rmse_bins": round(rmse_bins, 4),
        "auc": round(auc, 4),
        "sample_count": len(y_true),
        "bin_details": bin_details
    }
