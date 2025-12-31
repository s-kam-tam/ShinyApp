# World Bank Indicators Dashboard (Shiny for Python)

An interactive **Shiny for Python** dashboard for exploring gender-disaggregated financial indicators and macro-development trends using a World Bank–style contextual indicators dataset.

---

## Overview

This application provides three interactive views:

### 1. Comparisons & Wages
- **Grouped bar chart** comparing **women vs. men receiving calls/SMS asking for money (2024)**.
- **Scatter plot** comparing **account balance after pay day (%)** for women vs. men across countries.

### 2. World Poverty Count
- **Time-series line chart** of the **World poverty headcount ratio** (population living under **$2.15/day, 2017 PPP**).
- Interactive **year-range slider**.

### 3. GDP Growth
- **Multi-country GDP growth trend** over time.
- **Scrollable country selector** and **year-range slider** for focused comparisons.

---

## Data

The app loads a local CSV file:


Expected columns:
- `Indicator Name`
- `Indicator Code`
- `Country Name`
- `Disaggregation` (e.g., `female`, `male`)
- `Year`
- `Value`

Basic cleaning is applied:
- String trimming and normalization
- Lower-casing gender disaggregation
- Casting year to integer

---

## Indicators Used

### Tab 1 — Comparisons & Wages
- `con21.1` (female)
- `con21.2` (male)  
Used for the **2024 gender comparison bar chart**

- `fin36b.1`
- `fin36b.2`  
Used for the **women vs. men scatter plot** (pivoted by gender)

### Tab 2 — World Poverty Count
- `SI.POV.DDAY`  
Filtered to `Country Name = "World"`

### Tab 3 — GDP Growth
- `NY.GDP.MKTP.KD.ZG`

---

## Key Features

- Gender and country **checkbox filters**
- **Scrollable country selectors** to keep sidebars compact
- **Year-range sliders** (fixed to **1990–2024**)
- **Reactive data filtering** using `@reactive.calc`
- **Grammar-of-graphics visuals** built with `plotnine` (ggplot-style)

---

## Project Structure

Recommended repository layout:

.
├── app.py
├── Contextual_Indicators.csv
├── README.md
└── requirements.txt


---

## Installation

Create and activate a virtual environment (recommended), then install dependencies:

```bash
pip install -r requirements.txt

#Launch the App
shiny run --reload Gender_app.py
