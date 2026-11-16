// Applies a stored colour-scheme choice before the first paint. A classic script on
// purpose: a module runs after parsing, so the system scheme would flash first.
// The key is THEME_KEY in theme.mjs; tests/playground/theme.test.mjs holds the two together.
(function () {
  try {
    var theme = window.localStorage.getItem("eu-ai-act-classifier.theme");
    if (theme === "light" || theme === "dark") document.documentElement.dataset.theme = theme;
  } catch (error) { /* storage blocked: the system setting applies */ }
})();
