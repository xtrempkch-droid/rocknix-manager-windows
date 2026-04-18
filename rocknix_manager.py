#!/usr/bin/env python3
# rocknix_manager_v7_6.py
# Versão com Suporte a Tema Automático Windows e Estabilidade de DLLs

import sys, os, shutil, socket, subprocess, hashlib, tempfile, zipfile, time, locale
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox,
    QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QRadioButton, QLineEdit,
    QCheckBox, QInputDialog, QLabel, QComboBox, QGroupBox, QTabWidget,
    QAbstractItemView, QDialog, QListWidget, QListWidgetItem, QButtonGroup
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QPalette, QColor

# Suporte a Tema e SSH
try:
    import darkdetect
except ImportError:
    darkdetect = None

try:
    import paramiko
except ImportError:
    paramiko = None

# ----------------------------------------------------------------------
# 1. SISTEMA DE TEMA AUTOMÁTICO (WINDOWS)
# ----------------------------------------------------------------------
def apply_windows_theme(app):
    """Detecta o tema do Windows e aplica cores modernas."""
    app.setStyle("Fusion") 
    
    if darkdetect and darkdetect.isDark():
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(18, 18, 18))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        app.setPalette(palette)
        
        app.setStyleSheet("""
            QPushButton { background-color: #3d3d3d; padding: 6px; border-radius: 4px; border: 1px solid #555; color: white; }
            QPushButton:hover { background-color: #4d4d4d; }
            QHeaderView::section { background-color: #252525; color: white; padding: 4px; border: 1px solid #444; }
            QTableWidget { gridline-color: #444; background-color: #1e1e1e; color: white; }
            QTabWidget::pane { border: 1px solid #444; }
            QLineEdit { background-color: #2b2b2b; color: white; border: 1px solid #555; padding: 3px; }
        """)
    else:
        app.setPalette(app.style().standardPalette())

# ----------------------------------------------------------------------
# 2. TRADUÇÕES
# ----------------------------------------------------------------------
TRANSLATIONS = {
    "pt_BR": {
        "app_name": "Rocknix Manager",
        "mode_title": "Modo de Operação",
        "net_mode": "Rede (Rocknix)",
        "local_mode": "Local (SD/Pasta)",
        "btn_sync": "📡 Detectar Rede",
        "btn_local_path": "📂 Selecionar Destino",
        "status_disconnected": "Desconectado",
        "status_connected": "Conectado: {ip} ({mode})",
        "tab_roms": "🎮 ROMs",
        "tab_bios": "🧬 BIOS",
        "tab_console": "📜 Console",
        "config_zip": "⚙️ Config Compressão",
        "btn_bulk": "🎯 Definir Sistema em Massa",
        "btn_scan": "📂 Adicionar Pasta (Scan)",
        "btn_send": "🚀 Enviar Selecionados",
        "audit_local": "1. Auditar BIOS Local",
        "btn_deploy_bios": "2. Enviar {n} BIOS Validadas",
        "btn_audit_net": "🔎 Auditar via SSH",
        "dest_label": "Destino:",
        "msg_error": "Erro",
        "msg_success": "Sucesso",
        "msg_finished": "Operação Concluída!",
        "msg_configure_dest": "Por favor, conecte à rede ou selecione um destino local primeiro."
    }
}

# ----------------------------------------------------------------------
# 3. CLASSE PRINCIPAL (INTERFACE)
# ----------------------------------------------------------------------
class RocknixManager(QMainWindow):
    def __init__(self):
        super().__init__()
        # Detectar Idioma
        lang = locale.getdefaultlocale()[0]
        self.t = TRANSLATIONS.get(lang, TRANSLATIONS["pt_BR"])
        
        self.setWindowTitle(f"{self.t['app_name']} v7.6")
        self.resize(900, 600)
        
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Cabeçalho - Modo de Operação
        mode_group = QGroupBox(self.t["mode_title"])
        mode_layout = QHBoxLayout()
        self.radio_net = QRadioButton(self.t["net_mode"])
        self.radio_local = QRadioButton(self.t["local_mode"])
        self.radio_local.setChecked(True)
        mode_layout.addWidget(self.radio_net)
        mode_layout.addWidget(self.radio_local)
        
        self.btn_sync = QPushButton(self.t["btn_sync"])
        self.btn_local = QPushButton(self.t["btn_local_path"])
        mode_layout.addWidget(self.btn_sync)
        mode_layout.addWidget(self.btn_local)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Tabs
        self.tabs = QTabWidget()
        self.tab_roms = QWidget()
        self.tab_bios = QWidget()
        self.tab_console = QTextEdit()
        self.tab_console.setReadOnly(True)
        
        self.tabs.addTab(self.tab_roms, self.t["tab_roms"])
        self.tabs.addTab(self.tab_bios, self.t["tab_bios"])
        self.tabs.addTab(self.tab_console, self.t["tab_console"])
        layout.addWidget(self.tabs)

        # Tabela de ROMs (Exemplo rápido)
        rom_layout = QVBoxLayout(self.tab_roms)
        self.table_roms = QTableWidget(0, 4)
        self.table_roms.setHorizontalHeaderLabels(["Arquivo", "Sistema", "Tamanho", "Status"])
        self.table_roms.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        rom_layout.addWidget(self.table_roms)
        
        btn_send = QPushButton(self.t["btn_send"])
        rom_layout.addWidget(btn_send)

        # Rodapé
        self.status_label = QLabel(self.t["status_disconnected"])
        layout.addWidget(self.status_label)
        self.pbar = QProgressBar()
        layout.addWidget(self.pbar)

# ----------------------------------------------------------------------
# 4. EXECUÇÃO FINAL
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Fix para ícone e DPI no Windows
    if os.name == 'nt':
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("rocknix.manager.v7")
        except:
            pass

    app = QApplication(sys.argv)
    
    # Aplica o tema visual do Windows
    apply_windows_theme(app)
    
    window = RocknixManager()
    window.show()
    sys.exit(app.exec())
