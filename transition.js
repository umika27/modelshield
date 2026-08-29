/**
 * ModelShield Developer Layer Spatial Engine (transition.js)
 * Immersive 6-Stage Narrative: CODE -> BUILD -> SCAN -> ATTACK -> SHIELD -> DEPLOY
 */

let scene, camera, renderer;
let centralCoreGroup, cubeFrame, innerNodesGroup, shieldSphere, scanningBeam;
let particleSwarm, particlePositions, floatingArtifacts = [];
let pointLightCyan, pointLightBlue;

let mouseX = 0, mouseY = 0;
let targetCamX = 0, targetCamY = 0;
let scrollProgress = 0;
let currentStageIndex = 0;

// 6 Narrative Stages Data
const NARRATIVE_STAGES = [
  {
    stateLabel: "01: CODE",
    eyebrow: "PHASE 01 // SOURCE INITIALIZATION",
    headline: "Your model starts <br><span class='highlight-text'>as code.</span>",
    subheadline: "Every neural network begins as weight artifacts, dataset splits, and hyperparameters suspended in source control.",
    badgeIcon: "ri-git-commit-line",
    badgePrimary: "model.pkl • weights.bin • config.yaml",
    badgeSecondary: "Ready for execution graph synthesis",
    cliBadge: "SOURCE",
    cliCmd: "git status",
    cliStream: [
      { text: "# On branch main (clean working tree)", type: "info" },
      { text: "# Tracked artifacts: model.pkl, weights.bin, config.yaml", type: "info" }
    ],
    cliScore: "--",
    cliStatus: "AWAITING BUILD",
    cliProgress: 0
  },
  {
    stateLabel: "02: BUILD",
    eyebrow: "PHASE 02 // ENVIRONMENT COMPILATION",
    headline: "Build it.",
    subheadline: "Synthesizing computational nodes, resolving CUDA runtimes, and assembling the neural execution pipeline.",
    badgeIcon: "ri-cpu-line",
    badgePrimary: "$ load model.pkl --resolve-graph",
    badgeSecondary: "50 layers assembled • PyTorch 2.2",
    cliBadge: "BUILDING",
    cliCmd: "modelshield build candidate-v3",
    cliStream: [
      { text: "> Loading model.pkl into memory", type: "info" },
      { text: "> Resolving dependencies: PyTorch 2.2, CUDA 12.1", type: "info" },
      { text: "> Model graph constructed: 50 computational layers", type: "ok" }
    ],
    cliScore: "50",
    cliStatus: "COMPILED",
    cliProgress: 35
  },
  {
    stateLabel: "03: SCAN",
    eyebrow: "PHASE 03 // MULTI-AXIS INSPECTION",
    headline: "Now test it.",
    subheadline: "Scanning model parameters across reproducibility seeds, distribution bounds, and metadata invariants.",
    badgeIcon: "ri-radar-line",
    badgePrimary: "MODEL DETECTED: 25.6M PARAMETERS",
    badgeSecondary: "Scanning 4 verification vectors",
    cliBadge: "SCANNING",
    cliCmd: "modelshield scan --suite standard",
    cliStream: [
      { text: "> [1/4] Inspecting architecture: 25.6M parameters", type: "info" },
      { text: "> [2/4] Verifying reproducibility seed (seed=42)", type: "info" },
      { text: "> [3/4] Sweeping tolerance thresholds (-0.15 limit)", type: "info" }
    ],
    cliScore: "70",
    cliStatus: "SCANNING",
    cliProgress: 60
  },
  {
    stateLabel: "04: ATTACK",
    eyebrow: "PHASE 04 // ADVERSARIAL STRESS-TEST",
    headline: "Stress-test <br><span class='highlight-text'>under fire.</span>",
    subheadline: "Subjecting the model to simulated distribution shifts, low light blur, contrast drop, and adversarial perturbations.",
    badgeIcon: "ri-error-warning-line",
    badgePrimary: "3 POTENTIAL VULNERABILITIES DETECTED",
    badgeSecondary: "Low light blur • Motion blur • Contrast drop",
    cliBadge: "THREATS",
    cliCmd: "modelshield test --perturbation-all",
    cliStream: [
      { text: "⚠ Low Light Blur: 0.49 score (< 0.65 threshold)", type: "warn" },
      { text: "⚠ Contrast Drop: 0.58 score (< 0.63 threshold)", type: "warn" },
      { text: "> Compiling reproducibility capsule [capsule-147]", type: "info" }
    ],
    cliScore: "49",
    cliStatus: "BREACH FOUND",
    cliProgress: 78
  },
  {
    stateLabel: "05: SHIELD",
    eyebrow: "PHASE 05 // FORCEFIELD VERIFICATION",
    headline: "Verify it.",
    subheadline: "Activating the ModelShield regression forcefield. Disrupted particles are blocked at the perimeter and safety policies enforced.",
    badgeIcon: "ri-shield-check-line",
    badgePrimary: "VERIFIED // SECURITY SCORE 92/100",
    badgeSecondary: "Enforced policy: strict_block • Exit code 0",
    cliBadge: "VERIFIED",
    cliCmd: "modelshield verify --policy strict_block",
    cliStream: [
      { text: "✓ Robustness bounds satisfied", type: "ok" },
      { text: "✓ Reproducibility capsule locked [capsule-147]", type: "ok" },
      { text: "✓ Security barrier established around model core", type: "ok" },
      { text: "VERIFIED: 92/100 SECURITY SCORE", type: "ok" }
    ],
    cliScore: "92",
    cliStatus: "VERIFIED",
    cliProgress: 95
  },
  {
    stateLabel: "06: DEPLOY",
    eyebrow: "PHASE 06 // PRODUCTION RELEASE",
    headline: "Ship with <br><span class='highlight-text'>confidence.</span>",
    subheadline: "Model verified. Automated release gate approved. Seamless transition into your production registry.",
    badgeIcon: "ri-rocket-line",
    badgePrimary: "RELEASE GATE: PASSED (CI EXIT 0)",
    badgeSecondary: "Ready for deployment to production",
    cliBadge: "READY",
    cliCmd: "modelshield deploy --target production",
    cliStream: [
      { text: "✓ Release Gatekeeper: ALL CHECKS PASSED", type: "ok" },
      { text: "✓ Safe for production release", type: "ok" },
      { text: "STATUS: READY FOR DEPLOYMENT", type: "ok" }
    ],
    cliScore: "92",
    cliStatus: "DEPLOY READY",
    cliProgress: 100
  }
];

document.addEventListener("DOMContentLoaded", () => {
  initThreeEngine();
  setupScrollStory();
  setupMouseParallax();
  setupScrubberActions();
  updateNarrativeUI(0);
});

// ----------------------------------------------------------------------------
// 1. Three.js Spatial Engine & CLI Security Core
// ----------------------------------------------------------------------------
function initThreeEngine() {
  const canvas = document.getElementById("stage-canvas");
  if (!canvas || !window.THREE) return;

  // Scene & Camera
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.set(0, 0, 24);

  // Renderer
  renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  // Lights
  const ambient = new THREE.AmbientLight(0xffffff, 0.5);
  scene.add(ambient);

  pointLightCyan = new THREE.PointLight(0x38bdf8, 3.0, 60);
  pointLightCyan.position.set(6, 6, 10);
  scene.add(pointLightCyan);

  pointLightBlue = new THREE.PointLight(0x6366f1, 2.5, 60);
  pointLightBlue.position.set(-6, -6, 8);
  scene.add(pointLightBlue);

  // --- Central 3D CLI Security Core Group ---
  centralCoreGroup = new THREE.Group();
  scene.add(centralCoreGroup);

  // 1. Outer Translucent Wireframe Cube
  const cubeGeo = new THREE.BoxGeometry(3.2, 3.2, 3.2);
  const cubeMat = new THREE.MeshBasicMaterial({
    color: 0x38bdf8,
    wireframe: true,
    transparent: true,
    opacity: 0.3
  });
  cubeFrame = new THREE.Mesh(cubeGeo, cubeMat);
  centralCoreGroup.add(cubeFrame);

  // 2. Inner Neural Computational Nodes
  innerNodesGroup = new THREE.Group();
  const nodeGeo = new THREE.SphereGeometry(0.12, 16, 16);
  const nodeMat = new THREE.MeshStandardMaterial({
    color: 0x38bdf8,
    emissive: 0x0284c7,
    emissiveIntensity: 0.8,
    roughness: 0.2
  });

  const nodePositions = [
    [0, 0, 0], [1, 1, 1], [-1, 1, 1], [1, -1, 1], [-1, -1, 1],
    [1, 1, -1], [-1, 1, -1], [1, -1, -1], [-1, -1, -1],
    [0, 1.2, 0], [0, -1.2, 0], [1.2, 0, 0], [-1.2, 0, 0]
  ];

  nodePositions.forEach(pos => {
    const node = new THREE.Mesh(nodeGeo, nodeMat);
    node.position.set(pos[0], pos[1], pos[2]);
    innerNodesGroup.add(node);
  });
  centralCoreGroup.add(innerNodesGroup);

  // 3. Scanning Laser Beam Plane
  const beamGeo = new THREE.PlaneGeometry(5.0, 5.0);
  const beamMat = new THREE.MeshBasicMaterial({
    color: 0x38bdf8,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.0
  });
  scanningBeam = new THREE.Mesh(beamGeo, beamMat);
  scanningBeam.rotation.x = Math.PI / 2;
  centralCoreGroup.add(scanningBeam);

  // 4. Geodesic Forcefield Sphere (The Shield)
  const shieldGeo = new THREE.IcosahedronGeometry(3.6, 2);
  const shieldMat = new THREE.MeshPhysicalMaterial({
    color: 0x38bdf8,
    emissive: 0x0284c7,
    emissiveIntensity: 0.25,
    transmission: 0.85,
    roughness: 0.1,
    transparent: true,
    opacity: 0.0,
    wireframe: true
  });
  shieldSphere = new THREE.Mesh(shieldGeo, shieldMat);
  centralCoreGroup.add(shieldSphere);

  // 5. Environmental Floating Developer Tokens & Particles
  initFloatingArtifacts();

  // Resize Handler
  window.addEventListener("resize", onWindowResize);

  // Animation Loop
  animateScene();
}

function initFloatingArtifacts() {
  const count = 500;
  const particleGeo = new THREE.BufferGeometry();
  particlePositions = new Float32Array(count * 3);

  for (let i = 0; i < count; i++) {
    particlePositions[i * 3] = (Math.random() - 0.5) * 26;
    particlePositions[i * 3 + 1] = (Math.random() - 0.5) * 26;
    particlePositions[i * 3 + 2] = (Math.random() - 0.5) * 26;
  }

  particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
  const particleMat = new THREE.PointsMaterial({
    color: 0x7dd3fc,
    size: 0.07,
    transparent: true,
    opacity: 0.6
  });

  particleSwarm = new THREE.Points(particleGeo, particleMat);
  scene.add(particleSwarm);
}

function onWindowResize() {
  if (!camera || !renderer) return;
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

function animateScene() {
  requestAnimationFrame(animateScene);

  const time = performance.now() * 0.001;

  // Smooth Camera Tilt & Position Lerping
  camera.position.x += (targetCamX - camera.position.x) * 0.05;
  camera.position.y += (targetCamY - camera.position.y) * 0.05;

  // Rotate Central Core
  if (centralCoreGroup) {
    centralCoreGroup.rotation.y = time * 0.18;
    centralCoreGroup.rotation.x = Math.sin(time * 0.12) * 0.1;
  }

  if (innerNodesGroup) {
    innerNodesGroup.rotation.y = -time * 0.35;
    innerNodesGroup.rotation.z = time * 0.2;
  }

  if (particleSwarm) {
    particleSwarm.rotation.y = time * 0.04;
  }

  // Interpolate 3D State based on Scroll
  interpolateSpatialStory(scrollProgress, time);

  renderer.render(scene, camera);
}

// ----------------------------------------------------------------------------
// 2. Spatial 6-Stage Interpolation Engine
// ----------------------------------------------------------------------------
function interpolateSpatialStory(progress, time) {
  if (!camera || !cubeFrame || !shieldSphere) return;

  // Camera Dolly & Rotation across scroll (0.0 to 1.0)
  // Stage 1 (0.0 - 0.16) Code: Far camera
  if (progress < 0.16) {
    const t = progress / 0.16;
    camera.position.z = 24 - t * 4;
    cubeFrame.material.opacity = 0.2 + t * 0.15;
    shieldSphere.material.opacity = 0;
    scanningBeam.material.opacity = 0;
    centralCoreGroup.position.z = 0;
  }
  // Stage 2 (0.16 - 0.33) Build: Approach and assemble
  else if (progress < 0.33) {
    const t = (progress - 0.16) / 0.17;
    camera.position.z = 20 - t * 5;
    cubeFrame.material.opacity = 0.35 + t * 0.25;
    cubeFrame.rotation.y = t * Math.PI * 0.5;
    shieldSphere.material.opacity = 0;
    scanningBeam.material.opacity = 0;
    centralCoreGroup.position.z = 0;
  }
  // Stage 3 (0.33 - 0.50) Scan: Laser scan sweep
  else if (progress < 0.50) {
    const t = (progress - 0.33) / 0.17;
    camera.position.z = 15 - t * 3;
    scanningBeam.material.opacity = 0.6;
    scanningBeam.position.y = Math.sin(time * 4) * 2.0;
    shieldSphere.material.opacity = 0;
    centralCoreGroup.position.z = 0;
  }
  // Stage 4 (0.50 - 0.66) Attack: Jitter & threats
  else if (progress < 0.66) {
    const t = (progress - 0.50) / 0.16;
    camera.position.z = 12;
    scanningBeam.material.opacity = 0;
    // Jitter cube
    cubeFrame.position.x = (Math.random() - 0.5) * 0.08 * t;
    cubeFrame.position.y = (Math.random() - 0.5) * 0.08 * t;
    shieldSphere.material.opacity = t * 0.2;
    shieldSphere.scale.setScalar(0.9 + t * 0.1);
    centralCoreGroup.position.z = 0;
  }
  // Stage 5 (0.66 - 0.83) Shield: Forcefield locks
  else if (progress < 0.83) {
    const t = (progress - 0.66) / 0.17;
    camera.position.z = 12 + t * 4;
    cubeFrame.position.set(0, 0, 0);
    shieldSphere.material.opacity = 0.2 + t * 0.6;
    shieldSphere.scale.setScalar(1.0 + t * 0.08);
    centralCoreGroup.position.z = 0;
  }
  // Stage 6 (0.83 - 1.0) Deploy: Move forward toward viewer
  else {
    const t = (progress - 0.83) / 0.17;
    camera.position.z = 16 - t * 2;
    centralCoreGroup.position.z = t * 8; // Move forward toward screen
    shieldSphere.material.opacity = 0.8;
  }
}

// ----------------------------------------------------------------------------
// 3. Scroll Tracking & Narrative UI Controller
// ----------------------------------------------------------------------------
function setupScrollStory() {
  const storyContainer = document.getElementById("story-container");
  if (!storyContainer) return;

  window.addEventListener("scroll", () => {
    const rect = storyContainer.getBoundingClientRect();
    const scrollDist = -rect.top;
    const totalHeight = storyContainer.offsetHeight - window.innerHeight;

    if (totalHeight > 0) {
      scrollProgress = Math.max(0, Math.min(1, scrollDist / totalHeight));
    }

    // Determine current stage index (0 to 5)
    const stageIdx = Math.min(5, Math.floor(scrollProgress * 6));
    if (stageIdx !== currentStageIndex) {
      currentStageIndex = stageIdx;
      updateNarrativeUI(currentStageIndex);
    }

    // Update vertical scrubber indicator height
    const scrubberInd = document.getElementById("scrubber-indicator");
    if (scrubberInd) {
      scrubberInd.style.height = `${Math.round(scrollProgress * 100)}%`;
    }
  });
}

function updateNarrativeUI(index) {
  const stage = NARRATIVE_STAGES[index];
  if (!stage) return;

  // 1. HUD Telemetry
  const hudState = document.getElementById("hud-state-label");
  if (hudState) hudState.textContent = stage.stateLabel;

  // 2. Headline & Eyebrow Box
  const eyebrowText = document.getElementById("eyebrow-text");
  const headline = document.getElementById("state-headline");
  const subheadline = document.getElementById("state-subheadline");
  const badgeIcon = document.getElementById("badge-icon-elem");
  const badgePrimary = document.getElementById("badge-primary");
  const badgeSecondary = document.getElementById("badge-secondary");

  if (eyebrowText) eyebrowText.textContent = stage.eyebrow;
  if (headline) headline.innerHTML = stage.headline;
  if (subheadline) subheadline.textContent = stage.subheadline;
  if (badgeIcon) badgeIcon.className = stage.badgeIcon;
  if (badgePrimary) badgePrimary.textContent = stage.badgePrimary;
  if (badgeSecondary) badgeSecondary.textContent = stage.badgeSecondary;

  // Toggle Final Card on Stage 6 (Deploy)
  const finalCard = document.getElementById("final-card");
  const headlineBox = document.getElementById("headline-box");
  if (finalCard && headlineBox) {
    if (index === 5) {
      finalCard.style.display = "block";
      headlineBox.style.display = "none";
    } else {
      finalCard.style.display = "none";
      headlineBox.style.display = "block";
    }
  }

  // 3. Floating CLI Terminal
  const cliBadge = document.getElementById("cli-badge");
  const cliCmdText = document.getElementById("cli-cmd-text");
  const cliStream = document.getElementById("cli-stream");
  const cliScore = document.getElementById("cli-score");
  const cliStatusTxt = document.getElementById("cli-status-txt");
  const cliProgressWrapper = document.getElementById("cli-progress-wrapper");
  const cliProgressFill = document.getElementById("cli-progress-fill");

  if (cliBadge) cliBadge.textContent = stage.cliBadge;
  if (cliCmdText) cliCmdText.textContent = stage.cliCmd;
  if (cliScore) cliScore.innerHTML = `${stage.cliScore}<small>/100</small>`;
  if (cliStatusTxt) cliStatusTxt.textContent = stage.cliStatus;

  if (cliProgressWrapper && cliProgressFill) {
    if (stage.cliProgress > 0) {
      cliProgressWrapper.style.display = "block";
      cliProgressFill.style.width = `${stage.cliProgress}%`;
    } else {
      cliProgressWrapper.style.display = "none";
    }
  }

  if (cliStream) {
    cliStream.innerHTML = stage.cliStream.map(row => {
      return `<div class="cli-stream-row ${row.type}">${row.text}</div>`;
    }).join("");
  }

  // 4. Scrubber Active Node
  const scrubberNodes = document.querySelectorAll(".scrubber-node");
  scrubberNodes.forEach((node, idx) => {
    node.classList.toggle("active", idx === index);
  });
}

function setupScrubberActions() {
  const scrubberNodes = document.querySelectorAll(".scrubber-node");
  const storyContainer = document.getElementById("story-container");

  scrubberNodes.forEach(node => {
    node.addEventListener("click", () => {
      const stageIdx = parseInt(node.getAttribute("data-index"), 10);
      const totalHeight = storyContainer.offsetHeight - window.innerHeight;
      const targetScroll = storyContainer.offsetTop + (stageIdx * (totalHeight / 5.8));

      window.scrollTo({
        top: targetScroll,
        behavior: "smooth"
      });
    });
  });
}

// ----------------------------------------------------------------------------
// 4. Mouse Parallax & Inertia
// ----------------------------------------------------------------------------
function setupMouseParallax() {
  window.addEventListener("mousemove", (e) => {
    mouseX = (e.clientX / window.innerWidth) * 2 - 1;
    mouseY = -(e.clientY / window.innerHeight) * 2 + 1;

    targetCamX = mouseX * 2.0;
    targetCamY = mouseY * 1.5;

    if (pointLightCyan) {
      pointLightCyan.position.x = mouseX * 10;
      pointLightCyan.position.y = mouseY * 10;
    }
  });
}
