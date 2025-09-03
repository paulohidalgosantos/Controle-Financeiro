#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Updater - Sistema de Atualização Automática
Responsável por baixar, instalar e executar a nova versão do aplicativo
"""

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
from pathlib import Path
from typing import Optional   # 🔹 correção: faltava esse import


class UpdaterGUI:
    def __init__(self, exe_atual: str, versao_atual: str, versao_nova: str, url_download: str):
        self.exe_atual = exe_atual
        self.versao_atual = versao_atual
        self.versao_nova = versao_nova
        self.url_download = url_download

        self.pasta_app = os.path.dirname(exe_atual)
        self.nome_exe = os.path.basename(exe_atual)
        self.log_file = os.path.join(self.pasta_app, "update_log.txt")

        self.setup_ui()

    def setup_ui(self):
        """Configura a interface do updater"""
        self.root = tk.Tk()
        self.root.title("Atualizando Controle Financeiro")
        self.root.geometry("600x400")
        self.root.resizable(False, False)

        # Frame principal
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Título
        title_label = tk.Label(
            main_frame,
            text="Atualizando Aplicativo",
            font=("Arial", 16, "bold"),
            bg='#f0f0f0',
            fg='#333'
        )
        title_label.pack(pady=10)

        # Info da versão
        version_info = tk.Label(
            main_frame,
            text=f"Atualizando de v{self.versao_atual} para v{self.versao_nova}",
            font=("Arial", 10),
            bg='#f0f0f0',
            fg='#666'
        )
        version_info.pack(pady=5)

        # Área de log
        log_frame = tk.Frame(main_frame, bg='#f0f0f0')
        log_frame.pack(fill='both', expand=True, pady=10)

        tk.Label(
            log_frame,
            text="Log da Atualização:",
            font=("Arial", 10, "bold"),
            bg='#f0f0f0'
        ).pack(anchor='w')

        self.text_area = scrolledtext.ScrolledText(
            log_frame,
            state='normal',
            wrap=tk.WORD,
            height=15,
            font=("Consolas", 9)
        )
        self.text_area.pack(fill='both', expand=True)

        # Barra de progresso
        self.progress = tk.StringVar()
        self.progress.set("Preparando...")

        progress_label = tk.Label(
            main_frame,
            textvariable=self.progress,
            font=("Arial", 10),
            bg='#f0f0f0'
        )
        progress_label.pack(pady=5)

    def escrever_log(self, msg: str):
        """Escreve mensagem no log visual e arquivo"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        linha = f"[{timestamp}] {msg}"

        print(linha)

        try:
            self.text_area.config(state='normal')
            self.text_area.insert(tk.END, linha + "\n")
            self.text_area.see(tk.END)
            self.text_area.update_idletasks()
            self.root.update()
        except:
            pass

        # Salva no arquivo de log
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(linha + "\n")
        except:
            pass

    def atualizar_progresso(self, texto: str):
        """Atualiza o texto de progresso"""
        self.progress.set(texto)
        self.root.update()

    def atualizar_app(self):
        """Executa o processo de atualização"""
        pasta_temp = None

        try:
            self.escrever_log("=== INICIANDO ATUALIZAÇÃO ===")
            self.atualizar_progresso("Criando diretório temporário...")

            # Cria pasta temporária
            pasta_temp = tempfile.mkdtemp(prefix="CF_Update_")
            self.escrever_log(f"Pasta temporária criada: {pasta_temp}")

            # Baixa atualização
            self.atualizar_progresso("Baixando atualização...")
            zip_path = os.path.join(pasta_temp, "update.zip")

            self.escrever_log(f"Baixando de: {self.url_download}")
            urllib.request.urlretrieve(self.url_download, zip_path)
            self.escrever_log("Download concluído com sucesso!")

            # Extrai arquivos
            self.atualizar_progresso("Extraindo arquivos...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(pasta_temp)
            self.escrever_log("Extração concluída!")

            # Encontra o novo executável
            self.atualizar_progresso("Localizando novo executável...")
            novo_exe = self._encontrar_executavel(pasta_temp)

            if not novo_exe:
                raise Exception("Nenhum executável encontrado na atualização")

            self.escrever_log(f"Novo executável encontrado: {os.path.basename(novo_exe)}")

            # Substitui o aplicativo
            self._substituir_aplicativo(novo_exe)

            # Finaliza com sucesso
            self.escrever_log("=== ATUALIZAÇÃO CONCLUÍDA ===")
            self.atualizar_progresso("Atualização concluída! Iniciando aplicativo...")

            time.sleep(2)
            self._iniciar_novo_app()

        except Exception as e:
            self.escrever_log(f"ERRO: {e}")
            self.atualizar_progresso("Erro na atualização!")
            messagebox.showerror("Erro na Atualização", str(e))

        finally:
            if pasta_temp and os.path.exists(pasta_temp):
                try:
                    shutil.rmtree(pasta_temp)
                    self.escrever_log("Pasta temporária removida")
                except:
                    self.escrever_log("Aviso: não foi possível remover pasta temporária")

    def _encontrar_executavel(self, pasta: str) -> Optional[str]:
        """Encontra o executável na pasta extraída"""
        for root, dirs, files in os.walk(pasta):
            for arquivo in files:
                if arquivo.endswith(('.exe', '.pyw', '.py')):
                    if arquivo.endswith('.exe'):
                        return os.path.join(root, arquivo)

        for root, dirs, files in os.walk(pasta):
            for arquivo in files:
                if arquivo.endswith('.pyw'):
                    return os.path.join(root, arquivo)

        for root, dirs, files in os.walk(pasta):
            for arquivo in files:
                if arquivo == 'main.py' or 'controle' in arquivo.lower():
                    return os.path.join(root, arquivo)

        return None

    def _substituir_aplicativo(self, novo_exe: str):
        """Substitui o aplicativo antigo pelo novo"""
        destino = self.exe_atual
        backup = destino + ".old"

        self.atualizar_progresso("Criando backup do aplicativo atual...")

        for tentativa in range(10):
            try:
                if os.path.exists(destino):
                    os.rename(destino, backup)
                    self.escrever_log("Backup criado com sucesso")
                break
            except PermissionError:
                self.escrever_log(f"Tentativa {tentativa + 1}: arquivo em uso, aguardando...")
                time.sleep(1)
        else:
            raise Exception("Não foi possível criar backup - arquivo em uso")

        self.atualizar_progresso("Instalando nova versão...")
        shutil.copy2(novo_exe, destino)
        self.escrever_log("Nova versão instalada com sucesso!")

        try:
            os.remove(backup)
            self.escrever_log("Backup antigo removido")
        except:
            self.escrever_log("Aviso: não foi possível remover backup antigo")

    def _iniciar_novo_app(self):
        """Inicia o novo aplicativo"""
        try:
            self.escrever_log("Iniciando aplicativo atualizado...")

            if self.exe_atual.endswith('.exe'):
                subprocess.Popen([self.exe_atual], cwd=self.pasta_app)
            else:
                subprocess.Popen([sys.executable, self.exe_atual], cwd=self.pasta_app)

            self.escrever_log("Aplicativo iniciado com sucesso!")
            self.root.after(3000, self.root.destroy)

        except Exception as e:
            self.escrever_log(f"Erro ao iniciar aplicativo: {e}")
            messagebox.showerror("Erro", f"Aplicativo atualizado, mas erro ao iniciar: {e}")


def main():
    if len(sys.argv) < 5:
        messagebox.showerror(
            "Erro",
            "Updater chamado incorretamente.\n"
            "Uso: updater.py <exe_atual> <versao_atual> <versao_nova> <url_download>"
        )
        sys.exit(1)

    exe_atual = sys.argv[1]
    versao_atual = sys.argv[2]
    versao_nova = sys.argv[3]
    url_download = sys.argv[4]

    time.sleep(2)

    updater_gui = UpdaterGUI(exe_atual, versao_atual, versao_nova, url_download)
    threading.Thread(target=updater_gui.atualizar_app, daemon=True).start()
    updater_gui.root.mainloop()


if __name__ == "__main__":
    main()
