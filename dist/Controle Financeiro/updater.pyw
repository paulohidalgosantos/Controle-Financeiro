import os
import sys
import time
import threading
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
import requests


def atualizar_app():
    try:
        GITHUB_LATEST_RELEASE = "https://api.github.com/repos/paulohidalgosantos/Controle-Financeiro/releases/latest"
        status_label.config(text="Verificando versão...")
        app.update_idletasks()

        # Obter info da última release
        r = requests.get(GITHUB_LATEST_RELEASE)
        r.raise_for_status()
        release_info = r.json()
        assets = release_info.get("assets", [])
        if not assets:
            raise Exception("Nenhum asset encontrado na release.")

        # Procurar arquivo do app (exe)
        exe_asset = None
        for a in assets:
            if a["name"].endswith(".exe"):
                exe_asset = a
                break
        if not exe_asset:
            raise Exception("Arquivo .exe da release não encontrado.")

        download_url = exe_asset["browser_download_url"]
        temp_dir = os.path.join(os.path.dirname(sys.executable), "temp_update")
        os.makedirs(temp_dir, exist_ok=True)
        temp_file = os.path.join(temp_dir, exe_asset["name"])

        # Download com barra de progresso
        status_label.config(text="Baixando atualização...")
        app.update_idletasks()
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            chunk_size = 8192
            with open(temp_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        perc = int(downloaded / total_size * 100)
                        progress_bar['value'] = perc
                        app.update_idletasks()

        time.sleep(0.2)
        status_label.config(text="Substituindo app antigo...")
        app.update_idletasks()
        time.sleep(0.3)

        # Substituir app antigo automaticamente, mesmo se o usuário renomeou o exe
        exe_atual = sys.executable
        backup_path = exe_atual + ".backup"
        if os.path.exists(exe_atual):
            if os.path.exists(backup_path):
                os.remove(backup_path)
            shutil.move(exe_atual, backup_path)
        shutil.move(temp_file, exe_atual)

        # Limpar pasta temporária
        shutil.rmtree(temp_dir, ignore_errors=True)

        status_label.config(text="Atualização concluída!")
        progress_bar['value'] = 100
        app.update_idletasks()
        time.sleep(0.5)

        # Abrir app atualizado
        os.startfile(exe_atual)
        app.destroy()

    except Exception as e:
        messagebox.showerror("Erro na atualização", str(e))
        app.destroy()


# Criar janela de atualização
app = tk.Tk()
app.title("Atualizando Controle Financeiro")
app.geometry("400x120")
app.resizable(False, False)

lbl = tk.Label(app, text="Atualizando o aplicativo...", font=("Inter", 12))
lbl.pack(pady=(10, 5))

progress_bar = ttk.Progressbar(
    app, orient="horizontal", length=350, mode="determinate")
progress_bar.pack(pady=5)

status_label = tk.Label(app, text="Iniciando...", font=("Inter", 10))
status_label.pack(pady=(5, 10))

# Rodar atualização em thread separada para não travar a UI
threading.Thread(target=atualizar_app, daemon=True).start()

app.mainloop()
