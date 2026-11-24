import pymupdf
import pandas as pd

PDF = "data/epfo_payroll_september_2025.pdf"

STATES = {
    "ANDAMAN AND NICOBAR ISLANDS": ("Andaman and Nicobar Islands", "South"),
    "ANDHRA PRADESH": ("Andhra Pradesh", "South"),
    "ARUNACHAL PRADESH": ("Arunachal Pradesh", "North East"),
    "ASSAM": ("Assam", "North East"),
    "BIHAR": ("Bihar", "East"),
    "CHANDIGARH": ("Chandigarh", "North"),
    "CHATTISGARH": ("Chhattisgarh", "Central"),
    "DELHI": ("Delhi", "North"),
    "GOA": ("Goa", "West"),
    "GUJARAT": ("Gujarat", "West"),
    "HARYANA": ("Haryana", "North"),
    "HIMACHAL PRADESH": ("Himachal Pradesh", "North"),
    "JAMMU AND KASHMIR": ("Jammu and Kashmir", "North"),
    "JHARKHAND": ("Jharkhand", "East"),
    "KARNATAKA": ("Karnataka", "South"),
    "KERALA": ("Kerala", "South"),
    "LADAKH": ("Ladakh", "North"),
    "MADHYA PRADESH": ("Madhya Pradesh", "Central"),
    "MAHARASHTRA": ("Maharashtra", "West"),
    "MANIPUR": ("Manipur", "North East"),
    "MEGHALAYA": ("Meghalaya", "North East"),
    "MIZORAM": ("Mizoram", "North East"),
    "NAGALAND": ("Nagaland", "North East"),
    "ORISSA": ("Odisha", "East"),
    "PUNJAB": ("Punjab", "North"),
    "RAJASTHAN": ("Rajasthan", "North"),
    "TAMIL NADU": ("Tamil Nadu", "South"),
    "TELANGANA": ("Telangana", "South"),
    "TRIPURA": ("Tripura", "North East"),
    "UTTAR PRADESH": ("Uttar Pradesh", "North"),
    "UTTARAKHAND": ("Uttarakhand", "North"),
    "WEST BENGAL": ("West Bengal", "East"),
}
MONTHS = {"Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12, "Jan": 1, "Feb": 2, "Mar": 3}


def period(label):
    label = " ".join(label.split())
    if label.startswith("2017-18"):
        return "2017-18 (Sep-Mar)", "2017-18", "Part year"
    if label[:3] in MONTHS:
        y = 2000 + int(label[-2:])
        fy = f"{y}-{str(y + 1)[2:]}" if MONTHS[label[:3]] >= 4 else f"{y - 1}-{str(y)[2:]}"
        return f"{label[:3]} {y}", fy, "Month"
    return label, label, "Year"


doc = pymupdf.open(PDF)
rows, subtotals = [], []
for page in doc:
    for t in page.find_tables().tables:
        data = t.extract()
        cells = [c for r in data for c in r if isinstance(c, str)]
        age = next((c.split(":", 1)[1].strip() for c in cells if c.startswith("Age Bucket:")), None)
        heads = [i for i, r in enumerate(data) if r[0] == "State"]
        if not age or not heads:
            continue
        header = data[heads[0]]
        for r in data[heads[0] + 1:]:
            name = (r[0] or "").strip()
            if not name or name.startswith("Page"):
                continue
            for h, v in zip(header[1:], r[1:]):
                label, fy, kind = period(h)
                rec = {"Age": age, "Period": label, "FY": fy, "PeriodType": kind, "Value": int(v)}
                if name in ("SUB TOTAL", "Grand Total"):
                    if name == "SUB TOTAL":
                        subtotals.append(rec)
                    continue
                rec["SourceName"] = name
                rows.append(rec)

df = pd.DataFrame(rows)
df["State"] = df.SourceName.map(lambda s: STATES[s][0])
df["Region"] = df.SourceName.map(lambda s: STATES[s][1])
df = df.rename(columns={"Value": "NetPayroll"})
df = df[["FY", "Period", "PeriodType", "SourceName", "State", "Region", "Age", "NetPayroll"]]
df.to_csv("payroll_clean.csv", index=False)

p1 = doc[0].find_tables().tables[0].extract()
hdr = [" ".join((c or "").split()) for c in p1[[i for i, r in enumerate(p1) if r[0] and r[0].startswith("Month")][0]]]
ctl = []
for r in p1:
    lab = " ".join((r[0] or "").split())
    if lab[:2] == "20" or lab[:3] in MONTHS:
        for h, v in zip(hdr[1:7], r[1:7]):
            ctl.append({"Period": lab, "Age": h, "AllIndia": int(v)})
ctl = pd.DataFrame(ctl)
ctl["Period"] = ctl.Period.map(lambda s: period(s.replace("-20", "-") if s[:3] in MONTHS else s)[0])
mine = df.groupby(["Period", "Age"]).NetPayroll.sum().rename("SumOfStates")
sub = pd.DataFrame(subtotals).groupby(["Period", "Age"]).Value.sum().rename("SubTotalRow")
chk = ctl.set_index(["Period", "Age"]).join(mine).join(sub)
chk["Diff"] = chk.SumOfStates - chk.AllIndia
chk.reset_index().to_csv("control_check.csv", index=False)
print(chk[chk.Diff != 0])
print(len(df), "rows,", df.State.nunique(), "states,", df.Period.nunique(), "periods,", df.Age.nunique(), "age groups")
