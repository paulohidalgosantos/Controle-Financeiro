import os, sys, time, json, copy, locale, math, subprocess, urllib.request, webbrowser
from datetime import datetime
from collections import defaultdict
from operator import itemgetter
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import ttkbootstrap as tb
from ttkbootstrap import Style
from ttkbootstrap.constants import *
from functools import partial
from tkinter import filedialog

VERSAO_ATUAL = "1.0.5"

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
            if messagebox.askyesno("Atualização disponível", f"Nova versão {versao_remota} disponível.\nDeseja atualizar agora?"):
                baixar_e_instalar_atualizacao()
        else:
            messagebox.showinfo("Atualização", "Você já está usando a versão mais recente.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao verificar atualização:\n{e}")

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

# Funções de dados
def carregar_dados():
    global dados, cartoes, contas_fixas_modelo, tipos_gasto, inicio_uso
    global ultima_selecao_cartao, ultima_selecao_tipo, ultima_selecao_mes, ultima_selecao_ano

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
                tipos_gasto = conteudo.get("tipos_gasto")
                if not tipos_gasto:
                    tipos_gasto = TIPOS_GASTO_PADRAO.copy()

                inicio_uso = conteudo.get("inicio_uso", None)
                if inicio_uso:
                    inicio_uso = tuple(inicio_uso)

                ultima_selecao = conteudo.get("ultima_selecao", {})
                ultima_selecao_cartao = ultima_selecao.get("cartao", None)
                ultima_selecao_tipo = ultima_selecao.get("tipo_gasto", None)
                ultima_selecao_mes = ultima_selecao.get("mes", None)
                ultima_selecao_ano = ultima_selecao.get("ano", None)

        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            dados = {}
            cartoes = []
            contas_fixas_modelo = []
            tipos_gasto = TIPOS_GASTO_PADRAO.copy()
            inicio_uso = None
            ultima_selecao_cartao = None
            ultima_selecao_tipo = None
            ultima_selecao_mes = None
            ultima_selecao_ano = None
            messagebox.showwarning("Aviso", f"Erro ao carregar dados salvos. Iniciando com dados limpos.\nErro: {e}")
    else:
        dados = {}
        cartoes = []
        contas_fixas_modelo = []
        tipos_gasto = TIPOS_GASTO_PADRAO.copy()
        inicio_uso = None
        ultima_selecao_cartao = None
        ultima_selecao_tipo = None
        ultima_selecao_mes = None
        ultima_selecao_ano = None

    # ✅ Corrige gastos antigos sem "status"
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
                }
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

# Janela principal
app = tb.Window(themename="flatly")
app.title(f"Controle Financeiro {VERSAO_ATUAL}")
app.state('zoomed')

caminho_icone = recurso_caminho("icone.png")

try:
    icone = tk.PhotoImage(file=caminho_icone)
    app.iconphoto(False, icone)
except tk.TclError:
    print("⚠️ Ícone icone.png não encontrado.")

# Carregar os dados
carregar_dados()

# ---- Funções usadas no menu ----
def definir_inicio_uso():
    global inicio_uso

    janela = tk.Toplevel(app)
    janela.title("Definir Início do Uso")
    janela.geometry("250x230")
    janela.resizable(False, False)
    janela.grab_set()
    janela.transient(app)

    # Centralizar a janela na tela
    janela.update_idletasks()
    largura = 250
    altura = 230
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")

    ttk.Label(janela, text="Mês de início (1-12):").pack(pady=(15, 5))
    entry_mes = ttk.Entry(janela, justify="center")
    entry_mes.pack()

    ttk.Label(janela, text="Ano de início (ex: 2023):").pack(pady=(10, 5))
    entry_ano = ttk.Entry(janela, justify="center")
    entry_ano.pack()

    def confirmar():
        try:
            mes_str = entry_mes.get().strip()
            ano_str = entry_ano.get().strip()

            if not mes_str or not ano_str:
                raise ValueError("Os campos não podem estar vazios")

            mes = int(mes_str)
            ano = int(ano_str)

            if mes < 1 or mes > 12:
                raise ValueError("Mês inválido (deve ser entre 1 e 12)")
            if ano < 1900 or ano > 2100:
                raise ValueError("Ano inválido (deve estar entre 1900 e 2100)")

            global inicio_uso
            inicio_uso = (mes, ano)
            salvar_dados()
            messagebox.showinfo("Início definido", f"Início do uso definido para {mes:02d}/{ano}")
            janela.destroy()
            atualizar_resumo()

        except ValueError as ve:
            messagebox.showerror("Erro de validação", f"Erro: {ve}")

        except Exception:
            messagebox.showerror("Erro", "Valor inválido. Por favor, preencha os campos corretamente.")

    btn_confirmar = ttk.Button(janela, text="Confirmar", command=confirmar)
    btn_confirmar.pack(pady=15)

    # Permitir salvar com Enter
    janela.bind('<Return>', lambda event: confirmar())

def criar_menu():
    menubar = tk.Menu(app)

    menu_gerenciar = tk.Menu(menubar, tearoff=0, font=("Segoe UI", 10))
    menu_gerenciar.add_command(label="💳  Gerenciar Cartões", command=gerenciar_cartoes)
    menu_gerenciar.add_command(label="📂  Categorias de Gastos", command=abrir_gerenciador_categorias)
    menu_gerenciar.add_separator()
    menu_gerenciar.add_command(label="🔄  Buscar Atualização", command=buscar_atualizacao)
    menu_gerenciar.add_separator()
    menu_gerenciar.add_command(label="🗑️  Zerar Aplicativo", command=zerar_tudo)

    # Novas opções de exportar/importar logo abaixo de zerar
    menu_gerenciar.add_separator()
    menu_gerenciar.add_command(label="📤 Exportar Dados", command=exportar_dados)
    menu_gerenciar.add_command(label="📥 Importar Dados", command=importar_dados)

    # Botão para definir início do uso
    menu_gerenciar.add_separator()
    menu_gerenciar.add_command(label="📅 Definir Início do Uso", command=definir_inicio_uso)

    menubar.add_cascade(label="⚙️  Gerenciar", menu=menu_gerenciar)
    app.config(menu=menubar)


def gerenciar_cartoes():
    janela = tk.Toplevel(app)
    janela.title("Gerenciar Cartões")
    largura = 300
    altura = 180
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.resizable(False, False)
    janela.attributes("-topmost", True)
    janela.grab_set()

    ttk.Label(janela, text="Gerenciar Cartões", font=("Segoe UI", 13, "bold")).pack(pady=20)
    ttk.Button(janela, text="➕ Adicionar Cartão", width=25, command=lambda: adicionar_cartao(janela)).pack(pady=5)
    ttk.Button(janela, text="🗑️ Remover Cartão", width=25, command=lambda: excluir_cartao(janela)).pack(pady=5)

def abrir_gerenciador_categorias():
    janela = tk.Toplevel(app)
    janela.title("Gerenciar Categorias")

    largura = 300
    altura = 180
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.resizable(False, False)
    janela.attributes("-topmost", True)
    janela.grab_set()

    ttk.Label(janela, text="Gerenciar Categorias", font=("Segoe UI", 13, "bold")).pack(pady=20)

    ttk.Button(
        janela,
        text="📂 Editar categorias",
        width=25,
        command=lambda: editar_tipos_gastos(janela)
    ).pack(pady=5)

def zerar_tudo():
    senha = tk.simpledialog.askstring("Senha necessária", "Digite a senha para zerar todos os dados:", show="*")
    if senha is None:
        return  # Usuário cancelou
    if senha == "admin":
        if messagebox.askyesno("Confirmar", "Deseja realmente zerar todos os dados?"):
            global dados, contas_fixas_modelo, cartoes, tipos_gasto
            dados.clear()
            contas_fixas_modelo.clear()
            cartoes.clear()
            tipos_gasto = TIPOS_GASTO_PADRAO.copy()  # <<< RESTAURA OS PADRÕES
            salvar_dados()
            atualizar_resumo()
            messagebox.showinfo("Zerado", "Todos os dados foram apagados e os tipos de gastos foram restaurados.")
    else:
        messagebox.showerror("Senha incorreta", "Senha inválida. Ação cancelada.")

def exportar_dados():
    caminho = filedialog.asksaveasfilename(
        title="Exportar dados",
        defaultextension=".json",
        filetypes=[("Arquivo JSON", "*.json")],
        initialfile="controle_financeiro_backup.json"
    )
    if not caminho:
        return  # Cancelou

    try:
        dados_para_salvar = {
            f"{mes:02d}-{ano}": valor
            for (mes, ano), valor in dados.items()
        }
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump({
                "dados": dados_para_salvar,
                "cartoes": cartoes,
                "contas_fixas_modelo": contas_fixas_modelo,
                "tipos_gasto": tipos_gasto
            }, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("Exportação", "Dados exportados com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao exportar dados:\n{e}")

# --- Função para importar dados ---
def importar_dados():
    caminho = filedialog.askopenfilename(
        title="Importar dados",
        filetypes=[("Arquivo JSON", "*.json")]
    )
    if not caminho:
        return  # Cancelou

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = json.load(f)

        dados_carregados = conteudo.get("dados", {})
        global dados, cartoes, contas_fixas_modelo, tipos_gasto

        dados = {
            tuple(map(int, chave.split("-"))): valor
            for chave, valor in dados_carregados.items()
        }
        cartoes = conteudo.get("cartoes", [])
        contas_fixas_modelo = conteudo.get("contas_fixas_modelo", [])
        tipos_gasto = conteudo.get("tipos_gasto", TIPOS_GASTO_PADRAO.copy())

        salvar_dados()
        atualizar_resumo()  # Atualiza interface, certifique que essa função existe no seu código
        messagebox.showinfo("Importação", "Dados importados com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao importar dados:\n{e}")
# Chamar a função para exibir o menu
criar_menu()

# Ao fechar o app
def ao_fechar():
    salvar_dados()
    app.destroy()

app.protocol("WM_DELETE_WINDOW", ao_fechar)

# Funções utilitárias
def get_chave(mes, ano):
    return (mes, ano)

def configurar_inicio_uso():
    def confirmar():
        try:
            m = int(combo_mes.get())
            a = int(entry_ano.get())
            if not (1 <= m <= 12):
                raise ValueError
            if not (1900 <= a <= 2100):
                raise ValueError
            global inicio_uso
            inicio_uso = (m, a)
            salvar_dados()
            messagebox.showinfo("Configuração salva", f"Início do uso definido para {m:02d}/{a}")
            janela.destroy()
            atualizar_resumo()
        except Exception:
            messagebox.showerror("Erro", "Informe um mês e ano válidos.")

    janela = tk.Toplevel(app)
    janela.title("Configurar Início do Uso")
    janela.geometry("250x140")
    janela.grab_set()
    janela.resizable(False, False)

    ttk.Label(janela, text="Mês de início (1-12):").pack(pady=(10,0))
    combo_mes = ttk.Combobox(janela, values=list(range(1, 13)), state="readonly")
    combo_mes.pack(pady=5)
    if inicio_uso:
        combo_mes.current(inicio_uso[0]-1)
    else:
        combo_mes.current(0)

    ttk.Label(janela, text="Ano de início:").pack(pady=(10,0))
    entry_ano = ttk.Entry(janela)
    entry_ano.pack(pady=5)
    if inicio_uso:
        entry_ano.insert(0, str(inicio_uso[1]))
    else:
        entry_ano.insert(0, str(datetime.now().year))

    btn = ttk.Button(janela, text="Confirmar", command=confirmar)
    btn.pack(pady=10)

def inicializar_mes(mes, ano):
    global inicio_uso
    chave = get_chave(mes, ano)

    # Se início definido, não inicializar meses anteriores — apenas cria dados vazios para consulta
    if inicio_uso:
        mes_inicio, ano_inicio = inicio_uso
        if (ano < ano_inicio) or (ano == ano_inicio and mes < mes_inicio):
            if chave not in dados:
                dados[chave] = {
                    "receitas": {},
                    "conta": 0.0,
                    "despesas_fixas": [],
                    "gastos": [],
                    "cartao_credito": [],
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
            "cartao_credito": [],
            "tipos": []
        }

        mes_ant = mes - 1 if mes > 1 else 12
        ano_ant = ano if mes > 1 else ano - 1
        chave_anterior = get_chave(mes_ant, ano_ant)

        if chave_anterior in dados:
            info_ant = dados[chave_anterior]

            total_receitas_ant = sum(info_ant["receitas"].values())
            total_gastos_ant = sum(g["valor"] for g in info_ant["gastos"])
            total_credito_ant = sum(c["valor"] for c in info_ant["cartao_credito"])
            total_despesas_todas_ant = sum(d["valor"] for d in info_ant["despesas_fixas"])

            saldo_final_mes_anterior = info_ant["conta"] + total_receitas_ant - total_gastos_ant - total_credito_ant - total_despesas_todas_ant

            dados[chave]["conta"] = saldo_final_mes_anterior

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

    if chave_anterior in dados:
        info_ant = dados[chave_anterior]

        total_receitas_ant = sum(info_ant["receitas"].values())
        total_gastos_ant = sum(g["valor"] for g in info_ant["gastos"])
        total_credito_ant = sum(c["valor"] for c in info_ant["cartao_credito"])
        total_despesas_todas_ant = sum(d["valor"] for d in info_ant["despesas_fixas"])

        saldo_final_mes_anterior = info_ant["conta"] + total_receitas_ant - total_gastos_ant - total_credito_ant - total_despesas_todas_ant

        # Atualiza saldo inicial do mês atual
        dados[chave]["conta"] = saldo_final_mes_anterior

def atualizar_resumo(*args):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)

    if chave not in dados:
        inicializar_mes(mes, ano)
    else:
        recalcular_saldo_inicial(chave)

    info = dados[chave]

    # Limpar tudo antes de criar o conteúdo novo
    for frame in [scroll_frame_receitas, scroll_frame_despesas, scroll_frame_gastos, scroll_frame_credito, frame_resumo]:
        for widget in frame.winfo_children():
            widget.destroy()

    def criar_cabecalho_com_detalhes(container, titulo, total, funcao_adicionar, funcao_detalhes):
        frame_topo = ttk.Frame(container)
        frame_topo.pack(fill="x", pady=(0, 8))

        frame_header = ttk.Frame(frame_topo)
        frame_header.pack(fill="x", pady=(0, 10))

        btn_adicionar = ttk.Label(frame_header, text="➕", font=("Segoe UI Semibold", 16), foreground="#0d6efd", cursor="hand2")
        btn_adicionar.grid(row=0, column=0, sticky="w", padx=5)
        btn_adicionar.bind("<Button-1>", lambda e: funcao_adicionar())

        label_titulo = ttk.Label(frame_header, text=titulo, font=("Segoe UI Semibold", 14), foreground="#0d6efd", cursor="hand2")
        label_titulo.grid(row=0, column=1, sticky="w", padx=(10, 0))
        label_titulo.bind("<Button-1>", lambda e: funcao_detalhes())

        label_total = ttk.Label(
            frame_header,
            text=f"R$ {locale.currency(total, grouping=True).replace('R$', '').strip()}",
            font=("Segoe UI", 11, "bold"),
            foreground="#198754"
        )
        label_total.grid(row=0, column=2, sticky="w", padx=(10,0))

        frame_header.grid_columnconfigure(0, minsize=30)  # largura fixa pro botão

        return frame_topo

    # --- RECEITAS ---
    total_receitas = sum(info["receitas"].values())
    frame_receitas_topo = criar_cabecalho_com_detalhes(
        scroll_frame_receitas,
        "Receitas",
        total_receitas,
        lambda: adicionar_valor("Adicionar Receita", "receita"),
        lambda: None  # Você pode criar função para detalhes se quiser
    )

    frame_receitas_conteudo = tk.Frame(frame_receitas_topo, bg="#f0f2f5", padx=15, pady=15, relief="flat", borderwidth=0)
    frame_receitas_conteudo.pack(fill="x")

    for nome, valor in list(info["receitas"].items()):
        frame_linha = ttk.Frame(frame_receitas_conteudo)
        frame_linha.pack(anchor="w", fill="x", pady=4)

        ttk.Label(
            frame_linha,
            text=f"{nome}: {locale.currency(valor, grouping=True)}",
            foreground="#155724",
            font=("Segoe UI", 10, "bold")
        ).pack(side="left", anchor="w")

        btn_excluir = ttk.Label(
            frame_linha,
            text="🗑️",
            font=("Segoe UI", 11),
            foreground="red",
            cursor="hand2"
        )
        btn_excluir.pack(side="right", anchor="w", padx=5, pady=5)
        btn_excluir.bind("<Button-1>", lambda e, nome_receita=nome: excluir_receita(nome_receita))

    # --- DESPESAS FIXAS ---
    total_despesas_fixas = sum(d["valor"] for d in info["despesas_fixas"])
    frame_despesas_topo = criar_cabecalho_com_detalhes(
        scroll_frame_despesas,
        "Despesas Fixas",
        total_despesas_fixas,
        adicionar_despesa_fixa,
        lambda: None
    )

    frame_despesa_conteudo = tk.Frame(frame_despesas_topo, bg="#f0f2f5", padx=15, pady=15, relief="flat", borderwidth=0)
    frame_despesa_conteudo.pack(fill="x")

    despesas_ordenadas = sorted(info["despesas_fixas"], key=lambda d: d.get("vencimento", 99))
    from calendar import monthrange

    # Data selecionada no combobox
    data_selecionada = datetime(ano, mes, 1)
    ultimo_dia_mes = monthrange(ano, mes)[1]
    hoje = datetime.today()

    # É hoje o mês selecionado?
    mes_atual = (hoje.year == ano and hoje.month == mes)

    for d in despesas_ordenadas:
        idx_real = info["despesas_fixas"].index(d)
        vencimento = d.get("vencimento", "??")
        status = d["status"]

        if status == "Pago":
            cor = "#28a745"  # Verde
        elif status == "Aberto":
            if isinstance(vencimento, int):
                # Criar data do vencimento dentro do mês/ano selecionado
                venc_data = datetime(ano, mes, min(vencimento, ultimo_dia_mes))
                if venc_data < hoje:
                    cor = "#b22222"  # Vermelho: já venceu
                else:
                    cor = "#6c757d"  # Cinza escuro: ainda dentro do prazo
            else:
                cor = "#6c757d"  # Indefinido: cor neutra
        else:
            cor = "#000000"

        texto = f"{d['descricao']} - {locale.currency(d['valor'], grouping=True)} - Venc: {vencimento} ({d['status']})"

        container = ttk.Frame(frame_despesa_conteudo)
        container.pack(fill="x", pady=1)

        btn_editar = ttk.Label(container, text="🖉", font=("Segoe UI", 14), foreground="#0d6efd", cursor="hand2")
        btn_editar.pack(side="left", padx=(0, 8))
        btn_editar.bind("<Button-1>", lambda e, idx=idx_real: editar_despesa_fixa(idx))

        btn_excluir = ttk.Label(container, text="🗑️", font=("Segoe UI", 14), foreground="#dc3545", cursor="hand2")
        btn_excluir.pack(side="left", padx=(0, 8))
        btn_excluir.bind("<Button-1>", lambda e, idx=idx_real: excluir_despesa_fixa(idx))

        lbl = ttk.Label(container, text=texto, foreground=cor, font=("Segoe UI", 11, "bold"))
        lbl.pack(side="left", anchor="w")

    # --- GASTOS DIÁRIOS (agora só cabeçalho e abre janela detalhada) ---
    total_gastos_diarios = sum(g["valor"] for g in info["gastos"])
    criar_cabecalho_com_detalhes(
        scroll_frame_gastos,
        "Gastos Diários",
        total_gastos_diarios,
        lambda: adicionar_valor("Adicionar Gasto", "gasto"),
        mostrar_gastos_detalhados
    )

    # --- CARTÃO DE CRÉDITO (agora só cabeçalho e abre janela detalhada) ---
    # Agrupar gastos por cartão para verificar status "Pago"
    gastos_por_cartao = {}
    for c in info["cartao_credito"]:
        nome = c["cartao"]
        gastos_por_cartao.setdefault(nome, []).append(c)

    def cartao_pago(lista_gastos_cartao):
        return all(g.get("status") == "Pago" for g in lista_gastos_cartao)

    total_cartao_pago = 0
    total_cartao_todos = 0
    for nome_cartao, lista_gastos_cartao in gastos_por_cartao.items():
        total_gastos = sum(g["valor"] for g in lista_gastos_cartao)
        total_cartao_todos += total_gastos
        if cartao_pago(lista_gastos_cartao):
            total_cartao_pago += total_gastos

    criar_cabecalho_com_detalhes(
        scroll_frame_credito,
        "Cartão de Crédito",
        total_cartao_todos,
        adicionar_cartao_credito,
        abrir_cartao_credito_detalhado
    )

    # ------------------- RESUMO -------------------
    total_receitas = sum(info["receitas"].values())
    total_gastos = sum(g["valor"] for g in info["gastos"])
    total_pagas = sum(d["valor"] for d in info["despesas_fixas"] if d["status"] == "Pago")
    total_todas = sum(d["valor"] for d in info["despesas_fixas"])

    saldo_atual = total_receitas - total_gastos - total_cartao_pago - total_pagas
    saldo_final = total_receitas - total_gastos - total_cartao_todos - total_todas

    cor_saldo_atual = "#004085" if saldo_atual >= 0 else "#dc3545"  # azul se positivo, vermelho se negativo
    cor_saldo_final = "#004085" if saldo_final >= 0 else "#dc3545"

    ttk.Label(
        frame_resumo, 
        text=f"Saldo Atual: {locale.currency(saldo_atual, grouping=True)}", 
        font=("Segoe UI", 11, "bold"), 
        foreground=cor_saldo_atual
    ).pack(anchor="w")

    ttk.Label(
        frame_resumo, 
        text=f"Saldo Final: {locale.currency(saldo_final, grouping=True)}", 
        font=("Segoe UI", 11, "bold"), 
        foreground=cor_saldo_final
    ).pack(anchor="w", pady=3)

    # GASTOS POR TIPO (Diário + Cartão)
    ttk.Label(frame_resumo, text="Gastos por Tipo:", font=("Segoe UI", 11, "bold"), foreground="#000000").pack(anchor="w", pady=(10, 2))

    frame_gastos_tipo_container = ttk.Frame(frame_resumo)
    frame_gastos_tipo_container.pack(fill="x", pady=(0, 5))

    canvas_tipos = tk.Canvas(frame_gastos_tipo_container, height=50)
    scrollbar_tipos = ttk.Scrollbar(frame_gastos_tipo_container, orient="vertical", command=canvas_tipos.yview)
    frame_tipos_interno = ttk.Frame(canvas_tipos)

    frame_tipos_interno.bind(
        "<Configure>",
        lambda e: canvas_tipos.configure(scrollregion=canvas_tipos.bbox("all"))
    )

    canvas_tipos.create_window((0, 0), window=frame_tipos_interno, anchor="nw")
    canvas_tipos.configure(yscrollcommand=scrollbar_tipos.set)

    canvas_tipos.pack(side="left", fill="x", expand=True)
    scrollbar_tipos.pack(side="right", fill="y")

    gastos_por_tipo = {}

    # Somar gastos diários
    for g in info["gastos"]:
        tipo = g.get("tipo", "Indefinido")
        gastos_por_tipo[tipo] = gastos_por_tipo.get(tipo, 0) + g["valor"]

    # Somar gastos do cartão de crédito
    for c in info["cartao_credito"]:
        tipo = c.get("tipo", "Indefinido")
        gastos_por_tipo[tipo] = gastos_por_tipo.get(tipo, 0) + c["valor"]

    gastos_ordenados = sorted(gastos_por_tipo.items(), key=lambda x: x[0].lower())
    total = len(gastos_ordenados)
    colunas = math.ceil(total / 2)

    for i, (tipo, valor) in enumerate(gastos_ordenados):
        if i < colunas:
            linha = 0
            coluna = i
        else:
            linha = 1
            coluna = i - colunas

        ttk.Label(
            frame_tipos_interno,
            text=f"{tipo}: {locale.currency(valor, grouping=True)}",
            font=("Segoe UI", 10)
        ).grid(row=linha, column=coluna, sticky="w", padx=15, pady=2)

    # Atualiza a última seleção de mês/ano antes de salvar
    global ultima_selecao_mes, ultima_selecao_ano
    ultima_selecao_mes = mes
    ultima_selecao_ano = ano

    salvar_dados()  # Agora salva no mesmo JSON oculto


    app.update()

def criar_resumo_simples(container, titulo, total, comando_abrir):
    frame = ttk.Frame(container)
    frame.pack(fill="x", pady=5)

    label = ttk.Label(
        frame,
        text=f"{titulo}: {locale.currency(total, grouping=True)} ▶",
        font=("Segoe UI Semibold", 12),
        foreground="#0d6efd",
        cursor="hand2"
    )
    label.pack(side="left", anchor="w")
    label.bind("<Button-1>", lambda e: comando_abrir())

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
            f.pack(fill="x", padx=10, pady=(5, 10))
            estado_expansao_gastos_diarios[dia_local] = True

    for dia in sorted(gastos_por_dia):
        lista = gastos_por_dia[dia]

        container_dia = ttk.Frame(container)
        container_dia.pack(fill="x", pady=(5, 0))

        label_dia = ttk.Label(
            container_dia,
            text=f"📅 Dia {int(dia):02d}",
            foreground="#0d6efd",
            font=("Segoe UI Semibold", 11),
            cursor="hand2"
        )
        label_dia.pack(anchor="w", fill="x", pady=(0, 3))

        frame_detalhes = ttk.Frame(container_dia, padding=(15, 5))

        gastos_por_tipo = defaultdict(list)
        for idx, gasto in lista:
            tipo = gasto.get("tipo", "Indefinido")
            gastos_por_tipo[tipo].append(gasto)

        for tipo, gastos_lista in sorted(gastos_por_tipo.items()):
            label_tipo = ttk.Label(frame_detalhes, text=f"{tipo}:", font=("Segoe UI Semibold", 10), foreground="#212529")
            label_tipo.pack(anchor="w", padx=10, pady=(6, 2))

            for idx, gasto in enumerate(info["gastos"]):
                if gasto in gastos_lista:
                    valor_fmt = locale.currency(gasto["valor"], grouping=True)
                    desc = gasto.get("descricao", "Sem descrição")
                    gasto_text = f"• {desc}: {valor_fmt}"

                    container_gasto = ttk.Frame(frame_detalhes)
                    container_gasto.pack(anchor="w", fill="x", padx=30, pady=2)

                    ttk.Label(container_gasto, text=gasto_text, font=("Segoe UI", 9), foreground="#495057").pack(side="left")

                    btn_editar = ttk.Label(container_gasto, text="🖉", font=("Segoe UI", 10), foreground="#0d6efd", cursor="hand2")
                    btn_editar.pack(side="left", padx=8)
                    btn_editar.bind("<Button-1>", lambda e, idx=idx: editar_gasto_diario(idx, callback_apos_salvar=recarregar_callback))

                    btn_excluir = ttk.Label(container_gasto, text="🗑️", font=("Segoe UI", 10), foreground="#dc3545", cursor="hand2")
                    btn_excluir.pack(side="left")
                    btn_excluir.bind("<Button-1>", lambda e, idx=idx: excluir_gasto_diario(
                        idx, janela_detalhes=janela_detalhes, callback_apos_excluir=recarregar_callback))

        label_dia.bind("<Button-1>", lambda e, f=frame_detalhes, d=dia: toggle_detalhes_gastos(f, d))
        if estado_expansao_gastos_diarios.get(dia):
            frame_detalhes.pack(fill="x", padx=10, pady=(5, 10))

def mostrar_gastos_detalhados():
    global estado_expansao_gastos_diarios
    estado_expansao_gastos_diarios = defaultdict(bool)

    nova_janela = tk.Toplevel(app)
    nova_janela.title("Gastos Diários Detalhados")

    largura = 800
    altura = 800
    x = (nova_janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (nova_janela.winfo_screenheight() // 2) - (altura // 2)
    nova_janela.geometry(f"{largura}x{altura}+{x}+{y}")

    frame_topo = ttk.Frame(nova_janela)
    frame_topo.pack(side="top", fill="x", pady=(10, 5))
    frame_centro = ttk.Frame(frame_topo)
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
        command=lambda: adicionar_valor("Adicionar Gasto", "gasto", callback_apos_salvar=recarregar_gastos)
    )
    btn_adicionar.pack()

    canvas = tk.Canvas(nova_janela)
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

        canvas = tk.Canvas(parent, width=90, height=28, highlightthickness=0, bg=bg)

        raio = 10
        x0, y0, x1, y1 = 2, 2, 88, 26

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
            canvas.create_text((x0+x1)//2, (y0+y1)//2, text=texto, fill="white", font=("Segoe UI", 10, "bold"))

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
                font=("Segoe UI Semibold", 12),
                cursor="hand2"
            )
            estado_expansao_cartoes[nome_cartao] = False
        else:
            frame.pack(fill="x", padx=20, pady=(0, 10))
            label_widget.config(
                text=f"💳 {nome_cartao}: {locale.currency(total, grouping=True)} ▼",
                foreground="#0d6efd",
                font=("Segoe UI Semibold", 12),
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
        container_cartao.pack(fill="x", padx=10, pady=(8, 0))

        frame_titulo = ttk.Frame(container_cartao)
        frame_titulo.pack(fill="x", padx=0)

        frame_titulo.columnconfigure(0, weight=1)

        label = ttk.Label(
            frame_titulo,
            text=f"💳 {nome_cartao}: {locale.currency(total_cartao, grouping=True)}",
            foreground="#0d6efd",
            font=("Segoe UI Semibold", 12),
            cursor="hand2"
        )
        label.grid(row=0, column=0, sticky="we")

        badge = criar_badge_status(frame_titulo, status_cartao, partial(alternar_status_cartao, nome_cartao))
        badge.grid(row=0, column=1, sticky="e", padx=(1,0))

        label.bind("<Enter>", lambda e: label.config(foreground="#0a58ca"))
        label.bind("<Leave>", lambda e: label.config(foreground="#0d6efd"))

        frame_detalhes = ttk.Frame(container_cartao, padding=(10, 5))

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
            container.pack(anchor="w", fill="x", padx=10, pady=2)

            ttk.Label(container, text=texto, font=("Segoe UI", 10)).pack(side="left")

            btn_editar = ttk.Label(container, text="🖉", font=("Segoe UI", 11), foreground="#0d6efd", cursor="hand2")
            btn_editar.pack(side="left", padx=8)
            btn_editar.bind("<Button-1>", partial(lambda e, gasto: editar_gasto_cartao(gasto, callback_apos_salvar=recarregar_callback), gasto=c))

            btn_excluir = ttk.Label(container, text="🗑️", font=("Segoe UI", 11), foreground="#dc3545", cursor="hand2")
            btn_excluir.pack(side="left")
            btn_excluir.bind("<Button-1>", partial(lambda e, gasto: excluir_gasto_cartao(gasto, parent_janela=parent_janela, callback_apos_excluir=recarregar_gastos), gasto=c))

        if estado_expansao_cartoes.get(nome_cartao):
            frame_detalhes.pack(fill="x", padx=20, pady=(0, 10))

def abrir_cartao_credito_detalhado():
    global janela_gastos_detalhados
    janela_gastos_detalhados = tk.Toplevel(app)
    janela_gastos_detalhados.title("Cartões de Crédito Detalhados")

    largura, altura = 800, 800
    x = (janela_gastos_detalhados.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela_gastos_detalhados.winfo_screenheight() // 2) - (altura // 2)
    janela_gastos_detalhados.geometry(f"{largura}x{altura}+{x}+{y}")

    btn_adicionar = ttk.Button(
        janela_gastos_detalhados,
        text="➕ Adicionar Gasto no Cartão",
        command=lambda: adicionar_cartao_credito(callback_apos_salvar=recarregar_gastos)
    )
    btn_adicionar.pack(pady=10)

    container = ttk.Frame(janela_gastos_detalhados, padding=15)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container)
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

def atualizar_tipo_gasto_combo(combobox):
    combobox["values"] = tipos_gasto
    if tipos_gasto:
        combobox.set(tipos_gasto[0])

def adicionar_valor(titulo, tipo, callback_apos_salvar=None):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)
    inicializar_mes(mes, ano)

    janela = tk.Toplevel(app)
    janela.title(titulo)

    largura = 300
    altura = 300 if tipo == "gasto" else 200
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.attributes("-topmost", True)
    janela.grab_set()

    ttk.Label(janela, text="Descrição:").pack(pady=2)
    entrada_desc = ttk.Entry(janela)
    entrada_desc.pack(pady=2)

    ttk.Label(janela, text="Valor (R$):").pack(pady=2)
    entrada_valor = ttk.Entry(janela)
    entrada_valor.pack(pady=2)

    if tipo == "gasto":
        ttk.Label(janela, text="Dia do Gasto (1-31):").pack(pady=2)
        entrada_dia = ttk.Entry(janela)
        entrada_dia.pack(pady=2)

        ttk.Label(janela, text="Tipo de Gasto:").pack(pady=2)
        tipo_gasto_combo = ttk.Combobox(janela, state="readonly")
        tipo_gasto_combo.pack(pady=2)
        atualizar_tipo_gasto_combo(tipo_gasto_combo)

    def mostrar_erro_toplevel(mensagem, parent=janela):
        erro_janela = tk.Toplevel(parent)
        erro_janela.title("Erro")
        erro_janela.geometry("300x100")
        erro_janela.attributes("-topmost", True)
        erro_janela.grab_set()

        ttk.Label(erro_janela, text=mensagem, foreground="red", wraplength=280).pack(pady=10)
        ttk.Button(erro_janela, text="OK", command=erro_janela.destroy).pack()

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
                "dia": dia
            })

        atualizar_resumo()
        if callback_apos_salvar:
            callback_apos_salvar()
        janela.destroy()

    ttk.Button(janela, text="Salvar", command=salvar).pack(pady=10)
    janela.bind("<Return>", lambda event: salvar())

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

    largura, altura = 400, 200
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.resizable(False, False)

    ttk.Label(janela, text="Descrição:").pack(padx=10, pady=(10, 0), anchor="w")
    entry_descricao = ttk.Entry(janela)
    entry_descricao.pack(padx=10, pady=5, fill="x")
    entry_descricao.insert(0, gasto["descricao"])

    ttk.Label(janela, text="Valor:").pack(padx=10, pady=(10, 0), anchor="w")
    entry_valor = ttk.Entry(janela)
    entry_valor.pack(padx=10, pady=5, fill="x")
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

    ttk.Button(janela, text="Salvar", command=salvar).pack(pady=10)
    janela.bind("<Return>", salvar)
    entry_descricao.focus_set()

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

    largura = 350
    altura = 480
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.attributes("-topmost", True)
    janela.grab_set()

    ultimo_cartao = ultima_selecao_cartao if ultima_selecao_cartao in [c["nome"] for c in cartoes] else cartoes[0]["nome"]
    ultimo_tipo = ultima_selecao_tipo if ultima_selecao_tipo in tipos_gasto else tipos_gasto[0]

    ttk.Label(janela, text="Descrição:").pack(pady=2)
    entrada_desc = ttk.Entry(janela)
    entrada_desc.pack(pady=2)

    ttk.Label(janela, text="Valor Total (R$):").pack(pady=2)
    entrada_valor = ttk.Entry(janela)
    entrada_valor.pack(pady=2)

    ttk.Label(janela, text="Parcelas:").pack(pady=2)
    entrada_parcelas = ttk.Entry(janela)
    entrada_parcelas.insert(0, "1")
    entrada_parcelas.pack(pady=2)

    ttk.Label(janela, text="Data do Gasto (DDMMAAAA):").pack(pady=2)
    entrada_data = ttk.Entry(janela)
    entrada_data.pack(pady=2)

    ttk.Label(janela, text="Tipo de Gasto:").pack(pady=2)
    combo_tipo = ttk.Combobox(janela, values=tipos_gasto, state="readonly")
    combo_tipo.set(ultimo_tipo)
    combo_tipo.pack(pady=2)

    ttk.Label(janela, text="Cartão:").pack(pady=2)
    nomes_cartoes = [c["nome"] for c in cartoes]
    cartao_combo = ttk.Combobox(janela, values=nomes_cartoes, state="readonly")
    cartao_combo.set(ultimo_cartao)
    cartao_combo.pack(pady=2)

    fixo_var = tk.BooleanVar()
    check_fixo = ttk.Checkbutton(janela, text="Gasto Fixo (repetir todo mês)", variable=fixo_var)
    check_fixo.pack(pady=4)

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

    botao_salvar = ttk.Button(janela, text="Salvar", command=salvar)
    botao_salvar.pack(pady=(10, 15))
    janela.bind("<Return>", salvar)

def mostrar_erro_toplevel(mensagem, parent):
    erro_janela = tk.Toplevel(parent)
    erro_janela.title("Erro")
    erro_janela.geometry("300x100")
    erro_janela.attributes("-topmost", True)
    erro_janela.grab_set()

    ttk.Label(erro_janela, text=mensagem, foreground="red", wraplength=280).pack(pady=10)
    ttk.Button(erro_janela, text="OK", command=erro_janela.destroy).pack()

    erro_janela.update_idletasks()
    w = erro_janela.winfo_width()
    h = erro_janela.winfo_height()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
    erro_janela.geometry(f"+{x}+{y}")

def excluir_cartao(janela_anterior):
    if not cartoes:
        messagebox.showinfo("Aviso", "Nenhum cartão cadastrado para excluir.")
        janela_anterior.destroy()
        return

    # Crie a nova janela antes de destruir a anterior
    nova_janela = tk.Toplevel(app)
    nova_janela.title("Excluir Cartão")
    largura = 300
    altura = 150
    x = (nova_janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (nova_janela.winfo_screenheight() // 2) - (altura // 2)
    nova_janela.geometry(f"{largura}x{altura}+{x}+{y}")
    nova_janela.attributes("-topmost", True)
    nova_janela.grab_set()

    janela_anterior.destroy()

    ttk.Label(nova_janela, text="Selecione o cartão para excluir:").pack(pady=5)

    nomes_cartoes = [c['nome'] for c in cartoes]
    combo_cartoes = ttk.Combobox(nova_janela, values=nomes_cartoes, state="readonly")
    combo_cartoes.pack(pady=5)
    combo_cartoes.current(0)

    def mostrar_erro_toplevel(mensagem):
        erro_janela = tk.Toplevel(nova_janela)
        erro_janela.title("Erro")
        erro_janela.geometry("300x100")
        erro_janela.attributes("-topmost", True)
        erro_janela.grab_set()

        ttk.Label(erro_janela, text=mensagem, foreground="red", wraplength=280).pack(pady=10)
        ttk.Button(erro_janela, text="OK", command=erro_janela.destroy).pack()

        erro_janela.update_idletasks()
        w = erro_janela.winfo_width()
        h = erro_janela.winfo_height()
        x = nova_janela.winfo_rootx() + (nova_janela.winfo_width() // 2) - (w // 2)
        y = nova_janela.winfo_rooty() + (nova_janela.winfo_height() // 2) - (h // 2)
        erro_janela.geometry(f"+{x}+{y}")

    def confirmar_exclusao(cartao_nome, ao_confirmar):
        confirm_janela = tk.Toplevel(nova_janela)
        confirm_janela.title("Confirmar Exclusão")
        confirm_janela.geometry("320x140")
        confirm_janela.grab_set()
        confirm_janela.attributes("-topmost", True)

        ttk.Label(confirm_janela,
                  text=f"Excluir o cartão '{cartao_nome}'?\nGastos anteriores permanecerão.",
                  wraplength=280).pack(pady=15)

        botoes = ttk.Frame(confirm_janela)
        botoes.pack()

        ttk.Button(botoes, text="Sim", command=lambda: (confirm_janela.destroy(), ao_confirmar())).pack(side="left", padx=10)
        ttk.Button(botoes, text="Não", command=confirm_janela.destroy).pack(side="right", padx=10)

        # Centralizar
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
        confirmar_exclusao(cartao_excluir['nome'], lambda: (
            cartoes.remove(cartao_excluir),
            atualizar_resumo(),
            exibir_cartao(),
            nova_janela.destroy()
        ))

    ttk.Button(nova_janela, text="Excluir", command=excluir).pack(pady=10)

def editar_gasto_cartao(gasto_original, callback_apos_salvar=None):
    janela = tk.Toplevel(app)
    janela.title("Editar Gasto no Cartão")

    largura = 350
    altura = 420
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.attributes("-topmost", True)
    janela.grab_set()

    fixo = gasto_original.get("fixo", False)
    parcelas = 1 if fixo else gasto_original.get("total_parcelas", 1) or 1
    valor_parcela = round(gasto_original["valor"], 2)

    ttk.Label(janela, text="Descrição:").pack(pady=2)
    entrada_desc = ttk.Entry(janela)
    entrada_desc.insert(0, gasto_original["descricao"])
    entrada_desc.pack(pady=2)

    ttk.Label(janela, text="Valor da Parcela (R$):").pack(pady=2)
    entrada_valor = ttk.Entry(janela)
    entrada_valor.insert(0, str(valor_parcela))
    entrada_valor.pack(pady=2)

    ttk.Label(janela, text="Tipo de Gasto:").pack(pady=2)
    combo_tipo = ttk.Combobox(janela, values=tipos_gasto, state="readonly")
    combo_tipo.set(gasto_original.get("tipo", tipos_gasto[0]))
    combo_tipo.pack(pady=2)

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

    ttk.Button(janela, text="Salvar", command=salvar).pack(pady=(10, 20))
    janela.bind("<Return>", lambda e: salvar())

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

def excluir_cartao(janela_anterior):
    if not cartoes:
        messagebox.showinfo("Aviso", "Nenhum cartão cadastrado para excluir.")
        janela_anterior.destroy()
        return

    nova_janela = tk.Toplevel(app)
    nova_janela.title("Excluir Cartão")
    largura = 300
    altura = 150
    x = (nova_janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (nova_janela.winfo_screenheight() // 2) - (altura // 2)
    nova_janela.geometry(f"{largura}x{altura}+{x}+{y}")
    nova_janela.attributes("-topmost", True)
    nova_janela.grab_set()

    janela_anterior.destroy()

    ttk.Label(nova_janela, text="Selecione o cartão para excluir:").pack(pady=5)

    # Função para atualizar o combobox com os nomes atuais dos cartões
    def atualizar_combo():
        nomes_cartoes = [c['nome'] for c in cartoes]
        combo_cartoes['values'] = nomes_cartoes
        if nomes_cartoes:
            combo_cartoes.current(0)
        else:
            combo_cartoes.set('')

    combo_cartoes = ttk.Combobox(nova_janela, state="readonly")
    combo_cartoes.pack(pady=5)

    atualizar_combo()  # inicializa com os nomes atuais

    def mostrar_erro_toplevel(mensagem):
        erro_janela = tk.Toplevel(nova_janela)
        erro_janela.title("Erro")
        erro_janela.geometry("300x100")
        erro_janela.attributes("-topmost", True)
        erro_janela.grab_set()

        ttk.Label(erro_janela, text=mensagem, foreground="red", wraplength=280).pack(pady=10)
        ttk.Button(erro_janela, text="OK", command=erro_janela.destroy).pack()

        erro_janela.update_idletasks()
        w = erro_janela.winfo_width()
        h = erro_janela.winfo_height()
        x = nova_janela.winfo_rootx() + (nova_janela.winfo_width() // 2) - (w // 2)
        y = nova_janela.winfo_rooty() + (nova_janela.winfo_height() // 2) - (h // 2)
        erro_janela.geometry(f"+{x}+{y}")

    def confirmar_exclusao(cartao_nome, ao_confirmar):
        confirm_janela = tk.Toplevel(nova_janela)
        confirm_janela.title("Confirmar Exclusão")
        confirm_janela.geometry("320x140")
        confirm_janela.grab_set()
        confirm_janela.attributes("-topmost", True)

        ttk.Label(confirm_janela,
                  text=f"Excluir o cartão '{cartao_nome}'?\nGastos anteriores permanecerão.",
                  wraplength=280).pack(pady=15)

        botoes = ttk.Frame(confirm_janela)
        botoes.pack()

        ttk.Button(botoes, text="Sim", command=lambda: (confirm_janela.destroy(), ao_confirmar())).pack(side="left", padx=10)
        ttk.Button(botoes, text="Não", command=confirm_janela.destroy).pack(side="right", padx=10)

        # Centralizar
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
            atualizar_resumo()
            exibir_cartao()
            atualizar_combo()  # Atualiza a lista do combo para refletir a exclusão
            if not cartoes:
                # Se não tiver mais cartões, fecha a janela
                nova_janela.destroy()

        confirmar_exclusao(cartao_excluir['nome'], apos_confirmar)

    ttk.Button(nova_janela, text="Excluir", command=excluir).pack(pady=10)

def adicionar_cartao(janela_anterior):
    janela_anterior.destroy()
    janela = tk.Toplevel(app)
    janela.title("Adicionar Cartão")

    largura = 300
    altura = 200
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.attributes("-topmost", True)
    janela.grab_set()

    ttk.Label(janela, text="Nome do Cartão:").pack(pady=5)
    entrada_nome = ttk.Entry(janela)
    entrada_nome.pack(pady=5)

    ttk.Label(janela, text="Dia de Fechamento da Fatura (1-31):").pack(pady=5)
    entrada_fechamento = ttk.Entry(janela)
    entrada_fechamento.pack(pady=5)

    def mostrar_erro_toplevel(mensagem):
        erro_janela = tk.Toplevel(janela)
        erro_janela.title("Erro")
        erro_janela.geometry("300x100")
        erro_janela.attributes("-topmost", True)
        erro_janela.grab_set()

        ttk.Label(erro_janela, text=mensagem, foreground="red", wraplength=280).pack(pady=10)
        ttk.Button(erro_janela, text="OK", command=erro_janela.destroy).pack()

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

    ttk.Button(janela, text="Salvar", command=salvar).pack(pady=15)

    # Bind para tecla Enter ativar salvar
    janela.bind("<Return>", lambda event: salvar())

def excluir_cartao(janela_anterior):
    if not cartoes:
        messagebox.showinfo("Aviso", "Nenhum cartão cadastrado para excluir.")
        janela_anterior.destroy()
        return

    nova_janela = tk.Toplevel(app)
    nova_janela.title("Excluir Cartão")
    largura = 300
    altura = 150
    x = (nova_janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (nova_janela.winfo_screenheight() // 2) - (altura // 2)
    nova_janela.geometry(f"{largura}x{altura}+{x}+{y}")
    nova_janela.attributes("-topmost", True)
    nova_janela.grab_set()

    janela_anterior.destroy()

    ttk.Label(nova_janela, text="Selecione o cartão para excluir:").pack(pady=5)

    # Cria o combobox vazio (será preenchido abaixo)
    combo_cartoes = ttk.Combobox(nova_janela, state="readonly")
    combo_cartoes.pack(pady=5)

    # Atualiza os cartões no combobox
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
        erro_janela.geometry("300x100")
        erro_janela.attributes("-topmost", True)
        erro_janela.grab_set()

        ttk.Label(erro_janela, text=mensagem, foreground="red", wraplength=280).pack(pady=10)
        ttk.Button(erro_janela, text="OK", command=erro_janela.destroy).pack()

        erro_janela.update_idletasks()
        w = erro_janela.winfo_width()
        h = erro_janela.winfo_height()
        x = nova_janela.winfo_rootx() + (nova_janela.winfo_width() // 2) - (w // 2)
        y = nova_janela.winfo_rooty() + (nova_janela.winfo_height() // 2) - (h // 2)
        erro_janela.geometry(f"+{x}+{y}")

    def confirmar_exclusao(cartao_nome, ao_confirmar):
        confirm_janela = tk.Toplevel(nova_janela)
        confirm_janela.title("Confirmar Exclusão")
        confirm_janela.geometry("320x140")
        confirm_janela.grab_set()
        confirm_janela.attributes("-topmost", True)

        ttk.Label(confirm_janela,
                  text=f"Excluir o cartão '{cartao_nome}'?\nGastos antigos serão mantidos.",
                  wraplength=280).pack(pady=15)

        botoes = ttk.Frame(confirm_janela)
        botoes.pack()

        ttk.Button(botoes, text="Sim", command=lambda: (confirm_janela.destroy(), ao_confirmar())).pack(side="left", padx=10)
        ttk.Button(botoes, text="Não", command=confirm_janela.destroy).pack(side="right", padx=10)

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
            # Remove o cartão da lista
            cartoes.remove(cartao_excluir)

            # Atualiza tudo que depende dos cartões
            salvar_dados()
            atualizar_resumo()
            atualizar_combo()

            # Se nenhum cartão sobrou, fecha a janela
            if not cartoes:
                nova_janela.destroy()

        confirmar_exclusao(cartao_excluir['nome'], apos_confirmar)

    ttk.Button(nova_janela, text="Excluir", command=excluir).pack(pady=10)

def editar_despesa_fixa(indice):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)
    info = inicializar_mes(mes, ano)

    d = info["despesas_fixas"][indice]

    janela = tk.Toplevel(app)
    janela.title("Editar Despesa Fixa")
    largura, altura = 400, 250
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.attributes("-topmost", True)
    janela.grab_set()

    janela.bind("<Return>", lambda event: salvar_alteracoes())

    ttk.Label(janela, text="Descrição:").pack(pady=(10, 0))
    ttk.Label(janela, text=d["descricao"]).pack()

    ttk.Label(janela, text="Valor (R$):").pack()
    valor_entry = ttk.Entry(janela)
    valor_entry.insert(0, f"{d['valor']:.2f}".replace(".", ","))
    valor_entry.pack()

    ttk.Label(janela, text="Vencimento (dia):").pack()
    venc_entry = ttk.Entry(janela)
    venc_entry.insert(0, str(d.get("vencimento", "")))
    venc_entry.pack()

    status_btn = ttk.Button(janela, text=f"Alternar Status (Atual: {d['status']})")

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
        status_btn.config(text=f"Alternar Status (Atual: {d['status']})")
        salvar_dados()
        atualizar_resumo()

    status_btn.config(command=alternar_status)
    status_btn.pack(pady=5)

    ttk.Button(janela, text="Salvar", command=salvar_alteracoes).pack(pady=10)

def adicionar_despesa_fixa():
    janela = tk.Toplevel(app)
    janela.title("Nova Despesa Fixa")
    largura, altura = 300, 250
    janela.geometry(f"{largura}x{altura}")
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.attributes("-topmost", True)
    janela.grab_set()

    ttk.Label(janela, text="Descrição:").pack(pady=2)
    entrada_desc = ttk.Entry(janela)
    entrada_desc.pack(pady=2)

    ttk.Label(janela, text="Valor (R$):").pack(pady=2)
    entrada_valor = ttk.Entry(janela)
    entrada_valor.pack(pady=2)

    ttk.Label(janela, text="Dia de vencimento (1 a 31):").pack(pady=2)
    entrada_venc = ttk.Entry(janela)
    entrada_venc.pack(pady=2)

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

    ttk.Button(janela, text="Salvar", command=salvar).pack(pady=10)
    janela.bind("<Return>", lambda event: salvar())

def editar_tipos_gastos(janela_anterior):
    global tipos_gasto
    janela_anterior.destroy()

    janela = tk.Toplevel(app)
    janela.title("Editar Tipos de Gastos")
    largura = 400
    altura = 500
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.transient(app)
    janela.grab_set()

    ttk.Label(janela, text="Tipos de Gastos Atuais:").pack(pady=5)
    lista_tipos = tk.Listbox(janela, height=10)
    for tipo in tipos_gasto:
        lista_tipos.insert(tk.END, tipo)
    lista_tipos.pack(pady=5)

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
        if selecionado:
            tipo_selecionado = lista_tipos.get(selecionado)
            confirmar = messagebox.askyesno("Confirmar", f"Deseja excluir o tipo '{tipo_selecionado}'?")
            if confirmar:
                tipos_gasto.remove(tipo_selecionado)
                lista_tipos.delete(selecionado)
                janela.lift()
                salvar_dados()
        else:
            messagebox.showerror("Erro", "Selecione um tipo para excluir.")

    def editar_tipo():
        selecionado = lista_tipos.curselection()
        if selecionado:
            indice = selecionado[0]
            novo_nome = entrada_novo_tipo.get().strip()
            antigo_nome = lista_tipos.get(indice)

            if not novo_nome:
                messagebox.showwarning("Aviso", "Digite um nome válido.")
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

    ttk.Label(janela, text="Novo Tipo de Gasto ou Edição:").pack(pady=5)
    entrada_novo_tipo = ttk.Entry(janela)
    entrada_novo_tipo.pack(pady=5)

    ttk.Button(janela, text="Adicionar Tipo", command=adicionar_tipo).pack(pady=5)
    ttk.Button(janela, text="Excluir Tipo Selecionado", command=excluir_tipo).pack(pady=5)
    ttk.Button(janela, text="Editar Tipo Selecionado", command=editar_tipo).pack(pady=5)

    print(f"Tipos de gastos após carregamento: {tipos_gasto}")

# Interface
frame_selecao = ttk.Frame(app)
frame_selecao.pack(pady=10)

meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
combo_mes = ttk.Combobox(frame_selecao, values=meses, state="readonly", width=12)
anos = [str(y) for y in range(2025, 2050)]
combo_ano = ttk.Combobox(frame_selecao, values=anos, state="readonly", width=6)

# ⬇️ Carregar última seleção salva, se existir
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

combo_mes.pack(side="left", padx=5)
combo_ano.pack(side="left", padx=5)

combo_mes.bind("<<ComboboxSelected>>", lambda e: atualizar_resumo())
combo_ano.bind("<<ComboboxSelected>>", lambda e: atualizar_resumo())

frame_botoes = ttk.Frame(app)
frame_botoes.pack(pady=5)

frame_resumo = ttk.LabelFrame(app, text="Resumo Geral", padding=10)
frame_resumo.pack(fill="x", padx=10, pady=5)

frame_main = ttk.Frame(app)
frame_main.pack(fill="both", expand=True, padx=10, pady=5)

frame_receitas = ttk.LabelFrame(frame_main, text="Receitas", padding=10)
frame_receitas.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

frame_despesas = ttk.LabelFrame(frame_main, text="Despesas Fixas", padding=10)
frame_despesas.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

frame_gastos = ttk.LabelFrame(frame_main, text="Gastos Diários", padding=10)
frame_gastos.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

frame_credito = ttk.LabelFrame(frame_main, text="Cartão de Crédito", padding=10)
frame_credito.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

frame_main.rowconfigure(0, weight=1)
frame_main.rowconfigure(1, weight=1)
frame_main.columnconfigure(0, weight=1)
frame_main.columnconfigure(1, weight=1)

# --- Criar canvas + scrollbar + scroll_frame para cada frame principal ---

def criar_area_com_scroll(frame_pai, altura=180, exibir_scroll=True):
    canvas = tk.Canvas(frame_pai, height=altura)

    scroll_frame = ttk.Frame(canvas)
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

    # 🔽 Adiciona suporte à rolagem com a bolinha do mouse
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    scroll_frame.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
    scroll_frame.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

    return canvas, scrollbar, scroll_frame

canvas_receitas, scrollbar_receitas, scroll_frame_receitas = criar_area_com_scroll(frame_receitas)
canvas_despesas, scrollbar_despesas, scroll_frame_despesas = criar_area_com_scroll(frame_despesas)
canvas_gastos, scrollbar_gastos, scroll_frame_gastos = criar_area_com_scroll(frame_gastos, altura=50, exibir_scroll=False)
canvas_credito, scrollbar_credito, scroll_frame_credito = criar_area_com_scroll(frame_credito, altura=50, exibir_scroll=False)


canvas_receitas.config(height=300)
canvas_despesas.config(height=200)
canvas_gastos.config(height=50)
canvas_credito.config(height=50)

# Inicializa dados para o mês atual
atualizar_resumo()
app.mainloop()