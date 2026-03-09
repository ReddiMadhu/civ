import numpy as np
from scipy import stats

np.random.seed(42)
n = 100_000

# Current credit mix: [INTRNL06=55%, ASSIST01=15%, ASSIST03=30%]
# Find minimum overall Delq rate to achieve r >= 0.40

for delq_rate in [0.05, 0.07, 0.08, 0.10, 0.12, 0.15, 0.20]:
    credit = np.random.choice([1, 2, 3], size=n, p=[0.55, 0.15, 0.30])
    idx = np.argsort(credit + np.random.uniform(0, 0.01, n))
    delq = np.zeros(n, dtype=bool)
    n_delq = int(n * delq_rate)
    delq[idx[-n_delq:]] = True
    r = stats.pearsonr(delq.astype(float), credit.astype(float))[0]
    print(f"Delq={delq_rate:.0%}: r={r:.4f}")
