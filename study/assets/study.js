(() => {
  const prefersDark =
    typeof window !== "undefined" &&
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches;

  const mermaidTheme = prefersDark ? "dark" : "default";

  const run = () => {
    if (typeof window === "undefined") return;
    if (!window.mermaid) return;
    window.mermaid.initialize({ startOnLoad: true, theme: mermaidTheme });
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run, { once: true });
  } else {
    run();
  }
})();
