import os
import requests

URL = "https://pmvbry-cdn.epfindia.gov.in/wp-content/uploads/2025/10/September-2025.pdf"

os.makedirs("data", exist_ok=True)
r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
r.raise_for_status()
with open("data/epfo_payroll_september_2025.pdf", "wb") as f:
    f.write(r.content)
print(len(r.content))
