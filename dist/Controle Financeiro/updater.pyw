import os
import sys
import shutil
import urllib.request
import zipfile
import tempfile
import subprocess
import tkinter as tk
from tkinter import scrolledtext, messagebox
import time
import threading

# ---------------- CONFIGURAÇÕES ----------------
URL_ATUALIZACAO = "https://seu-servidor.com/ControleFinanceiro.zip"
LOG_FILE = "update_log.txt"

# ---------------- FUNÇÕES ----------------


def escrever_log(msg):
    """Escreve mensagem no Text e no arquivo de log."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{timestamp}] {msg}"
    print(linha)
    try:
        text_area.config(state='normal')
        text_area.insert(tk.END, linha + "\n")
        text_area.see(tk.END)
        text_area.update_idletasks()
    except:
        pass  # antes da janela pronta
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def atualizar_app(exe_atual):
    pasta_app = os.path.dirname(exe_atual)
    nome_exe = os.path.basename(exe_atual)
    pasta_temp = tempfile.mkdtemp(prefix="CF_Update_")

    try:
        escrever_log("Iniciando atualização...")

        zip_path = os.path.join(pasta_temp, "update.zip")
        escrever_log(f"Baixando atualização de {URL_ATUALIZACAO} ...")
        urllib.request.urlretrieve(URL_ATUALIZACAO, zip_path)
        escrever_log("Download concluído.")

        escrever_log("Extraindo arquivos...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(pasta_temp)
        escrever_log("Extração concluída.")

        # Procura novo exe
        novo_exe = None
        for root, _, files in os.walk(pasta_temp):
            for f in files:
                if f.endswith(".exe"):
                    novo_exe = os.path.join(root, f)
                    break
        if not novo_exe:
            escrever_log("Erro: nenhum executável encontrado na atualização.")
            messagebox.showerror(
                "Erro", "Nenhum executável encontrado na atualização.")
            return

        destino = os.path.join(pasta_app, nome_exe)
        backup = destino + ".old"

        # Espera até que o exe antigo seja liberado
        escrever_log("Substituindo aplicativo antigo...")
        for i in range(10):
            try:
                os.rename(destino, backup)
                escrever_log("Backup do antigo criado.")
                break
            except PermissionError:
                escrever_log("Arquivo em uso, aguardando...")
                time.sleep(1)
        else:
            escrever_log(
                "Erro: não foi possível substituir o aplicativo (arquivo em uso).")
            messagebox.showerror(
                "Erro", "Não foi possível substituir o aplicativo (arquivo em uso).")
            return

        # Copia novo exe
        shutil.copy2(novo_exe, destino)
        escrever_log("Novo aplicativo copiado com sucesso.")

        # Remove backup
        try:
            os.remove(backup)
            escrever_log("Backup antigo removido.")
        except:
            escrever_log("Não foi possível remover backup antigo.")

        escrever_log("Atualização concluída!")
        messagebox.showinfo(
            "Atualização", "Aplicativo atualizado com sucesso!")

        # Relança app atualizado
        subprocess.Popen([destino], cwd=pasta_app)
        root.destroy()

    except Exception as e:
        escrever_log(f"Erro na atualização: {e}")
        messagebox.showerror("Erro na atualização", str(e))
    finally:
        shutil.rmtree(pasta_temp, ignore_errors=True)


# ---------------- INTERFACE ----------------
root = tk.Tk()
root.title("Atualizando Controle Financeiro")
root.geometry("500x300")
root.resizable(False, False)

text_area = scrolledtext.ScrolledText(root, state='normal', wrap=tk.WORD)
text_area.pack(expand=True, fill='both', padx=10, pady=10)

# ---------------- INÍCIO ----------------
if len(sys.argv) < 2:
    messagebox.showerror("Erro", "Updater chamado de forma incorreta.")
    root.destroy()
else:
    exe_atual = sys.argv[1]  # caminho completo do exe original
    threading.Thread(target=atualizar_app, args=(
        exe_atual,), daemon=True).start()
    root.mainloop()
