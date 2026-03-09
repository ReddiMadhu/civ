"""
Property Insurance CLV Dataset Validator
Reads clv_synthetic_dataset.csv and prints a full pass/fail report
against Master Prompt v6.0 acceptance ranges.
"""

import sys
import numpy as np
import pandas as pd
from scipy import stats

CSV_PATH = r"c:\Users\madhu\Desktop\clv\clv_synthetic_dataset_fixed.csv"

PASS = "[PASS]"
FAIL = "[FAIL]"

def pf(condition, label, actual, expected):
    status = PASS if condition else FAIL
    print(f"  {status}  {label}")
    print(f"           actual={actual}   expected={expected}")

print("=" * 65)
print("  CLV Synthetic Dataset Validation Report")
print("=" * 65)

# Load
df = pd.read_csv(CSV_PATH, dtype={"POLICYRATEDSTATE_TP": str}, low_memory=False)
df["POLICYRATEDSTATE_TP"] = df["POLICYRATEDSTATE_TP"].str.zfill(2)
print(f"\n  Loaded: {len(df):,} rows x {len(df.columns)} columns\n")

# --------------------------------------------------------------------------
# 1. Schema checks
# --------------------------------------------------------------------------
print("-- [1] Schema --------------------------------------------------")
EXPECTED_COLS = [
    "FULLPOLICY_NB","POLICYEFFECTIVE_DT","ACCOUNTING_MONTH","INSUREDITEM_TP",
    "POLICYRATEDSTATE_TP","RATEDCOUNTY_TP","ZIP","HAZARD_SCORE",
    "INTEGRATEDCOVERAGE_TP","PROPERTYCOVERAGESUBTYPE_TP","CONSTRUCTION_TP",
    "ROOF_TP","DWELLINGSQUAREFEET_CT","DWELLINGSTORY_CT","HOME_AGE_YR",
    "HAS_MORTGAGE","RATEDINSUREDAGE_CT","MERITPOINT_CT","CREDITMODEL_CD",
    "AGENT_CHANNEL","DIRECTWRITTENPREMIUM_AM","EARNEDPREMIUM_AM","TAX_AM",
    "COMMISSION_EXPENSE_AM","ADMIN_EXPENSE_AM","PPCVRGLIMIT_AM",
    "GROSSLOSSPAIO_AM","CLAIMCOUNT_CT","EARNEDEXPOSURE_CT","WRITENEXPOSURE_CT",
    "POLICYTERM_CT","SEASONAL_IN","MULTIPRODUCTDISCOUNT_FLAG","DelequencyFlag",
    "DiscountRate","New_Existing_Recurring_Flag","NETLOSS_PAID_AM",
    "POLICY_RENEWED_FLAG",
]
pf(len(df) == 50_000, "Row count = 50,000", len(df), 50_000)
pf(len(df.columns) == 38, "Column count = 38", len(df.columns), 38)
missing_cols = [c for c in EXPECTED_COLS if c not in df.columns]
pf(len(missing_cols) == 0, "All 38 expected columns present",
   f"missing={missing_cols}" if missing_cols else "none missing", "none")
pf(df.isnull().sum().sum() == 0, "Zero nulls in entire dataset",
   df.isnull().sum().sum(), 0)
pf(df["FULLPOLICY_NB"].nunique() == 50_000, "FULLPOLICY_NB all unique",
   df["FULLPOLICY_NB"].nunique(), 50_000)

# --------------------------------------------------------------------------
# 2. Financial / actuarial metrics
# --------------------------------------------------------------------------
print("\n-- [2] Key Actuarial Metrics ------------------------------------")
loss_ratio        = df["NETLOSS_PAID_AM"].sum() / df["EARNEDPREMIUM_AM"].sum()
avg_prem          = df["DIRECTWRITTENPREMIUM_AM"].mean()
claim_freq        = (df["CLAIMCOUNT_CT"] > 0).mean()
delq_rate         = df["DelequencyFlag"].mean()
renewal_rate      = df["POLICY_RENEWED_FLAG"].mean()
avg_merit         = df["MERITPOINT_CT"].mean()
avg_home_age      = df["HOME_AGE_YR"].mean()
mortgage_share    = df["HAS_MORTGAGE"].mean()
recurring_share   = (df["New_Existing_Recurring_Flag"] == "Recurring").mean()

pf(0.55 <= loss_ratio <= 0.75, "Loss Ratio 55%-75%",
   f"{loss_ratio*100:.1f}%", "55%-75%")
pf(900 <= avg_prem <= 2600, "Avg Annual Premium $900-$2,600",
   f"${avg_prem:,.2f}", "$900-$2,600")
pf(0.08 <= claim_freq <= 0.15, "Claim Frequency 8%-15%",
   f"{claim_freq*100:.1f}%", "8%-15%")
pf(0.08 <= delq_rate <= 0.12, "Delinquency Rate 8%-12%",
   f"{delq_rate*100:.1f}%", "8%-12%")
pf(0.78 <= renewal_rate <= 0.88, "Renewal Rate 78%-88%",
   f"{renewal_rate*100:.1f}%", "78%-88%")
pf(5.5 <= avg_merit <= 6.5, "Avg MERITPOINT_CT 5.5-6.5",
   f"{avg_merit:.2f}", "5.5-6.5")
pf(28 <= avg_home_age <= 38, "Avg HOME_AGE_YR 28-38",
   f"{avg_home_age:.1f}", "28-38")
pf(0.45 <= mortgage_share <= 0.60, "HAS_MORTGAGE True share 45%-60%",
   f"{mortgage_share*100:.1f}%", "45%-60%")
pf(0.23 <= recurring_share <= 0.27, "Recurring share 23%-27%",
   f"{recurring_share*100:.1f}%", "23%-27%")

# --------------------------------------------------------------------------
# 3. Segment-level checks
# --------------------------------------------------------------------------
print("\n-- [3] Segment Metrics -----------------------------------------")
# FL Jul-Sep claim freq
fl_mask = (df["POLICYRATEDSTATE_TP"].astype(str) == "12")
fl_eff_dt = pd.to_datetime(df.loc[fl_mask, "POLICYEFFECTIVE_DT"])
fl_jul_sep_months = fl_eff_dt.dt.month.isin([7, 8, 9])
fl_jul_sep = fl_mask.copy()
fl_jul_sep[fl_mask] = fl_jul_sep_months.values
if fl_jul_sep.sum() > 0:
    fl_cat_freq = (df.loc[fl_jul_sep, "CLAIMCOUNT_CT"] > 0).mean()
    pf(0.22 <= fl_cat_freq <= 0.28, "FL Jul-Sep Claim Freq 22%-28%",
       f"{fl_cat_freq*100:.1f}%", "22%-28%")
else:
    print(f"  [SKIP]  FL Jul-Sep rows = 0, cannot compute FL CAT frequency")

# Subprime delinquency
sub_mask   = df["CREDITMODEL_CD"] == "ASSIST03"
elite_mask = df["CREDITMODEL_CD"] == "INTRNL06"
sub_delq   = df.loc[sub_mask,   "DelequencyFlag"].mean()
elite_delq = df.loc[elite_mask, "DelequencyFlag"].mean()
pf(0.20 <= sub_delq <= 0.30, "Subprime Delinquency Rate 20%-30%",
   f"{sub_delq*100:.1f}%", "20%-30%")
pf(sub_delq >= 3 * elite_delq, "Subprime delq >= 3x Elite",
   f"{sub_delq*100:.1f}% vs elite {elite_delq*100:.1f}% x3={elite_delq*3*100:.1f}%", "ratio >= 3")

# --------------------------------------------------------------------------
# 4. State frequency
# --------------------------------------------------------------------------
print("\n-- [4] State Frequency +-2% ------------------------------------")
target_state = {"12": 0.28, "48": 0.27, "06": 0.17, "36": 0.13, "18": 0.08, "26": 0.07}
state_actual = df["POLICYRATEDSTATE_TP"].astype(str).value_counts(normalize=True)
for sc, tgt in target_state.items():
    actual = state_actual.get(sc, 0.0)
    pf(abs(actual - tgt) <= 0.02, f"State {sc} frequency ~{tgt*100:.0f}%",
       f"{actual*100:.1f}%", f"{tgt*100:.0f}%+-2%")

# --------------------------------------------------------------------------
# 5. Referential integrity
# --------------------------------------------------------------------------
print("\n-- [5] Referential Integrity ------------------------------------")
cov_gt_prem = (df["PPCVRGLIMIT_AM"] > df["DIRECTWRITTENPREMIUM_AM"]).all()
pf(cov_gt_prem, "PPCVRGLIMIT_AM > DIRECTWRITTENPREMIUM_AM always",
   "ALL TRUE" if cov_gt_prem else "VIOLATIONS FOUND", "ALL TRUE")

netloss_ge0 = (df["NETLOSS_PAID_AM"] >= 0).all()
pf(netloss_ge0, "NETLOSS_PAID_AM >= 0 always",
   "ALL TRUE" if netloss_ge0 else "VIOLATIONS FOUND", "ALL TRUE")

zero_zero = ((df["CLAIMCOUNT_CT"] == 0) == (df["GROSSLOSSPAIO_AM"] == 0.0)).all()
pf(zero_zero, "CLAIMCOUNT_CT=0 <=> GROSSLOSSPAIO_AM=0.00",
   "ALL TRUE" if zero_zero else "VIOLATIONS FOUND", "ALL TRUE")

CONSTRUCTION_CPF = {1: 150, 2: 180, 4: 230, 6: 325}
df["_repl_val"] = df["DWELLINGSQUAREFEET_CT"] * df["CONSTRUCTION_TP"].map(CONSTRUCTION_CPF)
mort_rows = df[df["HAS_MORTGAGE"] == True]
mort_ok = (mort_rows["PPCVRGLIMIT_AM"] >= 0.80 * mort_rows["_repl_val"]).all()
pf(mort_ok, "Mortgage => PPCVRGLIMIT_AM >= 80% replacement",
   "ALL TRUE" if mort_ok else f"VIOLATIONS FOUND", "ALL TRUE")

df["_eff_ym"] = pd.to_datetime(df["POLICYEFFECTIVE_DT"]).dt.to_period("M").astype(str)
acct_ok = (df["ACCOUNTING_MONTH"] == df["_eff_ym"]).all()
pf(acct_ok, "ACCOUNTING_MONTH matches POLICYEFFECTIVE_DT",
   "ALL TRUE" if acct_ok else "MISMATCH FOUND", "ALL TRUE")

# --------------------------------------------------------------------------
# 6. Pearson Correlation Targets
# --------------------------------------------------------------------------
print("\n-- [6] Pearson Correlation Targets ------------------------------")

def check_r(name, x, y, lo, hi):
    mask = ~(np.isnan(x) | np.isnan(y) | np.isinf(x) | np.isinf(y))
    r, _ = stats.pearsonr(x[mask], y[mask])
    pf(lo <= r <= hi, name, f"r={r:.3f}", f"{lo:.2f} to {hi:.2f}")

sqft           = df["DWELLINGSQUAREFEET_CT"].values.astype(float)
prem           = df["DIRECTWRITTENPREMIUM_AM"].values.astype(float)
const_code     = df["CONSTRUCTION_TP"].values.astype(float)
cov_lim        = df["PPCVRGLIMIT_AM"].values.astype(float)
merit          = df["MERITPOINT_CT"].values.astype(float)
claim_freq_bin = (df["CLAIMCOUNT_CT"] > 0).values.astype(float)
home_age       = df["HOME_AGE_YR"].values.astype(float)
gross_loss     = df["GROSSLOSSPAIO_AM"].values.astype(float)
hazard         = df["HAZARD_SCORE"].values.astype(float)
credit_num     = np.where(df["CREDITMODEL_CD"] == "INTRNL06", 1,
                 np.where(df["CREDITMODEL_CD"] == "ASSIST03", 3, 2)).astype(float)
renewed_bin    = df["POLICY_RENEWED_FLAG"].values.astype(float)
age_num        = df["RATEDINSUREDAGE_CT"].values.astype(float)
state_risk     = df["POLICYRATEDSTATE_TP"].astype(str).map(
    {"12":1.45,"48":1.30,"06":1.35,"36":1.15,"18":1.10,"26":1.05}).values.astype(float)

check_r("SqFt <-> Premium",           sqft,       prem,          0.65, 0.75)
check_r("Construction <-> CovLimit",  const_code, cov_lim,       0.50, 0.60)
check_r("CreditTier <-> Delinquency", credit_num, df["DelequencyFlag"].values.astype(float), 0.40, 0.50)
check_r("MeritPoint <-> ClaimFreq",   merit,      claim_freq_bin,-0.40,-0.30)
check_r("HomeAge <-> GrossLoss",      home_age,   gross_loss,    0.20, 0.30)
check_r("HazardScore <-> ClaimFreq",  hazard,     claim_freq_bin, 0.35, 0.50)
check_r("Age <-> Retention",          age_num,    renewed_bin,   0.20, 0.30)
check_r("State <-> ClaimFreq",        state_risk, claim_freq_bin, 0.25, 0.35)

# --------------------------------------------------------------------------
# Summary
# --------------------------------------------------------------------------
print("\n" + "=" * 65)
print("  Validation complete.")
print("=" * 65)
