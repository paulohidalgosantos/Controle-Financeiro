import os
import sys
import shutil
import urllib.request
import zipfile
import tempfile
import subprocess
import tkinter as tk
from tkinter import messagebox
import time
import traceback

# ---------------- CONFIGURAÇÕES ----------------
# URL do zip contendo a atualização
URL_ATUALIZACAO = "https://seu-servidor.com/ControleFinanceiro.zip"


def log(msg, log_path):
    """Registra mensagens no log com timestamp"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")


def main():
    # Inicializa interface Tkinter mínima
    root = tk.Tk()
    root.withdraw()

    # Verifica parâmetros
    if len(sys.argv) < 3:
        messagebox.showerror("Erro", "Updater chamado de forma incorreta.")
        return

    exe_atual = sys.argv[1]   # caminho completo do exe original
    versao_local = sys.argv[2]

    pasta_app = os.path.dirname(exe_atual)
    nome_exe = os.path.basename(exe_atual)

    # Cria pasta temporária e log
    pasta_temp = tempfile.mkdtemp(prefix="CF_Update_")
    log_path = os.path.join(pasta_temp, "update_log.txt")
    log(f"Iniciando atualização do {nome_exe} versão {versao_local}", log_path)

    try:
        # Baixa atualização
        zip_path = os.path.join(pasta_temp, "update.zip")
        log(f"Baixando atualização de {URL_ATUALIZACAO}", log_path)
        urllib.request.urlretrieve(URL_ATUALIZACAO, zip_path)
        log("Download concluído", log_path)

        # Extrai atualização
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(pasta_temp)
        log(f"Arquivo extraído em {pasta_temp}", log_path)

        # Procura novo exe
        novo_exe = None
        for root_dir, _, files in os.walk(pasta_temp):
            for f in files:
                if f.endswith(".exe"):
                    novo_exe = os.path.join(root_dir, f)
                    log(f"Novo executável encontrado: {novo_exe}", log_path)
                    break
            if novo_exe:
                break

        if not novo_exe:
            log("Nenhum executável encontrado na atualização.", log_path)
            messagebox.showerror(
                "Erro", "Nenhum executável encontrado na atualização.")
            return

        destino = os.path.join(pasta_app, nome_exe)
        backup = destino + ".old"

        # Espera até que o exe antigo seja liberado
        log(f"Tentando substituir {destino}", log_path)
        for i in range(10):
            try:
                os.rename(destino, backup)
                log(f"Backup criado: {backup}", log_path)
                break
            except PermissionError:
                log(f"Tentativa {i+1}/10 falhou, arquivo em uso", log_path)
                time.sleep(1)
        else:
            log("Não foi possível substituir o aplicativo (arquivo em uso).", log_path)
            messagebox.showerror(
                "Erro", "Não foi possível substituir o aplicativo (arquivo em uso).")
            return

        # Copia novo exe
        shutil.copy2(novo_exe, destino)
        log(f"Novo executável copiado para {destino}", log_path)

        # Remove backup
        try:
            os.remove(backup)
            log(f"Backup removido: {backup}", log_path)
        except Exception as e:
            log(f"Falha ao remover backup: {e}", log_path)

        log("Atualização concluída com sucesso!", log_path)
        messagebox.showinfo(
            "Atualização", "Aplicativo atualizado com sucesso!")

        # Relança app atualizado
        subprocess.Popen([destino], cwd=pasta_app)
        log(f"Aplicativo relançado: {destino}", log_path)

    except Exception as e:
        log(f"ERRO na atualização: {e}", log_path)
        log(traceback.format_exc(), log_path)
        messagebox.showerror("Erro na atualização", str(e))

    finally:
        log("Finalizando updater", log_path)
        # Não remove a pasta temporária para permitir ver o log
        # shutil.rmtree(pasta_temp, ignore_errors=True)


if __name__ == "__main__":
    main()
