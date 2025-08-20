VERSAO_ATUAL = "1.0.7"

import os, sys, time, json, copy, math, subprocess, webbrowser, urllib.request, locale
from datetime import datetime
from collections import defaultdict
from operator import itemgetter
from functools import partial
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from PIL import Image, ImageTk
import ttkbootstrap as tb
from ttkbootstrap import Style
from ttkbootstrap.constants import *

def recurso_caminho(relativo):
    """Obtém caminho correto para recursos mesmo após empacotado com PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relativo)
    return os.path.join(os.path.abspath("."), relativo)

# Função para buscar atualização e baixar se disponível
def buscar_atualizacao():
    url_versao = "https://raw.githubusercontent.com/paulohidalgosantos/Controle-Financeiro/main/versao.txt"
    try:
        with urllib.request.urlopen(url_versao, timeout=5) as response:
            versao_remota = response.read().decode().strip()

        if versao_remota > VERSAO_ATUAL:
            # Janela de confirmação customizada
            confirm_janela = tk.Toplevel(app)
            confirm_janela.title("Atualização disponível")
            confirm_janela.resizable(False, False)
            largura, altura = 360, 150
            x = (app.winfo_screenwidth() // 2) - (largura // 2)
            y = (app.winfo_screenheight() // 2) - (altura // 2)
            confirm_janela.geometry(f"{largura}x{altura}+{x}+{y}")
            confirm_janela.grab_set()
            confirm_janela.attributes("-topmost", True)
            confirm_janela.configure(bg="#f8f9fa")
            aplicar_icone(confirm_janela)

            frame = tk.Frame(confirm_janela, bg="#f8f9fa", padx=20, pady=20)
            frame.pack(fill="both", expand=True)

            ttk.Label(frame, text=f"Nova versão {versao_remota} disponível.\nDeseja atualizar agora?",
                      font=("Inter", 11), justify="center", wraplength=320).pack(pady=15)

            botoes = tk.Frame(frame, bg="#f8f9fa")
            botoes.pack()

            def sim():
                baixar_e_instalar_atualizacao()
                confirm_janela.destroy()

            ttk.Button(botoes, text="✓ Sim", command=sim, bootstyle="success").pack(side="left", padx=10)
            ttk.Button(botoes, text="✗ Não", command=confirm_janela.destroy, bootstyle="secondary").pack(side="right", padx=10)

        else:
            # Janela de informação customizada
            info_janela = tk.Toplevel(app)
            info_janela.title("Atualização")
            info_janela.resizable(False, False)
            largura, altura = 300, 120
            x = (app.winfo_screenwidth() // 2) - (largura // 2)
            y = (app.winfo_screenheight() // 2) - (altura // 2)
            info_janela.geometry(f"{largura}x{altura}+{x}+{y}")
            info_janela.grab_set()
            info_janela.attributes("-topmost", True)
            info_janela.configure(bg="#f8f9fa")
            aplicar_icone(info_janela)

            frame_info = tk.Frame(info_janela, bg="#f8f9fa", padx=20, pady=20)
            frame_info.pack(fill="both", expand=True)

            ttk.Label(frame_info, text="Você já está usando a versão mais recente.",
                      font=("Inter", 11), justify="center", wraplength=280).pack(pady=10)
            ttk.Button(frame_info, text="OK", command=info_janela.destroy, bootstyle="secondary").pack()

    except Exception as e:
        # Janela de erro customizada
        erro_janela = tk.Toplevel(app)
        erro_janela.title("Erro")
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

        ttk.Label(frame_erro, text=f"Erro ao verificar atualização:\n{e}",
                  font=("Inter", 11), justify="center", wraplength=320).pack(pady=10)
        ttk.Button(frame_erro, text="OK", command=erro_janela.destroy, bootstyle="danger").pack()

def baixar_e_instalar_atualizacao():
    try:
        url_api = "https://api.github.com/repos/paulohidalgosantos/Controle-Financeiro/releases/latest"
        with urllib.request.urlopen(url_api, timeout=10) as response:
            release = json.loads(response.read().decode())

        exe_url = None
        for asset in release["assets"]:
            if asset["name"].endswith(".exe"):
                exe_url = asset["browser_download_url"]
                break

        if not exe_url:
            raise Exception("Nenhum executável .exe encontrado na última release.")

        caminho_atual = os.path.abspath(sys.argv[0])
        pasta = os.path.dirname(caminho_atual)
        nome_atual = os.path.basename(caminho_atual)
        
        # Criar pasta temporária para download
        temp_dir = os.path.join(pasta, "_temp_update")
        os.makedirs(temp_dir, exist_ok=True)
        
        novo_exe = os.path.join(temp_dir, "novo_controle_financeiro.exe")

        # Download com verificação de integridade
        print("Baixando atualização...")
        with urllib.request.urlopen(exe_url, timeout=30) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            conteudo = response.read()
            
            if len(conteudo) < 5_000_000:  # Mínimo 5MB para um executável válido
                raise Exception("Arquivo baixado parece incompleto ou corrompido.")
            
            with open(novo_exe, 'wb') as out_file:
                out_file.write(conteudo)

        # Verificar se o arquivo baixado é executável válido
        if not os.path.exists(novo_exe):
            raise Exception("Falha ao salvar o arquivo de atualização.")

        # Criar script de atualização mais robusto
        bat_path = os.path.join(temp_dir, "update_safe.bat")
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(f"""@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul

set "old_exe={nome_atual}"
set "new_exe=novo_controle_financeiro.exe"
set "app_path={pasta}"
set "temp_path={temp_dir}"

echo Iniciando processo de atualização...

REM Aguarda o processo anterior fechar completamente
:wait_close
tasklist /fi "imagename eq %old_exe%" 2>nul | find /i "%old_exe%" >nul
if not errorlevel 1 (
    echo Aguardando fechamento do aplicativo...
    timeout /t 3 /nobreak >nul
    goto wait_close
)

REM Cria backup do arquivo atual
echo Criando backup...
if exist "%app_path%\\%old_exe%" (
    copy "%app_path%\\%old_exe%" "%temp_path%\\backup_%old_exe%" >nul 2>&1
)

REM Remove o arquivo antigo
:remove_old
if exist "%app_path%\\%old_exe%" (
    del "%app_path%\\%old_exe%" >nul 2>&1
    if exist "%app_path%\\%old_exe%" (
        timeout /t 3 /nobreak >nul
        goto remove_old
    )
)

REM Move o novo arquivo
echo Instalando nova versão...
move "%temp_path%\\%new_exe%" "%app_path%\\%old_exe%" >nul 2>&1

REM Verifica se a cópia foi bem-sucedida
if exist "%app_path%\\%old_exe%" (
    echo Atualização concluída com sucesso!
    
    REM Inicia o novo aplicativo
    cd /d "%app_path%"
    start "" "%old_exe%"
    
    REM Remove arquivos temporários
    timeout /t 3 /nobreak >nul
    rmdir /s /q "%temp_path%" >nul 2>&1
) else (
    echo ERRO: Falha na atualização!
    REM Restaura backup se disponível
    if exist "%temp_path%\\backup_%old_exe%" (
        echo Restaurando versão anterior...
        copy "%temp_path%\\backup_%old_exe%" "%app_path%\\%old_exe%" >nul 2>&1
    )
    pause
)

REM Remove este script
del "%~f0" >nul 2>&1
endlocal
""")

        # Salvar dados antes de fechar
        salvar_dados()
        
        # Executar script de atualização
        subprocess.Popen([bat_path], shell=True, cwd=temp_dir)
        
        # Fechar aplicativo atual
        app.quit()

    except Exception as e:
        messagebox.showerror("Erro na Atualização", f"Erro ao atualizar:\n{e}\n\nTente baixar manualmente do GitHub.")

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
BASE_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", "ControleFinanceiro")
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
                dados_carregados = conteudo.get("dados", {})
                dados = {
                    tuple(map(int, chave.split("-"))): valor
                    for chave, valor in dados_carregados.items()
                }
                cartoes = conteudo.get("cartoes", [])
                contas_fixas_modelo = conteudo.get("contas_fixas_modelo", [])
                tipos_gasto = conteudo.get("tipos_gasto") or TIPOS_GASTO_PADRAO.copy()
                inicio_uso = tuple(conteudo.get("inicio_uso", [])) or None

                ultima_selecao = conteudo.get("ultima_selecao", {})
                ultima_selecao_cartao = ultima_selecao.get("cartao", None)
                ultima_selecao_tipo = ultima_selecao.get("tipo_gasto", None)
                ultima_selecao_mes = ultima_selecao.get("mes", None)
                ultima_selecao_ano = ultima_selecao.get("ano", None)

                usuarios = conteudo.get("usuarios", [])  # <-- novo

        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            dados, cartoes, contas_fixas_modelo = {}, [], []
            tipos_gasto = TIPOS_GASTO_PADRAO.copy()
            inicio_uso = None
            ultima_selecao_cartao = ultima_selecao_tipo = None
            ultima_selecao_mes = ultima_selecao_ano = None
            usuarios = []  # <-- novo
            messagebox.showwarning("Aviso", f"Erro ao carregar dados salvos. Iniciando com dados limpos.\nErro: {e}")
    else:
        dados, cartoes, contas_fixas_modelo = {}, [], []
        tipos_gasto = TIPOS_GASTO_PADRAO.copy()
        inicio_uso = None
        ultima_selecao_cartao = ultima_selecao_tipo = None
        ultima_selecao_mes = ultima_selecao_ano = None
        usuarios = []  # <-- novo

    for key in dados:
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
TIPOS_GASTO_PADRAO = ["Lazer", "Restaurante", "Supermercado", "Pessoal", "Transporte", "Saúde"]
tipos_gasto = TIPOS_GASTO_PADRAO.copy()

def resource_path(relative_path):
    """Retorna o caminho absoluto para um recurso, funcionando no Python e no EXE."""
    try:
        # PyInstaller cria uma pasta temporária _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def aplicar_icone(janela):
    """Aplica o ícone padrão a uma janela Toplevel."""
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
    frame_central.configure(relief="solid", borderwidth=1, highlightbackground="#e9ecef", highlightthickness=1)

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
            messagebox.showwarning("Atenção", "Nenhum usuário selecionado. Cadastre um novo usuário.")
            return
        global usuario_atual
        usuario_atual = usuario
        login.destroy()  # destrói login e libera janela principal

    def cadastrar():
        def salvar_usuario():
            novo = entry_nome.get().strip()
            if not novo:
                messagebox.showwarning("Atenção", "Digite um nome.")
                return
            if novo in usuarios:
                messagebox.showwarning("Atenção", "Usuário já existe.")
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

        entry_nome = tk.Entry(cadastro_frame, font=("Inter", 11), width=25, relief="solid", bd=1)
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
    APP_BG = "#f8f9fa"  # cinza claro (ou qualquer outra que preferir)

    # altera o fundo padrão para todos os widgets tk.*
    app.option_add("*Background", APP_BG)
    app.option_add("*foreground", "#212529")  # cor padrão do texto

    app.title(f"💰 Controle Financeiro {VERSAO_ATUAL}")
    app.state('zoomed')

    # Carregar ícone (compatível com empacotamento)
    icone = None
    try:
        caminho_icone = resource_path("icone.png")
        icone = tk.PhotoImage(file=caminho_icone)
        app.iconphoto(False, icone)
    except Exception:
        print("⚠️ Ícone icone.png não encontrado.")

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
header_frame = tk.Frame(app, height=80, bg="#0d6efd", relief="flat")
header_frame.pack(fill="x")
header_frame.pack_propagate(False)

welcome_frame = tk.Frame(header_frame, bg="#0d6efd")
welcome_frame.pack(expand=True, fill="both")

global label_bem_vindo
label_bem_vindo = tk.Label(
    welcome_frame,
    text=f"Bem-vindo, {usuario_atual}!",
    font=("Inter", 22, "bold"),
    anchor="center"
)
label_bem_vindo.pack(pady=15, expand=True)

# 🔒 Força as cores manualmente (ignora tema ttkbootstrap)
label_bem_vindo.configure(bg="#d9e3f1", fg="white")


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
        (" 💳     Gerenciar Cartões", gerenciar_cartoes),
        (" 📂     Categorias de Gastos", abrir_gerenciador_categorias),
        (" 🔄     Buscar Atualização", buscar_atualizacao),
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

    ttk.Label(main_frame, text="Mês de início (1 a 12):", font=("Inter", 11)).pack(pady=(15, 5))
    combo_mes = ttk.Combobox(main_frame, values=list(range(1, 13)), state="readonly",
                             justify="center", font=("Inter", 10))
    combo_mes.pack()
    combo_mes.current((inicio_uso[0] - 1) if inicio_uso else 0)

    ttk.Label(main_frame, text="Ano de início (ex: 2023):", font=("Inter", 11)).pack(pady=(15, 5))
    entry_ano = ttk.Entry(main_frame, justify="center", font=("Inter", 10))
    entry_ano.pack()
    entry_ano.insert(0, str(inicio_uso[1]) if inicio_uso else str(datetime.now().year))

    # ---------------- Função para mensagens com ícone ----------------
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
        ttk.Label(frame, text=mensagem, font=("Inter", 11), justify="center", wraplength=320).pack(pady=10)

        def fechar():
            msg_janela.destroy()
            if ao_fechar:
                ao_fechar()

        ttk.Button(frame, text="OK", command=fechar,
                   bootstyle="success" if tipo=="info" else "danger").pack()

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
            recalcular_saldos_em_cadeia()
            atualizar_resumo()

            mostrar_mensagem("Sucesso", f"Início do uso definido para {mes:02d}/{ano}", tipo="info",
                             ao_fechar=lambda: janela.destroy())

        except ValueError as ve:
            mostrar_mensagem("Erro de validação", f"Erro: {ve}", tipo="erro")
        except Exception:
            mostrar_mensagem("Erro", "Preencha os campos corretamente.", tipo="erro")

    ttk.Button(main_frame, text="✓ Confirmar", command=confirmar, bootstyle="success").pack(pady=20)
    janela.bind('<Return>', lambda event: confirmar())

def gerenciar_cartoes():
    janela = tk.Toplevel(app)
    janela.title("Gerenciar Cartões")
    janela.resizable(False, False)
    janela.attributes("-topmost", True)
    janela.grab_set()
    janela.configure(bg="#f8f9fa")

    centralizar_janela(janela, 350, 280)

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

def adicionar_cartao(janela_anterior):
    janela_anterior.destroy()
    janela = tk.Toplevel(app)
    janela.title("Adicionar Cartão")
    janela.configure(bg="#f8f9fa")

    largura = 350
    altura = 300
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.attributes("-topmost", True)
    janela.grab_set()

    main_frame = tk.Frame(janela, bg="#f8f9fa", padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="Nome do Cartão:", font=("Inter", 11)).pack(pady=8)
    entrada_nome = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_nome.pack(pady=5)

    ttk.Label(main_frame, text="Dia de Fechamento da Fatura (1-31):", font=("Inter", 11)).pack(pady=8)
    entrada_fechamento = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_fechamento.pack(pady=5)

    def mostrar_erro_toplevel(mensagem):
        erro_janela = tk.Toplevel(janela)
        erro_janela.title("Erro")
        erro_janela.geometry("350x120")
        erro_janela.attributes("-topmost", True)
        erro_janela.grab_set()
        erro_janela.configure(bg="#f8f9fa")

        erro_frame = tk.Frame(erro_janela, bg="#f8f9fa", padx=15, pady=15)
        erro_frame.pack(fill="both", expand=True)

        ttk.Label(erro_frame, text=mensagem, foreground="#dc3545", wraplength=300,
                 font=("Inter", 10)).pack(pady=10)
        ttk.Button(erro_frame, text="OK", command=erro_janela.destroy, 
                  bootstyle="danger").pack()

        erro_janela.update_idletasks()
        w = erro_janela.winfo_width()
        h = erro_janela.winfo_height()
        x = janela.winfo_rootx() + (janela.winfo_width() // 2) - (w // 2)
        y = janela.winfo_rooty() + (janela.winfo_height() // 2) - (h // 2)
        erro_janela.geometry(f"+{x}+{y}")

    def salvar():
        nome = entrada_nome.get().strip()
        fechamento_str = entrada_fechamento.get().strip()

        if not nome:
            mostrar_erro_toplevel("Nome do cartão não pode ser vazio.")
            return
        if not fechamento_str.isdigit():
            mostrar_erro_toplevel("Dia de fechamento deve ser um número entre 1 e 31.")
            return
        fechamento = int(fechamento_str)
        if not (1 <= fechamento <= 31):
            mostrar_erro_toplevel("Dia de fechamento deve estar entre 1 e 31.")
            return

        for c in cartoes:
            if c['nome'].lower() == nome.lower():
                mostrar_erro_toplevel("Cartão com esse nome já existe.")
                return

        cartoes.append({"nome": nome, "fechamento": fechamento})

        atualizar_resumo()
        janela.destroy()

    ttk.Button(main_frame, text="💾 Salvar", command=salvar, 
               bootstyle="success").pack(pady=20)

    # Bind para tecla Enter ativar salvar
    janela.bind("<Return>", lambda event: salvar())
    aplicar_icone(janela)

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

    ttk.Label(main_frame, text="Selecione o cartão para editar:", font=("Inter", 11)).pack(pady=8)

    combo_cartoes = ttk.Combobox(main_frame, state="readonly", values=[c['nome'] for c in cartoes],
                                 font=("Inter", 10))
    combo_cartoes.pack(pady=5)

    ttk.Label(main_frame, text="Novo nome do Cartão:", font=("Inter", 11)).pack(pady=(15, 5))
    entrada_nome = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_nome.pack(pady=5)

    ttk.Label(main_frame, text="Novo dia de Fechamento da Fatura (1-31):", font=("Inter", 11)).pack(pady=(15, 5))
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
            mostrar_erro_toplevel("Dia de fechamento deve ser um número entre 1 e 31.", janela)
            return
        fechamento = int(fechamento_str)
        if not (1 <= fechamento <= 31):
            mostrar_erro_toplevel("Dia de fechamento deve estar entre 1 e 31.", janela)
            return

        # Verificar se já existe outro cartão com esse nome (exceto o atual)
        for i, c in enumerate(cartoes):
            if i != idx and c['nome'].lower() == novo_nome.lower():
                mostrar_erro_toplevel("Já existe um cartão com esse nome.", janela)
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

        ttk.Label(frame, text="Cartão atualizado com sucesso!", font=("Inter", 11)).pack(pady=10)
        ttk.Button(frame, text="OK", command=sucesso_janela.destroy, bootstyle="success").pack()

    ttk.Button(main_frame, text="💾 Salvar Alterações", command=salvar, bootstyle="success").pack(pady=20)
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

    ttk.Label(main_frame, text="Selecione o cartão para excluir:", font=("Inter", 11)).pack(pady=8)

    combo_cartoes = ttk.Combobox(main_frame, state="readonly", font=("Inter", 10))
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
    largura, altura = 360, 200
    x = (app.winfo_screenwidth() // 2) - (largura // 2)
    y = (app.winfo_screenheight() // 2) - (altura // 2)
    senha_janela.geometry(f"{largura}x{altura}+{x}+{y}")
    senha_janela.grab_set()
    senha_janela.attributes("-topmost", True)
    senha_janela.configure(bg="#f8f9fa")
    aplicar_icone(senha_janela)

    frame_senha = tk.Frame(senha_janela, bg="#f8f9fa", padx=20, pady=20)
    frame_senha.pack(fill="both", expand=True)

    ttk.Label(frame_senha, text="Digite a senha para zerar todos os dados:", font=("Inter", 11)).pack(pady=(0, 10))
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
            largura, altura = 360, 200
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

                frame_info = tk.Frame(info_janela, bg="#f8f9fa", padx=20, pady=20)
                frame_info.pack(fill="both", expand=True)
                ttk.Label(frame_info, text="Todos os dados foram apagados e os tipos de gastos foram restaurados.",
                          font=("Inter", 11), justify="center", wraplength=320).pack(pady=10)
                ttk.Button(frame_info, text="OK", command=lambda: (info_janela.destroy(), app.destroy(), sys.exit()),
                           bootstyle="secondary").pack()

            ttk.Button(botoes, text="✓ Sim", command=sim, bootstyle="danger").pack(side="left", padx=10)
            ttk.Button(botoes, text="✗ Não", command=confirm_janela.destroy, bootstyle="secondary").pack(side="right", padx=10)
        else:
            # Janela de erro customizada
            erro_janela = tk.Toplevel(app)
            erro_janela.title("Senha incorreta")
            erro_janela.resizable(False, False)
            largura, altura = 360, 180
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
            ttk.Button(frame_erro, text="OK", command=erro_janela.destroy, bootstyle="danger").pack()

    ttk.Button(frame_senha, text="✓ Confirmar", command=verificar_senha, bootstyle="success").pack(pady=10)
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
        messagebox.showinfo("Exportação", "Dados exportados com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao exportar dados:\n{e}")

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
        messagebox.showinfo("Importação", "Dados importados com sucesso!")

        # Fecha completamente o app
        app.destroy()

    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao importar dados:\n{e}")

def trocar_usuario():
    global usuario_atual

    if not usuarios:
        messagebox.showinfo("Aviso", "Nenhum usuário cadastrado.", parent=app)
        return

    janela = tk.Toplevel(app)
    janela.title("Trocar Usuário")
    janela.resizable(False, False)
    centralizar_janela(janela, 320, 200)
    janela.grab_set()
    janela.attributes("-topmost", True)

    main_frame = tk.Frame(janela, padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="Selecione o usuário:", font=("Inter", 11)).pack(pady=10)

    combo = ttk.Combobox(main_frame, state="readonly", values=usuarios, font=("Inter", 10))
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

        ttk.Label(frame, text=mensagem, font=("Inter", 10), wraplength=260).pack(pady=15)
        ttk.Button(
            frame,
            text="OK",
            command=lambda: [sucesso_janela.destroy(), ao_fechar() if ao_fechar else None],
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

    ttk.Button(main_frame, text="✓ Confirmar", command=confirmar, bootstyle="success").pack(pady=15)
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

    ttk.Label(main_frame, text="👥 Lista de Usuários", font=("Inter", 14, "bold")).pack(pady=(0, 10))

    lista_usuarios = tk.Listbox(main_frame, font=("Inter", 10), height=8, 
                               selectbackground="#0d6efd", selectforeground="#ffffff")
    lista_usuarios.pack(pady=10, fill="both", expand=True)
    lista_usuarios.insert(tk.END, *usuarios)

    def adicionar():
        def salvar_novo_usuario():
            nome = entry_nome.get().strip()
            if not nome:
                messagebox.showwarning("Atenção", "Digite um nome.", parent=janela_adicionar)
                return
            if nome in usuarios:
                messagebox.showwarning("Atenção", "Usuário já existe.", parent=janela_adicionar)
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

        tk.Label(frame, text="Nome do usuário:", font=("Inter", 11)).pack(pady=(0, 8))
        entry_nome = ttk.Entry(frame, font=("Inter", 10))
        entry_nome.pack(pady=(0, 10))
        entry_nome.focus()
        entry_nome.bind("<Return>", lambda event: salvar_novo_usuario())

        ttk.Button(frame, text="💾 Salvar", command=salvar_novo_usuario, bootstyle="success").pack()

    def excluir():
        idx = lista_usuarios.curselection()
        if not idx:
            messagebox.showwarning("Atenção", "Selecione um usuário para excluir.", parent=janela)
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

        ttk.Button(botoes, text="✓ Sim", command=confirmar_exclusao, bootstyle="danger").pack(side="left", padx=10)
        ttk.Button(botoes, text="✗ Não", command=confirm_janela.destroy, bootstyle="secondary").pack(side="right", padx=10)

    botoes = ttk.Frame(main_frame)
    botoes.pack(pady=10)
    ttk.Button(botoes, text="➕ Adicionar", command=adicionar, bootstyle="success").pack(side="left", padx=8)
    ttk.Button(botoes, text="🗑️ Excluir", command=excluir, bootstyle="danger").pack(side="right", padx=8)

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
    global inicio_uso
    chave = get_chave(mes, ano)

    if inicio_uso:
        mes_inicio, ano_inicio = inicio_uso

        if (ano < ano_inicio) or (ano == ano_inicio and mes < mes_inicio):
            if chave not in dados:
                dados[chave] = {
                    "receitas": {},
                    "conta": 0.0,
                    "despesas_fixas": [],
                    "gastos": [],
                    "cartao_credito": carregar_parcelas_cartao_para_mes(mes, ano),
                    "tipos": []
                }
            return dados[chave]

    if chave not in dados:
        despesas_validas = []
        for d in contas_fixas_modelo:
            mes_inicio_d, ano_inicio_d = d.get("inicio", (1, 1900))
            if (ano_inicio_d, mes_inicio_d) <= (ano, mes):
                despesas_validas.append(d)

        dados[chave] = {
            "receitas": {},
            "conta": 0.0,
            "despesas_fixas": copy.deepcopy(despesas_validas),
            "gastos": [],
            "cartao_credito": carregar_parcelas_cartao_para_mes(mes, ano),
            "tipos": []
        }

        mes_ant = mes - 1 if mes > 1 else 12
        ano_ant = ano if mes > 1 else ano - 1

        if (ano_ant > ano_inicio) or (ano_ant == ano_inicio and mes_ant >= mes_inicio):
            chave_anterior = get_chave(mes_ant, ano_ant)
            if chave_anterior in dados:
                info_ant = dados[chave_anterior]

                total_receitas_ant = sum(info_ant["receitas"].values())
                total_gastos_ant = sum(g["valor"] for g in info_ant["gastos"])
                total_credito_ant = sum(c["valor"] for c in info_ant["cartao_credito"])
                total_despesas_todas_ant = sum(d["valor"] for d in info_ant["despesas_fixas"])

                saldo_final_mes_anterior = (
                    info_ant["conta"]
                    + total_receitas_ant
                    - total_gastos_ant
                    - total_credito_ant
                    - total_despesas_todas_ant
                )

                dados[chave]["conta"] = saldo_final_mes_anterior
        else:
            dados[chave]["conta"] = 0.0

    return dados[chave]

def calcular_saldo(chave):
    info = dados[chave]
    total_receitas = sum(info["receitas"].values())
    total_despesas_pagas = sum(d["valor"] for d in info["despesas_fixas"] if d["status"] == "Pago")
    total_gastos = sum(g["valor"] for g in info["gastos"])
    total_credito_pago = sum(c["valor"] for c in info["cartao_credito"]
                             if c["mes"] == chave[0] and c["ano"] == chave[1] and c.get("status") == "Pago")
    return total_receitas - total_gastos - total_credito_pago - total_despesas_pagas

def recalcular_saldo_inicial(chave):
    mes, ano = chave
    mes_ant = mes - 1 if mes > 1 else 12
    ano_ant = ano if mes > 1 else ano - 1
    chave_anterior = (mes_ant, ano_ant)

    if not inicio_uso:
        return

    mes_inicio, ano_inicio = inicio_uso

    # Se o mês anterior for anterior ao início de uso, saldo inicial será 0
    if (ano_ant < ano_inicio) or (ano_ant == ano_inicio and mes_ant < mes_inicio):
        dados[chave]["conta"] = 0.0
        return

    if chave_anterior in dados:
        info_ant = dados[chave_anterior]

        total_receitas_ant = sum(info_ant["receitas"].values())
        total_gastos_ant = sum(g["valor"] for g in info_ant["gastos"])
        total_credito_ant = sum(c["valor"] for c in info_ant["cartao_credito"])
        total_despesas_todas_ant = sum(d["valor"] for d in info_ant["despesas_fixas"])

        saldo_final_mes_anterior = (
            info_ant["conta"]
            + total_receitas_ant
            - total_gastos_ant
            - total_credito_ant
            - total_despesas_todas_ant
        )

        dados[chave]["conta"] = saldo_final_mes_anterior

def recalcular_saldos_em_cadeia():
    if not inicio_uso:
        return

    mes_inicio, ano_inicio = inicio_uso
    mes_atual = combo_mes.current() + 1
    ano_atual = int(combo_ano.get())

    ano, mes = ano_inicio, mes_inicio

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

def atualizar_resumo(*args):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)

    if chave not in dados:
        inicializar_mes(mes, ano)
    else:
        recalcular_saldo_inicial(chave)

    info = dados[chave]

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

    # --- RECEITAS ---
    total_receitas = sum(info["receitas"].values())
    frame_receitas_topo = criar_cabecalho_com_detalhes(
        scroll_frame_receitas,
        "Receitas",
        total_receitas,
        lambda: adicionar_valor("Adicionar Receita", "receita"),
        lambda: None
    )

    frame_receitas_conteudo = tk.Frame(frame_receitas_topo, bg="#d9e3f1", padx=18, pady=15)
    frame_receitas_conteudo.pack(fill="x")

    for nome, valor in list(info["receitas"].items()):
        frame_linha = tk.Frame(frame_receitas_conteudo, bg="#d9e3f1")
        frame_linha.pack(anchor="w", fill="x", pady=5)

        label_receita = tk.Label(
            frame_linha,
            text=f"{nome}: {locale.currency(valor, grouping=True)}",
            font=("Inter", 12, "bold"),
            bg="#d9e3f1"
        )
        label_receita.configure(fg="#28a745")  # verde
        label_receita.pack(side="left", anchor="w")

        btn_editar = tk.Label(
            frame_linha,
            text="✏️",
            font=("Inter", 14, "bold"),
            fg="white",
            bg="#d9e3f1",
            cursor="hand2"
        )
        btn_editar.pack(side="right", anchor="e", padx=8)
        btn_editar.bind("<Button-1>", lambda e, n=nome: editar_receita(n))

        btn_excluir = tk.Label(
            frame_linha,
            text="🗑️",
            font=("Inter", 14, "bold"),
            fg="#dc3545",
            bg="#d9e3f1",
            cursor="hand2"
        )
        btn_excluir.pack(side="right", anchor="e", padx=5)
        btn_excluir.bind("<Button-1>", lambda e, n=nome: excluir_receita(n))

    # --- DESPESAS FIXAS ---
    total_despesas_fixas = sum(d["valor"] for d in info["despesas_fixas"])
    frame_despesas_topo = criar_cabecalho_com_detalhes(
        scroll_frame_despesas,
        "Despesas Fixas",
        total_despesas_fixas,
        adicionar_despesa_fixa,
        lambda: None
    )

    frame_despesa_conteudo = tk.Frame(frame_despesas_topo, bg="#d9e3f1", padx=18, pady=15)
    frame_despesa_conteudo.pack(fill="x")

    despesas_ordenadas = sorted(info["despesas_fixas"], key=lambda d: d.get("vencimento", 99))

    from calendar import monthrange
    hoje = datetime.today()
    ultimo_dia_mes = monthrange(ano, mes)[1]

    for idx, d in enumerate(despesas_ordenadas):
        vencimento = d.get("vencimento", "??")
        status = d["status"]

        # Define a cor baseada no status e vencimento
        if status == "Pago":
            cor = "#28a745"  # verde
        elif status == "Aberto":
            if isinstance(vencimento, int):
                venc_data = datetime(ano, mes, min(vencimento, ultimo_dia_mes))
                cor = "#dc3545" if venc_data < hoje else "#0d6efd"  # vermelho ou azul
            else:
                cor = "#0d6efd"
        else:
            cor = "#212529"

        texto = f"{d['descricao']} - {locale.currency(d['valor'], grouping=True)} - Venc: {vencimento} ({status})"

        container = tk.Frame(frame_despesa_conteudo, bg="#d9e3f1")
        container.pack(fill="x", pady=3)

        # Botão editar
        btn_editar = tk.Label(container, text="✏️", font=("Inter", 14, "bold"), fg="white", bg="#d9e3f1", cursor="hand2")
        btn_editar.pack(side="left", padx=(0, 10))
        btn_editar.bind("<Button-1>", lambda e, i=idx: editar_despesa_fixa(i))

        # Botão excluir
        btn_excluir = tk.Label(container, text="🗑️", font=("Inter", 14, "bold"), fg="#dc3545", bg="#d9e3f1", cursor="hand2")
        btn_excluir.pack(side="left", padx=(0, 10))
        btn_excluir.bind("<Button-1>", lambda e, i=idx: excluir_despesa_fixa(i))

        # Label da despesa com cor condicional
        label_despesa = tk.Label(container, text=texto, font=("Inter", 12, "bold"), bg="#d9e3f1")
        label_despesa.configure(fg=cor)
        label_despesa.pack(side="left", anchor="w")

    # --- GASTOS DIÁRIOS ---
    total_gastos = sum(g["valor"] for g in info["gastos"])
    criar_cabecalho_com_detalhes(
        scroll_frame_gastos,
        "Gastos Diários",
        total_gastos,
        lambda: adicionar_valor("Adicionar Gasto", "gasto"),
        mostrar_gastos_detalhados
    )

    # --- CARTÃO DE CRÉDITO ---
    gastos_por_cartao = {}
    for c in info["cartao_credito"]:
        nome = c["cartao"]
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
    saldo_inicial = info["conta"]
    total_pagas = sum(d["valor"] for d in info["despesas_fixas"] if d["status"] == "Pago")
    total_todas = sum(d["valor"] for d in info["despesas_fixas"])

    saldo_atual = saldo_inicial + total_receitas - total_gastos - total_cartao_pago - total_pagas
    saldo_final = saldo_inicial + total_receitas - total_gastos - total_cartao_todos - total_todas

    cor_saldo_atual = "#0d6efd" if saldo_atual >= 0 else "#dc3545"
    cor_saldo_final = "#0d6efd" if saldo_final >= 0 else "#dc3545"

    resumo_container = tk.Frame(frame_resumo, bg="#d9e3f1", padx=15, pady=15)
    resumo_container.pack(fill="x", pady=5)

    label_saldo_atual = tk.Label(resumo_container,
                                 text=f"💰 Saldo Atual: {locale.currency(saldo_atual, grouping=True)}",
                                 font=("Inter", 12, "bold"),
                                 bg="#d9e3f1")
    label_saldo_atual.configure(fg=cor_saldo_atual)
    label_saldo_atual.pack(anchor="w")

    label_saldo_final = tk.Label(resumo_container,
                                 text=f"📊 Saldo Final: {locale.currency(saldo_final, grouping=True)}",
                                 font=("Inter", 12, "bold"),
                                 bg="#d9e3f1")
    label_saldo_final.configure(fg=cor_saldo_final)
    label_saldo_final.pack(anchor="w", pady=(5, 0))
    
    label_gastos_tipo = tk.Label(
        resumo_container,
        text="📈 Gastos por Tipo:",
        font=("Inter", 12, "bold"),
        bg="#d9e3f1",
        fg="#0d6efd"  # azul padrão do app
    )
    label_gastos_tipo.configure(fg="#7B8ACB")
    label_gastos_tipo.pack(anchor="w", pady=(15, 5))

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

    gastos_ordenados = sorted(enumerate(info["gastos"]), key=lambda x: (x[1].get("dia", 99), x[1].get("tipo", ""), x[1].get("descricao", "")))
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

        gastos_por_tipo = defaultdict(list)
        for idx, gasto in lista:
            tipo = gasto.get("tipo", "Indefinido")
            gastos_por_tipo[tipo].append(gasto)

        for tipo, gastos_lista in sorted(gastos_por_tipo.items()):
            label_tipo = ttk.Label(frame_detalhes, text=f"🏷️ {tipo}:", font=("Inter", 11, "bold"), 
                                 foreground="#495057")
            label_tipo.pack(anchor="w", padx=12, pady=(8, 3))

            for idx, gasto in enumerate(info["gastos"]):
                if gasto in gastos_lista:
                    valor_fmt = locale.currency(gasto["valor"], grouping=True)
                    desc = gasto.get("descricao", "Sem descrição")
                    usuario = gasto.get("usuario", "Desconhecido")
                    gasto_text = f"• {desc}: {valor_fmt} (Responsável: {usuario})"

                    container_gasto = ttk.Frame(frame_detalhes)
                    container_gasto.pack(anchor="w", fill="x", padx=35, pady=3)

                    ttk.Label(container_gasto, text=gasto_text, font=("Inter", 10), 
                            foreground="#212529").pack(side="left")

                    btn_editar = ttk.Label(container_gasto, text="✏️", font=("Inter", 12), 
                                         foreground="#0d6efd", cursor="hand2")
                    btn_editar.pack(side="left", padx=10)
                    btn_editar.bind("<Button-1>", lambda e, idx=idx: editar_gasto_diario(idx, callback_apos_salvar=recarregar_callback))

                    btn_excluir = ttk.Label(container_gasto, text="🗑️", font=("Inter", 12), 
                                          foreground="#dc3545", cursor="hand2")
                    btn_excluir.pack(side="left")
                    btn_excluir.bind("<Button-1>", lambda e, idx=idx: excluir_gasto_diario(
                        idx, janela_detalhes=janela_detalhes, callback_apos_excluir=recarregar_callback))

        label_dia.bind("<Button-1>", lambda e, f=frame_detalhes, d=dia: toggle_detalhes_gastos(f, d))
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

    frame_container = ttk.Frame()  # Placeholder

    def recarregar_gastos():
        for widget in frame_container.winfo_children():
            widget.destroy()
        _renderizar_gastos(
            container=frame_container,
            recarregar_callback=recarregar_gastos,
            janela_detalhes=nova_janela
        )

    btn_adicionar = ttk.Button(
        frame_centro,
        text="➕ Adicionar Gasto Diário",
        command=lambda: adicionar_valor("Adicionar Gasto", "gasto", callback_apos_salvar=recarregar_gastos),
        bootstyle="success"
    )
    btn_adicionar.pack(pady=15)

    canvas = tk.Canvas(nova_janela, highlightthickness=0)
    scrollbar = ttk.Scrollbar(nova_janela, orient="vertical", command=canvas.yview)
    frame_container = ttk.Frame(canvas)

    canvas.create_window((0, 0), window=frame_container, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    frame_container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Rolagem do mouse
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

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
            c.create_arc(x0, y0, x0+2*r, y0+2*r, start=90, extent=90, fill=fill, outline=fill)
            c.create_arc(x1-2*r, y0, x1, y0+2*r, start=0, extent=90, fill=fill, outline=fill)
            c.create_arc(x0, y1-2*r, x0+2*r, y1, start=180, extent=90, fill=fill, outline=fill)
            c.create_arc(x1-2*r, y1-2*r, x1, y1, start=270, extent=90, fill=fill, outline=fill)
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

        lista_gastos = [g for g in info_atual["cartao_credito"] if g["cartao"] == nome_cartao_local]

        novo_status = "Aberto" if all(g.get("status") == "Pago" for g in lista_gastos) else "Pago"

        for g in lista_gastos:
            g["status"] = novo_status

        salvar_dados()
        atualizar_resumo()
        _renderizar_gastos_cartao(scroll_frame, parent_janela=parent_janela, recarregar_callback=recarregar_callback)

    def recarregar_gastos():
        _renderizar_gastos_cartao(scroll_frame, parent_janela=parent_janela, recarregar_callback=recarregar_callback)

    for nome_cartao in sorted(gastos_por_cartao):
        lista = sorted(gastos_por_cartao[nome_cartao], key=lambda x: (x["ano"], x["mes"], x["dia"]))
        total_cartao = sum(g["valor"] for g in lista)

        status_cartao = "Pago" if all(g.get("status") == "Pago" for g in lista) else "Aberto"

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

        badge = criar_badge_status(frame_titulo, status_cartao, partial(alternar_status_cartao, nome_cartao))
        badge.grid(row=0, column=1, sticky="e", padx=(2,0))

        label.bind("<Enter>", lambda e: label.config(foreground="#0a58ca"))
        label.bind("<Leave>", lambda e: label.config(foreground="#0d6efd"))

        frame_detalhes = ttk.Frame(container_cartao, padding=(12, 8))

        label.bind(
            "<Button-1>",
            lambda e, f=frame_detalhes, l=label, n=nome_cartao, t=total_cartao: toggle_detalhes(f, l, n, t)
        )

        for c in lista:
            parcela = "Fixo" if c.get("fixo") else (f"Parcela {c['parcela_atual']}/{c['total_parcelas']}" if c["total_parcelas"] > 1 else "À vista")
            data = f"{c['dia']:02d}/{c['mes']:02d}/{c['ano']}"
            tipo = c.get("tipo", "Indefinido")
            valor_fmt = locale.currency(c["valor"], grouping=True)
            texto = f"• {data}: {c['descricao']} - {valor_fmt} ({parcela}) - Tipo: {tipo}"

            container = ttk.Frame(frame_detalhes)
            container.pack(anchor="w", fill="x", padx=12, pady=3)

            ttk.Label(container, text=texto, font=("Inter", 10, "bold")).pack(side="left")

            btn_editar = ttk.Label(container, text="✏️", font=("Inter", 12), foreground="#0d6efd", cursor="hand2")
            btn_editar.pack(side="left", padx=10)
            btn_editar.bind("<Button-1>", partial(lambda e, gasto: editar_gasto_cartao(gasto, callback_apos_salvar=recarregar_callback), gasto=c))

            btn_excluir = ttk.Label(container, text="🗑️", font=("Inter", 12), foreground="#dc3545", cursor="hand2")
            btn_excluir.pack(side="left")
            btn_excluir.bind("<Button-1>", partial(lambda e, gasto: excluir_gasto_cartao(gasto, parent_janela=parent_janela, callback_apos_excluir=recarregar_gastos), gasto=c))

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
        command=lambda: adicionar_cartao_credito(callback_apos_salvar=recarregar_gastos),
        bootstyle="success"
    )
    btn_adicionar.pack(pady=15)

    container = ttk.Frame(janela_gastos_detalhados, padding=18)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container, highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
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
        _renderizar_gastos_cartao(scroll_frame, parent_janela=janela_gastos_detalhados, recarregar_callback=recarregar_gastos)

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
    janela = tk.Toplevel(app)
    janela.title("Nova Despesa Fixa")
    largura, altura = 350, 350
    janela.geometry(f"{largura}x{altura}")
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.attributes("-topmost", True)
    janela.grab_set()

    main_frame = tk.Frame(janela, padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="Descrição:", font=("Inter", 11)).pack(pady=8)
    entrada_desc = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_desc.pack(pady=5)

    ttk.Label(main_frame, text="Valor (R$):", font=("Inter", 11)).pack(pady=8)
    entrada_valor = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_valor.pack(pady=5)

    ttk.Label(main_frame, text="Dia de vencimento (1 a 31):", font=("Inter", 11)).pack(pady=8)
    entrada_venc = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_venc.pack(pady=5)

    def salvar():
        descricao = entrada_desc.get().strip()

        try:
            valor = float(entrada_valor.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Erro", "Valor inválido.", parent=janela)
            entrada_valor.focus_set()
            return

        try:
            vencimento = int(entrada_venc.get())
            if not (1 <= vencimento <= 31):
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Dia de vencimento inválido (deve ser 1 a 31).", parent=janela)
            entrada_venc.focus_set()
            return

        if not descricao:
            messagebox.showerror("Erro", "Descrição não pode ser vazia.", parent=janela)
            entrada_desc.focus_set()
            return

        mes_selecionado = combo_mes.current() + 1
        ano_selecionado = int(combo_ano.get())

        nova = {
            "descricao": descricao,
            "valor": valor,
            "vencimento": vencimento,
            "status": "Aberto",
            "inicio": (ano_selecionado, mes_selecionado)  # <-- aqui ajustado para (ano, mes)
        }
        contas_fixas_modelo.append(nova)

        ano = ano_selecionado
        mes = mes_selecionado
        while ano <= 2030:
            chave = get_chave(mes, ano)
            if chave in dados:
                dados[chave]["despesas_fixas"].append(nova.copy())

            mes += 1
            if mes > 12:
                mes = 1
                ano += 1

        atualizar_resumo()
        janela.destroy()

    ttk.Button(main_frame, text="💾 Salvar", command=salvar, 
               bootstyle="success").pack(pady=20)
    janela.bind("<Return>", lambda event: salvar())
    aplicar_icone(janela)

def adicionar_cartao_credito(callback_apos_salvar=None):
    global ultima_selecao_cartao, ultima_selecao_tipo

    if not cartoes:
        mostrar_erro_toplevel("Nenhum cartão cadastrado. Cadastre um cartão primeiro.", app)
        return

    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)
    inicializar_mes(mes, ano)

    janela = tk.Toplevel(app)
    janela.title("Gasto no Cartão")

    largura = 500
    altura = 550
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.attributes("-topmost", True)
    janela.grab_set()

    main_frame = tk.Frame(janela, padx=25, pady=25)
    main_frame.pack(fill="both", expand=True)

    ultimo_cartao = ultima_selecao_cartao if ultima_selecao_cartao in [c["nome"] for c in cartoes] else cartoes[0]["nome"]
    ultimo_tipo = ultima_selecao_tipo if ultima_selecao_tipo in tipos_gasto else tipos_gasto[0]

    ttk.Label(main_frame, text="Descrição:", font=("Inter", 11)).pack(pady=5)
    entrada_desc = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_desc.pack(pady=5)

    ttk.Label(main_frame, text="Valor Total (R$):", font=("Inter", 11)).pack(pady=5)
    entrada_valor = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_valor.pack(pady=5)

    ttk.Label(main_frame, text="Parcelas:", font=("Inter", 11)).pack(pady=5)
    entrada_parcelas = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_parcelas.insert(0, "1")
    entrada_parcelas.pack(pady=5)

    ttk.Label(main_frame, text="Data do Gasto (DDMMAAAA):", font=("Inter", 11)).pack(pady=5)
    entrada_data = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_data.pack(pady=5)

    ttk.Label(main_frame, text="Tipo de Gasto:", font=("Inter", 11)).pack(pady=5)
    combo_tipo = ttk.Combobox(main_frame, values=tipos_gasto, state="readonly", font=("Inter", 10))
    combo_tipo.set(ultimo_tipo)
    combo_tipo.pack(pady=5)

    ttk.Label(main_frame, text="Cartão:", font=("Inter", 11)).pack(pady=5)
    nomes_cartoes = [c["nome"] for c in cartoes]
    cartao_combo = ttk.Combobox(main_frame, values=nomes_cartoes, state="readonly", font=("Inter", 10))
    cartao_combo.set(ultimo_cartao)
    cartao_combo.pack(pady=5)

    fixo_var = tk.BooleanVar()
    check_fixo = ttk.Checkbutton(main_frame, text="Gasto Fixo (repetir todo mês)", variable=fixo_var)
    check_fixo.pack(pady=8)

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
            mostrar_erro_toplevel("Por favor, preencha todos os campos.", janela)
            return

        try:
            valor = float(valor_raw.replace(",", "."))
            parcelas = int(parcelas_raw)
            cartao_info = next((c for c in cartoes if c["nome"] == cartao_nome), None)
            if not cartao_info:
                mostrar_erro_toplevel("Cartão selecionado não encontrado.", janela)
                return

            cartao = cartao_info["nome"]
            fechamento = cartao_info.get("fechamento")
            dia, mes_gasto, ano_gasto = formatar_data(data_raw)

            if parcelas < 1:
                raise ValueError("Parcelas devem ser >= 1.")
            if fechamento is None:
                raise ValueError(f"Cartão '{cartao}' não tem dia de fechamento cadastrado.")

        except Exception as e:
            mostrar_erro_toplevel(f"Dados inválidos: {str(e)}", janela)
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
                "status": "Aberto"  # Adicionado aqui ✅
            })

        ultima_selecao_cartao = cartao
        ultima_selecao_tipo = tipo
        salvar_dados()
        atualizar_resumo()
        if callback_apos_salvar:
            callback_apos_salvar()
        janela.destroy()

    botao_salvar = ttk.Button(main_frame, text="💾 Salvar", command=salvar, 
                             bootstyle="success")
    botao_salvar.pack(pady=20)
    janela.bind("<Return>", salvar)
    aplicar_icone(janela)

def editar_gasto_diario(idx, callback_apos_salvar=None):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    info = inicializar_mes(mes, ano)

    if idx < 0 or idx >= len(info["gastos"]):
        messagebox.showerror("Erro", "Índice de gasto inválido")
        return

    gasto = info["gastos"][idx]

    janela = tk.Toplevel(app)
    janela.title("Editar Gasto Diário")

    largura, altura = 420, 280
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.resizable(False, False)

    main_frame = tk.Frame(janela,padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="Descrição:", font=("Inter", 11)).pack(padx=10, pady=(10, 0), anchor="w")
    entry_descricao = ttk.Entry(main_frame, font=("Inter", 10))
    entry_descricao.pack(padx=10, pady=8, fill="x")
    entry_descricao.insert(0, gasto["descricao"])

    ttk.Label(main_frame, text="Valor:", font=("Inter", 11)).pack(padx=10, pady=(10, 0), anchor="w")
    entry_valor = ttk.Entry(main_frame, font=("Inter", 10))
    entry_valor.pack(padx=10, pady=8, fill="x")
    entry_valor.insert(0, str(gasto["valor"]))

    def salvar(event=None):
        nova_desc = entry_descricao.get().strip()
        try:
            novo_valor = float(entry_valor.get().replace(",", "."))
        except:
            messagebox.showerror("Erro", "Valor inválido")
            return

        if not nova_desc:
            messagebox.showerror("Erro", "Descrição não pode estar vazia")
            return

        info["gastos"][idx]["descricao"] = nova_desc
        info["gastos"][idx]["valor"] = novo_valor

        salvar_dados()
        janela.destroy()
        atualizar_resumo()
        if callback_apos_salvar:
            callback_apos_salvar()

    ttk.Button(main_frame, text="💾 Salvar", command=salvar, 
               bootstyle="success").pack(pady=15)
    janela.bind("<Return>", salvar)
    entry_descricao.focus_set()
    aplicar_icone(janela)

def adicionar_valor(titulo, tipo, callback_apos_salvar=None):
    global usuario_atual  # garante que usamos a variável global
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)
    inicializar_mes(mes, ano)

    janela = tk.Toplevel(app)
    janela.title(titulo)

    largura = 350
    altura = 350 if tipo == "gasto" else 250
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.attributes("-topmost", True)
    janela.grab_set()

    main_frame = tk.Frame(janela, padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="Descrição:", font=("Inter", 11)).pack(pady=5)
    entrada_desc = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_desc.pack(pady=5)

    ttk.Label(main_frame, text="Valor (R$):", font=("Inter", 11)).pack(pady=5)
    entrada_valor = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_valor.pack(pady=5)

    if tipo == "gasto":
        ttk.Label(main_frame, text="Dia do Gasto (1-31):", font=("Inter", 11)).pack(pady=5)
        entrada_dia = ttk.Entry(main_frame, font=("Inter", 10))
        entrada_dia.pack(pady=5)

        ttk.Label(main_frame, text="Tipo de Gasto:", font=("Inter", 11)).pack(pady=5)
        tipo_gasto_combo = ttk.Combobox(main_frame, state="readonly", font=("Inter", 10))
        tipo_gasto_combo.pack(pady=5)
        atualizar_tipo_gasto_combo(tipo_gasto_combo)

    def mostrar_erro_toplevel(mensagem, parent=janela):
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

    def salvar():
        desc = entrada_desc.get().strip()
        try:
            valor = float(entrada_valor.get().replace(",", "."))
        except:
            mostrar_erro_toplevel("Valor inválido.")
            return

        if not desc:
            mostrar_erro_toplevel("Descrição não pode ser vazia.")
            return

        if tipo == "receita":
            dados[chave]["receitas"][desc] = dados[chave]["receitas"].get(desc, 0.0) + valor

        elif tipo == "gasto":
            try:
                dia = int(entrada_dia.get())
                if dia < 1 or dia > 31:
                    raise ValueError
            except:
                mostrar_erro_toplevel("Dia inválido. Informe um número entre 1 e 31.")
                return

            tipo_gasto = tipo_gasto_combo.get()
            dados[chave]["gastos"].append({
                "descricao": desc,
                "valor": valor,
                "tipo": tipo_gasto,
                "dia": dia,
                "usuario": usuario_atual or "Desconhecido"  # salva o usuário logado
            })

        atualizar_resumo()
        if callback_apos_salvar:
            callback_apos_salvar()
        janela.destroy()

    ttk.Button(main_frame, text="💾 Salvar", command=salvar, 
               bootstyle="success").pack(pady=15)
    janela.bind("<Return>", lambda event: salvar())
    aplicar_icone(janela)

# ----------------------Funções editar----------------------------------
def editar_tipos_gastos(janela_anterior):
    global tipos_gasto
    janela_anterior.destroy()

    # Janela principal de edição
    janela = tk.Toplevel(app)
    janela.title("Editar Tipos de Gastos")
    largura = 450
    altura = 550
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.transient(app)
    janela.grab_set()
    aplicar_icone(janela)  # Ícone do app

    main_frame = tk.Frame(janela, padx=25, pady=25)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="📂 Tipos de Gastos Atuais:", font=("Inter", 13, "bold")).pack(pady=(0, 10))
    
    lista_tipos = tk.Listbox(main_frame, height=12, font=("Inter", 10),
                             selectbackground="#0d6efd", selectforeground="#ffffff")
    for tipo in tipos_gasto:
        lista_tipos.insert(tk.END, tipo)
    lista_tipos.pack(pady=8, fill="both", expand=True)

    entrada_novo_tipo = ttk.Entry(main_frame, font=("Inter", 10))
    ttk.Label(main_frame, text="Novo Tipo de Gasto ou Edição:", font=("Inter", 11)).pack(pady=(15, 5))
    entrada_novo_tipo.pack(pady=8, fill="x")

    # ---------------- Funções dos botões ----------------
    def adicionar_tipo():
        tipo_novo = entrada_novo_tipo.get().strip()
        if tipo_novo and tipo_novo not in tipos_gasto:
            tipos_gasto.append(tipo_novo)
            lista_tipos.insert(tk.END, tipo_novo)
            entrada_novo_tipo.delete(0, tk.END)
            salvar_dados()
        else:
            messagebox.showwarning("Aviso", "Tipo já existe ou está vazio.")

    def excluir_tipo():
        selecionado = lista_tipos.curselection()
        if not selecionado:
            mostrar_erro_toplevel("Selecione um tipo para excluir.", janela)
            return

        tipo_selecionado = lista_tipos.get(selecionado)

        # Janela de confirmação customizada
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

        ttk.Button(botoes, text="✓ Sim", command=confirmar, bootstyle="danger").pack(side="left", padx=10)
        ttk.Button(botoes, text="✗ Não", command=confirm_janela.destroy, bootstyle="secondary").pack(side="right", padx=10)

    def editar_tipo():
        selecionado = lista_tipos.curselection()
        if selecionado:
            indice = selecionado[0]
            novo_nome = entrada_novo_tipo.get().strip()
            antigo_nome = lista_tipos.get(indice)

            if not novo_nome:
                # Janela customizada com ícone
                aviso_janela = tk.Toplevel(janela)
                aviso_janela.title("Aviso")
                aviso_janela.resizable(False, False)
                largura_av, altura_av = 300, 120
                x = (janela.winfo_screenwidth() // 2) - (largura_av // 2)
                y = (janela.winfo_screenheight() // 2) - (altura_av // 2)
                aviso_janela.geometry(f"{largura_av}x{altura_av}+{x}+{y}")
                aviso_janela.grab_set()
                aviso_janela.attributes("-topmost", True)
                aviso_janela.configure(bg="#f8f9fa")
                aplicar_icone(aviso_janela)

                frame_aviso = tk.Frame(aviso_janela, bg="#f8f9fa", padx=20, pady=20)
                frame_aviso.pack(fill="both", expand=True)

                ttk.Label(frame_aviso, text="Digite um nome válido.", 
                      font=("Inter", 11), justify="center").pack(pady=10)

                ttk.Button(frame_aviso, text="OK", command=aviso_janela.destroy, bootstyle="secondary").pack()
                return

            if novo_nome == antigo_nome:
                messagebox.showinfo("Aviso", "O nome não foi alterado.")
                return
            if novo_nome in tipos_gasto:
                messagebox.showwarning("Aviso", "Este tipo já existe.")
                return

            tipos_gasto[indice] = novo_nome
            lista_tipos.delete(indice)
            lista_tipos.insert(indice, novo_nome)
            entrada_novo_tipo.delete(0, tk.END)
            salvar_dados()
        else:
            messagebox.showerror("Erro", "Selecione um tipo para editar.")

    # ---------------- Botões principais ----------------
    botoes_frame = tk.Frame(main_frame)
    botoes_frame.pack(pady=15)

    ttk.Button(botoes_frame, text="➕ Adicionar Tipo", command=adicionar_tipo, bootstyle="success").pack(pady=5, fill="x")
    ttk.Button(botoes_frame, text="🗑️ Excluir Tipo Selecionado", command=excluir_tipo, bootstyle="danger").pack(pady=5, fill="x")
    ttk.Button(botoes_frame, text="✏️ Editar Tipo Selecionado", command=editar_tipo, bootstyle="primary").pack(pady=5, fill="x")

    print(f"Tipos de gastos após carregamento: {tipos_gasto}")

def editar_despesa_fixa(indice):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)
    info = inicializar_mes(mes, ano)

    d = info["despesas_fixas"][indice]

    janela = tk.Toplevel(app)
    janela.title("Editar Despesa Fixa")
    largura, altura = 420, 300
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.attributes("-topmost", True)
    janela.grab_set()

    main_frame = tk.Frame(janela, padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    janela.bind("<Return>", lambda event: salvar_alteracoes())

    ttk.Label(main_frame, text="Descrição:", font=("Inter", 11)).pack(pady=(10, 0))
    ttk.Label(main_frame, text=d["descricao"], font=("Inter", 10, "bold")).pack()

    ttk.Label(main_frame, text="Valor (R$):", font=("Inter", 11)).pack(pady=(15, 0))
    valor_entry = ttk.Entry(main_frame, font=("Inter", 10))
    valor_entry.insert(0, f"{d['valor']:.2f}".replace(".", ","))
    valor_entry.pack(pady=5)

    ttk.Label(main_frame, text="Vencimento (dia):", font=("Inter", 11)).pack(pady=(15, 0))
    venc_entry = ttk.Entry(main_frame, font=("Inter", 10))
    venc_entry.insert(0, str(d.get("vencimento", "")))
    venc_entry.pack(pady=5)

    status_btn = ttk.Button(main_frame, text=f"📋 Alternar Status (Atual: {d['status']})",
                           bootstyle="info")

    def salvar_alteracoes():
        try:
            valor_str = valor_entry.get().replace(",", ".")
            novo_valor = float(valor_str)
            novo_vencimento = int(venc_entry.get())

            valor_antigo = d["valor"]
            vencimento_antigo = d.get("vencimento", None)
            descricao_alvo = d["descricao"]

            # Atualiza o valor e vencimento no mês atual
            d["valor"] = novo_valor
            d["vencimento"] = novo_vencimento

            # Replicar para próximos 11 meses caso valor ou vencimento tenham sido alterados
            if novo_valor != valor_antigo or novo_vencimento != vencimento_antigo:
                for i in range(1, 12):
                    mes_futuro = mes + i
                    ano_futuro = ano
                    if mes_futuro > 12:
                        mes_futuro -= 12
                        ano_futuro += 1

                    chave_futuro = get_chave(mes_futuro, ano_futuro)
                    info_futuro = inicializar_mes(mes_futuro, ano_futuro)

                    for desp in info_futuro["despesas_fixas"]:
                        if desp["descricao"] == descricao_alvo:
                            desp["valor"] = novo_valor
                            desp["vencimento"] = novo_vencimento
                            break

            salvar_dados()
            atualizar_resumo()
            janela.destroy()
        except ValueError:
            messagebox.showerror("Erro", "Valor ou vencimento inválido.")

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

    largura = 400
    altura = 480
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.attributes("-topmost", True)
    janela.grab_set()

    main_frame = tk.Frame(janela, padx=25, pady=25)
    main_frame.pack(fill="both", expand=True)

    fixo = gasto_original.get("fixo", False)
    parcelas = 1 if fixo else gasto_original.get("total_parcelas", 1) or 1
    valor_parcela = round(gasto_original["valor"], 2)

    ttk.Label(main_frame, text="Descrição:", font=("Inter", 11)).pack(pady=5)
    entrada_desc = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_desc.insert(0, gasto_original["descricao"])
    entrada_desc.pack(pady=5)

    ttk.Label(main_frame, text="Valor da Parcela (R$):", font=("Inter", 11)).pack(pady=5)
    entrada_valor = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_valor.insert(0, str(valor_parcela))
    entrada_valor.pack(pady=5)

    ttk.Label(main_frame, text="Tipo de Gasto:", font=("Inter", 11)).pack(pady=5)
    combo_tipo = ttk.Combobox(main_frame, values=tipos_gasto, state="readonly", font=("Inter", 10))
    combo_tipo.set(gasto_original.get("tipo", tipos_gasto[0]))
    combo_tipo.pack(pady=5)

    def salvar():
        try:
            novo_desc = entrada_desc.get().strip()
            novo_valor_parcela = float(entrada_valor.get().replace(",", "."))
            novo_tipo = combo_tipo.get().strip()

            if not novo_desc or not novo_tipo:
                raise ValueError("Campos não podem estar vazios.")

            dia = gasto_original["dia"]
            mes_inicial = gasto_original["mes"]
            ano_inicial = gasto_original["ano"]
            cartao = gasto_original["cartao"]
            desc_original = gasto_original["descricao"]

            meses_alvo = 24 if fixo else parcelas

            for i in range(meses_alvo):
                mes_fatura = mes_inicial + i
                ano_fatura = ano_inicial + (mes_fatura - 1) // 12
                mes_fatura = (mes_fatura - 1) % 12 + 1

                chave_fatura = (mes_fatura, ano_fatura)
                if chave_fatura not in dados:
                    inicializar_mes(mes_fatura, ano_fatura)

                for g in dados[chave_fatura]["cartao_credito"]:
                    mesmo_gasto = (
                        g["descricao"] == desc_original and
                        g["cartao"] == cartao and
                        g["dia"] == dia and
                        g["mes"] == mes_inicial and
                        g["ano"] == ano_inicial
                    )
                    if mesmo_gasto:
                        g["descricao"] = novo_desc
                        g["valor"] = round(novo_valor_parcela, 2)
                        g["tipo"] = novo_tipo

        except Exception as e:
            mostrar_erro_toplevel(f"Erro ao salvar: {e}", janela)
            return

        salvar_dados()
        atualizar_resumo()
        janela.destroy()
        if callback_apos_salvar:
            callback_apos_salvar()

    ttk.Button(main_frame, text="💾 Salvar", command=salvar, 
               bootstyle="success").pack(pady=25)
    janela.bind("<Return>", lambda e: salvar())

def editar_receita(nome_receita):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)
    inicializar_mes(mes, ano)

    valor_atual = dados[chave]["receitas"].get(nome_receita, 0.0)

    janela = tk.Toplevel(app)
    janela.title("Editar Receita")

    largura = 350
    altura = 280
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.attributes("-topmost", True)
    janela.grab_set()

    main_frame = tk.Frame(janela, padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(main_frame, text="Descrição:", font=("Inter", 11)).pack(pady=8)
    entrada_desc = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_desc.pack(pady=5)
    entrada_desc.insert(0, nome_receita)
    entrada_desc.config(state="disabled")  # bloquear edição do nome para manter a chave correta

    ttk.Label(main_frame, text="Valor (R$):", font=("Inter", 11)).pack(pady=8)
    entrada_valor = ttk.Entry(main_frame, font=("Inter", 10))
    entrada_valor.pack(pady=5)
    entrada_valor.insert(0, str(valor_atual).replace(".", ","))

    def mostrar_erro_toplevel(mensagem, parent=janela):
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

# ----------------------Funções excluir---------------------------------

def excluir_gasto_cartao(gasto, parent_janela=None, callback_apos_excluir=None):
    resposta = messagebox.askyesno(
        "Excluir Gasto",
        "Deseja excluir TODAS as parcelas deste gasto?",
        parent=parent_janela
    )
    if not resposta:
        return

    fixo = gasto.get("fixo", False)
    total_parcelas = gasto.get("total_parcelas", 1)
    parcelas = 24 if fixo else total_parcelas

    # Recupera os dados da compra
    dia = gasto.get("dia")
    mes_compra = gasto.get("mes")
    ano_compra = gasto.get("ano")
    cartao = gasto.get("cartao")
    descricao = gasto.get("descricao")

    # 🧠 Calcula corretamente o mês/ano da fatura como no cadastro
    cartao_info = next((c for c in cartoes if c["nome"] == cartao), None)
    fechamento = cartao_info.get("fechamento", 1) if cartao_info else 1

    if dia > fechamento:
        mes_inicial = mes_compra + 1
        ano_inicial = ano_compra + (1 if mes_inicial > 12 else 0)
        mes_inicial = 1 if mes_inicial > 12 else mes_inicial
    else:
        mes_inicial = mes_compra
        ano_inicial = ano_compra

    # 🔁 Loop para excluir todas as parcelas (ou uma, se for à vista)
    for i in range(parcelas):
        mes_fatura = mes_inicial + i
        ano_fatura = ano_inicial + (mes_fatura - 1) // 12
        mes_fatura = (mes_fatura - 1) % 12 + 1

        chave_fatura = (mes_fatura, ano_fatura)
        if chave_fatura in dados:
            nova_lista = []
            for g in dados[chave_fatura]["cartao_credito"]:
                mesmo_gasto = (
                    g.get("descricao") == descricao and
                    g.get("cartao") == cartao and
                    g.get("dia") == dia and
                    g.get("mes") == mes_compra and
                    g.get("ano") == ano_compra
                )
                if not mesmo_gasto:
                    nova_lista.append(g)
            dados[chave_fatura]["cartao_credito"] = nova_lista

    salvar_dados()
    atualizar_resumo()
    if callback_apos_excluir:
        callback_apos_excluir()

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

    confirmar = messagebox.askyesno(
        "Confirmação",
        f"Deseja realmente excluir a despesa fixa '{descricao_target}' a partir de {mes:02d}/{ano}?"
    )

    if not confirmar:
        return  # Usuário cancelou

    for ano_loop in range(ano, 2101):
        for mes_loop in range(1, 13):
            if ano_loop == ano and mes_loop < mes:
                continue

            chave = get_chave(mes_loop, ano_loop)
            if chave not in dados:
                continue

            dados[chave]["despesas_fixas"] = [
                d for d in dados[chave]["despesas_fixas"]
                if d.get("descricao") != descricao_target
            ]

    atualizar_resumo()

def excluir_receita(nome_receita):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)
    info = inicializar_mes(mes, ano)

    if nome_receita in info["receitas"]:
        confirmar = messagebox.askyesno("Excluir Receita", f"Deseja excluir a receita '{nome_receita}' deste mês?")
        if confirmar:
            del info["receitas"][nome_receita]
            salvar_dados()
            atualizar_resumo()

def excluir_gasto_diario(idx, janela_detalhes=None, callback_apos_excluir=None):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    info = inicializar_mes(mes, ano)

    if idx < 0 or idx >= len(info["gastos"]):
        messagebox.showerror("Erro", "Índice de gasto inválido", parent=janela_detalhes)
        return

    gasto = info["gastos"][idx]

    resposta = messagebox.askyesno(
        "Confirmação",
        f"Excluir gasto '{gasto['descricao']}' no dia {gasto['dia']}?",
        parent=janela_detalhes
    )

    if resposta:
        info["gastos"].pop(idx)
        salvar_dados()
        atualizar_resumo()
        if callback_apos_excluir:
            callback_apos_excluir()

# -------------------------Interface------------------------------------
frame_selecao = tk.Frame(app, pady=15, bg="#0d6efd")
frame_selecao.pack(pady=15, fill="x")

combo_container = tk.Frame(frame_selecao, bg="#0d6efd")
combo_container.pack()

ttk.Label(combo_container, text="📅 Período:", font=("Inter", 12, "bold")).pack(side="left", padx=(0, 10))

meses = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]
combo_mes = ttk.Combobox(combo_container, values=meses, state="readonly", width=14, font=("Inter", 11))

anos = [str(y) for y in range(2025, 2050)]
combo_ano = ttk.Combobox(combo_container, values=anos, state="readonly", width=8, font=("Inter", 11))

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

frame_botoes = ttk.Frame(app)
frame_botoes.pack(pady=8)

# -------------------------
# Resumo Geral
# -------------------------
frame_resumo = tk.LabelFrame(app, text="📊 Resumo Geral", padx=12, pady=12, bg="#d9e3f1", fg="#0d6efd", font=("Inter", 12, "bold"))
frame_resumo.pack(fill="x", padx=15, pady=10)

# -------------------------
# Main Frames
# -------------------------
frame_main = tk.Frame(app, bg="#0d6efd")
frame_main.pack(fill="both", expand=True, padx=15, pady=8)

# Função para criar card com borda e fundo
def criar_card(frame_pai, titulo, bg="#ffffff"):
    card = tk.Frame(frame_pai, bg=bg, bd=1, relief="solid", padx=10, pady=10)
    tk.Label(card, text=titulo, font=("Inter", 12, "bold"), bg=bg).pack(anchor="w")
    return card

frame_receitas = criar_card(frame_main, "💰 Receitas", bg="#e6ffea")
frame_receitas.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

frame_despesas = criar_card(frame_main, "🏠 Despesas Fixas", bg="#ffe6e6")
frame_despesas.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)

frame_gastos = criar_card(frame_main, "🛒 Gastos Diários", bg="#e6f0ff")
frame_gastos.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)

frame_credito = criar_card(frame_main, "💳 Cartão de Crédito", bg="#f2e6ff")
frame_credito.grid(row=1, column=1, sticky="nsew", padx=8, pady=8)

frame_main.rowconfigure(0, weight=1)
frame_main.rowconfigure(1, weight=1)
frame_main.columnconfigure(0, weight=1)
frame_main.columnconfigure(1, weight=1)

# -------------------------
# Scroll Areas
# -------------------------
def criar_area_com_scroll(frame_pai, altura=200, exibir_scroll=True):
    canvas = tk.Canvas(frame_pai, height=altura, highlightthickness=0, bg=frame_pai["bg"], relief="flat")
    scroll_frame = tk.Frame(canvas, bg=frame_pai["bg"])
    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

    if exibir_scroll:
        scrollbar = ttk.Scrollbar(frame_pai, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
    else:
        scrollbar = None

    canvas.pack(side="left", fill="both", expand=True)

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    scroll_frame.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
    scroll_frame.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

    return canvas, scrollbar, scroll_frame

canvas_receitas, scrollbar_receitas, scroll_frame_receitas = criar_area_com_scroll(frame_receitas, altura=320)
canvas_despesas, scrollbar_despesas, scroll_frame_despesas = criar_area_com_scroll(frame_despesas, altura=220)
canvas_gastos, scrollbar_gastos, scroll_frame_gastos = criar_area_com_scroll(frame_gastos, altura=60, exibir_scroll=False)
canvas_credito, scrollbar_credito, scroll_frame_credito = criar_area_com_scroll(frame_credito, altura=60, exibir_scroll=False)

# Inicializa dados para o mês atual
atualizar_resumo()
app.mainloop()

