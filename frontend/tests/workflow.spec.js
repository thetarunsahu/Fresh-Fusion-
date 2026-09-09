// Browser/API contract fixtures only. No demo measurements are shipped in the UI.
import { test, expect } from "@playwright/test";

const authUser = {
  id: 1,
  email: "tester@freshfusion.local",
  full_name: "FreshFusion Tester",
  role: "admin",
  is_active: true,
  created_at: "2026-09-01T09:00:00+00:00",
  last_login_at: null,
};
const a = {
  sample_id: "APP-TEST-A",
  fruit_type: "Apple",
  created_at: "2026-09-01T10:00:00+00:00",
  status: "collecting",
  camera_frames: 0,
  sensor_readings: 0,
};
const b = {
  ...a,
  sample_id: "BAN-TEST-B",
  fruit_type: "Banana",
  created_at: "2026-09-02T10:00:00+00:00",
};
const emptyFusion = {
  freshness_score: 50,
  sensor_score: null,
  vision_score: null,
  components: {
    validation: {
      verdict_ready: false,
      status: "no_fruit",
      views: [],
      views_count: 0,
    },
  },
  label: "waiting-for-fruit",
};
const reportFor = (sample) => ({
  inspection_id: sample.sample_id,
  sample,
  status: "MORE EVIDENCE REQUIRED",
  evidence: { camera: { recent: false }, sensors: { physical_present: false } },
  analysts: {
    vision: { identity: { fruit: sample.fruit_type } },
    sensor: {},
    reference: {},
    multiview: {},
  },
  critic: {
    status: "NEEDS MORE DATA",
    blocking: true,
    supporting_evidence: [],
    missing_evidence: ["Capture three changed viewpoints."],
    contradictions: [],
    warnings: [],
  },
  decision: {
    verdict_ready: false,
    freshness_score: null,
    label: null,
    confidence: null,
    status: "MORE EVIDENCE REQUIRED",
    reason: "Collect real evidence.",
  },
  timeline: [
    {
      id: "created",
      at: sample.created_at,
      kind: "intake",
      title: "Inspection created",
      detail: sample.fruit_type,
    },
  ],
  human_verifications: [],
});

async function authenticate(page) {
  await page.addInitScript(() => {
    localStorage.setItem("freshfusion.auth.token", "playwright-test-token");
  });
}

async function fixtures(page, overrides = {}) {
  const frames = [];
  const sockets = [];
  const reviews = [];
  await authenticate(page);
  await page.routeWebSocket("**/ws/live/**", (socket) => sockets.push(socket));
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (overrides.handle && (await overrides.handle(route, path))) return;
    let payload;
    const id = path.split("/")[4];
    const sample = id === a.sample_id ? a : b;
    if (path === "/api/v1/auth/me") payload = authUser;
    else if (path === "/api/v1/ai/ollama/health")
      payload = {
        available: true,
        model: "gemma3:4b",
        model_installed: true,
        base_url: "http://127.0.0.1:11434",
      };
    else if (path === "/api/v1/health")
      payload = {
        status: "online",
        phone_dashboard: "http://127.0.0.1:5188/phone.html",
        phone_mode: "lan-fallback",
        backend_port: 8000,
        frontend_port: 5188,
        esp32_endpoint: "http://127.0.0.1:8000/api/v1/sensors/readings",
        authentication: { mode: "jwt", device_authentication: "planned" },
      };
    else if (path === "/api/v1/samples/active") payload = overrides.active || b;
    else if (path === "/api/v1/samples") payload = [b, a];
    else if (path.endsWith("/bundle"))
      payload = { sample, sensors: [], images: [], fusion: emptyFusion };
    else if (path.endsWith("/investigation"))
      payload = { ...reportFor(sample), human_verifications: reviews };
    else if (path.endsWith("/verification")) {
      reviews.push({
        id: 1,
        ...request.postDataJSON(),
        created_at: new Date().toISOString(),
      });
      payload = reviews.at(-1);
    } else if (path.endsWith("/stream-frame")) {
      const body = request.postDataBuffer().toString();
      const field = (name) =>
        body.match(new RegExp(`name="${name}"\\r\\n\\r\\n([^\\r]+)`))?.[1];
      frames.push({
        sampleId: field("sample_id"),
        view: field("view"),
        truth: field("ground_truth"),
      });
      payload = {
        sample_id: field("sample_id"),
        physical_validation: { views_count: 1, verdict_ready: false },
        auto_detection: { sample_changed: false },
      };
    } else if (path.endsWith("/validation"))
      payload = {
        datasets: [],
        reference_index: { ready: false, classes: 0, samples: 0 },
        labelled_images: 0,
        human_ground_truth_records: 0,
        human_labelled_inspections: 0,
        model: { status: "not_deployed" },
      };
    else if (path.endsWith("/registry"))
      payload = { datasets: [], reference_index: { ready: false } };
    else payload = {};
    await route.fulfill({ json: payload });
  });
  return { frames, sockets, reviews };
}

test("landing and login remain public while workspace is authenticated", async ({ page }) => {
  await page.route("**/api/v1/**", (route) =>
    route.fulfill({ status: 503, json: { detail: "Backend unavailable" } }),
  );
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Inspect the fruit/ })).toBeVisible();
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Sign in to FreshFusion" })).toBeVisible();
  await page.goto("/#overview");
  await expect(page.getByRole("heading", { name: "Sign in to FreshFusion" })).toBeVisible();
});

test("authenticated workspace exposes final seven protected pages without fabricated results", async ({ page }) => {
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await authenticate(page);
  await page.route("**/api/v1/**", (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/v1/auth/me") return route.fulfill({ json: authUser });
    return route.fulfill({
      status: 503,
      json: { detail: "Backend intentionally unavailable" },
    });
  });
  await page.goto("/#overview");
  await expect(
    page.getByRole("heading", { name: "FreshFusion Investigation Workspace" }),
  ).toBeVisible();
  await expect(
    page.locator(".ffOverviewHero").getByRole("button", { name: "New inspection", exact: true }),
  ).toBeDisabled();
  for (const name of [
    "Live Inspection",
    "Investigation",
    "AI Copilot",
    "Dataset & Validation",
    "History & Evidence",
    "System",
    "Overview",
  ]) {
    await page.getByRole("navigation").getByRole("button", { name, exact: true }).click();
    await expect(
      page.getByRole("navigation").getByRole("button", { name, exact: true }),
    ).toHaveAttribute("aria-current", "page");
  }
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  await page.screenshot({ path: test.info().outputPath("overview-mobile.png"), fullPage: true });
  expect(errors).toEqual([]);
});

test("AI Copilot stays locked until selected inspection has recent live evidence", async ({ page }) => {
  await fixtures(page);
  await page.goto("/#ai");
  await expect(page.getByRole("heading", { name: "Ask the evidence — not a generic chatbot." })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Collect live evidence first." })).toBeVisible();
  await expect(page.getByLabel("Ask FreshFusion AI Copilot")).toBeDisabled();
  await expect(page.getByRole("button", { name: "Ask", exact: true })).toBeDisabled();
  await expect(page.getByText("Gemma 3 ready", { exact: true })).toBeVisible();
});

test("history selection survives polling, late responses and disposed WebSockets", async ({ page }) => {
  let hold = false, release, requested = false;
  const wait = new Promise((resolve) => (release = resolve));
  const { sockets } = await fixtures(page, {
    handle: async (route, path) => {
      if (hold && path === `/api/v1/samples/${b.sample_id}/bundle`) {
        requested = true;
        await wait;
        await route.fulfill({ json: { sample: b, sensors: [], images: [], fusion: emptyFusion } });
        return true;
      }
      return false;
    },
  });
  await page.goto("/#overview");
  await expect(page.locator(".selectedInspection")).toContainText(b.sample_id);
  await expect.poll(() => sockets.length).toBeGreaterThan(0);
  const countB = sockets.filter((socket) => socket.url().includes(b.sample_id)).length;
  hold = true;
  sockets.find((socket) => socket.url().includes(b.sample_id)).send(JSON.stringify({ type: "sensor", data: {} }));
  await expect.poll(() => requested).toBeTruthy();
  await page.getByRole("navigation").getByRole("button", { name: "History & Evidence", exact: true }).click();
  await page
    .locator(".historyGrid .workspacePanel")
    .filter({ hasText: a.sample_id })
    .getByRole("button", { name: "Open investigation" })
    .click();
  await expect(page.locator(".selectedInspection")).toContainText(a.sample_id);
  release();
  await page.waitForTimeout(5600);
  await expect(page.locator(".selectedInspection")).toContainText(a.sample_id);
  await expect(page.locator(".captureBanner")).toContainText(b.sample_id);
  expect(sockets.filter((socket) => socket.url().includes(b.sample_id)).length).toBe(countB);
  await expect(page.getByRole("heading", { name: "Vision Analyst", exact: true })).toBeVisible();
});

test("human ground truth persists separately while the verdict stays locked", async ({ page }) => {
  const { reviews } = await fixtures(page);
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/#investigation");
  await expect(page.getByRole("button", { name: "Accept system assessment" })).toBeDisabled();
  await page.getByLabel("Observed ground truth").selectOption("ripe");
  await page.getByLabel("Observation notes").fill("Browser contract test observation");
  await page.getByRole("button", { name: "Add ground truth" }).click();
  await expect(page.getByRole("status")).toContainText("Human observation saved");
  expect(reviews[0].ground_truth).toBe("ripe");
  await expect(page.getByText("VERDICT LOCKED", { exact: true })).toBeVisible();
  await expect(page.locator(".ffLockedScore strong")).toHaveText("—");
  await page.getByRole("navigation").getByRole("button", { name: "Dataset & Validation", exact: true }).click();
  await expect(page.getByText("NOT YET VALIDATED", { exact: true })).toHaveCount(5);
  await page.screenshot({ path: test.info().outputPath("validation-desktop.png"), fullPage: true });
  expect(errors).toEqual([]);
});

test("phone pauses when the chamber target changes and explicitly re-pairs", async ({ page }) => {
  let active = a;
  const { frames } = await fixtures(page, {
    handle: async (route, path) => {
      if (path === "/api/v1/samples/active") {
        await route.fulfill({ json: active });
        return true;
      }
      return false;
    },
  });
  await page.goto(`/phone.html?sample_id=${a.sample_id}`);
  await expect.poll(() => frames.length, { timeout: 15000 }).toBeGreaterThan(0);
  active = b;
  await expect(page.getByRole("button", { name: "Pair with active inspection" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Start camera", exact: true })).toBeDisabled();
  await page.getByRole("button", { name: "Pair with active inspection" }).click();
  await expect.poll(() => frames.at(-1)?.sampleId, { timeout: 15000 }).toBe(b.sample_id);
  await expect(page).toHaveURL(new RegExp(b.sample_id));
});

test("phone uploads current views and labels after background resume", async ({ page }) => {
  const { frames } = await fixtures(page, { active: a });
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(`/phone.html?sample_id=${a.sample_id}`);
  await expect.poll(() => frames.length, { timeout: 15000 }).toBeGreaterThan(0);
  expect(frames[0]).toMatchObject({ sampleId: a.sample_id, view: "front" });
  await page.getByRole("button", { name: "left", exact: true }).click();
  await page.getByLabel("Dataset label (optional)").selectOption("ripe");
  await expect.poll(() => frames.at(-1)?.view).toBe("left");
  expect(frames.at(-1).truth).toBe("ripe");
  await page.evaluate(() => {
    Object.defineProperty(document, "hidden", { configurable: true, get: () => true });
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await page.getByRole("button", { name: "back", exact: true }).click();
  await page.getByLabel("Dataset label (optional)").selectOption("overripe");
  await page.evaluate(() => {
    Object.defineProperty(document, "hidden", { configurable: true, get: () => false });
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await expect.poll(() => frames.at(-1)?.view).toBe("back");
  expect(frames.at(-1)).toMatchObject({ sampleId: a.sample_id, truth: "overripe" });
  await page.getByRole("button", { name: "Stop", exact: true }).click();
  const count = frames.length;
  await page.waitForTimeout(3000);
  expect(frames.length).toBe(count);
  expect(errors).toEqual([]);
});
