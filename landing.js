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
const STAGE_CONFIGS = [
  {
    index: 0,
    name: "STAGE 00 // HERO",
    title: "Secure Every Model Before It Ships.",
    desc: "ModelShield evaluates, stress-tests, and monitors AI models for security, robustness, and reproducibility.",
    model: "resnet50-v3.pkl",
    params: "25.6M FP16",
    framework: "PyTorch 2.2",
    state: "INITIALIZED",
    stateColor: "var(--accent-cyan)",
    cliTag: "DAEMON: LISTENING",
    cliLines: "> Listening on tcp://127.0.0.1:8080<br>> Ready for candidate model ingestion..."
  },
  {
    index: 1,
    name: "STAGE 01 // DETECT",
    title: "Model Detected.",
    desc: "Candidate model weights ingested. Deconstructing tensor computational graph and verifying layer hierarchy.",
    model: "resnet50-v3.pkl",
    params: "25.6M FP16",
    framework: "PyTorch 2.2",
    state: "INGESTION COMPLETE",
    stateColor: "var(--accent-cyan)",
    cliTag: "STREAM: GRAPH_SYNAPSE",
    cliLines: "> Extracting graph architecture: 50 layers<br>> Ingestion verified: 25,640,112 parameters<br>> Resolving layer activations..."
  },
  {
    index: 2,
    name: "STAGE 02 // BUILD",
    title: "Layer Topology Assembled.",
    desc: "Deep neural network matrices reconstructed into 5 core computational stages with active tensor conduits.",
    model: "resnet50-v3.pkl",
    params: "5 Stages Active",
    framework: "CUDA 12.1",
    state: "TOPOLOGY MAPPED",
    stateColor: "var(--accent-cyan)",
    cliTag: "STREAM: TENSOR_FLOW",
    cliLines: "> [L1] Conv2D (3x224x224 → 64)<br>> [L2] BatchNorm + ReLU activation<br>> [L3] ResBlock array (x8 Bottleneck)<br>> [L4] Dense feature mapper (2048)<br>> [L5] 1000 Class output logits"
  },
  {
    index: 3,
    name: "STAGE 03 // TEST",
    title: "Volumetric Evaluation.",
    desc: "Luminous multi-axis scanning plane sweeping through all layers — inspecting metadata, robustness, and privacy.",
    model: "resnet50-v3.pkl",
    params: "4 Test Vectors",
    framework: "Eval Engine v1",
    state: "STRESS SCANNING",
    stateColor: "var(--accent-cyan)",
    cliTag: "STREAM: SCAN_VECTORS",
    cliLines: "> Vector 1: Low Light Blur degradation<br>> Vector 2: Motion Blur perturbation<br>> Vector 3: Contrast Drop tolerance<br>> Vector 4: Membership Inference leak check"
  },
  {
    index: 4,
    name: "STAGE 04 // ATTACK",
    title: "Perturbation Attack.",
    desc: "Simulating gradient-based adversarial attack vectors (FGSM/PGD). 3 potential resilience breaches detected.",
    model: "resnet50-v3.pkl",
    params: "3 Breaches Found",
    framework: "Adversarial Lab",
    state: "VULNERABILITY DETECTED",
    stateColor: "var(--color-block)",
    cliTag: "STREAM: THREAT_LOG",
    cliLines: "⚠ Breach: Low Light Blur delta (-0.33)<br>⚠ Breach: Motion Blur sensitivity breach<br>⚠ Breach: Contrast Drop below threshold<br>> Generating reproducibility capsule [capsule-147]"
  },
  {
    index: 5,
    name: "STAGE 05 // SHIELD",
    title: "Model Verified.",
    desc: "Volumetric geometric shield forcefield forms around the model artifact, neutralizing adversarial perturbations.",
    model: "resnet50-v3.pkl",
    params: "Shield Active",
    framework: "Policy Enforced",
    state: "VERIFIED (92/100)",
    stateColor: "var(--color-pass)",
    cliTag: "STREAM: SECURITY_PERIMETER",
    cliLines: "✓ Defense perimeter locked<br>✓ Strict regression gate passed<br>✓ Security Score: 92 / 100 [LOW RISK]<br>✓ Model verified for deployment"
  },
  {
    index: 6,
    name: "STAGE 06 // DEPLOY",
    title: "Ship With Confidence.",
    desc: "Every vulnerability neutralized, regression tests frozen, and CI/CD release gate approved.",
    model: "resnet50-v3.pkl",
    params: "Signed Capsule",
    framework: "Prod Ready",
    state: "GATE: APPROVED",
    stateColor: "var(--color-pass)",
    cliTag: "STREAM: DEPLOY_GATE",
    cliLines: "$ modelshield deploy --production<br>>> Model container signed: capsule-v3.tar.gz<br>>> READY FOR PRODUCTION DEPLOYMENT"
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
});

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

  // Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
  scene.add(ambientLight);

  const dirLight1 = new THREE.DirectionalLight(0x38bdf8, 2.0);
  dirLight1.position.set(10, 12, 10);
  scene.add(dirLight1);

  const dirLight2 = new THREE.DirectionalLight(0x6366f1, 1.5);
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
    opacity: 0.35,
    linewidth: 1.5
  });
  boundingCube = new THREE.LineSegments(boxEdges, boxMat);
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

  const nodeGeometry = new THREE.SphereGeometry(0.12, 16, 16);
  const nodeMaterial = new THREE.MeshStandardMaterial({
    color: 0x38bdf8,
    emissive: 0x0284c7,
    emissiveIntensity: 0.8,
    roughness: 0.2,
    metalness: 0.8
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

  // 1. Smooth Camera Movement towards target position
  currentCamPos.x += (targetCamX - currentCamPos.x) * 0.06;
  currentCamPos.y += (targetCamY - currentCamPos.y) * 0.06;
  currentCamPos.z += (targetCamZ - currentCamPos.z) * 0.06;

  camera.position.set(
    currentCamPos.x + (mouseX * 0.8),
    currentCamPos.y + (mouseY * 0.8),
    currentCamPos.z
  );
  camera.lookAt(currentCamLook.x, currentCamLook.y, currentCamLook.z);

  // 2. Slow Ambient Rotation of the Model Artifact
  if (modelArtifactGroup) {
    modelArtifactGroup.rotation.y = time * 0.12 + (mouseX * 0.2);
    modelArtifactGroup.rotation.x = Math.sin(time * 0.08) * 0.08 + (mouseY * 0.15);
  }

  // 3. Pulse Signal Particles across layers
  if (signalParticles) {
    const pos = signalParticles.geometry.attributes.position.array;
    for (let i = 0; i < pos.length / 3; i++) {
      pos[i * 3] += 0.04;
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
    ambientParticleSystem.rotation.y = time * 0.02;
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

  // --- STAGE 0: HERO (0.0 - 0.12) ---
  if (p < 0.12) {
    targetCamX = 2.8;
    targetCamY = 0.4;
    targetCamZ = 15.5;
    targetCamLook = { x: 0.5, y: 0, z: 0 };

    modelArtifactGroup.scale.setScalar(0.95);
    boundingCube.material.opacity = 0.25;
    scanLaserPlane.material.opacity = 0.0;
    shieldMesh.material.opacity = 0.0;
    attackParticles.material.opacity = 0.0;

    setLayerEmissive(0x0284c7, 0.6);
  }
  // --- STAGE 1: DETECT (0.12 - 0.28) ---
  else if (p < 0.28) {
    const t = (p - 0.12) / 0.16;
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
  // --- STAGE 2: BUILD / ASSEMBLE (0.28 - 0.45) ---
  else if (p < 0.45) {
    const t = (p - 0.28) / 0.17;
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
  // --- STAGE 3: TEST / SCAN (0.45 - 0.62) ---
  else if (p < 0.62) {
    const t = (p - 0.45) / 0.17;
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
  // --- STAGE 4: ATTACK / PERTURBATION (0.62 - 0.78) ---
  else if (p < 0.78) {
    const t = (p - 0.62) / 0.16;
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
  // --- STAGE 5: SHIELD / VERIFICATION (0.78 - 0.92) ---
  else if (p < 0.92) {
    const t = (p - 0.78) / 0.14;
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
  // --- STAGE 6: CLI & DEPLOY MORPH (0.92 - 1.0) ---
  else {
    const t = (p - 0.92) / 0.08;
    targetCamX = 0.0;
    targetCamY = 0.0;
    targetCamZ = 16.0 + t * 4.0;
    targetCamLook = { x: 0, y: 0, z: 0 };

    // Collapse neural layers inward as it transforms into CLI
    modelArtifactGroup.scale.setScalar((1.0 - t * 0.6));
    boundingCube.material.opacity = (1 - t) * 0.4;
    shieldMesh.material.opacity = (1 - t) * 0.6;
    attackParticles.material.opacity = 0.0;

    setLayerEmissive(0x10b981, 0.8);
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

  const heroLayer = document.getElementById("hero-layer");
  const inspectionLayer = document.getElementById("inspection-layer");
  const cliTransformLayer = document.getElementById("cli-transform-layer");
  const progressBar = document.getElementById("story-progress-bar");
  const tagShield = document.getElementById("tag-shield");

  window.addEventListener("scroll", () => {
    const rect = scrollTrack.getBoundingClientRect();
    const totalDist = scrollTrack.offsetHeight - window.innerHeight;
    const currentDist = -rect.top;

    if (totalDist > 0) {
      scrollProgress = Math.max(0, Math.min(1, currentDist / totalDist));
    }

    if (progressBar) {
      progressBar.style.width = `${scrollProgress * 100}%`;
    }

    // Determine current stage index (0 to 6)
    let stageIdx = 0;
    if (scrollProgress < 0.12) stageIdx = 0;
    else if (scrollProgress < 0.28) stageIdx = 1;
    else if (scrollProgress < 0.45) stageIdx = 2;
    else if (scrollProgress < 0.62) stageIdx = 3;
    else if (scrollProgress < 0.78) stageIdx = 4;
    else if (scrollProgress < 0.92) stageIdx = 5;
    else stageIdx = 6;

    if (stageIdx !== currentStage) {
      currentStage = stageIdx;
      updateStageDOM(currentStage);
    }

    // Dynamic Layer Opacity Cross-Fading
    if (heroLayer && inspectionLayer && cliTransformLayer) {
      if (scrollProgress < 0.12) {
        // Hero visible
        const heroOpacity = Math.max(0, 1 - (scrollProgress / 0.12) * 1.5);
        heroLayer.style.opacity = heroOpacity;
        heroLayer.style.pointerEvents = heroOpacity > 0.5 ? "auto" : "none";
        heroLayer.style.transform = `translateY(${-scrollProgress * 150}px)`;

        inspectionLayer.style.opacity = 0;
        inspectionLayer.style.pointerEvents = "none";

        cliTransformLayer.style.opacity = 0;
        cliTransformLayer.style.pointerEvents = "none";
      } else if (scrollProgress < 0.90) {
        // Inspection HUD & 3D dominant (takes 65-70% viewport)
        heroLayer.style.opacity = 0;
        heroLayer.style.pointerEvents = "none";

        inspectionLayer.style.opacity = 1;
        inspectionLayer.style.pointerEvents = "auto";

        cliTransformLayer.style.opacity = 0;
        cliTransformLayer.style.pointerEvents = "none";
      } else {
        // Stage 6 CLI Morph visible
        heroLayer.style.opacity = 0;
        heroLayer.style.pointerEvents = "none";

        const fadeOutInspect = Math.max(0, 1 - (scrollProgress - 0.90) / 0.05);
        inspectionLayer.style.opacity = fadeOutInspect;
        inspectionLayer.style.pointerEvents = "none";

        const fadeInCLI = Math.min(1, (scrollProgress - 0.90) / 0.08);
        cliTransformLayer.style.opacity = fadeInCLI;
        cliTransformLayer.style.pointerEvents = fadeInCLI > 0.5 ? "auto" : "none";
        cliTransformLayer.style.transform = `translateY(${(1 - fadeInCLI) * 30}px)`;
      }
    }

    // Shield Tag state
    if (tagShield) {
      if (currentStage === 5) {
        tagShield.style.opacity = "1";
        tagShield.style.transform = "scale(1)";
      } else {
        tagShield.style.opacity = "0";
        tagShield.style.transform = "scale(0.9)";
      }
    }

    // Update scrubber buttons
    updateScrubberUI(currentStage);
  }, { passive: true });
}

function updateStageDOM(stageIdx) {
  const config = STAGE_CONFIGS[stageIdx];
  if (!config) return;

  const idxEl = document.getElementById("hud-stage-index");
  const titleEl = document.getElementById("hud-stage-title");
  const descEl = document.getElementById("hud-stage-desc");
  const modelEl = document.getElementById("meta-val-model");
  const paramsEl = document.getElementById("meta-val-params");
  const frameworkEl = document.getElementById("meta-val-framework");
  const stateEl = document.getElementById("meta-val-state");
  const cliTagEl = document.getElementById("hud-cli-tag");
  const cliContentEl = document.getElementById("hud-cli-content");

  if (idxEl) idxEl.innerText = config.name;
  if (titleEl) titleEl.innerText = config.title;
  if (descEl) descEl.innerText = config.desc;
  if (modelEl) modelEl.innerText = config.model;
  if (paramsEl) paramsEl.innerText = config.params;
  if (frameworkEl) frameworkEl.innerText = config.framework;
  if (stateEl) {
    stateEl.innerText = config.state;
    stateEl.style.color = config.stateColor;
  }
  if (cliTagEl) cliTagEl.innerText = config.cliTag;
  if (cliContentEl) cliContentEl.innerHTML = config.cliLines;
}

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
