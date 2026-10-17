import test from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, "..");

test("apps/web/package.json y package-lock.json tienen version 0.4.0-rc.2", () => {
  const pkgPath = path.join(webRoot, "package.json");
  const lockPath = path.join(webRoot, "package-lock.json");

  const pkg = JSON.parse(fs.readFileSync(pkgPath, "utf-8"));
  assert.strictEqual(pkg.version, "0.4.0-rc.2", "package.json debe tener version 0.4.0-rc.2");

  const lock = JSON.parse(fs.readFileSync(lockPath, "utf-8"));
  assert.strictEqual(lock.version, "0.4.0-rc.2", "package-lock.json raiz debe tener version 0.4.0-rc.2");
  assert.ok(lock.packages && lock.packages[""], "package-lock.json debe tener entrada packages['']");
  assert.strictEqual(
    lock.packages[""].version,
    "0.4.0-rc.2",
    "package-lock.json packages[''] debe tener version 0.4.0-rc.2"
  );
});

test("apps/web/CHANGELOG.md cubre 0.1.0, 0.2.0, 0.3.0, 0.4.0-rc.1 y 0.4.0-rc.2 con alcance integral del stack", () => {
  const changelogPath = path.join(webRoot, "CHANGELOG.md");
  assert.ok(fs.existsSync(changelogPath), "apps/web/CHANGELOG.md debe existir");

  const content = fs.readFileSync(changelogPath, "utf-8");

  // Cobertura integral del stack
  assert.match(content, /Tri-Coach/i);
  assert.match(content, /collector/i);
  assert.match(content, /GitHub Actions/i);
  assert.match(content, /Supabase/i);

  // Versiones
  assert.match(content, /\[0\.4\.0-rc\.2\]/);
  assert.match(content, /\[0\.4\.0-rc\.1\]/);
  assert.match(content, /\[0\.3\.0\]/);
  assert.match(content, /\[0\.2\.0\]/);
  assert.match(content, /\[0\.1\.0\]/);

  // Referencias historicas y actual
  assert.match(content, /b13aa16/);
  assert.match(content, /0d81139/);
  assert.match(content, /102430e/);
  assert.match(content, /SPEC-001/);
  assert.match(content, /SPEC-002/);
});

test("apps/web/README.md contiene seccion 'Version y cambios' con version 0.4.0-rc.2 y enlace a CHANGELOG.md", () => {
  const readmePath = path.join(webRoot, "README.md");
  assert.ok(fs.existsSync(readmePath), "apps/web/README.md debe existir");

  const content = fs.readFileSync(readmePath, "utf-8");
  assert.match(content, /Versi[oó]n y cambios/i);
  assert.match(content, /0\.4\.0-rc\.2/);
  assert.match(content, /SemVer/i);
  assert.match(content, /CHANGELOG\.md/);
});

test("La version del dashboard en package.json genera 'v0.4.0-rc.2'", () => {
  const pkg = JSON.parse(fs.readFileSync(path.join(webRoot, "package.json"), "utf-8"));
  const versionFormatted = `v${pkg.version}`;
  assert.strictEqual(versionFormatted, "v0.4.0-rc.2");
});
