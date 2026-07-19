import { expect, test } from "@playwright/test";
import { projectileFixture } from "../../src/features/games/fixture";

const conversation = { id: "00000000-0000-4000-8000-000000000001", title: null, status: "active", created_at: "2026-01-01T00:00:00Z" };

test.beforeEach(async ({ page }) => {
  await page.route("**/api/v1/games/demo", route => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(projectileFixture) }));
  await page.route("**/api/v1/conversations", route => route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify(conversation) }));
  await page.addInitScript(() => localStorage.clear());
});

test("forge renders a stable, playable game shell", async ({ page }, testInfo) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: projectileFixture.title })).toBeVisible();
  await expect(page.getByText("Solver verified")).toBeVisible();
  await expect(page.getByRole("button", { name: "Check answer" })).toBeEnabled();
  await page.screenshot({ path: testInfo.outputPath("forge.png"), fullPage: true });
  const box = await page.locator(".game").boundingBox();
  expect(box?.width).toBeGreaterThan(300);
  await expect(page.locator(".world")).toHaveAttribute("viewBox", "0 0 800 430");
  await expect(page.locator(".brand")).toContainText("PHYSICSFORGE");
});
