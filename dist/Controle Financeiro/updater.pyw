import os
import sys
import shutil
import urllib.request
import zipfile
import tempfile
import subprocess
import tkinter as tk
from tkinter import messagebox

# ---------------- CONFIGURAÇÕES ----------------
# link do zip contendo apenas o novo exe
URL_ATUALIZACAO = "https://seu-servidor.com/ControleFinanceiro.zip"
VERSAO_ATUAL = "1.1.1"  # será lido do app principal e passado como argumento


def main():
    if len(sys.argv) < 3:
        messagebox.showerror("Erro", "Updater chamado de forma incorreta.")
        return

    # caminho completo do exe atual (renomeado ou não)
    exe_atual = sys.argv[1]
    versao_local = sys.argv[2]

    pasta_app = os.path.dirname(exe_atual)
    nome_exe = os.path.basename(exe_atual)

    # Cria pasta temporária
    pasta_temp = tempfile.mkdtemp(prefix="CF_Update_")

    try:
        # Baixa atualização
        zip_path = os.path.join(pasta_temp, "update.zip")
        urllib.request.urlretrieve(URL_ATUALIZACAO, zip_path)

        # Extrai
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(pasta_temp)

        # Procura novo exe dentro do zip
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

        # Substitui exe antigo
        shutil.copy2(novo_exe, destino)

        # Mensagem de sucesso
        messagebox.showinfo(
            "Atualização", "Aplicativo atualizado com sucesso!")

        # Relança app atualizado
        subprocess.Popen([destino], cwd=pasta_app)

    except Exception as e:
        messagebox.showerror("Erro na atualização", str(e))

    finally:
        # Limpa pasta temporária
        try:
            shutil.rmtree(pasta_temp, ignore_errors=True)
        except:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    main()
