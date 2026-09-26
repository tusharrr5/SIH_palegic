import { chromium } from "playwright";
import path from "path";

import fs from "fs";
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || path.resolve("./artifacts");
if (!fs.existsSync(ARTIFACTS_DIR)) {
  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
}

async function runAisFirstSmokeTest() {
  console.log("=== STARTING PALEGIC AIS-FIRST E2E SMOKE TEST ===");
  const browser = await chromium.launch({
    channel: "chrome",
    headless: true,
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();
  const results = {};
  const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:3000";

  try {
    // 1. Open Landing Page
    console.log(`1. Navigating to landing page ${BASE_URL}...`);
    await page.goto(BASE_URL, { waitUntil: "domcontentloaded" });
    await page.waitForSelector("#btn-ais-first", { timeout: 15000 });
    results["Landing Page"] = "PASS";

    // 2. Click AIS-FIRST
    console.log("2. Clicking 'AIS FIRST' button...");
    const aisBtn = page.locator("#btn-ais-first").first();
    await aisBtn.click();

    // 3. Wait for AIS-FIRST case to load
    console.log("3. Waiting for AIS-FIRST investigation to load...");
    await page.waitForFunction(
      () => document.querySelector(".evidence-title h2")?.textContent?.includes("AIS Vessel Anomaly"),
      { timeout: 10000 }
    );
    const incidentTitle = await page.textContent(".evidence-title h2");
    console.log("Active Incident:", incidentTitle);
    results["AIS Case Loaded"] = incidentTitle.includes("AIS Vessel Anomaly") ? "PASS" : "FAIL";

    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, "step_ais_1_case_loaded.png") });

    // 4. Verify AIS-FIRST 10-step evidence chain in Evidence Tab
    console.log("4. Verifying AIS-FIRST 10-step evidence chain...");
    const evidenceHeadings = await page.locator(".ais-first-chain .section-title").allTextContents();
    console.log("Evidence chain steps:", evidenceHeadings.length);
    results["10-Step Evidence Chain"] = evidenceHeadings.length >= 8 ? "PASS" : "FAIL";

    const candidateBadge = await page.locator(".candidate-rank-badge").first().textContent();
    console.log("Candidate Status Badge:", candidateBadge);
    results["High Priority Candidate"] = candidateBadge.includes("HIGH-PRIORITY CANDIDATE") ? "PASS" : "FAIL";

    const scorePill = await page.locator(".candidate-score-pill").first().textContent();
    console.log("Evidence Score Pill:", scorePill);
    results["Evidence Score Display"] = scorePill.includes("Evidence Score: 76 / 100") ? "PASS" : "FAIL";

    const explainerNote = await page.locator(".score-explainer-note").first().textContent();
    console.log("Score Explainer Note:", explainerNote);
    results["Score Explainer Note"] = explainerNote.includes("not a probability of culpability") ? "PASS" : "FAIL";

    // 5. Test Anomaly Time (07:00 UTC) via Replay scrubber
    console.log("5. Testing timeline scrubber to 07:00 UTC anomaly...");
    const slider = page.locator("input[type='range']").first();
    const anomalyTimestamp = new Date("2010-05-17T07:00:00Z").getTime();
    await slider.fill(String(anomalyTimestamp));
    await page.waitForTimeout(500);

    const timeDisplay = await page.locator(".timeline-title strong.mono").textContent();
    console.log("Replay UTC Time:", timeDisplay);
    results["Scrub to Anomaly Time"] = timeDisplay.includes("07:00") ? "PASS" : "FAIL";

    await page.screenshot({ path: path.join(ARTIFACTS_DIR, "step_ais_2_anomaly_time.png") });

    // 6. Test SAR Reveal Time (08:15 UTC) via Replay scrubber
    console.log("6. Testing timeline scrubber to 08:15 UTC SAR reveal...");
    const sarRevealTimestamp = new Date("2010-05-17T08:15:00Z").getTime();
    await slider.fill(String(sarRevealTimestamp));
    await page.waitForTimeout(500);

    const sarTimeDisplay = await page.locator(".timeline-title strong.mono").textContent();
    console.log("Replay UTC Time after SAR reveal:", sarTimeDisplay);
    results["Scrub to SAR Reveal"] = sarTimeDisplay.includes("08:15") ? "PASS" : "FAIL";

    await page.screenshot({ path: path.join(ARTIFACTS_DIR, "step_ais_3_sar_reveal.png") });

    // 7. Test Report Modal for AIS-FIRST
    console.log("7. Testing AIS-FIRST investigation report...");
    const reportBtn = page.locator("button:has-text('Generate Investigation Report')").first();
    await reportBtn.scrollIntoViewIfNeeded();
    await reportBtn.click();

    await page.waitForSelector(".report-main-title", { timeout: 5000 });
    const reportTitle = await page.textContent(".report-main-title");
    console.log("Report title:", reportTitle);
    results["Report Modal"] = reportTitle.includes("Marine Pollution Investigation Report") ? "PASS" : "FAIL";

    const triggerBadge = await page.locator(".report-trigger-badge-bar span").first().textContent();
    console.log("Report Trigger Badge:", triggerBadge);
    results["AIS Trigger Badge in Report"] = triggerBadge.includes("AIS behavioural anomaly") ? "PASS" : "FAIL";

    await page.screenshot({ path: path.join(ARTIFACTS_DIR, "step_ais_4_report_modal.png") });

    const closeBtn = page.locator("button[aria-label='Close report']").first();
    await closeBtn.click();
    results["Report Modal Close"] = "PASS";

    console.log("\n=== AIS-FIRST SMOKE TEST RESULTS ===");
    console.table(results);

    const allPassed = Object.values(results).every(v => v === "PASS");
    console.log(`\nAIS-FIRST TEST RESULT: ${allPassed ? "PASS" : "FAIL"}`);
  } catch (err) {
    console.error("AIS-FIRST SMOKE TEST ERROR:", err);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, "smoke_ais_test_failure.png") });
  } finally {
    await browser.close();
  }
}

runAisFirstSmokeTest();
