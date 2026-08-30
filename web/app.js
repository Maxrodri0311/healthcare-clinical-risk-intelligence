document.addEventListener("DOMContentLoaded", () => {
    initImportanceChart();
    initFairnessRadar();
    updateSimulation();
});

function switchTab(tabId) {
    document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
    document.querySelectorAll(".tab-btn").forEach(el => el.classList.remove("active"));
    
    document.getElementById(tabId).classList.remove("hidden");
    const btn = document.getElementById(`btn-${tabId}`);
    if (btn) btn.classList.add("active");
}

function initImportanceChart() {
    const ctx = document.getElementById("importanceChart").getContext("2d");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: [
                "Charlson Comorbidity", 
                "Cancer Stage IV", 
                "Concurrent Chemo", 
                "Total Dose (Gy)", 
                "Prior Hospitalizations", 
                "Patient Age", 
                "Dose per Fraction",
                "Medicare Payer"
            ],
            datasets: [{
                label: "SHAP Relative Gain Impact",
                data: [0.342, 0.284, 0.198, 0.176, 0.152, 0.114, 0.089, 0.045],
                backgroundColor: [
                    "rgba(56, 189, 248, 0.85)",
                    "rgba(14, 165, 233, 0.85)",
                    "rgba(99, 102, 241, 0.85)",
                    "rgba(129, 140, 248, 0.85)",
                    "rgba(52, 211, 153, 0.85)",
                    "rgba(251, 191, 36, 0.85)",
                    "rgba(244, 63, 94, 0.85)",
                    "rgba(168, 85, 247, 0.85)"
                ],
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: c => ` Gain Weight: ${(c.parsed.x * 100).toFixed(1)}%`
                    }
                }
            },
            scales: {
                x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(51, 65, 85, 0.25)" } },
                y: { ticks: { color: "#f8fafc", font: { size: 10 } }, grid: { display: false } }
            }
        }
    });
}

function initFairnessRadar() {
    const ctx = document.getElementById("fairnessRadar").getContext("2d");
    new Chart(ctx, {
        type: "radar",
        data: {
            labels: ["Gender Parity", "Geriatric (65+)", "Commercial PPO", "Medicaid Managed", "Medicare Adv."],
            datasets: [
                {
                    label: "RHI Radion Disparate Impact",
                    data: [0.98, 0.82, 0.89, 0.84, 0.91],
                    borderColor: "#38bdf8",
                    backgroundColor: "rgba(56, 189, 248, 0.2)",
                    borderWidth: 2
                },
                {
                    label: "HHS 80% Rule Threshold",
                    data: [0.80, 0.80, 0.80, 0.80, 0.80],
                    borderColor: "#ef4444",
                    borderDash: [4, 4],
                    backgroundColor: "transparent",
                    borderWidth: 1.5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "bottom", labels: { color: "#94a3b8", font: { size: 10 } } }
            },
            scales: {
                r: {
                    min: 0.5,
                    max: 1.0,
                    ticks: { display: false },
                    grid: { color: "rgba(51, 65, 85, 0.3)" },
                    pointLabels: { color: "#cbd5e1", font: { size: 10 } }
                }
            }
        }
    });
}

function updateSimulation() {
    const charlson = parseInt(document.getElementById("slider-charlson").value);
    const dose = parseFloat(document.getElementById("slider-dose").value);
    const age = parseInt(document.getElementById("slider-age").value);
    const prior = parseInt(document.getElementById("slider-prior").value);

    document.getElementById("val-charlson").innerText = charlson;
    document.getElementById("val-dose").innerText = dose.toFixed(1) + " Gy";
    document.getElementById("val-age").innerText = age + " Yrs";
    document.getElementById("val-prior").innerText = prior;

    // Logit estimate
    const logit = -3.2 + 0.025 * (age - 60) + 0.35 * charlson + 0.02 * (dose - 45) + 0.45 * prior;
    const prob = 1.0 / (1.0 + Math.exp(-logit));
    const pct = (prob * 100).toFixed(1);

    document.getElementById("sim-risk-score").innerText = `${pct}%`;

    const badge = document.getElementById("sim-badge");
    if (prob >= 0.45) {
        badge.innerText = "CRITICAL RISK TIER (ICU SENSITIVE)";
        badge.className = "px-3.5 py-1.5 rounded-xl bg-rose-500/20 text-rose-300 border border-rose-500/40 text-xs font-bold";
    } else if (prob >= 0.20) {
        badge.innerText = "MODERATE RISK TIER";
        badge.className = "px-3.5 py-1.5 rounded-xl bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs font-bold";
    } else {
        badge.innerText = "LOW RISK AMBULATORY";
        badge.className = "px-3.5 py-1.5 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs font-bold";
    }

    const expectedCost = Math.round(prob * 45000);
    const netSavings = Math.max(0, Math.round(prob * (45000 - 1800) - 120));

    document.getElementById("sim-icu-cost").innerText = `$${expectedCost.toLocaleString()}`;
    document.getElementById("sim-net-savings").innerText = `$${netSavings.toLocaleString()}`;
}
