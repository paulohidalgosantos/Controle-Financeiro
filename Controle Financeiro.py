import ttkbootstrap as tb
from datetime import datetime
from collections import defaultdict
from operator import itemgetter
from functools import partial
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from PIL import Image, ImageTk
from ttkbootstrap import Style
from ttkbootstrap.constants import *
import os
import sys
import time
import json
import copy
import math
import subprocess
import webbrowser
import urllib.request
import locale
from tkinter import scrolledtext
import tempfile
import zipfile
import threading


VERSAO_ATUAL = "1.1.3"


def buscar_atualizacao(app):
    """Verifica se existe uma nova versão e atualiza o app em 1 exe."""
    try:
        # URL do arquivo de versão no GitHub (somente o número da versão)
        url_versao = "https://raw.githubusercontent.com/paulohidalgosantos/Controle-Financeiro/main/versao.txt"
        with urllib.request.urlopen(url_versao) as response:
            versao_nova = response.read().decode("utf-8").strip()

        if versao_nova == VERSAO_ATUAL:
            messagebox.showinfo(
                "Atualização", "Você já possui a versão mais recente.", parent=app)
            return

        resposta = messagebox.askyesno(
            "Atualização disponível",
            f"Versão {versao_nova} disponível.\nDeseja atualizar agora?",
            parent=app
        )
        if not resposta:
            return

        # ------------------- GUI de progresso -------------------
        class UpdaterGUI:
            def __init__(self):
                self.root = tk.Toplevel(app)
                self.root.title("Atualizando Controle Financeiro")
                self.root.geometry("600x400")

                self.label_status = ttk.Label(
                    self.root,
                    text=f"Atualizando da versão {VERSAO_ATUAL} para {versao_nova}...",
                    font=("Segoe UI", 12)
                )
                self.label_status.pack(pady=10)

                self.text_area = scrolledtext.ScrolledText(
                    self.root, wrap=tk.WORD, height=15, width=70, state="disabled")
                self.text_area.pack(padx=10, pady=10, fill="both", expand=True)

                self.progress = ttk.Progressbar(
                    self.root, mode="indeterminate")
                self.progress.pack(fill="x", padx=10, pady=10)
                self.progress.start(10)

            def escrever_log(self, msg):
                # Atualiza a GUI na thread principal
                self.root.after(0, self._escrever_gui, msg)

            def _escrever_gui(self, msg):
                self.text_area.configure(state="normal")
                self.text_area.insert(tk.END, msg + "\n")
                self.text_area.configure(state="disabled")
                self.text_area.see(tk.END)

            def fechar(self):
                self.root.after(0, self.root.destroy)

        gui = UpdaterGUI()

        # ------------------- Função de atualização -------------------
        def atualizar():
            try:
                tempdir = tempfile.mkdtemp()
                gui.escrever_log(f"Temp dir criada: {tempdir}")

                # URL do novo exe
                url_download = f"https://github.com/paulohidalgosantos/Controle-Financeiro/releases/download/v{versao_nova}/Controle.Financeiro.exe"
                temp_exe = os.path.join(tempdir, "Controle.Financeiro.exe")

                gui.escrever_log(f"Baixando atualização de {url_download}...")
                urllib.request.urlretrieve(url_download, temp_exe)
                gui.escrever_log("Download concluído.")

                # Caminho do app atual (respeita nome do usuário e pasta)
                exe_path = os.path.abspath(sys.argv[0])
                gui.escrever_log(f"Caminho do app atual: {exe_path}")

                bat_path = os.path.join(tempdir, "update.bat")

                # Cria batch temporário para substituir exe e reiniciar
                with open(bat_path, "w", encoding="utf-8") as f:
                    f.write(f"""
@echo off
ping 127.0.0.1 -n 3 >nul
copy /y "{temp_exe}" "{exe_path}"
start "" "{exe_path}"
del "%~f0"
""")

                gui.escrever_log("Preparando atualização final...")

                # Fecha app principal na thread principal
                gui.fechar()
                app.after(500, lambda: app.quit())
                app.after(500, lambda: app.destroy())

                time.sleep(1)
                subprocess.Popen([bat_path], shell=True)
                sys.exit()

            except Exception as e:
                gui.escrever_log(f"[ERRO] {e}")
                app.after(0, lambda: messagebox.showerror(
                    "Erro", f"Falha na atualização:\n{e}", parent=app))

        threading.Thread(target=atualizar, daemon=True).start()
        gui.root.mainloop()

    except Exception as e:
        messagebox.showerror(
            "Erro", f"Falha ao buscar atualização:\n{e}", parent=app)


def verificar_dependencias():
    """Verifica se todas as dependências estão disponíveis - útil para debug"""
    try:
        import tkinter
        print("✓ tkinter OK")
    except ImportError as e:
        print(f"✗ tkinter ERRO: {e}")

    try:
        import PIL
        print("✓ PIL OK")
    except ImportError as e:
        print(f"✗ PIL ERRO: {e}")

    try:
        import ttkbootstrap
        print("✓ ttkbootstrap OK")
    except ImportError as e:
        print(f"✗ ttkbootstrap ERRO: {e}")

    # Verificar se está rodando como executável empacotado
    if getattr(sys, 'frozen', False):
        print("✓ Rodando como executável empacotado")
        print(f"Pasta do executável: {getattr(sys, '_MEIPASS', 'N/A')}")
    else:
        print("✓ Rodando como script Python")

# Chame esta função apenas para debug quando necessário
# verificar_dependencias()


# Define BASE_DIR uma única vez
BASE_DIR = os.path.join(os.path.expanduser(
    "~"), "AppData", "Local", "ControleFinanceiro")
os.makedirs(BASE_DIR, exist_ok=True)

# Define pasta oculta para salvar os dados
PASTA_OCULTA = os.path.join(BASE_DIR, ".dados_ocultos")

if not os.path.exists(PASTA_OCULTA):
    os.mkdir(PASTA_OCULTA)
    os.system(f'attrib +h "{PASTA_OCULTA}"')  # Oculta a pasta no Windows

# Caminho do arquivo JSON
CAMINHO_ARQUIVO = os.path.join(PASTA_OCULTA, "Controle Financeiro.json")

# Dados globais
dados = {}
cartoes = []
contas_fixas_modelo = []
estado_expansao_cartoes = {}
estado_expansao_dias = {}
estado_expansao_gastos_diarios = {}
cartoes_fechamento = {}
janela_gastos_detalhados = None
inicio_uso = None
ultima_selecao_cartao = None
ultima_selecao_tipo = None
usuario_atual = None
usuarios = []
APP_BG = "#f8f9fa"


# Funções de dados
def carregar_dados():
    global dados, cartoes, contas_fixas_modelo, tipos_gasto, inicio_uso
    global ultima_selecao_cartao, ultima_selecao_tipo, ultima_selecao_mes, ultima_selecao_ano
    global usuarios  # <-- novo

    if os.path.exists(CAMINHO_ARQUIVO):
        try:
            with open(CAMINHO_ARQUIVO, "r", encoding="utf-8") as f:
                conteudo = json.load(f)

                # Sempre força cada mês a ser dict
                dados_carregados = conteudo.get("dados", {})
                dados = {
                    tuple(map(int, chave.split("-"))): (valor if isinstance(valor, dict) else {})
                    for chave, valor in dados_carregados.items()
                }

                cartoes = conteudo.get("cartoes", []) or []
                contas_fixas_modelo = conteudo.get(
                    "contas_fixas_modelo", []) or []
                tipos_gasto = conteudo.get(
                    "tipos_gasto") or TIPOS_GASTO_PADRAO.copy()

                # Corrige inicio_uso evitando erro se for None
                inicio_uso_raw = conteudo.get("inicio_uso")
                if inicio_uso_raw and isinstance(inicio_uso_raw, (list, tuple)) and len(inicio_uso_raw) == 2:
                    inicio_uso = tuple(inicio_uso_raw)
                else:
                    inicio_uso = None

                ultima_selecao = conteudo.get("ultima_selecao", {}) or {}
                ultima_selecao_cartao = ultima_selecao.get("cartao", None)
                ultima_selecao_tipo = ultima_selecao.get("tipo_gasto", None)
                ultima_selecao_mes = ultima_selecao.get("mes", None)
                ultima_selecao_ano = ultima_selecao.get("ano", None)

                usuarios = conteudo.get("usuarios", []) or []

        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            dados, cartoes, contas_fixas_modelo = {}, [], []
            tipos_gasto = TIPOS_GASTO_PADRAO.copy()
            inicio_uso = None
            ultima_selecao_cartao = ultima_selecao_tipo = None
            ultima_selecao_mes = ultima_selecao_ano = None
            usuarios = []
            show_warning(
                "Aviso",
                f"Erro ao carregar dados salvos. Iniciando com dados limpos.\nErro: {e}"
            )
    else:
        dados, cartoes, contas_fixas_modelo = {}, [], []
        tipos_gasto = TIPOS_GASTO_PADRAO.copy()
        inicio_uso = None
        ultima_selecao_cartao = ultima_selecao_tipo = None
        ultima_selecao_mes = ultima_selecao_ano = None
        usuarios = []

    # Garante que sempre exista lista de cartao_credito
    for key, valor in list(dados.items()):
        if not isinstance(valor, dict):
            dados[key] = {}
        for g in dados[key].get("cartao_credito", []):
            if "status" not in g:
                g["status"] = "Aberto"

    salvar_dados()


def salvar_dados():
    try:
        dados_para_salvar = {
            f"{mes:02d}-{ano}": valor
            for (mes, ano), valor in dados.items()
        }
        with open(CAMINHO_ARQUIVO, "w", encoding="utf-8") as f:
            json.dump({
                "dados": dados_para_salvar,
                "cartoes": cartoes,
                "contas_fixas_modelo": contas_fixas_modelo,
                "tipos_gasto": tipos_gasto,
                "inicio_uso": inicio_uso,
                "ultima_selecao": {
                    "cartao": ultima_selecao_cartao,
                    "tipo_gasto": ultima_selecao_tipo,
                    "mes": ultima_selecao_mes,
                    "ano": ultima_selecao_ano
                },
                "usuarios": usuarios  # <-- novo
            }, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Erro ao salvar dados:", e)


# Moeda Brasileira
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')

# Tipos de gasto iniciais
TIPOS_GASTO_PADRAO = ["Lazer", "Restaurante",
                      "Supermercado", "Pessoal", "Transporte", "Saúde"]
tipos_gasto = TIPOS_GASTO_PADRAO.copy()


def resource_path(relative_path):
    """Retorna o caminho absoluto para um recurso (mesmo após empacotamento)."""
    try:
        # PyInstaller cria uma pasta temporária em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Caso normal: pega a pasta onde está o script
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

# -----------------------------
# Função para aplicar ícone em qualquer janela (Tk ou Toplevel)
# -----------------------------


def aplicar_icone(janela):
    """Aplica o ícone padrão a qualquer janela Tkinter."""
    global icone
    if icone:
        janela.iconphoto(False, icone)
# -----------------------------
# Tela de Login
# -----------------------------


def tela_login(root, icone=None):
    global usuario_atual

    def centralizar_janela(janela, largura, altura):
        tela_largura = janela.winfo_screenwidth()
        tela_altura = janela.winfo_screenheight()
        x = (tela_largura - largura) // 2
        y = (tela_altura - altura) // 2
        janela.geometry(f"{largura}x{altura}+{x}+{y}")

    # Criar janela de login como Toplevel
    login = tk.Toplevel(root)
    login.title(f"Login - Controle Financeiro {VERSAO_ATUAL}")
    if icone:
        login.iconphoto(False, icone)

    largura_login, altura_login = 420, 350
    centralizar_janela(login, largura_login, altura_login)
    login.resizable(False, False)
    login.configure(bg="#f8f9fa")

    # Bloquear interação com janela principal até fechar login
    login.grab_set()
    login.focus_force()

    frame_central = tk.Frame(login, padx=30, pady=25)
    frame_central.pack(expand=True, fill="both", padx=20, pady=20)
    frame_central.configure(relief="solid", borderwidth=1,
                            highlightbackground="#e9ecef", highlightthickness=1)

    tk.Label(frame_central, text="👤 Acesso ao Sistema", font=("Inter", 16, "bold"),
             bg="#ffffff", fg="#212529").pack(pady=(0, 20))
    tk.Label(frame_central, text="Selecione o usuário:", font=("Inter", 11),
             bg="#ffffff", fg="#495057").pack(pady=(0, 8))

    combo_usuarios = ttk.Combobox(frame_central, values=usuarios, state="readonly",
                                  font=("Inter", 11), width=25)
    combo_usuarios.pack(pady=8)

    # -----------------------------
    # Funções internas
    # -----------------------------
    def entrar():
        usuario = combo_usuarios.get()
        if not usuario:
            show_warning(
                "Atenção", "Nenhum usuário selecionado. Cadastre um novo usuário.")
            return
        global usuario_atual
        usuario_atual = usuario
        login.destroy()  # destrói login e libera janela principal

    def cadastrar():
        def salvar_usuario():
            novo = entry_nome.get().strip()
            if not novo:
                show_warning("Atenção", "Digite um nome.")
                return
            if novo in usuarios:
                show_warning("Atenção", "Usuário já existe.")
                return

            usuarios.append(novo)
            salvar_dados()
            combo_usuarios["values"] = usuarios

            global usuario_atual
            usuario_atual = novo
            cadastro.destroy()

        cadastro = tk.Toplevel(login)
        cadastro.title("Novo Usuário")
        largura_cad, altura_cad = 350, 180
        centralizar_janela(cadastro, largura_cad, altura_cad)
        cadastro.resizable(False, False)
        cadastro.configure(bg="#ffffff")
        cadastro.grab_set()
        cadastro.focus_force()

        cadastro_frame = tk.Frame(cadastro, bg="#ffffff", padx=20, pady=20)
        cadastro_frame.pack(fill="both", expand=True)

        tk.Label(cadastro_frame, text="Nome do usuário:", font=("Inter", 12),
                 bg="#ffffff", fg="#495057").pack(pady=10)

        entry_nome = tk.Entry(cadastro_frame, font=(
            "Inter", 11), width=25, relief="solid", bd=1)
        entry_nome.pack(pady=8)
        entry_nome.focus()
        entry_nome.bind("<Return>", lambda event: salvar_usuario())

        tb.Button(cadastro_frame, text="✓ Salvar", command=salvar_usuario,
                  width=15, bootstyle="success").pack(pady=15)
        aplicar_icone(cadastro)

    # -----------------------------
    # Botões
    # -----------------------------
    frame_botoes = tk.Frame(frame_central, bg="#ffffff")
    frame_botoes.pack(pady=15)

    tb.Button(frame_botoes, text="🚀 Entrar", command=entrar,
              width=18, bootstyle="primary").pack(pady=8)
    tb.Button(frame_botoes, text="👤 Cadastrar Novo", command=cadastrar,
              width=18, bootstyle="outline-secondary").pack()

    # -----------------------------
    # Fechamento seguro do login
    # -----------------------------
    def fechar_login():
        global usuario_atual
        if 'usuario_atual' not in globals() or not usuario_atual:
            login.destroy()   # fecha a tela de login
            root.destroy()
            sys.exit()        # encerra o programa totalmente
        else:
            login.destroy()   # fecha apenas a tela de login

    login.protocol("WM_DELETE_WINDOW", fechar_login)

    # Espera o login ser concluído antes de continuar
    root.wait_window(login)


# -----------------------------
# Inicialização da aplicação
# -----------------------------
if __name__ == "__main__":
    carregar_dados()

    # Janela principal
    app = tb.Window(themename="morph")

    # --- COR PADRÃO ---
    APP_BG = "#f8f9fa"  # cinza claro
    app.option_add("*Background", APP_BG)
    app.option_add("*foreground", "#212529")  # cor padrão do texto

    app.title(f"💰 Controle Financeiro {VERSAO_ATUAL}")
    app.state('zoomed')

    # Agora que a janela Tk existe, cria o ícone
    try:
        caminho_icone = resource_path("icone.png")
        imagem = Image.open(caminho_icone)
        icone = ImageTk.PhotoImage(imagem)
        app.iconphoto(False, icone)
    except Exception as e:
        icone = None
        print(f"⚠️ Erro ao carregar ícone: {e}")

    # -------------------------
    # ESCONDER janela principal antes do login
    # -------------------------
    app.update()
    app.withdraw()

    # -------------------------
    # Chamar tela de login
    # -------------------------
    tela_login(app, icone)

    # -------------------------
    # MOSTRAR janela principal apenas se houver usuário logado
    # -------------------------
    if not ('usuario_atual' in globals() and usuario_atual):
        sys.exit()

    app.deiconify()
    app.state('zoomed')


def show_warning(msg, title="Aviso"):
    """Exibe uma mensagem de aviso usando a janela principal como parent."""
    messagebox.showwarning(title, msg, parent=app)


def show_error(msg, title="Erro"):
    """Exibe uma mensagem de erro usando a janela principal como parent."""
    messagebox.showerror(title, msg, parent=app)

    # -------------------------
    # ESCONDER janela principal antes do login
    # -------------------------
    app.update()
    app.withdraw()

    # -------------------------
    # Chamar tela de login
    # -------------------------
    tela_login(app, icone)

    # -------------------------
    # MOSTRAR janela principal apenas se houver usuário logado
    # -------------------------
    if not ('usuario_atual' in globals() and usuario_atual):
        sys.exit()

    app.deiconify()
    app.state('zoomed')


# -------------------------
# Header e boas-vindas
# -------------------------
header_frame = tk.Frame(app, height=50, bg="#0d6efd", relief="flat")
header_frame.pack(fill="x")
header_frame.pack_propagate(False)

welcome_frame = tk.Frame(header_frame, bg="#0d6efd")
welcome_frame.pack(expand=True, fill="both")

global label_bem_vindo
label_bem_vindo = tk.Label(
    welcome_frame,
    text=f"Olá {usuario_atual}!",
    font=("Inter", 19, "bold"),
    anchor="center"
)
label_bem_vindo.pack(pady=10, expand=True)

# 🔒 Força as cores manualmente (ignora tema ttkbootstrap)
label_bem_vindo.configure(bg="#d9e3f1")


# ---- Funções usadas no menu ----

def centralizar_janela(janela, largura, altura):
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")


def criar_menu():
    menubar = tk.Menu(app, bg="#f8f9fa", fg="#495057", activebackground="#e9ecef", activeforeground="#212529",
                      font=("Inter", 10))

    menu_gerenciar = tk.Menu(menubar, tearoff=0, font=("Inter", 10),
                             bg="#d9e3f1", fg="#495057", activebackground="#0d6efd", activeforeground="#f8f9fa")

    opcoes = [
        (" 👤     Trocar Usuário", trocar_usuario),
        (" 👥     Gerenciar Usuários", gerenciar_usuarios),
        (" 💳    Gerenciar Cartões", gerenciar_cartoes),
        (" 📂     Categorias de Gastos", abrir_gerenciador_categorias),
        (" 🔄     Buscar Atualização", partial(buscar_atualizacao, app)),
        (" 🗑️ Zerar Aplicativo", zerar_tudo),
        (" 📤     Exportar Dados", exportar_dados),
        (" 📥     Importar Dados", importar_dados),
        (" 📅     Definir Início do Uso", definir_inicio_uso)
    ]
    for i, (label, comando) in enumerate(opcoes):
        if i in [4, 6, 8]:
            menu_gerenciar.add_separator()
        menu_gerenciar.add_command(label=label, command=comando)
    menubar.add_cascade(label="⚙️  Gerenciar", menu=menu_gerenciar)
    app.config(menu=menubar)


def definir_inicio_uso():
    """Janela para definir o mês/ano de início de uso do sistema."""
    global inicio_uso

    janela = tk.Toplevel(app)
    janela.title("Definir Início do Uso")
    janela.resizable(False, False)
    janela.grab_set()
    janela.transient(app)
    janela.configure(bg="#f8f9fa")
    aplicar_icone(janela)

    largura, altura = 300, 250
    centralizar_janela(janela, largura, altura)

    main_frame = tk.Frame(janela, bg="#f8f9fa", padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="Mês de início (1 a 12):",
              font=("Inter", 11)).pack(pady=(15, 5))
    combo_mes = ttk.Combobox(main_frame, values=list(range(1, 13)), state="readonly",
                             justify="center", font=("Inter", 10))
    combo_mes.pack()
    combo_mes.current((inicio_uso[0] - 1) if inicio_uso else 0)

    ttk.Label(main_frame, text="Ano de início (ex: 2023):",
              font=("Inter", 11)).pack(pady=(15, 5))
    entry_ano = ttk.Entry(main_frame, justify="center", font=("Inter", 10))
    entry_ano.pack()
    entry_ano.insert(
        0, str(inicio_uso[1]) if inicio_uso else str(datetime.now().year))

    # ---------------- Função para mensagens ----------------
    def mostrar_mensagem(titulo, mensagem, tipo="info", ao_fechar=None):
        msg_janela = tk.Toplevel(janela)
        msg_janela.title(titulo)
        msg_janela.resizable(False, False)
        msg_janela.grab_set()
        msg_janela.attributes("-topmost", True)
        msg_janela.configure(bg="#f8f9fa")
        aplicar_icone(msg_janela)

        largura_msg, altura_msg = 360, 120
        x = (janela.winfo_screenwidth() // 2) - (largura_msg // 2)
        y = (janela.winfo_screenheight() // 2) - (altura_msg // 2)
        msg_janela.geometry(f"{largura_msg}x{altura_msg}+{x}+{y}")

        frame = tk.Frame(msg_janela, bg="#f8f9fa", padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=mensagem, font=("Inter", 11),
                  justify="center", wraplength=320).pack(pady=10)

        def fechar():
            msg_janela.destroy()
            if ao_fechar:
                ao_fechar()

        ttk.Button(frame, text="OK", command=fechar,
                   bootstyle="success" if tipo == "info" else "danger").pack()

    # ---------------- Função de confirmação ----------------
    def confirmar():
        nonlocal combo_mes, entry_ano, janela
        global inicio_uso

        try:
            mes = int(combo_mes.get())
            ano = int(entry_ano.get().strip())
            if not (1 <= mes <= 12):
                raise ValueError("Mês deve estar entre 1 e 12.")
            if not (1900 <= ano <= 2100):
                raise ValueError("Ano deve estar entre 1900 e 2100.")

            inicio_uso = (mes, ano)
            salvar_dados()

            # Recalcula todos os meses afetados pelo novo início de uso
            recalcular_saldos_em_cadeia()
            atualizar_resumo()  # Atualiza a interface com os novos saldos

            mostrar_mensagem(
                "Sucesso",
                f"Início do uso definido para {mes:02d}/{ano}",
                tipo="info",
                ao_fechar=lambda: janela.destroy()
            )

        except ValueError as ve:
            mostrar_mensagem("Erro de validação", f"Erro: {ve}", tipo="erro")
        except Exception:
            mostrar_mensagem(
                "Erro", "Preencha os campos corretamente.", tipo="erro")

    ttk.Button(main_frame, text="✓ Confirmar", command=confirmar,
               bootstyle="success").pack(pady=20)
    janela.bind('<Return>', lambda event: confirmar())


def gerenciar_cartoes():
    janela = tk.Toplevel(app)
    janela.title("Gerenciar Cartões")
    janela.resizable(False, False)
    janela.attributes("-topmost", True)
    janela.grab_set()
    janela.configure(bg="#f8f9fa")

    centralizar_janela(janela, 350, 250)

    main_frame = tk.Frame(janela, bg="#f8f9fa", padx=25, pady=25)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="💳 Gerenciar Cartões",
              font=("Inter", 15, "bold")).pack(pady=(0, 20))

    frame_botoes = ttk.Frame(main_frame)
    frame_botoes.pack(pady=10)

    ttk.Button(frame_botoes, text="➕ Adicionar Cartão", width=28,
               command=lambda: adicionar_cartao(janela), bootstyle="success").pack(pady=8)
    ttk.Button(frame_botoes, text="✏️ Editar Cartão", width=28,
               command=lambda: editar_cartao(janela), bootstyle="primary").pack(pady=8)
    ttk.Button(frame_botoes, text="🗑️ Remover Cartão", width=28,
               command=lambda: excluir_cartao(janela), bootstyle="danger").pack(pady=8)
    aplicar_icone(janela)


def abrir_gerenciador_categorias():
    janela = tk.Toplevel(app)
    janela.title("Gerenciar Categorias")
    janela.resizable(False, False)
    janela.attributes("-topmost", True)
    janela.grab_set()
    janela.configure(bg="#f8f9fa")

    centralizar_janela(janela, 350, 200)
    aplicar_icone(janela)  # Aplica o ícone na janela

    main_frame = tk.Frame(janela, bg="#f8f9fa", padx=25, pady=25)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="📂 Gerenciar Categorias",
              font=("Inter", 15, "bold")).pack(pady=(0, 20))
    ttk.Button(main_frame, text="📝 Editar categorias", width=28,
               command=lambda: editar_tipos_gastos(janela), bootstyle="primary").pack(pady=10)


def editar_cartao(janela_anterior):
    if not cartoes:
        mostrar_erro_toplevel("Nenhum cartão cadastrado para editar.", app)
        return

    janela_anterior.destroy()
    janela = tk.Toplevel(app)
    janela.title("Editar Cartão")
    janela.configure(bg="#f8f9fa")
    largura, altura = 350, 350
    centralizar_janela(janela, largura, altura)
    janela.attributes("-topmost", True)
    janela.grab_set()

    main_frame = tk.Frame(janela, bg="#f8f9fa", padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="Selecione o cartão para editar:",
              font=("Inter", 11)).pack(pady=8)

    combo_cartoes = ttk.Combobox(main_frame, state="readonly", values=[c['nome'] for c in cartoes],
                                 font=("Inter", 10))
    combo_cartoes.pack(pady=5)

    ttk.Label(main_frame, text="Novo nome do Cartão:",
              font=("Inter", 11)).pack(pady=(15, 5))
    entrada_nome = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_nome.pack(pady=5)

    ttk.Label(main_frame, text="Novo dia de Fechamento da Fatura (1-31):",
              font=("Inter", 11)).pack(pady=(15, 5))
    entrada_fechamento = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_fechamento.pack(pady=5)

    def carregar_dados(event=None):
        idx = combo_cartoes.current()
        if idx >= 0:
            cartao = cartoes[idx]
            entrada_nome.delete(0, tk.END)
            entrada_nome.insert(0, cartao['nome'])
            entrada_fechamento.delete(0, tk.END)
            entrada_fechamento.insert(0, str(cartao['fechamento']))

    combo_cartoes.bind("<<ComboboxSelected>>", carregar_dados)
    carregar_dados()  # Carrega dados do primeiro cartão

    def salvar():
        idx = combo_cartoes.current()
        if idx == -1:
            mostrar_erro_toplevel("Selecione um cartão para editar.", janela)
            return

        novo_nome = entrada_nome.get().strip()
        fechamento_str = entrada_fechamento.get().strip()

        if not novo_nome:
            mostrar_erro_toplevel("Nome do cartão não pode ser vazio.", janela)
            return
        if not fechamento_str.isdigit():
            mostrar_erro_toplevel(
                "Dia de fechamento deve ser um número entre 1 e 31.", janela)
            return
        fechamento = int(fechamento_str)
        if not (1 <= fechamento <= 31):
            mostrar_erro_toplevel(
                "Dia de fechamento deve estar entre 1 e 31.", janela)
            return

        # Verificar se já existe outro cartão com esse nome (exceto o atual)
        for i, c in enumerate(cartoes):
            if i != idx and c['nome'].lower() == novo_nome.lower():
                mostrar_erro_toplevel(
                    "Já existe um cartão com esse nome.", janela)
                return

        # Atualiza os dados do cartão
        cartoes[idx]['nome'] = novo_nome
        cartoes[idx]['fechamento'] = fechamento

        salvar_dados()
        atualizar_resumo()

        # Janela de sucesso customizada com ícone
        sucesso_janela = tk.Toplevel(janela)
        sucesso_janela.title("Sucesso")
        sucesso_janela.resizable(False, False)
        sucesso_janela.grab_set()
        sucesso_janela.attributes("-topmost", True)
        sucesso_janela.configure(bg="#f8f9fa")
        centralizar_janela(sucesso_janela, 300, 120)

        if icone:
            sucesso_janela.iconphoto(False, icone)

        frame = tk.Frame(sucesso_janela, bg="#f8f9fa", padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Cartão atualizado com sucesso!",
                  font=("Inter", 11)).pack(pady=10)
        ttk.Button(frame, text="OK", command=sucesso_janela.destroy,
                   bootstyle="success").pack()

    ttk.Button(main_frame, text="💾 Salvar Alterações",
               command=salvar, bootstyle="success").pack(pady=20)
    janela.bind("<Return>", lambda event: salvar())
    aplicar_icone(janela)


def excluir_cartao(janela_anterior):
    if not cartoes:
        nova_janela = tk.Toplevel(app)
        nova_janela.title("Aviso")
        nova_janela.configure(bg="#f8f9fa")
        largura = 380
        altura = 150

        # Centraliza a janela
        x = (nova_janela.winfo_screenwidth() // 2) - (largura // 2)
        y = (nova_janela.winfo_screenheight() // 2) - (altura // 2)
        nova_janela.geometry(f"{largura}x{altura}+{x}+{y}")

        nova_janela.attributes("-topmost", True)
        nova_janela.grab_set()

        main_frame = tk.Frame(nova_janela, bg="#f8f9fa", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        def abrir_adicionar_cartao():
            nova_janela.destroy()
            adicionar_cartao(nova_janela)  # Função real para adicionar cartão

        ttk.Label(
            main_frame,
            text="Nenhum cartão cadastrado.\nDeseja cadastrar um novo cartão?",
            wraplength=340, font=("Inter", 11)
        ).pack(pady=15)

        botoes = ttk.Frame(main_frame)
        botoes.pack(pady=10)

        ttk.Button(botoes, text="✓ Sim", command=abrir_adicionar_cartao,
                   bootstyle="success").pack(side="left", padx=10)
        ttk.Button(botoes, text="✗ Não", command=nova_janela.destroy,
                   bootstyle="secondary").pack(side="right", padx=10)

        aplicar_icone(nova_janela)
        janela_anterior.destroy()
        return

    nova_janela = tk.Toplevel(app)
    nova_janela.title("Excluir Cartão")
    nova_janela.configure(bg="#f8f9fa")
    largura = 350
    altura = 180
    x = (nova_janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (nova_janela.winfo_screenheight() // 2) - (altura // 2)
    nova_janela.geometry(f"{largura}x{altura}+{x}+{y}")
    nova_janela.attributes("-topmost", True)
    nova_janela.grab_set()

    janela_anterior.destroy()

    main_frame = tk.Frame(nova_janela, bg="#f8f9fa", padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="Selecione o cartão para excluir:",
              font=("Inter", 11)).pack(pady=8)

    combo_cartoes = ttk.Combobox(
        main_frame, state="readonly", font=("Inter", 10))
    combo_cartoes.pack(pady=5)

    def atualizar_combo():
        nomes_cartoes = [c['nome'] for c in cartoes]
        combo_cartoes['values'] = nomes_cartoes
        if nomes_cartoes:
            combo_cartoes.current(0)
        else:
            combo_cartoes.set('')

    atualizar_combo()

    def mostrar_erro_toplevel(mensagem):
        erro_janela = tk.Toplevel(nova_janela)
        erro_janela.title("Erro")
        erro_janela.geometry("330x110")
        erro_janela.attributes("-topmost", True)
        erro_janela.grab_set()

        erro_frame = tk.Frame(erro_janela, padx=15, pady=15)
        erro_frame.pack(fill="both", expand=True)

        ttk.Label(erro_frame, text=mensagem, foreground="#dc3545", wraplength=300,
                  font=("Inter", 10)).pack(pady=10)
        ttk.Button(erro_frame, text="OK", command=erro_janela.destroy,
                   bootstyle="danger").pack()

        aplicar_icone(erro_janela)

        erro_janela.update_idletasks()
        w = erro_janela.winfo_width()
        h = erro_janela.winfo_height()
        x = nova_janela.winfo_rootx() + (nova_janela.winfo_width() // 2) - (w // 2)
        y = nova_janela.winfo_rooty() + (nova_janela.winfo_height() // 2) - (h // 2)
        erro_janela.geometry(f"+{x}+{y}")

    def confirmar_exclusao(cartao_nome, ao_confirmar):
        confirm_janela = tk.Toplevel(nova_janela)
        confirm_janela.title("Confirmar Exclusão")
        confirm_janela.geometry("360x150")
        confirm_janela.grab_set()
        confirm_janela.attributes("-topmost", True)

        confirm_frame = tk.Frame(confirm_janela, padx=15, pady=20)
        confirm_frame.pack(fill="both", expand=True)

        ttk.Label(confirm_frame,
                  text=f"Excluir o cartão '{cartao_nome}'?\nGastos antigos serão mantidos.",
                  wraplength=320, font=("Inter", 11)).pack(pady=15)

        botoes = ttk.Frame(confirm_frame)
        botoes.pack()

        ttk.Button(botoes, text="✓ Sim", command=lambda: (confirm_janela.destroy(), ao_confirmar()),
                   bootstyle="danger").pack(side="left", padx=10)
        ttk.Button(botoes, text="✗ Não", command=confirm_janela.destroy,
                   bootstyle="secondary").pack(side="right", padx=10)

        aplicar_icone(confirm_janela)

        confirm_janela.update_idletasks()
        w = confirm_janela.winfo_width()
        h = confirm_janela.winfo_height()
        x = nova_janela.winfo_rootx() + (nova_janela.winfo_width() // 2) - (w // 2)
        y = nova_janela.winfo_rooty() + (nova_janela.winfo_height() // 2) - (h // 2)
        confirm_janela.geometry(f"+{x}+{y}")

    def excluir():
        idx = combo_cartoes.current()
        if idx == -1:
            mostrar_erro_toplevel("Selecione um cartão.")
            return

        cartao_excluir = cartoes[idx]

        def apos_confirmar():
            cartoes.remove(cartao_excluir)
            salvar_dados()
            atualizar_resumo()
            atualizar_combo()

            if not cartoes:
                nova_janela.destroy()

        confirmar_exclusao(cartao_excluir['nome'], apos_confirmar)

    ttk.Button(main_frame, text="🗑️ Excluir", command=excluir,
               bootstyle="danger").pack(pady=15)
    aplicar_icone(nova_janela)


def zerar_tudo():
    # Janela de entrada de senha customizada
    senha_janela = tk.Toplevel(app)
    senha_janela.title("Senha necessária")
    senha_janela.resizable(False, False)
    largura, altura = 360, 170
    x = (app.winfo_screenwidth() // 2) - (largura // 2)
    y = (app.winfo_screenheight() // 2) - (altura // 2)
    senha_janela.geometry(f"{largura}x{altura}+{x}+{y}")
    senha_janela.grab_set()
    senha_janela.attributes("-topmost", True)
    senha_janela.configure(bg="#f8f9fa")
    aplicar_icone(senha_janela)

    frame_senha = tk.Frame(senha_janela, bg="#f8f9fa", padx=20, pady=20)
    frame_senha.pack(fill="both", expand=True)

    ttk.Label(frame_senha, text="Digite a senha para zerar todos os dados:", font=(
        "Inter", 11)).pack(pady=(0, 10))
    entrada_senha = ttk.Entry(frame_senha, show="*", font=("Inter", 10))
    entrada_senha.pack(pady=(0, 10), fill="x")

    def verificar_senha():
        senha = entrada_senha.get()
        senha_janela.destroy()
        if senha == "admin":
            # Janela de confirmação customizada
            confirm_janela = tk.Toplevel(app)
            confirm_janela.title("Confirmar")
            confirm_janela.resizable(False, False)
            largura, altura = 360, 160
            x = (app.winfo_screenwidth() // 2) - (largura // 2)
            y = (app.winfo_screenheight() // 2) - (altura // 2)
            confirm_janela.geometry(f"{largura}x{altura}+{x}+{y}")
            confirm_janela.grab_set()
            confirm_janela.attributes("-topmost", True)
            confirm_janela.configure(bg="#f8f9fa")
            aplicar_icone(confirm_janela)

            frame = tk.Frame(confirm_janela, bg="#f8f9fa", padx=20, pady=20)
            frame.pack(fill="both", expand=True)

            ttk.Label(frame, text="Deseja realmente zerar todos os dados?",
                      font=("Inter", 11), justify="center", wraplength=320).pack(pady=15)

            botoes = tk.Frame(frame, bg="#f8f9fa")
            botoes.pack()

            def sim():
                global dados, contas_fixas_modelo, cartoes, tipos_gasto, usuarios
                dados.clear()
                contas_fixas_modelo.clear()
                cartoes.clear()
                tipos_gasto = TIPOS_GASTO_PADRAO.copy()
                usuarios.clear()
                salvar_dados()
                confirm_janela.destroy()

                # Janela informativa de sucesso
                info_janela = tk.Toplevel(app)
                info_janela.title("Zerado")
                info_janela.resizable(False, False)
                largura_info, altura_info = 360, 120
                x = (app.winfo_screenwidth() // 2) - (largura_info // 2)
                y = (app.winfo_screenheight() // 2) - (altura_info // 2)
                info_janela.geometry(f"{largura_info}x{altura_info}+{x}+{y}")
                info_janela.grab_set()
                info_janela.attributes("-topmost", True)
                info_janela.configure(bg="#f8f9fa")
                aplicar_icone(info_janela)

                frame_info = tk.Frame(
                    info_janela, bg="#f8f9fa", padx=20, pady=20)
                frame_info.pack(fill="both", expand=True)
                ttk.Label(frame_info, text="Todos os dados foram apagados e os tipos de gastos foram restaurados.",
                          font=("Inter", 11), justify="center", wraplength=320).pack(pady=10)
                ttk.Button(frame_info, text="OK", command=lambda: (info_janela.destroy(), app.destroy(), sys.exit()),
                           bootstyle="secondary").pack()

            ttk.Button(botoes, text="✓ Sim", command=sim,
                       bootstyle="danger").pack(side="left", padx=10)
            ttk.Button(botoes, text="✗ Não", command=confirm_janela.destroy,
                       bootstyle="secondary").pack(side="right", padx=10)
        else:
            # Janela de erro customizada
            erro_janela = tk.Toplevel(app)
            erro_janela.title("Senha incorreta")
            erro_janela.resizable(False, False)
            largura, altura = 360, 140
            x = (app.winfo_screenwidth() // 2) - (largura // 2)
            y = (app.winfo_screenheight() // 2) - (altura // 2)
            erro_janela.geometry(f"{largura}x{altura}+{x}+{y}")
            erro_janela.grab_set()
            erro_janela.attributes("-topmost", True)
            erro_janela.configure(bg="#f8f9fa")
            aplicar_icone(erro_janela)

            frame_erro = tk.Frame(erro_janela, bg="#f8f9fa", padx=20, pady=20)
            frame_erro.pack(fill="both", expand=True)
            ttk.Label(frame_erro, text="Senha inválida. Ação cancelada.",
                      font=("Inter", 11), justify="center", wraplength=320).pack(pady=10)
            ttk.Button(frame_erro, text="OK",
                       command=erro_janela.destroy, bootstyle="danger").pack()

    ttk.Button(frame_senha, text="✓ Confirmar",
               command=verificar_senha, bootstyle="success").pack(pady=10)
    senha_janela.bind('<Return>', lambda event: verificar_senha())


def exportar_dados():
    caminho = filedialog.asksaveasfilename(
        title="Exportar dados",
        defaultextension=".json",
        filetypes=[("Arquivo JSON", "*.json")],
        initialfile="controle_financeiro_backup.json"
    )
    if not caminho:
        return

    try:
        # Preparar dados para exportação
        dados_salvos = {
            f"{mes:02d}-{ano}": valor
            for (mes, ano), valor in dados.items()
        }
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump({
                "dados": dados_salvos,
                "cartoes": cartoes,
                "contas_fixas_modelo": contas_fixas_modelo,
                "tipos_gasto": tipos_gasto,
                "usuarios": usuarios
            }, f, ensure_ascii=False, indent=4)

        # Janela de sucesso customizada
        sucesso_janela = tk.Toplevel(app)
        sucesso_janela.title("Sucesso")
        sucesso_janela.resizable(False, False)
        largura, altura = 300, 120
        x = (app.winfo_screenwidth() // 2) - (largura // 2)
        y = (app.winfo_screenheight() // 2) - (altura // 2)
        sucesso_janela.geometry(f"{largura}x{altura}+{x}+{y}")
        sucesso_janela.grab_set()
        sucesso_janela.attributes("-topmost", True)
        sucesso_janela.configure(bg="#f8f9fa")
        aplicar_icone(sucesso_janela)

        frame = tk.Frame(sucesso_janela, bg="#f8f9fa", padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Dados exportados com sucesso!",
                  font=("Inter", 11), justify="center").pack(pady=10)
        ttk.Button(frame, text="OK", command=sucesso_janela.destroy,
                   bootstyle="success").pack()

    except Exception as e:
        # Janela de erro customizada
        mostrar_erro_toplevel(f"Falha ao exportar dados:\n{e}", app)


def importar_dados():
    caminho = filedialog.askopenfilename(
        title="Importar dados",
        filetypes=[("Arquivo JSON", "*.json")]
    )
    if not caminho:
        return

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = json.load(f)

        global dados, cartoes, contas_fixas_modelo, tipos_gasto, usuarios

        dados = {
            tuple(map(int, chave.split("-"))): valor
            for chave, valor in conteudo.get("dados", {}).items()
        }
        cartoes = conteudo.get("cartoes", [])
        contas_fixas_modelo = conteudo.get("contas_fixas_modelo", [])
        tipos_gasto = conteudo.get("tipos_gasto", TIPOS_GASTO_PADRAO.copy())
        usuarios = conteudo.get("usuarios", [])

        salvar_dados()
        atualizar_resumo()

        # Janela de sucesso customizada
        sucesso_janela = tk.Toplevel(app)
        sucesso_janela.title("Sucesso")
        sucesso_janela.resizable(False, False)
        largura, altura = 300, 120
        x = (app.winfo_screenwidth() // 2) - (largura // 2)
        y = (app.winfo_screenheight() // 2) - (altura // 2)
        sucesso_janela.geometry(f"{largura}x{altura}+{x}+{y}")
        sucesso_janela.grab_set()
        sucesso_janela.attributes("-topmost", True)
        sucesso_janela.configure(bg="#f8f9fa")
        aplicar_icone(sucesso_janela)

        frame = tk.Frame(sucesso_janela, bg="#f8f9fa", padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Dados importados com sucesso!",
                  font=("Inter", 11), justify="center").pack(pady=10)
        ttk.Button(frame, text="OK", command=sucesso_janela.destroy,
                   bootstyle="success").pack()

    except Exception as e:
        # Janela de erro customizada
        mostrar_erro_toplevel(f"Falha ao importar dados:\n{e}", app)


def trocar_usuario():
    global usuario_atual

    if not usuarios:
        show_info("Aviso", "Nenhum usuário cadastrado.", parent=app)
        return

    janela = tk.Toplevel(app)
    janela.title("Trocar Usuário")
    janela.resizable(False, False)
    centralizar_janela(janela, 320, 200)
    janela.grab_set()
    janela.attributes("-topmost", True)

    main_frame = tk.Frame(janela, padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="Selecione o usuário:",
              font=("Inter", 11)).pack(pady=10)

    combo = ttk.Combobox(main_frame, state="readonly",
                         values=usuarios, font=("Inter", 10))
    combo.pack(pady=8)

    if usuario_atual in usuarios:
        combo.current(usuarios.index(usuario_atual))
    else:
        combo.current(0)

    def mostrar_sucesso_toplevel(mensagem, parent, ao_fechar=None):
        sucesso_janela = tk.Toplevel(parent)
        sucesso_janela.title("Sucesso")
        sucesso_janela.geometry("300x120")
        sucesso_janela.attributes("-topmost", True)
        sucesso_janela.grab_set()
        sucesso_janela.configure(bg="#f8f9fa")

        if icone:
            sucesso_janela.iconphoto(False, icone)

        frame = tk.Frame(sucesso_janela, bg="#f8f9fa", padx=15, pady=15)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=mensagem, font=(
            "Inter", 10), wraplength=260).pack(pady=15)
        ttk.Button(
            frame,
            text="OK",
            command=lambda: [sucesso_janela.destroy(
            ), ao_fechar() if ao_fechar else None],
            bootstyle="success"
        ).pack()

        # Centralizar
        sucesso_janela.update_idletasks()
        w = sucesso_janela.winfo_width()
        h = sucesso_janela.winfo_height()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
        sucesso_janela.geometry(f"+{x}+{y}")

    def confirmar():
        global usuario_atual
        usuario_atual = combo.get()

        # Atualiza o texto do label de boas-vindas
        if 'label_bem_vindo' in globals():
            label_bem_vindo.config(text=f"Bem-vindo, {usuario_atual}!")

        # Mostrar mensagem de sucesso e só fechar a janela depois que o usuário clicar em OK
        mostrar_sucesso_toplevel(
            f"Usuário atual: {usuario_atual}",
            janela,
            ao_fechar=lambda: atualizar_resumo() or janela.destroy()
        )

    ttk.Button(main_frame, text="✓ Confirmar", command=confirmar,
               bootstyle="success").pack(pady=15)
    aplicar_icone(janela)


def gerenciar_usuarios():
    janela = tk.Toplevel(app)
    janela.title("Gerenciar Usuários")
    janela.resizable(False, False)
    centralizar_janela(janela, 400, 300)
    janela.grab_set()
    janela.attributes("-topmost", True)

    if icone:
        janela.iconphoto(False, icone)

    main_frame = tk.Frame(janela, padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="👥 Lista de Usuários",
              font=("Inter", 14, "bold")).pack(pady=(0, 10))

    lista_usuarios = tk.Listbox(main_frame, font=("Inter", 10), height=8,
                                selectbackground="#0d6efd", selectforeground="#ffffff")
    lista_usuarios.pack(pady=10, fill="both", expand=True)
    lista_usuarios.insert(tk.END, *usuarios)

    def adicionar():
        def salvar_novo_usuario():
            nome = entry_nome.get().strip()
            if not nome:
                show_warning("Atenção", "Digite um nome.",
                             parent=janela_adicionar)
                return
            if nome in usuarios:
                show_warning("Atenção", "Usuário já existe.",
                             parent=janela_adicionar)
                return

            usuarios.append(nome)
            lista_usuarios.insert(tk.END, nome)
            salvar_dados()
            janela_adicionar.destroy()

        janela_adicionar = tk.Toplevel(janela)
        janela_adicionar.title("Novo Usuário")
        janela_adicionar.resizable(False, False)
        centralizar_janela(janela_adicionar, 300, 150)
        janela_adicionar.grab_set()
        janela_adicionar.attributes("-topmost", True)
        janela_adicionar.focus_force()

        if icone:
            janela_adicionar.iconphoto(False, icone)

        frame = tk.Frame(janela_adicionar, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Nome do usuário:",
                 font=("Inter", 11)).pack(pady=(0, 8))
        entry_nome = ttk.Entry(frame, font=("Inter", 10))
        entry_nome.pack(pady=(0, 10))
        entry_nome.focus()
        entry_nome.bind("<Return>", lambda event: salvar_novo_usuario())

        ttk.Button(frame, text="💾 Salvar",
                   command=salvar_novo_usuario, bootstyle="success").pack()

    def excluir():
        idx = lista_usuarios.curselection()
        if not idx:
            show_warning(
                "Atenção", "Selecione um usuário para excluir.", parent=janela)
            return
        usuario = lista_usuarios.get(idx)

        def confirmar_exclusao():
            usuarios.remove(usuario)
            lista_usuarios.delete(idx)
            salvar_dados()
            confirm_janela.destroy()

        confirm_janela = tk.Toplevel(janela)
        confirm_janela.title("Confirmar Exclusão")
        confirm_janela.resizable(False, False)
        centralizar_janela(confirm_janela, 350, 150)
        confirm_janela.grab_set()
        confirm_janela.attributes("-topmost", True)
        confirm_janela.configure(bg="#f8f9fa")

        if icone:
            confirm_janela.iconphoto(False, icone)

        frame = tk.Frame(confirm_janela, bg="#f8f9fa", padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=f"Excluir usuário '{usuario}'?", wraplength=300,
                  font=("Inter", 11)).pack(pady=15)

        botoes = ttk.Frame(frame)
        botoes.pack(pady=5)

        ttk.Button(botoes, text="✓ Sim", command=confirmar_exclusao,
                   bootstyle="danger").pack(side="left", padx=10)
        ttk.Button(botoes, text="✗ Não", command=confirm_janela.destroy,
                   bootstyle="secondary").pack(side="right", padx=10)

    botoes = ttk.Frame(main_frame)
    botoes.pack(pady=10)
    ttk.Button(botoes, text="➕ Adicionar", command=adicionar,
               bootstyle="success").pack(side="left", padx=8)
    ttk.Button(botoes, text="🗑️ Excluir", command=excluir,
               bootstyle="danger").pack(side="right", padx=8)


# Chamada para montar o menu na inicialização
criar_menu()


# Ao fechar o app
def ao_fechar():
    salvar_dados()
    app.destroy()


app.protocol("WM_DELETE_WINDOW", ao_fechar)


# ----------------------Funções utilitarias-------------------------------
def get_chave(mes, ano):
    return (mes, ano)


def carregar_parcelas_cartao_para_mes(mes, ano):
    """Busca todas as parcelas de cartão que vencem neste mes/ano, mesmo que em meses anteriores ao início."""
    parcelas = []
    for chave, info in dados.items():
        for parcela in info.get("cartao_credito", []):
            if parcela.get("mes") == mes and parcela.get("ano") == ano:
                parcelas.append(parcela)
    return parcelas


def inicializar_mes(mes, ano):
    """Inicializa os dados do mês/ano se ainda não existirem."""
    chave = (mes, ano)
    if chave not in dados:
        dados[chave] = {
            "despesas_fixas": [],
            "gastos": [],
            "cartao_credito": [],
            "receitas": {},   # Agora é dict
            "conta": 0.0      # Saldo inicial
        }

        # adiciona apenas as despesas cujo início é <= mes/ano
        for desp in contas_fixas_modelo:
            inicio_mes, inicio_ano = desp["inicio"]
            if (inicio_ano < ano) or (inicio_ano == ano and inicio_mes <= mes):
                dados[chave]["despesas_fixas"].append(desp.copy())


def calcular_saldo(chave):
    info = dados[chave]
    total_receitas = sum(info["receitas"].values())
    total_despesas_pagas = sum(
        d["valor"] for d in info["despesas_fixas"] if d["status"] == "Pago")
    total_gastos = sum(g["valor"] for g in info["gastos"])
    total_credito_pago = sum(c["valor"] for c in info["cartao_credito"]
                             if c["mes"] == chave[0] and c["ano"] == chave[1] and c.get("status") == "Pago")
    return total_receitas - total_gastos - total_credito_pago - total_despesas_pagas


def recalcular_saldo_inicial(chave):
    """Recalcula o saldo inicial do mês/ano dado, considerando o início de uso."""
    if not inicio_uso:
        return

    mes, ano = chave
    inicio_mes, inicio_ano = inicio_uso

    # Se for antes do início de uso -> saldo zerado
    if (ano < inicio_ano) or (ano == inicio_ano and mes < inicio_mes):
        dados[chave]["conta"] = 0.0
        return

    # Se for exatamente o mês de início -> saldo inicial começa em zero
    if (ano == inicio_ano and mes == inicio_mes):
        dados[chave]["conta"] = 0.0
        return

    # Para meses após o início -> pega o saldo final do mês anterior
    mes_anterior, ano_anterior = (12, ano - 1) if mes == 1 else (mes - 1, ano)
    chave_anterior = (mes_anterior, ano_anterior)

    if chave_anterior in dados:
        saldo_anterior = calcular_saldo(chave_anterior)
        dados[chave]["conta"] = saldo_anterior
    else:
        dados[chave]["conta"] = 0.0


def recalcular_saldos_em_cadeia():
    """Recalcula todos os saldos desde o mês de início de uso até o mês atual."""
    if not inicio_uso:
        return

    mes_inicio, ano_inicio = inicio_uso
    mes_atual = combo_mes.current() + 1
    ano_atual = int(combo_ano.get())

    ano, mes = ano_inicio, mes_inicio

    # Percorre todos os meses do início até o mês atual
    while (ano < ano_atual) or (ano == ano_atual and mes <= mes_atual):
        chave = (mes, ano)
        inicializar_mes(mes, ano)
        recalcular_saldo_inicial(chave)

        # Avança para o próximo mês
        if mes == 12:
            mes = 1
            ano += 1
        else:
            mes += 1

    # Atualiza o resumo do app para refletir os novos saldos
    atualizar_resumo()


def atualizar_resumo(*args):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)

    if chave not in dados:
        inicializar_mes(mes, ano)
    else:
        recalcular_saldo_inicial(chave)

    info = dados[chave]

    # Usa .get() com valor padrão para evitar NoneType
    receitas_dict = info.get("receitas", {})
    despesas_fixas = info.get("despesas_fixas", [])
    gastos_diarios = info.get("gastos", [])
    cartoes = info.get("cartao_credito", [])

    total_receitas = sum(receitas_dict.values())
    total_despesas_fixas = sum(d["valor"] for d in despesas_fixas)
    total_gastos_diarios = sum(g["valor"] for g in gastos_diarios)
    total_cartao = sum(c["valor"] for c in cartoes)

    saldo_inicial = info.get("saldo_inicial", 0)
    saldo_final = saldo_inicial + total_receitas - \
        total_despesas_fixas - total_gastos_diarios - total_cartao

    # Limpar frames antes de atualizar
    for frame in [scroll_frame_receitas, scroll_frame_despesas, scroll_frame_gastos, scroll_frame_credito, frame_resumo]:
        for widget in frame.winfo_children():
            widget.destroy()

    def criar_cabecalho_com_detalhes(container, titulo, total, funcao_adicionar, funcao_detalhes):
        frame_topo = tk.Frame(container, bg="#0d6efd")
        frame_topo.pack(fill="x", pady=(0, 8))

        frame_header = tk.Frame(frame_topo, bg="#0d6efd")
        frame_header.pack(fill="x", pady=(0, 12))

        # Botão adicionar
        btn_adicionar = tk.Label(
            frame_header,
            text="➕",
            font=("Inter", 16, "bold"),
            fg="#28a745",
            bg="#0d6efd",
            cursor="hand2"
        )
        btn_adicionar.grid(row=0, column=0, sticky="w", padx=8)
        btn_adicionar.bind("<Button-1>", lambda e: funcao_adicionar())

        # Título
        label_titulo = tk.Label(
            frame_header,
            text=titulo,
            font=("Inter", 14, "bold"),
            fg="white",
            bg="#0d6efd",
            cursor="hand2"
        )
        label_titulo.grid(row=0, column=1, sticky="w", padx=(10, 0))
        label_titulo.bind("<Button-1>", lambda e: funcao_detalhes())

        # Total
        label_total = tk.Label(
            frame_header,
            text=f"R$ {locale.currency(total, grouping=True).replace('R$', '').strip()}",
            font=("Inter", 12, "bold"),
            fg="#198754",
            bg="#0d6efd"
        )
        label_total.grid(row=0, column=2, sticky="w", padx=(15, 0))

        frame_header.grid_columnconfigure(0, minsize=35)
        return frame_topo
    # ------------------ Atualizar Receitas ------------------
    # Limpa os itens antigos dentro do scroll_frame
    for widget in scroll_frame_receitas.winfo_children():
        widget.destroy()

    # Botão adicionar receita
    btn_adicionar = tk.Label(
        scroll_frame_receitas,
        text="➕",
        font=("Inter", 16, "bold"),
        fg="#28a745",
        bg="#e6ffea",
        cursor="hand2"
    )
    btn_adicionar.pack(anchor="w", pady=(0, 10))
    btn_adicionar.bind(
        "<Button-1>", lambda e: adicionar_valor("Adicionar Receita", "receita"))

    # Adiciona as receitas existentes
    for nome, valor in receitas_dict.items():
        frame_linha = tk.Frame(scroll_frame_receitas, bg="#e6ffea")
        frame_linha.pack(fill="x", pady=3)

        label_receita = tk.Label(
            frame_linha,
            text=f"{nome}: {locale.currency(valor, grouping=True)}",
            font=("Inter", 12, "bold"),
            bg="#e6ffea"
        )

        # ---------------- Regras de cor originais ----------------
        # Substitua abaixo pela sua lógica exata, se tiver mais critérios
        if valor >= 1000:        # exemplo simples de cor
            cor = "#28a745"
        else:
            cor = "#28a745"
        label_receita.configure(fg=cor)
        label_receita.pack(side="left", anchor="w")

        # Botão editar
        btn_editar = tk.Label(frame_linha, text="✏️", font=("Inter", 14, "bold"),
                              fg="white", bg="#e6ffea", cursor="hand2")
        btn_editar.pack(side="right", padx=5)
        btn_editar.bind("<Button-1>", lambda e, n=nome: editar_receita(n))

        # Botão excluir
        btn_excluir = tk.Label(frame_linha, text="🗑️", font=("Inter", 14, "bold"),
                               fg="#dc3545", bg="#e6ffea", cursor="hand2")
        btn_excluir.pack(side="right", padx=5)
        btn_excluir.bind("<Button-1>", lambda e, n=nome: excluir_receita(n))

    # Atualiza o total do card
    lbl_receitas.config(
        text=f"R$ {locale.currency(total_receitas, grouping=True).replace('R$', '').strip()}")

    # ------------------ Atualizar Despesas Fixas ------------------
    # Limpa os itens antigos dentro do scroll_frame
    for widget in scroll_frame_despesas.winfo_children():
        widget.destroy()

    # Botão adicionar despesa fixa
    btn_adicionar = tk.Label(
        scroll_frame_despesas,
        text="➕",
        font=("Inter", 16, "bold"),
        fg="#28a745",
        bg="#ffe6e6",
        cursor="hand2"
    )
    btn_adicionar.pack(anchor="w", pady=(0, 10))
    btn_adicionar.bind("<Button-1>", lambda e: adicionar_despesa_fixa())

    # Ordena despesas pelo vencimento
    despesas_ordenadas = sorted(
        enumerate(despesas_fixas),
        key=lambda x: x[1].get("vencimento", 99)
    )

    from calendar import monthrange
    hoje = datetime.today()
    ultimo_dia_mes = monthrange(ano, mes)[1]

    # Adiciona cada despesa fixa
    for original_idx, d in despesas_ordenadas:
        vencimento = d.get("vencimento", "??")
        status = d.get("status", "Aberto")

        # ---------------- Regras de cor ----------------
        if status == "Pago":
            cor = "#28a745"
        elif status == "Aberto":
            if isinstance(vencimento, int):
                venc_data = datetime(ano, mes, min(vencimento, ultimo_dia_mes))
                cor = "#dc3545" if venc_data < hoje else "#0d6efd"
            else:
                cor = "#0d6efd"
        else:
            cor = "#212529"

        texto = f"{d.get('descricao', '')} - {locale.currency(d['valor'], grouping=True)} - Venc: {vencimento} ({status})"

        container = tk.Frame(scroll_frame_despesas, bg="#ffe6e6")
        container.pack(fill="x", pady=3)

        # Botão editar
        btn_editar = tk.Label(container, text="✏️", font=("Inter", 14, "bold"),
                              fg="white", bg="#ffe6e6", cursor="hand2")
        btn_editar.pack(side="left", padx=(0, 10))
        btn_editar.bind("<Button-1>", lambda e,
                        i=original_idx: editar_despesa_fixa(i))

        # Botão excluir
        btn_excluir = tk.Label(container, text="🗑️", font=("Inter", 14, "bold"),
                               fg="#dc3545", bg="#ffe6e6", cursor="hand2")
        btn_excluir.pack(side="left", padx=(0, 10))
        btn_excluir.bind("<Button-1>", lambda e,
                         i=original_idx: excluir_despesa_fixa(i))

        # Label da despesa com cor dinâmica
        label_despesa = tk.Label(container, text=texto, font=(
            "Inter", 12, "bold"), bg="#ffe6e6")
        label_despesa.configure(fg=cor)
        label_despesa.pack(side="left", anchor="w")

    # Atualiza o total do card
    lbl_despesas.config(
        text=f"R$ {locale.currency(total_despesas_fixas, grouping=True).replace('R$', '').strip()}")
    # --- GASTOS DIÁRIOS ---
    total_gastos = sum(g["valor"] for g in gastos_diarios)
    for widget in scroll_frame_gastos.winfo_children():
        widget.destroy()

    # Frame clicável com lupa para abrir detalhes da seção
    frame_gastos_clicavel = tk.Frame(
        scroll_frame_gastos, bg="#e6f0ff", cursor="hand2")
    frame_gastos_clicavel.pack(fill="x", pady=(0, 5))
    frame_gastos_clicavel.bind(
        "<Button-1>", lambda e: mostrar_gastos_detalhados())

    # Ícone lupa
    lbl_lupa = tk.Label(
        frame_gastos_clicavel,
        text="🔍",
        font=("Inter", 16, "bold"),
        bg="#e6f0ff",
        cursor="hand2"
    )
    lbl_lupa.pack(side="left", padx=5, pady=5)
    lbl_lupa.bind("<Button-1>", lambda e: mostrar_gastos_detalhados())

    # Botão adicionar
    btn_adicionar = tk.Label(
        frame_gastos_clicavel,
        text="➕",
        font=("Inter", 16, "bold"),
        fg="#28a745",
        bg="#e6f0ff",
        cursor="hand2"
    )
    btn_adicionar.pack(side="left", padx=5, pady=5)
    btn_adicionar.bind(
        "<Button-1>", lambda e: adicionar_valor("Adicionar Gasto", "gasto"))

    # --- CARTÃO DE CRÉDITO ---
    gastos_por_cartao = {}
    for c in cartoes:
        nome = c.get("cartao", "Cartão")
        gastos_por_cartao.setdefault(nome, []).append(c)

    def cartao_pago(lista_gastos_cartao):
        return all(g.get("status") == "Pago" for g in lista_gastos_cartao)

    total_cartao_pago = 0
    total_cartao_todos = 0
    for nome_cartao, lista_gastos_cartao in gastos_por_cartao.items():
        total_gastos_cartao = sum(g["valor"] for g in lista_gastos_cartao)
        total_cartao_todos += total_gastos_cartao
        if cartao_pago(lista_gastos_cartao):
            total_cartao_pago += total_gastos_cartao

    for widget in scroll_frame_credito.winfo_children():
        widget.destroy()

    # Frame clicável com lupa para abrir detalhes do cartão
    frame_credito_clicavel = tk.Frame(
        scroll_frame_credito, bg="#f2e6ff", cursor="hand2")
    frame_credito_clicavel.pack(fill="x", pady=(0, 5))
    frame_credito_clicavel.bind(
        "<Button-1>", lambda e: abrir_cartao_credito_detalhado())

    # Ícone lupa
    lbl_lupa_credito = tk.Label(
        frame_credito_clicavel,
        text="🔍",
        font=("Inter", 16, "bold"),
        bg="#f2e6ff",
        cursor="hand2"
    )
    lbl_lupa_credito.pack(side="left", padx=5, pady=5)
    lbl_lupa_credito.bind(
        "<Button-1>", lambda e: abrir_cartao_credito_detalhado())

    # Botão adicionar
    btn_adicionar = tk.Label(
        frame_credito_clicavel,
        text="➕",
        font=("Inter", 16, "bold"),
        fg="#28a745",
        bg="#f2e6ff",
        cursor="hand2"
    )
    btn_adicionar.pack(side="left", padx=5, pady=5)
    btn_adicionar.bind("<Button-1>", lambda e: adicionar_cartao_credito())

    # --- RESUMO ---
    # Saldo final do mês anterior
    if (mes, ano) == inicio_uso:
        saldo_final_ant = 0
    else:
        mes_ant, ano_ant = (12, ano - 1) if mes == 1 else (mes - 1, ano)
        chave_ant = (mes_ant, ano_ant)

        if chave_ant in dados:
            info_ant = dados[chave_ant]
            receitas_ant = sum(info_ant.get("receitas", {}).values())
            despesas_ant = sum(d["valor"]
                               for d in info_ant.get("despesas_fixas", []))
            gastos_ant = sum(g["valor"] for g in info_ant.get("gastos", []))
            cartao_ant = sum(c["valor"]
                             for c in info_ant.get("cartao_credito", []))
            saldo_inicial_ant = info_ant.get("saldo_inicial", 0)
            saldo_final_ant = saldo_inicial_ant + receitas_ant - \
                despesas_ant - gastos_ant - cartao_ant
        else:
            saldo_final_ant = 0

    # Despesas pagas
    total_pagas = sum(d["valor"] for d in despesas_fixas if d.get("status") == "Pago") \
        + sum(c["valor"] for c in cartoes if c.get("status") == "Pago") \
        + sum(g["valor"] for g in gastos_diarios)

    # Todas as despesas
    total_todas = sum(d["valor"] for d in despesas_fixas) \
        + sum(c["valor"] for c in cartoes) \
        + sum(g["valor"] for g in gastos_diarios)

    # Calcula saldo inicial e saldo final
    saldo_inicial = saldo_final_ant + total_receitas - total_pagas
    saldo_final = saldo_final_ant + total_receitas - total_todas

    # Define cores
    cor_saldo_atual = "#0d6efd" if saldo_inicial >= 0 else "#dc3545"
    cor_saldo_final = "#0d6efd" if saldo_final >= 0 else "#dc3545"

    resumo_container = tk.Frame(frame_resumo, bg="#d9e3f1", padx=0, pady=0)
    resumo_container.pack(fill="x", pady=0)

    label_saldo_atual = tk.Label(resumo_container,
                                 text=f"💰 Saldo Atual: {locale.currency(saldo_inicial, grouping=True)}",
                                 font=("Inter", 12, "bold"),
                                 bg="#d9e3f1")
    label_saldo_atual.configure(fg=cor_saldo_atual)
    label_saldo_atual.pack(anchor="w")

    label_saldo_final = tk.Label(resumo_container,
                                 text=f"📊 Saldo Final: {locale.currency(saldo_final, grouping=True)}",
                                 font=("Inter", 12, "bold"),
                                 bg="#d9e3f1")
    label_saldo_final.configure(fg=cor_saldo_final)
    label_saldo_final.pack(anchor="w", pady=(2.5, 0))

    # --- Gastos finais (diários + cartão) por tipo ---
    gastos_por_tipo = {}
    for g in gastos_diarios:
        tipo = g.get("tipo", "Outros")
        gastos_por_tipo[tipo] = gastos_por_tipo.get(
            tipo, 0) + g.get("valor", 0)

    for c in cartoes:
        tipo = c.get("tipo", "Outros")
        gastos_por_tipo[tipo] = gastos_por_tipo.get(
            tipo, 0) + c.get("valor", 0)

    label_gastos_tipo = tk.Label(
        resumo_container,
        text="📈 Gastos por Tipo:",
        font=("Inter", 12, "bold"),
        bg="#d9e3f1",
        fg="#0d6efd"
    )
    label_gastos_tipo.pack(anchor="w", pady=(5, 5))

    # Frame com altura fixa para limitar o espaço
    frame_gastos_tipo = tk.Frame(
        resumo_container, bg="#d9e3f1", height=60)  # altura fixa
    frame_gastos_tipo.pack(fill="x", anchor="w")
    # impede que o frame aumente automaticamente
    frame_gastos_tipo.pack_propagate(False)

    tipos = sorted(gastos_por_tipo.items(), key=lambda x: x[0])
    max_por_linha = (len(tipos) + 1) // 2  # até 2 linhas

    for linha in range(2):
        frame_linha = tk.Frame(frame_gastos_tipo, bg="#d9e3f1")
        frame_linha.pack(anchor="w", pady=2)
        for idx in range(linha * max_por_linha, min((linha + 1) * max_por_linha, len(tipos))):
            tipo, valor = tipos[idx]
            cor = "#0d6efd" if valor >= 0 else "#dc3545"
            lbl = tk.Label(
                frame_linha,
                text=f"{tipo}: {locale.currency(valor, grouping=True)}",
                font=("Inter", 11, "bold"),
                bg="#d9e3f1",
                fg=cor,
                padx=10
            )
            lbl.pack(side="left", anchor="w")

    # Atualiza os totais nos cards
    lbl_receitas.config(
        text=f"R$ {locale.currency(total_receitas, grouping=True).replace('R$', '').strip()}")
    lbl_despesas.config(
        text=f"R$ {locale.currency(total_despesas_fixas, grouping=True).replace('R$', '').strip()}")
    lbl_gastos.config(
        text=f"R$ {locale.currency(total_gastos_diarios, grouping=True).replace('R$', '').strip()}")
    lbl_credito.config(
        text=f"R$ {locale.currency(total_cartao, grouping=True).replace('R$', '').strip()}")


def excluir_despesa_fixa(idx):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave_atual = get_chave(mes, ano)

    if chave_atual not in dados:
        return

    try:
        descricao_target = dados[chave_atual]["despesas_fixas"][idx]["descricao"]
    except IndexError:
        return

    # Janela de confirmação personalizada
    confirm_janela = tk.Toplevel(app)
    confirm_janela.title("Confirmação")
    largura, altura = 400, 180
    x = (confirm_janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (confirm_janela.winfo_screenheight() // 2) - (altura // 2)
    confirm_janela.geometry(f"{largura}x{altura}+{x}+{y}")
    confirm_janela.attributes("-topmost", True)
    confirm_janela.grab_set()
    aplicar_icone(confirm_janela)

    frame = tk.Frame(confirm_janela, padx=20, pady=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text=f"Deseja realmente excluir a despesa fixa '{descricao_target}' a partir de {mes:02d}/{ano}?",
              font=("Inter", 11), wraplength=360, justify="center").pack(pady=15)

    def confirmar():
        for ano_loop in range(ano, 2101):
            for mes_loop in range(1, 13):
                if ano_loop == ano and mes_loop < mes:
                    continue
                chave = get_chave(mes_loop, ano_loop)
                if chave in dados:
                    dados[chave]["despesas_fixas"] = [
                        d for d in dados[chave]["despesas_fixas"]
                        if d.get("descricao") != descricao_target
                    ]
        atualizar_resumo()
        confirm_janela.destroy()

    botoes = tk.Frame(frame)
    botoes.pack()
    ttk.Button(botoes, text="✓ Sim", command=confirmar,
               bootstyle="danger").pack(side="left", padx=10)
    ttk.Button(botoes, text="✗ Não", command=confirm_janela.destroy,
               bootstyle="secondary").pack(side="right", padx=10)

    # --- GASTOS DIÁRIOS ---
    total_gastos = sum(g["valor"] for g in gastos_diarios)
    criar_cabecalho_com_detalhes(
        scroll_frame_gastos,
        "Gastos Diários",
        total_gastos,
        lambda: adicionar_valor("Adicionar Gasto", "gasto"),
        mostrar_gastos_detalhados
    )

    # --- CARTÃO DE CRÉDITO ---
    gastos_por_cartao = {}
    for c in cartoes:
        nome = c.get("cartao", "Cartão")
        gastos_por_cartao.setdefault(nome, []).append(c)

    def cartao_pago(lista_gastos_cartao):
        return all(g.get("status") == "Pago" for g in lista_gastos_cartao)

    total_cartao_pago = 0
    total_cartao_todos = 0
    for nome_cartao, lista_gastos_cartao in gastos_por_cartao.items():
        total_gastos_cartao = sum(g["valor"] for g in lista_gastos_cartao)
        total_cartao_todos += total_gastos_cartao
        if cartao_pago(lista_gastos_cartao):
            total_cartao_pago += total_gastos_cartao

    criar_cabecalho_com_detalhes(
        scroll_frame_credito,
        "Cartão de Crédito",
        total_cartao_todos,
        adicionar_cartao_credito,
        abrir_cartao_credito_detalhado
    )

    # --- RESUMO ---
    resumo_container = tk.Frame(frame_resumo, bg="#d9e3f1", padx=12, pady=8)
    resumo_container.pack(fill="x", pady=(0, 5))

    label_saldo_atual = tk.Label(
        resumo_container,
        text=f"💰 Saldo Atual: {locale.currency(saldo_atual, grouping=True)}",
        font=("Inter", 12, "bold"),
        bg="#d9e3f1",
        fg=cor_saldo_atual
    )
    label_saldo_atual.pack(anchor="w", pady=(0, 2))

    label_saldo_final = tk.Label(
        resumo_container,
        text=f"📊 Saldo Final: {locale.currency(saldo_final, grouping=True)}",
        font=("Inter", 12, "bold"),
        bg="#d9e3f1",
        fg=cor_saldo_final
    )
    label_saldo_final.pack(anchor="w", pady=(0, 2))

    # --- Gastos finais (diários + cartão) por tipo ---
    gastos_por_tipo = {}
    for g in gastos_diarios:
        tipo = g.get("tipo", "Outros")
        gastos_por_tipo[tipo] = gastos_por_tipo.get(
            tipo, 0) + g.get("valor", 0)

    for c in cartoes:
        tipo = c.get("tipo", "Outros")
        gastos_por_tipo[tipo] = gastos_por_tipo.get(
            tipo, 0) + c.get("valor", 0)

    label_gastos_tipo = tk.Label(
        resumo_container,
        text="📈 Gastos por Tipo:",
        font=("Inter", 12, "bold"),
        bg="#d9e3f1",
        fg="#0d6efd"
    )
    label_gastos_tipo.pack(anchor="w", pady=(15, 5))

    tipos = sorted(gastos_por_tipo.items(), key=lambda x: x[0])
    max_por_linha = (len(tipos) + 1) // 2  # até 2 linhas

    for linha in range(2):
        frame_linha = tk.Frame(resumo_container, bg="#d9e3f1")
        frame_linha.pack(anchor="w", pady=2)
        for idx in range(linha * max_por_linha, min((linha + 1) * max_por_linha, len(tipos))):
            tipo, valor = tipos[idx]
            cor = "#0d6efd" if valor >= 0 else "#dc3545"
            lbl = tk.Label(
                frame_linha,
                text=f"{tipo}: {locale.currency(valor, grouping=True)}",
                font=("Inter", 11, "bold"),
                bg="#d9e3f1",
                fg=cor,
                padx=10
            )
            lbl.pack(side="left", anchor="w")


def criar_resumo_simples(container, titulo, total, comando_abrir):
    frame = ttk.Frame(container)
    frame.pack(fill="x", pady=8)

    label = ttk.Label(
        frame,
        text=f"{titulo}: {locale.currency(total, grouping=True)} ▶",
        font=("Inter", 13, "bold"),
        foreground="#0d6efd",
        cursor="hand2"
    )
    label.pack(side="left", anchor="w")
    label.bind("<Button-1>", lambda e: comando_abrir())


def atualizar_tipo_gasto_combo(combobox):
    combobox["values"] = tipos_gasto
    if tipos_gasto:
        combobox.set(tipos_gasto[0])


def mostrar_erro_toplevel(mensagem, parent):
    erro_janela = tk.Toplevel(parent)
    erro_janela.title("Erro")
    erro_janela.geometry("350x120")
    erro_janela.attributes("-topmost", True)
    erro_janela.grab_set()

    erro_frame = tk.Frame(erro_janela, padx=15, pady=15)
    erro_frame.pack(fill="both", expand=True)

    ttk.Label(erro_frame, text=mensagem, foreground="#dc3545", wraplength=320,
              font=("Inter", 10)).pack(pady=10)
    ttk.Button(erro_frame, text="OK", command=erro_janela.destroy,
               bootstyle="danger").pack()

    erro_janela.update_idletasks()
    w = erro_janela.winfo_width()
    h = erro_janela.winfo_height()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
    erro_janela.geometry(f"+{x}+{y}")
    aplicar_icone(erro_janela)

# ----------------------Gastos detalhados-------------------------------


def _renderizar_gastos(container, recarregar_callback=None, janela_detalhes=None):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)
    info = dados[chave]

    # Ordena os gastos por dia, tipo e descrição
    gastos_ordenados = sorted(
        enumerate(info["gastos"]),
        key=lambda x: (x[1].get("dia", 99), x[1].get(
            "tipo", ""), x[1].get("descricao", ""))
    )

    # Agrupa por dia
    gastos_por_dia = defaultdict(list)
    for idx, gasto in gastos_ordenados:
        dia = gasto.get("dia", "??")
        gastos_por_dia[dia].append((idx, gasto))

    def toggle_detalhes_gastos(f, dia_local):
        if f.winfo_ismapped():
            f.pack_forget()
            estado_expansao_gastos_diarios[dia_local] = False
        else:
            f.pack(fill="x", padx=12, pady=(8, 12))
            estado_expansao_gastos_diarios[dia_local] = True

    # Renderiza cada dia
    for dia in sorted(gastos_por_dia):
        lista = gastos_por_dia[dia]

        container_dia = ttk.Frame(container)
        container_dia.pack(fill="x", pady=(8, 0))

        label_dia = ttk.Label(
            container_dia,
            text=f"📅 Dia {int(dia):02d}",
            foreground="#0d6efd",
            font=("Inter", 12, "bold"),
            cursor="hand2"
        )
        label_dia.pack(anchor="w", fill="x", pady=(0, 5))

        frame_detalhes = ttk.Frame(container_dia, padding=(18, 8))

        # Agrupa por tipo de gasto
        gastos_por_tipo = defaultdict(list)
        for idx, gasto in lista:
            tipo = gasto.get("tipo", "Indefinido")
            gastos_por_tipo[tipo].append((idx, gasto))

        # Renderiza cada tipo de gasto
        for tipo, gastos_lista in sorted(gastos_por_tipo.items()):
            label_tipo = ttk.Label(
                frame_detalhes,
                text=f"🏷️ {tipo}:",
                font=("Inter", 11, "bold"),
                foreground="#495057"
            )
            label_tipo.pack(anchor="w", padx=12, pady=(8, 3))

            # Renderiza cada gasto do tipo
            for idx, gasto in gastos_lista:
                valor_fmt = locale.currency(gasto["valor"], grouping=True)
                desc = gasto.get("descricao", "Sem descrição")
                usuario = gasto.get("usuario", "Desconhecido")
                gasto_text = f"• {desc}: {valor_fmt} (Responsável: {usuario})"

                container_gasto = ttk.Frame(frame_detalhes)
                container_gasto.pack(anchor="w", fill="x", padx=35, pady=3)

                ttk.Label(
                    container_gasto,
                    text=gasto_text,
                    font=("Inter", 10),
                    foreground="#212529"
                ).pack(side="left")

                # Botão editar
                btn_editar = ttk.Label(
                    container_gasto,
                    text="✏️",
                    font=("Inter", 12),
                    foreground="#0d6efd",
                    cursor="hand2"
                )
                btn_editar.pack(side="left", padx=10)
                btn_editar.bind(
                    "<Button-1>",
                    lambda e, i=idx: editar_gasto_diario(
                        i, callback_apos_salvar=recarregar_callback)
                )

                # Botão excluir
                btn_excluir = ttk.Label(
                    container_gasto,
                    text="🗑️",
                    font=("Inter", 12),
                    foreground="#dc3545",
                    cursor="hand2"
                )
                btn_excluir.pack(side="left")
                btn_excluir.bind(
                    "<Button-1>",
                    lambda e, i=idx: excluir_gasto_diario(
                        i,
                        janela_detalhes=janela_detalhes,
                        callback_apos_excluir=recarregar_callback
                    )
                )

        # Expansão/colapso dos dias
        label_dia.bind(
            "<Button-1>",
            lambda e, f=frame_detalhes, d=dia: toggle_detalhes_gastos(f, d)
        )
        if estado_expansao_gastos_diarios.get(dia):
            frame_detalhes.pack(fill="x", padx=12, pady=(8, 12))


def mostrar_gastos_detalhados():
    global estado_expansao_gastos_diarios
    estado_expansao_gastos_diarios = defaultdict(bool)

    nova_janela = tk.Toplevel(app)
    nova_janela.title("💳 Gastos Diários Detalhados")

    largura = 850
    altura = 750
    x = (nova_janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (nova_janela.winfo_screenheight() // 2) - (altura // 2)
    nova_janela.geometry(f"{largura}x{altura}+{x}+{y}")

    # Header da janela
    header_frame = tk.Frame(nova_janela, height=60)
    header_frame.pack(side="top", fill="x", pady=(0, 5))
    header_frame.pack_propagate(False)

    frame_centro = ttk.Frame(header_frame)
    frame_centro.pack(expand=True)

    # Container que vai receber os gastos (dentro de um canvas com scroll)
    frame_container = ttk.Frame()

    def recarregar_gastos():
        for widget in frame_container.winfo_children():
            widget.destroy()
        _renderizar_gastos(
            container=frame_container,
            recarregar_callback=recarregar_gastos,
            janela_detalhes=nova_janela
        )

    # Botão adicionar gasto
    btn_adicionar = ttk.Button(
        frame_centro,
        text="➕ Adicionar Gasto Diário",
        command=lambda: adicionar_valor(
            "Adicionar Gasto", "gasto",
            callback_apos_salvar=recarregar_gastos
        ),
        bootstyle="success"
    )
    btn_adicionar.pack(pady=15)

    # Scroll
    canvas = tk.Canvas(nova_janela, highlightthickness=0)
    scrollbar = ttk.Scrollbar(
        nova_janela, orient="vertical", command=canvas.yview)
    frame_container = ttk.Frame(canvas)

    canvas.create_window((0, 0), window=frame_container, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    frame_container.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    # Rolagem do mouse
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # Render inicial
    recarregar_gastos()

    aplicar_icone(nova_janela)


def marcar_cartao_como_pago(nome_cartao):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)
    info = dados[chave]

    for gasto in info["cartao_credito"]:
        if gasto["cartao"] == nome_cartao and gasto["mes"] == mes and gasto["ano"] == ano:
            gasto["status"] = "Pago"  # Marca o gasto como pago

    salvar_dados()
    atualizar_resumo()


def _renderizar_gastos_cartao(scroll_frame, parent_janela=None, recarregar_callback=None):

    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)
    info = dados[chave]

    global estado_expansao_cartoes
    if "estado_expansao_cartoes" not in globals():
        estado_expansao_cartoes = {}

    # Limpa o container antes de renderizar
    for w in scroll_frame.winfo_children():
        w.destroy()

    gastos_por_cartao = {}
    for g in info["cartao_credito"]:
        nome = g["cartao"]
        gastos_por_cartao.setdefault(nome, []).append(g)

    def criar_badge_status(parent, status, callback):
        cores = {
            "Pago": ("#28a745", "#218838"),
            "Aberto": ("#dc3545", "#c82333")
        }
        cor_fundo, cor_hover = cores.get(status, ("#6c757d", "#5a6268"))
        texto = "✔ Pago" if status == "Pago" else "⏳ Aberto"

        try:
            bg = parent.cget("background")
        except tk.TclError:
            bg = parent.winfo_toplevel().cget("background")

        canvas = tk.Canvas(parent, width=100, height=32, highlightthickness=0)

        raio = 12
        x0, y0, x1, y1 = 2, 2, 98, 30

        def ret_arredondado(c, x0, y0, x1, y1, r, fill):
            c.create_arc(x0, y0, x0+2*r, y0+2*r, start=90,
                         extent=90, fill=fill, outline=fill)
            c.create_arc(x1-2*r, y0, x1, y0+2*r, start=0,
                         extent=90, fill=fill, outline=fill)
            c.create_arc(x0, y1-2*r, x0+2*r, y1, start=180,
                         extent=90, fill=fill, outline=fill)
            c.create_arc(x1-2*r, y1-2*r, x1, y1, start=270,
                         extent=90, fill=fill, outline=fill)
            c.create_rectangle(x0+r, y0, x1-r, y1, fill=fill, outline=fill)
            c.create_rectangle(x0, y0+r, x1, y1-r, fill=fill, outline=fill)

        def desenhar(cor):
            canvas.delete("all")
            ret_arredondado(canvas, x0, y0, x1, y1, raio, cor)
            canvas.create_text((x0+x1)//2, (y0+y1)//2, text=texto, fill="white",
                               font=("Inter", 10, "bold"))

        desenhar(cor_fundo)

        def on_enter(e):
            desenhar(cor_hover)

        def on_leave(e):
            desenhar(cor_fundo)

        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        canvas.bind("<Button-1>", lambda e: callback())
        canvas.config(cursor="hand2")

        return canvas

    def toggle_detalhes(frame, label_widget, nome_cartao, total):
        if frame.winfo_ismapped():
            frame.pack_forget()
            label_widget.config(
                text=f"💳 {nome_cartao}: {locale.currency(total, grouping=True)} ▶",
                foreground="#0d6efd",
                font=("Inter", 13, "bold"),
                cursor="hand2"
            )
            estado_expansao_cartoes[nome_cartao] = False
        else:
            frame.pack(fill="x", padx=25, pady=(0, 12))
            label_widget.config(
                text=f"💳 {nome_cartao}: {locale.currency(total, grouping=True)} ▼",
                foreground="#0d6efd",
                font=("Inter", 13, "bold"),
                cursor="hand2"
            )
            estado_expansao_cartoes[nome_cartao] = True

    def alternar_status_cartao(nome_cartao_local):
        mes_atual = combo_mes.current() + 1
        ano_atual = int(combo_ano.get())
        chave_atual = get_chave(mes_atual, ano_atual)
        info_atual = dados[chave_atual]

        lista_gastos = [g for g in info_atual["cartao_credito"]
                        if g["cartao"] == nome_cartao_local]

        novo_status = "Aberto" if all(
            g.get("status") == "Pago" for g in lista_gastos) else "Pago"

        for g in lista_gastos:
            g["status"] = novo_status

        salvar_dados()
        atualizar_resumo()
        _renderizar_gastos_cartao(
            scroll_frame, parent_janela=parent_janela, recarregar_callback=recarregar_callback)

    def recarregar_gastos():
        _renderizar_gastos_cartao(
            scroll_frame, parent_janela=parent_janela, recarregar_callback=recarregar_callback)

    for nome_cartao in sorted(gastos_por_cartao):
        lista = sorted(gastos_por_cartao[nome_cartao], key=lambda x: (
            x["ano"], x["mes"], x["dia"]))
        total_cartao = sum(g["valor"] for g in lista)

        status_cartao = "Pago" if all(
            g.get("status") == "Pago" for g in lista) else "Aberto"

        container_cartao = ttk.Frame(scroll_frame)
        container_cartao.pack(fill="x", padx=12, pady=(10, 0))

        frame_titulo = ttk.Frame(container_cartao)
        frame_titulo.pack(fill="x", padx=0)

        frame_titulo.columnconfigure(0, weight=1)

        label = ttk.Label(
            frame_titulo,
            text=f"💳 {nome_cartao}: {locale.currency(total_cartao, grouping=True)}",
            foreground="#0d6efd",
            font=("Inter", 13, "bold"),
            cursor="hand2"
        )
        label.grid(row=0, column=0, sticky="we")

        badge = criar_badge_status(frame_titulo, status_cartao, partial(
            alternar_status_cartao, nome_cartao))
        badge.grid(row=0, column=1, sticky="e", padx=(2, 0))

        label.bind("<Enter>", lambda e: label.config(foreground="#0a58ca"))
        label.bind("<Leave>", lambda e: label.config(foreground="#0d6efd"))

        frame_detalhes = ttk.Frame(container_cartao, padding=(12, 8))

        label.bind(
            "<Button-1>",
            lambda e, f=frame_detalhes, l=label, n=nome_cartao, t=total_cartao: toggle_detalhes(
                f, l, n, t)
        )

        for c in lista:
            parcela = "Fixo" if c.get("fixo") else (
                f"Parcela {c['parcela_atual']}/{c['total_parcelas']}" if c["total_parcelas"] > 1 else "À vista")
            data = f"{c['dia']:02d}/{c['mes']:02d}/{c['ano']}"
            tipo = c.get("tipo", "Indefinido")
            valor_fmt = locale.currency(c["valor"], grouping=True)
            texto = f"• {data}: {c['descricao']} - {valor_fmt} ({parcela}) - Tipo: {tipo}"

            container = ttk.Frame(frame_detalhes)
            container.pack(anchor="w", fill="x", padx=12, pady=3)

            ttk.Label(container, text=texto, font=(
                "Inter", 10, "bold")).pack(side="left")

            btn_editar = ttk.Label(container, text="✏️", font=(
                "Inter", 12), foreground="#0d6efd", cursor="hand2")
            btn_editar.pack(side="left", padx=10)
            btn_editar.bind("<Button-1>", partial(lambda e, gasto: editar_gasto_cartao(
                gasto, callback_apos_salvar=recarregar_callback), gasto=c))

            btn_excluir = ttk.Label(container, text="🗑️", font=(
                "Inter", 12), foreground="#dc3545", cursor="hand2")
            btn_excluir.pack(side="left")
            btn_excluir.bind("<Button-1>", partial(lambda e, gasto: excluir_gasto_cartao(
                gasto, parent_janela=parent_janela, callback_apos_excluir=recarregar_gastos), gasto=c))

        if estado_expansao_cartoes.get(nome_cartao):
            frame_detalhes.pack(fill="x", padx=25, pady=(0, 12))


def abrir_cartao_credito_detalhado():
    global janela_gastos_detalhados
    janela_gastos_detalhados = tk.Toplevel(app)
    janela_gastos_detalhados.title("💳 Cartões de Crédito Detalhados")

    largura, altura = 850, 750
    x = (janela_gastos_detalhados.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela_gastos_detalhados.winfo_screenheight() // 2) - (altura // 2)
    janela_gastos_detalhados.geometry(f"{largura}x{altura}+{x}+{y}")

    # Header da janela
    header_frame = tk.Frame(janela_gastos_detalhados, height=60)
    header_frame.pack(side="top", fill="x", pady=(0, 5))
    header_frame.pack_propagate(False)

    btn_adicionar = ttk.Button(
        header_frame,
        text="➕ Adicionar Gasto no Cartão",
        command=lambda: adicionar_cartao_credito(
            callback_apos_salvar=recarregar_gastos),
        bootstyle="success"
    )
    btn_adicionar.pack(pady=15)

    container = ttk.Frame(janela_gastos_detalhados, padding=18)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container, highlightthickness=0)
    scrollbar = ttk.Scrollbar(
        container, orient="vertical", command=canvas.yview)
    scroll_frame = ttk.Frame(canvas)

    # Atualiza a região de rolagem sempre que o conteúdo mudar
    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Função que recarrega os gastos na janela
    def recarregar_gastos():
        _renderizar_gastos_cartao(
            scroll_frame, parent_janela=janela_gastos_detalhados, recarregar_callback=recarregar_gastos)

    # Funções para rolagem com mouse wheel compatível Windows/Linux/Mac
    def _on_mousewheel(event):
        if event.delta:
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        elif event.num == 4:
            canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            canvas.yview_scroll(1, "units")

    def _bind_mousewheel(event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)

    def _unbind_mousewheel(event):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

    canvas.bind("<Enter>", _bind_mousewheel)
    canvas.bind("<Leave>", _unbind_mousewheel)

    # Carrega a lista inicial de gastos
    recarregar_gastos()
    aplicar_icone(janela_gastos_detalhados)

# ----------------------Funções adicionar-------------------------------


def adicionar_despesa_fixa():
    """Adiciona uma nova despesa fixa no mês atualmente selecionado e replica nos próximos meses."""
    mes_atual = combo_mes.current() + 1
    ano_atual = int(combo_ano.get())

    # Garante que o mês já exista no dicionário
    inicializar_mes(mes_atual, ano_atual)

    janela = tk.Toplevel(app)
    janela.title("Nova Despesa Fixa")
    largura, altura = 350, 350
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.attributes("-topmost", True)
    janela.grab_set()
    aplicar_icone(janela)

    main_frame = tk.Frame(janela, padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    # Campos de entrada
    ttk.Label(main_frame, text="Descrição:", font=("Inter", 11)).pack(pady=8)
    entrada_desc = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_desc.pack(pady=5)

    ttk.Label(main_frame, text="Valor (R$):", font=("Inter", 11)).pack(pady=8)
    entrada_valor = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_valor.pack(pady=5)

    ttk.Label(main_frame, text="Dia de vencimento (1 a 31):",
              font=("Inter", 11)).pack(pady=8)
    entrada_venc = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_venc.pack(pady=5)

    # Mensagem de erro
    def mostrar_erro(msg):
        messagebox.showerror("Erro", msg, parent=janela)

    # Salvar a despesa
    def salvar():
        descricao = entrada_desc.get().strip()
        if not descricao:
            mostrar_erro("Descrição não pode ser vazia.")
            return

        try:
            valor = float(entrada_valor.get().replace(",", "."))
        except:
            mostrar_erro("Valor inválido.")
            return

        try:
            vencimento = int(entrada_venc.get())
            if not (1 <= vencimento <= 31):
                raise ValueError
        except:
            mostrar_erro("Dia de vencimento inválido (1 a 31).")
            return

        nova_despesa = {
            "descricao": descricao,
            "valor": valor,
            "vencimento": vencimento,
            "status": "Aberto",
            "inicio": (mes_atual, ano_atual)
        }

        # Adiciona no modelo global
        contas_fixas_modelo.append(nova_despesa.copy())

        # Adiciona no mês atual
        dados[(mes_atual, ano_atual)]["despesas_fixas"].append(
            nova_despesa.copy())

        # Replicar nos meses futuros
        for chave in dados:
            m, a = chave
            if (a, m) > (ano_atual, mes_atual):
                # Inicializa se necessário
                inicializar_mes(m, a)
                # Adiciona a despesa replicada
                dados[chave]["despesas_fixas"].append(nova_despesa.copy())

        salvar_dados()
        atualizar_resumo()
        janela.destroy()

    ttk.Button(main_frame, text="💾 Salvar", command=salvar,
               bootstyle="success").pack(pady=20)
    janela.bind("<Return>", lambda event: salvar())


def adicionar_cartao_credito(callback_apos_salvar=None):
    global ultima_selecao_cartao, ultima_selecao_tipo

    if not cartoes:
        erro_janela = tk.Toplevel(app)
        erro_janela.title("Erro")
        erro_janela.resizable(False, False)
        erro_janela.geometry("350x120")
        erro_janela.attributes("-topmost", True)
        erro_janela.grab_set()
        aplicar_icone(erro_janela)
        frame = tk.Frame(erro_janela, padx=15, pady=15, bg="#f8f9fa")
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Nenhum cartão cadastrado. Cadastre um cartão primeiro.",
                  foreground="#dc3545", wraplength=320, font=("Inter", 10),
                  justify="center", background="#f8f9fa").pack(pady=10)
        ttk.Button(frame, text="OK", command=erro_janela.destroy,
                   bootstyle="danger").pack()
        return

    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)
    inicializar_mes(mes, ano)

    janela = tk.Toplevel(app)
    janela.title("Gasto no Cartão")
    largura, altura = 500, 620
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.attributes("-topmost", True)
    janela.grab_set()
    aplicar_icone(janela)

    main_frame = tk.Frame(janela, padx=25, pady=25)
    main_frame.pack(fill="both", expand=True)

    ultimo_cartao = ultima_selecao_cartao if ultima_selecao_cartao in [
        c["nome"] for c in cartoes] else cartoes[0]["nome"]
    ultimo_tipo = ultima_selecao_tipo if ultima_selecao_tipo in tipos_gasto else tipos_gasto[0]

    ttk.Label(main_frame, text="Descrição:", font=("Inter", 11)).pack(pady=5)
    entrada_desc = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_desc.pack(pady=5)

    ttk.Label(main_frame, text="Valor Total (R$):",
              font=("Inter", 11)).pack(pady=5)
    entrada_valor = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_valor.pack(pady=5)

    ttk.Label(main_frame, text="Parcelas:", font=("Inter", 11)).pack(pady=5)
    entrada_parcelas = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_parcelas.insert(0, "1")
    entrada_parcelas.pack(pady=5)

    ttk.Label(main_frame, text="Data do Gasto (DDMMAAAA):",
              font=("Inter", 11)).pack(pady=5)
    entrada_data = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_data.pack(pady=5)

    ttk.Label(main_frame, text="Tipo de Gasto:",
              font=("Inter", 11)).pack(pady=5)
    combo_tipo = ttk.Combobox(
        main_frame, values=tipos_gasto, state="readonly", font=("Inter", 10))
    combo_tipo.set(ultimo_tipo)
    combo_tipo.pack(pady=5)

    ttk.Label(main_frame, text="Cartão:", font=("Inter", 11)).pack(pady=5)
    nomes_cartoes = [c["nome"] for c in cartoes]
    cartao_combo = ttk.Combobox(
        main_frame, values=nomes_cartoes, state="readonly", font=("Inter", 10))
    cartao_combo.set(ultimo_cartao)
    cartao_combo.pack(pady=5)

    fixo_var = tk.BooleanVar()
    check_fixo = ttk.Checkbutton(
        main_frame, text="Gasto Fixo (repetir todo mês)", variable=fixo_var)
    check_fixo.pack(pady=8)

    # ---------------- Subfunção de erro com ícone ----------------
    def mostrar_erro(mensagem):
        erro_janela = tk.Toplevel(janela)
        erro_janela.title("Erro")
        erro_janela.resizable(False, False)
        erro_janela.geometry("350x120")
        erro_janela.attributes("-topmost", True)
        erro_janela.grab_set()
        aplicar_icone(erro_janela)
        frame = tk.Frame(erro_janela, padx=15, pady=15, bg="#f8f9fa")
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=mensagem, foreground="#dc3545", wraplength=320,
                  font=("Inter", 10), justify="center", background="#f8f9fa").pack(pady=10)
        ttk.Button(frame, text="OK", command=erro_janela.destroy,
                   bootstyle="danger").pack()
        erro_janela.update_idletasks()
        w = erro_janela.winfo_width()
        h = erro_janela.winfo_height()
        x = janela.winfo_rootx() + (janela.winfo_width() // 2) - (w // 2)
        y = janela.winfo_rooty() + (janela.winfo_height() // 2) - (h // 2)
        erro_janela.geometry(f"+{x}+{y}")

    def formatar_data(data_str):
        if len(data_str) != 8 or not data_str.isdigit():
            raise ValueError("Data inválida. Deve ser no formato DDMMAAAA.")
        dia = int(data_str[:2])
        mes = int(data_str[2:4])
        ano = int(data_str[4:])
        datetime(ano, mes, dia)
        return dia, mes, ano

    def salvar(event=None):
        global ultima_selecao_cartao, ultima_selecao_tipo

        desc = entrada_desc.get().strip()
        valor_raw = entrada_valor.get().strip()
        parcelas_raw = entrada_parcelas.get().strip()
        data_raw = entrada_data.get().strip()
        tipo = combo_tipo.get().strip()
        cartao_nome = cartao_combo.get().strip()
        fixo = fixo_var.get()

        if not all([desc, valor_raw, parcelas_raw, data_raw, tipo, cartao_nome]):
            mostrar_erro("Por favor, preencha todos os campos.")
            return

        try:
            valor = float(valor_raw.replace(",", "."))
            parcelas = int(parcelas_raw)
            cartao_info = next(
                (c for c in cartoes if c["nome"] == cartao_nome), None)
            if not cartao_info:
                mostrar_erro("Cartão selecionado não encontrado.")
                return

            cartao = cartao_info["nome"]
            fechamento = cartao_info.get("fechamento")
            dia, mes_gasto, ano_gasto = formatar_data(data_raw)

            if parcelas < 1:
                raise ValueError("Parcelas devem ser >= 1.")
            if fechamento is None:
                raise ValueError(
                    f"Cartão '{cartao}' não tem dia de fechamento cadastrado.")

        except Exception as e:
            mostrar_erro(f"Dados inválidos: {str(e)}")
            return

        meses_repeticao = 24 if fixo else parcelas
        parcelas = 1 if fixo else parcelas

        for i in range(meses_repeticao):
            if dia > fechamento:
                mes_fatura = mes_gasto + 1
                ano_fatura = ano_gasto + (1 if mes_fatura > 12 else 0)
                mes_fatura = 1 if mes_fatura > 12 else mes_fatura
            else:
                mes_fatura = mes_gasto
                ano_fatura = ano_gasto

            mes_fatura += i
            ano_fatura += (mes_fatura - 1) // 12
            mes_fatura = (mes_fatura - 1) % 12 + 1

            inicializar_mes(mes_fatura, ano_fatura)
            dados[(mes_fatura, ano_fatura)]["cartao_credito"].append({
                "descricao": desc,
                "valor": round(valor / parcelas, 2),
                "cartao": cartao,
                "dia": dia,
                "mes": mes_gasto,
                "ano": ano_gasto,
                "parcela_atual": i + 1 if not fixo else 0,
                "total_parcelas": parcelas if not fixo else 0,
                "tipo": tipo,
                "fixo": fixo,
                "status": "Aberto"
            })

        ultima_selecao_cartao = cartao
        ultima_selecao_tipo = tipo
        salvar_dados()
        atualizar_resumo()
        if callback_apos_salvar:
            callback_apos_salvar()
        janela.destroy()

    ttk.Button(main_frame, text="💾 Salvar", command=salvar,
               bootstyle="success").pack(pady=20)
    janela.bind("<Return>", salvar)


def adicionar_valor(titulo, tipo, callback_apos_salvar=None):
    global usuario_atual
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)
    inicializar_mes(mes, ano)

    janela = tk.Toplevel(app)
    janela.title(titulo)
    largura = 350
    altura = 450 if tipo == "gasto" else 250
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.attributes("-topmost", True)
    janela.grab_set()
    aplicar_icone(janela)

    main_frame = tk.Frame(janela, padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="Descrição:", font=("Inter", 11)).pack(pady=5)
    entrada_desc = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_desc.pack(pady=5)

    ttk.Label(main_frame, text="Valor (R$):", font=("Inter", 11)).pack(pady=5)
    entrada_valor = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_valor.pack(pady=5)

    if tipo == "gasto":
        ttk.Label(main_frame, text="Dia do Gasto (1-31):",
                  font=("Inter", 11)).pack(pady=5)
        entrada_dia = ttk.Entry(main_frame, font=("Inter", 10))
        entrada_dia.pack(pady=5)

        ttk.Label(main_frame, text="Tipo de Gasto:",
                  font=("Inter", 11)).pack(pady=5)
        tipo_gasto_combo = ttk.Combobox(
            main_frame, state="readonly", font=("Inter", 10))
        tipo_gasto_combo.pack(pady=5)
        atualizar_tipo_gasto_combo(tipo_gasto_combo)

    # ---------------- Subfunção de erro com ícone ----------------
    def mostrar_erro_toplevel(mensagem):
        erro_janela = tk.Toplevel(janela)
        erro_janela.title("Erro")
        erro_janela.resizable(False, False)
        erro_janela.geometry("350x120")
        erro_janela.attributes("-topmost", True)
        erro_janela.grab_set()
        aplicar_icone(erro_janela)

        frame = tk.Frame(erro_janela, padx=15, pady=15, bg="#f8f9fa")
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=mensagem, foreground="#dc3545", wraplength=320,
                  font=("Inter", 10), justify="center", background="#f8f9fa").pack(pady=10)
        ttk.Button(frame, text="OK", command=erro_janela.destroy,
                   bootstyle="danger").pack()
        erro_janela.update_idletasks()
        w = erro_janela.winfo_width()
        h = erro_janela.winfo_height()
        x = janela.winfo_rootx() + (janela.winfo_width() // 2) - (w // 2)
        y = janela.winfo_rooty() + (janela.winfo_height() // 2) - (h // 2)
        erro_janela.geometry(f"+{x}+{y}")

    # ---------------- Salvar ----------------
    def salvar():
        desc = entrada_desc.get().strip()
        valor_texto = entrada_valor.get().strip()
        if not desc:
            mostrar_erro_toplevel("Descrição não pode ser vazia.")
            return
        if not valor_texto:
            mostrar_erro_toplevel("Informe o valor.")
            return

        try:
            valor = float(valor_texto.replace(",", "."))
        except:
            mostrar_erro_toplevel("Valor inválido. Use apenas números.")
            return

        if tipo == "receita":
            dados[chave]["receitas"][desc] = dados[chave]["receitas"].get(
                desc, 0.0) + valor
        else:
            try:
                dia = int(entrada_dia.get())
                if dia < 1 or dia > 31:
                    raise ValueError
            except:
                mostrar_erro_toplevel(
                    "Dia inválido. Informe um número entre 1 e 31.")
                return
            tipo_gasto_val = tipo_gasto_combo.get()
            if not tipo_gasto_val:
                mostrar_erro_toplevel("Selecione um tipo de gasto.")
                return

            dados[chave]["gastos"].append({
                "descricao": desc,
                "valor": valor,
                "tipo": tipo_gasto_val,
                "dia": dia,
                "usuario": usuario_atual or "Desconhecido"
            })

        atualizar_resumo()
        if callback_apos_salvar:
            callback_apos_salvar()
        janela.destroy()

    ttk.Button(main_frame, text="💾 Salvar", command=salvar,
               bootstyle="success").pack(pady=15)
    janela.bind("<Return>", lambda event: salvar())

# ----------------------Funções editar----------------------------------


def editar_tipos_gastos(janela_anterior):
    global tipos_gasto
    janela_anterior.destroy()

    janela = tk.Toplevel(app)
    janela.title("Editar Tipos de Gastos")
    largura, altura = 450, 550
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.transient(app)
    janela.grab_set()
    aplicar_icone(janela)

    main_frame = tk.Frame(janela, padx=25, pady=25)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="📂 Tipos de Gastos Atuais:",
              font=("Inter", 13, "bold")).pack(pady=(0, 10))

    lista_tipos = tk.Listbox(main_frame, height=12, font=("Inter", 10),
                             selectbackground="#0d6efd", selectforeground="#ffffff")
    for tipo in tipos_gasto:
        lista_tipos.insert(tk.END, tipo)
    lista_tipos.pack(pady=8, fill="both", expand=True)

    ttk.Label(main_frame, text="Novo Tipo de Gasto ou Edição:",
              font=("Inter", 11)).pack(pady=(15, 5))
    entrada_novo_tipo = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_novo_tipo.pack(pady=8, fill="x")

    # ---------- Função auxiliar de aviso customizado ----------
    def mostrar_erro_toplevel(mensagem, parent):
        aviso_janela = tk.Toplevel(parent)
        aviso_janela.title("Aviso")
        aviso_janela.resizable(False, False)
        largura, altura = 300, 120
        x = (parent.winfo_screenwidth() // 2) - (largura // 2)
        y = (parent.winfo_screenheight() // 2) - (altura // 2)
        aviso_janela.geometry(f"{largura}x{altura}+{x}+{y}")
        aviso_janela.grab_set()
        aviso_janela.attributes("-topmost", True)
        aviso_janela.configure(bg="#f8f9fa")
        aplicar_icone(aviso_janela)

        frame = tk.Frame(aviso_janela, bg="#f8f9fa", padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=mensagem, font=("Inter", 11),
                  justify="center").pack(pady=10)
        ttk.Button(frame, text="OK", command=aviso_janela.destroy,
                   bootstyle="secondary").pack()

    # ---------------- Funções dos botões ----------------
    def adicionar_tipo():
        tipo_novo = entrada_novo_tipo.get().strip()
        if tipo_novo and tipo_novo not in tipos_gasto:
            tipos_gasto.append(tipo_novo)
            lista_tipos.insert(tk.END, tipo_novo)
            entrada_novo_tipo.delete(0, tk.END)
            salvar_dados()
        else:
            mostrar_erro_toplevel("Tipo já existe ou está vazio.", janela)

    def excluir_tipo():
        selecionado = lista_tipos.curselection()
        if not selecionado:
            mostrar_erro_toplevel("Selecione um tipo para excluir.", janela)
            return

        tipo_selecionado = lista_tipos.get(selecionado)

        # Janela de confirmação
        confirm_janela = tk.Toplevel(janela)
        confirm_janela.title("Confirmar Exclusão")
        confirm_janela.resizable(False, False)
        largura_conf, altura_conf = 360, 150
        x = (janela.winfo_screenwidth() // 2) - (largura_conf // 2)
        y = (janela.winfo_screenheight() // 2) - (altura_conf // 2)
        confirm_janela.geometry(f"{largura_conf}x{altura_conf}+{x}+{y}")
        confirm_janela.grab_set()
        confirm_janela.attributes("-topmost", True)
        confirm_janela.configure(bg="#f8f9fa")
        aplicar_icone(confirm_janela)

        frame = tk.Frame(confirm_janela, bg="#f8f9fa", padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=f"Deseja realmente excluir o tipo '{tipo_selecionado}'?",
                  font=("Inter", 11), wraplength=320, justify="center").pack(pady=15)

        botoes = tk.Frame(frame, bg="#f8f9fa")
        botoes.pack()

        def confirmar():
            tipos_gasto.remove(tipo_selecionado)
            lista_tipos.delete(selecionado)
            salvar_dados()
            confirm_janela.destroy()

        ttk.Button(botoes, text="✓ Sim", command=confirmar,
                   bootstyle="danger").pack(side="left", padx=10)
        ttk.Button(botoes, text="✗ Não", command=confirm_janela.destroy,
                   bootstyle="secondary").pack(side="right", padx=10)

    def editar_tipo():
        selecionado = lista_tipos.curselection()
        if not selecionado:
            mostrar_erro_toplevel("Selecione um tipo para editar.", janela)
            return

        indice = selecionado[0]
        novo_nome = entrada_novo_tipo.get().strip()
        antigo_nome = lista_tipos.get(indice)

        if not novo_nome:
            mostrar_erro_toplevel("Digite um nome válido.", janela)
            return
        if novo_nome == antigo_nome:
            mostrar_erro_toplevel("O nome não foi alterado.", janela)
            return
        if novo_nome in tipos_gasto:
            mostrar_erro_toplevel("Este tipo já existe.", janela)
            return

        tipos_gasto[indice] = novo_nome
        lista_tipos.delete(indice)
        lista_tipos.insert(indice, novo_nome)
        entrada_novo_tipo.delete(0, tk.END)
        salvar_dados()

    # ---------------- Botões principais ----------------
    botoes_frame = tk.Frame(main_frame)
    botoes_frame.pack(pady=15)

    ttk.Button(botoes_frame, text="➕ Adicionar Tipo",
               command=adicionar_tipo, bootstyle="success").pack(pady=5, fill="x")
    ttk.Button(botoes_frame, text="🗑️ Excluir Tipo Selecionado",
               command=excluir_tipo, bootstyle="danger").pack(pady=5, fill="x")
    ttk.Button(botoes_frame, text="✏️ Editar Tipo Selecionado",
               command=editar_tipo, bootstyle="primary").pack(pady=5, fill="x")


def editar_despesa_fixa(indice):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)

    # Inicializa o mês se não existir
    if chave not in dados:
        inicializar_mes(mes, ano)
    info = dados[chave]  # pega o dict correto

    d = info["despesas_fixas"][indice]

    janela = tk.Toplevel(app)
    janela.title("Editar Despesa Fixa")
    largura, altura = 420, 300
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.attributes("-topmost", True)
    janela.grab_set()
    aplicar_icone(janela)

    main_frame = tk.Frame(janela, padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    janela.bind("<Return>", lambda event: salvar_alteracoes())

    ttk.Label(main_frame, text="Descrição:",
              font=("Inter", 11)).pack(pady=(10, 0))
    ttk.Label(main_frame, text=d["descricao"],
              font=("Inter", 10, "bold")).pack()

    ttk.Label(main_frame, text="Valor (R$):",
              font=("Inter", 11)).pack(pady=(15, 0))
    valor_entry = ttk.Entry(main_frame, font=("Inter", 10))
    valor_entry.insert(0, f"{d['valor']:.2f}".replace(".", ","))
    valor_entry.pack(pady=5)

    ttk.Label(main_frame, text="Vencimento (dia):",
              font=("Inter", 11)).pack(pady=(15, 0))
    venc_entry = ttk.Entry(main_frame, font=("Inter", 10))
    venc_entry.insert(0, str(d.get("vencimento", "")))
    venc_entry.pack(pady=5)

    status_btn = ttk.Button(
        main_frame, text=f"📋 Alternar Status (Atual: {d['status']})", bootstyle="info")

    def mostrar_erro(msg):
        erro_janela = tk.Toplevel(janela)
        erro_janela.title("Erro")
        erro_janela.geometry("350x120")
        erro_janela.attributes("-topmost", True)
        erro_janela.grab_set()
        aplicar_icone(erro_janela)
        frame = tk.Frame(erro_janela, padx=15, pady=15)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=msg, foreground="#dc3545",
                  wraplength=320, font=("Inter", 10)).pack(pady=10)
        ttk.Button(frame, text="OK", command=erro_janela.destroy,
                   bootstyle="danger").pack()
        erro_janela.update_idletasks()
        w, h = erro_janela.winfo_width(), erro_janela.winfo_height()
        x = janela.winfo_rootx() + (janela.winfo_width() // 2) - (w // 2)
        y = janela.winfo_rooty() + (janela.winfo_height() // 2) - (h // 2)
        erro_janela.geometry(f"+{x}+{y}")

    def salvar_alteracoes():
        try:
            valor_str = valor_entry.get().replace(",", ".")
            novo_valor = float(valor_str)
            novo_vencimento = int(venc_entry.get())
        except:
            mostrar_erro("Valor ou vencimento inválido.")
            return

        d["valor"] = novo_valor
        d["vencimento"] = novo_vencimento
        salvar_dados()
        atualizar_resumo()
        janela.destroy()

    def alternar_status():
        d["status"] = "Pago" if d["status"] == "Aberto" else "Aberto"
        status_btn.config(text=f"📋 Alternar Status (Atual: {d['status']})")
        salvar_dados()
        atualizar_resumo()

    status_btn.config(command=alternar_status)
    status_btn.pack(pady=8)
    ttk.Button(main_frame, text="💾 Salvar", command=salvar_alteracoes,
               bootstyle="success").pack(pady=15)


def editar_gasto_cartao(gasto_original, callback_apos_salvar=None):
    janela = tk.Toplevel(app)
    janela.title("Editar Gasto no Cartão")
    largura, altura = 400, 350
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.attributes("-topmost", True)
    janela.grab_set()
    aplicar_icone(janela)

    main_frame = tk.Frame(janela, padx=25, pady=25)
    main_frame.pack(fill="both", expand=True)

    fixo = gasto_original.get("fixo", False)
    parcelas = 24 if fixo else gasto_original.get("total_parcelas", 1) or 1
    valor_parcela = round(gasto_original["valor"], 2)

    ttk.Label(main_frame, text="Descrição:", font=("Inter", 11)).pack(pady=5)
    entrada_desc = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_desc.insert(0, gasto_original["descricao"])
    entrada_desc.pack(pady=5)

    ttk.Label(main_frame, text="Valor da Parcela (R$):",
              font=("Inter", 11)).pack(pady=5)
    entrada_valor = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_valor.insert(0, str(valor_parcela))
    entrada_valor.pack(pady=5)

    ttk.Label(main_frame, text="Tipo de Gasto:",
              font=("Inter", 11)).pack(pady=5)
    combo_tipo = ttk.Combobox(
        main_frame, values=tipos_gasto, state="readonly", font=("Inter", 10))
    combo_tipo.set(gasto_original.get("tipo", tipos_gasto[0]))
    combo_tipo.pack(pady=5)

    def mostrar_erro_toplevel(mensagem):
        erro_janela = tk.Toplevel(janela)
        erro_janela.title("Erro")
        erro_janela.geometry("350x120")
        erro_janela.attributes("-topmost", True)
        erro_janela.grab_set()
        aplicar_icone(erro_janela)
        frame = tk.Frame(erro_janela, padx=15, pady=15)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=mensagem, foreground="#dc3545",
                  wraplength=320, font=("Inter", 10)).pack(pady=10)
        ttk.Button(frame, text="OK", command=erro_janela.destroy,
                   bootstyle="danger").pack()
        erro_janela.update_idletasks()
        w, h = erro_janela.winfo_width(), erro_janela.winfo_height()
        x = janela.winfo_rootx() + (janela.winfo_width() // 2) - (w // 2)
        y = janela.winfo_rooty() + (janela.winfo_height() // 2) - (h // 2)
        erro_janela.geometry(f"+{x}+{y}")

    def salvar():
        try:
            novo_desc = entrada_desc.get().strip()
            novo_valor_parcela = float(entrada_valor.get().replace(",", "."))
            novo_tipo = combo_tipo.get().strip()
            if not novo_desc or not novo_tipo:
                raise ValueError("Campos não podem estar vazios.")
        except Exception as e:
            mostrar_erro_toplevel(f"Erro: {e}")
            return

        dia, mes_inicial, ano_inicial = gasto_original["dia"], gasto_original["mes"], gasto_original["ano"]
        cartao = gasto_original["cartao"]
        desc_original = gasto_original["descricao"]

        # buscar o fechamento do cartão
        cartao_info = next((c for c in cartoes if c["nome"] == cartao), None)
        fechamento = cartao_info.get("fechamento") if cartao_info else None
        if fechamento is None:
            mostrar_erro_toplevel(
                f"O cartão '{cartao}' não tem fechamento cadastrado.")
            return

        # calcular a fatura inicial correta
        if dia > fechamento:
            mes_fatura = mes_inicial + 1
            ano_fatura = ano_inicial + (1 if mes_fatura > 12 else 0)
            mes_fatura = 1 if mes_fatura > 12 else mes_fatura
        else:
            mes_fatura = mes_inicial
            ano_fatura = ano_inicial

        hoje = datetime.today()
        mes_atual, ano_atual = hoje.month, hoje.year

        # percorrer parcelas/faturas
        for i in range(parcelas):
            m = mes_fatura + i
            a = ano_fatura + (m - 1) // 12
            m = (m - 1) % 12 + 1

            if a < ano_atual or (a == ano_atual and m < mes_atual):
                continue

            chave_fatura = (m, a)
            if chave_fatura not in dados:
                inicializar_mes(m, a)

            for g in dados[chave_fatura]["cartao_credito"]:
                if (
                    g["descricao"] == desc_original
                    and g["cartao"] == cartao
                    and g["dia"] == dia
                    and g["mes"] == mes_inicial
                    and g["ano"] == ano_inicial
                ):
                    g["descricao"] = novo_desc
                    g["valor"] = round(novo_valor_parcela, 2)
                    g["tipo"] = novo_tipo

        salvar_dados()
        atualizar_resumo()
        janela.destroy()
        if callback_apos_salvar:
            callback_apos_salvar()

    ttk.Button(main_frame, text="💾 Salvar", command=salvar,
               bootstyle="success").pack(pady=25)
    janela.bind("<Return>", lambda e: salvar())
    entrada_desc.focus_set()


def editar_receita(nome_receita):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)
    inicializar_mes(mes, ano)
    valor_atual = dados[chave]["receitas"].get(nome_receita, 0.0)

    janela = tk.Toplevel(app)
    janela.title("Editar Receita")
    largura, altura = 350, 280
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.attributes("-topmost", True)
    janela.grab_set()
    aplicar_icone(janela)

    main_frame = tk.Frame(janela, padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="Descrição:", font=("Inter", 11)).pack(pady=8)
    entrada_desc = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_desc.pack(pady=5)
    entrada_desc.insert(0, nome_receita)
    entrada_desc.config(state="disabled")

    ttk.Label(main_frame, text="Valor (R$):", font=("Inter", 11)).pack(pady=8)
    entrada_valor = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_valor.pack(pady=5)
    entrada_valor.insert(0, str(valor_atual).replace(".", ","))

    def mostrar_erro_toplevel(mensagem):
        erro_janela = tk.Toplevel(janela)
        erro_janela.title("Erro")
        erro_janela.geometry("350x120")
        erro_janela.attributes("-topmost", True)
        erro_janela.grab_set()
        aplicar_icone(erro_janela)
        frame = tk.Frame(erro_janela, padx=15, pady=15)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=mensagem, foreground="#dc3545",
                  wraplength=320, font=("Inter", 10)).pack(pady=10)
        ttk.Button(frame, text="OK", command=erro_janela.destroy,
                   bootstyle="danger").pack()
        erro_janela.update_idletasks()
        w, h = erro_janela.winfo_width(), erro_janela.winfo_height()
        x = janela.winfo_rootx() + (janela.winfo_width() // 2) - (w // 2)
        y = janela.winfo_rooty() + (janela.winfo_height() // 2) - (h // 2)
        erro_janela.geometry(f"+{x}+{y}")

    def salvar():
        try:
            valor_novo = float(entrada_valor.get().replace(",", "."))
        except:
            mostrar_erro_toplevel("Valor inválido.")
            return
        if valor_novo < 0:
            mostrar_erro_toplevel("Valor não pode ser negativo.")
            return
        dados[chave]["receitas"][nome_receita] = valor_novo
        atualizar_resumo()
        janela.destroy()

    ttk.Button(main_frame, text="💾 Salvar", command=salvar,
               bootstyle="success").pack(pady=15)
    janela.bind("<Return>", lambda event: salvar())


def editar_gasto_diario(idx, callback_apos_salvar=None):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)
    info = dados.get(chave)

    if not info or idx < 0 or idx >= len(info["gastos"]):
        show_error("Erro", "Índice de gasto inválido")
        return

    gasto = info["gastos"][idx]

    janela = tk.Toplevel(app)
    janela.title("Editar Gasto Diário")
    largura, altura = 420, 340
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.resizable(False, False)
    aplicar_icone(janela)

    main_frame = tk.Frame(janela, padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    # Descrição
    ttk.Label(main_frame, text="Descrição:", font=("Inter", 11)
              ).pack(padx=10, pady=(10, 0), anchor="w")
    entry_descricao = ttk.Entry(main_frame, font=("Inter", 10))
    entry_descricao.pack(padx=10, pady=8, fill="x")
    entry_descricao.insert(0, gasto["descricao"])

    # Valor
    ttk.Label(main_frame, text="Valor:", font=("Inter", 11)
              ).pack(padx=10, pady=(10, 0), anchor="w")
    entry_valor = ttk.Entry(main_frame, font=("Inter", 10))
    entry_valor.pack(padx=10, pady=8, fill="x")
    entry_valor.insert(0, str(gasto["valor"]))

    # Tipo de gasto
    ttk.Label(main_frame, text="Tipo:", font=("Inter", 11)
              ).pack(padx=10, pady=(10, 0), anchor="w")
    tipos_existentes = ["Alimentação", "Transporte",
                        "Saúde", "Lazer", "Moradia", "Outros"]
    entry_tipo = ttk.Combobox(
        main_frame, values=tipos_existentes, font=("Inter", 10))
    entry_tipo.pack(padx=10, pady=8, fill="x")
    entry_tipo.set(gasto.get("tipo", "Outros"))

    def mostrar_erro_toplevel(mensagem):
        erro_janela = tk.Toplevel(janela)
        erro_janela.title("Erro")
        erro_janela.geometry("350x120")
        erro_janela.attributes("-topmost", True)
        erro_janela.grab_set()
        aplicar_icone(erro_janela)
        frame = tk.Frame(erro_janela, padx=15, pady=15)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=mensagem, foreground="#dc3545",
                  wraplength=320, font=("Inter", 10)).pack(pady=10)
        ttk.Button(frame, text="OK", command=erro_janela.destroy,
                   bootstyle="danger").pack()
        erro_janela.update_idletasks()
        w, h = erro_janela.winfo_width(), erro_janela.winfo_height()
        x = janela.winfo_rootx() + (janela.winfo_width() // 2) - (w // 2)
        y = janela.winfo_rooty() + (janela.winfo_height() // 2) - (h // 2)
        erro_janela.geometry(f"+{x}+{y}")

    def salvar(event=None):
        nova_desc = entry_descricao.get().strip()
        try:
            novo_valor = float(entry_valor.get().replace(",", "."))
        except:
            mostrar_erro_toplevel("Valor inválido.")
            return
        if not nova_desc:
            mostrar_erro_toplevel("Descrição não pode estar vazia.")
            return
        novo_tipo = entry_tipo.get().strip() or "Outros"

        info["gastos"][idx]["descricao"] = nova_desc
        info["gastos"][idx]["valor"] = novo_valor
        info["gastos"][idx]["tipo"] = novo_tipo

        salvar_dados()
        atualizar_resumo()
        janela.destroy()
        if callback_apos_salvar:
            callback_apos_salvar()

    ttk.Button(main_frame, text="💾 Salvar", command=salvar,
               bootstyle="success").pack(pady=15)
    janela.bind("<Return>", salvar)
    entry_descricao.focus_set()

# ----------------------Funções excluir---------------------------------


def excluir_gasto_cartao(gasto, parent_janela=None, callback_apos_excluir=None):
    confirm_janela = tk.Toplevel(app)
    confirm_janela.title("Excluir Gasto")
    largura, altura = 350, 150
    x = (confirm_janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (confirm_janela.winfo_screenheight() // 2) - (altura // 2)
    confirm_janela.geometry(f"{largura}x{altura}+{x}+{y}")
    confirm_janela.attributes("-topmost", True)
    confirm_janela.grab_set()
    aplicar_icone(confirm_janela)

    frame = tk.Frame(confirm_janela, padx=20, pady=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(
        frame,
        text="Deseja excluir TODAS as parcelas deste gasto a partir deste mês?",
        font=("Inter", 11),
        wraplength=320,
        justify="center"
    ).pack(pady=10)

    def confirmar():
        fixo = gasto.get("fixo", False)
        total_parcelas = gasto.get("total_parcelas", 1)
        parcelas = 24 if fixo else total_parcelas

        dia = gasto.get("dia")
        mes_compra = gasto.get("mes")
        ano_compra = gasto.get("ano")
        cartao = gasto.get("cartao")
        descricao = gasto.get("descricao")

        # --- NOVO: calcular a fatura inicial com base no fechamento ---
        cartao_info = next((c for c in cartoes if c["nome"] == cartao), None)
        fechamento = cartao_info.get("fechamento") if cartao_info else None

        if fechamento is None:
            messagebox.showerror(
                "Erro", f"O cartão '{cartao}' não possui fechamento cadastrado.")
            confirm_janela.destroy()
            return

        if dia > fechamento:
            mes_fatura_inicial = mes_compra + 1
            ano_fatura_inicial = ano_compra + \
                (1 if mes_fatura_inicial > 12 else 0)
            mes_fatura_inicial = 1 if mes_fatura_inicial > 12 else mes_fatura_inicial
        else:
            mes_fatura_inicial = mes_compra
            ano_fatura_inicial = ano_compra

        # Pega mês e ano selecionados na interface
        mes_selecionado = combo_mes.current() + 1
        ano_selecionado = int(combo_ano.get())

        # Itera sobre todas as parcelas/faturas
        for i in range(parcelas):
            m = mes_fatura_inicial + i
            a = ano_fatura_inicial + (m - 1) // 12
            m = (m - 1) % 12 + 1

            # Exclui somente se for no mês/ano selecionado ou depois
            if (a < ano_selecionado) or (a == ano_selecionado and m < mes_selecionado):
                continue

            chave_fatura = (m, a)
            if chave_fatura in dados:
                dados[chave_fatura]["cartao_credito"] = [
                    g for g in dados[chave_fatura]["cartao_credito"]
                    if not (
                        g.get("descricao") == descricao
                        and g.get("cartao") == cartao
                        and g.get("dia") == dia
                        and g.get("mes") == mes_compra
                        and g.get("ano") == ano_compra
                    )
                ]

        salvar_dados()
        atualizar_resumo()
        if callback_apos_excluir:
            callback_apos_excluir()
        confirm_janela.destroy()

    botoes = tk.Frame(frame)
    botoes.pack(pady=10)
    ttk.Button(botoes, text="✓ Sim", command=confirmar,
               bootstyle="danger").pack(side="left", padx=10)
    ttk.Button(botoes, text="✗ Não", command=confirm_janela.destroy,
               bootstyle="secondary").pack(side="right", padx=10)


def excluir_despesa_fixa(idx):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave_atual = get_chave(mes, ano)

    if chave_atual not in dados:
        return

    # acessa diretamente a despesa correta
    try:
        descricao_target = dados[chave_atual]["despesas_fixas"][idx]["descricao"]
    except IndexError:
        return

    # Janela de confirmação personalizada
    confirm_janela = tk.Toplevel(app)
    confirm_janela.title("Confirmação")
    largura, altura = 400, 180
    x = (confirm_janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (confirm_janela.winfo_screenheight() // 2) - (altura // 2)
    confirm_janela.geometry(f"{largura}x{altura}+{x}+{y}")
    confirm_janela.attributes("-topmost", True)
    confirm_janela.grab_set()
    aplicar_icone(confirm_janela)

    frame = tk.Frame(confirm_janela, padx=20, pady=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text=f"Deseja realmente excluir a despesa fixa '{descricao_target}' a partir de {mes:02d}/{ano}?",
              font=("Inter", 11), wraplength=360, justify="center").pack(pady=15)

    def confirmar():
        for ano_loop in range(ano, 2101):
            for mes_loop in range(1, 13):
                if ano_loop == ano and mes_loop < mes:
                    continue
                chave = get_chave(mes_loop, ano_loop)
                if chave in dados:
                    dados[chave]["despesas_fixas"] = [
                        d for d in dados[chave]["despesas_fixas"]
                        if d.get("descricao") != descricao_target
                    ]
        atualizar_resumo()
        confirm_janela.destroy()

    botoes = tk.Frame(frame)
    botoes.pack()
    ttk.Button(botoes, text="✓ Sim", command=confirmar,
               bootstyle="danger").pack(side="left", padx=10)
    ttk.Button(botoes, text="✗ Não", command=confirm_janela.destroy,
               bootstyle="secondary").pack(side="right", padx=10)


def excluir_receita(nome_receita):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)

    if chave not in dados:
        inicializar_mes(mes, ano)

    info = dados[chave]  # <- pega os dados do mês após inicializar

    if nome_receita not in info["receitas"]:
        return

    # Janela de confirmação personalizada
    confirm_janela = tk.Toplevel(app)
    confirm_janela.title("Excluir Receita")
    largura, altura = 350, 150
    x = (confirm_janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (confirm_janela.winfo_screenheight() // 2) - (altura // 2)
    confirm_janela.geometry(f"{largura}x{altura}+{x}+{y}")
    confirm_janela.attributes("-topmost", True)
    confirm_janela.grab_set()
    aplicar_icone(confirm_janela)

    frame = tk.Frame(confirm_janela, padx=20, pady=20)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text=f"Deseja excluir a receita '{nome_receita}' deste mês?", font=(
        "Inter", 11), wraplength=320, justify="center").pack(pady=15)

    def confirmar():
        del info["receitas"][nome_receita]
        salvar_dados()
        atualizar_resumo()
        confirm_janela.destroy()

    botoes = tk.Frame(frame)
    botoes.pack()
    ttk.Button(botoes, text="✓ Sim", command=confirmar,
               bootstyle="danger").pack(side="left", padx=10)
    ttk.Button(botoes, text="✗ Não", command=confirm_janela.destroy,
               bootstyle="secondary").pack(side="right", padx=10)


def excluir_gasto_diario(idx, janela_detalhes=None, callback_apos_excluir=None):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)
    info = dados.get(chave)

    if not info or idx < 0 or idx >= len(info["gastos"]):
        show_error("Erro", "Índice de gasto inválido", parent=janela_detalhes)
        return

    gasto = info["gastos"][idx]

    confirm_janela = tk.Toplevel(app)
    confirm_janela.title("Excluir Gasto Diário")
    largura, altura = 380, 160
    x = (confirm_janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (confirm_janela.winfo_screenheight() // 2) - (altura // 2)
    confirm_janela.geometry(f"{largura}x{altura}+{x}+{y}")
    confirm_janela.attributes("-topmost", True)
    confirm_janela.grab_set()
    aplicar_icone(confirm_janela)

    frame = tk.Frame(confirm_janela, padx=20, pady=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text=f"Excluir gasto '{gasto['descricao']}' no dia {gasto['dia']}?",
              font=("Inter", 11), wraplength=340, justify="center").pack(pady=15)

    def confirmar():
        info["gastos"].pop(idx)
        salvar_dados()
        atualizar_resumo()
        if callback_apos_excluir:
            callback_apos_excluir()
        confirm_janela.destroy()

    botoes = tk.Frame(frame)
    botoes.pack()
    ttk.Button(botoes, text="✓ Sim", command=confirmar,
               bootstyle="danger").pack(side="left", padx=10)
    ttk.Button(botoes, text="✗ Não", command=confirm_janela.destroy,
               bootstyle="secondary").pack(side="right", padx=10)


# -------------------------Interface Responsiva------------------------------------
frame_selecao = tk.Frame(app, pady=2, bg="#0d6efd")
frame_selecao.pack(pady=(2, 2), fill="x")

combo_container = tk.Frame(frame_selecao, bg="#0d6efd")
combo_container.pack()

ttk.Label(combo_container, text="📅 Período:", font=(
    "Inter", 13, "bold")).pack(side="left", padx=(0, 10))

meses = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]
combo_mes = ttk.Combobox(combo_container, values=meses,
                         state="readonly", width=14, font=("Inter", 11))

anos = [str(y) for y in range(2025, 2050)]
combo_ano = ttk.Combobox(combo_container, values=anos,
                         state="readonly", width=8, font=("Inter", 11))

try:
    with open("ultima_selecao.json", "r") as f:
        ultima_selecao = json.load(f)
        mes_inicial = ultima_selecao.get("mes", datetime.now().month)
        ano_inicial = ultima_selecao.get("ano", datetime.now().year)
except Exception:
    mes_inicial = datetime.now().month
    ano_inicial = datetime.now().year

combo_mes.current(mes_inicial - 1)
combo_ano.set(str(ano_inicial))

combo_mes.pack(side="left", padx=8)
combo_ano.pack(side="left", padx=8)

combo_mes.bind("<<ComboboxSelected>>", lambda e: atualizar_resumo())
combo_ano.bind("<<ComboboxSelected>>", lambda e: atualizar_resumo())

frame_resumo = tk.LabelFrame(
    app, text="📊 Resumo Geral",
    padx=12, pady=12, bg="#d9e3f1", fg="#0d6efd",
    font=("Inter", 13, "bold")
)
frame_resumo.pack(fill="x", padx=10, pady=(2, 5))

frame_main = tk.Frame(app, bg="#0d6efd")
frame_main.pack(fill="both", expand=True, padx=15, pady=8)

# -------------------------
# Função para criar cards
# -------------------------


def criar_card(container, titulo, bg, expandable=True, pady=5, height=None):
    sombra = tk.Frame(container, bg="#b0b0b0")
    sombra.pack(side="left", fill="both", expand=True, padx=5, pady=pady)

    frame = tk.Frame(sombra, bg=bg, bd=1, relief="ridge")
    frame.pack(expand=True, fill="both", padx=(0, 2), pady=(0, 2))

    header = tk.Frame(frame, bg=bg)
    header.pack(fill="x", padx=10, pady=8)

    lbl_titulo = ttk.Label(header, text=titulo, font=(
        "Segoe UI", 11, "bold"), background=bg)
    lbl_titulo.pack(side="left")
    lbl_total = ttk.Label(header, text="R$ 0,00",
                          font=("Segoe UI", 10), background=bg)
    lbl_total.pack(side="right")

    if expandable:
        canvas = tk.Canvas(frame, bg=bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=bg)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return frame, lbl_total, scroll_frame
    else:
        scroll_frame = tk.Frame(frame, bg=bg, height=height)
        scroll_frame.pack(fill="both", expand=True, pady=5)
        return frame, lbl_total, scroll_frame


# -------------------------
# Containers topo e base
# -------------------------
container_cards_topo = tk.Frame(frame_main, bg="#0d6efd")
container_cards_topo.pack(fill="both", expand=True, pady=5)

container_cards_base = tk.Frame(frame_main, bg="#0d6efd")
# altura automática pelo conteúdo
container_cards_base.pack(fill="x", expand=False, pady=5)

container_cards_topo.pack_propagate(False)  # controla altura do topo
container_cards_base.pack_propagate(True)   # base mantém altura automática

# -------------------------
# Topo: Receitas e Despesas Fixas
# -------------------------
frame_receitas, lbl_receitas, lista_receitas = criar_card(
    container_cards_topo, "💰 Receitas", bg="#e6ffea", expandable=True)
frame_receitas.pack(side="left", fill="both", expand=True, padx=5)

frame_despesas, lbl_despesas, lista_despesas = criar_card(
    container_cards_topo, "🏠 Despesas Fixas", bg="#ffe6e6", expandable=True)
frame_despesas.pack(side="left", fill="both", expand=True, padx=5)

# -------------------------
# Base: Gastos Diários e Cartão de Crédito
# -------------------------
frame_gastos, lbl_gastos, lista_gastos = criar_card(
    container_cards_base, "🛒 Gastos Diários", bg="#e6f0ff", expandable=False
)
frame_gastos.pack(side="left", fill="x", expand=True, padx=5)

frame_credito, lbl_credito, lista_credito = criar_card(
    container_cards_base, "💳 Cartão de Crédito", bg="#f2e6ff", expandable=False
)
frame_credito.pack(side="left", fill="x", expand=True, padx=5)

# ---- Compatibilidade com atualizar_resumo ----
scroll_frame_receitas = lista_receitas
scroll_frame_despesas = lista_despesas
scroll_frame_gastos = lista_gastos
scroll_frame_credito = lista_credito

# -------------------------
# Ajuste de altura e largura proporcional topo
# -------------------------
# -------------------------
# Ajuste de altura proporcional topo
# -------------------------


def ajustar_topo(event):
    altura_total = event.height
    proporcao_topo = 0.6  # 60% da altura do frame_main para topo
    container_cards_topo.config(height=int(altura_total * proporcao_topo))
    # largura das seções do topo é ajustada automaticamente pelo pack(expand=True, fill="both")


# Inicializa dados para o mês atual
atualizar_resumo()
app.mainloop()
