import os
import pandas as pd
from shiny import App, ui, render, reactive
from plotnine import (
    ggplot,
    aes,
    geom_col,
    geom_line,
    geom_point,
    theme_minimal,
    labs,
    theme,
    element_text,
    scale_x_continuous,
    coord_cartesian,
)

# -----------------------------------------------------------
# LOAD DATA
# -----------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "Contextual_Indicators.csv")
df = pd.read_csv(DATA_PATH)

# Basic cleaning
df["Indicator Name"] = df["Indicator Name"].astype(str).str.strip()
df["Indicator Code"] = df["Indicator Code"].astype(str).str.strip()
df["Country Name"] = df["Country Name"].astype(str).str.strip()
df["Disaggregation"] = df["Disaggregation"].astype(str).str.strip().str.lower()
df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype(int)


# Countries in con21.1 (women) and con21.2 (men) in 2024
cmp_df = df[
    (df["Year"] == 2024)
    & (df["Indicator Code"].isin(["con21.1", "con21.2"]))
]
cmp_countries = sorted(cmp_df["Country Name"].unique().tolist())

# World poverty range (SI.POV.DDAY, World)
poverty_df = df[
    (df["Indicator Code"] == "SI.POV.DDAY")
    & (df["Country Name"] == "World")
].copy()

POV_MIN_YEAR = 1990
POV_MAX_YEAR = 2024

# GDP years (for NY.GDP.MKTP.KD.ZG)
gdp_df = df[df["Indicator Code"] == "NY.GDP.MKTP.KD.ZG"].copy()
# Fixed GDP slider year range
GDP_MIN_YEAR = 1990
GDP_MAX_YEAR = 2024


# -----------------------------------------------------------
# UI LAYOUT
# -----------------------------------------------------------
app_ui = ui.page_navbar(

    # -------------------------------------------------------
    # TAB 1 — COMPARISON + SCATTER PLOT
    # -------------------------------------------------------
    ui.nav_panel(
        "Comparisons & Wages",

        ui.layout_sidebar(
            ui.sidebar(
                ui.h3("Filters"),

                # Gender filter
                ui.input_checkbox_group(
                    "cmp_gender",
                    "Select gender:",
                    choices=["female", "male"],
                    selected=["female", "male"],
                ),

                ui.br(),

                # Scrollable country list
                ui.div(
                    ui.input_checkbox_group(
                        "cmp_countries",
                        "Select countries):",
                        choices=cmp_countries,
                        selected=[],
                    ),
                    style=(
                        "max-height: 250px; overflow-y: scroll; "
                        "border: 1px solid #ccc; padding: 6px; border-radius: 5px;"
                    ),
                ),
            ),

            ui.div(
                ui.h3("Comparison of Women vs Men Receiving Calls/SMS asking for money (2024)"),
                ui.output_plot("cmp_plot"),

                ui.hr(),
                ui.h3("Distribution of Account Balance after Pay Day % (Men vs Women)"),
                ui.output_plot("fin_scatter"),
            ),
        ),
    ),

    # -------------------------------------------------------
    # TAB 2 — WORLD POVERTY HEADCOUNT
    # -------------------------------------------------------
    ui.nav_panel(
        "World Poverty Count",

        ui.layout_sidebar(
            ui.sidebar(
                ui.h3("World Poverty Headcount"),
                ui.markdown(
                    """
This graph shows the proportion of the population living on less than $2.15/day (2017 PPP)
for the world based on World Bank data (Indicator Code: SI.POV.DDAY).
                    """
                ),
            ),

            ui.div(
                ui.output_plot("poverty_plot"),

                ui.input_slider(
                    "poverty_years",
                    "Select year range:",
                    min=POV_MIN_YEAR,
                    max=POV_MAX_YEAR,
                    value=(POV_MIN_YEAR, POV_MAX_YEAR),
                ),
            ),
        ),
    ),

    # -------------------------------------------------------
    # TAB 3 — GDP GROWTH
    # -------------------------------------------------------
    ui.nav_panel(
        "GDP Growth",

        ui.layout_sidebar(
            ui.sidebar(
                ui.h3("Annual GDP Growth (%)"),

                # Scrollable country selector
                ui.div(
                    ui.input_checkbox_group(
                        "gdp_countries",
                        "Select countries:",
                        choices=sorted(
                            df.loc[
                                df["Indicator Code"] == "NY.GDP.MKTP.KD.ZG",
                                "Country Name",
                            ]
                            .unique()
                            .tolist()
                        ),
                        selected=[],
                    ),
                    style=(
                        "max-height: 250px; overflow-y: scroll; "
                        "border: 1px solid #ccc; padding: 6px; border-radius: 5px;"
                    ),
                ),

                ui.br(),

                # Year slider for GDP
                ui.input_slider(
                    "gdp_years",
                    "Select year range:",
                    min=GDP_MIN_YEAR,
                    max=GDP_MAX_YEAR,
                    value=(GDP_MIN_YEAR, GDP_MAX_YEAR),
                ),
            ),

            ui.div(
                ui.h3("Annual GDP Growth (%)"),
                ui.output_plot("gdp_plot"),
            ),
        ),
    ),

    title="World Bank Indicators Dashboard",
)

# -----------------------------------------------------------
# SERVER LOGIC
# -----------------------------------------------------------
def server(input, output, session):

    # -------------------------------------------------------
    # TAB 1 — COMPARISON DATA (SCAM CALLS)
    # -------------------------------------------------------
    @reactive.calc
    def cmp_filtered():
        d = df[
            (df["Indicator Code"].isin(["con21.1", "con21.2"]))
            & (df["Year"] == 2024)
        ].copy()

        # Gender filter
        genders = input.cmp_gender()
        if genders:
            d = d[d["Disaggregation"].isin(genders)]

        # Country filter
        countries = input.cmp_countries()
        if countries:
            d = d[d["Country Name"].isin(countries)]

        return d

    @output
    @render.plot
    def cmp_plot():
        d = cmp_filtered()
        if d.empty:
            return None

        d["GenderLabel"] = d["Disaggregation"].str.title()

        p = (
            ggplot(d, aes(x="Country Name", y="Value", fill="GenderLabel"))
            + geom_col(position="dodge")
            + theme_minimal()
            + labs(
                x="Country",
                y="Percentage of population (%)",
                fill="Gender",
            )
            + theme(
                axis_text_x=element_text(rotation=90, size=6),
                plot_title=element_text(ha="center", size=12),
            )
        )
        return p.draw()

    # -------------------------------------------------------
    # TAB 1 — SCATTER PLOT (FIN36B.1 vs FIN36B.2)
    # -------------------------------------------------------
    @reactive.calc
    def fin_scatter_data():
        d = df[df["Indicator Code"].isin(["fin36b.1", "fin36b.2"])].copy()

        pivot = (
            d.pivot_table(
                index="Country Name",
                columns="Disaggregation",
                values="Value",
                aggfunc="mean",
            )
            .reset_index()
            .dropna(subset=["female", "male"])
        )
        return pivot

    @output
    @render.plot
    def fin_scatter():
        d = fin_scatter_data()
        if d.empty:
            return None

        p = (
            ggplot(d, aes(x="female", y="male"))
            + geom_point(color="steelblue", size=3)
            + theme_minimal()
            + labs(
                title="Account Balance after Pay Day",
                x="Women (% age 15+)",
                y="Men (% age 15+)",
            )
        )
        return p.draw()

    # -------------------------------------------------------
    # TAB 2 — POVERTY TREND (WORLD)
    # -------------------------------------------------------
    @reactive.calc
    def poverty_filtered():
        d = df[
            (df["Indicator Code"] == "SI.POV.DDAY")
            & (df["Country Name"] == "World")
        ].copy()

        if d.empty:
            return d

        yr_min, yr_max = input.poverty_years()
        d = d[(d["Year"] >= yr_min) & (d["Year"] <= yr_max)]
        d = d.sort_values("Year")
        return d

    @output
    @render.plot
    def poverty_plot():
        d = poverty_filtered()
        if d.empty:
            return None

        p = (
            ggplot(d, aes(x="Year", y="Value"))
            + geom_line(color="steelblue", size=1.2)
            + theme_minimal()
            + labs(
                title ="World Poverty Headcount Ratio",
                x="Year",
                y="Poverty headcount ratio (% of population)",
            )
            + scale_x_continuous(
                breaks=list(range(d["Year"].min(), d["Year"].max() + 1, 1))
            )
            + coord_cartesian(ylim=(0, None))  # y-axis starts at 0
        )
        return p.draw()

    # -------------------------------------------------------
    # TAB 3 — GDP GROWTH TREND
    # -------------------------------------------------------
    @reactive.calc
    def gdp_filtered():
        d = df[df["Indicator Code"] == "NY.GDP.MKTP.KD.ZG"].copy()

        # Year filter
        yr_min, yr_max = input.gdp_years()
        d = d[(d["Year"] >= yr_min) & (d["Year"] <= yr_max)]

        # Country filter
        countries = input.gdp_countries()
        if countries:
            d = d[d["Country Name"].isin(countries)]

        return d.sort_values(["Country Name", "Year"])

    @output
    @render.plot
    def gdp_plot():
        d = gdp_filtered()
        if d.empty:
            return None

        p = (
            ggplot(d, aes(x="Year", y="Value", color="Country Name"))
            + geom_line(size=1.2)
            + theme_minimal()
            + labs(
                x="Year",
                y="GDP Growth (%)",
                color="Country",
            )
            + scale_x_continuous(
                breaks=list(range(d["Year"].min(), d["Year"].max() + 1, 1))
            )
        )
        return p.draw()


# -----------------------------------------------------------
# APP
# -----------------------------------------------------------
app = App(app_ui, server)




# shiny run --reload --launch-browser Gender_app.py

