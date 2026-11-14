# utils/guncelleme_kontrol.py
import requests
import webbrowser
from tkinter import messagebox
from versiyon import VERSIYON

# GitHub kullanıcı adın ve repo adın
GITHUB_USER = "kullanici_adin"
GITHUB_REPO = "dogrudan-temin"

def guncelleme_kontrol_et():
    """GitHub'daki en son sürümü kontrol eder."""
    try:
        # GitHub API'sine istek at (Rate limit'e takılmamak için 'latest' redirect'i kullanılabilir ama en garantisi API'dir)
        url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
        response = requests.get(url, timeout=5)
        
        if response.status_code != 200:
            return # Repo henüz yayında değilse veya internet yoksa sessizce geç

        data = response.json()
        son_surum = data.get("tag_name", "").replace("v", "").strip()
        mevcut_surum = VERSIYON.replace("v", "").strip()

        # Basit string karşılaştırması (Versiyonlar 4.0.0 gibi olduğu için yeterli)
        if son_surum and son_surum != mevcut_surum:
            # Yeni sürüm var!
            indirme_linki = data.get("html_url")
            
            cevap = messagebox.askyesno(
                "🚀 Yeni Güncelleme Mevcut!",
                f"Yeni bir sürüm yayınlandı!\n\n"
                f"Mevcut Sürüm: {mevcut_surum}\n"
                f"Yeni Sürüm: {son_surum}\n\n"
                f"İndirme sayfasına gitmek ister misiniz?"
            )
            if cevap:
                webbrowser.open(indirme_linki)
                
    except Exception as e:
        # İnternet yoksa veya başka bir hata olursa programı kesme, sadece logla
        print(f"Güncelleme kontrolü başarısız: {e}")