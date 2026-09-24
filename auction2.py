import numpy as np
import pandas as pd
import scipy.optimize as opt

def run_auction2_model(extra_mw=0, ppa_price=0, capex_mult=1.0, opex_mult=1.0, prod_mult=1.0, interest_rate_p2=0.05):
    # ==========================================
    # 1. ΒΑΣΙΚΕΣ ΥΠΟΘΕΣΕΙΣ & ΚΟΣΤΗ (ΒΑΣΗ: 2026)
    # ==========================================
    base_mw = 800.0
    total_mw = base_mw + extra_mw  # Συνολική ισχύς (800 MW έως 1150 MW)
    
    
    
    # Το CAPEX και το OPEX κλιμακώνονται ανάλογα με τη συνολική ισχύ (total_mw)
    capex_per_mw = 22.41 * capex_mult  # mDKK / MW
    total_capex = total_mw * capex_per_mw * 1e6  # Total CAPEX σε DKK
    
    opex_per_kw_year = 756.0 * opex_mult  # DKK / kW / έτος
    base_annual_opex = total_mw * 1000.0 * opex_per_kw_year  # Base OPEX σε DKK
    
    inflation_rate = 0.02
    discount_rate = 0.06
    debt_ratio = 0.70
    loan_amount = total_capex * debt_ratio

    # ==========================================
    # 2. ΥΠΟΛΟΓΙΣΜΟΣ ΔΟΣΕΩΝ ΔΑΝΕΙΟΥ (2026-2045)
    # ==========================================
    # Φάση 1: 2026-2031 (6 έτη με 4% σε 20ετή βάση)
    r1, n1 = 0.04, 20
    ds1 = loan_amount * (r1 * (1 + r1)**n1) / (((1 + r1)**n1) - 1)

    rem_debt = loan_amount
    for _ in range(2026, 2032):
        interest = rem_debt * r1
        principal = ds1 - interest
        rem_debt -= principal

    # Φάση 2: 2032-2045 (14 έτη)
    r2, n2 = interest_rate_p2, 14
    ds2 = rem_debt * (r2 * (1 + r2)**n2) / (((1 + r2)**n2) - 1)

    # ==========================================
    # 3. ΠΡΟΒΛΕΨΕΙΣ ΤΙΜΩΝ & ΛΕΙΤΟΥΡΓΙΑ (2032-2056)
    # ==========================================
    years_operating = np.arange(2032, 2057)
    df_project = pd.DataFrame({'Year': years_operating})

    # Καμπύλη τιμών αγοράς (Spot Market) με αφετηρία το 2026
    real_points = {2030: 230.0, 2040: 360.0, 2050: 290.0}
    df_full = pd.DataFrame({'Year': np.arange(2026, 2057)})
    df_full['Real_Price_DKK'] = np.nan
    for y, p in real_points.items():
        df_full.loc[df_full['Year'] == y, 'Real_Price_DKK'] = p

    df_full['Real_Price_DKK'] = df_full['Real_Price_DKK'].interpolate(method='linear')
    for y in range(2051, 2057):
        df_full.loc[df_full['Year'] == y, 'Real_Price_DKK'] = df_full.loc[df_full['Year'] == y-1, 'Real_Price_DKK'].values[0] - 7.0

    # Ονομαστικές τιμές Spot με πληθωρισμό από το 2026
    df_full['Nominal_Price_DKK'] = df_full['Real_Price_DKK'] * ((1 + inflation_rate) ** (df_full['Year'] - 2026))
    df_project = df_project.merge(df_full[['Year', 'Nominal_Price_DKK']], on='Year', how='left')

    # OPEX προσαρμοσμένο στον πληθωρισμό από το 2026
    df_project['Annual_OPEX'] = base_annual_opex * ((1 + inflation_rate) ** (df_project['Year'] - 2026))

    # Παραγωγή Ενέργειας (MWh) διαχωρισμένη σε Base (800 MW) και Extra (PPA/Spot)
    capacity_factor = 0.525
    annual_mwh_base_p50 = base_mw * 8760 * capacity_factor * prod_mult
    annual_mwh_extra_p50 = extra_mw * 8760 * capacity_factor * prod_mult
    
    annual_mwh_base_p75 = annual_mwh_base_p50 * 0.90
    annual_mwh_extra_p75 = annual_mwh_extra_p50 * 0.90

    # ==========================================
    # 4. ΕΥΡΕΣΗ STRIKE PRICE (NPV = 0) & DSCR
    # ==========================================
    def eval_sp(strike_price):
        cfd_years = 20
        ppa_years = 10
        
        # --- 4α. Υπολογισμός Εσόδων P50 (για NPV) ---
        # 1. Έσοδα από τα 800 MW (CfD για 20 έτη, Spot μετά)
        prices_base = np.where(np.arange(1, 26) <= cfd_years, strike_price, df_project['Nominal_Price_DKK'].values)
        revenue_base = annual_mwh_base_p50 * prices_base
        
        # 2. Έσοδα από τα Extra MW (PPA για 10 έτη, Spot μετά)
        if extra_mw > 0:
            prices_extra = np.where(np.arange(1, 26) <= ppa_years, ppa_price, df_project['Nominal_Price_DKK'].values)
            revenue_extra = annual_mwh_extra_p50 * prices_extra
        else:
            revenue_extra = 0.0
            
        total_revenue = revenue_base + revenue_extra
        annual_cf = total_revenue - df_project['Annual_OPEX'].values
        
        # NPV υπολογισμένο στο 2026 (t = 0)
        t_years = years_operating - 2026
        npv = -total_capex + np.sum(annual_cf / ((1 + discount_rate) ** t_years))
        
        # --- 4β. Υπολογισμός DSCR P75 (2032-2045: 14 έτη) ---
        p75_rev_base = annual_mwh_base_p75 * strike_price  # 2032-2045 εμπίπτει στα 20 έτη CfD
        if extra_mw > 0:
            # Για τα πρώτα 10 έτη (2032-2041) ισχύει το PPA, για τα επόμενα 4 (2042-2045) ισχύει το Spot
            prices_extra_p75 = np.where(np.arange(1, 15) <= ppa_years, ppa_price, df_project['Nominal_Price_DKK'].iloc[:14].values)
            p75_rev_extra = annual_mwh_extra_p75 * prices_extra_p75
        else:
            p75_rev_extra = 0.0
            
        p75_total_rev = p75_rev_base + p75_rev_extra
        p75_cf = p75_total_rev - df_project['Annual_OPEX'].iloc[:14].values
        min_dscr_p75 = (p75_cf / ds2).min()
        
        return npv, min_dscr_p75

    # Εύρεση του ελάχιστου CfD Strike Price
    res = opt.root_scalar(lambda sp: eval_sp(sp)[0], bracket=[100, 3000], method="brentq")
    opt_sp = res.root
    _, min_dscr = eval_sp(opt_sp)
    
    return opt_sp, min_dscr

# ==========================================
# 5. GRID SEARCH (ΔΙΑΝΥΣΜΑΤΑ PPA & ΕΠΕΚΤΑΣΕΩΝ)
# ==========================================

# 1. Διάνυσμα Τιμών PPA (Πρόσθεσε τις τιμές που θέλεις μέσα στη λίστα, π.χ. [350, 400, 450])
ppa_prices = [300, 350, 400, 450, 766, 900] 

# 2. Διάνυσμα Επιπλέον Ισχύος (ανά 5 Α/Γ των 14 MW)
extra_capacities = [70, 140, 210, 280, 350]

# Εκτέλεση υπολογισμών αν έχεις ορίσει τιμές στο ppa_prices
if len(ppa_prices) > 0:
    results_grid = []
    
    # 1. Υπολογισμός Base Case (0 Extra MW - Auction 1) για σύγκριση
    sp_base, dscr_base = run_auction2_model(extra_mw=0, ppa_price=0)
    results_grid.append({
        "Extra Capacity (MW)": 0,
        "Total Capacity (MW)": 800,
        "PPA Price (DKK/MWh)": "-",
        "CfD Strike Price (DKK/MWh)": round(sp_base, 2),
        "Min DSCR (P75)": round(dscr_base, 2)
    })
    
    # 2. Loop πάνω στα διανύσματα PPA και Capacities
    for extra_mw in extra_capacities:
        for ppa_p in ppa_prices:
            sp, dscr = run_auction2_model(extra_mw=extra_mw, ppa_price=ppa_p)
            results_grid.append({
                "Extra Capacity (MW)": extra_mw,
                "Total Capacity (MW)": 800 + extra_mw,
                "PPA Price (DKK/MWh)": ppa_p,
                "CfD Strike Price (DKK/MWh)": round(sp, 2),
                "Min DSCR (P75)": round(dscr, 2)
            })

    df_results = pd.DataFrame(results_grid)
    print(df_results.to_string(index=False))
else:
    print("Το 'ppa_prices' είναι άδειο. Πρόσθεσε τιμές στη λίστα ppa_prices (π.χ. ppa_prices = [350, 400, 450]) για να τρέξει ο πίνακας!")