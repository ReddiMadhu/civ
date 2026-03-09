import pandas as pd
import numpy as np
import scipy.stats as stats

CSV_PATH = "c:/Users/madhu/Desktop/clv/clv_synthetic_dataset.csv"
OUT_PATH = "c:/Users/madhu/Desktop/clv/clv_synthetic_dataset_fixed.csv"

print("Loading dataset...")
df = pd.read_csv(CSV_PATH, dtype={"POLICYRATEDSTATE_TP": str}, low_memory=False)
df["POLICYRATEDSTATE_TP"] = df["POLICYRATEDSTATE_TP"].str.zfill(2)

def r(x, y):
    mask = ~(np.isnan(x) | np.isnan(y) | np.isinf(x) | np.isinf(y))
    return stats.pearsonr(x[mask], y[mask])[0]

def force_corr_vectorized(target_col, ref_col, target_r):
    """
    Rapidly rank-correlates target_col to ref_col without changing marginal distribution.
    Creates a hidden standard normal Z that is correlated with ref_col, 
    then sorts target_col to match Z's rank order.
    """
    x = df[target_col].values.copy()
    y = df[ref_col].values.copy()
    
    current_r = r(x, y)
    print(f"[{target_col} <-> {ref_col}] Initial r={current_r:.3f}, Target={target_r}")
    
    if abs(current_r - target_r) < 0.01:
        return
        
    # We want to re-order x so that its correlation with y is exactly target_r.
    # 1. Normalize y to standard normal (rank-based)
    y_ranks = stats.rankdata(y + np.random.uniform(0, 1e-6, len(y)))
    y_norm = stats.norm.ppf(y_ranks / (len(y) + 1))
    
    # 2. Binary search for mixing parameter alpha
    # Z = alpha * y_norm + sqrt(1 - alpha^2) * noise
    low, high = -1.0, 1.0
    best_x = x.copy()
    best_diff = 999
    
    noise = np.random.normal(0, 1, len(y))
    x_sorted = np.sort(x)
    
    for _ in range(40):
        alpha = (low + high) / 2
        
        # Ensure alpha is valid domain
        alpha_c = np.clip(alpha, -0.999, 0.999)
        Z = alpha_c * y_norm + np.sqrt(1 - alpha_c**2) * noise
        
        # We want x to be sorted in the exactly same order as Z
        # Rank of Z tells us where to put the smallest element of x
        Z_ranks = stats.rankdata(Z, method='ordinal').astype(int) - 1
        x_new = np.empty_like(x)
        # Place the i-th smallest element of x into the position of the i-th smallest element of Z
        # i.e., sort Z to find its original indices
        if target_r < 0:
            Z_argsort = np.argsort(-Z) # reverse sorting order for negative correlation
        else:
            Z_argsort = np.argsort(Z)
            
        x_new[Z_argsort] = x_sorted

        new_r = r(x_new, y)
        diff = new_r - target_r
        
        if abs(diff) < best_diff:
            best_diff = abs(diff)
            best_x = x_new.copy()
            
        if diff < 0:
            if target_r > 0: low = alpha
            else: high = alpha
        else:
            if target_r > 0: high = alpha
            else: low = alpha
            
        if abs(diff) < 0.005:
            break
            
    print(f"[{target_col} <-> {ref_col}] Final r={r(best_x, y):.3f}")
    df[target_col] = best_x

# 1. SqFt <-> Premium (0.65 - 0.75)  (Current ~0.64 -> Needs bump)
force_corr_vectorized("DIRECTWRITTENPREMIUM_AM", "DWELLINGSQUAREFEET_CT", 0.70)

# 2. Construction <-> CovLimit (0.50 - 0.60) (Current ~0.67 -> Needs drop)
force_corr_vectorized("PPCVRGLIMIT_AM", "CONSTRUCTION_TP", 0.55)

# 3. CreditTier <-> Delinquency (0.40 - 0.50)
credit_num = np.where(df["CREDITMODEL_CD"] == "INTRNL06", 1, np.where(df["CREDITMODEL_CD"] == "ASSIST03", 3, 2)).astype(float)
df["_temp_credit"] = credit_num

if r(df["DelequencyFlag"], credit_num) < 0.40:
    # Delinquency rate is ~4.5%. We MUST place ALL delinquencies
    # on SUBPRIME (3). If we run out, then AVERAGE (2).
    # This mathematically guarantees the maximum possible Pearson R.
    n_delq = int(df["DelequencyFlag"].sum())
    
    # Sort dataset by credit tier. To avoid breaking other correlations, 
    # we tie-break using pure random noise. 
    # Highest values (credit=3) will be at the end of sort_idx
    sort_idx = np.argsort(credit_num + np.random.uniform(0, 0.5, len(df)))
    
    delq_new = np.zeros(len(df), dtype=bool)
    delq_new[sort_idx[-n_delq:]] = True
    df["DelequencyFlag"] = delq_new
    
    print(f"Forced Delq -> Credit Pearson: {r(df['DelequencyFlag'], credit_num):.3f}")

# 4. MeritPoint <-> ClaimFreq (-0.40 to -0.30) 
df["_temp_freq"] = (df["CLAIMCOUNT_CT"] > 0).astype(float)
force_corr_vectorized("MERITPOINT_CT", "_temp_freq", -0.35)

# 5. HomeAge <-> GrossLoss (0.20 - 0.30) (Current ~0.06 -> Needs bump)
# Handled below alongside referential zero mapping!

# 6. HazardScore <-> ClaimFreq (0.35 - 0.50)
force_corr_vectorized("HAZARD_SCORE", "_temp_freq", 0.42)

# 7. Age <-> Retention (0.20 - 0.30)
force_corr_vectorized("POLICY_RENEWED_FLAG", "RATEDINSUREDAGE_CT", 0.25)

# 8. State <-> ClaimFreq (0.25 - 0.35)
state_mapping = {"12":1.45,"48":1.30,"06":1.35,"36":1.15,"18":1.10,"26":1.05}
state_risk = df["POLICYRATEDSTATE_TP"].map(state_mapping).fillna(1.0).values.astype(float)
df["_temp_state"] = state_risk

# Can't easily shift State strings continuously. Let's shift ClaimFreq based on state!
# Wait, changing ClaimFreq breaks ClaimCount vs GrossLoss zero-zero integrity.
# We will sort States directly.
def force_state_corr(target_r):
    x_state = df["POLICYRATEDSTATE_TP"].values.copy()
    y = df["_temp_freq"].values.copy()
    
    current_r = r(pd.Series(x_state).map(state_mapping).fillna(1.0).values.astype(float), y)
    print(f"[State <-> Freq] Initial r={current_r:.3f}, Target={target_r}")
    
    if abs(current_r - target_r) < 0.01: return
    
    # We will sort State so that higher claim freqs get higher risk states
    y_ranks = stats.rankdata(y) + np.random.uniform(0, 1, len(y)) # break ties
    y_norm = stats.norm.ppf(y_ranks / (len(y) + 1))
    
    # Re-map states string -> risk float
    x_risk = pd.Series(x_state).map(state_mapping).fillna(1.0).values.astype(float)
    x_sorted_by_risk = x_state[np.argsort(x_risk + np.random.uniform(0, 0.01, len(x_risk)))]
    
    low, high = -1.0, 1.0
    best_x = x_state.copy()
    best_diff = 999
    noise = np.random.normal(0, 1, len(y))
    
    for _ in range(40):
        orig_alpha = (low + high) / 2
        alpha = np.clip(orig_alpha, -0.999, 0.999)
        Z = alpha * y_norm + np.sqrt(1 - alpha**2) * noise
        
        Z_argsort = np.argsort(Z)
        x_new = np.empty_like(x_state)
        x_new[Z_argsort] = x_sorted_by_risk
        
        test_r = r(pd.Series(x_new).map(state_mapping).fillna(1.0).values.astype(float), y)
        diff = test_r - target_r
        
        if abs(diff) < best_diff:
            best_diff = abs(diff)
            best_x = x_new.copy()
            
        if diff < 0: low = orig_alpha
        else: high = orig_alpha
            
    print(f"[State <-> Freq] Final r={r(pd.Series(best_x).map(state_mapping).fillna(1.0).values.astype(float), y):.3f}")
    df["POLICYRATEDSTATE_TP"] = best_x

force_state_corr(0.30)

print("\n--- Repairing Referential Integrity ---")

# 1. State ZIP logic: If we swapped states, ZIPs might be wrong for that state!
# But ZIP doesn't affect Pearson. Let's just generate fresh random zips for the new state array to maintain State/ZIP integrity!
STATE_ZIPS = {
    "12": ["33101","33125","33139","33156","33301","33401","33602","33701","32801","34201","33705","32901","33004","32003","33060","32084","33458","33629","33980","32205"],
    "48": ["77001","77002","77019","77494","75201","75202","75215","78201","78202","78701","78702","79901","79902","77380","77845","76101","76102","77840","78201","75063"],
    "06": ["90001","90210","94102","94103","92101","92037","95814","95816","91101","91201","90401","94501","93101","93001","91301","90802","94601","95008","92618","93311"],
    "36": ["10001","10002","10007","10019","10036","11201","11215","11354","12203","13202","10304","11530","10701","11901","14201","14604","12601","11720","10950","10583"],
    "18": ["60601","60602","60614","60615","60626","60637","60647","61820","62701","62901","60201","60301","60402","60510","61265","60901","61101","62220","60901","61401"],
    "26": ["48201","48202","48301","48304","49503","49505","48103","48104","48823","48912","49001","49002","48430","48640","49601","48858","48602","48503","49120","48198"],
}
state_arr = df["POLICYRATEDSTATE_TP"].values
zip_arr = np.array([STATE_ZIPS[s][np.random.randint(0, len(STATE_ZIPS[s]))] for s in state_arr])
df["ZIP"] = zip_arr

# 2. Premium Derivations
# DWP was swapped, recompute EARNED/TAX/COMMISSION/ADMIN
CHANNEL_COMMISSION  = {"Independent": 0.15, "Captive": 0.10, "Direct": 0.08}
comm_rate = df["AGENT_CHANNEL"].map(CHANNEL_COMMISSION).values
df["EARNEDPREMIUM_AM"] = (0.925 * df["DIRECTWRITTENPREMIUM_AM"]).round(2)
df["TAX_AM"] = (0.045 * df["DIRECTWRITTENPREMIUM_AM"]).round(2)
df["COMMISSION_EXPENSE_AM"] = (df["DIRECTWRITTENPREMIUM_AM"] * comm_rate).round(2)
df["ADMIN_EXPENSE_AM"] = (0.03 * df["DIRECTWRITTENPREMIUM_AM"] + 50.0).round(2)

# 3. CovLimit Derivations
# CovLimit was swapped. Ensure CovLimit > DWP
df["PPCVRGLIMIT_AM"] = np.maximum(df["PPCVRGLIMIT_AM"], df["DIRECTWRITTENPREMIUM_AM"] * 1.05)

CONSTRUCTION = {1: {"cpf": 150}, 2: {"cpf": 180}, 4: {"cpf": 230}, 6: {"cpf": 325}}
cost_per_sqft = df["CONSTRUCTION_TP"].map(lambda x: CONSTRUCTION[x]["cpf"]).values
replacement_value = df["DWELLINGSQUAREFEET_CT"] * cost_per_sqft
df.loc[df["HAS_MORTGAGE"], "PPCVRGLIMIT_AM"] = np.maximum(df.loc[df["HAS_MORTGAGE"], "PPCVRGLIMIT_AM"], 0.80 * replacement_value[df["HAS_MORTGAGE"]])
df["PPCVRGLIMIT_AM"] = df["PPCVRGLIMIT_AM"].round(2)

# 4. GrossLoss Derivation
# GrossLoss was swapped. Re-enforce zero-zero integrity:
# If ClaimCount==0, Gross Loss must be 0.
# If GrossLoss==0, ClaimCount must be 0.
mask_zero_claim = (df["CLAIMCOUNT_CT"] == 0)

print("Fixing GrossLoss/ClaimCount referential mapping...")
orig_gross = df["GROSSLOSSPAIO_AM"].values
non_zero_gross = orig_gross[orig_gross > 0]
non_zero_claims = (df["CLAIMCOUNT_CT"] > 0).astype(int).sum()

if len(non_zero_gross) > non_zero_claims:
    non_zero_gross = np.sort(non_zero_gross)[::-1][:non_zero_claims]
elif len(non_zero_gross) < non_zero_claims:
    pad = np.random.choice(non_zero_gross, non_zero_claims - len(non_zero_gross))
    non_zero_gross = np.concatenate([non_zero_gross, pad])

target_mask = (df["CLAIMCOUNT_CT"] > 0)
age_where_claims = df.loc[target_mask, "HOME_AGE_YR"].values

age_ranks = stats.rankdata(age_where_claims + np.random.uniform(0, 0.1, len(age_where_claims))) - 1
age_ranks = age_ranks.astype(int)
sorted_gross = np.sort(non_zero_gross)

# By sorting it on the full 50,000 array using vector mapping we ensure exact targets
# Map non-zero losses into the exact indices where ClaimCount > 0, ordered by HomeAge!
loss_idx_to_fill = np.where(target_mask)[0]
# age_ranks tells us which rank each Claiming HomeAge has (0 is oldest, etc if we sorted descending)
# We want the highest losses attached to the oldest homes.
# sorted_gross is ascending, so we simply slot them in by age rank
mapped_gross_array = np.zeros(len(df))
# For each claim index, we look at its rank among claiming homes, and assign that rank's sorted loss
mapped_gross_array[loss_idx_to_fill] = sorted_gross[age_ranks]

df["GROSSLOSSPAIO_AM"] = np.round(mapped_gross_array, 2)
print(f"Forced HomeAge -> GrossLoss Pearson: {r(df['GROSSLOSSPAIO_AM'], df['HOME_AGE_YR']):.3f}")
# Recompute NETLOSS_PAID_AM
# PROPERTYCOVERAGESUBTYPE_TP keys range: 25xx HO3, 26xx HO2, 27xx HO6, 28xx MHO
DEDUCTIBLE = {
    25: {"INTRNL06": 1000, "ASSIST01": 2500, "ASSIST03": 5000},
    26: {"INTRNL06": 1500, "ASSIST01": 3000, "ASSIST03": 5500},
    27: {"INTRNL06": 1000, "ASSIST01": 2500, "ASSIST03": 5000},
    28: {"INTRNL06": 2000, "ASSIST01": 3500, "ASSIST03": 6000},
}
deductible_arr = np.array([
    DEDUCTIBLE[int(st) // 100][cr]
    for st, cr in zip(df["PROPERTYCOVERAGESUBTYPE_TP"], df["CREDITMODEL_CD"])
], dtype=float)

df["NETLOSS_PAID_AM"] = np.maximum(0, df["GROSSLOSSPAIO_AM"] - deductible_arr).round(2)

print("\nSaving final dataset...")
df.drop(columns=["_temp_credit", "_temp_freq", "_temp_state"], inplace=True)
df.to_csv(OUT_PATH, index=False)
print("Saved.")
