/* Market Pulse — Alpine.js components & HTMX bridges. */

document.addEventListener("alpine:init", () => {
  // ── Theme (dark / light / system) ─────────────────────────────
  Alpine.store("theme", {
    mode: localStorage.getItem("mp-theme") || "system",
    init() { this.apply(); window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => this.apply()); },
    apply() {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      const dark = this.mode === "dark" || (this.mode === "system" && prefersDark);
      document.documentElement.classList.toggle("dark", dark);
    },
    toggle() {
      this.mode = this.mode === "dark" ? "light" : "dark";
      localStorage.setItem("mp-theme", this.mode);
      this.apply();
    },
  });

  // ── Sidebar state ─────────────────────────────────────────────
  Alpine.store("sidebar", {
    open: window.innerWidth >= 1024,
    toggle() { this.open = !this.open; },
  });

  // ── Command palette ───────────────────────────────────────────
  Alpine.store("palette", {
    visible: false,
    query: "",
    actions: [
      { label: "Generate today's episode", hint: "⇧⌘G", href: "/generate" },
      { label: "Open dashboard", href: "/" },
      { label: "Browse library", href: "/library" },
      { label: "Open settings", href: "/settings" },
      { label: "Toggle dark mode", action: () => Alpine.store("theme").toggle() },
    ],
    show() { this.visible = true; this.query = ""; setTimeout(() => document.getElementById("mp-palette-input")?.focus(), 20); },
    hide() { this.visible = false; },
    filtered() {
      const q = this.query.toLowerCase().trim();
      if (!q) return this.actions;
      return this.actions.filter(a => a.label.toLowerCase().includes(q));
    },
    run(a) {
      this.hide();
      if (a.action) a.action();
      if (a.href) window.location.href = a.href;
    },
  });

  // ── Toast queue ───────────────────────────────────────────────
  Alpine.store("toasts", {
    items: [],
    push(kind, msg) {
      const id = Math.random().toString(36).slice(2);
      this.items.push({ id, kind, msg });
      setTimeout(() => { this.items = this.items.filter(t => t.id !== id); }, 4200);
    },
  });

  // ── Job pill (polls /jobs/active every 3s if no active SSE) ──
  Alpine.store("pill", {
    active: null,
    async refresh() {
      try {
        const r = await fetch("/jobs/active.json");
        if (!r.ok) { this.active = null; return; }
        const data = await r.json();
        this.active = data.job || null;
      } catch (e) { this.active = null; }
    },
    init() {
      this.refresh();
      setInterval(() => this.refresh(), 4000);
    },
  });
});

// ── Global hotkeys ────────────────────────────────────────────
document.addEventListener("keydown", (e) => {
  const meta = e.metaKey || e.ctrlKey;
  if (meta && e.key.toLowerCase() === "k") {
    e.preventDefault();
    Alpine.store("palette").show();
  }
  if (e.key === "Escape" && Alpine.store("palette").visible) {
    Alpine.store("palette").hide();
  }
});

// ── HTMX event bridges ───────────────────────────────────────
document.body.addEventListener("htmx:responseError", (evt) => {
  try {
    Alpine.store("toasts").push("error", `${evt.detail.xhr.status}: request failed`);
  } catch (e) {}
});
document.body.addEventListener("mp:toast", (evt) => {
  try { Alpine.store("toasts").push(evt.detail.kind || "info", evt.detail.msg); } catch (e) {}
});
