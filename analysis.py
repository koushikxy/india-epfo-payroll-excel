import json

import pandas as pd

df = pd.read_csv("payroll_clean.csv")
y = df[df.PeriodType == "Year"]
facts = {}


def add(key, value, code):
    facts[key] = {"value": value, "code": code}


t = y.groupby("FY").NetPayroll.sum()
add("india_by_year", {k: int(v) for k, v in t.items()}, "y.groupby('FY').NetPayroll.sum()")
add("india_2024_25_vs_2022_23_pct", round((t["2024-25"] / t["2022-23"] - 1) * 100, 1), "t['2024-25'] / t['2022-23'] - 1")
add("india_2024_25_vs_2018_19_times", round(t["2024-25"] / t["2018-19"], 2), "t['2024-25'] / t['2018-19']")
add("india_2021_22_vs_2020_21_pct", round((t["2021-22"] / t["2020-21"] - 1) * 100, 1), "t['2021-22'] / t['2020-21'] - 1")

band = y.assign(Young=y.Age.isin(["18-21", "22-25"])).groupby(["FY", "Young"]).NetPayroll.sum().unstack()
young = band[True] / band.sum(axis=1)
add("share_18_25_by_year_pct", {k: round(v * 100, 1) for k, v in young.items()}, "18-21 plus 22-25 / all ages, by year")
over = y[y.Age.isin(["26-28", "29-35", "More than 35"])].groupby("FY").NetPayroll.sum()
add("aged_26_plus_2018_19", int(over["2018-19"]), "26-28 + 29-35 + More than 35, 2018-19")
add("aged_26_plus_2024_25", int(over["2024-25"]), "26-28 + 29-35 + More than 35, 2024-25")
add("aged_18_25_2018_19", int(band.loc["2018-19", True]), "18-21 + 22-25, 2018-19")
add("aged_18_25_2024_25", int(band.loc["2024-25", True]), "18-21 + 22-25, 2024-25")

s = y.pivot_table(index="State", columns="FY", values="NetPayroll", aggfunc="sum")
share = s["2024-25"] / t["2024-25"]
top5 = share.sort_values(ascending=False).head(5)
add("top5_states_2024_25", list(top5.index), "share.sort_values(ascending=False).head(5).index")
add("top5_share_2024_25_pct", round(top5.sum() * 100, 1), "top5.sum()")
add("maharashtra_share_pct", {"2018-19": round(s.loc["Maharashtra", "2018-19"] / t["2018-19"] * 100, 1), "2024-25": round(share["Maharashtra"] * 100, 1)}, "Maharashtra / India")
add("maharashtra_2024_25", int(s.loc["Maharashtra", "2024-25"]), "s.loc['Maharashtra','2024-25']")
chg = s["2024-25"] / s["2022-23"] - 1
add("states_below_peak_count", int((chg < 0).sum()), "count of states with 2024-25 below 2022-23")
add("states_count", int(len(s)), "states and UTs in the EPFO tables")
add("change_from_peak_pct", {k: round(chg[k] * 100, 1) for k in ["Uttar Pradesh", "Odisha", "Telangana", "Jharkhand", "Tamil Nadu", "Andhra Pradesh", "Uttarakhand", "Punjab"]}, "s['2024-25'] / s['2022-23'] - 1")
times = s["2024-25"] / s["2018-19"]
add("times_2018_19", {k: round(times[k], 2) for k in ["Odisha", "Uttar Pradesh", "Haryana", "Maharashtra", "West Bengal"]}, "s['2024-25'] / s['2018-19']")

st = y[y.FY == "2024-25"].pivot_table(index="State", columns="Age", values="NetPayroll", aggfunc="sum")
yshare = (st["18-21"] + st["22-25"]) / st.sum(axis=1)
add("share_18_25_2024_25_by_state_pct", {k: round(yshare[k] * 100, 1) for k in ["Karnataka", "Bihar", "Maharashtra", "Tamil Nadu", "Odisha", "Jharkhand"]}, "(18-21 + 22-25) / all ages, 2024-25")

b = y[(y.State == "Bihar") & (y.Age == "More than 35")].set_index("FY").NetPayroll
add("bihar_over35", {k: int(b[k]) for k in ["2019-20", "2020-21", "2021-22"]}, "Bihar, More than 35")
j = y[(y.State == "Jharkhand") & (y.Age == "More than 35")].set_index("FY").NetPayroll
add("jharkhand_over35", {k: int(j[k]) for k in ["2023-24", "2024-25"]}, "Jharkhand, More than 35")
jh = y[(y.State == "Jharkhand") & (y.Age != "More than 35")].groupby("FY").NetPayroll.sum()
add("jharkhand_change_excl_over35_pct", round((jh["2024-25"] / jh["2022-23"] - 1) * 100, 1), "Jharkhand without More than 35, 2024-25 vs 2022-23")

m = df[df.PeriodType == "Month"].groupby("Period").NetPayroll.sum()
add("apr_jul_2025", {k: int(v) for k, v in m.items()}, "monthly totals Apr-Jul 2025")
add("rows_clean", len(df), "len(payroll_clean.csv)")
json.dump(facts, open("facts.json", "w"), indent=2)
for k, v in facts.items():
    print(k, v["value"])
