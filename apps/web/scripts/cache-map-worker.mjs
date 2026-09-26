// MapLibre v6 imports a sibling module from its worker. Keep both local for offline use.
import { mkdirSync, copyFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
const require = createRequire(import.meta.url);
const dist = join(dirname(require.resolve("maplibre-gl/package.json")), "dist");
const destination = join(dirname(fileURLToPath(import.meta.url)), "..", "public", "maplibre");
mkdirSync(destination, { recursive: true });
for (const filename of ["maplibre-gl-worker.mjs", "maplibre-gl-shared.mjs"]) {
  copyFileSync(join(dist, filename), join(destination, filename));
}

copyFileSync(join(dist, "..", "LICENSE.txt"), join(destination, "LICENSE.txt"));
