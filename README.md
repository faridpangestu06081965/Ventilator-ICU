# ICU Mechanical Ventilator & Lung Mechanics Simulator

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)
![PyQtGraph](https://img.shields.io/badge/Oscilloscope-PyQtGraph-cyan.svg)
![Domain](https://img.shields.io/badge/Domain-Biomedical--Pulmonology-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

An industrial-grade **ICU Mechanical Ventilator Workstation** simulating closed-loop respiratory control, human lung mechanics dynamics, real-time pressure/flow oscilloscopes, and dynamic **Pressure-Volume (P-V) Loops**.

---

## 📌 Key Features & Engineering Highlights

- 🫁 **Respiratory Mechanics Simulation**:
  - Implements the **Equation of Motion for the Respiratory System**: $P(t) = PEEP + \frac{V(t)}{C} + R \cdot F(t)$.
  - Adjustable dynamic Lung Compliance ($C_{\text{dyn}}$: 10–80 mL/cmH2O) to model normal vs. ARDS lungs.
  - Adjustable Airway Resistance ($R_{\text{aw}}$: 2–35 cmH2O/(L/s)) to model asthma/COPD pathologies.
- ⚡ **Dual Ventilation Modes**:
  - **Volume-Controlled Ventilation (VCV)**: Delivers fixed tidal volume via constant flow profile.
  - **Pressure-Controlled Ventilation (PCV)**: Delivers target peak inspiratory pressure with exponential flow decay.
- 📊 **60 FPS Real-Time Diagnostic Dashboard**:
  - Airway Pressure ($P_{\text{aw}}$) and Flow Rate waveforms using PyQtGraph.
  - Live **Pressure-Volume (P-V) Loop** graphics for direct lung mechanics diagnostic visualization.
- 🛡️ **Barotrauma Safety Interlock**:
  - Continuous monitoring of peak airway pressure with automatic latched safety interlock when exceeding $30\ \text{cmH2O}$.

---

## 🛠️ Tech Stack

- **Language**: Python 3.8+
- **GUI Framework**: PyQt6
- **Plotting & Oscilloscopes**: PyQtGraph
- **Numeric Processing**: NumPy

---

## 🚀 Quick Start

```bash
pip install PyQt6 pyqtgraph numpy
python ventilator_sim.py
