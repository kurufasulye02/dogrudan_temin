# main.py
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from gui.ana_pencere import AnaPencere
from utils.ui_helpers import setup_logging
from utils.guncelleme_kontrol import guncelleme_kontrol_et # YENİ EKLENDİ
import sys
import traceback
import os

from versiyon import VERSIYON

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def global_exception_handler(exc_type, exc_value, exc_traceback):
    err_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    import logging
    logging.error("Yakalanmayan Hata:\n" + err_msg)
    
    Messagebox.show_error(
        title="Beklenmeyen Bir Hata Oluştu",
        message=f"Sistemde bir hata oluştu. Hata detayları 'logs' klasörüne kaydedildi.\n\nHata: {exc_value}",
    )

if __name__ == "__main__":
    setup_logging()
    sys.excepthook = global_exception_handler
    
    root = ttk.Window(themename="flatly")
    root.title(f"🏫 DOĞRUDAN TEMİN MODÜLÜ - {VERSIYON}")
    
    try:
        icon_yolu = resource_path("logo.ico")
        if os.path.exists(icon_yolu):
            root.iconbitmap(icon_yolu)
    except Exception as e:
        print(f"İkon yüklenemedi: {e}")
        
    app = AnaPencere(root)
    
    # YENİ: Program açıldıktan 2 saniye sonra arka planda güncellemeyi kontrol et
    root.after(2000, guncelleme_kontrol_et)
    
    root.mainloop()