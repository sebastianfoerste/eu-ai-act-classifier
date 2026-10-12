// Python runs off the UI thread. Only static code and packages are fetched;
// the profile you paste is never sent anywhere.
let pyodide;
const progress = text => self.postMessage({ type: "progress", text });

self.onmessage = async ({ data }) => {
  try {
    if (data.type === "init") {
      progress("Loading Python runtime…");
      const { loadPyodide } = await import("https://cdn.jsdelivr.net/pyodide/v0.28.2/full/pyodide.mjs");
      pyodide = await loadPyodide();
      progress("Loading the rule engine…");
      // Pydantic is the classifier's only dependency and ships with Pyodide.
      await pyodide.loadPackage(["micropip", "pydantic"]);
      pyodide.globals.set("wheel_url", data.wheelUrl);
      await pyodide.runPythonAsync("import micropip\nawait micropip.install(wheel_url, deps=False)");
      const response = await fetch(new URL("classify.py", import.meta.url));
      if (!response.ok) throw new Error("The browser bridge could not be loaded.");
      await pyodide.runPythonAsync(await response.text());
      self.postMessage({ type: "ready" });
    } else if (data.type === "classify") {
      pyodide.globals.set("profile_text", data.text);
      pyodide.globals.set("include_advisory", Boolean(data.advisory));
      try {
        const result = await pyodide.runPythonAsync("classify_profile(profile_text, include_advisory)");
        self.postMessage({ type: "result", id: data.id, ...JSON.parse(result) });
      } finally {
        pyodide.globals.delete("profile_text");
        pyodide.globals.delete("include_advisory");
      }
    }
  } catch {
    // Avoid exposing Python tracebacks containing profile text.
    self.postMessage({
      type: "error", id: data.id,
      text: data.type === "init"
        ? "The rule engine could not load. Check your connection and retry. Your profile is still here."
        : "The classification could not finish. Check the profile structure and try again. Your profile is still here.",
    });
  }
};
