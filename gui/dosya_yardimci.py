# gui/dosya_yardimci.py
import os
import platform
import subprocess
from pathlib import Path


def _varsayilan_klasor() -> str:
    varsayilan = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
    os.makedirs(varsayilan, exist_ok=True)
    return varsayilan


def alim_klasoru_getir(db, alim_id) -> str:
    alim = db.alim_getir(alim_id) if alim_id else None
    if alim and alim.dosya_klasoru and os.path.isdir(alim.dosya_klasoru):
        return alim.dosya_klasoru

    try:
        db_path = getattr(getattr(db, 'db', None), 'db_path', None)
        if db_path:
            db_klasoru = Path(db_path).resolve().parent
            if db_klasoru.is_dir() and db_klasoru.name != 'dogrudan_temin':
                return str(db_klasoru)
    except Exception:
        pass
    return _varsayilan_klasor()


def klasoru_ac(klasor: str):
    if platform.system() == 'Windows':
        os.startfile(klasor)
    elif platform.system() == 'Darwin':
        subprocess.run(['open', klasor])
    else:
        subprocess.run(['xdg-open', klasor])


def dosyayi_ac(dosya_yolu: str):
    if platform.system() == 'Windows':
        os.startfile(dosya_yolu)
    elif platform.system() == 'Darwin':
        subprocess.run(['open', dosya_yolu])
    else:
        subprocess.run(['xdg-open', dosya_yolu])