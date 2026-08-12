// Copies the pipeline-generated data (../public/data) into web/public/data so
// `next build` (output: export) can ship it as static assets.
import { cp, mkdir, access } from "node:fs/promises";
import { constants } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");
const src = resolve(root, "..", "public", "data");
const dest = resolve(root, "public", "data");

async function exists(p) {
  try {
    await access(p, constants.F_OK);
    return true;
  } catch {
    return false;
  }
}

if (!(await exists(src))) {
  console.warn(`[copy-data] source missing: ${src} (run the pipeline first)`);
  process.exit(0);
}

await mkdir(dest, { recursive: true });
await cp(src, dest, { recursive: true });
console.log(`[copy-data] copied ${src} -> ${dest}`);
