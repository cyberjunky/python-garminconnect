import test from "node:test";
import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, "..", "..");

function extractImportSpecifiers(filePath) {
  if (!fs.existsSync(filePath)) return [];
  const content = fs.readFileSync(filePath, "utf-8");
  const specifiers = [];
  const staticImportRegex = /(?:import|export)\s+(?:[\w*\s{},]*\s+from\s+)?['"]([^'"]+)['"]/g;
  let match;
  while ((match = staticImportRegex.exec(content)) !== null) {
    specifiers.push(match[1]);
  }
  const dynamicImportRegex = /import\s*\(\s*['"]([^'"]+)['"]\s*\)/g;
  while ((match = dynamicImportRegex.exec(content)) !== null) {
    specifiers.push(match[1]);
  }
  return specifiers;
}

function listTsFiles(dir) {
  if (!fs.existsSync(dir)) return [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  let files = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files = files.concat(listTsFiles(full));
    } else if (/\.(ts|tsx)$/.test(entry.name)) {
      files.push(full);
    }
  }
  return files;
}

test("REQ-022 / P22: Dominio en lib/chat/domain es TypeScript puro sin dependencias externas", () => {
  const domainDir = path.join(webRoot, "lib", "chat", "domain");
  assert.ok(fs.existsSync(domainDir), "lib/chat/domain debe existir");

  const domainFiles = listTsFiles(domainDir);
  assert.ok(domainFiles.length > 0, "lib/chat/domain debe contener archivos TypeScript de dominio");

  for (const file of domainFiles) {
    const specifiers = extractImportSpecifiers(file);
    for (const spec of specifiers) {
      assert.doesNotMatch(
        spec,
        /^(next|react|@supabase|openai)/,
        `Dominio puro ${path.relative(webRoot, file)} no debe importar frameworks ni SDKs (${spec})`
      );
      assert.doesNotMatch(
        spec,
        /infra/,
        `Dominio puro ${path.relative(webRoot, file)} no debe importar infraestructura (${spec})`
      );
      assert.doesNotMatch(
        spec,
        /(app|components)/,
        `Dominio puro ${path.relative(webRoot, file)} no debe importar capas de presentacion (${spec})`
      );
    }
  }
});

test("REQ-022 / P22: Aplicacion en lib/chat/application depende solo del dominio y puertos, no de adaptadores", () => {
  const appDir = path.join(webRoot, "lib", "chat", "application");
  assert.ok(fs.existsSync(appDir), "lib/chat/application debe existir");

  const appFiles = listTsFiles(appDir);
  assert.ok(appFiles.length > 0, "lib/chat/application debe contener archivos de aplicacion y puertos");

  for (const file of appFiles) {
    const specifiers = extractImportSpecifiers(file);
    for (const spec of specifiers) {
      assert.doesNotMatch(
        spec,
        /^(next|react|@supabase|openai)/,
        `Capa de aplicacion ${path.relative(webRoot, file)} no debe importar frameworks ni SDKs (${spec})`
      );
      assert.doesNotMatch(
        spec,
        /infra/,
        `Capa de aplicacion ${path.relative(webRoot, file)} no debe importar adaptadores concretos de infra (${spec})`
      );
    }
  }
});

test("REQ-022 / P22: lib/condition.ts conserva calculos y prompt puros sin importar Supabase", () => {
  const conditionFile = path.join(webRoot, "lib", "condition.ts");
  const specifiers = extractImportSpecifiers(conditionFile);
  for (const spec of specifiers) {
    assert.doesNotMatch(
      spec,
      /@supabase/,
      `lib/condition.ts no debe importar @supabase (${spec})`
    );
    assert.doesNotMatch(
      spec,
      /(supabase|supabase\.ts)$/,
      `lib/condition.ts no debe importar clientes de supabase (${spec})`
    );
  }
});

test("REQ-022 / P22: Adaptadores de infraestructura en lib/infra implementan puertos y no son importados por dominio", () => {
  const infraDir = path.join(webRoot, "lib", "infra");
  assert.ok(fs.existsSync(infraDir), "lib/infra debe existir");
  const infraFiles = listTsFiles(infraDir);
  assert.ok(infraFiles.length > 0, "lib/infra debe contener adaptadores de infraestructura");
});
