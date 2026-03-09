"""
Property Insurance CLV Synthetic Dataset Generator
Master Prompt v6.0 — Actuarial Gold Standard
Generates 50,000 rows x 38 columns deterministically.
"""

import numpy as np
import pandas as pd
from faker import Faker

# ---------------------------------------------------------------------------
# 0. Seed & constants
# ---------------------------------------------------------------------------
SEED = 42
N = 50_000
np.random.seed(SEED)
fake = Faker("en_US")
Faker.seed(SEED)

DISCOUNT_RATE_CLV = 0.08  # CLV formula discount rate (informational)

# ---------------------------------------------------------------------------
# 1. Lookup / config tables
# ---------------------------------------------------------------------------

# --- States ---
# code, weight, risk_factor, beta_a, beta_b, cat_months (None=all), cat_lambda, cat_sev_mult, cat_hazard_threshold
STATE_CONFIG = {
    "12": dict(weight=0.28, risk_factor=1.45, beta_a=2.0, beta_b=1.5, cat_months={7,8,9}, cat_lambda=0.13, cat_sev_mult=3.0, cat_hazard_threshold=0.50),
    "48": dict(weight=0.27, risk_factor=1.30, beta_a=1.5, beta_b=2.0, cat_months=None,    cat_lambda=0.14, cat_sev_mult=1.8, cat_hazard_threshold=None),
    "06": dict(weight=0.17, risk_factor=1.35, beta_a=2.0, beta_b=2.0, cat_months={8,9,10},cat_lambda=0.18, cat_sev_mult=2.5, cat_hazard_threshold=0.50),
    "36": dict(weight=0.13, risk_factor=1.15, beta_a=1.0, beta_b=3.0, cat_months=None,    cat_lambda=None, cat_sev_mult=1.0, cat_hazard_threshold=None),
    "18": dict(weight=0.08, risk_factor=1.10, beta_a=1.0, beta_b=4.0, cat_months=None,    cat_lambda=None, cat_sev_mult=1.0, cat_hazard_threshold=None),
    "26": dict(weight=0.07, risk_factor=1.05, beta_a=1.0, beta_b=4.0, cat_months=None,    cat_lambda=None, cat_sev_mult=1.0, cat_hazard_threshold=None),
}

# --- ZIP codes per state (representative sample, all real ZIPs) ---
STATE_ZIPS = {
    "12": ["33101","33125","33139","33156","33301","33401","33602","33701","32801","34201",
           "33705","32901","33004","32003","33060","32084","33458","33629","33980","32205"],
    "48": ["77001","77002","77019","77494","75201","75202","75215","78201","78202","78701",
           "78702","79901","79902","77380","77845","76101","76102","77840","78201","75063"],
    "06": ["90001","90210","94102","94103","92101","92037","95814","95816","91101","91201",
           "90401","94501","93101","93001","91301","90802","94601","95008","92618","93311"],
    "36": ["10001","10002","10007","10019","10036","11201","11215","11354","12203","13202",
           "10304","11530","10701","11901","14201","14604","12601","11720","10950","10583"],
    "18": ["60601","60602","60614","60615","60626","60637","60647","61820","62701","62901",
           "60201","60301","60402","60510","61265","60901","61101","62220","60901","61401"],
    "26": ["48201","48202","48301","48304","49503","49505","48103","48104","48823","48912",
           "49001","49002","48430","48640","49601","48858","48602","48503","49120","48198"],
}

# --- Property types ---
ITEM_TYPE_WEIGHTS = [0.65, 0.18, 0.10, 0.07]
ITEM_TYPE_CODES   = [18, 19, 7, 20]
# coverage multiplier relative to HO3 benchmark
ITEM_TYPE_COV_MULT = {18: 1.00, 19: 0.90, 7: 0.75, 20: 1.10}

# --- Construction ---
# code, multiplier, cost_per_sqft
CONSTRUCTION = {
    1: dict(mult=1.00, cpf=150),
    2: dict(mult=1.10, cpf=180),
    4: dict(mult=1.20, cpf=230),
    6: dict(mult=1.30, cpf=325),
}
CONSTRUCTION_CODES   = [1, 2, 4, 6]
CONSTRUCTION_WEIGHTS = [0.55, 0.20, 0.15, 0.10]

# --- Roof ---
ROOF_CODES   = [1, 2, 3, 5]
ROOF_WEIGHTS = [0.55, 0.20, 0.15, 0.10]
ROOF_COV_MULT         = {1: 1.00, 2: 1.20, 3: 1.00, 5: 1.25}
ROOF_STORM_FREQ_MULT  = {1: 1.00, 2: 1.00, 3: 0.70, 5: 1.00}

# --- Coverage subtype ---
SUBTYPE_CODES   = [2511, 2500, 2537]
SUBTYPE_WEIGHTS = [0.50, 0.35, 0.15]
SUBTYPE_MULT    = {2511: 1.15, 2500: 1.00, 2537: 0.85}
# Deductibles: {credit_tier: deductible}
DEDUCTIBLE = {
    2500: {"INTRNL06": 1000, "ASSIST01": 1250, "ASSIST03": 2000},
    2511: {"INTRNL06":  750, "ASSIST01": 1000, "ASSIST03": 1500},
    2537: {"INTRNL06":  500, "ASSIST01":  750, "ASSIST03": 1000},
}

# --- Credit tiers ---
CREDIT_CODES     = ["INTRNL06", "ASSIST01", "ASSIST03"]
CREDIT_WEIGHTS   = [0.55, 0.15, 0.30]
CREDIT_DELQ_RATE = {"INTRNL06": 0.005, "ASSIST01": 0.030, "ASSIST03": 0.120}
# merit skew: (mu adjustment, sigma scale)
CREDIT_MERIT_SKEW = {"INTRNL06": (2.0, 0.8), "ASSIST01": (0.0, 1.0), "ASSIST03": (-2.0, 0.8)}

# --- Agent channel ---
CHANNEL_CODES       = ["Independent", "Captive", "Direct"]
CHANNEL_WEIGHTS     = [0.60, 0.25, 0.15]
CHANNEL_COMMISSION  = {"Independent": 0.15, "Captive": 0.10, "Direct": 0.08}

# --- Tenure ---
TENURE_CODES   = ["New", "Existing", "Recurring"]
TENURE_WEIGHTS = [0.35, 0.40, 0.25]
TENURE_RENEWAL_PROB = {"New": 0.70, "Existing": 0.85, "Recurring": 0.95}

# --- Policy term ---
TERM_CODES   = [12, 6]
TERM_WEIGHTS = [0.70, 0.30]

# --- Inflation ---
INFLATION = {
    2022: dict(premium=1.000, coverage=1.000, severity=1.000),
    2023: dict(premium=1.072, coverage=1.050, severity=1.045),
    2024: dict(premium=1.167, coverage=1.115, severity=1.106),
    2025: dict(premium=1.227, coverage=1.154, severity=1.141),
}

# ---------------------------------------------------------------------------
# 2. Helper: discrete weighted choice (vectorised)
# ---------------------------------------------------------------------------
def wchoice(codes, weights, size):
    weights = np.array(weights, dtype=float)
    weights /= weights.sum()
    idx = np.random.choice(len(codes), size=size, p=weights)
    return np.array(codes)[idx]

# ---------------------------------------------------------------------------
# 3. Generate arrays
# ---------------------------------------------------------------------------

# --- 3a. Policy IDs ---
policy_ids = np.array([f"HA{i:08d}" for i in range(1, N + 1)])

# --- 3b. Effective dates ---
start_ord    = pd.Timestamp("2022-01-01").toordinal()
end_ord      = pd.Timestamp("2025-12-31").toordinal()
eff_ordinals = np.random.randint(start_ord, end_ord + 1, size=N)
eff_dates_pd = pd.DatetimeIndex([pd.Timestamp.fromordinal(int(o)) for o in eff_ordinals])

year_arr  = eff_dates_pd.year.to_numpy()
month_arr = eff_dates_pd.month.to_numpy()
accounting_month = pd.array([f"{y}-{m:02d}" for y, m in zip(year_arr, month_arr)], dtype="object")

# --- 3c. State & ZIP ---
state_codes   = list(STATE_CONFIG.keys())
state_weights = [STATE_CONFIG[c]["weight"] for c in state_codes]
state_arr     = wchoice(state_codes, state_weights, N).astype(str)

zip_arr = np.array([
    STATE_ZIPS[s][np.random.randint(0, len(STATE_ZIPS[s]))]
    for s in state_arr
])

# Random county cluster 100-2000
county_arr = np.random.randint(100, 2001, size=N)

# --- 3d. Hazard Score ---
hazard_arr = np.zeros(N)
for sc in state_codes:
    mask = (state_arr == sc)
    cfg  = STATE_CONFIG[sc]
    hazard_arr[mask] = np.random.beta(cfg["beta_a"], cfg["beta_b"], mask.sum())
hazard_arr = np.clip(hazard_arr, 0.0, 1.0).round(2)

# --- 3e. Property type ---
item_type_arr = wchoice(ITEM_TYPE_CODES, ITEM_TYPE_WEIGHTS, N)
cov_mult_item = np.array([ITEM_TYPE_COV_MULT[c] for c in item_type_arr])

# --- 3f. Coverage subtype ---
subtype_arr  = wchoice(SUBTYPE_CODES, SUBTYPE_WEIGHTS, N)
subtype_mult = np.array([SUBTYPE_MULT[c] for c in subtype_arr])

# --- 3g. Construction ---
const_arr = wchoice(CONSTRUCTION_CODES, CONSTRUCTION_WEIGHTS, N)
const_mult = np.array([CONSTRUCTION[c]["mult"] for c in const_arr])
cost_per_sqft = np.array([CONSTRUCTION[c]["cpf"] for c in const_arr], dtype=float)

# --- 3h. Roof ---
roof_arr = wchoice(ROOF_CODES, ROOF_WEIGHTS, N)
roof_cov_mult        = np.array([ROOF_COV_MULT[r] for r in roof_arr])
roof_storm_freq_mult = np.array([ROOF_STORM_FREQ_MULT[r] for r in roof_arr])

# --- 3i. Property dimensions ---
sqft_arr    = np.clip(np.random.normal(2200, 700, N).round(0), 800, 6000).astype(int)
story_arr   = np.random.choice([1, 2, 3], size=N, p=[0.55, 0.35, 0.10])
home_age_arr = np.clip(np.random.normal(32, 18, N).round(0), 1, 90).astype(int)

# --- 3j. Seasonal ---
seasonal_arr = np.random.binomial(1, 0.08, N).astype(bool)

# --- 3k. Policyholder age ---
age_arr = np.clip(np.random.normal(47, 12, N).round(0), 21, 85).astype(int)

# --- 3l. Credit tier ---
credit_arr = wchoice(CREDIT_CODES, CREDIT_WEIGHTS, N)

# --- 3m. Merit score (correlated with credit) ---
# Strengthened correlation: MeritPoint <-> ClaimFreq (-0.30 to -0.40)
merit_mu  = np.where(credit_arr == "INTRNL06", 9.0,
            np.where(credit_arr == "ASSIST03", 2.0, 5.0))
merit_sig = np.where(credit_arr == "INTRNL06", 0.5,
            np.where(credit_arr == "ASSIST03", 0.5, 1.0))
merit_arr = np.clip(np.round(np.random.normal(merit_mu, merit_sig)), 1, 10).astype(int)

# --- 3n. Mortgage flag ---
p_mortgage = np.where(age_arr <= 45, 0.75, np.where(age_arr <= 60, 0.50, 0.20))
mortgage_arr = np.random.binomial(1, p_mortgage).astype(bool)

# --- 3o. Agent channel & tenure ---
channel_arr = wchoice(CHANNEL_CODES, CHANNEL_WEIGHTS, N)
tenure_arr  = wchoice(TENURE_CODES,  TENURE_WEIGHTS,  N)

# Multi-product discount
multi_discount_arr = np.random.binomial(1, 0.35, N).astype(bool)

# --- 3p. Policy term & exposure ---
term_arr = wchoice(TERM_CODES, TERM_WEIGHTS, N)
# Days active: assume full term for simplicity (policy in-force)
days_active = np.where(term_arr == 12, 365, 182)
earned_exp_arr  = (days_active / 365.0).round(4)
written_exp_arr = (term_arr / 12.0).round(4)

# ---------------------------------------------------------------------------
# 4. Inflation lookup arrays
# ---------------------------------------------------------------------------
infl_prem = np.array([INFLATION[y]["premium"]  for y in year_arr])
infl_cov  = np.array([INFLATION[y]["coverage"] for y in year_arr])
infl_sev  = np.array([INFLATION[y]["severity"] for y in year_arr])

# ---------------------------------------------------------------------------
# 5. Premium calculation
# ---------------------------------------------------------------------------
state_risk = np.array([STATE_CONFIG[s]["risk_factor"] for s in state_arr])
story_adj_rate = 0.75 * (1 + 0.05 * (story_arr - 1))

# SqFt <-> Premium target: 0.65-0.75 (was ~0.825). Increase independence/noise.
noise = np.random.lognormal(0, 0.28, N) 
dwp_arr = (
    sqft_arr * 0.88 * story_adj_rate
    * cov_mult_item
    * const_mult
    * state_risk
    * infl_prem
    *(1.0 + (hazard_arr * 0.15)) # slight hazard pricing
    * noise
).round(2)

# Derived financials
comm_rate_arr = np.array([CHANNEL_COMMISSION[c] for c in channel_arr])
earned_prem   = (0.925 * dwp_arr).round(2)
tax_arr        = (0.045 * dwp_arr).round(2)
commission_arr = (dwp_arr * comm_rate_arr).round(2)
admin_arr      = (0.03 * dwp_arr + 50.0).round(2)

# ---------------------------------------------------------------------------
# 6. Coverage limit
# ---------------------------------------------------------------------------
# Construction <-> CovLimit target: 0.50-0.60 (was ~0.732). Add noise to decouple.
limit_noise = np.random.lognormal(0, 0.20, N)
raw_limit = (
    sqft_arr * cost_per_sqft
    * const_mult
    * roof_cov_mult
    * subtype_mult
    * infl_cov
    * limit_noise
).round(2)

# Hard constraint 1: limit > DWP
raw_limit = np.maximum(raw_limit, dwp_arr * 1.05)

# Hard constraint 2: mortgage → limit ≥ 80% replacement value
replacement_value = sqft_arr * cost_per_sqft
raw_limit = np.where(mortgage_arr, np.maximum(raw_limit, 0.80 * replacement_value), raw_limit)
coverage_limit_arr = raw_limit.round(2)

# ---------------------------------------------------------------------------
# 7. Deductible per row
# ---------------------------------------------------------------------------
deductible_arr = np.array([
    DEDUCTIBLE[int(st)][cr]
    for st, cr in zip(subtype_arr, credit_arr)
], dtype=float)

# ---------------------------------------------------------------------------
# 8. Claims model — frequency-severity coupled
# ---------------------------------------------------------------------------

# Merit modifier - much stronger to hit -0.30 target correlation
merit_mod = np.where(merit_arr <= 3, 2.50,
            np.where(merit_arr <= 6, 1.00, 0.35))

# HomeAge <-> GrossLoss connection via freq
home_age_mod = 1.0 + (home_age_arr / 45.0)**1.5

# Story modifier
story_mod = 1 + 0.05 * (story_arr - 1)

# Seasonal modifier
seasonal_mod = np.where(seasonal_arr, 1.03, 1.00)

# Roof modifier (storm frequency)
roof_freq_mod = roof_storm_freq_mult

# Hazard modifier - much stronger to hit >0.35 correlation
hazard_mod = 1.0 + (hazard_arr * 3.5)

# State <-> ClaimFreq - force state variations larger
state_risk = np.array([STATE_CONFIG[s]["risk_factor"] for s in state_arr])
state_mod = (state_risk - 1.0) * 2.5 + 1.0

# Base lambda adjusted to maintain ~13% total freq
lambda_base = (
    0.02
    * merit_mod
    * home_age_mod
    * story_mod
    * seasonal_mod
    * roof_freq_mod
    * hazard_mod
    * state_mod
)

# CAT override
cat_lambda_arr    = lambda_base.copy()
cat_sev_mult_arr  = np.ones(N)

for sc in state_codes:
    cfg = STATE_CONFIG[sc]
    if cfg["cat_lambda"] is None:
        continue
    smask = (state_arr == sc)
    if cfg["cat_months"] is not None:
        mmask = np.isin(month_arr, list(cfg["cat_months"]))
        cmask = smask & mmask
    else:
        cmask = smask

    if cfg["cat_hazard_threshold"] is not None:
        cmask = cmask & (hazard_arr > cfg["cat_hazard_threshold"])

    cat_lambda_arr[cmask]   = cfg["cat_lambda"]
    cat_sev_mult_arr[cmask] = cfg["cat_sev_mult"]

# Poisson claim count
claim_count_arr = np.random.poisson(cat_lambda_arr).astype(int)

# Lognormal severity per claim → coupled gross loss
# median=$6,000 sigma=1.0 → E[severity] = exp(log(6000)+0.5) ≈ $9,934
# At 12% freq: E[gross_loss/policy] ≈ 0.12 * 9934 ≈ $1,192
# After avg $1,125 deductible: net ≈ $1,000; earned_prem ~$2,380 → LR ≈ 65%
gross_loss_arr = np.zeros(N)
unique_counts = np.unique(claim_count_arr[claim_count_arr > 0])
for c in unique_counts:
    mask = (claim_count_arr == c)
    n_pol = mask.sum()
    
    # Scale median slightly by home age to help HomeAge <-> GrossLoss
    age_mult_sev = 1.0 + (home_age_arr[mask] / 80.0)
    
    # Calibration to >60% net LR
    # broadcast age_mult_sev to (n_pol, 1)
    mu_val = np.log(3600 * age_mult_sev)[:, np.newaxis]
    sev = np.random.lognormal(mu_val, 0.90, (n_pol, c))
    sev *= (infl_sev[mask] * cat_sev_mult_arr[mask])[:, np.newaxis]
    gross_loss_arr[mask] = sev.sum(axis=1)

gross_loss_arr = gross_loss_arr.round(2)

# Net loss
net_loss_arr = np.maximum(0, gross_loss_arr - deductible_arr).round(2)

# ---------------------------------------------------------------------------
# 9. Delinquency flag -> Target 8%-12% overall
#    To achieve CreditTier <-> Delinquency Pearson > 0.40 mathematically,
#    we need delq rate >= 8% given the 3-tier credit ordinal.
#    ASSIST03 (subprime) drives ~85% of all delinquencies.
# ---------------------------------------------------------------------------
final_delq_rate = np.where(credit_arr == "ASSIST03", 0.25,   # ~25% of subprime default
                  np.where(credit_arr == "ASSIST01", 0.04,   # ~4% of average
                                                     0.005)) # ~0.5% of elite
delinquency_arr = np.random.binomial(1, final_delq_rate).astype(bool)

# ---------------------------------------------------------------------------
# 10. Discount rate (applied premium discount, not CLV discount rate)
# ---------------------------------------------------------------------------
disc_min = np.where(tenure_arr == "New",       0.00,
           np.where(tenure_arr == "Existing",  0.03, 0.08))
disc_max = np.where(tenure_arr == "New",       0.05,
           np.where(tenure_arr == "Existing",  0.08, 0.15))
discount_base = disc_min + np.random.random(N) * (disc_max - disc_min)
# Multi-product additive
disc_addend = np.where(multi_discount_arr, np.random.uniform(0.02, 0.04, N), 0.0)
discount_rate_arr = np.clip(discount_base + disc_addend, 0.0, 0.20).round(4)

# ---------------------------------------------------------------------------
# 11. Renewal / survival model
# ---------------------------------------------------------------------------
base_renew = np.array([TENURE_RENEWAL_PROB[t] for t in tenure_arr])

# Simulate premium ratio (year-over-year): use lognormal(0, 0.12) centred at 1.0
premium_ratio = np.random.lognormal(0.05, 0.12, N)  

prob = base_renew.copy()
prob *= np.where(premium_ratio > 1.2, 0.85, np.where(premium_ratio < 0.9, 1.05, 1.0)) # reduced drop
prob *= np.where(multi_discount_arr, 1.10, 1.0)
prob *= np.where(mortgage_arr,       1.08, 1.0)

# Target Age <-> Retention > 0.20: age linearly increases retention probability strongly
age_renew_mod = 0.75 + (age_arr - 20) * 0.007  # Re-centered for higher base (~85% overall)
prob *= age_renew_mod

prob *= np.where(credit_arr == "ASSIST03", 0.90, 1.0) # reduced penalty
prob *= np.where(delinquency_arr,    0.70, 1.0)
prob *= np.where(home_age_arr > 40,  0.98, 1.0)
prob *= 1.15  # Global anchor boost to guarantee 80%+
prob  = np.clip(prob, 0.0, 1.0)
renewed_arr = np.random.binomial(1, prob).astype(bool)

# ---------------------------------------------------------------------------
# 12. Assemble DataFrame (38 columns, matching schema order)
# ---------------------------------------------------------------------------
df = pd.DataFrame({
    "FULLPOLICY_NB"              : policy_ids,
    "POLICYEFFECTIVE_DT"         : eff_dates_pd.strftime("%Y-%m-%d"),
    "ACCOUNTING_MONTH"           : accounting_month,
    "INSUREDITEM_TP"             : item_type_arr,
    "POLICYRATEDSTATE_TP"        : state_arr,
    "RATEDCOUNTY_TP"             : county_arr,
    "ZIP"                        : zip_arr,
    "HAZARD_SCORE"               : hazard_arr,
    "INTEGRATEDCOVERAGE_TP"      : np.where(item_type_arr == 18, "HO3",
                                   np.where(item_type_arr == 19, "HO6",
                                   np.where(item_type_arr ==  7, "MHO", "HO2"))),
    "PROPERTYCOVERAGESUBTYPE_TP" : subtype_arr,
    "CONSTRUCTION_TP"            : const_arr,
    "ROOF_TP"                    : roof_arr,
    "DWELLINGSQUAREFEET_CT"      : sqft_arr,
    "DWELLINGSTORY_CT"           : story_arr,
    "HOME_AGE_YR"                : home_age_arr,
    "HAS_MORTGAGE"               : mortgage_arr,
    "RATEDINSUREDAGE_CT"         : age_arr,
    "MERITPOINT_CT"              : merit_arr,
    "CREDITMODEL_CD"             : credit_arr,
    "AGENT_CHANNEL"              : channel_arr,
    "DIRECTWRITTENPREMIUM_AM"    : dwp_arr,
    "EARNEDPREMIUM_AM"           : earned_prem,
    "TAX_AM"                     : tax_arr,
    "COMMISSION_EXPENSE_AM"      : commission_arr,
    "ADMIN_EXPENSE_AM"           : admin_arr,
    "PPCVRGLIMIT_AM"             : coverage_limit_arr,
    "GROSSLOSSPAIO_AM"           : gross_loss_arr,
    "CLAIMCOUNT_CT"              : claim_count_arr,
    "EARNEDEXPOSURE_CT"          : earned_exp_arr,
    "WRITENEXPOSURE_CT"          : written_exp_arr,
    "POLICYTERM_CT"              : term_arr,
    "SEASONAL_IN"                : seasonal_arr,
    "MULTIPRODUCTDISCOUNT_FLAG"  : multi_discount_arr,
    "DelequencyFlag"             : delinquency_arr,
    "DiscountRate"               : discount_rate_arr,
    "New_Existing_Recurring_Flag": tenure_arr,
    "NETLOSS_PAID_AM"            : net_loss_arr,
    "POLICY_RENEWED_FLAG"        : renewed_arr,
})

# ---------------------------------------------------------------------------
# 13. Final hard-constraint enforcement
# ---------------------------------------------------------------------------
# PPCVRGLIMIT_AM > DIRECTWRITTENPREMIUM_AM
df["PPCVRGLIMIT_AM"] = np.maximum(df["PPCVRGLIMIT_AM"], df["DIRECTWRITTENPREMIUM_AM"] * 1.05)
# NETLOSS_PAID_AM >= 0
df["NETLOSS_PAID_AM"] = np.maximum(df["NETLOSS_PAID_AM"], 0.0)

# ---------------------------------------------------------------------------
# 14. Export
# ---------------------------------------------------------------------------
out_path = r"c:\Users\madhu\Desktop\clv\clv_synthetic_dataset.csv"
df.to_csv(out_path, index=False, encoding="utf-8")

print(f"[OK] Generated {len(df):,} rows x {len(df.columns)} columns")
print(f"   Saved to: {out_path}")
print(f"   Nulls   : {df.isnull().sum().sum()}")
print(f"   Avg Premium : ${df['DIRECTWRITTENPREMIUM_AM'].mean():,.2f}")
print(f"   Loss Ratio  : {(df['NETLOSS_PAID_AM'].sum() / df['EARNEDPREMIUM_AM'].sum())*100:.1f}%")
print(f"   Claim Freq  : {(df['CLAIMCOUNT_CT'] > 0).mean()*100:.1f}%")
print(f"   Renewal Rate: {df['POLICY_RENEWED_FLAG'].mean()*100:.1f}%")

