"""
Calibrate severity median accounting for actual CAT population mix.
FL=28%, TX=27%, CA=17%, NY=13%, IL=8%, MI=7%
CAT applies only to rows where hazard>0.5 (for FL/CA) or always (TX)
"""
import numpy as np
np.random.seed(42)
N = 100_000
earned = 2377
avg_ded = 1100
freq = 0.13  # target claim frequency (what the generator actually produces)

# Rough CAT fractions:
# FL: 28% of policies, only Jul-Sep = 3/12 of the time, only if hazard>0.5 (beta(2,1.5) → P(>0.5)≈60%)
# TX: 27% of policies, always CAT with lambda=0.14 (overrides base ~0.12)
# CA: 17% of policies, only Aug-Oct = 3/12, only if hazard>0.5 (beta(2,2) → P(>0.5)≈50%)
# NY/IL/MI: no CAT override

# Effective CAT severity multiplier for the population:
# FL CAT fraction: 0.28 * (3/12) * 0.60 → 0.042 of rows → sev_mult 3.0
# TX CAT fraction: 0.27 * 1.0 → 0.27 of rows → sev_mult 1.8
# CA CAT fraction: 0.17 * (3/12) * 0.50 → 0.021 of rows → sev_mult 2.5
# Non-CAT fraction: 1 - 0.042 - 0.27 - 0.021 = 0.667

pop_weights = [0.042, 0.27, 0.021, 0.667]
sev_mults   = [3.0,   1.8,  2.5,   1.0  ]

weighted_mult = sum(w * m for w, m in zip(pop_weights, sev_mults))
print(f"Weighted CAT severity multiplier: {weighted_mult:.2f}")
# This gives the effective average severity multiplier across the population

for sev_med in [1500, 2000, 2500, 3000, 3500, 4000]:
    for sig in [0.8, 0.9, 1.0, 1.1]:
        total_loss = 0
        for w, mult in zip(pop_weights, sev_mults):
            n = int(N * w * freq)
            if n < 1:
                n = 1
            sev = np.random.lognormal(np.log(sev_med), sig, n) * mult
            net = np.maximum(0, sev - avg_ded)
            total_loss += net.mean() * freq * w

        net_lr = total_loss / earned
        marker = "***" if 0.55 <= net_lr <= 0.75 else "   "
        print(f"{marker} med={sev_med} sig={sig}: net_LR={net_lr*100:.1f}%")
