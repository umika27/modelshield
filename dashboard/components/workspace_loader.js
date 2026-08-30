/**
 * WorkspaceLoader Component
 * Professional IDE-style workspace initialization screen for ModelShield.
 * Manages loading stages, subtle progress bar, smooth fade transition, and error/retry states.
 */

export class WorkspaceLoader {
  constructor(options = {}) {
    this.options = {
      containerId: "workspace-loader",
      onComplete: null,
      onError: null,
      gifPath: "../agents/gif/idle.gif",
      totalDuration: 4800,
      ...options
    };

    this.state = "IDLE"; // IDLE, INITIALIZING, COMPLETE, ERROR
    this.element = null;
    this.timerIds = [];
    this.reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    this.stages = [
      { time: 0, title: "Initializing workspace", status: "Loading project context & graph schema" },
      { time: 1200, title: "Initializing workspace", status: "Preparing neural verification environment" },
      { time: 2400, title: "Initializing workspace", status: "Loading candidate model weight matrices" },
      { time: 3600, title: "Initializing workspace", status: "Restoring workbench state & security gates" }
    ];

    this.rareShortcuts = [
      { key: "Ctrl + Shift + \\", desc: "Jump to matching bracket" },
      { key: "Alt + Z", desc: "Toggle soft word wrap" },
      { key: "Ctrl + F2", desc: "Select all symbol occurrences" },
      { key: "Ctrl + Shift + K", desc: "Delete current line instantly" },
      { key: "Ctrl + Alt + Down", desc: "Add multi-cursor caret below" },
      { key: "Ctrl + K, Ctrl + S", desc: "Open shortcut reference map" },
      { key: "Ctrl + R (Shell)", desc: "Reverse command history search" },
      { key: "Ctrl + L (Terminal)", desc: "Clear terminal viewport" },
      { key: "Ctrl + Shift + V", desc: "Paste plain unformatted text" },
      { key: "Ctrl + Shift + P", desc: "Trigger IDE Command Palette" }
    ];

    this.funFacts = [
      "💡 Fun Fact: ResNet-50 contains 25.6M parameters and over 23B floating-point operations per inference!",
      "💡 Fun Fact: Adversarial attacks can fool image classifiers by perturbing just a single pixel in an image!",
      "💡 Fun Fact: The term 'Artificial Intelligence' was coined by John McCarthy at Dartmouth in 1956.",
      "💡 Fun Fact: FP16 quantization cuts model memory by 50% with under 0.1% accuracy degradation.",
      "💡 Fun Fact: Differential Privacy guarantees that no single training sample can be reconstructed from weights.",
      "💡 Fun Fact: FGSM (Fast Gradient Sign Method) generates adversarial noise in a single backward pass!",
      "💡 Fun Fact: Modern LLMs process tokens in parallel via multi-head attention matrices using GPU tensor cores."
    ];

    this.tickerIndex = Math.floor(Math.random() * this.rareShortcuts.length);
    this.init();
  }

  init() {
    this.createDom();
    this.bindKeyboardShortcuts();
  }

  createDom() {
    let loaderEl = document.getElementById(this.options.containerId);
    if (!loaderEl) {
      loaderEl = document.createElement("div");
      loaderEl.id = this.options.containerId;
      document.body.appendChild(loaderEl);
    }

    loaderEl.className = "workspace-loader-overlay";
    loaderEl.setAttribute("role", "status");
    loaderEl.setAttribute("aria-live", "polite");

    const initialItem = this.rareShortcuts[this.tickerIndex];

    loaderEl.innerHTML = `
      <div class="workspace-loader-content">
        <div class="workspace-loader-agent">
          <img src="${this.options.gifPath}" alt="Workspace Initialization Agent" class="loader-agent-gif" />
        </div>
        <div class="workspace-loader-title" id="loader-title">Initializing workspace</div>
        <div class="workspace-loader-status mono" id="loader-status">Loading project context &amp; graph schema</div>
        <div class="workspace-loader-progress-track">
          <div class="workspace-loader-progress-fill" id="loader-progress-fill"></div>
        </div>
        
        <!-- Rare Developer Shortcut Ticker (Auto-rotating & Clickable) -->
        <div class="loader-shortcut-ticker mono" id="loader-shortcut-ticker" title="Click or press 'F' for random AI fun fact!">
          <span class="ticker-label">RARE DEV TIP:</span>
          <span class="key-badge" id="ticker-key">${initialItem.key}</span>
          <span class="ticker-desc" id="ticker-desc">${initialItem.desc}</span>
        </div>

        <div class="loader-fact-toast mono" id="loader-fact-toast" style="display: none;"></div>

        <div class="workspace-loader-error-box" id="loader-error-box" style="display: none;">
          <button type="button" class="btn-loader-retry" id="btn-loader-retry" aria-label="Retry workspace initialization">
            <i class="ri-refresh-line"></i> Retry
          </button>
        </div>
      </div>
    `;

    this.element = loaderEl;
    this.titleEl = loaderEl.querySelector("#loader-title");
    this.statusEl = loaderEl.querySelector("#loader-status");
    this.progressFillEl = loaderEl.querySelector("#loader-progress-fill");
    this.tickerKeyEl = loaderEl.querySelector("#ticker-key");
    this.tickerDescEl = loaderEl.querySelector("#ticker-desc");
    this.shortcutTickerEl = loaderEl.querySelector("#loader-shortcut-ticker");
    this.factToastEl = loaderEl.querySelector("#loader-fact-toast");
    this.errorBoxEl = loaderEl.querySelector("#loader-error-box");
    this.retryBtnEl = loaderEl.querySelector("#btn-loader-retry");

    if (this.retryBtnEl) {
      this.retryBtnEl.addEventListener("click", () => this.start());
    }
    if (this.shortcutTickerEl) {
      this.shortcutTickerEl.addEventListener("click", () => this.rotateShortcutManually());
    }

    // Try alternate relative GIF path if primary fails to load
    const gifImg = loaderEl.querySelector(".loader-agent-gif");
    if (gifImg) {
      gifImg.onerror = () => {
        if (gifImg.src.includes("../agents/gif/")) {
          gifImg.src = "agents/gif/idle.gif";
        } else if (gifImg.src.includes("agents/gif/")) {
          gifImg.src = "../agents_gif/idle.gif";
        } else if (gifImg.src.includes("agents_gif/")) {
          gifImg.src = "agents_gif/idle.gif";
        }
      };
    }
  }

  rotateShortcutManually() {
    this.tickerIndex = (this.tickerIndex + 1) % this.rareShortcuts.length;
    this.updateTickerDOM();
  }

  updateTickerDOM() {
    const item = this.rareShortcuts[this.tickerIndex];
    if (!item || !this.tickerKeyEl || !this.tickerDescEl) return;

    this.tickerKeyEl.textContent = item.key;
    this.tickerDescEl.textContent = item.desc;

    if (this.shortcutTickerEl) {
      this.shortcutTickerEl.classList.remove("ticker-swap");
      void this.shortcutTickerEl.offsetWidth;
      this.shortcutTickerEl.classList.add("ticker-swap");
    }
  }

  bindKeyboardShortcuts() {
    this.keydownHandler = (e) => {
      if (this.state !== "INITIALIZING" && this.state !== "IDLE") return;
      if (e.key === "f" || e.key === "F" || e.key === " ") {
        e.preventDefault();
        this.triggerFunFact();
      }
    };
    window.addEventListener("keydown", this.keydownHandler);
  }

  triggerFunFact() {
    if (!this.factToastEl) return;
    const randomFact = this.funFacts[Math.floor(Math.random() * this.funFacts.length)];
    this.factToastEl.textContent = randomFact;
    this.factToastEl.style.display = "block";
    this.factToastEl.classList.remove("toast-active");
    void this.factToastEl.offsetWidth;
    this.factToastEl.classList.add("toast-active");

    // Extend completion timer by 2.5s if fun fact is triggered so user can read it
    if (this.completionTimerId) {
      clearTimeout(this.completionTimerId);
      this.completionTimerId = setTimeout(() => {
        if (this.state !== "INITIALIZING") return;
        if (this.progressFillEl) this.progressFillEl.style.width = "100%";
        setTimeout(() => this.finish(), 300);
      }, 2800);
      this.timerIds.push(this.completionTimerId);
    }
  }

  start() {
    if (this.state === "INITIALIZING") return;
    this.state = "INITIALIZING";
    this.clearTimers();

    // Reset DOM state
    this.element.style.display = "flex";
    this.element.style.opacity = "1";
    this.element.classList.remove("has-error");
    if (this.errorBoxEl) this.errorBoxEl.style.display = "none";
    if (this.factToastEl) this.factToastEl.style.display = "none";
    if (this.progressFillEl) {
      this.progressFillEl.style.display = "block";
      this.progressFillEl.style.width = "0%";
    }

    const totalDuration = this.options.totalDuration;

    // Schedule stage text & progress updates
    this.stages.forEach((stage, idx) => {
      const timerId = setTimeout(() => {
        if (this.state !== "INITIALIZING") return;
        if (this.titleEl) this.titleEl.textContent = stage.title;
        if (this.statusEl) this.statusEl.textContent = stage.status;
        
        const progressPct = Math.round(((idx + 1) / this.stages.length) * 90);
        if (this.progressFillEl) {
          this.progressFillEl.style.width = `${progressPct}%`;
        }
      }, stage.time);

      this.timerIds.push(timerId);
    });

    // Auto-rotate rare developer shortcuts every 2 seconds
    this.tickerInterval = setInterval(() => {
      if (this.state !== "INITIALIZING") return;
      this.tickerIndex = Math.floor(Math.random() * this.rareShortcuts.length);
      this.updateTickerDOM();
    }, 2000);

    // Schedule final completion
    this.completionTimerId = setTimeout(() => {
      if (this.state !== "INITIALIZING") return;
      
      if (this.progressFillEl) {
        this.progressFillEl.style.width = "100%";
      }

      setTimeout(() => {
        this.finish();
      }, 200);
    }, totalDuration);

    this.timerIds.push(this.completionTimerId);
  }

  fail(reason = "Unable to load the project environment.") {
    this.clearTimers();
    this.state = "ERROR";
    this.element.classList.add("has-error");

    if (this.titleEl) this.titleEl.textContent = "Workspace initialization failed";
    if (this.statusEl) this.statusEl.textContent = reason;
    if (this.progressFillEl) this.progressFillEl.style.display = "none";
    if (this.errorBoxEl) this.errorBoxEl.style.display = "block";

    if (typeof this.options.onError === "function") {
      this.options.onError(reason);
    }
  }

  finish() {
    this.state = "COMPLETE";
    if (this.keydownHandler) {
      window.removeEventListener("keydown", this.keydownHandler);
    }
    
    if (this.reducedMotion) {
      this.element.style.display = "none";
      if (typeof this.options.onComplete === "function") {
        this.options.onComplete();
      }
      return;
    }

    // Smooth opacity fade transition
    this.element.style.transition = "opacity 300ms ease";
    this.element.style.opacity = "0";

    setTimeout(() => {
      this.element.style.display = "none";
      if (typeof this.options.onComplete === "function") {
        this.options.onComplete();
      }
    }, 300);
  }

  clearTimers() {
    this.timerIds.forEach(id => clearTimeout(id));
    this.timerIds = [];
    if (this.tickerInterval) {
      clearInterval(this.tickerInterval);
      this.tickerInterval = null;
    }
  }
}

export function initWorkspaceLoader(options) {
  return new WorkspaceLoader(options);
}
