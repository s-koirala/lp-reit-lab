"""lp-reit-lab — interactive property screener (v0, SYNTHETIC data).

Progressive disclosure for a stats-literate non-specialist (research memo §7-8):
filters -> ranked go/no-go shortlist -> map -> per-property drill-down.

Run:  uv run streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import dataclasses  # noqa: E402
import math  # noqa: E402

import folium  # noqa: E402
import pandas as pd  # noqa: E402
import plotly.graph_objects as go  # noqa: E402
import streamlit as st  # noqa: E402
from streamlit_folium import st_folium  # noqa: E402

from lp_reit_lab import scoring  # noqa: E402
from lp_reit_lab.config import Assumptions, load_scoring  # noqa: E402
from lp_reit_lab.finance.evaluate import evaluate_property  # noqa: E402
from lp_reit_lab.finance.sensitivity import tornado  # noqa: E402
from lp_reit_lab.synthetic import SYNTHETIC_NOTICE, generate_listings  # noqa: E402

VERDICT_COLOR = {"GO": "#1a9850", "WATCH": "#fd8d3c", "NO-GO": "#d73027"}
SCORING = load_scoring()
BASE = Assumptions.load()

st.set_page_config(page_title="lp-reit-lab screener", layout="wide")


@st.cache_data
def _listings(n: int, seed: int) -> pd.DataFrame:
    return generate_listings(n, seed)


def sidebar_assumptions() -> Assumptions:
    """Sidebar sliders -> a modified Assumptions (the three load-bearing levers first)."""
    st.sidebar.header("Assumptions")
    st.sidebar.caption("Forward levers underwriting scrutinizes most (memo §7).")
    rent_growth = st.sidebar.slider("Rent growth (annual)", 0.0, 0.08,
                                    BASE.rent_growth_annual, 0.005)
    exit_spread = st.sidebar.slider("Exit-cap spread over going-in", 0.0, 0.03,
                                    BASE.exit_cap_spread, 0.0025)
    discount = st.sidebar.slider("Discount rate", 0.04, 0.14, BASE.discount_rate, 0.005)
    rate = st.sidebar.slider("Mortgage rate (annual)", 0.04, 0.10,
                             BASE.mortgage_rate_annual, 0.0025)
    down = st.sidebar.slider("Down payment fraction", 0.20, 0.50, BASE.down_payment_fraction, 0.05)
    vacancy = st.sidebar.slider("Vacancy rate", 0.0, 0.15, BASE.vacancy_rate, 0.01)
    hold = st.sidebar.slider("Hold (years)", 3, 15, BASE.hold_years, 1)
    return dataclasses.replace(
        BASE, rent_growth_annual=rent_growth, exit_cap_spread=exit_spread,
        discount_rate=discount, mortgage_rate_annual=rate,
        down_payment_fraction=down, vacancy_rate=vacancy, hold_years=hold,
    )


def build_results(listings: pd.DataFrame, a: Assumptions) -> pd.DataFrame:
    """Evaluate + score every listing under the current assumptions."""
    records = []
    for row in listings.itertuples(index=False):
        res = evaluate_property(float(row.price), float(row.est_monthly_rent),
                                float(row.hoa_monthly), a)
        sc = scoring.score_property(res, SCORING)
        records.append({
            "property_id": row.property_id, "neighborhood": row.neighborhood,
            "beds": row.beds, "price": row.price, "rent": row.est_monthly_rent,
            "hoa": row.hoa_monthly, "latitude": row.latitude, "longitude": row.longitude,
            "cap_rate": res["going_in_cap"], "cash_on_cash": res["cash_on_cash"],
            "monthly_cash_flow": res["monthly_cash_flow"], "dscr": res["dscr"],
            "levered_irr": res["levered_irr"], "equity_multiple": res["equity_multiple"],
            "composite": sc["composite_score"], "verdict": sc["verdict"],
        })
    return pd.DataFrame(records).sort_values("composite", ascending=False)


def render_map(results: pd.DataFrame) -> None:
    """Folium map on free OSM tiles, markers coloured by verdict."""
    if results.empty:
        st.info("No properties match the filters.")
        return
    center = [results["latitude"].mean(), results["longitude"].mean()]
    fmap = folium.Map(location=center, zoom_start=13, tiles="OpenStreetMap")
    for row in results.itertuples(index=False):
        folium.CircleMarker(
            location=[row.latitude, row.longitude], radius=6,
            color=VERDICT_COLOR[row.verdict], fill=True, fill_opacity=0.85,
            popup=(f"{row.property_id} · {row.neighborhood}<br>${row.price:,.0f} · "
                   f"cap {row.cap_rate:.1%} · CoC {row.cash_on_cash:.1%}<br>{row.verdict}"),
        ).add_to(fmap)
    st_folium(fmap, height=440, use_container_width=True)


def render_tornado(price: float, rent: float, hoa: float, a: Assumptions) -> None:
    """Levered-IRR sensitivity to the load-bearing assumptions."""
    specs = [
        ("exit_cap_spread", max(0.0, a.exit_cap_spread - 0.01), a.exit_cap_spread + 0.01),
        ("rent_growth_annual", max(0.0, a.rent_growth_annual - 0.02), a.rent_growth_annual + 0.02),
        ("mortgage_rate_annual", a.mortgage_rate_annual - 0.01, a.mortgage_rate_annual + 0.01),
        ("vacancy_rate", max(0.0, a.vacancy_rate - 0.03), a.vacancy_rate + 0.05),
    ]
    tdf = tornado(price, rent, hoa, a, specs, metric="levered_irr")
    fig = go.Figure(go.Bar(
        x=tdf["swing"], y=tdf["variable"], orientation="h",
        marker_color="#4575b4",
    ))
    fig.update_layout(title="Levered-IRR sensitivity (swing)", height=300,
                      xaxis_tickformat=".1%", margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)


def render_drilldown(results: pd.DataFrame, listings: pd.DataFrame, a: Assumptions) -> None:
    """Per-property scorecard, pro forma, and sensitivity."""
    pid = st.selectbox("Property", results["property_id"].tolist())
    src = listings.loc[listings["property_id"] == pid].iloc[0]
    res = evaluate_property(float(src["price"]), float(src["est_monthly_rent"]),
                            float(src["hoa_monthly"]), a)
    sc = scoring.score_property(res, SCORING)

    st.markdown(f"### {pid} — {src['neighborhood']} · {src['beds']}BR · "
                f"{src['sqft']:,} sqft · built {src['year_built']}")
    st.markdown(f"**Verdict:** :{_verdict_badge(sc['verdict'])}")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Monthly cash flow", f"${res['monthly_cash_flow']:,.0f}")
    c2.metric("Cash-on-cash", f"{res['cash_on_cash']:.1%}")
    c3.metric("Going-in cap", f"{res['going_in_cap']:.2%}")
    c4.metric("Levered IRR", _fmt_pct(res["levered_irr"]))
    c5.metric("DSCR", f"{res['dscr']:.2f}")

    left, right = st.columns(2)
    with left:
        st.markdown("**Pro forma (levered)**")
        proforma = res["proforma"].copy()
        for col in ["gross_potential_rent", "egi", "opex", "noi",
                    "debt_service", "levered_cash_flow"]:
            proforma[col] = proforma[col].map(lambda v: f"${v:,.0f}")
        st.dataframe(proforma, hide_index=True, use_container_width=True)
        st.caption(f"Equity in ${res['equity_invested']:,.0f} · exit cap "
                   f"{res['exit_cap']:.2%} · sale ${res['sale_price']:,.0f} · "
                   f"equity multiple {res['equity_multiple']:.2f}x")
    with right:
        render_tornado(float(src["price"]), float(src["est_monthly_rent"]),
                       float(src["hoa_monthly"]), a)
        if bool(src.get("pre_1980_assessment_risk", False)):
            st.warning("Pre-1980 building — elevated special-assessment risk (memo §4.5).")


def _verdict_badge(verdict: str) -> str:
    return {"GO": "green[GO]", "WATCH": "orange[WATCH]", "NO-GO": "red[NO-GO]"}[verdict]


def _fmt_pct(value: float) -> str:
    return "n/a" if math.isnan(value) else f"{value:.1%}"


def main() -> None:
    st.title("lp-reit-lab — Lincoln Park investment screener")
    st.caption(SYNTHETIC_NOTICE)
    st.caption("Market-demand analysis only — never tenant screening/steering "
               "(Fair Housing Act §3604; research memo §3).")

    a = sidebar_assumptions()
    st.sidebar.header("Data")
    n = st.sidebar.slider("Synthetic listings", 50, 400, 150, 50)
    seed = st.sidebar.number_input("Seed", value=20260605, step=1)
    listings = _listings(int(n), int(seed))

    st.sidebar.header("Filters")
    hoods = st.sidebar.multiselect("Neighborhood", sorted(listings["neighborhood"].unique()),
                                   default=sorted(listings["neighborhood"].unique()))
    beds = st.sidebar.multiselect("Bedrooms", sorted(listings["beds"].unique()), default=[3])
    price_hi = int(listings["price"].max())
    price_cap = st.sidebar.slider("Max price", 200_000, price_hi, price_hi, 25_000)
    min_coc = st.sidebar.slider("Min cash-on-cash", -0.10, 0.15, -0.10, 0.01)
    max_hoa = st.sidebar.slider("Max HOA", 150, int(listings["hoa_monthly"].max()),
                                int(listings["hoa_monthly"].max()), 50)

    results = build_results(listings, a)
    mask = (
        results["neighborhood"].isin(hoods) & results["beds"].isin(beds)
        & (results["price"] <= price_cap) & (results["cash_on_cash"] >= min_coc)
        & (results["hoa"] <= max_hoa)
    )
    results = results[mask]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Candidates", len(results))
    k2.metric("GO", int((results["verdict"] == "GO").sum()))
    med_cap = _fmt_pct(results["cap_rate"].median()) if not results.empty else "n/a"
    med_coc = _fmt_pct(results["cash_on_cash"].median()) if not results.empty else "n/a"
    k3.metric("Median cap", med_cap)
    k4.metric("Median CoC", med_coc)

    tab_list, tab_map, tab_detail = st.tabs(["Shortlist", "Map", "Property detail"])
    with tab_list:
        show = results[["property_id", "neighborhood", "beds", "price", "rent", "hoa",
                        "cap_rate", "cash_on_cash", "monthly_cash_flow", "dscr",
                        "levered_irr", "equity_multiple", "verdict"]]
        st.dataframe(
            show.style.format({
                "price": "${:,.0f}", "rent": "${:,.0f}", "hoa": "${:,.0f}",
                "cap_rate": "{:.2%}", "cash_on_cash": "{:.1%}",
                "monthly_cash_flow": "${:,.0f}", "dscr": "{:.2f}",
                "levered_irr": "{:.1%}", "equity_multiple": "{:.2f}x",
            }).map(lambda v: f"color:{VERDICT_COLOR.get(v, '#000')}", subset=["verdict"]),
            hide_index=True, use_container_width=True, height=460,
        )
    with tab_map:
        render_map(results)
    with tab_detail:
        if results.empty:
            st.info("No properties match the filters.")
        else:
            render_drilldown(results, listings, a)


main()
