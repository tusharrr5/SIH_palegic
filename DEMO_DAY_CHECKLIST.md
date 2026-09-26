# PALEGIC SIH 2026 — DEMO-DAY CHECKLIST

**Problem Statement ID:** 26143  
**Team:** Ekatva  
**System:** PALEGIC Explainable Maritime Intelligence  

---

1. **Connect Mac to reliable internet** (Wi-Fi or stable phone hotspot).
2. **Connect charger** to prevent power throttling or standby during demo.
3. **Disable sleep** (`System Settings > Energy Saver` or run `caffeinate -d` in a separate terminal).
4. **Start database** (PostgreSQL 17 / PostGIS):
   ```bash
   brew services start postgresql@17
   ```
5. **Start PALEGIC demo services**:
   ```bash
   ./scripts/start_sih_demo.sh
   ```
6. **Start Cloudflare tunnel** (handled automatically by `start_sih_demo.sh`).
7. **Copy current public URL** displayed in terminal or in `CURRENT_DEMO_URL.txt`:
   ```bash
   cat CURRENT_DEMO_URL.txt
   ```
8. **Open URL in Incognito/Private window**:
   ```text
   <PUBLIC_URL>/?demo=true
   ```
9. **Test AIS-FIRST**:
   - Click **AIS FIRST** on landing hero.
   - Verify initial state: normal surveillance at 06:00 UTC (no slick displayed).
   - Scrub timeline to 07:00 UTC (vessel anomaly detected).
   - Scrub timeline to 08:15 UTC (targeted satellite verification reveals suspected surface anomaly).
   - Check Evidence Score: **76 / 100** (explicitly labeled: decision-support score, not probability).
   - Open **Investigation Report** and check 10-step provenance chain.
10. **Test SAR-FIRST**:
    - Click **RUN SIH DEMO** / **SAR FIRST** (Ennore Port 2017 case).
    - Verify surface signal $\rightarrow$ candidate vessels ranked (BW Maple rank #1, score 51/100).
    - Verify drift backtracking and 14-section report modal.
11. **Keep terminal/tunnel running during presentation**:
    - Do not close the terminal running the demo or tunnel until the session ends.
    - To cleanly stop all services when finished:
      ```bash
      ./scripts/stop_sih_demo.sh
      ```
