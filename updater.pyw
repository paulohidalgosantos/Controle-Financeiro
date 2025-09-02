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

# ---------------- CONFIGURAÇÕES ----------------
URL_ATUALIZACAO = "https://seu-servidor.com/ControleFinanceiro.zip"


def main():
    if len(sys.argv) < 3:
        messagebox.showerror("Erro", "Updater chamado de forma incorreta.")
        return

    exe_atual = sys.argv[1]   # caminho completo do exe original
    versao_local = sys.argv[2]

    pasta_app = os.path.dirname(exe_atual)
    nome_exe = os.path.basename(exe_atual)

    pasta_temp = tempfile.mkdtemp(prefix="CF_Update_")

    try:
        # Baixa atualização
        zip_path = os.path.join(pasta_temp, "update.zip")
        urllib.request.urlretrieve(URL_ATUALIZACAO, zip_path)

        # Extrai
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(pasta_temp)

        # Procura novo exe
        novo_exe = None
        for root, _, files in os.walk(pasta_temp):
            for f in files:
                if f.endswith(".exe"):
                    novo_exe = os.path.join(root, f)
                    break

        if not novo_exe:
            messagebox.showerror(
                "Erro", "Nenhum executável encontrado na atualização.")
            return

        destino = os.path.join(pasta_app, nome_exe)
        backup = destino + ".old"

        # Espera até que o exe antigo seja liberado
        for _ in range(30):
            try:
                os.rename(destino, backup)
                break
            except PermissionError:
                time.sleep(1)
        else:
            messagebox.showerror(
                "Erro", "Não foi possível substituir o aplicativo (arquivo em uso).")
            return

        # Copia novo exe para o destino
        shutil.copy2(novo_exe, destino)

        # Remove backup
        try:
            os.remove(backup)
        except:
            pass

        messagebox.showinfo(
            "Atualização", "Aplicativo atualizado com sucesso!")

        # Relança app atualizado
        subprocess.Popen([destino], cwd=pasta_app)

    except Exception as e:
        messagebox.showerror("Erro na atualização", str(e))

    finally:
        shutil.rmtree(pasta_temp, ignore_errors=True)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    main()
