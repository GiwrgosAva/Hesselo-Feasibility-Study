import numpy as np
import pandas as pd
import scipy.optimize as opt

# ==========================================
# 1. ΒΑΣΙΚΕΣ ΥΠΟΘΕΣΕΙΣ (ΕΤΟΣ ΒΑΣΗΣ: 2026)
# ==========================================
capacity_mw = 800.0  # MW
capex_per_mw = 22.41  # mDKK / MW
opex_per_kw_year = 756.0  # DKK / kW / year
inflation_rate = 0.02

total_capex = capacity_mw * capex_per_mw * 1e6  # 17.928 δισ. DKK
debt_ratio = 0.70
loan_amount = total_capex * debt_ratio  # 12.5496 δισ. DKK

# ==========================================
# 2. ΥΠΟΛΟΓΙΣΜΟΣ ΔΟΣΕΩΝ ΔΑΝΕΙΟΥ (2026-2045)
# ==========================================
# Περίοδος 1: 2026-2031 (6 έτη με 4% σε 20ετή βάση)
r1 = 0.04
n1 = 20
debt_service_phase1 = loan_amount * (r1 * (1 + r1)**n1) / (((1 + r1)**n1) - 1)

remaining_debt = loan_amount
for y in range(2026, 2032):
    interest = remaining_debt * r1
    principal = debt_service_phase1 - interest
    remaining_debt -= principal

# Περίοδος 2: 2032-2045 (14 εναπομείναντα έτη με 5%)
r2 = 0.05
n2 = 14
debt_service_phase2 = remaining_debt * (r2 * (1 + r2)**n2) / (((1 + r2)**n2) - 1)

# ==========================================
# 3. ΠΡΟΒΛΕΨΕΙΣ ΤΙΜΩΝ & ΛΕΙΤΟΥΡΓΙΑ (2032-2056)
# ==========================================
years_operating = np.arange(2032, 2057)
df_project = pd.DataFrame({'Year': years_operating})

real_points = {2030: 230.0, 2040: 360.0, 2050: 290.0}

# ΑΛΛΑΓΗ: Έναρξη DataFrame από το 2026 (όχι 2025)
df_full = pd.DataFrame({'Year': np.arange(2026, 2057)})
df_full['Real_Price_DKK'] = np.nan
for y, p in real_points.items():
    df_full.loc[df_full['Year'] == y, 'Real_Price_DKK'] = p

df_full['Real_Price_DKK'] = df_full['Real_Price_DKK'].interpolate(method='linear')
for y in range(2051, 2057):
    df_full.loc[df_full['Year'] == y, 'Real_Price_DKK'] = df_full.loc[df_full['Year'] == y-1, 'Real_Price_DKK'].values[0] - 7.0

# ΑΛΛΑΓΗ: Πληθωρισμός με βάση το 2026 (df_full['Year'] - 2026)
df_full['Nominal_Price_DKK'] = df_full['Real_Price_DKK'] * ((1 + inflation_rate) ** (df_full['Year'] - 2026))
df_project = df_project.merge(df_full[['Year', 'Nominal_Price_DKK']], on='Year', how='left')

base_annual_opex = capacity_mw * (opex_per_kw_year * 1000)
# ΑΛΛΑΓΗ: OPEX με βάση το 2026 (df_project['Year'] - 2026)
df_project['Annual_OPEX'] = base_annual_opex * ((1 + inflation_rate) ** (df_project['Year'] - 2026))

capacity_factor = 0.525
annual_mwh_p50 = capacity_mw * 8760 * capacity_factor
annual_mwh_p75 = annual_mwh_p50 * 0.90
discount_rate = 0.06

# ==========================================
# 4. ΕΥΡΕΣΗ STRIKE PRICE & DSCR
# ==========================================
def evaluate_project(strike_price):
    cfd_years = 20
    prices = np.where(np.arange(1, 26) <= cfd_years, strike_price, df_project['Nominal_Price_DKK'])
    
    annual_revenue = annual_mwh_p50 * prices
    annual_cf = annual_revenue - df_project['Annual_OPEX']
    
    # NPV υπολογισμένο στο 2026 (t = 0)
    cash_flows = np.insert(annual_cf.values, 0, -total_capex)
    time_indices = np.insert(np.arange(6, 31), 0, 0)
    npv = sum(cf / ((1 + discount_rate) ** t) for t, cf in zip(time_indices, cash_flows))
    
    # DSCR P75 (2032-2045: 14 έτη)
    p75_revenue = annual_mwh_p75 * strike_price
    p75_cf = p75_revenue - df_project['Annual_OPEX'].iloc[:14]
    min_dscr_p75 = (p75_cf / debt_service_phase2).min()
    
    return npv, min_dscr_p75

result = opt.root_scalar(lambda sp: evaluate_project(sp)[0], bracket=[100, 1500], method="brentq")
optimal_strike_price = result.root
npv, min_dscr_p75 = evaluate_project(optimal_strike_price)

print(f"Δόση Δανείου 2026-2031 (4%): {debt_service_phase1 / 1e6:.2f} mDKK/έτος")
print(f"Δόση Δανείου 2032-2045 (5%): {debt_service_phase2 / 1e6:.2f} mDKK/έτος")
print(f"Ελάχιστο Strike Price (NPV = 0): {optimal_strike_price:.2f} DKK/MWh")
print(f"Ελάχιστος Δείκτης DSCR P75 (2032-2045): {min_dscr_p75:.2f}")
