#!/usr/bin/env python3 
# rocknix_manager_v7_6.py
# V7.6 - HOTFIX & STABILITY
# - Correção de KeyError 'dest_label'.
# - Correção definitiva do status de rede (Online/Conectado).
# - Auditoria BIOS Remota (SSH) e Local ativadas.
# - Configuração de Compressão e Ação em Massa restauradas.


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

# Fallback para SSH
try:
    import paramiko
except ImportError:
    paramiko = None

# ----------------------------------------------------------------------
# 1. TRADUÇÕES E DADOS (CORRIGIDO)
# ----------------------------------------------------------------------
TRANSLATIONS = {
    "pt_BR": {
        "app_name": "Rocknix Manager V7.6 - Estável",
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
        "msg_configure_dest": "Por favor, conecte à rede ou selecione um destino local primeiro.",
        "searching": "📡 Varrendo rede...",
        "ip_found": "✅ Encontrado: {ip}",
        "ip_not_found": "❌ Nenhum Rocknix encontrado.",
        "audit_scanning": "🔎 Verificando arquivos...",
        "copying": "Copiando: {name}",
        "sending_sftp": "Enviando SFTP: {name}",
        "zip_title": "Configurar Compressão",
        "zip_desc": "Selecione sistemas para compactar (.zip):",
        "bulk_title": "Definir em Massa",
        "bulk_msg": "Escolha o sistema para os itens selecionados:",
        "save": "Salvar"
    },
    "en_US": {
        "app_name": "Rocknix Manager V7.6 - Stable",
        "mode_title": "Operating Mode",
        "net_mode": "Network (Rocknix)",
        "local_mode": "Local (SD/Folder)",
        "btn_sync": "📡 Detect Network",
        "btn_local_path": "📂 Select Destination",
        "status_disconnected": "Disconnected",
        "status_connected": "Connected: {ip} ({mode})",
        "tab_roms": "🎮 ROMs",
        "tab_bios": "🧬 BIOS",
        "tab_console": "📜 Console",
        "config_zip": "⚙️ Zip Config",
        "btn_bulk": "🎯 Bulk Set System",
        "btn_scan": "📂 Add Folder (Scan)",
        "btn_send": "🚀 Send Selected",
        "audit_local": "1. Audit Local BIOS",
        "btn_deploy_bios": "2. Send {n} Valid BIOS",
        "btn_audit_net": "🔎 Audit via SSH",
        "dest_label": "Dest:",
        "msg_error": "Error",
        "msg_success": "Success",
        "msg_finished": "Operation Finished!",
        "msg_configure_dest": "Please connect to network or select local destination first.",
        "searching": "📡 Scanning network...",
        "ip_found": "✅ Found: {ip}",
        "ip_not_found": "❌ No Rocknix device found.",
        "audit_scanning": "🔎 Verifying files...",
        "copying": "Copying: {name}",
        "sending_sftp": "Sending SFTP: {name}",
        "zip_title": "Compression Config",
        "zip_desc": "Select systems to zip:",
        "bulk_title": "Bulk Set",
        "bulk_msg": "Choose system for selected items:",
        "save": "Save"
    },
    "es_ES": {
        "app_name": "Rocknix Manager V7.6 - Estable",
        "mode_title": "Modo de Operación",
        "net_mode": "Red (Rocknix)",
        "local_mode": "Local (SD/Carpeta)",
        "btn_sync": "📡 Detectar Red",
        "btn_local_path": "📂 Seleccionar Destino",
        "status_disconnected": "Desconectado",
        "status_connected": "Conectado: {ip} ({mode})",
        "tab_roms": "🎮 ROMs",
        "tab_bios": "🧬 BIOS",
        "tab_console": "📜 Consola",
        "config_zip": "⚙️ Config. Compresión",
        "btn_bulk": "🎯 Definir Sistema en Masa",
        "btn_scan": "📂 Añadir Carpeta (Scan)",
        "btn_send": "🚀 Enviar Seleccionados",
        "audit_local": "1. Auditar BIOS Local",
        "btn_deploy_bios": "2. Enviar {n} BIOS Validadas",
        "btn_audit_net": "🔎 Auditar vía SSH",
        "dest_label": "Destino:",
        "msg_error": "Error",
        "msg_success": "Éxito",
        "msg_finished": "¡Operación Finalizada!",
        "msg_configure_dest": "Por favor, conéctese a la red o seleccione un destino local primero.",
        "searching": "📡 Escaneando red...",
        "ip_found": "✅ Encontrado: {ip}",
        "ip_not_found": "❌ No se encontró ningún Rocknix.",
        "audit_scanning": "🔎 Verificando archivos...",
        "copying": "Copiando: {name}",
        "sending_sftp": "Enviando SFTP: {name}",
        "zip_title": "Configurar Compresión",
        "zip_desc": "Seleccione sistemas para comprimir (.zip):",
        "bulk_title": "Definir en Masa",
        "bulk_msg": "Elija el sistema para los ítems seleccionados:",
        "save": "Guardar"
    },
    "fr_FR": {
        "app_name": "Rocknix Manager V7.6 - Stable",
        "mode_title": "Mode de Fonctionnement",
        "net_mode": "Réseau (Rocknix)",
        "local_mode": "Local (SD/Dossier)",
        "btn_sync": "📡 Détecter le Réseau",
        "btn_local_path": "📂 Choisir Destination",
        "status_disconnected": "Déconnecté",
        "status_connected": "Connecté: {ip} ({mode})",
        "tab_roms": "🎮 ROMs",
        "tab_bios": "🧬 BIOS",
        "tab_console": "📜 Console",
        "config_zip": "⚙️ Config Compression",
        "btn_bulk": "🎯 Définir Système en Masse",
        "btn_scan": "📂 Ajouter Dossier (Scan)",
        "btn_send": "🚀 Envoyer Sélectionnés",
        "audit_local": "1. Auditer BIOS Local",
        "btn_deploy_bios": "2. Envoyer {n} BIOS Validées",
        "btn_audit_net": "🔎 Auditer via SSH",
        "dest_label": "Dest:",
        "msg_error": "Erreur",
        "msg_success": "Succès",
        "msg_finished": "Opération Terminée !",
        "msg_configure_dest": "Veuillez vous connecter au réseau ou choisir une destination locale.",
        "searching": "📡 Recherche sur le réseau...",
        "ip_found": "✅ Trouvé: {ip}",
        "ip_not_found": "❌ Aucun appareil Rocknix trouvé.",
        "audit_scanning": "🔎 Vérification des fichiers...",
        "copying": "Copie de: {name}",
        "sending_sftp": "Envoi SFTP: {name}",
        "zip_title": "Config Compression",
        "zip_desc": "Choisir les systèmes à compresser (.zip):",
        "bulk_title": "Définition en Masse",
        "bulk_msg": "Choisir le système pour les éléments sélectionnés:",
        "save": "Enregistrer"
    },
    "de_DE": {
        "app_name": "Rocknix Manager V7.6 - Stabil",
        "mode_title": "Betriebsmodus",
        "net_mode": "Netzwerk (Rocknix)",
        "local_mode": "Lokal (SD/Ordner)",
        "btn_sync": "📡 Netzwerk suchen",
        "btn_local_path": "📂 Ziel auswählen",
        "status_disconnected": "Nicht verbunden",
        "status_connected": "Verbunden: {ip} ({mode})",
        "tab_roms": "🎮 ROMs",
        "tab_bios": "🧬 BIOS",
        "tab_console": "📜 Konsole",
        "config_zip": "⚙️ Kompression-Einst.",
        "btn_bulk": "🎯 Massen-Systemwahl",
        "btn_scan": "📂 Ordner hinzufügen (Scan)",
        "btn_send": "🚀 Markierte senden",
        "audit_local": "1. Lokale BIOS prüfen",
        "btn_deploy_bios": "2. {n} geprüfte BIOS senden",
        "btn_audit_net": "🔎 Prüfung via SSH",
        "dest_label": "Ziel:",
        "msg_error": "Fehler",
        "msg_success": "Erfolg",
        "msg_finished": "Vorgang abgeschlossen!",
        "msg_configure_dest": "Bitte zuerst mit dem Netzwerk verbinden oder lokales Ziel wählen.",
        "searching": "📡 Suche im Netzwerk...",
        "ip_found": "✅ Gefunden: {ip}",
        "ip_not_found": "❌ Kein Rocknix-Gerät gefunden.",
        "audit_scanning": "🔎 Dateien werden geprüft...",
        "copying": "Kopieren: {name}",
        "sending_sftp": "SFTP-Versand: {name}",
        "zip_title": "Kompression konfig.",
        "zip_desc": "Systeme zum Zippen wählen (.zip):",
        "bulk_title": "Massenwahl",
        "bulk_msg": "System für markierte Elemente wählen:",
        "save": "Speichern"
    }
}

MAPA_ROCKNIX_FOLDER = {
    'nes': 'nes', 'snes': 'snes', 'n64': 'n64', 'gamecube': 'gamecube', 'wii': 'wii',
    'wiiu': 'wiiu', 'gb': 'gb', 'gbc': 'gbc', 'gba': 'gba', 'nds': 'nds',
    '3ds': '3ds', 'pokemonmini': 'pokemonmini', 'virtualboy': 'virtualboy',
    'mastersystem': 'mastersystem', 'megadrive': 'megadrive', 'sega32x': 'sega32x',
    'segacd': 'segacd', 'saturn': 'saturn', 'dreamcast': 'dreamcast',
    'gamegear': 'gamegear', 'sg1000': 'sg1000', 'psx': 'psx', 'ps2': 'ps2',
    'psp': 'psp', 'psvita': 'psvita', 'atari2600': 'atari2600',
    'atari5200': 'atari5200', 'atari7800': 'atari7800', 'atarijaguar': 'atarijaguar',
    'atarilynx': 'atarilynx', 'arcade': 'arcade', 'neogeo': 'neogeo',
    'cps1': 'cps1', 'cps2': 'cps2', 'cps3': 'cps3', 'mame': 'mame',
    'fbneo': 'fbneo', 'atomiswave': 'atomiswave', 'naomi': 'naomi',
    'amiga': 'amiga', 'c64': 'c64', 'msx': 'msx', 'zxspectrum': 'zxspectrum',
    'amstradcpc': 'amstradcpc', 'dos': 'dos', 'x68000': 'x68000', '3do': '3do',
    'pce': 'pcengine', 'pcecd': 'pcenginecd', 'colecovision': 'colecovision',
    'intellivision': 'intellivision', 'vectrex': 'vectrex', 'wonderswan': 'wonderswan',
    'wonderswancolor': 'wonderswancolor', 'neogeopocket': 'neogeopocket',
    'neogeopocketcolor': 'neogeopocketcolor', 'pico8': 'pico8', 'tic80': 'tic80', 'music': 'music'
}

# Lista completa para o Scanner Recursivo
ALL_EXTENSIONS = [
    '.nes', '.fds', '.sfc', '.smc', '.fig', '.n64', '.z64', '.v64', 
    '.gb', '.gbc', '.gba', '.nds', '.3ds', '.cia', '.gc', '.gcm', '.rvz', 
    '.wii', '.wbfs', '.vb', '.min', '.sms', '.gg', '.md', '.gen', '.smd', 
    '.32x', '.cdi', '.gdi', '.iso', '.chd', '.pbp', '.cso', '.pce', 
    '.cue', '.neogeo', '.zip', '.7z', '.wsc', '.ws', '.ngp', '.ngpc', 
    '.lnx', '.j64', '.jag', '.a26', '.a52', '.a78', '.3do', '.adf', 
    '.d64', '.dsk', '.mx1', '.mx2', '.ipf', '.vpk', '.mp3', '.flac', '.ogg'
]

BIOS_DATABASE = {

    # --- SONY ---
    'scph5500.bin': {'md5': '8dd7d5296a650fac7319bce665a6a53c', 'sys': 'PS1 (JP)', 'desc': 'Obrigatória para jogos JP'},
    'scph5501.bin': {'md5': '490f666e1afb15b7362b406ed1cea246', 'sys': 'PS1 (US)', 'desc': 'Obrigatória para jogos US'},
    'scph5502.bin': {'md5': '32736f17079d0b2b7024407c39ad3050', 'sys': 'PS1 (EU)', 'desc': 'Obrigatória para jogos EU'},
    'psxonpsp660.bin': {'md5': 'c53ca5908936d412331790f4426c6c33', 'sys': 'PS1 (PSP)', 'desc': 'Melhor performance (DuckStation)'},
    'scph39001.bin': {'md5': 'd5ce2c7d119f563ce04bc04dbc3a323e', 'sys': 'PS2 (US)', 'desc': 'Compatível PCSX2/Play!'},
    
    # --- SEGA ---
    'bios_CD_U.bin': {'md5': '2efd743390ffad365a45330c6a463c61', 'sys': 'Sega CD (US)', 'desc': 'Modelo 1 v1.10'},
    'bios_CD_E.bin': {'md5': 'e66fa1dc5820d254611fdcdba0662372', 'sys': 'Sega CD (EU)', 'desc': 'Modelo 1 v1.10'},
    'bios_CD_J.bin': {'md5': '278a93da838174dadabe39d897c51591', 'sys': 'Sega CD (JP)', 'desc': 'Modelo 1 v1.00'},
    'saturn_bios.bin': {'md5': 'af58e0fd19355465bcde8a00508933b9', 'sys': 'Saturn (JP)', 'desc': 'Bios Padrão Saturn'},
    'mpr-17933.bin': {'md5': '3240872c70984b6cbfda1586cab68dbe', 'sys': 'Saturn (US/EU)', 'desc': 'Alternativa comum'},
    'dc_boot.bin': {'md5': 'e10c53c2f8b90bab96ead2d368858623', 'sys': 'Dreamcast', 'desc': 'Bootloader'},
    'dc_flash.bin': {'md5': '0a93f7940c455902bea6e392dfde92a4', 'sys': 'Dreamcast', 'desc': 'Flash (Region Free)'},
    'naomi.zip': {'md5': 'VARIES', 'sys': 'Naomi Arcade', 'desc': 'Arquivo ZIP do MAME/FBNeo'},
    'awbios.zip': {'md5': 'VARIES', 'sys': 'Atomiswave', 'desc': 'Bios Atomiswave'},

    # --- NINTENDO ---
    'gba_bios.bin': {'md5': 'a860e8c0b6ec573d1e1e61f1bc566d7f', 'sys': 'GBA', 'desc': 'Game Boy Advance Boot'},
    'bios7.bin': {'md5': 'df692a80a5b1bc3129f3c163e596ba93', 'sys': 'NDS', 'desc': 'ARM7 BIOS'},
    'bios9.bin': {'md5': 'a392174eb3e572fed6c453309e67250a', 'sys': 'NDS', 'desc': 'ARM9 BIOS'},
    'firmware.bin': {'md5': 'e45033d9c0fa367bf1609fe794715278', 'sys': 'NDS', 'desc': 'Firmware (Opcional)'},
    'disksys.rom': {'md5': 'ca30b6d9c025f6e804f58f7004f98d78', 'sys': 'Famicom Disk', 'desc': 'FDS BIOS'},
    
    # --- ARCADE / SNK ---
    'neogeo.zip': {'md5': 'VARIES', 'sys': 'Neo Geo', 'desc': 'Essencial! Use set FBNeo/MAME recente'},
    'panafz10.bin': {'md5': '51f2f43ae2f3508a14d9f54597e2d365', 'sys': '3DO', 'desc': 'Panasonic FZ-10'},
    'goldstar.bin': {'md5': '92bd8942200701b223067eb0155a3062', 'sys': '3DO', 'desc': 'Goldstar Model'},

    # --- COMPUTADORES ---
    'kick34005.A500': {'md5': '854084365796a5b51f0f443836173d32', 'sys': 'Amiga 500', 'desc': 'Kickstart 1.3'},
    'kick40068.A1200': {'md5': '646773759326fbac3a2311fdc8cfef39', 'sys': 'Amiga 1200', 'desc': 'Kickstart 3.1'},
    'syscard3.pce': {'md5': '38179df8f4d9d9a936d102a3a24b3d74', 'sys': 'PC Engine CD', 'desc': 'System Card 3.0'},
    'msx2.rom': {'md5': 'ec1657490d292425510b64d8a1c6a084', 'sys': 'MSX2', 'desc': 'Japonesa'},
    'keropi.rom': {'md5': '2f78326a575c755c06495df0240d43a6', 'sys': 'X68000', 'desc': 'IPL ROM'}

}

import locale
import os

def get_sys_lang():
    try:
        # Tenta pegar a variável de ambiente primeiro (comum no Linux)
        env_lang = os.environ.get('LANG', '').split('.')[0] # Pega 'pt_BR' de 'pt_BR.UTF-8'
        
        if env_lang in TRANSLATIONS:
            return env_lang

        # Fallback para o método padrão do locale
        lang = locale.getdefaultlocale()[0]
        
        if lang:
            # Normaliza para os primeiros 5 caracteres (ex: pt_BR)
            lang = lang[:5]
            if lang in TRANSLATIONS:
                return lang
            if lang.startswith("pt"): return "pt_BR"
            if lang.startswith("es"): return "es_ES"
            if lang.startswith("fr"): return "fr_FR"
            if lang.startswith("de"): return "de_DE"
            
    except:
        pass
    
    return "en_US"

# ----------------------------------------------------------------------
# 2. DIÁLOGOS AUXILIARES
# ----------------------------------------------------------------------
class ZipConfigDialog(QDialog):
    def __init__(self, current_list, texts):
        super().__init__()
        self.texts = texts
        self.setWindowTitle(self.texts['zip_title'])
        self.setMinimumWidth(300)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.texts['zip_desc']))
        self.list_widget = QListWidget()
        for sys_name in sorted(MAPA_ROCKNIX_FOLDER.keys()):
            item = QListWidgetItem(sys_name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if sys_name in current_list else Qt.CheckState.Unchecked)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)
        btn = QPushButton(self.texts['save'])
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

    def get_selected(self):
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.text())
        return selected

class DeepInspector:
    @staticmethod
    def identify(path):
        ext = path.suffix.lower()
        try:
            with open(path, 'rb') as f:
                header = f.read(32768)
                if b'PLAYSTATION' in header: return 'psx'
                if b'SEGA SEGASATURN' in header: return 'saturn'
                if b'Dreamcast' in header: return 'dreamcast'
                if header[0:4] in [b'\x80\x37\x12\x40', b'\x40\x12\x37\x80']: return 'n64'
        except: pass
#        ext_map = {'.nes': 'nes', '.sfc': 'snes', '.smc': 'snes', '.gba': 'gba', 
#                   '.nds': 'nds', '.iso': 'ps2', '.cdi': 'dreamcast', '.chd': 'psx', '.vpk': 'psvita'}
        ext_map = {
            # Nintendo
            '.nes': 'nes', '.fds': 'nes',
            '.sfc': 'snes', '.smc': 'snes', '.fig': 'snes',
            '.n64': 'n64', '.z64': 'n64', '.v64': 'n64',
            '.gb': 'gb', '.gbc': 'gbc', '.gba': 'gba',
            '.nds': 'nds', '.3ds': '3ds', '.cia': '3ds',
            '.gc': 'gamecube', '.gcm': 'gamecube', '.rvz': 'gamecube',
            '.wii': 'wii', '.wbfs': 'wii',
            '.vb': 'vb', '.min': 'pokemonmini',
            
            # Sega
            '.sms': 'mastersystem', '.gg': 'gg',
            '.md': 'megadrive', '.gen': 'megadrive', '.smd': 'megadrive',
            '.32x': 'sega32x',
            '.cdi': 'dreamcast', '.gdi': 'dreamcast',
            
            # Sony
            '.iso': 'ps2', # Pode ser mudado pelo DNA acima
            '.chd': 'psx', # Pode ser mudado pelo DNA acima
            '.pbp': 'psx',
            '.cso': 'psp',
            '.vpk': 'psvita',
            
            # Arcade & Engine
            '.pce': 'pcengine', '.cue': 'psx', # CUE é genérico, assume PSX
            '.neogeo': 'neogeo', '.zip': 'fbneo', '.7z': 'fbneo',
            
            # Outros
            '.wsc': 'wswanc', '.ws': 'wswan',
            '.ngp': 'ngp', '.ngpc': 'ngpc',
            '.lnx': 'lynx',
            '.j64': 'jaguar', '.jag': 'jaguar',
            '.a26': 'atari2600', '.a52': 'atari5200', '.a78': 'atari7800',
            '.3do': '3do',
            '.adf': 'amiga', '.d64': 'commodore64',
            '.dsk': 'msx', '.mx1': 'msx', '.mx2': 'msx', '.mp3': 'music', '.ogg': 'music', '.flac': 'music'
        }


        return ext_map.get(ext, 'desconhecido')

# ----------------------------------------------------------------------
# 3. WORKERS
# ----------------------------------------------------------------------
class NetworkFusion(QThread):
    found_signal = pyqtSignal(str, str, str) # IP, Msg, Mode
    log_signal = pyqtSignal(str)

    def __init__(self, texts):
        super().__init__()
        self.texts = texts

    def run(self):
        self.log_signal.emit(self.texts['searching'])
        ip = self.resolve_hostname()
        if not ip: ip = self.scan_network()

        if not ip:
            self.found_signal.emit("", self.texts['ip_not_found'], "NONE")
            return

        self.log_signal.emit(self.texts['ip_found'].format(ip=ip))
        mode = "SSH" if paramiko else "NONE"
        
        # Tentativa de Montagem GIO
        if sys.platform.startswith('linux') and shutil.which("gio"):
            try:
                subprocess.run(["gio", "mount", f"smb://{ip}/roms"], timeout=4, capture_output=True)
                if self.locate_mount(ip): mode = "GIO"
            except: pass

        self.found_signal.emit(ip, "Online", mode)

    def resolve_hostname(self):
        for h in ['ROCKNIX.local', 'ROCKNIX']:
            try: return socket.gethostbyname(h)
            except: pass
        return None

    def scan_network(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80)); local_ip = s.getsockname()[0]; s.close()
            base = '.'.join(local_ip.split('.')[:-1])
            for i in range(1, 150):
                t = f"{base}.{i}"
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM); sock.settimeout(0.04)
                if sock.connect_ex((t, 445)) == 0: sock.close(); return t
                sock.close()
        except: pass
        return None

    def locate_mount(self, ip):
        uid = os.getuid() if hasattr(os, "getuid") else 1000
        possible = [Path(f"/run/user/{uid}/gvfs/"), Path(os.path.expanduser("~/.gvfs/"))]
        for base in possible:
            if base.exists():
                for p in base.iterdir():
                    if ip in p.name: return str(p)
        return None

class BiosAuditorRemote(QThread):
    log_sinal = pyqtSignal(str); item_checked = pyqtSignal(str, str, str); concluido = pyqtSignal()
    def __init__(self, ip): super().__init__(); self.ip = ip
    def run(self):
        if not paramiko: self.concluido.emit(); return
        try:
            ssh = paramiko.SSHClient(); ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.ip, username='root', password='linux', timeout=5)
            stdin, stdout, stderr = ssh.exec_command("ls /storage/roms/bios")
            remote_files = stdout.read().decode().splitlines()
            for f_name, info in BIOS_DATABASE.items():
                if f_name in remote_files:
                    if info['md5'] == 'VARIES': self.item_checked.emit(f_name, "✅ Presente", "orange")
                    else:
                        stdin, out, err = ssh.exec_command(f"md5sum /storage/roms/bios/{f_name}")
                        res = out.read().decode().strip()
                        if res and res.startswith(info['md5']): self.item_checked.emit(f_name, "✅ OK", "green")
                        else: self.item_checked.emit(f_name, "❌ Hash Errado", "red")
                else: self.item_checked.emit(f_name, "❓ Ausente", "gray")
            ssh.close()
        except Exception as e: self.log_sinal.emit(f"Erro SSH: {e}")
        self.concluido.emit()

class WorkerEnvio(QThread):
    log = pyqtSignal(str); progresso = pyqtSignal(int); concluido = pyqtSignal(bool)
    def __init__(self, lista, modo, ip, mount_path, local_dest, zip_list, texts):
        super().__init__()
        self.lista = lista; self.modo = modo; self.ip = ip; self.mount_path = mount_path
        self.local_dest = local_dest; self.zip_list = zip_list; self.texts = texts

    def run(self):
        total = len(self.lista)
        if total == 0: self.concluido.emit(False); return
        base = self.local_dest if self.modo == "LOCAL" else self.mount_path
        
        if self.modo in ["GIO", "LOCAL"] and base:
            with tempfile.TemporaryDirectory() as tmp:
                tmp_p = Path(tmp)
                for i, (orig, sys_n, nome) in enumerate(self.lista):
                    folder = MAPA_ROCKNIX_FOLDER.get(sys_n, sys_n)
                    dest = Path(base) / "roms" / folder
                    if self.modo == "LOCAL" and Path(base).name == "roms": dest = Path(base) / folder
                    dest.mkdir(parents=True, exist_ok=True)
                    final_path = orig
                    if sys_n in self.zip_list and not orig.lower().endswith('.zip'):
                        z = tmp_p / f"{Path(orig).stem}.zip"
                        with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
                            zf.write(orig, arcname=nome)
                        final_path = str(z); nome = z.name
                    shutil.copy2(final_path, dest / nome)
                    self.log.emit(self.texts['copying'].format(name=nome))
                    self.progresso.emit(int(((i+1)/total)*100))
            self.concluido.emit(True); return

        if self.modo == "SSH" and paramiko:
            try:
                ssh = paramiko.SSHClient(); ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(self.ip, username='root', password='linux')
                sftp = ssh.open_sftp()
                for i, (orig, sys_n, nome) in enumerate(self.lista):
                    folder = MAPA_ROCKNIX_FOLDER.get(sys_n, sys_n)
                    rem_dir = f"/storage/roms/{folder}"
                    ssh.exec_command(f"mkdir -p {rem_dir}")
                    sftp.put(str(orig), f"{rem_dir}/{nome}")
                    self.log.emit(self.texts['sending_sftp'].format(name=nome))
                    self.progresso.emit(int(((i+1)/total)*100))
                sftp.close(); ssh.close(); self.concluido.emit(True)
            except Exception as e: self.log.emit(f"Erro SSH: {e}"); self.concluido.emit(False)

# ----------------------------------------------------------------------
# 4. UI PRINCIPAL
# ----------------------------------------------------------------------
class RocknixGui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lang = get_sys_lang()
        self.texts = TRANSLATIONS[self.lang]
        self.modo_ativo = "NONE"
        self.mount_path = None
        self.local_dest_path = None
        self.current_ip = ""
        self.sistemas_zip = ['nes', 'snes', 'gb', 'gbc', 'gba']
        self.bios_validas = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.texts['app_name'])
        self.resize(1000, 800)
        self.setStyleSheet("QMainWindow { background-color: #1a1a1a; color: #eee; } QPushButton { padding: 8px; }")

        central = QWidget(); self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Top Bar
        dest_box = QGroupBox(self.texts['mode_title']); dl = QHBoxLayout()
        self.rb_net = QRadioButton(self.texts['net_mode']); self.rb_net.setChecked(True)
        self.rb_local = QRadioButton(self.texts['local_mode'])
        self.btn_sync = QPushButton(self.texts['btn_sync']); self.btn_sync.clicked.connect(self.sync_net)
        self.btn_dest = QPushButton(self.texts['btn_local_path']); self.btn_dest.clicked.connect(self.sel_dest); self.btn_dest.hide()
        self.lbl_st = QLabel(self.texts['status_disconnected'])
        dl.addWidget(self.rb_net); dl.addWidget(self.rb_local); dl.addStretch(); dl.addWidget(self.lbl_st); dl.addWidget(self.btn_sync); dl.addWidget(self.btn_dest)
        dest_box.setLayout(dl); layout.addWidget(dest_box)

        self.tabs = QTabWidget(); layout.addWidget(self.tabs)
        
        # ROMS
        self.t_roms = QWidget(); v_roms = QVBoxLayout(self.t_roms)
        t_btns = QHBoxLayout(); b_zip = QPushButton(self.texts['config_zip']); b_zip.clicked.connect(self.config_zip)
        b_bulk = QPushButton(self.texts['btn_bulk']); b_bulk.clicked.connect(self.bulk_set)
        t_btns.addWidget(b_zip); t_btns.addWidget(b_bulk); v_roms.addLayout(t_btns)
        
        self.tb_roms = QTableWidget(0, 4); self.tb_roms.setHorizontalHeaderLabels(["X", "File", "DNA", "Dest"])
        self.tb_roms.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tb_roms.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        v_roms.addWidget(self.tb_roms)
        
        h_roms = QHBoxLayout(); b_scan = QPushButton(self.texts['btn_scan']); b_scan.clicked.connect(self.scan_roms)
        b_send = QPushButton(self.texts['btn_send']); b_send.clicked.connect(self.send_roms)
        h_roms.addWidget(b_scan); h_roms.addWidget(b_send); v_roms.addLayout(h_roms)
        self.tabs.addTab(self.t_roms, self.texts['tab_roms'])

        # BIOS
        self.t_bios = QWidget(); v_bios = QVBoxLayout(self.t_bios)
        self.tb_bios = QTableWidget(0, 3); self.tb_bios.setHorizontalHeaderLabels(["BIOS", "Status", "Info"])
        self.tb_bios.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        v_bios.addWidget(self.tb_bios)
        h_bios = QHBoxLayout()
        b_audit_l = QPushButton(self.texts['audit_local']); b_audit_l.clicked.connect(self.audit_bios_local)
        self.btn_deploy = QPushButton(self.texts['btn_deploy_bios'].format(n=0)); self.btn_deploy.setEnabled(False); self.btn_deploy.clicked.connect(self.deploy_bios)
        b_audit_n = QPushButton(self.texts['btn_audit_net']); b_audit_n.clicked.connect(self.audit_bios_net)
        self.dest_combo = QComboBox(); self.dest_combo.addItems(["/storage/roms/bios", "/roms/bios"]); self.dest_combo.setEditable(True)
        h_bios.addWidget(b_audit_l); h_bios.addWidget(QLabel(self.texts['dest_label'])); h_bios.addWidget(self.dest_combo); h_bios.addWidget(self.btn_deploy); h_bios.addWidget(b_audit_n)
        v_bios.addLayout(h_bios); self.tabs.addTab(self.t_bios, self.texts['tab_bios'])

        self.log = QTextEdit(); self.log.setReadOnly(True); self.log.setStyleSheet("background: #000; color: #0f0;")
        self.tabs.addTab(self.log, self.texts['tab_console'])
        self.prog = QProgressBar(); layout.addWidget(self.prog)
        self.rb_net.toggled.connect(self.toggle_mode)

    def toggle_mode(self):
        net = self.rb_net.isChecked()
        self.btn_sync.setVisible(net); self.btn_dest.setVisible(not net)
        self.modo_ativo = "NONE" if net else "LOCAL"
        self.lbl_st.setText(self.texts['status_disconnected'] if net else "Modo Local Ativo")

    def sync_net(self):
        self.net_thread = NetworkFusion(self.texts)
        self.net_thread.log_signal.connect(self.log.append)
        self.net_thread.found_signal.connect(self.on_net_found)
        self.net_thread.start()

    def on_net_found(self, ip, msg, mode):
        self.current_ip = ip; self.modo_ativo = mode
        if ip: self.lbl_st.setText(self.texts['status_connected'].format(ip=ip, mode=mode))
        else: self.lbl_st.setText(msg)
        if mode == "GIO": self.mount_path = self.net_thread.locate_mount(ip)

    def sel_dest(self):
        p = QFileDialog.getExistingDirectory(self, "Selecionar Destino"); 
        if p: self.local_dest_path = p; self.lbl_st.setText(f"Destino Local: {p}")

    def config_zip(self):
        d = ZipConfigDialog(self.sistemas_zip, self.texts)
        if d.exec(): self.sistemas_zip = d.get_selected()

    def bulk_set(self):
        sel = self.tb_roms.selectionModel().selectedRows()
        if not sel: return
        s, ok = QInputDialog.getItem(self, self.texts['bulk_title'], self.texts['bulk_msg'], sorted(MAPA_ROCKNIX_FOLDER.keys()), 0, False)
        if ok:
            for idx in sel: self.tb_roms.cellWidget(idx.row(), 3).setCurrentText(s)

    def scan_roms(self):
        p = QFileDialog.getExistingDirectory(self, "Add Folder")
        if not p: return
        for f in Path(p).rglob("*"):
            if f.is_file() and f.suffix.lower() in ALL_EXTENSIONS:
                r = self.tb_roms.rowCount(); self.tb_roms.insertRow(r)
                ck = QTableWidgetItem(); ck.setCheckState(Qt.CheckState.Checked); self.tb_roms.setItem(r, 0, ck)
                self.tb_roms.setItem(r, 1, QTableWidgetItem(f.name))
                dna = DeepInspector.identify(f); self.tb_roms.setItem(r, 2, QTableWidgetItem(dna))
                cb = QComboBox(); cb.addItems(sorted(MAPA_ROCKNIX_FOLDER.keys())); cb.setCurrentText(dna); self.tb_roms.setCellWidget(r, 3, cb)
                self.tb_roms.item(r, 1).setData(Qt.ItemDataRole.UserRole, str(f))

    def send_roms(self):
        if self.modo_ativo == "NONE": QMessageBox.warning(self, "Ops", self.texts['msg_configure_dest']); return
        lst = []
        for i in range(self.tb_roms.rowCount()):
            if self.tb_roms.item(i, 0).checkState() == Qt.CheckState.Checked:
                path = self.tb_roms.item(i, 1).data(Qt.ItemDataRole.UserRole)
                lst.append((path, self.tb_roms.cellWidget(i, 3).currentText(), Path(path).name))
        self.sender = WorkerEnvio(lst, self.modo_ativo, self.current_ip, self.mount_path, self.local_dest_path, self.sistemas_zip, self.texts)
        self.sender.log.connect(self.log.append); self.sender.progresso.connect(self.prog.setValue)
        self.sender.concluido.connect(lambda: QMessageBox.information(self, "OK", self.texts['msg_finished']))
        self.sender.start()

    def audit_bios_local(self):
        p = QFileDialog.getExistingDirectory(self, "BIOS Folder")
        if not p: return
        self.tb_bios.setRowCount(0); self.bios_validas = []
        for f_name, info in BIOS_DATABASE.items():
            f_path = Path(p) / f_name
            st = "Ausente"; color = "gray"
            if f_path.exists():
                h = hashlib.md5(); 
                with open(f_path, "rb") as f: 
                    for chunk in iter(lambda: f.read(4096), b""): h.update(chunk)
                if info['md5'] == 'VARIES' or h.hexdigest() == info['md5']:
                    st = "✅ OK"; color = "green"; self.bios_validas.append(f_path)
                else: st = "❌ Inválido"; color = "red"
            self.add_bios_row(f_name, st, color)
        self.btn_deploy.setEnabled(bool(self.bios_validas))
        self.btn_deploy.setText(self.texts['btn_deploy_bios'].format(n=len(self.bios_validas)))

    def audit_bios_net(self):
        if not self.current_ip: return
        self.tb_bios.setRowCount(0)
        self.auditor_net = BiosAuditorRemote(self.current_ip)
        self.auditor_net.item_checked.connect(self.add_bios_row)
        self.auditor_net.start()

    def add_bios_row(self, name, st, color):
        r = self.tb_bios.rowCount(); self.tb_bios.insertRow(r)
        self.tb_bios.setItem(r, 0, QTableWidgetItem(name))
        it = QTableWidgetItem(st)
        if color == "green": it.setForeground(Qt.GlobalColor.green)
        elif color == "red": it.setForeground(Qt.GlobalColor.red)
        self.tb_bios.setItem(r, 1, it)

    def deploy_bios(self):
        # Reutilizando WorkerEnvio simplificado ou lógica direta aqui
        QMessageBox.information(self, "BIOS", "Enviando BIOS...")

if __name__ == "__main__":
    app = QApplication(sys.argv); gui = RocknixGui(); gui.show(); sys.exit(app.exec())
