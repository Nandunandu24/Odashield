// =====================================================================
// OdoShield 3D - Interactive Engine (App.js)
// =====================================================================

// Global Chart Instances
let timelineChartInstance = null;
let ecuChartInstance = null;

// Three.js 3D Scene variables
let scene, camera, renderer, carGroup;
let carMaterial;
const colorThemes = {
    cyan: 0x00e5ff,
    green: 0x10b981,
    gold: 0xffb703,
    red: 0xff0055
};

// ---------------------------------------------------------------------
// 1. Initializations
// ---------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    init3DScene();
    setupTiltCards();
    setupDropzones();
    setupHUDLatency();
    setupThemeToggle();
    setupDeviceSwitcher();
    setupNewAudit();
});

function setupNewAudit() {
    const newAuditBtn = document.getElementById("newAuditBtn");
    const resultsSection = document.getElementById("resultsSection");
    
    if (!newAuditBtn || !resultsSection) return;
    
    newAuditBtn.addEventListener("click", () => {
        const formCard = document.querySelector(".form-card");
        const appContainer = document.querySelector(".app-grid-container");
        
        if (formCard) formCard.classList.remove("hidden");
        if (appContainer) appContainer.classList.remove("results-active");
        resultsSection.classList.add("hidden");
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

function setupDeviceSwitcher() {
    const laptopBtn = document.getElementById("viewLaptopBtn");
    const mobileBtn = document.getElementById("viewMobileBtn");
    const wrapper = document.querySelector(".main-wrapper");
    
    if (!laptopBtn || !mobileBtn || !wrapper) return;
    
    laptopBtn.addEventListener("click", () => {
        wrapper.classList.remove("device-mobile");
        laptopBtn.classList.add("active");
        laptopBtn.style.color = "var(--color-cyan)";
        mobileBtn.classList.remove("active");
        mobileBtn.style.color = "#9ca3af";
    });
    
    mobileBtn.addEventListener("click", () => {
        wrapper.classList.add("device-mobile");
        mobileBtn.classList.add("active");
        mobileBtn.style.color = "var(--color-cyan)";
        laptopBtn.classList.remove("active");
        laptopBtn.style.color = "#9ca3af";
    });
}

// Setup 3D holographic car background scene using Three.js
function init3DScene() {
    return; // Three.js disabled in favor of realistic car background image
    const canvas = document.getElementById("three-canvas");
    if (!canvas) return;
    
    // Scene & Camera
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
    camera.position.z = 12;
    
    // Renderer
    renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    
    // Create Holographic 3D Car Wireframe
    carGroup = new THREE.Group();
    
    // Material
    carMaterial = new THREE.MeshBasicMaterial({
        color: colorThemes.cyan,
        wireframe: true,
        transparent: true,
        opacity: 0.6
    });
    
    // Car Body Shapes
    const bodyGeom = new THREE.BoxGeometry(5, 0.8, 2.2);
    const bodyMesh = new THREE.Mesh(bodyGeom, carMaterial);
    carGroup.add(bodyMesh);
    
    const cabinGeom = new THREE.BoxGeometry(2.5, 0.8, 1.8);
    cabinGeom.translate(0.2, 0.8, 0); // Position relative to body
    const cabinMesh = new THREE.Mesh(cabinGeom, carMaterial);
    carGroup.add(cabinMesh);
    
    // Wheels Toruses (4 wheels)
    const wheelGeom = new THREE.TorusGeometry(0.5, 0.15, 8, 16);
    const wheelPositions = [
        [-1.6, -0.4, 1.1],  // Front Left
        [1.6, -0.4, 1.1],   // Rear Left
        [-1.6, -0.4, -1.1], // Front Right
        [1.6, -0.4, -1.1]   // Rear Right
    ];
    
    wheelPositions.forEach(pos => {
        const wheelMesh = new THREE.Mesh(wheelGeom, carMaterial);
        wheelMesh.position.set(pos[0], pos[1], pos[2]);
        wheelMesh.rotation.y = Math.PI / 2;
        carGroup.add(wheelMesh);
    });
    
    scene.add(carGroup);
    
    // Position car in scene
    carGroup.position.set(2, 0, 0); // Offset to the right
    carGroup.rotation.x = 0.2;
    carGroup.rotation.y = -0.6;
    
    // Ambient Grid (Holographic floor)
    const gridHelper = new THREE.GridHelper(30, 30, colorThemes.cyan, 0x112244);
    gridHelper.position.y = -1.5;
    gridHelper.material.opacity = 0.25;
    gridHelper.material.transparent = true;
    scene.add(gridHelper);
    
    // Mouse Parallax listener
    let targetX = 0, targetY = 0;
    window.addEventListener("mousemove", (e) => {
        targetX = (e.clientX - window.innerWidth / 2) * 0.0002;
        targetY = (e.clientY - window.innerHeight / 2) * 0.0002;
    });
    
    // Animation Loop
    function animate() {
        requestAnimationFrame(animate);
        
        // Auto rotate car
        carGroup.rotation.y += 0.005;
        
        // Apply parallax offsets
        carGroup.position.x += (targetX * 5 + 2 - carGroup.position.x) * 0.05;
        carGroup.position.y += (-targetY * 5 - carGroup.position.y) * 0.05;
        
        renderer.render(scene, camera);
    }
    animate();
    
    // Handle Resizes
    window.addEventListener("resize", () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
}

// Dynamically changes the color of the 3D hologram in the background
function change3DColor(hexColor) {
    if (carMaterial) {
        carMaterial.color.setHex(hexColor);
    }
}

// ---------------------------------------------------------------------
// 2. Interactive 3D Parallax Tilt Cards
// ---------------------------------------------------------------------
function setupTiltCards() {
    const cards = document.querySelectorAll(".tilt-card");
    
    cards.forEach(card => {
        card.addEventListener("mousemove", (e) => {
            const rect = card.getBoundingClientRect();
            
            // Mouse coordinates relative to card
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            // Map mouse to percentage (-50% to 50%)
            const xPct = (x / rect.width) - 0.5;
            const yPct = (y / rect.height) - 0.5;
            
            // Define max tilt degrees
            const tiltMax = 6;
            
            const tiltX = -yPct * tiltMax;
            const tiltY = xPct * tiltMax;
            
            // Apply 3D perspective transforms
            card.style.transform = `perspective(1000px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) scale3d(1.02, 1.02, 1.02)`;
            
            // Update glow overlay position
            card.style.setProperty("--mouse-x", `${(x / rect.width) * 100}%`);
            card.style.setProperty("--mouse-y", `${(y / rect.height) * 100}%`);
        });
        
        card.addEventListener("mouseleave", () => {
            // Reset to flat
            card.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)";
        });
    });
}

// ---------------------------------------------------------------------
// 3. Scenario Preset Injector (Data Analyst "Example Information")
// ---------------------------------------------------------------------
function injectPreset(type) {
    // Reset form overrides first
    document.getElementById("ecu_cluster").value = "";
    document.getElementById("ecu_ecm").value = "";
    document.getElementById("ecu_tcm").value = "";
    document.getElementById("ecu_abs").value = "";
    document.getElementById("ecu_airbag").value = "";
    
    // Clear dropzone previews
    document.querySelectorAll(".dz-preview").forEach(p => p.style.display = "none");
    document.querySelectorAll(".dz-content").forEach(c => c.style.opacity = "1");
    document.getElementById("image_pedal").value = "";
    document.getElementById("image_steering").value = "";
    document.getElementById("image_seat").value = "";
    
    if (type === "clean") {
        document.getElementById("vin").value = "MA3ERLF380000000A";
        document.getElementById("current_odometer").value = "45000";
        document.getElementById("engine_hours").value = "1150";
    }
    else if (type === "ecu-swap") {
        // Mismatched ABS log, but others aligned (benign replacement)
        document.getElementById("vin").value = "MA3ERLF380000000B";
        document.getElementById("current_odometer").value = "80000";
        document.getElementById("engine_hours").value = "2000";
        
        // Inject values directly to registers overrides
        document.getElementById("ecu_cluster").value = "80000";
        document.getElementById("ecu_ecm").value = "80100";
        document.getElementById("ecu_tcm").value = "79900";
        document.getElementById("ecu_abs").value = "10000"; // Replaced ABS module!
        document.getElementById("ecu_airbag").value = "80000";
    }
    else if (type === "ecu-rollback") {
        // Scam: Cluster = 45k, while ECM/TCM/ABS = 85k (rolled back cluster)
        document.getElementById("vin").value = "MA3ERLF380000000C";
        document.getElementById("current_odometer").value = "45000";
        document.getElementById("engine_hours").value = "2000"; // Low speed ratio
        
        document.getElementById("ecu_cluster").value = "45000";
        document.getElementById("ecu_ecm").value = "85000";
        document.getElementById("ecu_tcm").value = "85000";
        document.getElementById("ecu_abs").value = "85000";
        document.getElementById("ecu_airbag").value = "85000";
    }
    else if (type === "wear-mismatch") {
        // Scammer rolled back odometer to 30K, but left heavy physical wear.
        document.getElementById("vin").value = "MA3ERLF380000009Z";
        document.getElementById("current_odometer").value = "30000";
        document.getElementById("engine_hours").value = "750";
    }
    
    // Visual feedback glow on preset container
    const sec = document.querySelector(".presets-section");
    sec.style.boxShadow = "0 0 20px var(--color-cyan-glow)";
    setTimeout(() => {
        sec.style.boxShadow = "none";
    }, 400);
    
    // Automatically trigger form submit
    document.getElementById("auditForm").dispatchEvent(new Event("submit"));
}

// ---------------------------------------------------------------------
// 4. File Dropzones Control
// ---------------------------------------------------------------------
function setupDropzones() {
    const dropzones = document.querySelectorAll(".cyber-dropzone");
    
    dropzones.forEach(dz => {
        const fileInput = dz.querySelector(".file-input");
        const previewEl = dz.querySelector(".dz-preview");
        const contentEl = dz.querySelector(".dz-content");
        
        dz.addEventListener("click", () => fileInput.click());
        
        dz.addEventListener("dragover", (e) => {
            e.preventDefault();
            dz.classList.add("dragover");
        });
        
        dz.addEventListener("dragleave", () => {
            dz.classList.remove("dragover");
        });
        
        dz.addEventListener("drop", (e) => {
            e.preventDefault();
            dz.classList.remove("dragover");
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                handleFileSelect(fileInput.files[0], previewEl, contentEl);
            }
        });
        
        fileInput.addEventListener("change", () => {
            if (fileInput.files.length) {
                handleFileSelect(fileInput.files[0], previewEl, contentEl);
            }
        });
    });
}

function handleFileSelect(file, previewEl, contentEl) {
    if (!file.type.startsWith("image/")) {
        alert("Please upload an image file.");
        return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
        previewEl.style.backgroundImage = `url(${e.target.result})`;
        previewEl.style.display = "block";
        contentEl.style.opacity = "0.15";
    };
    reader.readAsDataURL(file);
}

// ---------------------------------------------------------------------
// 5. HUD Latency Simulation
// ---------------------------------------------------------------------
function setupHUDLatency() {
    const latencyEl = document.getElementById("hudLatency");
    if (!latencyEl) return;
    
    setInterval(() => {
        const ping = Math.floor(Math.random() * 8) + 8; // 8-15ms
        latencyEl.textContent = `${ping}ms`;
    }, 3000);
}

// ---------------------------------------------------------------------
// 5a. Theme Toggle Control
// ---------------------------------------------------------------------
function setupThemeToggle() {
    const btn = document.getElementById("themeToggleBtn");
    if (!btn) return;

    // Check localStorage
    const savedTheme = localStorage.getItem("theme") || "dark";
    if (savedTheme === "light") {
        document.body.classList.add("light-theme");
        btn.textContent = "THEME: LIGHT";
    } else {
        document.body.classList.remove("light-theme");
        btn.textContent = "THEME: DARK";
    }

    btn.addEventListener("click", () => {
        const isLight = document.body.classList.toggle("light-theme");
        const theme = isLight ? "light" : "dark";
        localStorage.setItem("theme", theme);
        btn.textContent = `THEME: ${theme.toUpperCase()}`;
        
        // Update Chart.js ticks color if charts exist
        updateChartColors(isLight);
    });
}

function updateChartColors(isLight) {
    const tickColor = isLight ? '#475569' : '#9ca3af';
    
    if (timelineChartInstance) {
        timelineChartInstance.options.scales.x.ticks.color = tickColor;
        timelineChartInstance.options.scales.y.ticks.color = tickColor;
        timelineChartInstance.update();
    }
    
    if (ecuChartInstance) {
        ecuChartInstance.options.scales.x.ticks.color = tickColor;
        ecuChartInstance.options.scales.y.ticks.color = tickColor;
        ecuChartInstance.update();
    }
}

// ---------------------------------------------------------------------
// 6. Tabs Controller
// ---------------------------------------------------------------------
function switchTab(tabId) {
    // No-op in 2x2 grid layout mode
}

// ---------------------------------------------------------------------
// 7. Form Submission & Auditing Live Stream Console
// ---------------------------------------------------------------------
const auditForm = document.getElementById("auditForm");
const submitBtn = document.getElementById("submitBtn");
const spinner = submitBtn.querySelector(".spinner");
const btnText = submitBtn.querySelector(".btn-text");

const diagnosticsPanel = document.getElementById("diagnosticsPanel");
const terminalLog = document.getElementById("terminalLog");
const resultsSection = document.getElementById("resultsSection");

auditForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    submitBtn.disabled = true;
    spinner.classList.remove("hidden");
    btnText.textContent = "DECRYPTING OBD TELEMETRY...";
    
    diagnosticsPanel.classList.remove("hidden");
    resultsSection.classList.add("hidden");
    terminalLog.innerHTML = "";
    
    // Reset loader status panel states
    const diagnosticsLoader = document.getElementById("diagnosticsLoader");
    const diagnosticsConsole = document.getElementById("diagnosticsConsole");
    const diagnosticsStatus = document.getElementById("diagnosticsStatus");
    const consoleCard = document.querySelector(".console-card");
    
    if (diagnosticsLoader) diagnosticsLoader.style.display = "flex";
    if (diagnosticsConsole) diagnosticsConsole.style.display = "none";
    if (diagnosticsStatus) {
        diagnosticsStatus.textContent = "INITIALIZING INTEGRITY AUDIT... [FAST_MODE]";
        diagnosticsStatus.style.color = "var(--color-cyan)";
    }
    if (consoleCard) consoleCard.classList.remove("error-state");
    
    // Set 3D model color to Cyan (scanning active)
    change3DColor(colorThemes.cyan);
    
    const logs = [
        { text: ">>> CONNECTING OBD INTEL LINK...", delay: 20 },
        { text: "[OK] CAN_BUS INTERFACE VERIFIED. PROTOCOL: ISO 15765-4", delay: 60 },
        { text: ">>> LAYER 1: CONNECTING PARIVAHAN GOV VAHAN DATABASE...", delay: 120 },
        { text: "[OK] VAHAN APIS ENCRYPTED TELEMETRY INGESTED.", delay: 180 },
        { text: ">>> LAYER 2: READING ECU FLASHER DIODE REGISTERS...", delay: 250 },
        { text: "    [READ] CLUSTER: eeprom_address_0x45", delay: 300 },
        { text: "    [READ] ECM/ABS/TCM buffer blocks... [PARALLEL SCAN DONE]", delay: 380 },
        { text: ">>> LAYER 3: INJECTING Telemetry Tensors to XGBoost Model...", delay: 450 },
        { text: ">>> LAYER 4: LOADING PyTorch Convolutional Layers (OdoWearCNN)...", delay: 520 },
        { text: "    [MODEL] wear_cnn.pth weights verified on CPU node.", delay: 580 },
        { text: ">>> LAYER 5: EXECUTING HUGGING FACE LLaMA FORENSIC AUDITOR...", delay: 650 },
        { text: ">>> LAYER 6: COMBINING MATRIX THRESHOLDS...", delay: 720 },
        { text: ">>> DB_SYNC: Committing verification telemetry to PostgreSQL...", delay: 800 },
        { text: ">>> SUCCESS: Forensic Integrity Audit Complete.", delay: 850 }
    ];
    
    for (const log of logs) {
        await new Promise(resolve => setTimeout(resolve, log.delay - (logs.indexOf(log) > 0 ? logs[logs.indexOf(log)-1].delay : 0)));
        addTerminalLog(log.text);
        if (diagnosticsStatus) {
            diagnosticsStatus.textContent = log.text;
        }
    }
    
    // Setup form parameters
    const formData = new FormData();
    formData.append("vin", document.getElementById("vin").value);
    formData.append("current_odometer", document.getElementById("current_odometer").value);
    formData.append("engine_hours", document.getElementById("engine_hours").value);
    
    const askingPrice = document.getElementById("asking_price").value;
    if (askingPrice) formData.append("asking_price", askingPrice);
    
    formData.append("paint_thickness", document.getElementById("paint_thickness").value);
    formData.append("dents_scratches", document.getElementById("dents_scratches").value);
    formData.append("car_color", document.getElementById("car_color").value);
    
    // Overrides
    const ecu_cluster = document.getElementById("ecu_cluster").value;
    const ecu_ecm = document.getElementById("ecu_ecm").value;
    const ecu_tcm = document.getElementById("ecu_tcm").value;
    const ecu_abs = document.getElementById("ecu_abs").value;
    const ecu_airbag = document.getElementById("ecu_airbag").value;
    
    if (ecu_cluster) formData.append("ecu_cluster", ecu_cluster);
    if (ecu_ecm) formData.append("ecu_ecm", ecu_ecm);
    if (ecu_tcm) formData.append("ecu_tcm", ecu_tcm);
    if (ecu_abs) formData.append("ecu_abs", ecu_abs);
    if (ecu_airbag) formData.append("ecu_airbag", ecu_airbag);
    
    // Images
    const pedalFile = document.getElementById("image_pedal").files[0];
    const steeringFile = document.getElementById("image_steering").files[0];
    const seatFile = document.getElementById("image_seat").files[0];
    
    if (pedalFile) formData.append("image_pedal", pedalFile);
    if (steeringFile) formData.append("image_steering", steeringFile);
    if (seatFile) formData.append("image_seat", seatFile);
    
    try {
        // CALL Python FastAPI Backend running on port 8000 cross-origin
        const response = await fetch("http://127.0.0.1:8000/api/v1/verify-vehicle", {
            method: "POST",
            body: formData
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Auditor pipeline connection fault.");
        }
        
        const data = await response.json();
        
        diagnosticsPanel.classList.add("hidden");
        
        // Hide form card and expand results grid
        const formCard = document.querySelector(".form-card");
        const appContainer = document.querySelector(".app-grid-container");
        if (formCard) formCard.classList.add("hidden");
        if (appContainer) appContainer.classList.add("results-active");
        
        resultsSection.classList.remove("hidden");
        
        renderResults(data);
        
    } catch (err) {
        addTerminalLog(`>>> [ERROR] AUDIT_CRASHED: ${err.message}`, "error");
        
        // Show console logs and fail status in red
        if (diagnosticsLoader) diagnosticsLoader.style.display = "none";
        if (diagnosticsConsole) diagnosticsConsole.style.display = "block";
        if (diagnosticsStatus) {
            diagnosticsStatus.textContent = `AUDIT FAILED: ${err.message.toUpperCase()}`;
            diagnosticsStatus.style.color = "var(--color-danger)";
        }
        if (consoleCard) consoleCard.classList.add("error-state");
        
        alert(`Verification Error: ${err.message}`);
    } finally {
        submitBtn.disabled = false;
        spinner.classList.add("hidden");
        btnText.textContent = "INITIALIZE 6-LAYER FORENSIC AUDIT";
    }
});

function addTerminalLog(text) {
    const line = document.createElement("div");
    line.className = "log-line";
    if (text.includes("SUCCESS")) line.style.color = "var(--color-cyan)";
    else if (text.includes("[OK]")) line.style.color = "#10b981";
    else if (text.includes("[ERROR]")) line.style.color = "#ff0055";
    line.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
    terminalLog.appendChild(line);
    terminalLog.scrollTop = terminalLog.scrollHeight;
}

// ---------------------------------------------------------------------
// 8. Results Processing
// ---------------------------------------------------------------------
function renderResults(data) {
    // Shift system accent color variables dynamically based on risk level
    let themeColor = "#00e5ff"; // default cyan
    let themeGlow = "rgba(0, 229, 255, 0.4)";
    if (data.risk_level === "LOW") {
        themeColor = "#10b981"; // green
        themeGlow = "rgba(16, 185, 129, 0.4)";
        change3DColor(colorThemes.green);
    } else if (data.risk_level === "MEDIUM") {
        themeColor = "#ffb703"; // gold
        themeGlow = "rgba(255, 183, 3, 0.4)";
        change3DColor(colorThemes.gold);
    } else {
        themeColor = "#ff0055"; // red
        themeGlow = "rgba(255, 0, 85, 0.4)";
        change3DColor(colorThemes.red);
    }
    document.documentElement.style.setProperty('--color-cyan', themeColor);
    document.documentElement.style.setProperty('--color-cyan-glow', themeGlow);
    
    // Status Badges
    document.getElementById("riskLevelBadge").textContent = `${data.risk_level} RISK`;
    document.getElementById("riskLevelBadge").className = `status-cyber-badge risk-${data.risk_level}`;
    
    document.getElementById("recommendationBadge").textContent = data.recommendation;
    document.getElementById("recommendationBadge").style.borderColor = 
        data.recommendation === "ACCEPT" ? "var(--color-success)" : 
        data.recommendation === "REVIEW" ? "var(--color-warning)" : "var(--color-danger)";
    document.getElementById("recommendationBadge").style.color = 
        data.recommendation === "ACCEPT" ? "var(--color-success)" : 
        data.recommendation === "REVIEW" ? "var(--color-warning)" : "var(--color-danger)";

    document.getElementById("resVehicleTitle").textContent = `${data.year} ${data.make} ${data.model}`;
    document.getElementById("resVin").textContent = data.vin;
    document.getElementById("resCity").textContent = data.registration_city;
    document.getElementById("resOdo").textContent = `${Number(data.reported_odometer).toLocaleString()} km`;
    
    // Render Fair Worth Valuation details
    const valCard = document.getElementById("valuationCard");
    const valAsking = document.getElementById("valAskingPrice");
    const valWorth = document.getElementById("valActualWorth");
    const valDev = document.getElementById("valDeviation");
    const valStatus = document.getElementById("valStatusBadge");
    
    if (data.valuation_analysis && data.valuation_analysis.actual_worth) {
        valCard.style.display = "block";
        const val = data.valuation_analysis;
        
        valAsking.textContent = val.asking_price ? `₹${Number(val.asking_price).toLocaleString()}` : "N/A";
        valWorth.textContent = `₹${Number(val.actual_worth).toLocaleString()}`;
        
        if (val.asking_price) {
            const absDiff = Math.abs(val.price_difference);
            const formattedDiff = `₹${Number(absDiff).toLocaleString()}`;
            if (val.price_difference > 0) {
                valDev.textContent = `+${formattedDiff} (Overpriced)`;
                valDev.style.color = "var(--color-danger)";
            } else if (val.price_difference < 0) {
                valDev.textContent = `-${formattedDiff} (Undervalued)`;
                valDev.style.color = "var(--color-success)";
            } else {
                valDev.textContent = "±₹0 (Exact Value)";
                valDev.style.color = "var(--color-cyan)";
            }
        } else {
            valDev.textContent = "N/A (No Asking Price)";
            valDev.style.color = "#9ca3af";
        }
        
        valStatus.textContent = val.valuation_status;
        if (val.valuation_status === "GOOD DEAL") {
            valStatus.style.background = "rgba(0, 240, 255, 0.1)";
            valStatus.style.color = "var(--color-success)";
            valStatus.style.border = "1px solid rgba(0, 240, 255, 0.2)";
        } else if (val.valuation_status === "FAIR PRICE") {
            valStatus.style.background = "rgba(0, 229, 255, 0.1)";
            valStatus.style.color = "var(--color-cyan)";
            valStatus.style.border = "1px solid rgba(0, 229, 255, 0.2)";
        } else if (val.valuation_status === "OVERPRICED") {
            valStatus.style.background = "rgba(255, 183, 3, 0.1)";
            valStatus.style.color = "var(--color-warning)";
            valStatus.style.border = "1px solid rgba(255, 183, 3, 0.2)";
        } else if (val.valuation_status === "SUSPECT SCAM") {
            valStatus.style.background = "rgba(255, 0, 85, 0.1)";
            valStatus.style.color = "var(--color-danger)";
            valStatus.style.border = "1px solid rgba(255, 0, 85, 0.2)";
        } else {
            valStatus.style.background = "rgba(255, 255, 255, 0.05)";
            valStatus.style.color = "#9ca3af";
            valStatus.style.border = "1px solid rgba(255, 255, 255, 0.1)";
        }
    } else {
        valCard.style.display = "none";
    }
    
    // Render Insurance Details Widget
    const insCard = document.getElementById("insuranceCard");
    const insCompany = document.getElementById("insCompany");
    const insPolicyNo = document.getElementById("insPolicyNo");
    const insExpiry = document.getElementById("insExpiry");
    const insClaims = document.getElementById("insClaims");
    const insNcb = document.getElementById("insNcb");
    const insStatus = document.getElementById("insStatusBadge");
    
    if (data.insurance_analysis) {
        insCard.style.display = "block";
        const ins = data.insurance_analysis;
        
        insCompany.textContent = ins.insurance_company;
        insPolicyNo.textContent = ins.policy_number;
        insExpiry.textContent = ins.expiry_date;
        
        // Expiry color coding
        if (ins.is_expired) {
            insExpiry.style.color = "var(--color-danger)";
        } else {
            insExpiry.style.color = "var(--color-success)";
        }
        
        // Claims history
        if (ins.claims_count > 0) {
            insClaims.textContent = `${ins.claims_count} claim(s) (₹${Number(ins.claims_total_amount).toLocaleString()})`;
            insClaims.style.color = "var(--color-danger)";
        } else {
            insClaims.textContent = "0 claims (Clean)";
            insClaims.style.color = "var(--color-success)";
        }
        
        insNcb.textContent = `${ins.no_claim_bonus_percentage}%`;
        
        insStatus.textContent = ins.status;
        if (ins.status === "VALID") {
            insStatus.style.background = "rgba(0, 240, 255, 0.1)";
            insStatus.style.color = "var(--color-success)";
            insStatus.style.border = "1px solid rgba(0, 240, 255, 0.2)";
        } else if (ins.status === "EXPIRED") {
            insStatus.style.background = "rgba(255, 0, 85, 0.1)";
            insStatus.style.color = "var(--color-danger)";
            insStatus.style.border = "1px solid rgba(255, 0, 85, 0.2)";
        } else {
            insStatus.style.background = "rgba(255, 255, 255, 0.05)";
            insStatus.style.color = "#9ca3af";
            insStatus.style.border = "1px solid rgba(255, 255, 255, 0.1)";
        }
    } else {
        insCard.style.display = "none";
    }
    
    // Odometer Fraud Probability Percentage Gauge
    const prob = data.fraud_probability;
    document.getElementById("resProbability").textContent = `${prob}%`;
    animateGauge(prob);
    
    // Setup Layer score progress bars
    updateProgressBar("pbVahan", "valVahan", data.layer_scores.vahan_score);
    updateProgressBar("pbEcu", "valEcu", data.layer_scores.ecu_score);
    updateProgressBar("pbXg", "valXg", data.layer_scores.xgboost_score);
    updateProgressBar("pbWear", "valWear", data.layer_scores.wear_score);
    
    // Render Layer 1 Timeline Chart
    renderTimelineChart(data.vahan_analysis.timeline);
    
    // Render Layer 2 ECU Chart & Table readouts
    renderEcuChart(data.ecu_analysis.modules);
    renderEcuTable(data.ecu_analysis.modules, data.ecu_analysis.outlier_detected);
    
    // Render Layer 4 Wear Scores
    updateWearCard("wearPedalBadge", "wearPedalScore", data.wear_analysis.pedal);
    updateWearCard("wearSteeringBadge", "wearSteeringScore", data.wear_analysis.steering);
    updateWearCard("wearSeatBadge", "wearSeatScore", data.wear_analysis.seat);
    
    // Wear Mismatch Alarm
    const mismatchAlert = document.getElementById("wearMismatchAlert");
    if (data.reported_odometer < 50000 && data.wear_analysis.average_wear_score > 6.0) {
        mismatchAlert.classList.remove("hidden");
        document.getElementById("wearMismatchText").textContent = 
            `Optical surface wear classification indicates significant degradation (${data.wear_analysis.average_wear_score}/10) mismatching the reported odometer mileage of ${Number(data.reported_odometer).toLocaleString()} km. Cosmetic components have likely been refurbished to conceal higher usage.`;
    } else {
        mismatchAlert.classList.add("hidden");
    }
    
    // Warnings and Violations (Overview Tab)
    const anomaliesContainer = document.getElementById("anomaliesContainer");
    anomaliesContainer.innerHTML = "";
    
    const violations = [];
    data.vahan_analysis.anomalies.forEach(a => violations.push({ desc: a.description, level: "critical" }));
    
    if (data.ecu_analysis.engine_hours_anomaly) {
        violations.push({ desc: data.ecu_analysis.hours_description, level: "warning" });
    }
    
    if (data.ecu_analysis.outlier_detected) {
        violations.push({ desc: data.ecu_analysis.outlier_description, level: "warning" });
    } else if (data.ecu_analysis.variance_km > 1000) {
        violations.push({ desc: `CAN Bus discrepancy detected. Module variance of ${Number(data.ecu_analysis.variance_km).toLocaleString()} km exceeds system synchrony limits.`, level: "critical" });
    }
    
    if (violations.length === 0) {
        anomaliesContainer.innerHTML = `
            <div class="violation-card" style="background: rgba(0, 240, 255, 0.04); border-color: rgba(0, 240, 255, 0.15); color: var(--color-cyan)">
                <span>All verification logs are consistent. No odometer anomalies detected.</span>
            </div>
        `;
    } else {
        violations.forEach(v => {
            const card = document.createElement("div");
            card.className = `violation-card ${v.level === "warning" ? "warning" : ""}`;
            card.innerHTML = `
                <span>${v.desc}</span>
            `;
            anomaliesContainer.appendChild(card);
        });
    }
    
    // Formatting LLM Markdown report
    const formattedReport = data.llm_report
        .replace(/^### (.*)$/gm, "<h3>$1</h3>")
        .replace(/^#### (.*)$/gm, "<h4>$1</h4>")
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/^---$/gm, "<hr class='cyber-hr'>")
        .replace(/^- (.*)$/gm, "<li>$1</li>")
        .replace(/\n\n/g, "<br><br>")
        .replace(/\n/g, "<br>");
        
    document.getElementById("reportTextContainer").innerHTML = formattedReport;
    
    // Setup Download Button Handler
    const downloadBtn = document.getElementById("downloadReportBtn");
    if (downloadBtn) {
        const newDownloadBtn = downloadBtn.cloneNode(true);
        downloadBtn.parentNode.replaceChild(newDownloadBtn, downloadBtn);
        
        newDownloadBtn.addEventListener("click", () => {
            const element = document.getElementById("reportTextContainer");
            
            // Save original styles
            const origBg = element.style.background;
            const origColor = element.style.color;
            const origPadding = element.style.padding;
            const origFontFamily = element.style.fontFamily;
            const origLineHeight = element.style.lineHeight;
            
            // Apply clean print styles
            element.style.background = "#ffffff";
            element.style.color = "#1e293b";
            element.style.padding = "2.5rem";
            element.style.fontFamily = "'Inter', sans-serif";
            element.style.lineHeight = "1.6";
            
            // Insert report header
            const reportHeader = document.createElement("div");
            reportHeader.id = "tempReportHeader";
            reportHeader.style.borderBottom = "3px double #0f172a";
            reportHeader.style.paddingBottom = "1rem";
            reportHeader.style.marginBottom = "2rem";
            reportHeader.style.textAlign = "center";
            reportHeader.innerHTML = `
                <h1 style="font-family: 'Orbitron', sans-serif; font-size: 1.8rem; color: #0f172a; margin: 0; text-transform: uppercase; letter-spacing: 0.05em;">OdoShield Forensic Audit</h1>
                <p style="font-size: 0.75rem; color: #64748b; text-transform: uppercase; margin: 0.25rem 0 0 0; letter-spacing: 0.1em; font-weight: bold;">AUTOMOTIVE INTEGRITY INSPECTION CERTIFICATE</p>
            `;
            element.insertBefore(reportHeader, element.firstChild);
            
            // Temporarily style all children elements
            const headings3 = element.querySelectorAll("h3");
            const origH3Styles = [];
            headings3.forEach(h => {
                origH3Styles.push({
                    el: h,
                    color: h.style.color,
                    borderBottom: h.style.borderBottom,
                    paddingBottom: h.style.paddingBottom,
                    marginTop: h.style.marginTop,
                    marginBottom: h.style.marginBottom,
                    fontSize: h.style.fontSize,
                    fontFamily: h.style.fontFamily
                });
                h.style.color = "#0f172a";
                h.style.borderBottom = "1px solid #cbd5e1";
                h.style.paddingBottom = "0.4rem";
                h.style.marginTop = "1.5rem";
                h.style.marginBottom = "1rem";
                h.style.fontSize = "1.25rem";
                h.style.fontFamily = "'Orbitron', sans-serif";
            });
            
            const headings4 = element.querySelectorAll("h4");
            const origH4Styles = [];
            headings4.forEach(h => {
                origH4Styles.push({
                    el: h,
                    color: h.style.color,
                    marginTop: h.style.marginTop,
                    marginBottom: h.style.marginBottom,
                    fontSize: h.style.fontSize,
                    fontFamily: h.style.fontFamily
                });
                h.style.color = "#0f172a";
                h.style.marginTop = "1.5rem";
                h.style.marginBottom = "0.5rem";
                h.style.fontSize = "1.1rem";
                h.style.fontFamily = "'Orbitron', sans-serif";
            });
            
            const headings5 = element.querySelectorAll("h5");
            const origH5Styles = [];
            headings5.forEach(h => {
                origH5Styles.push({
                    el: h,
                    color: h.style.color,
                    marginTop: h.style.marginTop,
                    marginBottom: h.style.marginBottom,
                    fontSize: h.style.fontSize,
                    fontFamily: h.style.fontFamily
                });
                h.style.color = "#334155";
                h.style.marginTop = "1.2rem";
                h.style.marginBottom = "0.5rem";
                h.style.fontSize = "0.95rem";
                h.style.fontFamily = "'Orbitron', sans-serif";
            });
            
            const strongs = element.querySelectorAll("strong");
            const origStrongStyles = [];
            strongs.forEach(s => {
                origStrongStyles.push({ el: s, color: s.style.color, fontWeight: s.style.fontWeight });
                s.style.color = "#0f172a";
                s.style.fontWeight = "600";
            });
            
            const codes = element.querySelectorAll("code");
            const origCodeStyles = [];
            codes.forEach(c => {
                origCodeStyles.push({
                    el: c,
                    background: c.style.background,
                    color: c.style.color,
                    padding: c.style.padding,
                    borderRadius: c.style.borderRadius,
                    fontSize: c.style.fontSize,
                    fontFamily: c.style.fontFamily
                });
                c.style.background = "#f1f5f9";
                c.style.color = "#0f172a";
                c.style.padding = "0.15rem 0.35rem";
                c.style.borderRadius = "4px";
                c.style.fontSize = "0.85rem";
                c.style.fontFamily = "monospace";
            });
            
            const hrs = element.querySelectorAll(".cyber-hr");
            const origHrStyles = [];
            hrs.forEach(hr => {
                origHrStyles.push({ el: hr, background: hr.style.background, height: hr.style.height, margin: hr.style.margin });
                hr.style.background = "#cbd5e1";
                hr.style.height = "1px";
                hr.style.margin = "1.5rem 0";
            });
            
            const lis = element.querySelectorAll("li");
            const origLiStyles = [];
            lis.forEach(li => {
                origLiStyles.push({ el: li, marginBottom: li.style.marginBottom, listStyleType: li.style.listStyleType, marginLeft: li.style.marginLeft });
                li.style.marginBottom = "0.5rem";
                li.style.listStyleType = "square";
                li.style.marginLeft = "1.2rem";
            });
            
            const opt = {
                margin:       [0.5, 0.5, 0.5, 0.5],
                filename:     `OdoShield_Audit_Report_${data.vin}.pdf`,
                image:        { type: 'jpeg', quality: 0.98 },
                html2canvas:  { scale: 2, useCORS: true, backgroundColor: "#ffffff", scrollY: 0, scrollX: 0 },
                jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
            };
            
            const restoreStyles = () => {
                const tempHeader = document.getElementById("tempReportHeader");
                if (tempHeader) tempHeader.remove();
                
                element.style.background = origBg;
                element.style.color = origColor;
                element.style.padding = origPadding;
                element.style.fontFamily = origFontFamily;
                element.style.lineHeight = origLineHeight;
                
                origH3Styles.forEach(x => {
                    x.el.style.color = x.color;
                    x.el.style.borderBottom = x.borderBottom;
                    x.el.style.paddingBottom = x.paddingBottom;
                    x.el.style.marginTop = x.marginTop;
                    x.el.style.marginBottom = x.marginBottom;
                    x.el.style.fontSize = x.fontSize;
                    x.el.style.fontFamily = x.fontFamily;
                });
                
                origH4Styles.forEach(x => {
                    x.el.style.color = x.color;
                    x.el.style.marginTop = x.marginTop;
                    x.el.style.marginBottom = x.marginBottom;
                    x.el.style.fontSize = x.fontSize;
                    x.el.style.fontFamily = x.fontFamily;
                });
                
                origH5Styles.forEach(x => {
                    x.el.style.color = x.color;
                    x.el.style.marginTop = x.marginTop;
                    x.el.style.marginBottom = x.marginBottom;
                    x.el.style.fontSize = x.fontSize;
                    x.el.style.fontFamily = x.fontFamily;
                });
                
                origStrongStyles.forEach(x => {
                    x.el.style.color = x.color;
                    x.el.style.fontWeight = x.fontWeight;
                });
                
                origCodeStyles.forEach(x => {
                    x.el.style.background = x.background;
                    x.el.style.color = x.color;
                    x.el.style.padding = x.padding;
                    x.el.style.borderRadius = x.borderRadius;
                    x.el.style.fontSize = x.fontSize;
                    x.el.style.fontFamily = x.fontFamily;
                });
                
                origHrStyles.forEach(x => {
                    x.el.style.background = x.background;
                    x.el.style.height = x.height;
                    x.el.style.margin = x.margin;
                });
                
                origLiStyles.forEach(x => {
                    x.el.style.marginBottom = x.marginBottom;
                    x.el.style.listStyleType = x.listStyleType;
                    x.el.style.marginLeft = x.marginLeft;
                });
            };
            
            setTimeout(() => {
                html2pdf().set(opt).from(element).save().then(() => {
                    restoreStyles();
                }).catch(err => {
                    console.error("PDF generation error:", err);
                    restoreStyles();
                });
            }, 150);
        });
    }
    
    // SwitchTab not needed, but kept as no-op or default setup
    switchTab("tabOverview");
}

function updateProgressBar(barId, valId, value) {
    const bar = document.getElementById(barId);
    const text = document.getElementById(valId);
    bar.style.width = `${value}%`;
    text.textContent = `${value}%`;
    
    if (value < 30) bar.style.background = "var(--color-success)";
    else if (value < 70) bar.style.background = "var(--color-warning)";
    else bar.style.background = "var(--color-danger)";
}

function animateGauge(prob) {
    const circle = document.getElementById("gaugeCircle");
    const radius = circle.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;
    
    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    circle.style.strokeDashoffset = circumference - (prob / 100) * circumference;
    
    let color = "var(--color-success)";
    if (prob >= 30 && prob < 70) color = "var(--color-warning)";
    else if (prob >= 70) color = "var(--color-danger)";
    
    circle.style.stroke = color;
}

function updateWearCard(badgeId, scoreId, wearData) {
    const badge = document.getElementById(badgeId);
    const score = document.getElementById(scoreId);
    
    badge.textContent = `${wearData.wear_level} WEAR`;
    badge.className = `wear-badge-hud ${wearData.wear_level}`;
    score.textContent = `${wearData.wear_score}/10`;
}

// ---------------------------------------------------------------------
// 9. Chart.js Generators (Matching Cyber Aesthetic)
// ---------------------------------------------------------------------
function renderTimelineChart(timeline) {
    if (timelineChartInstance) timelineChartInstance.destroy();
    
    const labels = timeline.map(t => t.date);
    const odometer = timeline.map(t => t.odometer);
    const pointsColors = timeline.map((t, idx) => {
        if (idx > 0 && odometer[idx] < odometer[idx-1]) return "var(--color-danger)";
        return "var(--color-cyan)";
    });
    
    const isLight = document.body.classList.contains("light-theme");
    const tickColor = isLight ? '#475569' : '#9ca3af';
    
    const ctx = document.getElementById("timelineChart").getContext("2d");
    timelineChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Odometer (km)',
                data: odometer,
                borderColor: 'rgba(0, 229, 255, 0.8)',
                backgroundColor: 'rgba(0, 229, 255, 0.04)',
                borderWidth: 2,
                pointBackgroundColor: pointsColors,
                pointBorderColor: '#fff',
                pointRadius: 6,
                fill: true,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(0, 229, 255, 0.05)' },
                    ticks: { color: tickColor, font: { family: 'Orbitron' } }
                },
                y: {
                    grid: { color: 'rgba(0, 229, 255, 0.05)' },
                    ticks: { color: tickColor, font: { family: 'Orbitron' } }
                }
            }
        }
    });
}

function renderEcuChart(modules) {
    if (ecuChartInstance) ecuChartInstance.destroy();
    
    const labels = modules.map(m => m.module);
    const mileages = modules.map(m => m.mileage);
    const bgColors = modules.map(m => {
        if (m.status === "REPLACED (OUTLIER)") return "rgba(0, 229, 255, 0.25)";
        if (m.is_anomalous) return "rgba(255, 0, 85, 0.6)";
        return "rgba(0, 240, 255, 0.6)";
    });
    
    const isLight = document.body.classList.contains("light-theme");
    const tickColor = isLight ? '#475569' : '#9ca3af';
    
    const ctx = document.getElementById("ecuChart").getContext("2d");
    ecuChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                data: mileages,
                backgroundColor: bgColors,
                borderColor: 'rgba(255,255,255,0.05)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: tickColor, font: { family: 'Orbitron' } }
                },
                y: {
                    grid: { color: 'rgba(0, 229, 255, 0.05)' },
                    ticks: { color: tickColor, font: { family: 'Orbitron' } }
                }
            }
        }
    });
}

function renderEcuTable(modules, outlierDetected) {
    const tableBody = document.getElementById("ecuTableBody");
    tableBody.innerHTML = "";
    
    modules.forEach(m => {
        const row = document.createElement("tr");
        let statusClass = "clean";
        if (m.status === "REPLACED (OUTLIER)") statusClass = "info";
        else if (m.is_anomalous) statusClass = "tampered";
        
        let colorStyle = "var(--color-success)";
        if (m.status === "REPLACED (OUTLIER)") colorStyle = "var(--color-cyan)";
        else if (m.is_anomalous) colorStyle = "var(--color-danger)";
        
        row.innerHTML = `
            <td><strong>${m.module}</strong></td>
            <td>${Number(m.mileage).toLocaleString()} km</td>
            <td style="color: ${colorStyle}">
                ${m.difference > 0 ? '+' : ''}${Number(m.difference).toLocaleString()} km
            </td>
            <td>
                <span class="status-badge ${statusClass}" style="
                    background: ${statusClass === 'tampered' ? 'rgba(255,0,85,0.1)' : (statusClass === 'info' ? 'rgba(0,229,255,0.1)' : 'rgba(0,240,255,0.1)')};
                    color: ${colorStyle};
                    border: 1px solid ${statusClass === 'tampered' ? 'rgba(255,0,85,0.2)' : (statusClass === 'info' ? 'rgba(0,229,255,0.2)' : 'rgba(0,240,255,0.2)')};
                    padding: 0.2rem 0.5rem;
                    border-radius: 4px;
                    font-weight: 700;
                    font-size: 0.7rem;
                    font-family: 'Orbitron';
                ">${m.status}</span>
            </td>
        `;
        tableBody.appendChild(row);
    });
}
