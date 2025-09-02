import os
import sys
import time
import shutil
import zipfile
import tempfile
import urllib.request
import subprocess
import tkinter as tk
from tkinter import messagebox

# -------------------------
# Configurações
# -------------------------
REPO_RELEASE = "https://github.com/paulohidalgosantos/Controle-Financeiro/releases/latest/download/app.zip"

# Pasta temporária para update
TEMP_DIR = tempfile.mkdtemp(prefix="controle_financeiro_update_")
LOG_FILE = os.path.join(TEMP_DIR, "update_log.txt")


def log(msg):
    """Grava mensagens no log e exibe no console"""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(msg)


def baixar_zip(destino_zip):
    log("Iniciando download do pacote de atualização...")
    try:
        urllib.request.urlretrieve(REPO_RELEASE, destino_zip)
        log(f"Download concluído: {destino_zip}")
    except Exception as e:
        log(f"ERRO no download: {e}")
        messagebox.showerror("Erro", f"Falha no download da atualização:\n{e}")
        sys.exit(1)


def extrair_zip(arquivo_zip, destino):
    log(f"Extraindo {arquivo_zip} para {destino} ...")
    try:
        with zipfile.ZipFile(arquivo_zip, "r") as zip_ref:
            zip_ref.extractall(destino)
        log("Extração concluída.")
    except Exception as e:
        log(f"ERRO na extração: {e}")
        messagebox.showerror("Erro", f"Falha na extração do pacote:\n{e}")
        sys.exit(1)


def substituir_app(app_antigo, pasta_nova):
    log(f"Substituindo aplicativo antigo: {app_antigo}")
    try:
        # Remove antigo
        if os.path.exists(app_antigo):
            os.remove(app_antigo)
            log("Aplicativo antigo removido.")
        else:
            log("Aviso: aplicativo antigo não encontrado (será apenas copiado).")

        # Copia novo
        nome_exe = os.path.basename(app_antigo)
        novo_exe = os.path.join(pasta_nova, nome_exe)

        if not os.path.exists(novo_exe):
            log(f"ERRO: não encontrei {novo_exe} no pacote baixado.")
            messagebox.showerror(
                "Erro", "Novo executável não encontrado no pacote.")
            sys.exit(1)

        shutil.copy2(novo_exe, app_antigo)
        log("Novo aplicativo copiado com sucesso.")
    except Exception as e:
        log(f"ERRO na substituição: {e}")
        messagebox.showerror("Erro", f"Falha ao substituir o aplicativo:\n{e}")
        sys.exit(1)


def relancar(app_antigo):
    log(f"Relançando o aplicativo atualizado: {app_antigo}")
    try:
        subprocess.Popen([app_antigo], shell=True)
        log("Aplicativo atualizado relançado com sucesso.")
        messagebox.showinfo(
            "Atualização", "Aplicativo atualizado com sucesso!")
        sys.exit(0)
    except Exception as e:
        log(f"ERRO ao relançar: {e}")
        messagebox.showerror("Erro", f"Falha ao relançar o aplicativo:\n{e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        messagebox.showerror("Erro", "Caminho do aplicativo não informado.")
        return

    app_antigo = sys.argv[1]
    log("=== Início da atualização ===")
    log(f"App antigo: {app_antigo}")

    destino_zip = os.path.join(TEMP_DIR, "update.zip")
    pasta_extraida = os.path.join(TEMP_DIR, "nova_versao")

    baixar_zip(destino_zip)
    extrair_zip(destino_zip, pasta_extraida)
    substituir_app(app_antigo, pasta_extraida)
    relancar(app_antigo)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    main()
