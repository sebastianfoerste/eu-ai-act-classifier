import { spawn } from "node:child_process";
import path from "node:path";

const REPO_ROOT =
  process.env.CLASSIFIER_REPO_ROOT ?? path.resolve(/* turbopackIgnore: true */ process.cwd(), "..");
const TIMEOUT_MS = 20000;

export async function runClassifierBridge(command: string, payload?: unknown): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const child = spawn(
      "uv",
      ["run", "python", "-m", "eu_ai_act_classifier.local_api", command],
      {
        cwd: REPO_ROOT,
        env: { ...process.env, PYTHONUNBUFFERED: "1" },
        stdio: ["pipe", "pipe", "pipe"],
      },
    );

    let stdout = "";
    let stderr = "";
    const timer = setTimeout(() => {
      child.kill("SIGTERM");
      reject(new Error("classifier bridge timed out"));
    }, TIMEOUT_MS);

    child.stdout.on("data", (chunk: Buffer) => {
      stdout += chunk.toString("utf8");
    });
    child.stderr.on("data", (chunk: Buffer) => {
      stderr += chunk.toString("utf8");
    });
    child.on("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      if (code !== 0) {
        reject(new Error(stderr || `classifier bridge exited with ${code}`));
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch (error) {
        reject(error);
      }
    });

    if (payload === undefined) {
      child.stdin.end();
    } else {
      child.stdin.end(JSON.stringify(payload));
    }
  });
}
