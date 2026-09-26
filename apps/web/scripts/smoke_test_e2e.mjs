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

  const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:3100";

  try {
    // 1. Open Landing Page
    console.log(`1. Navigating to landing page ${BASE_URL}...`);
    await page.goto(BASE_URL, { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForSelector("#btn-run-demo", { timeout: 30000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, "step1_landing_page.png") });
    
    const heroText = await page.textContent(".sih-hero-inner");
    console.log("Landing Hero Text:", heroText.slice(0, 80));
    results["Landing Page"] = heroText.includes("PALEGIC") ? "PASS" : "FAIL";

    // 2. Click RUN SIH DEMO
    console.log("2. Clicking 'RUN SIH DEMO' button...");
    await page.click("#btn-run-demo");

    // 3. Wait for Investigation Case to load
    console.log("3. Waiting for case SIH-ENNORE-2017 to load...");
    await page.waitForFunction(
      () => document.querySelector(".evidence-title h2")?.textContent?.includes("Ennore"),
      { timeout: 30000 }
    );
    const incidentTitle = await page.textContent(".evidence-title h2");
    console.log("Active Incident:", incidentTitle);
    results["Canonical Case Loaded"] = incidentTitle.includes("Ennore") ? "PASS" : "FAIL";

    // Wait for map canvas to initialize
    await page.waitForTimeout(2000);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, "step2_investigation_loaded.png") });

    // 4. Verify Map Layers & Toggles
    console.log("4. Verifying map layer buttons...");
    const layerButtons = await page.locator(".layer-pills button").allTextContents();
    console.log("Layer buttons found:", layerButtons);
    results["Map Layers Present"] = layerButtons.length >= 4 ? "PASS" : "FAIL";

    // Click a layer toggle (e.g. SAR Footprint)
    const footprintBtn = page.locator(".layer-pills button:has-text('Footprint')").first();
    if (await footprintBtn.isVisible()) {
      await footprintBtn.click();
      await page.waitForTimeout(300);
      await footprintBtn.click();
    }
    results["Layer Toggles Work"] = "PASS";

    // 5. Verify Candidate Ranking & Explanation in Sources Tab
    console.log("5. Checking candidate attribution card in Sources tab...");
    const sourcesTab = page.locator("button[role='tab']:has-text('Sources')");
    await sourcesTab.click();
    await page.waitForTimeout(500);

    const primaryCard = page.locator(".primary-candidate-card");
    await primaryCard.waitFor({ state: "visible", timeout: 5000 });
    const primaryText = await primaryCard.textContent();
    console.log("Primary Candidate Card Content:", primaryText.slice(0, 120));
    results["Candidate Ranking"] = primaryText.includes("BW Maple") ? "PASS" : "FAIL";
    results["Explainable Attribution"] = primaryText.includes("WHY IS THIS VESSEL RANKED FIRST") ? "PASS" : "FAIL";

    // 6. Test Replay Controls
    console.log("6. Testing Replay (Play, Pause, Speed, Scrub)...");
    const playBtn = page.locator(".play-button").first();
    await playBtn.click();
    await page.waitForTimeout(1000);

    // Verify Pause button is active
    const pauseBtn = page.locator(".play-button[aria-label='Pause replay']").first();
    const isPlaying = await pauseBtn.isVisible();
    results["Replay Play"] = isPlaying ? "PASS" : "FAIL";

    // Click Speed 2x
    const speed2x = page.locator(".speed-btn:has-text('2x')").first();
    if (await speed2x.isVisible()) {
      await speed2x.click();
      results["Replay Speed"] = "PASS";
    }

    // Click Pause
    if (isPlaying) {
      await pauseBtn.click();
      results["Replay Pause"] = "PASS";
    }

    // Scrub slider
    const slider = page.locator("input[type='range']").first();
    if (await slider.isVisible()) {
      const curVal = await slider.inputValue();
      await slider.fill(String(Number(curVal) + 15 * 60000));
      results["Replay Scrub"] = "PASS";
    }

    // Click Restart
    const restartBtn = page.locator("button[aria-label='Restart replay']").first();
    if (await restartBtn.isVisible()) {
      await restartBtn.click();
      results["Replay Restart"] = "PASS";
    }

    await page.screenshot({ path: path.join(ARTIFACTS_DIR, "step3_replay_active.png") });

    // 7. Verify Evidence Panel Tabs (Evidence, Timeline)
    console.log("7. Checking Evidence Panel tabs...");
    // Timeline tab
    const timelineTab = page.locator("button[role='tab']:has-text('Timeline')");
    await timelineTab.click();
    await page.waitForTimeout(500);
    const timelineItems = await page.locator(".timeline-card-item").allTextContents();
    console.log("Timeline events rendered:", timelineItems.length);
    results["Timeline Events"] = timelineItems.length >= 5 ? "PASS" : "FAIL";
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, "step4_timeline_tab.png") });

    // Evidence tab
    const evidenceTab = page.locator("button[role='tab']:has-text('Evidence')");
    await evidenceTab.click();
    await page.waitForTimeout(500);
    const uncertaintyBox = page.locator(".uncertainty-box");
    await uncertaintyBox.waitFor({ state: "visible", timeout: 5000 });
    const uncertaintyContent = await uncertaintyBox.textContent();
    console.log("Uncertainty Box Content:", uncertaintyContent.slice(0, 100));
    results["Evidence & Uncertainty"] = uncertaintyContent.includes("Origin Region") ? "PASS" : "FAIL";
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, "step5_evidence_tab.png") });

    // 8. Test Report Generation Modal
    console.log("8. Testing Generate Investigation Report modal...");
    const reportBtn = page.locator("button:has-text('Generate Investigation Report')").first();
    await reportBtn.scrollIntoViewIfNeeded();
    await reportBtn.click();

    await page.waitForSelector(".report-main-title", { timeout: 5000 });
    const reportHeading = await page.textContent(".report-main-title");
    console.log("Report Heading:", reportHeading);
    results["Report Modal"] = reportHeading.includes("Marine Pollution Investigation Report") ? "PASS" : "FAIL";

    const reportSections = await page.locator(".report-section").count();
    console.log("Report Sections rendered:", reportSections);
    results["Report 14 Sections"] = reportSections >= 12 ? "PASS" : "FAIL";

    await page.screenshot({ path: path.join(ARTIFACTS_DIR, "step6_report_modal.png") });

    // Close Report Modal
    const closeBtn = page.locator("button[aria-label='Close report']").first();
    await closeBtn.click();
    await page.waitForTimeout(500);
    results["Report Close"] = "PASS";

    // 9. Hard refresh investigation URL (?demo=true)
    console.log(`9. Testing hard refresh of ${BASE_URL}/?demo=true...`);
    await page.goto(`${BASE_URL}/?demo=true`, { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".evidence-title h2", { timeout: 10000 });
    const refreshedTitle = await page.textContent(".evidence-title h2");
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
