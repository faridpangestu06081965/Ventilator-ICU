# -*- coding: utf-8 -*-
import sys
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QSlider, QGroupBox, 
                             QRadioButton, QFrame, QGridLayout)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
import pyqtgraph as pg

pg.setConfigOption('background', '#0b0f19')
pg.setConfigOption('foreground', '#d0e0f0')

class VentilatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ICU MECHANICAL VENTILATOR & LUNG MECHANICS WORKSTATION")
        self.resize(1300, 850)

        # Ventilation Setpoints
        self.mode = "VCV"  # VCV (Volume Control) or PCV (Pressure Control)
        self.set_vt = 500  # mL (Tidal Volume)
        self.set_rr = 15   # Breaths per minute
        self.set_peep = 5  # cmH2O
        
        # Patient Lung Mechanics (Physiology)
        self.compliance = 50.0 # mL/cmH2O
        self.resistance = 5.0  # cmH2O/(L/s)

        # Simulation States
        self.time_sec = 0.0
        self.dt = 0.02  # 50 Hz update

        # Buffers for Real-Time Waveforms
        self.buffer_len = 250
        self.time_buffer = np.linspace(-5, 0, self.buffer_len)
        self.press_buffer = np.full(self.buffer_len, self.set_peep)
        self.flow_buffer = np.zeros(self.buffer_len)
        self.vol_buffer = np.zeros(self.buffer_len)

        # Single Breath Cycle Buffers for P-V Loop
        self.pv_press = []
        self.pv_vol = []

        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(20)

    def init_ui(self):
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: #080c14; color: #e0e8f0; font-family: 'Segoe UI';")
        self.setCentralWidget(main_widget)
        
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)

        header = QFrame()
        header.setStyleSheet("background-color: #121926; border: 1px solid #1a2638; border-radius: 8px;")
        header_layout = QHBoxLayout(header)
        
        title_lbl = QLabel("ICU VENTILATOR WORKSTATION | MODEL VENTI-5000 PRO")
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #00d2ff;")
        
        self.status_badge = QLabel("VENTILATING: NORMAL")
        self.status_badge.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.status_badge.setStyleSheet("color: #00ff88; background-color: #0a2e1e; padding: 6px 14px; border-radius: 6px;")
        
        self.alarm_badge = QLabel("PATIENT INTERLOCK: OK")
        self.alarm_badge.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.alarm_badge.setStyleSheet("color: #00e5ff; background-color: #0d2838; padding: 6px 12px; border-radius: 6px;")

        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self.alarm_badge)
        header_layout.addWidget(self.status_badge)
        main_layout.addWidget(header)

        content_layout = QHBoxLayout()
        left_panel = QVBoxLayout()
        
        mode_group = QGroupBox("VENTILATION MODE")
        mode_group.setStyleSheet("QGroupBox { font-weight: bold; color: #00d2ff; border: 1px solid #1a2d42; border-radius: 6px; margin-top: 10px; padding-top: 10px; }")
        mode_layout = QVBoxLayout(mode_group)
        
        self.radio_vcv = QRadioButton("Volume-Controlled (VCV)")
        self.radio_pcv = QRadioButton("Pressure-Controlled (PCV)")
        self.radio_vcv.setChecked(True)
        
        self.radio_vcv.toggled.connect(lambda: self.set_vent_mode("VCV"))
        self.radio_pcv.toggled.connect(lambda: self.set_vent_mode("PCV"))
        
        mode_layout.addWidget(self.radio_vcv)
        mode_layout.addWidget(self.radio_pcv)
        left_panel.addWidget(mode_group)

        set_group = QGroupBox("VENTILATOR SETPOINTS")
        set_group.setStyleSheet("QGroupBox { font-weight: bold; color: #00d2ff; border: 1px solid #1a2d42; border-radius: 6px; margin-top: 10px; padding-top: 10px; }")
        set_layout = QGridLayout(set_group)

        set_layout.addWidget(QLabel("Tidal Volume (Vt):"), 0, 0)
        self.lbl_vt = QLabel("500 mL")
        self.lbl_vt.setStyleSheet("color: #00ff88; font-weight: bold;")
        set_layout.addWidget(self.lbl_vt, 0, 1)

        self.slider_vt = QSlider(Qt.Orientation.Horizontal)
        self.slider_vt.setRange(200, 800)
        self.slider_vt.setValue(500)
        self.slider_vt.valueChanged.connect(self.update_settings)
        set_layout.addWidget(self.slider_vt, 1, 0, 1, 2)

        set_layout.addWidget(QLabel("Respiratory Rate (RR):"), 2, 0)
        self.lbl_rr = QLabel("15 BPM")
        self.lbl_rr.setStyleSheet("color: #00ff88; font-weight: bold;")
        set_layout.addWidget(self.lbl_rr, 2, 1)

        self.slider_rr = QSlider(Qt.Orientation.Horizontal)
        self.slider_rr.setRange(8, 35)
        self.slider_rr.setValue(15)
        self.slider_rr.valueChanged.connect(self.update_settings)
        set_layout.addWidget(self.slider_rr, 3, 0, 1, 2)

        set_layout.addWidget(QLabel("PEEP:"), 4, 0)
        self.lbl_peep = QLabel("5 cmH2O")
        self.lbl_peep.setStyleSheet("color: #ff2a6d; font-weight: bold;")
        set_layout.addWidget(self.lbl_peep, 4, 1)

        self.slider_peep = QSlider(Qt.Orientation.Horizontal)
        self.slider_peep.setRange(0, 20)
        self.slider_peep.setValue(5)
        self.slider_peep.valueChanged.connect(self.update_settings)
        set_layout.addWidget(self.slider_peep, 5, 0, 1, 2)

        left_panel.addWidget(set_group)

        lung_group = QGroupBox("PATIENT LUNG MECHANICS SIMULATOR")
        lung_group.setStyleSheet("QGroupBox { font-weight: bold; color: #ffcc00; border: 1px solid #1a2d42; border-radius: 6px; margin-top: 10px; padding-top: 10px; }")
        lung_layout = QGridLayout(lung_group)

        lung_layout.addWidget(QLabel("Compliance (Cdyn):"), 0, 0)
        self.lbl_comp = QLabel("50 mL/cmH2O")
        self.lbl_comp.setStyleSheet("color: #ffcc00; font-weight: bold;")
        lung_layout.addWidget(self.lbl_comp, 0, 1)

        self.slider_comp = QSlider(Qt.Orientation.Horizontal)
        self.slider_comp.setRange(10, 80)
        self.slider_comp.setValue(50)
        self.slider_comp.valueChanged.connect(self.update_lung_physics)
        lung_layout.addWidget(self.slider_comp, 1, 0, 1, 2)

        lung_layout.addWidget(QLabel("Airway Resistance (Raw):"), 2, 0)
        self.lbl_res = QLabel("5 cmH2O/(L/s)")
        self.lbl_res.setStyleSheet("color: #ffcc00; font-weight: bold;")
        lung_layout.addWidget(self.lbl_res, 2, 1)

        self.slider_res = QSlider(Qt.Orientation.Horizontal)
        self.slider_res.setRange(2, 35)
        self.slider_res.setValue(5)
        self.slider_res.valueChanged.connect(self.update_lung_physics)
        lung_layout.addWidget(self.slider_res, 3, 0, 1, 2)

        left_panel.addWidget(lung_group)
        left_panel.addStretch()

        content_layout.addLayout(left_panel, stretch=1)

        right_panel = QVBoxLayout()
        graphs_layout = QHBoxLayout()
        wave_layout = QVBoxLayout()
        
        self.plot_press = pg.PlotWidget(title="<b>AIRWAY PRESSURE Paw (cmH2O)</b>")
        self.plot_press.setYRange(0, 50)
        self.plot_press.showGrid(x=True, y=True, alpha=0.3)
        self.curve_press = self.plot_press.plot(pen=pg.mkPen('#00ff88', width=2))
        wave_layout.addWidget(self.plot_press)

        self.plot_flow = pg.PlotWidget(title="<b>AIRFLOW RATE (L/min)</b>")
        self.plot_flow.setYRange(-60, 60)
        self.plot_flow.showGrid(x=True, y=True, alpha=0.3)
        self.curve_flow = self.plot_flow.plot(pen=pg.mkPen('#00d2ff', width=2))
        wave_layout.addWidget(self.plot_flow)

        graphs_layout.addLayout(wave_layout, stretch=2)

        self.plot_pv = pg.PlotWidget(title="<b>DYNAMIC PRESSURE-VOLUME (P-V) LOOP</b>")
        self.plot_pv.setXRange(0, 50)
        self.plot_pv.setYRange(0, 800)
        self.plot_pv.setLabel('left', 'Volume (mL)')
        self.plot_pv.setLabel('bottom', 'Pressure (cmH2O)')
        self.plot_pv.showGrid(x=True, y=True, alpha=0.3)
        self.curve_pv = self.plot_pv.plot(pen=pg.mkPen('#ffcc00', width=2.5))
        graphs_layout.addWidget(self.plot_pv, stretch=1)

        right_panel.addLayout(graphs_layout)
        content_layout.addLayout(right_panel, stretch=3)
        main_layout.addLayout(content_layout)

        footer = QFrame()
        footer.setStyleSheet("background-color: #121926; border: 1px solid #1a2638; border-radius: 6px; padding: 6px;")
        footer_layout = QHBoxLayout(footer)

        self.lbl_tele_peak = QLabel("P_peak: 15.0 cmH2O")
        self.lbl_tele_plat = QLabel("P_plat: 12.0 cmH2O")
        self.lbl_tele_vt = QLabel("Delivered Vt: 500 mL")
        self.lbl_tele_ve = QLabel("Minute Vol (Ve): 7.5 L/min")

        for lbl in [self.lbl_tele_peak, self.lbl_tele_plat, self.lbl_tele_vt, self.lbl_tele_ve]:
            lbl.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
            lbl.setStyleSheet("color: #90a4ae;")
            footer_layout.addWidget(lbl)

        main_layout.addWidget(footer)

    def set_vent_mode(self, mode):
        self.mode = mode

    def update_settings(self):
        self.set_vt = self.slider_vt.value()
        self.set_rr = self.slider_rr.value()
        self.set_peep = self.slider_peep.value()
        
        self.lbl_vt.setText(f"{self.set_vt} mL")
        self.lbl_rr.setText(f"{self.set_rr} BPM")
        self.lbl_peep.setText(f"{self.set_peep} cmH2O")

    def update_lung_physics(self):
        self.compliance = float(self.slider_comp.value())
        self.resistance = float(self.slider_res.value())
        self.lbl_comp.setText(f"{int(self.compliance)} mL/cmH2O")
        self.lbl_res.setText(f"{int(self.resistance)} cmH2O/(L/s)")

    def update_simulation(self):
        self.time_sec += self.dt
        
        t_total = 60.0 / self.set_rr
        t_insp = t_total / 3.0
        cycle_pos = self.time_sec % t_total

        tau = (self.resistance * (self.compliance / 1000.0))
        tau = max(0.05, tau)

        if cycle_pos < self.dt:
            self.pv_press = []
            self.pv_vol = []

        if self.mode == "VCV":
            if cycle_pos <= t_insp:
                flow_lps = (self.set_vt / 1000.0) / t_insp
                vol_ml = (flow_lps * cycle_pos) * 1000.0
                press = self.set_peep + (vol_ml / self.compliance) + (flow_lps * self.resistance)
                flow_lpmin = flow_lps * 60.0
            else:
                t_e = cycle_pos - t_insp
                vol_ml = self.set_vt * np.exp(-t_e / tau)
                flow_lps = -(vol_ml / 1000.0) / tau
                press = self.set_peep + (vol_ml / self.compliance) + (flow_lps * self.resistance)
                flow_lpmin = flow_lps * 60.0

        else:
            p_target = self.set_peep + 25.0
            if cycle_pos <= t_insp:
                press = self.set_peep + (p_target - self.set_peep) * (1.0 - np.exp(-cycle_pos / tau))
                vol_ml = (self.compliance * (press - self.set_peep))
                flow_lps = ((p_target - press) / max(0.1, self.resistance))
                flow_lpmin = flow_lps * 60.0
            else:
                t_e = cycle_pos - t_insp
                vol_ml = (self.compliance * (p_target - self.set_peep)) * np.exp(-t_e / tau)
                flow_lps = -((p_target - self.set_peep) / max(0.1, self.resistance)) * np.exp(-t_e / tau)
                press = self.set_peep + (vol_ml / self.compliance) + (flow_lps * self.resistance)
                flow_lpmin = flow_lps * 60.0

        # Latched Safety Interlock Logic
        est_flow_lps = ((self.set_vt / 1000.0) / t_insp) if self.mode == "VCV" else 1.0
        est_p_peak = self.set_peep + (self.set_vt / self.compliance) + (est_flow_lps * self.resistance)

        if est_p_peak > 30.0 or press > 30.0:
            self.alarm_badge.setText("ALARM: HIGH PEAK PRESSURE (>30 cmH2O)")
            self.alarm_badge.setStyleSheet("color: #ffffff; background-color: #ff0055; padding: 6px 12px; border-radius: 6px;")
            self.status_badge.setText("VENTILATION INTERLOCK TRIGGERED")
            self.status_badge.setStyleSheet("color: #ff0055; background-color: #380d18; padding: 6px 14px; border-radius: 6px;")
            if press > 30.0:
                press = 30.0
        else:
            self.alarm_badge.setText("PATIENT INTERLOCK: OK")
            self.alarm_badge.setStyleSheet("color: #00e5ff; background-color: #0d2838; padding: 6px 12px; border-radius: 6px;")
            self.status_badge.setText("VENTILATING: NORMAL")
            self.status_badge.setStyleSheet("color: #00ff88; background-color: #0a2e1e; padding: 6px 14px; border-radius: 6px;")

        self.press_buffer = np.roll(self.press_buffer, -1)
        self.flow_buffer = np.roll(self.flow_buffer, -1)
        self.press_buffer[-1] = press
        self.flow_buffer[-1] = flow_lpmin

        self.pv_press.append(press)
        self.pv_vol.append(vol_ml)

        self.curve_press.setData(self.press_buffer)
        self.curve_flow.setData(self.flow_buffer)
        self.curve_pv.setData(self.pv_press, self.pv_vol)

        ve = (vol_ml * self.set_rr) / 1000.0
        self.lbl_tele_peak.setText(f"P_peak: {max(self.press_buffer):.1f} cmH2O")
        self.lbl_tele_plat.setText(f"P_plat: {(self.set_peep + (vol_ml/self.compliance)):.1f} cmH2O")
        self.lbl_tele_vt.setText(f"Delivered Vt: {int(vol_ml)} mL")
        self.lbl_tele_ve.setText(f"Minute Vol (Ve): {ve:.1f} L/min")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VentilatorApp()
    window.show()
    sys.exit(app.exec())
