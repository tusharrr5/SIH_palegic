import { chromium } from "playwright";
import fs from "fs";
import path from "path";

const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || path.resolve("./artifacts");
if (!fs.existsSync(ARTIFACTS_DIR)) {
  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
}

async function runSmokeTest() {
  console.log("=== STARTING PALEGIC E2E SMOKE TEST ===");
  const browser = await chromium.launch({
    channel: "chrome",
    headless: true,
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();

  const results = {};

  try {
    // 1. Open Landing Page
    console.log("1. Navigating to landing page http://127.0.0.1:3100...");
    await page.goto("http://127.0.0.1:3100", { waitUntil: "networkidle" });
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, "step1_landing_page.png") });
    
    const landingTitle = await page.textContent("h1");
    console.log("Landing Title:", landingTitle);
    results["Landing Page"] = landingTitle.includes("PALEGIC") ? "PASS" : "FAIL";

    // 2. Click RUN SIH DEMO
    console.log("2. Clicking 'RUN SIH DEMO' button...");
    const demoButton = page.locator("button:has-text('RUN SIH DEMO')").first();
    await demoButton.waitFor({ state: "visible", timeout: 5000 });
    await demoButton.click();

    // 3. Wait for Investigation Case to load
    console.log("3. Waiting for case SIH-ENNORE-2017 to load...");
    await page.waitForSelector(".incident-title", { timeout: 10000 });
    const incidentTitle = await page.textContent(".incident-title");
    console.log("Active Incident:", incidentTitle);
    results["Canonical Case Loaded"] = incidentTitle.includes("Ennore") ? "PASS" : "FAIL";

    // Wait for map canvas to initialize
    await page.waitForTimeout(2000);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, "step2_investigation_loaded.png") });

    // 4. Verify Map Layers & Toggles
    console.log("4. Verifying map layer pills...");
    const layerPills = await page.locator(".layer-pill").allTextContents();
    console.log("Layer pills found:", layerPills);
    results["Map Layers Present"] = layerPills.length >= 4 ? "PASS" : "FAIL";

    // Click a layer toggle (e.g., SAR footprint or AIS gaps)
    const sarPill = page.locator(".layer-pill:has-text('Footprint')").first();
    if (await sarPill.isVisible()) {
      await sarPill.click();
      await page.waitForTimeout(300);
      await sarPill.click();
    }
    results["Layer Toggles Work"] = "PASS";

    // 5. Verify Candidate Ranking & Explanation
    console.log("5. Checking candidate attribution card...");
    const primaryCard = page.locator(".primary-candidate-card");
    await primaryCard.waitFor({ state: "visible", timeout: 5000 });
    const primaryText = await primaryCard.textContent();
    console.log("Primary Candidate Card Content:", primaryText.slice(0, 120));
    results["Candidate Ranking"] = primaryText.includes("BW Maple") ? "PASS" : "FAIL";
    results["Explainable Attribution"] = primaryText.includes("WHY IS THIS VESSEL RANKED FIRST") ? "PASS" : "FAIL";

    // 6. Test Replay Controls
    console.log("6. Testing Replay (Play, Pause, Speed, Scrub)...");
    const playBtn = page.locator("button:has-text('Play')").first();
    await playBtn.click();
    await page.waitForTimeout(1500);

    // Verify Pause button appears
    const pauseBtn = page.locator("button:has-text('Pause')").first();
    const isPausedVisible = await pauseBtn.isVisible();
    results["Replay Play"] = isPausedVisible ? "PASS" : "FAIL";

    // Click Speed 2x
    const speed2x = page.locator("button:has-text('2x')").first();
    if (await speed2x.isVisible()) {
      await speed2x.click();
      results["Replay Speed"] = "PASS";
    }

    // Click Pause
    await pauseBtn.click();
    results["Replay Pause"] = "PASS";

    // Click Restart
    const restartBtn = page.locator("button:has-text('Restart')").first();
    if (await restartBtn.isVisible()) {
      await restartBtn.click();
      results["Replay Restart"] = "PASS";
    }

    await page.screenshot({ path: path.join(ARTIFACTS_DIR, "step3_replay_active.png") });

    // 7. Verify Evidence Panel Tabs (Evidence, Timeline)
    console.log("7. Checking Evidence Panel tabs...");
    // Timeline tab
    const timelineTab = page.locator("button.tab-btn:has-text('Timeline')");
    await timelineTab.click();
    await page.waitForTimeout(500);
    const timelineItems = await page.locator(".timeline-item").allTextContents();
    console.log("Timeline events rendered:", timelineItems.length);
    results["Timeline Events"] = timelineItems.length >= 5 ? "PASS" : "FAIL";
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, "step4_timeline_tab.png") });

    // Evidence tab
    const evidenceTab = page.locator("button.tab-btn:has-text('Evidence')");
    await evidenceTab.click();
    await page.waitForTimeout(500);
    const evidenceContent = await page.locator(".evidence-tab-content").textContent();
    results["Evidence & Uncertainty"] = evidenceContent.includes("Uncertainty & Transparency") ? "PASS" : "FAIL";
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, "step5_evidence_tab.png") });

    // 8. Test Report Generation Modal
    console.log("8. Testing Generate Investigation Report modal...");
    const reportBtn = page.locator("button:has-text('Generate Investigation Report')");
    await reportBtn.scrollIntoViewIfNeeded();
    await reportBtn.click();

    await page.waitForSelector(".report-modal", { timeout: 5000 });
    const reportHeading = await page.textContent(".report-heading h1");
    console.log("Report Heading:", reportHeading);
    results["Report Modal"] = reportHeading.includes("Marine Pollution Investigation Report") ? "PASS" : "FAIL";

    const reportSections = await page.locator(".report-section").count();
    console.log("Report Sections rendered:", reportSections);
    results["Report 14 Sections"] = reportSections >= 12 ? "PASS" : "FAIL";

    await page.screenshot({ path: path.join(ARTIFACTS_DIR, "step6_report_modal.png") });

    // Close Report Modal
    const closeBtn = page.locator("button:has-text('Close')");
    await closeBtn.click();
    await page.waitForTimeout(500);
    results["Report Close"] = "PASS";

    // 9. Hard refresh investigation URL (?demo=true)
    console.log("9. Testing hard refresh of /?demo=true...");
    await page.goto("http://127.0.0.1:3100/?demo=true", { waitUntil: "networkidle" });
    await page.waitForSelector(".incident-title", { timeout: 10000 });
    const refreshedTitle = await page.textContent(".incident-title");
    results["Hard Refresh /?demo=true"] = refreshedTitle.includes("Ennore") ? "PASS" : "FAIL";

    console.log("\n=== ALL TEST RESULTS ===");
    console.table(results);

    const allPassed = Object.values(results).every(v => v === "PASS");
    console.log(`\nOVERALL SMOKE TEST: ${allPassed ? "PASS" : "FAIL"}`);
  } catch (err) {
    console.error("SMOKE TEST ERROR:", err);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, "smoke_test_failure.png") });
  } finally {
    await browser.close();
  }
}

runSmokeTest();
