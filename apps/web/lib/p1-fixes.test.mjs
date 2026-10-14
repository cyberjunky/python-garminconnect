import test from "node:test";
import assert from "node:assert";
import { formatActivityWhen } from "./lastActivity.ts";
import { todayBogotaIso } from "./lastUpdated.ts";

test("formatActivityWhen formats local time without 5-hour offset", () => {
  // Test with space separator
  const result1 = formatActivityWhen("2026-10-11 11:11:04");
  assert.match(result1, /11:11/);
  assert.doesNotMatch(result1, /06:11/);
  assert.match(result1, /11/);
  assert.match(result1, /oct/i);

  // Test with ISO 'T' separator
  const result2 = formatActivityWhen("2026-10-11T11:11:04");
  assert.match(result2, /11:11/);
  assert.doesNotMatch(result2, /06:11/);

  // Test falsy input
  assert.strictEqual(formatActivityWhen(null), "—");
  assert.strictEqual(formatActivityWhen(undefined), "—");
  assert.strictEqual(formatActivityWhen(""), "—");
});

test("todayBogotaIso calculates date in America/Bogota timezone", () => {
  // When UTC is 02:00 on Oct 14, in Bogota (UTC-5) it is 21:00 on Oct 13
  const dateAtLateNightUtc = new Date("2026-10-14T02:00:00Z");
  const bogotaDate = todayBogotaIso(dateAtLateNightUtc);
  assert.strictEqual(bogotaDate, "2026-10-13");

  // When UTC is 15:00 on Oct 14, in Bogota it is 10:00 on Oct 14
  const dateAtDayUtc = new Date("2026-10-14T15:00:00Z");
  assert.strictEqual(todayBogotaIso(dateAtDayUtc), "2026-10-14");
});

test("BB change sign formatting logic prevents +-12", () => {
  const formatBb = (bb) => (bb != null ? `${bb > 0 ? "+" : ""}${bb}` : "—");

  assert.strictEqual(formatBb(14), "+14");
  assert.strictEqual(formatBb(-12), "-12");
  assert.strictEqual(formatBb(0), "0");
  assert.strictEqual(formatBb(null), "—");
  assert.strictEqual(formatBb(undefined), "—");
});
