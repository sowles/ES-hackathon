import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const root = dirname(fileURLToPath(import.meta.url));

function runPython(script, extra = []) {
  const result = spawnSync("python3", [join(root, "scripts", script), ...extra], {
    cwd: root,
    encoding: "utf8",
  });
  if (result.status !== 0) {
    const msg = result.stderr || result.stdout || `python3 ${script} failed`;
    throw new Error(msg);
  }
  return result.stdout;
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => {
      try {
        const raw = Buffer.concat(chunks).toString("utf8") || "{}";
        resolve(JSON.parse(raw));
      } catch (err) {
        reject(err);
      }
    });
    req.on("error", reject);
  });
}

function briefDataPlugin() {
  return {
    name: "chief-brief-data",
    buildStart() {
      runPython("draft_brief.py");
    },
    configureServer(server) {
      runPython("draft_brief.py");
      server.middlewares.use(async (req, res, next) => {
        const url = (req.url || "").split("?")[0];
        if (url === "/api/brief" || url === "/brief.json") {
          try {
            runPython("draft_brief.py");
            const data = readFileSync(join(root, "public", "brief.json"));
            res.statusCode = 200;
            res.setHeader("content-type", "application/json; charset=utf-8");
            res.end(data);
          } catch (err) {
            res.statusCode = 500;
            res.setHeader("content-type", "application/json");
            res.end(JSON.stringify({ error: String(err.message || err) }));
          }
          return;
        }
        if (url !== "/api/review" || req.method !== "POST") {
          next();
          return;
        }
        try {
          const body = await readBody(req);
          const action = body.action || "";
          const comment = body.comment || "";
          runPython("review_brief.py", ["--action", action, "--comment", comment]);
          res.statusCode = 200;
          res.setHeader("content-type", "application/json");
          res.end(JSON.stringify({ ok: true }));
        } catch (err) {
          res.statusCode = 400;
          res.setHeader("content-type", "application/json");
          res.end(JSON.stringify({ ok: false, error: String(err.message || err) }));
        }
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), briefDataPlugin()],
});
