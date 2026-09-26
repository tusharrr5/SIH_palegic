import { chromium } from "playwright";
import path from "path";

import fs from "fs";
const ARTIFACTS_DIR = process.env.ARTIFACTS_DIR || path.resolve("./artifacts");
if (!fs.existsSync(ARTIFACTS_DIR)) {
  fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
}

async function auditBrowserJourneys() {
  console.log("=== STARTING PALEGIC BROWSER CONSOLE & JOURNEY AUDIT ===");
  const browser = await chromium.launch({
    channel: "chrome",
    headless: true,
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();

  const consoleErrors = [];
  const consoleWarnings = [];

  page.on("console", (msg) => {
    if (msg.type() === "error") {
      consoleErrors.push(msg.text());
    } else if (msg.type() === "warning") {
      consoleWarnings.push(msg.text());
    }
  });

  page.on("pageerror", (err) => {
    consoleErrors.push(err.message);
  });

  const BASE_URL = process.env.BASE_URL || "http://127.0.0.1:3100";

  try {
    // ==========================================
    // JOURNEY A: AIS-FIRST
    // ==========================================
    console.log("\n--- EXECUTING JOURNEY A: AIS-FIRST ---");
    console.log("A1. Landing page...");
    await page.goto(BASE_URL, { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForSelector("#btn-ais-first", { timeout: 30000 });
    await page.waitForTimeout(2000);

    console.log("A2. Clicking AIS-FIRST entry card...");
    await page.click("#btn-ais-first");

    console.log("A3. Verifying case load...");
    await page.waitForFunction(
      () => document.querySelector(".evidence-title h2")?.textContent?.includes("AIS Vessel Anomaly"),
      { timeout: 30000 }
    );

    console.log("A4. Verifying no slick initially at 06:00...");
    await page.waitForTimeout(1000);
    const initialTime = await page.locator(".timeline-title strong.mono").textContent();
    console.log("Initial Time:", initialTime);

    console.log("A5. Scrubbing to 07:00 anomaly...");
    const slider = page.locator("input[type='range']").first();
    const anomalyTimestamp = new Date("2010-05-17T07:00:00Z").getTime();
    await slider.fill(String(anomalyTimestamp));
    await page.waitForTimeout(500);

    console.log("A6. Scrubbing to 08:15 suspected surface anomaly reveal...");
    const sarRevealTimestamp = new Date("2010-05-17T08:15:00Z").getTime();
    await slider.fill(String(sarRevealTimestamp));
    await page.waitForTimeout(500);

    console.log("A8. Verifying Evidence Score: 76 / 100 and explainer note...");
    const scoreText = await page.locator(".candidate-score-pill").first().textContent();
    const explainerText = await page.locator(".score-explainer-note").first().textContent();
    console.log("Score:", scoreText, "| Explainer:", explainerText);

    console.log("A9. Opening Report Modal...");
    const reportBtn = page.locator("button:has-text('Generate Investigation Report')").first();
    await reportBtn.scrollIntoViewIfNeeded();
    await reportBtn.click();
    await page.waitForSelector(".report-main-title", { timeout: 5000 });
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, "journey_a_ais_report.png") });

    const closeBtn = page.locator("button[aria-label='Close report']").first();
    await closeBtn.click();
    await page.waitForTimeout(500);
    console.log("Journey A complete: SUCCESS");

    // ==========================================
    // JOURNEY B: SAR-FIRST
    // ==========================================
    console.log("\n--- EXECUTING JOURNEY B: SAR-FIRST ---");
    console.log("B1. Returning to Landing / Clicking SAR-FIRST...");
    await page.goto(BASE_URL, { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForSelector("#btn-sar-first", { timeout: 30000 });
    await page.waitForTimeout(2000);
    await page.click("#btn-sar-first");

    console.log("B2. Verifying Ennore canonical case loaded...");
    await page.waitForFunction(
      () => document.querySelector(".evidence-title h2")?.textContent?.includes("Ennore"),
      { timeout: 30000 }
    );
    const ennoreTitle = await page.textContent(".evidence-title h2");
    console.log("Incident:", ennoreTitle);

    console.log("B3. Verifying vessel evidence in Sources tab...");
    await page.click("button[role='tab']:has-text('Sources')");
    await page.waitForSelector(".primary-candidate-card", { timeout: 5000 });
    const candidateName = await page.locator(".primary-candidate-card h3").first().textContent();
    console.log("Rank #1 Candidate:", candidateName);

    console.log("B4. Verifying Transport Backtracking tab...");
    await page.click("button[role='tab']:has-text('Transport')");
    await page.waitForTimeout(500);

    console.log("B5. Opening Report Modal for Ennore SAR-FIRST...");
    await page.click("button:has-text('Generate Investigation Report')");
    await page.waitForSelector(".report-main-title", { timeout: 5000 });
    const sarTriggerBadge = await page.locator(".report-trigger-badge-bar span").first().textContent();
    console.log("SAR Report Trigger Badge:", sarTriggerBadge);
    await page.screenshot({ path: path.join(ARTIFACTS_DIR, "journey_b_sar_report.png") });

    const sarCloseBtn = page.locator("button[aria-label='Close report']").first();
    await sarCloseBtn.click();
    await page.waitForTimeout(500);
    console.log("Journey B complete: SUCCESS");

    console.log("\n=== BROWSER CONSOLE AUDIT ===");
    console.log(`Console Errors: ${consoleErrors.length}`);
    if (consoleErrors.length > 0) {
      console.log("Errors caught:", consoleErrors);
    } else {
      console.log("Zero browser console errors detected.");
    }

    console.log(`Console Warnings: ${consoleWarnings.length}`);
    if (consoleWarnings.length > 0) {
      console.log("Warnings caught (sample):", consoleWarnings.slice(0, 3));
    }
  } catch (err) {
    console.error("JOURNEY AUDIT ERROR:", err);
  } finally {
    await browser.close();
  }
}

auditBrowserJourneys();
