/**
 * AgentGif Component
 * Displays animated agent GIF in topbar/header with a subtle cycle/switch button.
 * Automatically discovers GIF files in agents/gif/ (with fallback & preloading).
 */

export class AgentGifComponent {
  constructor(containerElement) {
    this.container = containerElement;
    this.gifs = [];
    this.currentIndex = 0;
    this.basePath = "../agents/gif/";
    this.imgElement = null;
    this.btnElement = null;
    
    if (this.container) {
      this.init();
    }
  }

  async init() {
    this.gifs = await this.discoverGifs();
    if (!this.gifs || this.gifs.length === 0) {
      if (this.container) this.container.style.display = "none";
      return;
    }

    this.render();
    this.preloadGifs();
  }

  async discoverGifs() {
    const candidateRegistries = [
      "../agents/gif/registry.json",
      "agents/gif/registry.json",
      "../agents_gif/registry.json",
      "agents_gif/registry.json"
    ];

    for (const regPath of candidateRegistries) {
      try {
        const response = await fetch(regPath);
        if (response.ok) {
          const list = await response.json();
          if (Array.isArray(list) && list.length > 0) {
            this.basePath = regPath.substring(0, regPath.lastIndexOf("/") + 1);
            return list;
          }
        }
      } catch (err) {
        // Continue trying fallback paths if fetch fails
      }
    }

    // Default auto-discovered list matching files in agents/gif/
    this.basePath = "../agents/gif/";
    return [
      "idle.gif",
      "analyse.gif",
      "attack.gif",
      "defence.gif",
      "landing.gif",
      "reward.gif",
      "dead.gif"
    ];
  }

  getGifUrl(filename) {
    return `${this.basePath}${filename}`;
  }

  preloadGifs() {
    if (!this.gifs) return;
    this.gifs.forEach(filename => {
      const img = new Image();
      img.src = this.getGifUrl(filename);
    });
  }

  render() {
    if (!this.container) return;

    const currentGif = this.gifs[this.currentIndex];
    const formattedName = currentGif.replace(/\.gif$/i, "");

    this.container.className = "agent-gif-container";
    this.container.innerHTML = `
      <div class="agent-gif-wrapper" title="Agent state: ${formattedName}">
        <img class="agent-gif-img" src="${this.getGifUrl(currentGif)}" alt="Agent GIF (${formattedName})" />
      </div>
      <button type="button" class="btn-agent-switch" id="btn-switch-agent" title="Change agent (${formattedName})" aria-label="Change agent">
        <i class="ri-repeat-line"></i>
      </button>
    `;

    this.imgElement = this.container.querySelector(".agent-gif-img");
    this.btnElement = this.container.querySelector("#btn-switch-agent");

    if (this.imgElement) {
      this.imgElement.onerror = () => {
        // Attempt fallback paths if initial path resolution failed
        if (this.basePath === "../agents/gif/") {
          this.basePath = "agents/gif/";
          this.imgElement.src = this.getGifUrl(currentGif);
        } else if (this.basePath === "agents/gif/") {
          this.basePath = "../agents_gif/";
          this.imgElement.src = this.getGifUrl(currentGif);
        } else if (this.basePath === "../agents_gif/") {
          this.basePath = "agents_gif/";
          this.imgElement.src = this.getGifUrl(currentGif);
        } else {
          // If all image loading attempts fail, hide the container gracefully
          this.container.style.display = "none";
        }
      };
    }

    if (this.btnElement) {
      this.btnElement.addEventListener("click", () => this.nextGif());
    }
  }

  nextGif() {
    if (!this.gifs || this.gifs.length === 0) return;
    this.currentIndex = (this.currentIndex + 1) % this.gifs.length;
    const nextGif = this.gifs[this.currentIndex];
    const formattedName = nextGif.replace(/\.gif$/i, "");

    if (this.imgElement) {
      this.imgElement.src = this.getGifUrl(nextGif);
      this.imgElement.alt = `Agent GIF (${formattedName})`;
      const wrapper = this.container.querySelector(".agent-gif-wrapper");
      if (wrapper) wrapper.title = `Agent state: ${formattedName}`;
    }

    if (this.btnElement) {
      this.btnElement.title = `Change agent (${formattedName})`;
    }
  }
}

export function initAgentGif(containerElement) {
  return new AgentGifComponent(containerElement);
}
