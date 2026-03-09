import pandas as pd
import numpy as np
from scipy import stats
import ast

def calc_pearson_from_file():
    df = pd.read_csv("c:/Users/madhu/Desktop/clv/clv_synthetic_dataset.csv", dtype={"POLICYRATEDSTATE_TP": str})
    print(df["POLICYRATEDSTATE_TP"].value_counts())
    
    sqft = df["DWELLINGSQUAREFEET_CT"].values.astype(float)
    prem = df["DIRECTWRITTENPREMIUM_AM"].values.astype(float)
    const_code = df["CONSTRUCTION_TP"].values.astype(float)
    cov_lim = df["PPCVRGLIMIT_AM"].values.astype(float)
    merit = df["MERITPOINT_CT"].values.astype(float)
    claim_freq_bin = (df["CLAIMCOUNT_CT"] > 0).values.astype(float)
    home_age = df["HOME_AGE_YR"].values.astype(float)
    gross_loss = df["GROSSLOSSPAIO_AM"].values.astype(float)
    hazard = df["HAZARD_SCORE"].values.astype(float)
    delq_bin = df["DelequencyFlag"].values.astype(float)
    credit_num = np.where(df["CREDITMODEL_CD"] == "INTRNL06", 1, np.where(df["CREDITMODEL_CD"] == "ASSIST03", 3, 2)).astype(float)
    renewed_bin = df["POLICY_RENEWED_FLAG"].values.astype(float)
    age_num = df["RATEDINSUREDAGE_CT"].values.astype(float)
    state_mapping = {"12":1.45,"48":1.30,"06":1.35,"36":1.15,"18":1.10,"26":1.05}
    state_risk = df["POLICYRATEDSTATE_TP"].astype(str).str.zfill(2).map(state_mapping).fillna(1.0).values.astype(float)
    
    def r(x, y):
        mask = ~(np.isnan(x) | np.isnan(y) | np.isinf(x) | np.isinf(y))
        return stats.pearsonr(x[mask], y[mask])[0]
        
    print(f"SqFt-Prem: {r(sqft, prem):.3f} (target 0.65-0.75)")
    print(f"Const-Cov: {r(const_code, cov_lim):.3f} (target 0.50-0.60)")
    print(f"Cred-Delq: {r(credit_num, delq_bin):.3f} (target 0.40-0.50)")
    print(f"Merit-Freq: {r(merit, claim_freq_bin):.3f} (target -0.40 to -0.30)")
    print(f"Age-Loss: {r(home_age, gross_loss):.3f} (target 0.20-0.30)")
    print(f"Haz-Freq: {r(hazard, claim_freq_bin):.3f} (target 0.35-0.50)")
    print(f"Age-Ret: {r(age_num, renewed_bin):.3f} (target 0.20-0.30)")
    print(f"State-Freq: {r(state_risk, claim_freq_bin):.3f} (target 0.25-0.35)")

if __name__ == "__main__":
    calc_pearson_from_file()
