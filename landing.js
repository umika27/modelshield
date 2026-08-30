/**
 * ModelShield Spatial WebGL & Scroll-Driven Storytelling Engine (landing.js)
 * High-End AI Security Infrastructure & Neural Network Visualizer
 */

// ============================================================================
// 1. GLOBAL STATE & STAGES DEFINITION
// ============================================================================

let scene, camera, renderer;
let modelArtifactGroup, boundingCube, shieldMesh, scanLaserPlane;
let neuralLayers = [];       // 5 Neural Network Layers (Groups)
let synapticLines = [];      // Inter-layer connection lines
let signalParticles = [];    // Pulsing data packets travelling along synapses
let ambientParticleSystem, ambientPositions, ambientCount = 600;
let attackParticles, attackPositions, attackVelocities, attackCount = 140;
let floatingDataPoints = []; // 3D floating metadata nodes

let mouseX = 0, mouseY = 0;
let targetCamX = 0, targetCamY = 0, targetCamZ = 16;
let currentCamPos = { x: 0, y: 0, z: 16 };
let currentCamLook = { x: 0, y: 0, z: 0 };
let scrollProgress = 0;
let currentStage = 0;

// Stage Data Content Definitions
// Stage Data Content Definitions with Per-Stage Popup Telemetry
const STAGE_CONFIGS = [
  {
    index: 0,
    name: "STAGE 00 // HERO",
    title: "Verify Your ML Models.",
    popups: {
      tl: { label: "SYSTEM_ID // RESNET50_V3", title: "NEURAL GRAPH CAPTURE" },
      tr: { label: "SECURITY SCORE", title: "92.50 (+01.75 PASS)" },
      bl: { label: "TENSOR WEIGHTS", title: "25.6M FP16 (OPTIMAL)" },
      br: { label: "RELEASE_GATE // VERIFIED", title: "CLICK TO INSPECT MODEL" }
    }
  },
  {
    index: 1,
    name: "STAGE 01 // DETECT",
    title: "Model Weight Ingestion.",
    popups: {
      tl: { label: "GRAPH_INGESTION", title: "25.6M FP16 WEIGHTS" },
      tr: { label: "PARSER_STATUS", title: "50 LAYERS VERIFIED" },
      bl: { label: "VRAM_ALLOCATION", title: "102.4 MB ALLOCATED" },
      br: { label: "CHECKSUM_HASH", title: "SHA256: 42f8b... OK" }
    }
  },
  {
    index: 2,
    name: "STAGE 02 // BUILD",
    title: "Neural Topology Assembly.",
    popups: {
      tl: { label: "CONV2D_LAYER_01", title: "3x224x224 → 64 MAPS" },
      tr: { label: "SYNAPTIC_CONDUITS", title: "5 TENSOR STAGES ACTIVE" },
      bl: { label: "RESBLOCK_ARRAY", title: "8 BOTTLENECK BLOCKS" },
      br: { label: "LOGIT_HEAD", title: "1000 CLASS OUTPUTS" }
    }
  },
  {
    index: 3,
    name: "STAGE 03 // TEST",
    title: "Volumetric Stress Scan.",
    popups: {
      tl: { label: "SCAN_PLANE_AXIS", title: "SWEEPING ALL LAYERS" },
      tr: { label: "STRESS_VECTORS", title: "4 AXES EVALUATING" },
      bl: { label: "ACCURACY_DELTA", title: "BASE: 94.2% / CAND: 92.5%" },
      br: { label: "PRIVACY_CHECK", title: "ZERO EMBEDDING LEAKAGE" }
    }
  },
  {
    index: 4,
    name: "STAGE 04 // ATTACK",
    title: "Adversarial Attack Simulation.",
    popups: {
      tl: { label: "ATTACK_VECTOR", title: "FGSM / PGD GRADIENTS" },
      tr: { label: "VULNERABILITY", title: "3 BREACHES FOUND" },
      bl: { label: "DEGRADATION", title: "LOW-LIGHT DELTA -0.33" },
      br: { label: "REPRO_CAPSULE", title: "CAPSULE #147 FROZEN" }
    }
  },
  {
    index: 5,
    name: "STAGE 05 // SHIELD",
    title: "Security Perimeter Verification.",
    popups: {
      tl: { label: "SECURITY_SHIELD", title: "FORCEFIELD ACTIVE" },
      tr: { label: "RELEASE_POLICY", title: "STRICT GATE PASSED" },
      bl: { label: "DETERMINISM", title: "100% REPRODUCIBILITY" },
      br: { label: "STATUS", title: "RELEASE APPROVED" }
    }
  }
];

// ============================================================================
// 2. INITIALIZATION
// ============================================================================

document.addEventListener("DOMContentLoaded", () => {
  initThemeManager();
  initThreeSpatialScene();
  initHeroTerminalAnimations();
  initScrollStoryController();
  initCursorInteractions();
  initScrubberNavigation();
  initPolicySimulator();
  initWorkspaceNavigationGuards();
  initPhasedHeroSequence();
  initPipCopyHandler();
  initPlatformSlider();
});

function initPipCopyHandler() {
  const pipBox = document.getElementById("pip-install-box");
  const copyBtn = document.getElementById("pip-copy-btn");
  const copyIcon = document.getElementById("pip-copy-icon");
  const copyLabel = document.getElementById("pip-copy-label");

  if (!pipBox) return;

  const handleCopy = (e) => {
    e.stopPropagation();
    const commandText = "pip install modelshield";
    navigator.clipboard.writeText(commandText).then(() => {
      if (copyLabel) copyLabel.textContent = "Copied!";
      if (copyIcon) copyIcon.className = "ri-check-line color-emerald";
      setTimeout(() => {
        if (copyLabel) copyLabel.textContent = "Copy";
        if (copyIcon) copyIcon.className = "ri-file-copy-line";
      }, 2000);
    }).catch(() => {});
  };

  pipBox.addEventListener("click", handleCopy);
  if (copyBtn) copyBtn.addEventListener("click", handleCopy);
}

function initPhasedHeroSequence() {
  const canvas = document.getElementById("webgl-canvas");
  const heroTop = document.getElementById("hero-top-group");
  const heroBottom = document.getElementById("hero-bottom-group");
  if (!canvas) return;

  // Phase 1 (0.0s): Typography visible in spatial composition, 3D Canvas starts transparent
  canvas.style.opacity = "0";
  if (heroTop) heroTop.style.opacity = "1";
  if (heroBottom) heroBottom.style.opacity = "1";

  // Phase 2 (~1.6s): 3D Model gradually fades into view in center of spatial composition
  setTimeout(() => {
    canvas.style.opacity = "1";
  }, 1600);
}

function initWorkspaceNavigationGuards() {
  const workspaceLinks = document.querySelectorAll('a[href*="dashboard/index.html"]');
  workspaceLinks.forEach(link => {
    link.addEventListener("click", (e) => {
      if (link.dataset.initializing === "true") {
        e.preventDefault();
        return;
      }
      link.dataset.initializing = "true";
      link.style.pointerEvents = "none";
      link.style.opacity = "0.75";
      
      const span = link.querySelector("span");
      if (span && !span.textContent.includes("Initializing")) {
        span.textContent = "Initializing...";
      }
    });
  });
}

// ============================================================================
// 3. THEME MANAGER (Dark / Light)
// ============================================================================

function initThemeManager() {
  const savedTheme = localStorage.getItem("modelshield-theme") || "dark";
  applyTheme(savedTheme);

  const darkBtn = document.getElementById("theme-dark-btn");
  const lightBtn = document.getElementById("theme-light-btn");

  if (darkBtn && lightBtn) {
    darkBtn.addEventListener("click", () => applyTheme("dark"));
    lightBtn.addEventListener("click", () => applyTheme("light"));
  }
}

function applyTheme(theme) {
  document.body.setAttribute("data-theme", theme);
  localStorage.setItem("modelshield-theme", theme);

  const darkBtn = document.getElementById("theme-dark-btn");
  const lightBtn = document.getElementById("theme-light-btn");

  if (darkBtn && lightBtn) {
    darkBtn.classList.toggle("active", theme === "dark");
    darkBtn.setAttribute("aria-checked", theme === "dark");
    lightBtn.classList.toggle("active", theme === "light");
    lightBtn.setAttribute("aria-checked", theme === "light");
  }

  // Update Three.js lights / background accents if initialized
  if (scene) {
    const isDark = theme === "dark";
    if (boundingCube) {
      boundingCube.material.color.setHex(isDark ? 0x38bdf8 : 0x0284c7);
      boundingCube.material.opacity = isDark ? 0.25 : 0.4;
    }
  }
}

// ============================================================================
// 4. THREE.JS SPATIAL 3D SCENE & NEURAL NETWORK ARTIFACT
// ============================================================================

function initThreeSpatialScene() {
  const canvas = document.getElementById("webgl-canvas");
  if (!canvas || !window.THREE) return;

  // Scene & Perspective Camera
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.set(0, 0, 16);

  // High Performance WebGL Renderer
  renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, powerPreference: "high-performance" });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  // Lighting (Restrained, low-intensity engineered lighting)
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
  scene.add(ambientLight);

  const dirLight1 = new THREE.DirectionalLight(0x38bdf8, 0.8);
  dirLight1.position.set(10, 12, 10);
  scene.add(dirLight1);

  const dirLight2 = new THREE.DirectionalLight(0x6366f1, 0.4);
  dirLight2.position.set(-10, -10, 8);
  scene.add(dirLight2);

  // --- Central 3D Model Artifact Group ---
  modelArtifactGroup = new THREE.Group();
  scene.add(modelArtifactGroup);

  // Position initial model slightly to center-right on desktop
  modelArtifactGroup.position.set(0, 0, 0);

  // 1. Outer Computational Transparent Bounding Cube / Prism
  const boxGeo = new THREE.BoxGeometry(6.4, 5.2, 5.2);
  const boxEdges = new THREE.EdgesGeometry(boxGeo);
  const boxMat = new THREE.LineBasicMaterial({
    color: 0x38bdf8,
    transparent: true,
    opacity: 0.2,
    linewidth: 1
  });
  boundingCube = new THREE.LineSegments(boxEdges, boxMat);
  boundingCube.visible = false;
  modelArtifactGroup.add(boundingCube);

  // 2. Construct 5 Distinct Neural Network Layers
  buildNeuralNetworkLayers();

  // 3. Synaptic Signal Particles (Pulsing data flowing across layers)
  buildSignalParticles();

  // 4. Volumetric Scanning Laser Plane (Stage 3)
  const laserGeo = new THREE.PlaneGeometry(6.6, 5.4);
  const laserMat = new THREE.MeshBasicMaterial({
    color: 0x38bdf8,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.0, // Activated during scanning stage
    depthWrite: false
  });
  scanLaserPlane = new THREE.Mesh(laserGeo, laserMat);
  scanLaserPlane.rotation.y = Math.PI / 2;
  modelArtifactGroup.add(scanLaserPlane);

  // 5. Volumetric Geometric Shield (Stage 5)
  const shieldGeo = new THREE.IcosahedronGeometry(4.2, 2);
  const shieldMat = new THREE.MeshPhysicalMaterial({
    color: 0x38bdf8,
    emissive: 0x0284c7,
    emissiveIntensity: 0.4,
    roughness: 0.1,
    transmission: 0.9,
    thickness: 1.2,
    transparent: true,
    opacity: 0.0, // Activated in stage 5
    wireframe: false
  });
  shieldMesh = new THREE.Mesh(shieldGeo, shieldMat);
  modelArtifactGroup.add(shieldMesh);

  // 6. Ambient Data Particles Cloud
  buildAmbientParticles();

  // 7. Adversarial Attack Particles (Stage 4)
  buildAttackParticles();

  // Resize handler
  window.addEventListener("resize", onWindowResize);

  // Start Animation Loop
  animateScene();
}

/**
 * Builds the 5 Neural Network Layers with Nodes and Synapses
 */
function buildNeuralNetworkLayers() {
  const layerXPositions = [-2.4, -1.2, 0.0, 1.2, 2.4];
  const layerNodeCounts = [
    { rows: 4, cols: 4 }, // L1: Conv Grid (16 nodes)
    { rows: 3, cols: 3 }, // L2: Latent Features (9 nodes)
    { rows: 4, cols: 3 }, // L3: ResBlocks (12 nodes)
    { rows: 3, cols: 2 }, // L4: Dense Mapping (6 nodes)
    { rows: 2, cols: 2 }  // L5: Logits (4 nodes)
  ];

  const nodeGeometry = new THREE.SphereGeometry(0.1, 16, 16);
  const nodeMaterial = new THREE.MeshStandardMaterial({
    color: 0x38bdf8,
    emissive: 0x0284c7,
    emissiveIntensity: 0.2,
    roughness: 0.3,
    metalness: 0.7
  });

  const layerNodesData = [];

  for (let l = 0; l < 5; l++) {
    const layerGroup = new THREE.Group();
    layerGroup.position.x = layerXPositions[l];

    const config = layerNodeCounts[l];
    const nodesInLayer = [];

    const spacingY = 3.2 / (config.rows + 1);
    const spacingZ = 3.2 / (config.cols + 1);

    for (let r = 0; r < config.rows; r++) {
      for (let c = 0; c < config.cols; c++) {
        const nodeMesh = new THREE.Mesh(nodeGeometry, nodeMaterial.clone());
        const y = -1.6 + (r + 1) * spacingY;
        const z = -1.6 + (c + 1) * spacingZ;

        nodeMesh.position.set(0, y, z);
        nodeMesh.userData = {
          baseY: y,
          baseZ: z,
          layerIdx: l,
          jitterOffset: Math.random() * 10
        };

        layerGroup.add(nodeMesh);
        nodesInLayer.push(nodeMesh);
      }
    }

    // Layer Outer Ring / Frame
    const ringGeo = new THREE.RingGeometry(1.8, 1.84, 32);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.2
    });
    const frameRing = new THREE.Mesh(ringGeo, ringMat);
    frameRing.rotation.y = Math.PI / 2;
    layerGroup.add(frameRing);

    modelArtifactGroup.add(layerGroup);
    neuralLayers.push({ group: layerGroup, nodes: nodesInLayer, ring: frameRing });
    layerNodesData.push(nodesInLayer);
  }

  // Construct Synaptic Line Connections between adjacent layers
  for (let l = 0; l < 4; l++) {
    const currentNodes = layerNodesData[l];
    const nextNodes = layerNodesData[l + 1];

    const linesPositions = [];

    // Connect nodes with probabilistic sampling to keep geometry elegant & fast
    for (let i = 0; i < currentNodes.length; i++) {
      for (let j = 0; j < nextNodes.length; j++) {
        if (Math.random() > 0.45 || (i % 2 === j % 2)) {
          const p1 = new THREE.Vector3(layerXPositions[l], currentNodes[i].position.y, currentNodes[i].position.z);
          const p2 = new THREE.Vector3(layerXPositions[l + 1], nextNodes[j].position.y, nextNodes[j].position.z);

          linesPositions.push(p1.x, p1.y, p1.z);
          linesPositions.push(p2.x, p2.y, p2.z);
        }
      }
    }

    const lineGeo = new THREE.BufferGeometry();
    lineGeo.setAttribute('position', new THREE.Float32BufferAttribute(linesPositions, 3));

    const lineMat = new THREE.LineBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.18
    });

    const synapses = new THREE.LineSegments(lineGeo, lineMat);
    modelArtifactGroup.add(synapses);
    synapticLines.push(synapses);
  }
}

/**
 * Builds data pulse particles traveling across synapses
 */
function buildSignalParticles() {
  const signalCount = 60;
  const signalGeo = new THREE.BufferGeometry();
  const positions = new Float32Array(signalCount * 3);

  for (let i = 0; i < signalCount; i++) {
    positions[i * 3] = -2.4 + Math.random() * 4.8;
    positions[i * 3 + 1] = (Math.random() - 0.5) * 2.5;
    positions[i * 3 + 2] = (Math.random() - 0.5) * 2.5;
  }

  signalGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const signalMat = new THREE.PointsMaterial({
    color: 0x38bdf8,
    size: 0.14,
    transparent: true,
    opacity: 0.8
  });

  const signalPoints = new THREE.Points(signalGeo, signalMat);
  modelArtifactGroup.add(signalPoints);
  signalParticles = signalPoints;
}

/**
 * Ambient Background Particles
 */
function buildAmbientParticles() {
  const geo = new THREE.BufferGeometry();
  ambientPositions = new Float32Array(ambientCount * 3);

  for (let i = 0; i < ambientCount; i++) {
    ambientPositions[i * 3] = (Math.random() - 0.5) * 32;
    ambientPositions[i * 3 + 1] = (Math.random() - 0.5) * 24;
    ambientPositions[i * 3 + 2] = (Math.random() - 0.5) * 24;
  }

  geo.setAttribute('position', new THREE.BufferAttribute(ambientPositions, 3));
  const mat = new THREE.PointsMaterial({
    color: 0x94a3b8,
    size: 0.05,
    transparent: true,
    opacity: 0.4
  });

  ambientParticleSystem = new THREE.Points(geo, mat);
  scene.add(ambientParticleSystem);
}

/**
 * Adversarial Attack Perturbation Particles
 */
function buildAttackParticles() {
  const geo = new THREE.BufferGeometry();
  attackPositions = new Float32Array(attackCount * 3);
  attackVelocities = new Float32Array(attackCount * 3);

  for (let i = 0; i < attackCount; i++) {
    attackPositions[i * 3] = (Math.random() - 0.5) * 12;
    attackPositions[i * 3 + 1] = (Math.random() - 0.5) * 12;
    attackPositions[i * 3 + 2] = (Math.random() - 0.5) * 12;

    attackVelocities[i * 3] = (Math.random() - 0.5) * 0.05;
    attackVelocities[i * 3 + 1] = (Math.random() - 0.5) * 0.05;
    attackVelocities[i * 3 + 2] = (Math.random() - 0.5) * 0.05;
  }

  geo.setAttribute('position', new THREE.BufferAttribute(attackPositions, 3));
  const mat = new THREE.PointsMaterial({
    color: 0xf43f5e,
    size: 0.12,
    transparent: true,
    opacity: 0.0 // Initially invisible
  });

  attackParticles = new THREE.Points(geo, mat);
  modelArtifactGroup.add(attackParticles);
}

function onWindowResize() {
  if (!camera || !renderer) return;
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}

// ============================================================================
// 5. ANIMATION LOOP & SCROLL-DRIVEN STATE INTERPOLATION
// ============================================================================

function animateScene() {
  requestAnimationFrame(animateScene);

  const time = performance.now() * 0.001;

  // 1. Ultra-Smooth Buttery Camera Movement towards target position
  currentCamPos.x += (targetCamX - currentCamPos.x) * 0.038;
  currentCamPos.y += (targetCamY - currentCamPos.y) * 0.038;
  currentCamPos.z += (targetCamZ - currentCamPos.z) * 0.038;

  camera.position.set(
    currentCamPos.x + (mouseX * 0.8),
    currentCamPos.y + (mouseY * 0.8),
    currentCamPos.z
  );
  camera.lookAt(currentCamLook.x, currentCamLook.y, currentCamLook.z);

  // 2. Slow, Restrained Ambient Rotation of the Model Artifact
  if (modelArtifactGroup) {
    modelArtifactGroup.rotation.y = time * 0.05 + (mouseX * 0.05);
    modelArtifactGroup.rotation.x = Math.sin(time * 0.03) * 0.03 + (mouseY * 0.05);
  }

  // 3. Pulse Signal Particles across layers
  if (signalParticles) {
    const pos = signalParticles.geometry.attributes.position.array;
    for (let i = 0; i < pos.length / 3; i++) {
      pos[i * 3] += 0.03;
      if (pos[i * 3] > 2.6) {
        pos[i * 3] = -2.6;
        pos[i * 3 + 1] = (Math.random() - 0.5) * 2.5;
        pos[i * 3 + 2] = (Math.random() - 0.5) * 2.5;
      }
    }
    signalParticles.geometry.attributes.position.needsUpdate = true;
  }

  // 4. Ambient Background Particle Drift
  if (ambientParticleSystem) {
    ambientParticleSystem.rotation.y = time * 0.01;
  }

  // 5. Dynamic Scroll Interpolation (0.0 to 1.0)
  updateScrollStageDynamics(scrollProgress, time);

  renderer.render(scene, camera);
}

/**
 * Updates 3D elements based on scroll progress (0.0 -> 1.0)
 */
function updateScrollStageDynamics(p, time) {
  if (!modelArtifactGroup) return;

  // --- STAGE 0: HERO (0.0 - 0.16) ---
  if (p < 0.16) {
    targetCamX = 0.0;
    targetCamY = 0.0;
    targetCamZ = 14.0;
    targetCamLook = { x: 0.0, y: 0, z: 0 };

    modelArtifactGroup.scale.setScalar(0.9);
    boundingCube.visible = false;
    scanLaserPlane.material.opacity = 0.0;
    shieldMesh.material.opacity = 0.0;
    attackParticles.material.opacity = 0.0;

    setLayerEmissive(0x38bdf8, 0.15);
  }
  // --- STAGE 1: DETECT (0.16 - 0.35) ---
  else if (p < 0.35) {
    const t = (p - 0.16) / 0.19;
    targetCamX = 2.0 - t * 1.5;
    targetCamY = 0.2;
    targetCamZ = 14.0 - t * 1.5;
    targetCamLook = { x: 0.2, y: 0, z: 0 };

    modelArtifactGroup.scale.setScalar(1.0 + t * 0.15);
    boundingCube.material.opacity = 0.35 + t * 0.15;
    scanLaserPlane.material.opacity = 0.0;
    shieldMesh.material.opacity = 0.0;
    attackParticles.material.opacity = 0.0;

    setLayerEmissive(0x38bdf8, 0.8);
  }
  // --- STAGE 2: BUILD / ASSEMBLE (0.35 - 0.55) ---
  else if (p < 0.55) {
    const t = (p - 0.35) / 0.20;
    targetCamX = 0.5 + Math.sin(t * Math.PI) * 1.2;
    targetCamY = 0.4 + t * 0.4;
    targetCamZ = 12.5 - t * 1.0;
    targetCamLook = { x: 0, y: 0, z: 0 };

    modelArtifactGroup.scale.setScalar(1.15);
    boundingCube.material.opacity = 0.45;
    scanLaserPlane.material.opacity = 0.0;
    shieldMesh.material.opacity = 0.0;
    attackParticles.material.opacity = 0.0;

    // Expand layer spacing slightly during assembly
    neuralLayers.forEach((layer, idx) => {
      layer.group.position.x = (-2.4 + idx * 1.2) * (1.0 + t * 0.15);
    });

    setLayerEmissive(0x38bdf8, 1.0);
  }
  // --- STAGE 3: TEST / SCAN (0.55 - 0.72) ---
  else if (p < 0.72) {
    const t = (p - 0.55) / 0.17;
    targetCamX = 0.0;
    targetCamY = 0.3;
    targetCamZ = 11.2;
    targetCamLook = { x: 0, y: 0, z: 0 };

    modelArtifactGroup.scale.setScalar(1.2);
    boundingCube.material.opacity = 0.5;

    // Scan plane sweeps from X: -3.0 to +3.0
    scanLaserPlane.position.x = -3.0 + t * 6.0;
    scanLaserPlane.material.opacity = 0.45 + Math.sin(time * 8) * 0.15;
    shieldMesh.material.opacity = 0.0;
    attackParticles.material.opacity = t * 0.2;

    setLayerEmissive(0x38bdf8, 1.2);
  }
  // --- STAGE 4: ATTACK / PERTURBATION (0.72 - 0.88) ---
  else if (p < 0.88) {
    const t = (p - 0.72) / 0.16;
    targetCamX = (Math.sin(time * 12) * 0.08) - 0.4;
    targetCamY = (Math.cos(time * 10) * 0.08);
    targetCamZ = 11.8;
    targetCamLook = { x: 0, y: 0, z: 0 };

    modelArtifactGroup.scale.setScalar(1.2);
    boundingCube.material.opacity = 0.4;
    scanLaserPlane.material.opacity = 0.0;
    shieldMesh.material.opacity = t * 0.2;

    // Attack particles collide inwards
    attackParticles.material.opacity = 0.5 + t * 0.4;
    const pos = attackParticles.geometry.attributes.position.array;
    for (let i = 0; i < pos.length / 3; i++) {
      pos[i * 3] += attackVelocities[i * 3] * 3;
      pos[i * 3 + 1] += attackVelocities[i * 3 + 1] * 3;
      pos[i * 3 + 2] += attackVelocities[i * 3 + 2] * 3;
    }
    attackParticles.geometry.attributes.position.needsUpdate = true;

    // Jitter nodes to simulate attack perturbation
    neuralLayers.forEach(layer => {
      layer.nodes.forEach(node => {
        node.position.y = node.userData.baseY + Math.sin(time * 20 + node.userData.jitterOffset) * 0.08;
        node.position.z = node.userData.baseZ + Math.cos(time * 20 + node.userData.jitterOffset) * 0.08;
      });
    });

    setLayerEmissive(0xf59e0b, 1.0); // Amber warning
  }
  // --- STAGE 5: SHIELD / VERIFICATION (0.88 - 1.0) ---
  else {
    const t = (p - 0.88) / 0.12;
    targetCamX = 0.0;
    targetCamY = 0.2;
    targetCamZ = 13.5;
    targetCamLook = { x: 0, y: 0, z: 0 };

    modelArtifactGroup.scale.setScalar(1.15);
    boundingCube.material.opacity = 0.5;
    scanLaserPlane.material.opacity = 0.0;

    // Volumetric crystalline forcefield shield activates!
    shieldMesh.material.opacity = 0.35 + t * 0.45;
    shieldMesh.rotation.y = time * 0.3;
    shieldMesh.rotation.x = time * 0.2;
    attackParticles.material.opacity = (1 - t) * 0.4;

    // Stabilize nodes back to baseline
    neuralLayers.forEach(layer => {
      layer.nodes.forEach(node => {
        node.position.y = node.userData.baseY;
        node.position.z = node.userData.baseZ;
      });
    });

    setLayerEmissive(0x10b981, 1.0); // Emerald verified
  }
}

function setLayerEmissive(hexColor, intensity) {
  neuralLayers.forEach(layer => {
    layer.nodes.forEach(node => {
      node.material.emissive.setHex(hexColor);
      node.material.emissiveIntensity = intensity;
    });
  });
}

// ============================================================================
// 6. SCROLL STORY CONTROLLER & DOM SYNC
// ============================================================================

function initScrollStoryController() {
  const storyContainer = document.getElementById("storyline");
  const scrollTrack = document.getElementById("scroll-track");
  if (!storyContainer || !scrollTrack) return;

  const spatialComp = document.getElementById("spatial-composition");
  const heroTop = document.getElementById("hero-top-group");
  const heroBottom = document.getElementById("hero-bottom-group");
  const hudStage = document.getElementById("spatial-hud-stage");
  const cliStage = document.getElementById("spatial-cli-stage");
  const landingNav = document.querySelector(".landing-nav");

  window.addEventListener("scroll", () => {
    // Hide header on scroll down, show at top of page
    if (landingNav) {
      if (window.scrollY > 40) {
        landingNav.classList.add("is-hidden");
        landingNav.classList.add("is-scrolled");
      } else {
        landingNav.classList.remove("is-hidden");
        landingNav.classList.remove("is-scrolled");
      }
    }

    const rect = scrollTrack.getBoundingClientRect();
    const totalDist = scrollTrack.offsetHeight - window.innerHeight;
    const currentDist = -rect.top;

    if (totalDist > 0) {
      scrollProgress = Math.max(0, Math.min(1, currentDist / totalDist));
    }

    // Determine current stage index (0 to 5)
    let stageIdx = 0;
    if (scrollProgress < 0.16) stageIdx = 0;
    else if (scrollProgress < 0.35) stageIdx = 1;
    else if (scrollProgress < 0.55) stageIdx = 2;
    else if (scrollProgress < 0.72) stageIdx = 3;
    else if (scrollProgress < 0.88) stageIdx = 4;
    else stageIdx = 5;

    if (stageIdx !== currentStage) {
      currentStage = stageIdx;
      updateStageDOM(currentStage);
    }

    // Dynamic Spatial Composition Lifecycle
    if (spatialComp) {
      const floatingCallouts = document.querySelectorAll(".floating-callout, .spatial-leader-svg");
      const gifBadge = document.getElementById("landing-gif-container");

      if (scrollProgress < 0.16) {
        // --- STAGE 00 // HERO: Floating 3D Spatial Callouts Active ---
        const p0 = scrollProgress / 0.16;
        const heroOpacity = Math.max(0, 1 - p0 * 1.4);

        spatialComp.style.setProperty("--scene-scale", (1.0 - p0 * 0.08).toFixed(3));
        spatialComp.style.setProperty("--scene-translate-y", `${-p0 * 40}px`);
        spatialComp.style.setProperty("--scene-translate-x", "0px");

        if (heroTop) {
          heroTop.style.opacity = heroOpacity;
          heroTop.style.transform = `translateY(${-p0 * 30}px)`;
        }
        floatingCallouts.forEach(el => {
          el.style.opacity = heroOpacity;
          el.style.pointerEvents = heroOpacity > 0.5 ? "auto" : "none";
        });
        if (gifBadge) {
          gifBadge.style.opacity = heroOpacity;
          gifBadge.style.pointerEvents = heroOpacity > 0.5 ? "auto" : "none";
        }

        if (hudStage) {
          hudStage.style.opacity = 0;
          hudStage.style.transform = "translate(-50%, 25px)";
          hudStage.style.pointerEvents = "none";
        }

      } else {
        // --- STAGES 01 - 05 // VERIFICATION JOURNEY ---
        if (heroTop) heroTop.style.opacity = 0;
        floatingCallouts.forEach(el => {
          el.style.opacity = 1;
          el.style.pointerEvents = "auto";
        });
        if (gifBadge) {
          gifBadge.style.opacity = "0";
          gifBadge.style.pointerEvents = "none";
        }

        let scale = 1.05;
        let transX = 0;

        if (currentStage === 1) scale = 1.06;
        else if (currentStage === 2) scale = 1.15;
        else if (currentStage === 3) scale = 1.20;
        else if (currentStage === 4) scale = 1.18;
        else if (currentStage === 5) scale = 1.12;

        spatialComp.style.setProperty("--scene-scale", scale.toFixed(3));
        spatialComp.style.setProperty("--scene-translate-x", `${transX}px`);
        spatialComp.style.setProperty("--scene-translate-y", "0px");

        // Shorten leader line arrows as model scale enlarges so arrows terminate cleanly at outer edge
        const leaderSvg = document.querySelector(".spatial-leader-svg");
        if (leaderSvg) {
          const arrowShortenScale = Math.max(0.65, 1.0 - (scale - 1.0) * 1.85);
          leaderSvg.style.transform = `scale(${arrowShortenScale.toFixed(3)})`;
        }

        if (hudStage) {
          hudStage.style.opacity = 1;
          hudStage.style.transform = "translate(-50%, 0px)";
          hudStage.style.pointerEvents = "auto";
        }
      }
    }

    // Update scrubber buttons
    updateScrubberUI(currentStage);
  }, { passive: true });
}

function updateStageDOM(stageIdx) {
  const config = STAGE_CONFIGS[stageIdx];
  if (!config) return;

  const hudStage = document.getElementById("spatial-hud-stage");
  const idxEl = document.getElementById("hud-stage-index");
  const titleEl = document.getElementById("hud-stage-title");

  if (hudStage) {
    hudStage.style.transform = "translate(-50%, 15px)";
    hudStage.style.opacity = "0.3";
  }

  const stageName = (window.ModelShieldI18n && window.ModelShieldI18n.t(`stage${stageIdx}.name`)) || config.name;
  const stageTitle = (window.ModelShieldI18n && window.ModelShieldI18n.t(`stage${stageIdx}.title`)) || config.title;

  setTimeout(() => {
    if (idxEl) {
      idxEl.innerText = stageName;
      idxEl.classList.remove("slide-up-active");
      void idxEl.offsetWidth;
      idxEl.classList.add("slide-up-active");
    }
    if (titleEl) {
      titleEl.innerText = stageTitle;
      titleEl.classList.remove("slide-up-active");
      void titleEl.offsetWidth;
      titleEl.classList.add("slide-up-active");
    }

    // Update 4 corner popup detail callouts dynamically per stage
    if (config.popups) {
      const popTLlbl = document.getElementById("pop-tl-label");
      const popTLtitle = document.getElementById("pop-tl-title");
      const popTRlbl = document.getElementById("pop-tr-label");
      const popTRtitle = document.getElementById("pop-tr-title");
      const popBLlbl = document.getElementById("pop-bl-label");
      const popBLtitle = document.getElementById("pop-bl-title");
      const popBRlbl = document.getElementById("pop-br-label");
      const popBRtitle = document.getElementById("pop-br-title");

      if (popTLlbl && config.popups.tl) popTLlbl.innerText = config.popups.tl.label;
      if (popTLtitle && config.popups.tl) popTLtitle.innerText = config.popups.tl.title;
      if (popTRlbl && config.popups.tr) popTRlbl.innerText = config.popups.tr.label;
      if (popTRtitle && config.popups.tr) popTRtitle.innerText = config.popups.tr.title;
      if (popBLlbl && config.popups.bl) popBLlbl.innerText = config.popups.bl.label;
      if (popBLtitle && config.popups.bl) popBLtitle.innerText = config.popups.bl.title;
      if (popBRlbl && config.popups.br) popBRlbl.innerText = config.popups.br.label;
      if (popBRtitle && config.popups.br) popBRtitle.innerText = config.popups.br.title;
    }

    if (hudStage) {
      hudStage.style.transform = "translate(-50%, 0px)";
      hudStage.style.opacity = "1";
    }
  }, 50);
}

window.addEventListener("modelshield_lang_change", () => {
  updateStageDOM(currentStage);
});

function updateScrubberUI(activeIdx) {
  const scrubberItems = document.querySelectorAll(".scrubber-item");
  scrubberItems.forEach(item => {
    const stage = parseInt(item.getAttribute("data-stage"), 10);
    item.classList.toggle("active", stage === activeIdx);
  });
}

function initScrubberNavigation() {
  const scrubberItems = document.querySelectorAll(".scrubber-item");
  const scrollTrack = document.getElementById("scroll-track");
  if (!scrollTrack) return;

  const stageScrollRatios = [0.0, 0.18, 0.35, 0.52, 0.70, 0.85, 0.96];

  scrubberItems.forEach(item => {
    item.addEventListener("click", () => {
      const stage = parseInt(item.getAttribute("data-stage"), 10);
      const ratio = stageScrollRatios[stage] || 0;
      const totalDist = scrollTrack.offsetHeight - window.innerHeight;
      const targetScroll = scrollTrack.offsetTop + ratio * totalDist;

      window.scrollTo({
        top: targetScroll,
        behavior: "smooth"
      });
    });
  });
}

// ============================================================================
// 7. CURSOR PARALLAX & INTERACTION
// ============================================================================

function initCursorInteractions() {
  window.addEventListener("mousemove", (e) => {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
    mouseY = -(e.clientY / window.innerHeight - 0.5) * 2;
  });

  // Stage 06 Morph Terminal 3D Hover Tilt & Spotlight Tracking
  const morphTerm = document.getElementById("morph-terminal");
  if (morphTerm) {
    morphTerm.addEventListener("mousemove", (e) => {
      const rect = morphTerm.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const centerX = rect.width / 2;
      const centerY = rect.height / 2;

      const rotateX = ((y - centerY) / centerY) * -6; // 6 deg max tilt
      const rotateY = ((x - centerX) / centerX) * 6;

      morphTerm.style.setProperty("--spot-x", `${x}px`);
      morphTerm.style.setProperty("--spot-y", `${y}px`);
      morphTerm.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) scale3d(1.02, 1.02, 1.02)`;
    });

    morphTerm.addEventListener("mouseleave", () => {
      morphTerm.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)";
    });
  }

  // Interactive Copy Line Handlers inside Terminal
  const copyLines = document.querySelectorAll(".interactive-copy-line");
  copyLines.forEach(line => {
    line.addEventListener("click", (e) => {
      e.stopPropagation();
      const textToCopy = line.dataset.copy || line.textContent.trim();
      const tooltip = line.querySelector(".line-copy-tooltip");
      const icon = line.querySelector(".line-copy-icon");

      navigator.clipboard.writeText(textToCopy).then(() => {
        if (tooltip) tooltip.textContent = "Copied!";
        if (icon) icon.className = "ri-check-line line-copy-icon color-emerald";

        setTimeout(() => {
          if (tooltip) tooltip.textContent = "Copy";
          if (icon) icon.className = "ri-file-copy-line line-copy-icon";
        }, 1800);
      }).catch(() => {});
    });
  });

  // Cursor-Related Spotlight Hover & Full Click Fill for "Go to Workspace" Buttons
  const workspaceBtns = document.querySelectorAll(
    ".btn-morph-primary, .btn-banner-primary, .nav-btn-primary, .callout-action-btn"
  );
  workspaceBtns.forEach(btn => {
    btn.addEventListener("mousemove", (e) => {
      const rect = btn.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      btn.style.setProperty("--btn-mouse-x", `${x.toFixed(1)}px`);
      btn.style.setProperty("--btn-mouse-y", `${y.toFixed(1)}px`);
    });

    btn.addEventListener("click", () => {
      btn.classList.add("btn-clicked");
    });
  });

  // Dynamic Speech Bubble Popup on Agent GIF Hover (Rare Developer Shortcuts, No Emojis)
  const landingGifContainer = document.getElementById("landing-gif-container");
  const bubbleTextEl = document.getElementById("bubble-text");

  const shortcutTips = [
    { key: "Ctrl + Shift + P", desc: "Trigger IDE Command Palette" },
    { key: "Ctrl + Shift + \\", desc: "Jump to matching bracket" },
    { key: "Alt + Z", desc: "Toggle soft word wrap" },
    { key: "Ctrl + F2", desc: "Select all symbol occurrences" },
    { key: "Ctrl + Shift + K", desc: "Delete current line instantly" },
    { key: "Ctrl + Alt + Down", desc: "Add multi-cursor caret below" },
    { key: "Ctrl + K, Ctrl + S", desc: "Open shortcut reference map" },
    { key: "Ctrl + R", desc: "Reverse command history search" },
    { key: "Ctrl + L", desc: "Clear terminal viewport" },
    { key: "Ctrl + Shift + V", desc: "Paste plain unformatted text" }
  ];

  if (landingGifContainer && bubbleTextEl) {
    landingGifContainer.addEventListener("mouseenter", () => {
      const tip = shortcutTips[Math.floor(Math.random() * shortcutTips.length)];
      bubbleTextEl.innerHTML = `<span class="bubble-key-badge">${tip.key}</span> ${tip.desc}`;
    });
  }
}

// ============================================================================
// 8. HERO TERMINAL PROGRESSIVE SCORE ANIMATION
// ============================================================================

function initHeroTerminalAnimations() {
  const counterEl = document.getElementById("hero-score-counter");
  if (!counterEl) return;

  let currentVal = 0;
  const targetVal = 92;
  const duration = 1600;
  const startTime = performance.now();

  function stepCount(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    // Ease Out Quad
    const easeProgress = 1 - (1 - progress) * (1 - progress);
    currentVal = Math.floor(easeProgress * targetVal);

    counterEl.innerText = currentVal;

    if (progress < 1) {
      requestAnimationFrame(stepCount);
    }
  }

  setTimeout(() => {
    requestAnimationFrame(stepCount);
  }, 400);
}

// ============================================================================
// 9. INTERACTIVE RELEASE POLICY SIMULATOR
// ============================================================================

function initPolicySimulator() {
  const modelSelect = document.getElementById("model-select");
  const sliderEps = document.getElementById("slider-epsilon");
  const sliderTol = document.getElementById("slider-tolerance");
  const valEps = document.getElementById("val-epsilon");
  const valTol = document.getElementById("val-tolerance");
  const btnStrict = document.getElementById("btn-strict-gate");
  const btnSoft = document.getElementById("btn-soft-gate");

  const simTarget = document.getElementById("sim-target");
  const simEps = document.getElementById("sim-eps");
  const simTol = document.getElementById("sim-tol");
  const simVerdict = document.getElementById("sim-verdict");

  if (!modelSelect || !sliderEps || !sliderTol) return;

  let isStrict = true;

  function recalculatePolicy() {
    const eps = parseFloat(sliderEps.value);
    const tol = parseFloat(sliderTol.value);
    const model = modelSelect.value;

    if (valEps) valEps.innerText = eps.toFixed(3);
    if (valTol) valTol.innerText = `${tol.toFixed(0)}%`;

    if (simTarget) simTarget.innerText = modelSelect.options[modelSelect.selectedIndex].text;
    if (simEps) simEps.innerText = `ε = ${eps.toFixed(3)}`;
    if (simTol) simTol.innerText = `${tol.toFixed(1)}%`;

    // Simulated degradation delta calculation
    let degradation = - (eps * 120);
    if (model === "vit") degradation *= 0.8;
    if (model === "llama") degradation *= 0.65;

    const isPassed = degradation >= tol;

    if (simVerdict) {
      if (isPassed) {
        simVerdict.className = "color-emerald";
        simVerdict.innerText = "PASS — APPROVED FOR CI PIPELINE";
      } else if (!isStrict) {
        simVerdict.className = "color-amber";
        simVerdict.innerText = `REVIEW REQUIRED (Delta: ${degradation.toFixed(1)}% breached)`;
      } else {
        simVerdict.className = "color-rose";
        simVerdict.innerText = `BLOCKED (EXIT CODE 1: ${degradation.toFixed(1)}% breach)`;
      }
    }
  }

  sliderEps.addEventListener("input", recalculatePolicy);
  sliderTol.addEventListener("input", recalculatePolicy);
  modelSelect.addEventListener("change", recalculatePolicy);

  if (btnStrict && btnSoft) {
    btnStrict.addEventListener("click", () => {
      isStrict = true;
      btnStrict.classList.add("active");
      btnSoft.classList.remove("active");
      recalculatePolicy();
    });

    btnSoft.addEventListener("click", () => {
      isStrict = false;
      btnSoft.classList.add("active");
      btnStrict.classList.remove("active");
      recalculatePolicy();
    });
  }

  recalculatePolicy();
}

// ============================================================================
// 8. HORIZONTAL PLATFORM ARCHITECTURE SLIDER (APPLE EVENTS STYLE)
// ============================================================================

function initPlatformSlider() {
  const track = document.getElementById("platform-slider-track");
  const prevBtn = document.getElementById("slider-prev-btn");
  const nextBtn = document.getElementById("slider-next-btn");
  const thumb = document.getElementById("slider-progress-thumb");

  if (!track) return;

  const updateControls = () => {
    const maxScroll = track.scrollWidth - track.clientWidth;
    if (maxScroll <= 0) {
      if (prevBtn) prevBtn.classList.add("disabled");
      if (nextBtn) nextBtn.classList.add("disabled");
      if (thumb) thumb.style.transform = "translateX(0%)";
      return;
    }

    const current = track.scrollLeft;
    const progress = Math.max(0, Math.min(1, current / maxScroll));

    if (prevBtn) prevBtn.classList.toggle("disabled", current <= 8);
    if (nextBtn) nextBtn.classList.toggle("disabled", current >= maxScroll - 8);

    if (thumb) {
      const travel = (180 - (180 * 0.3)); // Track width (180px) minus thumb width (30%)
      thumb.style.transform = `translateX(${progress * travel}px)`;
    }
  };

  const getCardStep = () => {
    const firstCard = track.querySelector(".platform-slider-card");
    if (!firstCard) return 380;
    return firstCard.offsetWidth + 24; // Card width + gap
  };

  if (prevBtn) {
    prevBtn.addEventListener("click", () => {
      const step = getCardStep();
      track.scrollBy({ left: -step, behavior: "smooth" });
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      const step = getCardStep();
      track.scrollBy({ left: step, behavior: "smooth" });
    });
  }

  // Mouse Drag-to-Scroll Support
  let isDown = false;
  let startX = 0;
  let scrollLeftPos = 0;
  let hasDragged = false;

  track.addEventListener("mousedown", (e) => {
    isDown = true;
    hasDragged = false;
    track.classList.add("is-dragging");
    startX = e.pageX - track.offsetLeft;
    scrollLeftPos = track.scrollLeft;
  });

  window.addEventListener("mouseup", () => {
    if (!isDown) return;
    isDown = false;
    track.classList.remove("is-dragging");
  });

  track.addEventListener("mouseleave", () => {
    if (!isDown) return;
    isDown = false;
    track.classList.remove("is-dragging");
  });

  track.addEventListener("mousemove", (e) => {
    if (!isDown) return;
    e.preventDefault();
    const x = e.pageX - track.offsetLeft;
    const walk = (x - startX) * 1.4;
    if (Math.abs(walk) > 5) {
      hasDragged = true;
    }
    track.scrollLeft = scrollLeftPos - walk;
  });

  // Prevent unwanted click navigation if the user was dragging
  track.querySelectorAll(".platform-slider-card").forEach(card => {
    card.addEventListener("click", (e) => {
      if (hasDragged) {
        e.preventDefault();
        hasDragged = false;
      }
    });
  });

  track.addEventListener("scroll", updateControls, { passive: true });
  window.addEventListener("resize", updateControls, { passive: true });

  // Initial state check
  setTimeout(updateControls, 100);
}

