"""Bionic Windows launcher. Requires Docker Desktop with Linux containers."""
import os,subprocess,sys,tempfile,time,urllib.request,zipfile,webbrowser
from pathlib import Path
from tkinter import Tk,messagebox
REPO="https://github.com/Kaktus2889/Bionic/archive/refs/heads/main.zip"
def alert(title,message):
    root=Tk();root.withdraw();messagebox.showinfo(title,message);root.destroy()
def run():
    if not shutil.which("docker"):
        alert("Bionic","Zainstaluj Docker Desktop, uruchom go i spróbuj ponownie.\nhttps://www.docker.com/products/docker-desktop/");return
    home=Path(os.environ.get("LOCALAPPDATA",str(Path.home())))/"Bionic";home.mkdir(parents=True,exist_ok=True)
    target=home/"Bionic-main"
    if not (target/"docker-compose.yml").exists():
        archive=home/"source.zip"
        urllib.request.urlretrieve(REPO,archive)
        with zipfile.ZipFile(archive) as z:
            for member in z.infolist():
                dest=(home/member.filename).resolve()
                if not dest.is_relative_to(home.resolve()):raise ValueError("Unsafe archive path")
            z.extractall(home)
        archive.unlink(missing_ok=True)
    subprocess.run(["docker","info"],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=25)
    subprocess.run(["docker","compose","up","-d","--build"],cwd=target,check=True,timeout=1200)
    webbrowser.open("http://localhost:3000")
    alert("Bionic","Bionic uruchomiony. Dashboard: http://localhost:3000\nAby zatrzymać: docker compose down w folderze "+str(target))
if __name__=="__main__":
    import shutil
    try:run()
    except Exception as exc:alert("Bionic — błąd",str(exc))
