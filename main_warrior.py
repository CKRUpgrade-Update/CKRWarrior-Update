import customtkinter as ctk
import pyautogui
import mss
import numpy as np
import cv2
from PIL import Image, ImageTk
import threading
import time
import ctypes
import os
import sys
import json
import requests
from pynput import keyboard

# --- WINDOWS DPI ZIRHI ---
try: ctypes.windll.user32.SetProcessDPIAware()
except: pass

# --- YÖNETİCİ İZNİ BLOĞU ---
def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

if not is_admin():
    if getattr(sys, 'frozen', False):
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv[1:]), None, 1)
    else:
        script_path = os.path.abspath(sys.argv[0])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script_path}"', None, 1)
    os._exit(0)

# --- OTOMATİK GÜNCELLEME SİSTEMİ ---
MEVCUT_VERSIYON = "1.1"
VERSIYON_URL = "https://raw.githubusercontent.com/CKRUpgrade-Update/CKRWarrior-Update/main/versiyon.txt"
API_URL = "https://api.github.com/repos/CKRUpgrade-Update/CKRWarrior-Update/releases/latest"

def guncelleme_kontrol_et():
    if not getattr(sys, 'frozen', False): return
    try:
        import time as time_lib
        import subprocess
        headers_versiyon = {'Cache-Control': 'no-cache, no-store, must-revalidate', 'Pragma': 'no-cache', 'Expires': '0'}
        cevap = requests.get(f"{VERSIYON_URL}?t={int(time_lib.time())}", headers=headers_versiyon, timeout=5)
        yeni_versiyon = cevap.text.strip()
        if yeni_versiyon != MEVCUT_VERSIYON:
            msg_cevap = ctypes.windll.user32.MessageBoxW(0, f"Yeni bir CKR Warrior sürümü bulundu (v{yeni_versiyon}).\nİçeriklerle birlikte şimdi güncellensin mi?", "CKR Update", 4 + 0x40)
            if msg_cevap != 6: return
            api_cevap = requests.get(f"{API_URL}?t={int(time_lib.time())}", headers=headers_versiyon, timeout=10)
            if api_cevap.status_code != 200: return
            assets = api_cevap.json().get("assets", [])
            mevcut_exe = sys.executable
            exe_dir = os.path.dirname(mevcut_exe)
            temp_dir = os.environ.get('TEMP', exe_dir)
            indirilenler = []
            headers_exe = {'User-Agent': 'Mozilla/5.0'}
            for asset in assets:
                dosya_adi = asset["name"]
                gecici_yol = os.path.join(temp_dir, dosya_adi + ".update")
                r = requests.get(asset["browser_download_url"], stream=True, allow_redirects=True, headers=headers_exe)
                if r.status_code == 200:
                    with open(gecici_yol, "wb") as f:
                        for chunk in r.iter_content(chunk_size=2097152):
                            if chunk: f.write(chunk)
                    indirilenler.append((gecici_yol, dosya_adi))
            if not indirilenler: return
            for k in list(os.environ.keys()):
                 if k.upper().startswith('_MEI') or k.upper().startswith('TCL') or k.upper().startswith('TK'): del os.environ[k]
            bat_yolu = os.path.join(temp_dir, "ckr_updater.bat")
            bat_icerik = f"@echo off\ntimeout /t 1 /nobreak > NUL\ntaskkill /f /im \"{os.path.basename(mevcut_exe)}\" > NUL 2>&1\ntimeout /t 1 /nobreak > NUL\n:DONGU\ndel /f /q \"{mevcut_exe}\"\nif exist \"{mevcut_exe}\" (\n    timeout /t 1 /nobreak > NUL\n    goto DONGU\n)\n"
            for kls in ['yaratik', 'altisim', 'icons']: bat_icerik += f"if not exist \"{os.path.join(exe_dir, kls)}\" mkdir \"{os.path.join(exe_dir, kls)}\"\n"
            for gecici, asil in indirilenler:
                if asil.lower().endswith('.png'):
                    if asil.startswith('icon_'): h = os.path.join(exe_dir, 'icons', asil)
                    elif asil.startswith('alt_'): h = os.path.join(exe_dir, 'altisim', asil)
                    else: h = os.path.join(exe_dir, 'yaratik', asil)
                elif asil.lower().endswith('.exe'): h = mevcut_exe
                else: h = os.path.join(exe_dir, asil)
                bat_icerik += f"move /y \"{gecici}\" \"{h}\" > NUL\n"
            bat_icerik += f"start \"\" \"{mevcut_exe}\"\ndel /f /q \"%~f0\"\n"
            with open(bat_yolu, "w", encoding="utf-8") as f: f.write(bat_icerik)
            subprocess.Popen(["cmd.exe", "/c", bat_yolu], creationflags=0x08000000, close_fds=True)
            os._exit(0)
    except: pass

guncelleme_kontrol_et()

# --- DONANIM MOUSE & KLAVYE API ---
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

def win32_click(x, y):
    ctypes.windll.user32.SetCursorPos(int(x), int(y))
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def get_external_path(rel_path):
    base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel_path)

klavye_kilidi = threading.Lock()

class MacroApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"CKRMacro-Warrior v{MEVCUT_VERSIYON}")
        self.geometry("1100x850")
        
        ikon_yolu = get_external_path("anahatar.ico")
        if os.path.exists(ikon_yolu): self.iconbitmap(ikon_yolu)
            
        self.yaratik_klasoru = get_external_path("yaratik")
        self.altisim_klasoru = get_external_path("altisim")
        self.icons_klasoru = get_external_path("icons")
        self.settings_file = get_external_path("ayarlar.json")
        for k in [self.yaratik_klasoru, self.altisim_klasoru, self.icons_klasoru]: os.makedirs(k, exist_ok=True)
            
        self.makro_aktif = False
        self.tarama_alani = None
        self.tarama_alani_2 = None
        self.hp_bar_alani = None
        self.mp_bar_alani = None
        self.buff_bar_alani = None
        self.hedef_path = ""
        self.alt_isim_path = ""
        
        self.var_master_allow = ctk.BooleanVar(value=False)
        self.var_anti_afk_mode = ctk.BooleanVar(value=False)
        self.var_hp_active = ctk.BooleanVar(value=False)
        self.var_mp_active = ctk.BooleanVar(value=False)
        self.var_always_on_top = ctk.BooleanVar(value=False)
        self.macro_hotkey = ctk.StringVar(value="CAPS_LOCK")
        
        # YENİ: Alt İsim Tıklama Mesafesi (1, 2, 3 cm)
        self.var_afk_mesafe = ctk.StringVar(value="2")
        
        self.attack_vars = {}
        self.buff_ui = {}
        self.pot_vars = {"hp_limit": ctk.StringVar(value="70"), "hp_tus": ctk.StringVar(value="8"), "mp_limit": ctk.StringVar(value="30"), "mp_tus": ctk.StringVar(value="9")}
        
        self.warrior_r_ms = ctk.StringVar(value="485")
        self.warrior_skill_ms = ctk.StringVar(value="350") 
        self.main_atk_page = ctk.StringVar(value="F1") # YENİ: ANA ATAK SAYFASI HAFIZASI
        
        self.buff_listesi = ["KAFA", "SPRINT", "DEFANS", "KOL", "KILIC", "BOOSTER", "FRENZY", "REGEN"]
        self.buff_son_gorulme = {b: time.time() for b in self.buff_listesi}
        # YENİ EKLENEN: Scroll Buffları Listesi ve Hafızası
        self.scroll_listesi = ["sw", "hp", "def", "ap", "str", "agacatak", "agacdef", "redpot"]
        self.scroll_son_gorulme = {s: time.time() for s in self.scroll_listesi}
        self.scroll_ui = {}

        self.scancodes = {
            "1":0x02, "2":0x03, "3":0x04, "4":0x05, "5":0x06, "6":0x07, "7":0x08, "8":0x09, "9":0x0A, "0":0x0B,
            "Q":0x10, "W":0x11, "E":0x12, "R":0x13, "T":0x14, "Y":0x15, "U":0x16, "I":0x17, "O":0x18, "P":0x19,
            "A":0x1E, "S":0x1F, "D":0x20, "F":0x21, "G":0x22, "H":0x23, "J":0x24, "K":0x25, "L":0x26,
            "Z":0x2C, "X":0x2D, "C":0x2E, "V":0x2F, "B":0x30, "N":0x31, "M":0x32,
            "F1":0x3B, "F2":0x3C, "F3":0x3D, "F4":0x3E, "F5":0x3F, "F6":0x40, "F7":0x41, "F8":0x42
        }

        self.setup_ui()
        self.galeri_tara()
        self.load_settings()
        
        threading.Thread(target=self.atak_dongusu, daemon=True).start()
        threading.Thread(target=self.buff_dongusu, daemon=True).start()
        threading.Thread(target=self.pot_dongusu, daemon=True).start()
        
        self.listener = keyboard.Listener(on_press=self.on_global_hotkey)
        self.listener.start()

    def key_press(self, key_str):
        sc = self.scancodes.get(str(key_str).upper())
        if sc:
            ctypes.windll.user32.keybd_event(0, sc, 0x0008, 0)
            time.sleep(0.015) # Tuş basma süresi çok hafif hızlandırıldı
            ctypes.windll.user32.keybd_event(0, sc, 0x0008 | 0x0002, 0)

    def atak_dongusu(self):
        while True:
            if self.makro_aktif and self.var_master_allow.get():
                with mss.mss() as sct:
                    ys = False
                    
                    # 1. Yaratık Hedefi (Can Barı) Ekranda mı?
                    if self.tarama_alani and self.hedef_path:
                        ndl = cv2.imread(self.hedef_path)
                        if ndl is not None:
                            try:
                                scr = np.array(sct.grab({"top": self.tarama_alani[1], "left": self.tarama_alani[0], "width": self.tarama_alani[2], "height": self.tarama_alani[3]}))[:,:,:3]
                                res = cv2.matchTemplate(scr, ndl, cv2.TM_CCOEFF_NORMED)
                                # Can barı eşleştiyse, saldırmaya hazırdır
                                if cv2.minMaxLoc(res)[1] >= 0.75: 
                                    ys = True
                            except: pass

                    # 2. Can Barı YOKSA (Yaratık ölüyse veya henüz hedefe girmedikse)
                    if not ys: 
                        if self.var_anti_afk_mode.get() and self.tarama_alani_2 and self.alt_isim_path:
                            
                            # BEKLEME SÜRESİ KALDIRILDI! Işık hızında alt isim taramaya devam.
                            alt = cv2.imread(self.alt_isim_path)
                            if alt is not None:
                                try:
                                    scr2 = np.array(sct.grab({"top": self.tarama_alani_2[1], "left": self.tarama_alani_2[0], "width": self.tarama_alani_2[2], "height": self.tarama_alani_2[3]}))[:,:,:3]
                                    res2 = cv2.matchTemplate(scr2, alt, cv2.TM_CCOEFF_NORMED)
                                    _, max_v, _, max_l = cv2.minMaxLoc(res2)
                                    
                                    if max_v >= 0.75:
                                        # Seçilen santime göre dinamik piksel boşluğu
                                        secim = self.var_afk_mesafe.get()
                                        if secim == "1": y_off = 40
                                        elif secim == "3": y_off = 120
                                        else: y_off = 80 # Varsayılan 2cm
                                        
                                        cx = int(self.tarama_alani_2[0] + max_l[0] + (alt.shape[1]//2))
                                        cy = int(self.tarama_alani_2[1] + max_l[1] + alt.shape[0] + y_off)
                                        
                                        win32_click(cx, cy)
                                        # Tıkladıktan sonra mili-saniyelik dinlenme, ardından hedef açılmadıysa VAZGEÇMEDEN TEKRAR TIKLAR!
                                        time.sleep(0.05) 
                                except: pass
                        else:
                            # Anti-AFK kapalıysa veya alt isim seçili değilse, seri Z taramaya devam
                            with klavye_kilidi: self.key_press("Z")
                            time.sleep(0.05)
                            
                    # 3. Can Barı VARSA (Yaratık Seçiliyse) Seri Vurmaya Başla!
                    else: 
                        if self.attack_vars["R"]["active"].get():
                            with klavye_kilidi: self.key_press("R")
                            try: time.sleep(int(self.warrior_r_ms.get())/1000)
                            except: time.sleep(0.1)
                        for i in range(1, 6):
                            if not self.makro_aktif: break
                            if self.attack_vars[str(i)]["active"].get():
                                with klavye_kilidi: self.key_press(str(i))
                                try: time.sleep(int(self.warrior_skill_ms.get())/1000)
                                except: time.sleep(0.1)
            time.sleep(0.001)

    def buff_dongusu(self):
        while True:
            if self.makro_aktif and self.var_master_allow.get() and getattr(self, 'buff_bar_alani', None):
                with mss.mss() as sct:
                    try:
                        b_alani = self.buff_bar_alani
                        mon = {"top": b_alani[1], "left": b_alani[0], "width": b_alani[2], "height": b_alani[3]}
                        scr = np.array(sct.grab(mon))[:,:,:3]
                        
                        # Hem yetenekleri hem de scrolları tek bir listede birleştirip tarıyoruz
                        tum_bufflar = [(b, self.buff_ui[b], self.buff_son_gorulme) for b in self.buff_listesi] + \
                                      [(s, self.scroll_ui[s], self.scroll_son_gorulme) for s in self.scroll_listesi]
                        
                        for item_adi, ui_data, son_gorulme_hafizasi in tum_bufflar:
                            if not self.makro_aktif: break
                            if ui_data["active"].get():
                                path = os.path.join(self.icons_klasoru, f"{item_adi}.png")
                                if os.path.exists(path):
                                    ndl = cv2.imread(path)
                                    if ndl is not None:
                                        # Kutu boyutu koruması
                                        if scr.shape[0] < ndl.shape[0] or scr.shape[1] < ndl.shape[1]:
                                            continue
                                            
                                        res = cv2.matchTemplate(scr, ndl, cv2.TM_CCOEFF_NORMED)
                                        max_val = cv2.minMaxLoc(res)[1]
                                        
                                        if max_val >= 0.65:
                                            son_gorulme_hafizasi[item_adi] = time.time()
                                        else:
                                            # Eğer 2.5 saniyedir hiç görmediyse bas
                                            if time.time() - son_gorulme_hafizasi[item_adi] > 2.5:
                                                with klavye_kilidi:
                                                    self.key_press(ui_data["page_key"].get())
                                                    time.sleep(0.05)
                                                    self.key_press(ui_data["skill_key"].get())
                                                    time.sleep(0.05)
                                                    self.key_press(self.main_atk_page.get())
                                                
                                                time.sleep(0.8) # Animasyon süresi
                                                son_gorulme_hafizasi[item_adi] = time.time()
                    except: pass
            time.sleep(0.1)

    def pot_dongusu(self):
        while True:
            if self.makro_aktif and self.var_master_allow.get():
                with mss.mss() as sct:
                    mp_basildi = False
                    if self.var_mp_active.get() and self.mp_bar_alani:
                        try:
                            mon_mp = {"top": self.mp_bar_alani[1], "left": self.mp_bar_alani[0], "width": self.mp_bar_alani[2], "height": self.mp_bar_alani[3]}
                            img = np.array(sct.grab(mon_mp))[:,:,:3]
                            limit = int(self.pot_vars["mp_limit"].get())
                            check_x = int((img.shape[1] * limit) / 100)
                            check_x = min(max(check_x, 0), img.shape[1] - 1) 
                            px = img[img.shape[0]//2, check_x]
                            if int(px[0]) < 90:
                                with klavye_kilidi: self.key_press(self.pot_vars["mp_tus"].get())
                                mp_basildi = True
                                time.sleep(0.05) # Hızlandırıldı
                        except: pass
                        
                    if not mp_basildi and self.var_hp_active.get() and self.hp_bar_alani:
                        try:
                            mon_hp = {"top": self.hp_bar_alani[1], "left": self.hp_bar_alani[0], "width": self.hp_bar_alani[2], "height": self.hp_bar_alani[3]}
                            img = np.array(sct.grab(mon_hp))[:,:,:3]
                            limit = int(self.pot_vars["hp_limit"].get())
                            check_x = int((img.shape[1] * limit) / 100)
                            check_x = min(max(check_x, 0), img.shape[1] - 1)
                            px = img[img.shape[0]//2, check_x]
                            if int(px[2]) < 90:
                                with klavye_kilidi: self.key_press(self.pot_vars["hp_tus"].get())
                                time.sleep(0.05) # Hızlandırıldı
                        except: pass
            time.sleep(0.05) # Potları saniyede 20 kez tarar

    def on_global_hotkey(self, key):
        try: k = key.char.upper()
        except AttributeError:
            k = key.name.upper()
            if k == 'CAPS_LOCK': k = "CAPS_LOCK"
        if k == self.macro_hotkey.get().upper(): self.after(0, self.toggle_macro) 

    def toggle_macro(self):
        if not self.var_master_allow.get(): return
        self.makro_aktif = not self.makro_aktif
        if self.makro_aktif:
            self.lbl_durum.configure(text="DURUM: AKTİF", text_color="#2ecc71")
            self.btn_toggle.configure(text="DURDUR", fg_color="#e74c3c")
        else:
            self.lbl_durum.configure(text="DURUM: PASİF", text_color="#e74c3c")
            self.btn_toggle.configure(text="BAŞLAT", fg_color="#2ecc71")

    def toggle_always_on_top(self):
        self.attributes("-topmost", self.var_always_on_top.get())

    def listen_for_key(self, tv, bw):
        bw.configure(text="Bas...", fg_color="#e74c3c", text_color="white"); self.focus_set()
        def on_key(e):
            k = e.keysym.upper()
            if k == "RETURN": k = "ENTER"
            elif k == "ESCAPE": k = "ESC"
            elif k == "CAPS_LOCK": k = "CAPS_LOCK"
            elif k.startswith("SHIFT"): k = "SHIFT"
            tv.set(k); bw.configure(text=k, fg_color="#2980b9", text_color="white"); self.unbind("<KeyPress>") 
        self.bind("<KeyPress>", on_key)

    def setup_ui(self):
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color="#141414", corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        ctk.CTkLabel(self.sidebar, text=f"CKR WARRIOR\nv{MEVCUT_VERSIYON}", font=("Arial", 24, "bold"), text_color="#f1c40f").pack(pady=(40, 30))
        self.btn_yaratik = ctk.CTkButton(self.sidebar, text="🎯 YARATIK", font=("Arial", 14, "bold"), height=45, command=lambda: self.select_frame("yaratik"), fg_color="transparent", text_color="white")
        self.btn_yaratik.pack(pady=5, padx=15, fill="x")
        self.btn_warrior = ctk.CTkButton(self.sidebar, text="⚔️ SAVAŞ & BUFF", font=("Arial", 14, "bold"), height=45, command=lambda: self.select_frame("warrior"), fg_color="transparent", text_color="white")
        self.btn_warrior.pack(pady=5, padx=15, fill="x")
        self.btn_pot = ctk.CTkButton(self.sidebar, text="🧪 AKILLI POT", font=("Arial", 14, "bold"), height=45, command=lambda: self.select_frame("pot"), fg_color="transparent", text_color="white")
        self.btn_pot.pack(pady=5, padx=15, fill="x")
        sf = ctk.CTkFrame(self.sidebar, fg_color="#1a1a1a", border_width=1, border_color="#333333", corner_radius=8)
        sf.pack(side="bottom", pady=20, fill="x", padx=10, ipady=5)
        self.lbl_durum = ctk.CTkLabel(sf, text="DURUM: PASİF", font=("Arial", 16, "bold"), text_color="#e74c3c")
        self.lbl_durum.pack(pady=(10, 5))
        self.btn_toggle = ctk.CTkButton(sf, text="BAŞLAT", font=("Arial", 14, "bold"), fg_color="#2ecc71", text_color="white", height=35, command=self.toggle_macro)
        self.btn_toggle.pack(fill="x", padx=15, pady=5)
        hr = ctk.CTkFrame(sf, fg_color="transparent")
        hr.pack(fill="x", padx=15, pady=(5, 10))
        ctk.CTkLabel(hr, text="Çalıştırma Tuşu:", font=("Arial", 11, "bold"), text_color="#bdc3c7").pack(side="left")
        self.btn_macro_hk = ctk.CTkButton(hr, textvariable=self.macro_hotkey, width=65, height=24, fg_color="#2980b9", text_color="white", font=("Arial", 11, "bold"))
        self.btn_macro_hk.configure(command=lambda b=self.btn_macro_hk, v=self.macro_hotkey: self.listen_for_key(v, b))
        self.btn_macro_hk.pack(side="right")
        ctk.CTkCheckBox(self.sidebar, text="Her Zaman Üstte", variable=self.var_always_on_top, command=self.toggle_always_on_top, font=("Arial", 12), text_color="white").pack(side="bottom", pady=5)
        self.cont = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=0)
        self.cont.pack(side="right", fill="both", expand=True)
        self.f_yaratik = ctk.CTkFrame(self.cont, fg_color="transparent")
        self.f_warrior = ctk.CTkFrame(self.cont, fg_color="transparent")
        self.f_pot = ctk.CTkFrame(self.cont, fg_color="transparent")
        self.setup_yaratik_ui(); self.setup_warrior_ui(); self.setup_pot_ui(); self.select_frame("yaratik")

    def setup_yaratik_ui(self):
        ctk.CTkLabel(self.f_yaratik, text="YARATIK HEDEFLEME SİSTEMİ", font=("Arial", 22, "bold"), text_color="#f1c40f").pack(pady=(20, 10))
        top = ctk.CTkFrame(self.f_yaratik, border_width=1, border_color="#f1c40f", fg_color="#252525")
        top.pack(padx=30, pady=10, fill="x")
        ctk.CTkSwitch(top, text="MAKRO MASTER İZNİ (ANA ŞALTER)", variable=self.var_master_allow, font=("Arial", 16, "bold"), text_color="white", progress_color="#2ecc71").pack(pady=15)
        b1 = ctk.CTkFrame(self.f_yaratik, fg_color="#252525", corner_radius=8, border_width=1, border_color="#555555")
        b1.pack(padx=30, pady=10, fill="x")
        ctk.CTkLabel(b1, text="1. ANA YARATIK HEDEFİ", font=("Arial", 14, "bold"), text_color="#3498db").pack(pady=5)
        f1 = ctk.CTkFrame(b1, fg_color="transparent"); f1.pack(pady=5)
        ctk.CTkButton(f1, text="TARAMA ALANI ÇİZ", command=lambda: self.alan_sec(1), fg_color="#2980b9", text_color="white").grid(row=0, column=0, padx=5)
        ctk.CTkButton(f1, text="PNG YAKALA", command=self.sec_baslat, fg_color="#e67e22", text_color="white").grid(row=0, column=1, padx=5)
        self.opt_galeri_1 = ctk.CTkOptionMenu(f1, values=["Seçiniz..."], width=150, text_color="white", command=self.gorsel_yukle_1)
        self.opt_galeri_1.grid(row=0, column=2, padx=5)
        self.lbl_img_1 = ctk.CTkLabel(b1, text="Görsel Bekleniyor...", text_color="#7f8c8d", font=("Arial", 12)); self.lbl_img_1.pack(pady=10)
        b2 = ctk.CTkFrame(self.f_yaratik, fg_color="#252525", corner_radius=8, border_width=1, border_color="#555555")
        b2.pack(padx=30, pady=10, fill="x")
        box_2 = ctk.CTkFrame(self.f_yaratik, fg_color="#252525", corner_radius=8, border_width=1, border_color="#555555")
        box_2.pack(padx=30, pady=10, fill="x")
        
        top_f2 = ctk.CTkFrame(box_2, fg_color="transparent")
        top_f2.pack(fill="x", pady=5)
        
        ctk.CTkCheckBox(top_f2, text="ANTİ-AFK MODU", variable=self.var_anti_afk_mode, font=("Arial", 14, "bold"), text_color="#e74c3c").pack(side="left", padx=(10, 15))
        
        dist_f = ctk.CTkFrame(top_f2, fg_color="transparent")
        dist_f.pack(side="left")
        ctk.CTkLabel(dist_f, text="Tıklama:", font=("Arial", 11), text_color="#bdc3c7").pack(side="left", padx=5)
        ctk.CTkRadioButton(dist_f, text="1cm", variable=self.var_afk_mesafe, value="1", font=("Arial", 11), text_color="white").pack(side="left", padx=2)
        ctk.CTkRadioButton(dist_f, text="2cm", variable=self.var_afk_mesafe, value="2", font=("Arial", 11), text_color="white").pack(side="left", padx=2)
        ctk.CTkRadioButton(dist_f, text="3cm", variable=self.var_afk_mesafe, value="3", font=("Arial", 11), text_color="white").pack(side="left", padx=2)

        btn_f2 = ctk.CTkFrame(box_2, fg_color="transparent")
        btn_f2.pack(pady=5)
        ctk.CTkButton(btn_f2, text="TARAMA ALANI ÇİZ", command=lambda: self.alan_sec(2), fg_color="#2980b9", text_color="white").grid(row=0, column=0, padx=5)
        ctk.CTkButton(btn_f2, text="PNG YAKALA", command=self.alt_isim_sec_baslat, fg_color="#e67e22", text_color="white").grid(row=0, column=1, padx=5)
        
        self.opt_galeri_2 = ctk.CTkOptionMenu(btn_f2, values=["Seçiniz..."], width=150, text_color="white", command=self.gorsel_yukle_2)
        self.opt_galeri_2.grid(row=0, column=2, padx=5)
        self.lbl_img_2 = ctk.CTkLabel(box_2, text="Görsel Bekleniyor...", text_color="#7f8c8d", font=("Arial", 12))
        self.lbl_img_2.pack(pady=10)

    def gorsel_yukle_1(self, f):
        if f == "Seçiniz...": return
        self.hedef_path = os.path.join(self.yaratik_klasoru, f)
        try: 
            img = Image.open(self.hedef_path)
            img.thumbnail((120, 120))
            self.lbl_img_1.configure(image=ctk.CTkImage(light_image=img, dark_image=img, size=img.size), text="")
        except: 
            self.lbl_img_1.configure(image=None, text="Görsel Yüklenemedi!") # BURASI DEĞİŞTİ (None eklendi)

    def gorsel_yukle_2(self, f):
        if f == "Seçiniz...": return
        self.alt_isim_path = os.path.join(self.altisim_klasoru, f)
        try: 
            img = Image.open(self.alt_isim_path)
            img.thumbnail((120, 120))
            self.lbl_img_2.configure(image=ctk.CTkImage(light_image=img, dark_image=img, size=img.size), text="")
        except: 
            self.lbl_img_2.configure(image=None, text="Görsel Yüklenemedi!") # BURASI DEĞİŞTİ (None eklendi)

    def setup_warrior_ui(self):
        af = ctk.CTkFrame(self.f_warrior, fg_color="#252525", border_width=1, border_color="#f1c40f", corner_radius=8)
        af.pack(padx=30, pady=(30, 10), fill="x", ipadx=10, ipady=15)
        ctk.CTkLabel(af, text="WARRIOR SALDIRI AYARLARI", font=("Arial", 16, "bold"), text_color="#f1c40f").pack(pady=(0, 15))
        
        # YENİ EKLENEN ANA ATAK SAYFASI (F1 vs.)
        mr = ctk.CTkFrame(af, fg_color="transparent"); mr.pack(pady=5)
        ctk.CTkLabel(mr, text="SKILL MS:", font=("Arial", 12, "bold"), text_color="#bdc3c7").pack(side="left", padx=5)
        ctk.CTkEntry(mr, textvariable=self.warrior_skill_ms, width=60, text_color="white", fg_color="#333333").pack(side="left", padx=(0, 15))
        ctk.CTkLabel(mr, text="R MS:", font=("Arial", 12, "bold"), text_color="#bdc3c7").pack(side="left", padx=5)
        ctk.CTkEntry(mr, textvariable=self.warrior_r_ms, width=60, text_color="white", fg_color="#333333").pack(side="left", padx=(0, 15))
        
        ctk.CTkLabel(mr, text="ANA SAYFA:", font=("Arial", 12, "bold"), text_color="#f39c12").pack(side="left", padx=(10, 5))
        btn_main = ctk.CTkButton(mr, textvariable=self.main_atk_page, width=45, height=26, fg_color="#d35400", text_color="white", font=("Arial", 11, "bold"))
        btn_main.configure(command=lambda bw=btn_main, v=self.main_atk_page: self.listen_for_key(v, bw)); btn_main.pack(side="left")

        tf = ctk.CTkFrame(af, fg_color="transparent"); tf.pack(pady=15)
        for i in range(1, 6):
            self.attack_vars[str(i)] = {"active": ctk.BooleanVar(), "key": ctk.StringVar(value=str(i))}
            f = ctk.CTkFrame(tf, fg_color="transparent"); f.pack(side="left", padx=15)
            ctk.CTkCheckBox(f, text=str(i), variable=self.attack_vars[str(i)]["active"], font=("Arial", 14, "bold"), text_color="white").pack(side="left")
        self.attack_vars["R"] = {"active": ctk.BooleanVar(value=True), "key": ctk.StringVar(value="R")}
        fr = ctk.CTkFrame(tf, fg_color="transparent"); fr.pack(side="left", padx=15)
        ctk.CTkCheckBox(fr, text="R", variable=self.attack_vars["R"]["active"], font=("Arial", 14, "bold"), text_color="white").pack(side="left")
        
        # --- GÖRSEL BUFF SİSTEMİ (SEKMELİ YAPI) ---
        bf = ctk.CTkFrame(self.f_warrior, fg_color="#252525", corner_radius=8, border_width=1, border_color="#555555")
        bf.pack(padx=30, pady=10, fill="both", expand=True)
        
        top_bf = ctk.CTkFrame(bf, fg_color="transparent")
        top_bf.pack(fill="x", pady=(10, 0))
        ctk.CTkLabel(top_bf, text="--- GÖRSEL BUFF SİSTEMİ ---", font=("Arial", 14, "bold"), text_color="#bdc3c7").pack(side="left", padx=10)
        ctk.CTkButton(top_bf, text="BUFF İKONLARI TARAMA ALANINI ÇİZ", command=lambda: self.bar_alani_sec("buff_bar"), fg_color="#8e44ad", text_color="white").pack(side="right", padx=10)

        # Sekme (Tab) Yöneticisi
        buff_tabs = ctk.CTkTabview(bf, fg_color="transparent", height=250)
        buff_tabs.pack(fill="both", expand=True, padx=10, pady=5)
        
        tab_yetenek = buff_tabs.add("Yetenek Buff")
        tab_scroll = buff_tabs.add("Scroll Buff")

        # 1. SEKME: YETENEK BUFFLARI
        scr_yetenek = ctk.CTkScrollableFrame(tab_yetenek, fg_color="transparent")
        scr_yetenek.pack(fill="both", expand=True)
        for b in self.buff_listesi:
            self.buff_ui[b] = {"active": ctk.BooleanVar(), "page_key": ctk.StringVar(value="F1"), "skill_key": ctk.StringVar(value="1")}
            row = ctk.CTkFrame(scr_yetenek, fg_color="#1a1a1a", corner_radius=5, border_width=1, border_color="#333")
            row.pack(fill="x", pady=3, ipady=4, padx=5)
            
            icon_path = os.path.join(self.icons_klasoru, f"{b}.png")
            icon_label = ctk.CTkLabel(row, text="[IMG]", width=35, text_color="#f1c40f")
            if os.path.exists(icon_path):
                try:
                    pil_img = Image.open(icon_path)
                    pil_img.thumbnail((30, 30))
                    ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
                    icon_label.configure(image=ctk_img, text="")
                except: pass
            icon_label.pack(side="left", padx=(10, 5))
            
            ctk.CTkCheckBox(row, text=b, variable=self.buff_ui[b]["active"], width=100, font=("Arial", 12, "bold"), text_color="white").pack(side="left", padx=5)
            ctk.CTkLabel(row, text="Sayfa:", font=("Arial", 11), text_color="#bdc3c7").pack(side="left", padx=(20, 5))
            bp = ctk.CTkButton(row, textvariable=self.buff_ui[b]["page_key"], width=45, height=26, fg_color="#2980b9", text_color="white", font=("Arial", 11, "bold"))
            bp.configure(command=lambda bw=bp, v=self.buff_ui[b]["page_key"]: self.listen_for_key(v, bw)); bp.pack(side="left")
            ctk.CTkLabel(row, text="Tuş:", font=("Arial", 11), text_color="#bdc3c7").pack(side="left", padx=(15, 5))
            bsk = ctk.CTkButton(row, textvariable=self.buff_ui[b]["skill_key"], width=40, height=26, fg_color="#2980b9", text_color="white", font=("Arial", 11, "bold"))
            bsk.configure(command=lambda bw=bsk, v=self.buff_ui[b]["skill_key"]: self.listen_for_key(v, bw)); bsk.pack(side="left")

        # 2. SEKME: SCROLL BUFFLARI
        scr_scroll = ctk.CTkScrollableFrame(tab_scroll, fg_color="transparent")
        scr_scroll.pack(fill="both", expand=True)
        for s in self.scroll_listesi:
            self.scroll_ui[s] = {"active": ctk.BooleanVar(), "page_key": ctk.StringVar(value="F1"), "skill_key": ctk.StringVar(value="1")}
            row = ctk.CTkFrame(scr_scroll, fg_color="#1a1a1a", corner_radius=5, border_width=1, border_color="#333")
            row.pack(fill="x", pady=3, ipady=4, padx=5)
            
            icon_path = os.path.join(self.icons_klasoru, f"{s}.png")
            icon_label = ctk.CTkLabel(row, text="[IMG]", width=35, text_color="#f1c40f")
            if os.path.exists(icon_path):
                try:
                    pil_img = Image.open(icon_path)
                    pil_img.thumbnail((30, 30))
                    ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
                    icon_label.configure(image=ctk_img, text="")
                except: pass
            icon_label.pack(side="left", padx=(10, 5))
            
            # .upper() kullanarak küçük harfli scroll isimlerini arayüzde BÜYÜK gösteriyoruz
            ctk.CTkCheckBox(row, text=s.upper(), variable=self.scroll_ui[s]["active"], width=100, font=("Arial", 12, "bold"), text_color="white").pack(side="left", padx=5)
            ctk.CTkLabel(row, text="Sayfa:", font=("Arial", 11), text_color="#bdc3c7").pack(side="left", padx=(20, 5))
            bp = ctk.CTkButton(row, textvariable=self.scroll_ui[s]["page_key"], width=45, height=26, fg_color="#2980b9", text_color="white", font=("Arial", 11, "bold"))
            bp.configure(command=lambda bw=bp, v=self.scroll_ui[s]["page_key"]: self.listen_for_key(v, bw)); bp.pack(side="left")
            ctk.CTkLabel(row, text="Tuş:", font=("Arial", 11), text_color="#bdc3c7").pack(side="left", padx=(15, 5))
            bsk = ctk.CTkButton(row, textvariable=self.scroll_ui[s]["skill_key"], width=40, height=26, fg_color="#2980b9", text_color="white", font=("Arial", 11, "bold"))
            bsk.configure(command=lambda bw=bsk, v=self.scroll_ui[s]["skill_key"]: self.listen_for_key(v, bw)); bsk.pack(side="left")

        ctk.CTkButton(self.f_warrior, text="💾 TÜM AYARLARI KAYDET", fg_color="#2ecc71", text_color="white", font=("Arial", 14, "bold"), height=40, command=self.save_settings).pack(pady=10, padx=30, fill="x")

    def setup_pot_ui(self):
        ctk.CTkLabel(self.f_pot, text="AKILLI POT YÖNETİMİ", font=("Arial", 22, "bold"), text_color="#3498db").pack(pady=(30, 10))
        pf = ctk.CTkFrame(self.f_pot, fg_color="transparent"); pf.pack(padx=50, pady=20, fill="both", expand=True)
        hb = ctk.CTkFrame(pf, border_width=2, border_color="#e74c3c", fg_color="#252525", corner_radius=8); hb.pack(fill="x", pady=15, ipady=15)
        ctk.CTkCheckBox(hb, text="HP POT AKTİF", variable=self.var_hp_active, font=("Arial", 16, "bold"), text_color="#e74c3c").pack(pady=10)
        hr = ctk.CTkFrame(hb, fg_color="transparent"); hr.pack(pady=5)
        ctk.CTkButton(hr, text="HP BAR ÇİZ", command=lambda: self.bar_alani_sec("hp_bar"), fg_color="#c0392b", text_color="white", font=("Arial", 12, "bold"), width=120).grid(row=0, column=0, padx=15)
        ctk.CTkLabel(hr, text="Sınır %:", text_color="white", font=("Arial", 12)).grid(row=0, column=1, padx=5)
        ctk.CTkEntry(hr, textvariable=self.pot_vars["hp_limit"], width=50, justify="center", text_color="white", fg_color="#333333").grid(row=0, column=2)
        ctk.CTkLabel(hr, text="Tuş:", text_color="white", font=("Arial", 12)).grid(row=0, column=3, padx=10)
        bhp = ctk.CTkButton(hr, textvariable=self.pot_vars["hp_tus"], width=50, fg_color="#2980b9", text_color="white", font=("Arial", 12, "bold"))
        bhp.configure(command=lambda b=bhp, v=self.pot_vars["hp_tus"]: self.listen_for_key(v, b)); bhp.grid(row=0, column=4)
        mb = ctk.CTkFrame(pf, border_width=2, border_color="#3498db", fg_color="#252525", corner_radius=8); mb.pack(fill="x", pady=15, ipady=15)
        ctk.CTkCheckBox(mb, text="MP POT AKTİF", variable=self.var_mp_active, font=("Arial", 16, "bold"), text_color="#3498db").pack(pady=10)
        mr = ctk.CTkFrame(mb, fg_color="transparent"); mr.pack(pady=5)
        ctk.CTkButton(mr, text="MP BAR ÇİZ", command=lambda: self.bar_alani_sec("mp_bar"), fg_color="#2980b9", text_color="white", font=("Arial", 12, "bold"), width=120).grid(row=0, column=0, padx=15)
        ctk.CTkLabel(mr, text="Sınır %:", text_color="white", font=("Arial", 12)).grid(row=0, column=1, padx=5)
        ctk.CTkEntry(mr, textvariable=self.pot_vars["mp_limit"], width=50, justify="center", text_color="white", fg_color="#333333").grid(row=0, column=2)
        ctk.CTkLabel(mr, text="Tuş:", text_color="white", font=("Arial", 12)).grid(row=0, column=3, padx=10)
        bmp = ctk.CTkButton(mr, textvariable=self.pot_vars["mp_tus"], width=50, fg_color="#2980b9", text_color="white", font=("Arial", 12, "bold"))
        bmp.configure(command=lambda b=bmp, v=self.pot_vars["mp_tus"]: self.listen_for_key(v, b)); bmp.grid(row=0, column=4)
        ctk.CTkButton(self.f_pot, text="💾 TÜM AYARLARI KAYDET", fg_color="#2ecc71", text_color="white", font=("Arial", 14, "bold"), height=40, command=self.save_settings).pack(pady=20, fill="x")

    def select_frame(self, name):
        self.btn_yaratik.configure(fg_color="#f1c40f" if name == "yaratik" else "transparent", text_color="black" if name == "yaratik" else "white")
        self.btn_warrior.configure(fg_color="#f1c40f" if name == "warrior" else "transparent", text_color="black" if name == "warrior" else "white")
        self.btn_pot.configure(fg_color="#f1c40f" if name == "pot" else "transparent", text_color="black" if name == "pot" else "white")
        self.f_yaratik.pack_forget(); self.f_warrior.pack_forget(); self.f_pot.pack_forget()
        if name == "yaratik": self.f_yaratik.pack(fill="both", expand=True)
        elif name == "warrior": self.f_warrior.pack(fill="both", expand=True)
        elif name == "pot": self.f_pot.pack(fill="both", expand=True)

    def bar_alani_sec(self, tip): 
        RegionSelector(lambda x, y, w, h: self.alan_kaydet(f"{tip}_alani", x, y, w, h))
        
    def alan_sec(self, no): 
        isim = "tarama_alani" if no == 1 else "tarama_alani_2"
        RegionSelector(lambda x, y, w, h: self.alan_kaydet(isim, x, y, w, h))

    # YENİ: Alan çizildiği an otomatik JSON dosyasına işleyen motor
    def alan_kaydet(self, degisken_adi, x, y, w, h):
        setattr(self, degisken_adi, (int(x), int(y), int(w), int(h)))
        self.save_settings()

    def sec_baslat(self): 
        MagnifierSelector(lambda img, cx, cy: self.sec_bitir(img))
        
    def sec_bitir(self, img):
        if img:
            n = ctk.CTkInputDialog(text="İsim (Örn: yaratik1):", title="PNG Kaydet").get_input()
            if n: 
                img.save(os.path.join(self.yaratik_klasoru, f"{n}.png"))
                self.galeri_tara()
                self.opt_galeri_1.set(f"{n}.png")
                self.gorsel_yukle_1(f"{n}.png")
                self.save_settings() # PNG seçildiği an kaydeder

    def alt_isim_sec_baslat(self): 
        MagnifierSelector(lambda img, cx, cy: self.alt_isim_bitir(img))
        
    def alt_isim_bitir(self, img):
        if img:
            n = ctk.CTkInputDialog(text="İsim (Örn: altisim1):", title="Alt İsim Kaydet").get_input()
            if n: 
                img.save(os.path.join(self.altisim_klasoru, f"{n}.png"))
                self.galeri_tara()
                self.opt_galeri_2.set(f"{n}.png")
                self.gorsel_yukle_2(f"{n}.png")
                self.save_settings() # PNG seçildiği an kaydeder

    def galeri_tara(self):
        yr = [f for f in os.listdir(self.yaratik_klasoru) if f.endswith(".png")]
        self.opt_galeri_1.configure(values=yr if yr else ["Seçiniz..."])
        ar = [f for f in os.listdir(self.altisim_klasoru) if f.endswith(".png")]
        self.opt_galeri_2.configure(values=ar if ar else ["Seçiniz..."])

    def save_settings(self):
        data = {
            "master_allow": self.var_master_allow.get(), 
            "anti_afk_mode": self.var_anti_afk_mode.get(),
            "afk_mesafe": getattr(self, "var_afk_mesafe", ctk.StringVar(value="2")).get(), # Hata korumalı
            "hp_active": self.var_hp_active.get(), 
            "mp_active": self.var_mp_active.get(),
            "always_on_top": self.var_always_on_top.get(), 
            "macro_hotkey": self.macro_hotkey.get(),
            "galeri_1": self.opt_galeri_1.get(), 
            "galeri_2": self.opt_galeri_2.get(),
            "r_ms": self.warrior_r_ms.get(), 
            "skill_ms": self.warrior_skill_ms.get(), 
            "main_atk_page": getattr(self, "main_atk_page", ctk.StringVar(value="F1")).get(),
            "hp_limit": self.pot_vars["hp_limit"].get(), 
            "hp_tus": self.pot_vars["hp_tus"].get(),
            "mp_limit": self.pot_vars["mp_limit"].get(), 
            "mp_tus": self.pot_vars["mp_tus"].get(),
            "attacks": {k: {"active": v["active"].get(), "key": v["key"].get()} for k, v in self.attack_vars.items()},
            "buffs": {k: {"active": v["active"].get(), "page_key": v["page_key"].get(), "skill_key": v["skill_key"].get()} for k, v in self.buff_ui.items()},
            "scrolls": {k: {"active": v["active"].get(), "page_key": v["page_key"].get(),
            "skill_key": v["skill_key"].get()} for k, v in self.scroll_ui.items()},                
            "coords": {
                "tarama_alani": getattr(self, 'tarama_alani', None), 
                "tarama_alani_2": getattr(self, 'tarama_alani_2', None), 
                "hp_bar_alani": getattr(self, 'hp_bar_alani', None), 
                "mp_bar_alani": getattr(self, 'mp_bar_alani', None), 
                "buff_bar_alani": getattr(self, 'buff_bar_alani', None)
                
            }
        }
        try:
            with open(self.settings_file, "w") as f: json.dump(data, f)
        except: pass

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f: data = json.load(f)
                if "master_allow" in data: self.var_master_allow.set(data["master_allow"])
                if "anti_afk_mode" in data: self.var_anti_afk_mode.set(data["anti_afk_mode"])
                if "afk_mesafe" in data: getattr(self, "var_afk_mesafe", ctk.StringVar()).set(data["afk_mesafe"])
                if "hp_active" in data: self.var_hp_active.set(data["hp_active"])
                if "mp_active" in data: self.var_mp_active.set(data["mp_active"])
                if "macro_hotkey" in data: self.macro_hotkey.set(data["macro_hotkey"])
                if "always_on_top" in data: self.var_always_on_top.set(data["always_on_top"]); self.toggle_always_on_top()
                if "galeri_1" in data and data["galeri_1"] != "Seçiniz...": self.opt_galeri_1.set(data["galeri_1"]); self.gorsel_yukle_1(data["galeri_1"])
                if "galeri_2" in data and data["galeri_2"] != "Seçiniz...": self.opt_galeri_2.set(data["galeri_2"]); self.gorsel_yukle_2(data["galeri_2"])
                if "r_ms" in data: self.warrior_r_ms.set(data["r_ms"])
                if "skill_ms" in data: self.warrior_skill_ms.set(data["skill_ms"])
                if "main_atk_page" in data: getattr(self, "main_atk_page", ctk.StringVar()).set(data["main_atk_page"])
                if "hp_limit" in data: self.pot_vars["hp_limit"].set(data["hp_limit"])
                if "hp_tus" in data: self.pot_vars["hp_tus"].set(data["hp_tus"])
                if "mp_limit" in data: self.pot_vars["mp_limit"].set(data["mp_limit"])
                if "mp_tus" in data: self.pot_vars["mp_tus"].set(data["mp_tus"])
                if "attacks" in data:
                    for k, v in data["attacks"].items():
                        if k in self.attack_vars: self.attack_vars[k]["active"].set(v["active"]); self.attack_vars[k]["key"].set(v["key"])
                if "buffs" in data:
                    for k, v in data["buffs"].items():
                        if k in self.buff_ui: self.buff_ui[k]["active"].set(v["active"]); self.buff_ui[k]["page_key"].set(v["page_key"]); self.buff_ui[k]["skill_key"].set(v["skill_key"])
                if "scrolls" in data:
                    for k, v in data["scrolls"].items():
                        if k in self.scroll_ui: 
                            self.scroll_ui[k]["active"].set(v["active"])
                            self.scroll_ui[k]["page_key"].set(v["page_key"])
                            self.scroll_ui[k]["skill_key"].set(v["skill_key"])
                if "coords" in data:
                    c = data["coords"]
                    self.tarama_alani = c.get("tarama_alani")
                    self.tarama_alani_2 = c.get("tarama_alani_2")
                    self.hp_bar_alani = c.get("hp_bar_alani")
                    self.mp_bar_alani = c.get("mp_bar_alani")
                    self.buff_bar_alani = c.get("buff_bar_alani")
            except: pass

class MagnifierSelector:
    def __init__(self, callback, cancel_callback=None):
        self.callback = callback; self.cancel_callback = cancel_callback 
        self.root = ctk.CTkToplevel()
        with mss.mss() as sct:
            monitor_all = sct.monitors[0]
            img = sct.grab(monitor_all)
        self.orig = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
        self.offset_x, self.offset_y = monitor_all['left'], monitor_all['top']
        self.root.geometry(f"{monitor_all['width']}x{monitor_all['height']}+{self.offset_x}+{self.offset_y}")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True); self.root.focus_force(); self.root.config(cursor="cross")
        self.tk_orig = ImageTk.PhotoImage(self.orig)
        self.c = ctk.CTkCanvas(self.root, highlightthickness=0); self.c.pack(fill="both", expand=True)
        self.c.create_image(0, 0, image=self.tk_orig, anchor="nw")
        self.c.bind("<Button-1>", self.zoom_stage); self.root.bind("<Escape>", self.cancel_zoom) 

    def cancel_zoom(self, e=None):
        self.root.destroy()
        if self.cancel_callback: self.cancel_callback() 

    def zoom_stage(self, e):
        zx, zy = e.x, e.y; sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        crop_w, crop_h = sw // 3, sh // 3
        x1, y1 = max(0, zx - crop_w // 2), max(0, zy - crop_h // 2)
        x2, y2 = min(self.orig.width, x1 + crop_w), min(self.orig.height, y1 + crop_h)
        self.crop_x1, self.crop_y1 = x1, y1; self.scale_x, self.scale_y = sw / (x2 - x1), sh / (y2 - y1)
        self.zoomed_img = self.orig.crop((x1, y1, x2, y2)).resize((sw, sh), Image.Resampling.LANCZOS)
        self.tk_zoom = ImageTk.PhotoImage(self.zoomed_img)
        self.c.delete("all"); self.c.create_image(0, 0, image=self.tk_zoom, anchor="nw")
        self.c.bind("<Button-1>", self.bs); self.c.bind("<B1-Motion>", self.bm); self.c.bind("<ButtonRelease-1>", self.be)

    def bs(self, e): 
        self.bx, self.by = e.x, e.y; self.rect = self.c.create_rectangle(e.x, e.y, e.x, e.y, outline="#39FF14", width=3)
    def bm(self, e): 
        if hasattr(self, 'rect'): self.c.coords(self.rect, self.bx, self.by, e.x, e.y)
    def be(self, e): 
        if hasattr(self, 'rect'):
            zx1, zy1 = min(self.bx, e.x), min(self.by, e.y); zx2, zy2 = max(self.bx, e.x), max(self.by, e.y)
            orig_x1 = self.crop_x1 + int(zx1 / self.scale_x); orig_y1 = self.crop_y1 + int(zy1 / self.scale_y)
            orig_x2 = self.crop_x1 + int(zx2 / self.scale_x); orig_y2 = self.crop_y1 + int(zy2 / self.scale_y)
            if abs(orig_x2 - orig_x1) > 2:
                final_crop = self.orig.crop((orig_x1, orig_y1, orig_x2, orig_y2))
                cx = self.offset_x + orig_x1 + (orig_x2 - orig_x1) // 2; cy = self.offset_y + orig_y1 + (orig_y2 - orig_y1) // 2
                self.root.destroy(); self.callback(final_crop, cx, cy)
            else: self.cancel_zoom()

class RegionSelector:
    def __init__(self, callback, cancel_callback=None):
        self.callback = callback; self.cancel_callback = cancel_callback
        self.root = ctk.CTkToplevel()
        with mss.mss() as sct: monitor_all = sct.monitors[0]
        self.offset_x = monitor_all['left']; self.offset_y = monitor_all['top']
        self.root.geometry(f"{monitor_all['width']}x{monitor_all['height']}+{self.offset_x}+{self.offset_y}")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True, "-alpha", 0.3); self.root.config(cursor="cross")
        self.c = ctk.CTkCanvas(self.root, bg="black", highlightthickness=0); self.c.pack(fill="both", expand=True)
        self.c.bind("<Button-1>", self.on_press); self.c.bind("<B1-Motion>", self.on_drag); self.c.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Escape>", lambda e: self.cancel())

    def on_press(self, e):
        self.start_x, self.start_y = e.x, e.y
        self.rect = self.c.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="#39FF14", width=3)
    def on_drag(self, e): self.c.coords(self.rect, self.start_x, self.start_y, e.x, e.y)
    def on_release(self, e):
        x1, y1 = min(self.start_x, e.x), min(self.start_y, e.y); x2, y2 = max(self.start_x, e.x), max(self.start_y, e.y)
        self.root.destroy()
        if x2 - x1 > 10 and y2 - y1 > 10: self.callback(x1 + self.offset_x, y1 + self.offset_y, x2 - x1, y2 - y1)
        elif self.cancel_callback: self.cancel_callback()
    def cancel(self):
        self.root.destroy()
        if self.cancel_callback: self.cancel_callback() 

if __name__ == "__main__":
    app = MacroApp(); app.mainloop()