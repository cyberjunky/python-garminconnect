import path from "node:path";
import { pathToFileURL, fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, "..", "..");

export async function resolve(specifier, context, nextResolve) {
  let target = specifier;
  if (target.startsWith("@/")) {
    target = pathToFileURL(path.join(webRoot, target.slice(2))).href;
  }

  try {
    return await nextResolve(target, context);
  } catch (err) {
    if (err.code === "ERR_MODULE_NOT_FOUND") {
      const extensions = [".ts", ".tsx", ".js", ".mjs", "/index.ts", "/index.tsx", "/index.js"];
      for (const ext of extensions) {
        try {
          return await nextResolve(target + ext, context);
        } catch {
          // Continue trying other extensions
        }
      }
    }
    throw err;
  }
}
