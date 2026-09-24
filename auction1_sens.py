import numpy as np
import pandas as pd
import scipy.optimize as opt

def run_model(capex_mult=1.0, opex_mult=1.0, prod_mult=1.0, interest_rate_p2=0.05):
    # ==========================================
    # 1. BAZIKO A PIPARAMETRO
    # ==========================================
    capacity_mw = 800.0
    capacity_kw = capacity_mw * 1000.0
    
    capex_per_mw = 22.41 * capex_mult  # mDKK / MW
    total_capex = capacity_mw * capex_per_mw * 1e6  # Total CAPEX iti DKK
    
    opex_per_kw_year = 756.0 * opex_mult  # DKK / kW / tawen
    base_annual_opex = capacity_kw * opex_per_kw_year  # Base OPEX iti DKK
    
    inflation_rate = 0.02
    discount_rate = 0.06
    debt_ratio = 0.70
    loan_amount = total_capex * debt_ratio

    # ==========================================
    # 2. COMPUTASYON TI UTANG (2026-2045)
    # ==========================================
    # Phase 1: 2026-2031 (6 a tawen, 4% interest, 20-tawen amortization)
    r1, n1 = 0.04, 20
    ds1 = loan_amount * (r1 * (1 + r1)**n1) / (((1 + r1)**n1) - 1)

    rem_debt = loan_amount
    for _ in range(2026, 2032):
        interest = rem_debt * r1
        principal = ds1 - interest
        rem_debt -= principal

    # Phase 2: 2032-2045 (14 a tawen a natda)
    r2, n2 = interest_rate_p2, 14
    ds2 = rem_debt * (r2 * (1 + r2)**n2) / (((1 + r2)**n2) - 1)

    # ==========================================
    # 3. PRESIO KEN OPERASYON (2032-2056) - TAWEN BAZIKO: 2026
    # ==========================================
    years_operating = np.arange(2032, 2057)
    df_project = pd.DataFrame({'Year': years_operating})

    # Kurba ti presio iti merkado (Manipud 2026 agingga 2056)
    real_points = {2030: 230.0, 2040: 360.0, 2050: 290.0}
    df_full = pd.DataFrame({'Year': np.arange(2026, 2057)})
    df_full['Real_Price_DKK'] = np.nan
    for y, p in real_points.items():
        df_full.loc[df_full['Year'] == y, 'Real_Price_DKK'] = p

    df_full['Real_Price_DKK'] = df_full['Real_Price_DKK'].interpolate(method='linear')
    
    # Minus 7 DKK kada tawen kalpasan ti 2050
    for y in range(2051, 2057):
        df_full.loc[df_full['Year'] == y, 'Real_Price_DKK'] = df_full.loc[df_full['Year'] == y-1, 'Real_Price_DKK'].values[0] - 7.0

    # Pammagayat iti Inflation manipud 2026
    df_full['Nominal_Price_DKK'] = df_full['Real_Price_DKK'] * ((1 + inflation_rate) ** (df_full['Year'] - 2026))
    df_project = df_project.merge(df_full[['Year', 'Nominal_Price_DKK']], on='Year', how='left')

    # OPEX a kimmuyog iti inflation manipud 2026
    df_project['Annual_OPEX'] = base_annual_opex * ((1 + inflation_rate) ** (df_project['Year'] - 2026))

    annual_mwh_p50 = capacity_mw * 8760 * 0.525 * prod_mult
    annual_mwh_p75 = annual_mwh_p50 * 0.90

    # ==========================================
    # 4. PANAGSAPUL TI STRIKE PRICE (NPV = 0) KEN DSCR
    # ==========================================
    def eval_sp(sp):
        cfd_years = 20
        # Dagiti umuna a 20 a tawen (2032-2051) ket usaren ti Strike Price, dagiti natda a 5 a tawen (2052-2056) ket usaren ti presio iti merkado
        prices = np.where(np.arange(1, 26) <= cfd_years, sp, df_project['Nominal_Price_DKK'].values)
        
        annual_revenue = annual_mwh_p50 * prices
        annual_cf = annual_revenue - df_project['Annual_OPEX'].values
        
        # NPV a nakabase iti tawen 2026 (t = 0)
        # CAPEX iti t = 0 (2026), Operational Cash Flows iti t = 6 agingga 30 (2032 agingga 2056)
        t_years = years_operating - 2026
        npv = -total_capex + np.sum(annual_cf / ((1 + discount_rate) ** t_years))
        
        # DSCR P75 para iti 2032-2045 (14 a tawen)
        p75_revenue = annual_mwh_p75 * sp
        p75_cf = p75_revenue - df_project['Annual_OPEX'].iloc[:14].values
        min_dscr_p75 = (p75_cf / ds2).min()
        
        return npv, min_dscr_p75

    # Panagsapul iti Strike Price nu NPV = 0
    res = opt.root_scalar(lambda sp: eval_sp(sp)[0], bracket=[100, 3000], method="brentq")
    opt_sp = res.root
    _, min_dscr = eval_sp(opt_sp)
    
    return opt_sp, min_dscr

# ==========================================
# 5. SENSITIVITY ANALYSIS
# ==========================================
scenarios = {
    "Base Case": (1.0, 1.0, 1.0, 0.05),
    "CAPEX +10%": (1.1, 1.0, 1.0, 0.05),
    "CAPEX -10%": (0.9, 1.0, 1.0, 0.05),
    "OPEX +20%": (1.0, 1.2, 1.0, 0.05),
    "Production -10% (Low Wind)": (1.0, 1.0, 0.9, 0.05),
    "Production +10% (High Wind)": (1.0, 1.0, 1.1, 0.05),
    "Interest Rate 6% (Post-2032)": (1.0, 1.0, 1.0, 0.06),
    "Interest Rate 4% (Post-2032)": (1.0, 1.0, 1.0, 0.04),
}

results = []
for name, params in scenarios.items():
    sp, dscr = run_model(*params)
    results.append({
        "Σενάριο": name,
        "Strike Price (DKK/MWh)": round(sp, 2),
        "Min DSCR (P75)": round(dscr, 2)
    })

df_sens = pd.DataFrame(results)
print(df_sens.to_string(index=False))