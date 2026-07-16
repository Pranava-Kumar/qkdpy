#!/usr/bin/env python3
"""Test script for qkdpy modules — UTF-8 safe for Windows consoles."""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

#!/usr/bin/env python3
"""Comprehensive blackbox test of the qkdpy ML/Optimization module (v0.6.0).

Tests:
  - QKDOptimizer (Bayesian, genetic, neural optimization)
  - EfficientQKDPredictor (training, quantization, pruning, edge deployment)
  - AdaptiveModelSelector (memory detection, optimal config)
  - KnowledgeDistillation (teacher/student, temperature sweep)
  - EfficientModels (architecture sizing, resource constraints)
"""

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import math
import time

import numpy as np

# ---------------------------------------------------------------------------
# Check optional dependencies
# ---------------------------------------------------------------------------
try:
    import sklearn
    from sklearn.metrics import r2_score

    SKLEARN_AVAIL = True
    print(f"[INFO] sklearn version: {sklearn.__version__}")
except ImportError:
    SKLEARN_AVAIL = False
    print("[WARN] sklearn not available -- some tests will use fallbacks")

try:
    import psutil  # noqa: F401

    PSUTIL_AVAIL = True
except ImportError:
    PSUTIL_AVAIL = False
    print("[WARN] psutil not available -- memory estimation will use fallback")

# ---------------------------------------------------------------------------
# Imports from qkdpy
# ---------------------------------------------------------------------------
from qkdpy.ml import (
    AdaptiveModelSelector,
    EfficientQKDPredictor,
    KnowledgeDistillation,
    QKDAnomalyDetector,
    QKDOptimizer,
)

np.random.seed(42)
print("=" * 72)
print("  qkdpy v0.6.0 -- ML/Optimization Module Blackbox Test")
print("=" * 72)


# ===========================================================================
# UTILITY: synthetic QKD key-rate model
# ===========================================================================
def binary_entropy(x):
    """Binary Shannon entropy h2(x)."""
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return -x * math.log2(x) - (1.0 - x) * math.log2(1.0 - x)


def qkd_key_rate_from_dict(params):
    """Compute a physically-motivated key rate from a dict.

    Parameters
    ----------
    loss : float     (dB/km)  typical 0.1--0.5
    noise_level : float       (dark count prob) 1e-3 -- 1e-1
    distance : float (km)     0--150
    """
    loss = params.get("loss", 0.2)
    noise = params.get("noise_level", 0.01)
    dist = params.get("distance", 50.0)
    wl = params.get("wavelength", 1550.0)
    pw = params.get("power", 0.0)

    # Attenuation (dB -> linear)
    attenuation = 10.0 ** (-loss * dist / 10.0)
    # QBER  (noise + background from dark counts)
    qber = min(0.5, noise + 0.005 * (1.0 - attenuation))
    # Raw rate (MHz) scaled by attenuation & detector efficiency
    clock = 100.0  # MHz
    efficiency = 0.3 * (1.0 - min(1.0, abs(wl - 1550.0) / 200.0))
    raw_rate = clock * 1e6 * attenuation * efficiency
    # Key rate = raw * (1 - 2*h2(QBER))
    h = binary_entropy(qber)
    key_rate = raw_rate * max(0.0, 1.0 - 2.0 * h)
    # Power penalty
    if pw != 0.0:
        key_rate *= max(0.0, 1.0 - 0.1 * abs(pw))
    return key_rate


def qkd_key_rate_vector(X):
    """Vectorised version expecting (N, 5) array [loss, noise, dist, wl, pw]."""
    loss, noise, dist, wl, pw = X.T
    att = 10.0 ** (-loss * dist / 10.0)
    qber = np.minimum(0.5, noise + 0.005 * (1.0 - att))

    # safe binary entropy per element
    def h_vec(q):
        q = np.clip(q, 1e-12, 1.0 - 1e-12)
        return -q * np.log2(q) - (1.0 - q) * np.log2(1.0 - q)

    h = h_vec(qber)
    raw = (
        100.0 * 1e6 * att * (0.3 * (1.0 - np.minimum(1.0, np.abs(wl - 1550.0) / 200.0)))
    )
    kr = raw * np.maximum(0.0, 1.0 - 2.0 * h)
    kr *= np.maximum(0.0, 1.0 - 0.1 * np.abs(pw))
    return kr + np.random.normal(0, kr * 0.02).astype(X.dtype)


# ===========================================================================
# 1 -- QKDOptimizer
# ===========================================================================
print("\n" + "=" * 72)
print("SECTION 1: QKDOptimizer")
print("=" * 72)

# ---------- 1a: create for BB84 and E91 ----------
opt_bb84 = QKDOptimizer("BB84")
opt_e91 = QKDOptimizer("E91")
print("\n[1a] Created QKDOptimizer for protocols:")
print(f"     BB84 -- protocol_name={opt_bb84.protocol_name!r}")
print(f"     E91  -- protocol_name={opt_e91.protocol_name!r}")
print(f"     Sklearn available: {opt_bb84.sklearn_available}")

# Parameter space for channel optimisation
param_space = {
    "loss": (0.1, 0.5),
    "noise_level": (0.001, 0.1),
    "distance": (10.0, 150.0),
}

# ---------- 1b: Bayesian optimisation ----------
print("\n[1b] Bayesian optimisation -- 20 iterations")
print("     Objective: key_rate (MHz) -- maximize")
print(f"     Parameter space: {param_space}")
t0 = time.time()
bayes_result = opt_bb84.optimize_channel_parameters(
    param_space,
    qkd_key_rate_from_dict,
    num_iterations=20,
    method="bayesian",
)
t_bayes = time.time() - t0

print(f"     Time taken:           {t_bayes:.4f} s")
print(f"     Best params:          {bayes_result['best_parameters']}")
print(f"     Best obj value:       {bayes_result['best_objective_value']:.6e}")
print(
    f"     Objective history:    {[f'{v:.4e}' for v in bayes_result['objective_history']]}"
)
print(f"     History length:       {len(bayes_result['objective_history'])}")

# ---------- 1c: Genetic algorithm ----------
print("\n[1c] Genetic algorithm optimisation -- 20 iterations")
print("     Objective: key_rate -- maximize")
print("     GA params: pop_size=20, mut_rate=0.1, cross_rate=0.8, elitism=2")
t0 = time.time()
ga_result = opt_e91.optimize_channel_parameters(
    param_space,
    qkd_key_rate_from_dict,
    num_iterations=20,
    method="genetic",
)
t_ga = time.time() - t0

print(f"     Time taken:           {t_ga:.4f} s")
print(f"     Best params:          {ga_result['best_parameters']}")
print(f"     Best obj value:       {ga_result['best_objective_value']:.6e}")
print(
    f"     Final fitness scores: {[f'{v:.4e}' for v in ga_result['final_fitness_scores']]}"
)
best_ga_fit = max(ga_result["final_fitness_scores"])
print(f"     Best in final pop:    {best_ga_fit:.6e}")

# ---------- 1d: Neural optimisation (if sklearn or fallback) ----------
print("\n[1d] Neural network optimisation -- 20 iterations")
print("     Objective: key_rate -- maximize")
opt_nn = QKDOptimizer("BB84_nn")
t0 = time.time()
nn_result = opt_nn.optimize_channel_parameters(
    param_space,
    qkd_key_rate_from_dict,
    num_iterations=20,
    method="neural",
)
t_nn = time.time() - t0

print(f"     Time taken:           {t_nn:.4f} s")
print(f"     Best params:          {nn_result['best_parameters']}")
print(f"     Best obj value:       {nn_result['best_objective_value']:.6e}")
print(f"     History length:       {len(nn_result['objective_history'])}")

# ---------- 1e: Objective summary ----------
print("\n[1e] Objective function summary")
print("     All methods maximise key_rate = clock * att * eff * max(0, 1-2*h2(QBER))")
print("     att = 10^(-loss*dist/10), QBER ~ noise + 0.005*(1-att)")
print(f"     Bayesian best: {bayes_result['best_objective_value']:.4e}")
print(f"     Genetic  best: {ga_result['best_objective_value']:.4e}")
print(f"     Neural   best: {nn_result['best_objective_value']:.4e}")

# ---------------------------------------------------------------------------
# Also test QKDAnomalyDetector (bonus)
# ---------------------------------------------------------------------------
print("\n[1f] QKDAnomalyDetector (bonus)")
detector = QKDAnomalyDetector()
# Establish baseline
baseline = []
for _ in range(100):
    params = {k: np.random.uniform(*v) for k, v in param_space.items()}
    params["qber"] = params["noise_level"] + 0.01
    params["key_rate"] = qkd_key_rate_from_dict(params)
    baseline.append(params)
detector.establish_baseline(baseline)
print(f"     Baseline metrics: {list(detector.baseline_statistics.keys())}")
for k, v in detector.baseline_statistics.items():
    print(f"       {k}: mean={v['mean']:.4e}, std={v['std']:.4e}")
# Test anomaly
normal_metrics = {"loss": 0.2, "noise_level": 0.01, "qber": 0.02, "key_rate": 1e5}
anom = detector.detect_anomalies(normal_metrics)
print(f"     Normal sample anomalies: {anom}")
anom_metrics = {"loss": 5.0, "noise_level": 0.5, "qber": 0.4, "key_rate": -100}
anom2 = detector.detect_anomalies(anom_metrics)
print(f"     Anomalous sample anomalies: {anom2}")
report = detector.get_detection_report()
print(f"     Detection report total: {report['total_detections']}")
print(f"     Anomaly rates: {report['anomaly_rates']}")


# ===========================================================================
# 2 -- EfficientQKDPredictor
# ===========================================================================
print("\n" + "=" * 72)
print("SECTION 2: EfficientQKDPredictor")
print("=" * 72)

# ---------- 2a: create ----------
print("\n[2a] Creating EfficientQKDPredictor")
predictor = EfficientQKDPredictor(
    input_dim=5,
    max_memory_mb=128,
    enable_quantization=True,
    enable_pruning=True,
)
print(f"     Input dim:           {predictor.input_dim}")
print(f"     Max memory (MB):     {predictor.max_memory_mb}")
print(f"     Quantization:        {predictor.enable_quantization}")
print(f"     Pruning:             {predictor.enable_pruning}")
print(f"     Hidden layers:       {predictor.hidden_layers}")

# ---------- 2b: synthetic training data ----------
print("\n[2b] Generating synthetic QKD training data")
N_train = 2000
X_train = np.column_stack(
    [
        np.random.uniform(0.1, 0.5, N_train),  # loss (dB/km)
        np.random.uniform(0.001, 0.1, N_train),  # noise_level
        np.random.uniform(10, 150, N_train),  # distance (km)
        np.random.uniform(1300, 1700, N_train),  # wavelength (nm)
        np.random.uniform(-3, 3, N_train),  # power penalty factor
    ]
).astype(np.float32)
y_train = qkd_key_rate_vector(X_train).astype(np.float32)
print(f"     X shape: {X_train.shape}, y shape: {y_train.shape}")
print(
    f"     y range: [{y_train.min():.4e}, {y_train.max():.4e}], mean={y_train.mean():.4e}"
)

# ---------- 2c: train ----------
print("\n[2c] Training predictor (epochs=200, lr=0.01)")
t0 = time.time()
train_result = predictor.fit(
    X_train, y_train, epochs=200, learning_rate=0.01, batch_size=64
)
t_train = time.time() - t0
print(f"     Training time:       {t_train:.4f} s")
print(f"     Epochs trained:      {train_result['epochs_trained']}")
print(f"     Final train loss:    {train_result['final_train_loss']:.6e}")
print(f"     Best val loss:       {train_result['best_val_loss']:.6e}")

# R^2 on training set
if SKLEARN_AVAIL:
    y_pred_train = predictor.predict(X_train)
    r2 = r2_score(y_train, y_pred_train)
    print(f"     R^2 score (train):    {r2:.6f}")
else:
    y_pred_train = predictor.predict(X_train)
    ss_res = np.sum((y_train - y_pred_train) ** 2)
    ss_tot = np.sum((y_train - np.mean(y_train)) ** 2)
    r2_manual = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    print(f"     R^2 score (train):    {r2_manual:.6f} (manual calc)")

# ---------- 2d: test prediction on new inputs ----------
print("\n[2d] Test predictions on new inputs")
test_inputs = np.array(
    [
        [0.2, 0.01, 50.0, 1550.0, 0.0],  # ideal short-range
        [0.3, 0.02, 100.0, 1550.0, 0.0],  # medium
        [0.5, 0.05, 150.0, 1310.0, 1.0],  # long-range noisy
        [0.15, 0.005, 20.0, 1550.0, -0.5],  # near-perfect
        [0.4, 0.08, 130.0, 1700.0, 2.0],  # poor conditions
    ],
    dtype=np.float32,
)
for i, inp in enumerate(test_inputs):
    pred = predictor.predict(inp.reshape(1, -1))[0]
    true_val = qkd_key_rate_vector(inp.reshape(1, -1))[0]
    # crude confidence: variance of last 10 predictions
    # (simulated via small-noise Monte Carlo)
    noisy_preds = []
    for _ in range(30):
        noisy = predictor.predict(inp.reshape(1, -1))[0]
        noisy_preds.append(noisy)
    ci = 1.96 * np.std(noisy_preds)  # ~95% CI assuming normality
    err_pct = abs(pred - true_val) / max(abs(true_val), 1e-12) * 100
    print(
        f"     Input {i}: loss={inp[0]:.3f}, noise={inp[1]:.4f}, "
        f"dist={inp[2]:.0f}, wl={inp[3]:.0f}, pw={inp[4]:.1f}"
    )
    print(
        f"       Predicted: {pred:.4e}, True: {true_val:.4e}, "
        f"Error: {err_pct:.2f}%, CI(95%): +/-{ci:.4e}"
    )

# ---------- 2e: quantization test ----------
print("\n[2e] Quantization effect")
pred_q_on = EfficientQKDPredictor(5, max_memory_mb=128, enable_quantization=True)
pred_q_off = EfficientQKDPredictor(5, max_memory_mb=128, enable_quantization=False)
# train identically (same seed)
np.random.seed(123)
pred_q_on.fit(X_train, y_train, epochs=50, learning_rate=0.01, batch_size=64)
np.random.seed(123)
pred_q_off.fit(X_train, y_train, epochs=50, learning_rate=0.01, batch_size=64)
size_on = pred_q_on.get_model_size_bytes()
size_off = pred_q_off.get_model_size_bytes()
print(
    f"     Quant ON  -- hidden layers: {pred_q_on.hidden_layers},  model size: {size_on} bytes ({size_on / 1024:.2f} KB)"
)
print(
    f"     Quant OFF -- hidden layers: {pred_q_off.hidden_layers}, model size: {size_off} bytes ({size_off / 1024:.2f} KB)"
)
# R^2 comparison
if SKLEARN_AVAIL:
    r2_on = r2_score(y_train, pred_q_on.predict(X_train))
    r2_off = r2_score(y_train, pred_q_off.predict(X_train))
    print(f"     R^2 with quant ON:  {r2_on:.6f}")
    print(f"     R^2 with quant OFF: {r2_off:.6f}")
print(f"     Size ratio (OFF/ON): {size_off / max(size_on, 1):.2f}x")

# ---------- 2f: pruning test ----------
print("\n[2f] Pruning effect")
pred_prune_on = EfficientQKDPredictor(
    5, max_memory_mb=128, enable_pruning=True, pruning_threshold=0.01
)
pred_prune_off = EfficientQKDPredictor(5, max_memory_mb=128, enable_pruning=False)
np.random.seed(42)
pred_prune_on.fit(X_train, y_train, epochs=50, learning_rate=0.01, batch_size=64)
np.random.seed(42)
pred_prune_off.fit(X_train, y_train, epochs=50, learning_rate=0.01, batch_size=64)
sparsity_on = pred_prune_on.get_sparsity()
sparsity_off = pred_prune_off.get_sparsity()
print(f"     Prune ON  -- sparsity: {sparsity_on:.4f} ({sparsity_on * 100:.2f}% zeros)")
print(
    f"     Prune OFF -- sparsity: {sparsity_off:.4f} ({sparsity_off * 100:.2f}% zeros)"
)
size_prune_on = pred_prune_on.get_model_size_bytes()
size_prune_off = pred_prune_off.get_model_size_bytes()
print(f"     Model size (ON):  {size_prune_on} bytes")
print(f"     Model size (OFF): {size_prune_off} bytes")

# ---------- 2g: edge deployment ----------
print("\n[2g] Edge deployment simulation")
pred_edge = EfficientQKDPredictor(
    5, max_memory_mb=64, enable_quantization=True, enable_pruning=True
)
np.random.seed(42)
pred_edge.fit(X_train, y_train, epochs=50, learning_rate=0.01, batch_size=64)
# inference speed
N_infer = 1000
X_infer = np.random.randn(N_infer, 5).astype(np.float32)
t0 = time.time()
for _ in range(100):
    _ = pred_edge.predict(X_infer)
t_infer = (time.time() - t0) / 100
t_per_sample = t_infer / N_infer * 1e6  # microseconds per sample
print(f"     Hidden layers:   {pred_edge.hidden_layers}")
print(
    f"     Model size:      {pred_edge.get_model_size_bytes()} bytes "
    f"({pred_edge.get_model_size_bytes() / 1024:.2f} KB)"
)
print(f"     Num weights:     {sum(w.size for w in pred_edge.weights)}")
print(f"     Sparsity:        {pred_edge.get_sparsity():.4f}")
print(
    f"     Avg inference:   {t_infer:.6f} s for {N_infer} samples "
    f"({t_per_sample:.3f} us/sample)"
)

# ---------- 2h: memory tradeoff ----------
print("\n[2h] Accuracy vs memory tradeoff")
memory_configs = [64, 128, 256]
mem_results = []
for mem in memory_configs:
    p = EfficientQKDPredictor(
        5, max_memory_mb=mem, enable_quantization=True, enable_pruning=False
    )
    np.random.seed(42)
    t0 = time.time()
    res = p.fit(X_train, y_train, epochs=100, learning_rate=0.01, batch_size=64)
    t_fit = time.time() - t0
    yp = p.predict(X_train)
    if SKLEARN_AVAIL:
        r2 = r2_score(y_train, yp)
    else:
        ss_res = np.sum((y_train - yp) ** 2)
        ss_tot = np.sum((y_train - np.mean(y_train)) ** 2)
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    mem_results.append(
        {
            "max_mb": mem,
            "hidden": p.hidden_layers,
            "size_bytes": p.get_model_size_bytes(),
            "size_kb": p.get_model_size_bytes() / 1024,
            "r2": r2,
            "train_time": t_fit,
            "epochs": res["epochs_trained"],
            "final_loss": res["final_train_loss"],
        }
    )
    print(
        f"     Memory={mem:>3d} MB  hidden={str(p.hidden_layers):<15s}  "
        f"size={p.get_model_size_bytes() / 1024:>8.2f} KB  "
        f"R^2={r2:.6f}  time={t_fit:.3f}s  epochs={res['epochs_trained']}"
    )


# ===========================================================================
# 3 -- AdaptiveModelSelector
# ===========================================================================
print("\n" + "=" * 72)
print("SECTION 3: AdaptiveModelSelector")
print("=" * 72)

print("\n[3a] Available memory detection")
avail_mb = AdaptiveModelSelector.get_available_memory_mb()
print(f"     Available memory (detected): {avail_mb} MB")

print("\n[3b] Create optimal predictor")
opt_pred = AdaptiveModelSelector.create_optimal_predictor(input_dim=5)
print(f"     Hidden layers:        {opt_pred.hidden_layers}")
print(f"     Max memory (MB):      {opt_pred.max_memory_mb}")
print(f"     Quantization:         {opt_pred.enable_quantization}")
print(f"     Pruning:              {opt_pred.enable_pruning}")
print(
    f"     Model size:           {opt_pred.get_model_size_bytes()} bytes "
    f"({opt_pred.get_model_size_bytes() / 1024:.2f} KB)"
)

# Train the optimally-created predictor
print("\n[3c] Train optimally-created predictor")
np.random.seed(42)
t0 = time.time()
opt_res = opt_pred.fit(X_train, y_train, epochs=100, learning_rate=0.01, batch_size=64)
t_opt = time.time() - t0
if SKLEARN_AVAIL:
    r2_opt = r2_score(y_train, opt_pred.predict(X_train))
else:
    yp = opt_pred.predict(X_train)
    ss_res = np.sum((y_train - yp) ** 2)
    ss_tot = np.sum((y_train - np.mean(y_train)) ** 2)
    r2_opt = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
print(f"     Training time:        {t_opt:.3f}s")
print(f"     Epochs trained:       {opt_res['epochs_trained']}")
print(f"     Final train loss:     {opt_res['final_train_loss']:.6e}")
print(f"     R^2 score:             {r2_opt:.6f}")

# Test with different dataset sizes
print("\n[3d] Scaling with dataset size")
for n_samples in [100, 500, 1000]:
    X_sub = X_train[:n_samples]
    y_sub = y_train[:n_samples]
    p = EfficientQKDPredictor(
        5, max_memory_mb=128, enable_quantization=True, enable_pruning=False
    )
    np.random.seed(42)
    t0 = time.time()
    r = p.fit(
        X_sub, y_sub, epochs=100, learning_rate=0.01, batch_size=min(64, n_samples)
    )
    t_fit = time.time() - t0
    yp = p.predict(X_sub)
    if SKLEARN_AVAIL:
        r2 = r2_score(y_sub, yp)
    else:
        ss_res = np.sum((y_sub - yp) ** 2)
        ss_tot = np.sum((y_sub - np.mean(y_sub)) ** 2)
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    print(
        f"     n={n_samples:>4d}  epochs={r['epochs_trained']:>3d}  "
        f"loss={r['final_train_loss']:.4e}  R^2={r2:.6f}  time={t_fit:.3f}s"
    )


# ===========================================================================
# 4 -- KnowledgeDistillation
# ===========================================================================
print("\n" + "=" * 72)
print("SECTION 4: KnowledgeDistillation")
print("=" * 72)

# ----- Build teacher (3 hidden layers) -----
print("\n[4a] Creating teacher (3 hidden layers) and student (1 hidden layer)")
teacher = EfficientQKDPredictor(
    5,
    max_memory_mb=512,
    enable_quantization=False,
    enable_pruning=False,
)
# Force 3 hidden layers [64, 32, 16]
teacher.hidden_layers = [64, 32, 16]
teacher._initialize_weights()
print(f"     Teacher hidden layers: {teacher.hidden_layers}")
print(
    f"     Teacher parameters: {sum(w.size for w in teacher.weights) + sum(b.size for b in teacher.biases)}"
)

student_scratch = EfficientQKDPredictor(
    5,
    max_memory_mb=64,
    enable_quantization=True,
    enable_pruning=False,
)
# Force 1 hidden layer [16]
student_scratch.hidden_layers = [16]
student_scratch._initialize_weights()
print(f"     Student hidden layers: {student_scratch.hidden_layers}")
print(
    f"     Student parameters: {sum(w.size for w in student_scratch.weights) + sum(b.size for b in student_scratch.biases)}"
)

# Train teacher
print("\n[4b] Training teacher (200 epochs)")
np.random.seed(42)
t0 = time.time()
teacher_res = teacher.fit(
    X_train, y_train, epochs=200, learning_rate=0.01, batch_size=64
)
t_teacher = time.time() - t0
teacher_preds = teacher.predict(X_train)
if SKLEARN_AVAIL:
    teacher_r2 = r2_score(y_train, teacher_preds)
else:
    ss_res = np.sum((y_train - teacher_preds) ** 2)
    ss_tot = np.sum((y_train - np.mean(y_train)) ** 2)
    teacher_r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
print(f"     Training time:       {t_teacher:.3f}s")
print(f"     Epochs trained:      {teacher_res['epochs_trained']}")
print(f"     Final train loss:    {teacher_res['final_train_loss']:.6e}")
print(f"     R^2 (teacher):        {teacher_r2:.6f}")

# Train student from scratch (without distillation)
print("\n[4c] Training student from scratch (200 epochs)")
np.random.seed(42)
t0 = time.time()
scratch_res = student_scratch.fit(
    X_train, y_train, epochs=200, learning_rate=0.01, batch_size=64
)
t_scratch = time.time() - t0
scratch_preds = student_scratch.predict(X_train)
if SKLEARN_AVAIL:
    scratch_r2 = r2_score(y_train, scratch_preds)
else:
    ss_res = np.sum((y_train - scratch_preds) ** 2)
    ss_tot = np.sum((y_train - np.mean(y_train)) ** 2)
    scratch_r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
print(f"     Training time:       {t_scratch:.3f}s")
print(f"     Epochs trained:      {scratch_res['epochs_trained']}")
print(f"     Final train loss:    {scratch_res['final_train_loss']:.6e}")
print(f"     R^2 (student scratch):{scratch_r2:.6f}")

# Knowledge distillation with default T=2, alpha=0.5
print("\n[4d] Knowledge distillation (T=2.0, alpha=0.5, 200 epochs)")
student_distilled = EfficientQKDPredictor(
    5,
    max_memory_mb=64,
    enable_quantization=True,
    enable_pruning=False,
)
student_distilled.hidden_layers = [16]
student_distilled._initialize_weights()

distiller = KnowledgeDistillation(
    teacher_predict=teacher.predict, temperature=2.0, alpha=0.5
)
np.random.seed(42)
t0 = time.time()
distill_res = distiller.distill(
    student_distilled,
    X_train,
    y_train,
    epochs=200,
    learning_rate=0.01,
    batch_size=64,
)
t_distill = time.time() - t0
distilled_preds = student_distilled.predict(X_train)
if SKLEARN_AVAIL:
    distilled_r2 = r2_score(y_train, distilled_preds)
else:
    ss_res = np.sum((y_train - distilled_preds) ** 2)
    ss_tot = np.sum((y_train - np.mean(y_train)) ** 2)
    distilled_r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
print(f"     Distillation time:   {t_distill:.3f}s")
print(f"     Epochs trained:      {distill_res['epochs_trained']}")
print(f"     Final train loss:    {distill_res['final_train_loss']:.6e}")
print(f"     R^2 (distilled):      {distilled_r2:.6f}")
print(f"     Improvement vs scratch: {distilled_r2 - scratch_r2:+.6f}")

# ---------- Temperature sweep ----------
print("\n[4e] Temperature sweep (T=1, 2, 5, 10)")
temperatures = [1.0, 2.0, 5.0, 10.0]
temp_results = []
for T in temperatures:
    s = EfficientQKDPredictor(
        5, max_memory_mb=64, enable_quantization=True, enable_pruning=False
    )
    s.hidden_layers = [16]
    s._initialize_weights()
    d = KnowledgeDistillation(teacher_predict=teacher.predict, temperature=T, alpha=0.5)
    np.random.seed(42)
    r = d.distill(s, X_train, y_train, epochs=200, learning_rate=0.01, batch_size=64)
    yp = s.predict(X_train)
    if SKLEARN_AVAIL:
        r2 = r2_score(y_train, yp)
    else:
        ss_res = np.sum((y_train - yp) ** 2)
        ss_tot = np.sum((y_train - np.mean(y_train)) ** 2)
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    temp_results.append({"T": T, "R^2": r2, "final_loss": r["final_train_loss"]})
    print(f"     T={T:>4.1f}  R^2={r2:.6f}  final_loss={r['final_train_loss']:.6e}")

# ---------- Model size comparison ----------
print("\n[4f] Model size comparison")
t_params = sum(w.size for w in teacher.weights) + sum(b.size for b in teacher.biases)
t_bytes = teacher.get_model_size_bytes()
s_params = sum(w.size for w in student_scratch.weights) + sum(
    b.size for b in student_scratch.biases
)
s_bytes = student_scratch.get_model_size_bytes()
print(f"     Teacher: {t_params} params, {t_bytes} bytes ({t_bytes / 1024:.2f} KB)")
print(f"     Student: {s_params} params, {s_bytes} bytes ({s_bytes / 1024:.2f} KB)")
print(
    f"     Reduction: {(1 - s_params / t_params) * 100:.1f}% params, "
    f"{(1 - s_bytes / t_bytes) * 100:.1f}% memory"
)


# ===========================================================================
# 5 -- EfficientModels (architecture enumeration)
# ===========================================================================
print("\n" + "=" * 72)
print("SECTION 5: EfficientModels -- Architecture Analysis")
print("=" * 72)

print("\n[5a] Architecture scale with resource constraints")
for mem in [32, 64, 128, 256, 512]:
    for quant in [True, False]:
        p = EfficientQKDPredictor(
            5, max_memory_mb=mem, enable_quantization=quant, enable_pruning=False
        )
        n_params = sum(w.size for w in p.weights) + sum(b.size for b in p.biases)
        size_kb = p.get_model_size_bytes() / 1024
        print(
            f"     mem={mem:>3d}MB  quant={str(quant):>5s}  hidden={str(p.hidden_layers):<20s}  "
            f"params={n_params:>5d}  size={size_kb:>8.2f}KB"
        )

# Full pipeline test: create, train, evaluate
print("\n[5b] Multi-architecture benchmark (100 epochs each)")
arch_results = []
for mem in [64, 128, 256]:
    p = EfficientQKDPredictor(
        5, max_memory_mb=mem, enable_quantization=True, enable_pruning=False
    )
    np.random.seed(42)
    t0 = time.time()
    r = p.fit(X_train, y_train, epochs=100, learning_rate=0.01, batch_size=64)
    t_fit = time.time() - t0
    # inference speed
    X_inf = np.random.randn(500, 5).astype(np.float32)
    t_inf0 = time.time()
    for _ in range(20):
        _ = p.predict(X_inf)
    t_inf = (time.time() - t_inf0) / 20
    yp = p.predict(X_train)
    if SKLEARN_AVAIL:
        r2 = r2_score(y_train, yp)
    else:
        ss_res = np.sum((y_train - yp) ** 2)
        ss_tot = np.sum((y_train - np.mean(y_train)) ** 2)
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    arch_results.append(
        {
            "mem": mem,
            "hidden": p.hidden_layers,
            "params": sum(w.size for w in p.weights),
            "size_kb": p.get_model_size_bytes() / 1024,
            "r2": r2,
            "train_time": t_fit,
            "infer_time_500": t_inf,
        }
    )
    print(
        f"     mem={mem:>3d}MB  hidden={str(p.hidden_layers):<20s}  "
        f"params={sum(w.size for w in p.weights):>5d}  "
        f"size={p.get_model_size_bytes() / 1024:>7.2f}KB  "
        f"R^2={r2:.6f}  train={t_fit:.3f}s  "
        f"infer_500={t_inf * 1e3:.3f}ms"
    )


# ===========================================================================
# SUMMARY
# ===========================================================================
print("\n" + "=" * 72)
print("  TEST SUMMARY")
print("=" * 72)
print(f"""
1. QKDOptimizer
   Bayesian  best: {bayes_result["best_objective_value"]:.4e}  ({t_bayes:.3f}s)
   Genetic   best: {ga_result["best_objective_value"]:.4e}  ({t_ga:.3f}s)
   Neural    best: {nn_result["best_objective_value"]:.4e}  ({t_nn:.3f}s)
   AnomalyDetector: {report["total_detections"]:.0f} detections, rates={report["anomaly_rates"]}

2. EfficientQKDPredictor
   Train loss:  {train_result["final_train_loss"]:.6e}
   R^2:          {r2 if SKLEARN_AVAIL else r2_manual:.6f}
   Model size:  {predictor.get_model_size_bytes() / 1024:.2f} KB
   Sparsity:    {predictor.get_sparsity():.4f}

3. AdaptiveModelSelector
   Memory:     {avail_mb} MB
   Opt config: hidden={opt_pred.hidden_layers}, mem={opt_pred.max_memory_mb}MB, quant={opt_pred.enable_quantization}
   R^2:         {r2_opt:.6f}

4. KnowledgeDistillation
   Teacher R^2:        {teacher_r2:.6f}
   Student scratch R^2:{scratch_r2:.6f}
   Student distilled  R^2: {distilled_r2:.6f}   (improv: {distilled_r2 - scratch_r2:+.6f})
   Temp sweep: {[(t["T"], round(t["R^2"], 6)) for t in temp_results]}

5. EfficientModels
   Archs tested: {len(arch_results)} memory levels
   Best R^2: {max(a["r2"] for a in arch_results):.6f}  @ {max(a["mem"] for a in arch_results)}MB
""")
print("=" * 72)
print("  ALL TESTS COMPLETE")
print("=" * 72)
