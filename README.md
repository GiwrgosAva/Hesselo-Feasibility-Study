# Feasibility & Economic Analysis: Hesselø Offshore Wind Farm Bidding Strategy

![DTU Course Project](https://img.shields.io/badge/DTU-Feasibility%20Studies%20of%20Energy%20Systems-red)
![License](https://img.shields.io/badge/License-MIT-blue)
![Python/Excel](https://img.shields.io/badge/Tools-Excel%20%7C%20Python-green)

Financial modeling, feasibility analysis, and bidding strategy development for the **Hesselø Offshore Wind Farm** (Denmark) across three distinct government auction mechanisms.

---

## 📌 Project Overview

This project evaluates the commercial, financial, and technical feasibility of developing the Hesselø Offshore Wind Farm in Kattegat, Denmark. Acting as an offshore wind developer, our team performed comprehensive financial modeling, sensitivity analyses, and auction bidding optimization to determine whether and how to bid.

### Key Technical Parameters
* **Location:** Kattegat, Denmark (Hesselø site)
* **Capacity:** 800 MW – 1200 MW (Grid Connection: 1200 MW)
* **Commissioning Year:** 2032 | **Project Lifetime:** 25 Years
* **Turbine Model:** Siemens Gamesa SG 14-236 DD
* **Capacity Factor:** 52.5%
* **Minimum Bankability Metric:** Debt Service Coverage Ratio (DSCR) $\ge 1.2$ at P75

---

## 📊 Auction Strategies & Bidding Summary

We evaluated three separate auction structures to optimize value and manage market risks:

### 1. Auction 1: Pure 2-Sided CfD (Cap: DKK 21.9B)
* **Mechanism:** 20-year two-sided Contract for Difference with annual reference prices.
* **Strike Price Bid:** `[Insert Bid e.g. XXX DKK/MWh]`
* **Expected Total State Support (Real 2026):** `[Insert Value DKK Billion]`

### 2. Auction 2: Hybrid Model (CfD + PPA)
* **Mechanism:** 800 MW under 20-yr CfD + up to 400 MW additional capacity under 10-yr fixed-price PPA (followed by merchant/spot sales).
* **CfD Strike Price:** `[Insert Value DKK/MWh]`
* **PPA Price & Capacity:** `[Insert Value DKK/MWh]` @ `[Insert MW e.g. 400 MW]`
* **Expected Net State Support:** `[Insert Value DKK Billion]`

### 3. Auction 3: Multi-Criteria Auction (Non-Price & ESG Focus)
* **Mechanism:** Weighted scoring combining price (30 pts), environmental design (30 pts), hybrid/PtX operation (20 pts), and social/community investment (20 pts).
* **Offered Strike Price:** `[Insert Value DKK/MWh]`
* **ESG & Sustainability Features Included:**
  * *Environmental:* `[e.g. Recyclable blades, Green steel turbines, Noise mitigation]`
  * *Hybrid setup:* `[e.g. 100 MWe electrolyser capacity paired with 100 MW overplanting]`
  * *Social:* `[e.g. X DKK/MW community fund + Y% coastal community co-ownership]`
* **Total Estimated Auction Score:** `[Insert Score / 100]`

---

## 🛠 Financial Methodology & Risk Analysis

The model computes project Cash Flows, NPV (discounted to 2026), IRR, and Debt Sizing based on project LCOE and CAPEX/OPEX components (turbines, substructures, array/export cables, onshore/offshore substations).

### Sensitivity Analysis
Key risk variables tested:
1. **P75 Wind Resource Uncertainty:** Ensuring DSCR remain above 1.2 under adverse wind conditions.
2. **CAPEX Fluctuation:** Sensitivity to raw material (steel) and supply chain price surges.
3. **Power Market Prices:** Impact of cannibalization and spot price variance post-PPA.

---

## 📂 Repository Structure

```text
├── scripts/
│   ├── auction_1_cfd.py            # Financial model & bidding calculation for Auction 1 (2-sided CfD)
│   ├── sensitivity_auction_1.py    # Sensitivity & risk analysis for Auction 1 (DSCR, CAPEX, P75)
│   └── auction_2_hybrid.py         # Financial model for Auction 2 (Hybrid CfD + PPA)
├── presentation/
│   └── Hesselo_Feasibility_Final_Presentation.pdf
└── README.md

## 🚀 How to Run the Code

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/GiwrgosAva/Hesselo-Feasibility-Study.git](https://github.com/GiwrgosAva/Hesselo-Feasibility-Study.git)
   cd Hesselo-Feasibility-Study
