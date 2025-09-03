import os
import sys
import shutil
import tempfile
import zipfile
import urllib.request
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional

def log(msg):
    print(msg, flush=True)
    with open("update_log.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

class UpdaterGUI:
    def __init__(self, exe_atual: str, versao_atual: str, versao_nova: str, url_download: str):
        self.exe_atual = exe_atual
        self.versao_atual = versao_atual
        self.versao_nova = versao_nova
        self.url_download = url_download
        self.temp_dir = tempfile.mkdtemp()

        log(f"Temp dir criada: {self.temp_dir}")

        self.root = tk.Tk()
        self.root.title("Atualizando Controle Financeiro")
        self.root.geometry("600x400")

        self.label_status = ttk.Label(
            self.root,
            text=f"Atualizando da versão {versao_atual} para {versao_nova}...",
            font=("Segoe UI", 12)
        )
        self.label_status.pack(pady=10)

        self.text_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, height=15, width=70, state="disabled")
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.progress = ttk.Progressbar(self.root, mode="indeterminate")
        self.progress.pack(fill="x", padx=10, pady=10)
        self.progress.start(10)

    def escrever_log(self, mensagem: str):
        log(mensagem)
        self.text_area.configure(state="normal")
        self.text_area.insert(tk.END, mensagem + "\n")
        self.text_area.configure(state="disabled")
        self.text_area.see(tk.END)
        self.root.update()

    def baixar_arquivo(self, url: str, destino: str):
        self.escrever_log(f"Baixando atualização de {url}...")
        try:
            urllib.request.urlretrieve(url, destino)
            self.escrever_log("Download concluído.")
        except Exception as e:
            self.escrever_log(f"[ERRO] Falha ao baixar arquivo: {e}")
            raise

    def atualizar_app(self):
        try:
            zip_path = os.path.join(self.temp_dir, "update.zip")
            self.baixar_arquivo(self.url_download, zip_path)

            self.escrever_log("Extraindo arquivos...")
            try:
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(self.temp_dir)
                self.escrever_log("Extração concluída.")
            except Exception as e:
                self.escrever_log(f"[ERRO] Falha ao extrair zip: {e}")
                raise

            self.escrever_log("Substituindo arquivos do aplicativo...")
            exe_dir = os.path.dirname(self.exe_atual)
            for item in os.listdir(self.temp_dir):
                if item == "update.zip":
                    continue
                s = os.path.join(self.temp_dir, item)
                d = os.path.join(exe_dir, item)
                try:
                    if os.path.isdir(s):
                        if os.path.exists(d):
                            shutil.rmtree(d)
                        shutil.copytree(s, d)
                    else:
                        shutil.copy2(s, d)
                    self.escrever_log(f"Substituído: {item}")
                except Exception as e:
                    self.escrever_log(f"[ERRO] Falha ao copiar {item}: {e}")
                    raise

            self.escrever_log("Atualização concluída com sucesso!")

            exe_novo = self._encontrar_executavel(exe_dir)
            if exe_novo:
                self.escrever_log(f"Iniciando nova versão: {exe_novo}")
                os.startfile(exe_novo)
            else:
                self.escrever_log("Executável atualizado não encontrado!")

            self.root.after(2000, self.root.destroy)

        except Exception as e:
            self.escrever_log(f"[ERRO FATAL] {e}")
            messagebox.showerror("Erro", f"Falha na atualização: {e}")

    def _encontrar_executavel(self, pasta: str) -> Optional[str]:
        for item in os.listdir(pasta):
            if item.lower().endswith(".exe") and "controle" in item.lower():
                return os.path.join(pasta, item)
        return None

def main():
    print("=== Updater iniciado ===", flush=True)
    print(f"Argumentos recebidos: {sys.argv}", flush=True)
    with open("update_log.txt", "a", encoding="utf-8") as f:
        f.write("=== Updater iniciado ===\n")
        f.write(f"Argumentos recebidos: {sys.argv}\n")

    if len(sys.argv) < 5:
        print("[ERRO] Updater chamado incorretamente!", flush=True)
        messagebox.showerror(
            "Erro",
            f"Updater chamado incorretamente.\nArgs recebidos: {sys.argv}\n"
            "Uso: updater.py <exe_atual> <versao_atual> <versao_nova> <url_download>"
        )
        sys.exit(1)

    exe_atual = sys.argv[1]
    versao_atual = sys.argv[2]
    versao_nova = sys.argv[3]
    url_download = sys.argv[4]

    updater_gui = UpdaterGUI(exe_atual, versao_atual, versao_nova, url_download)
    updater_gui.escrever_log(f"Argumentos recebidos: {sys.argv}")

    threading.Thread(target=updater_gui.atualizar_app, daemon=True).start()
    updater_gui.root.mainloop()

if __name__ == "__main__":
    main()
