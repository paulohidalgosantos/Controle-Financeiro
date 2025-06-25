import os, sys, time, json, copy, locale
from datetime import datetime
from collections import defaultdict
from operator import itemgetter
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import ttkbootstrap as tb
from ttkbootstrap import Style
from functools import partial
import urllib.request
import webbrowser
from ttkbootstrap.constants import *

VERSAO_ATUAL = "1.0.1"

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
cartoes_fechamento = {}

# Funções de dados
def carregar_dados():
    global dados, cartoes, contas_fixas_modelo, tipos_gasto
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

        except Exception as e:
            print("Erro ao carregar dados:", e)

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
                "tipos_gasto": tipos_gasto
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
app.title("Controle Financeiro")
app.state('zoomed')

# Carregar os dados
carregar_dados()

# ---- Funções usadas no menu ----

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
    if messagebox.askyesno("Confirmar", "Deseja realmente zerar todos os dados?"):
        global dados, contas_fixas_modelo, cartoes, tipos_gasto
        dados.clear()
        contas_fixas_modelo.clear()
        cartoes.clear()
        tipos_gasto = TIPOS_GASTO_PADRAO.copy()  # <<< RESTAURA OS PADRÕES
        salvar_dados()
        atualizar_resumo()
        messagebox.showinfo("Zerado", "Todos os dados foram apagados e os tipos de gastos foram restaurados.")

        
# Criar barra de menu (deve vir depois das funções que ela usa)
def criar_menu():
    menubar = tk.Menu(app)

    menu_gerenciar = tk.Menu(menubar, tearoff=0, font=("Segoe UI", 10))
    menu_gerenciar.add_command(label="💳  Gerenciar Cartões", command=gerenciar_cartoes)
    menu_gerenciar.add_command(label="📂  Categorias de Gastos", command=abrir_gerenciador_categorias)
    menu_gerenciar.add_separator()
    menu_gerenciar.add_command(label="🔄  Buscar Atualização", command=buscar_atualizacao)
    menu_gerenciar.add_separator()
    menu_gerenciar.add_command(label="🗑️  Zerar Aplicativo", command=zerar_tudo)

    menubar.add_cascade(label="⚙️  Gerenciar", menu=menu_gerenciar)
    app.config(menu=menubar)

def buscar_atualizacao():
    url_versao = "https://raw.githubusercontent.com/paulohidalgosantos/Controle-Financeiro/main/versao.txt"
    try:
        with urllib.request.urlopen(url_versao, timeout=5) as response:
            versao_remota = response.read().decode().strip()

        if versao_remota > VERSAO_ATUAL:
            if messagebox.askyesno("Atualização disponível", f"Nova versão {versao_remota} disponível.\nDeseja baixar agora?"):
                abrir_link_download()
        else:
            messagebox.showinfo("Atualização", "Você já está usando a versão mais recente.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao verificar atualização:\n{e}")

def abrir_link_download():
    # Você pode personalizar isso com o link do executável mais recente
    webbrowser.open("https://github.com/paulohidalgosantos/Controle-Financeiro/releases/latest")

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

def inicializar_mes(mes, ano):
    chave = get_chave(mes, ano)
    
    if chave not in dados:
        # Inicializa o mês com estrutura padrão
        dados[chave] = {
            "receitas": {},
            "conta": 0.0,
            "despesas_fixas": copy.deepcopy(contas_fixas_modelo),
            "gastos": [],
            "cartao_credito": [],
            "tipos": []
        }
        
        # Calcula mês e ano anterior, com ciclo anual
        mes_ant = mes - 1 if mes > 1 else 12
        ano_ant = ano if mes > 1 else ano - 1
        chave_anterior = get_chave(mes_ant, ano_ant)
        
        if chave_anterior in dados:
            info_ant = dados[chave_anterior]

            total_receitas_ant = sum(info_ant["receitas"].values())
            total_gastos_ant = sum(g["valor"] for g in info_ant["gastos"])
            total_credito_ant = sum(c["valor"] for c in info_ant["cartao_credito"])
            # Aqui consideramos TODAS as despesas fixas (pagas ou não)
            total_despesas_todas_ant = sum(d["valor"] for d in info_ant["despesas_fixas"])

            saldo_final_mes_anterior = info_ant["conta"] + total_receitas_ant - total_gastos_ant - total_credito_ant - total_despesas_todas_ant

            # Ajusta saldo inicial do mês atual para saldo final do mês anterior
            dados[chave]["conta"] = saldo_final_mes_anterior

    return dados[chave]

def calcular_saldo(chave):
    info = dados[chave]
    total_receitas = sum(info["receitas"].values())
    total_despesas_pagas = sum([d["valor"] for d in info["despesas_fixas"] if d["status"] == "Pago"])
    total_gastos = sum([g["valor"] for g in info["gastos"]])
    total_credito = sum([c["valor"] for c in info["cartao_credito"] if c["mes"] == chave[0] and c["ano"] == chave[1]])
    return total_receitas - total_gastos - total_credito - total_despesas_pagas

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

    for frame in [scroll_frame_receitas, scroll_frame_despesas, scroll_frame_gastos, scroll_frame_credito, frame_resumo]:
        for widget in frame.winfo_children():
            widget.destroy()

    # RECEITAS
    frame_receitas_topo = ttk.Frame(scroll_frame_receitas)
    frame_receitas_topo.pack(fill="x", pady=(0, 8))

    frame_receitas_header = ttk.Frame(frame_receitas_topo)
    frame_receitas_header.pack(fill="x")

    btn_adicionar_receita = ttk.Label(frame_receitas_header, text="➕", font=("Segoe UI", 14), foreground="blue", cursor="hand2")
    btn_adicionar_receita.grid(row=0, column=0, sticky="w", padx=5)
    btn_adicionar_receita.bind("<Button-1>", lambda e: adicionar_valor("Adicionar Receita", "receita"))

    label_receitas = ttk.Label(frame_receitas_header, text="Receitas", font=("Segoe UI", 12, "bold"))
    label_receitas.grid(row=0, column=1, sticky="w")

    frame_receitas_header.grid_columnconfigure(1, weight=1)

    frame_receitas_conteudo = ttk.Frame(frame_receitas_topo)
    frame_receitas_conteudo.pack(fill="x")

    for nome, valor in list(info["receitas"].items()):
        frame_linha = ttk.Frame(frame_receitas_conteudo)
        frame_linha.pack(anchor="w", fill="x", pady=2)

        ttk.Label(frame_linha, text=f"{nome}: {locale.currency(valor, grouping=True)}", foreground="#155724").pack(side="left", anchor="w")

        btn_excluir = ttk.Label(frame_linha, text="🗑️", font=("Segoe UI", 10), foreground="red", cursor="hand2")
        btn_excluir.pack(side="right", padx=5)
        btn_excluir.bind("<Button-1>", lambda e, nome_receita=nome: excluir_receita(nome_receita))

    total_receitas = sum(info["receitas"].values())
    ttk.Label(frame_receitas_conteudo, text=f"Total: {locale.currency(total_receitas, grouping=True)}", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=5)

    # DESPESAS FIXAS
    frame_despesa_topo = ttk.Frame(scroll_frame_despesas)
    frame_despesa_topo.pack(fill="x", pady=(0, 8))

    frame_despesa_header = ttk.Frame(frame_despesa_topo)
    frame_despesa_header.pack(fill="x")

    btn_adicionar = ttk.Label(frame_despesa_header, text="➕", font=("Segoe UI", 14), foreground="blue", cursor="hand2")
    btn_adicionar.grid(row=0, column=0, sticky="w", padx=5)
    btn_adicionar.bind("<Button-1>", lambda e: adicionar_despesa_fixa())

    label_despesas = ttk.Label(frame_despesa_header, text="Despesas Fixas", font=("Segoe UI", 14, "bold"))
    label_despesas.grid(row=0, column=1, sticky="w")

    frame_despesa_header.grid_columnconfigure(1, weight=1)

    frame_despesa_conteudo = ttk.Frame(frame_despesa_topo)
    frame_despesa_conteudo.pack(fill="x")

    despesas_ordenadas = sorted(info["despesas_fixas"], key=lambda d: d.get("vencimento", 99))
    dia_atual = datetime.today().day

    for d in despesas_ordenadas:
        idx_real = info["despesas_fixas"].index(d)

        cor = "#28a745" if d["status"] == "Pago" else "#dc3545"
        vencimento = d.get("vencimento", "??")
        if d["status"] == "Aberto" and isinstance(vencimento, int) and vencimento < dia_atual:
            cor = "#b22222"
        texto = f"{d['descricao']} - {locale.currency(d['valor'], grouping=True)} - Venc: {vencimento} ({d['status']})"

        container = ttk.Frame(frame_despesa_conteudo)
        container.pack(fill="x", pady=2)

        btn_editar = ttk.Label(container, text="🖉", font=("Segoe UI", 11), foreground="blue", cursor="hand2")
        btn_editar.pack(side="left", padx=(0, 5))
        btn_editar.bind("<Button-1>", lambda e, idx=idx_real: editar_despesa_fixa(idx))

        btn_excluir = ttk.Label(container, text="🗑️", font=("Segoe UI", 11), foreground="red", cursor="hand2")
        btn_excluir.pack(side="left", padx=(0, 5))
        btn_excluir.bind("<Button-1>", lambda e, idx=idx_real: excluir_despesa_fixa(idx))

        lbl = ttk.Label(container, text=texto, foreground=cor, font=("Segoe UI", 11, "bold"))
        lbl.pack(side="left", anchor="w")

    # GASTOS DIÁRIOS
    frame_gastos_topo = ttk.Frame(scroll_frame_gastos)
    frame_gastos_topo.pack(fill="x", pady=(0, 8))

    frame_gastos_header = ttk.Frame(frame_gastos_topo)
    frame_gastos_header.pack(fill="x")

    btn_adicionar_gasto = ttk.Label(frame_gastos_header, text="➕", font=("Segoe UI", 14), foreground="blue", cursor="hand2")
    btn_adicionar_gasto.grid(row=0, column=0, sticky="w", padx=5)
    btn_adicionar_gasto.bind("<Button-1>", lambda e: adicionar_valor("Adicionar Gasto", "gasto"))

    label_gastos = ttk.Label(frame_gastos_header, text="Gastos Diários", font=("Segoe UI", 12, "bold"))
    label_gastos.grid(row=0, column=1, sticky="w")

    frame_gastos_header.grid_columnconfigure(1, weight=1)

    frame_gastos_conteudo = ttk.Frame(frame_gastos_topo)
    frame_gastos_conteudo.pack(fill="x")

    total_gastos_diarios = sum(g["valor"] for g in info["gastos"])
    ttk.Label(frame_gastos_conteudo, text=f"Gastos Diários total: {locale.currency(total_gastos_diarios, grouping=True)}", font=("Segoe UI", 12, "bold")).pack(anchor="w")

    # ... resto do código dos gastos diários permanece igual ...

    # CARTÕES DE CRÉDITO
    total_cartoes = sum(c["valor"] for c in info["cartao_credito"])

    frame_credito_topo = ttk.Frame(scroll_frame_credito)
    frame_credito_topo.pack(fill="x", padx=10, pady=(0, 5))

    frame_credito_header = ttk.Frame(frame_credito_topo)
    frame_credito_header.pack(fill="x")

    btn_adicionar_credito = ttk.Label(frame_credito_header, text="➕", font=("Segoe UI", 14), foreground="blue", cursor="hand2")
    btn_adicionar_credito.grid(row=0, column=0, sticky="w", padx=5)
    btn_adicionar_credito.bind("<Button-1>", lambda e: adicionar_cartao_credito())

    label_credito = ttk.Label(
        frame_credito_header,
        text=f"Faturas Cartão de Crédito total: {locale.currency(total_cartoes, grouping=True)}",
        font=("Segoe UI", 12, "bold")
    )
    label_credito.grid(row=0, column=1, sticky="w")

    frame_credito_header.grid_columnconfigure(1, weight=1)

    frame_credito_conteudo = ttk.Frame(frame_credito_topo)
    frame_credito_conteudo.pack(fill="x")

    gastos_cartao_por_nome = {}
    for c in info["cartao_credito"]:
        nome = c["cartao"]
        if nome not in gastos_cartao_por_nome:
            gastos_cartao_por_nome[nome] = []
        gastos_cartao_por_nome[nome].append(c)

    def toggle_detalhes(frame, label_widget, nome, total):
        if frame.winfo_ismapped():
            frame.pack_forget()
            label_widget.config(text=f"💳 {nome}: {locale.currency(total, grouping=True)} ▶", foreground="blue", font=("Segoe UI", 10, "bold"))
            estado_expansao_cartoes[nome] = False
        else:
            frame.pack(fill="x", padx=20, pady=(0, 10))
            label_widget.config(text=f"💳 {nome}: {locale.currency(total, grouping=True)} ▼", foreground="blue", font=("Segoe UI", 10, "bold"))
            estado_expansao_cartoes[nome] = True

    for nome_cartao in sorted(gastos_cartao_por_nome):
        lista = sorted(gastos_cartao_por_nome[nome_cartao], key=lambda x: (x["ano"], x["mes"], x["dia"]))
        total_cartao = sum(g["valor"] for g in lista)

        container_cartao = ttk.Frame(frame_credito_conteudo)
        container_cartao.pack(fill="x", padx=10, pady=(8, 0))

        label = ttk.Label(container_cartao,
            text=f"💳 {nome_cartao}: {locale.currency(total_cartao, grouping=True)} ▶",
            foreground="blue", font=("Segoe UI", 10, "bold"), cursor="hand2")
        label.pack(anchor="w", fill="x")

        frame_detalhes = ttk.Frame(container_cartao)

        for c in lista:
            if c.get("fixo"):
                parcela = "Fixo"
            elif c["total_parcelas"] > 1:
                parcela = f"Parcela {c['parcela_atual']}/{c['total_parcelas']}"
            else:
                parcela = "À vista"
            data = f"{c['dia']:02d}/{c['mes']:02d}/{c['ano']}"
            tipo = c.get("tipo", "Indefinido")
            valor_fmt = locale.currency(c["valor"], grouping=True)

            container_gasto = ttk.Frame(frame_detalhes)
            container_gasto.pack(anchor="w", fill="x", padx=10, pady=1)

            texto_gasto = f"• {data}: {c['descricao']} - {valor_fmt} ({parcela}) - Tipo: {tipo}"
            ttk.Label(container_gasto, text=texto_gasto, font=("Segoe UI", 9)).pack(side="left")

            btn_editar = ttk.Label(container_gasto, text="🖉", font=("Segoe UI", 10), foreground="blue", cursor="hand2")
            btn_editar.pack(side="left", padx=5)
            btn_editar.bind("<Button-1>", lambda e, gasto=c: editar_gasto_cartao(gasto))

            btn_excluir = ttk.Label(container_gasto, text="🗑️", font=("Segoe UI", 10), foreground="red", cursor="hand2")
            btn_excluir.pack(side="left")
            btn_excluir.bind("<Button-1>", lambda e, gasto=c: excluir_gasto_cartao(gasto))


        label.bind("<Button-1>", lambda e, f=frame_detalhes, l=label, n=nome_cartao, t=total_cartao: toggle_detalhes(f, l, n, t))

        if estado_expansao_cartoes.get(nome_cartao):
            frame_detalhes.pack(fill="x", padx=20, pady=(0, 10))
            label.config(text=f"💳 {nome_cartao}: {locale.currency(total_cartao, grouping=True)} ▼", foreground="blue", font=("Segoe UI", 10, "bold"))


    # ------------------- RESUMO -------------------
    total_gastos = sum(g["valor"] for g in info["gastos"])
    total_credito = sum(c["valor"] for c in info["cartao_credito"] if c["mes"] == chave[0] and c["ano"] == chave[1])
    total_pagas = sum(d["valor"] for d in info["despesas_fixas"] if d["status"] == "Pago")
    total_todas = sum(d["valor"] for d in info["despesas_fixas"])

    saldo_atual = info["conta"] + total_receitas - total_gastos - total_credito - total_pagas
    saldo_final = info["conta"] + total_receitas - total_gastos - total_credito - total_todas

    ttk.Label(frame_resumo, text=f"Saldo Atual (contas pagas): {locale.currency(saldo_atual, grouping=True)}", font=("Segoe UI", 11, "bold"), foreground="#006400").pack(anchor="w")
    ttk.Label(frame_resumo, text=f"Saldo Final (considerando todas contas): {locale.currency(saldo_final, grouping=True)}", font=("Segoe UI", 11, "bold"), foreground="#004085").pack(anchor="w", pady=3)

    # GASTOS POR TIPO (Diário + Cartão)
    ttk.Label(frame_resumo, text="Gastos por Tipo:", font=("Segoe UI", 11, "bold"), foreground="#000000").pack(anchor="w", pady=(10, 2))

    # Frame fixo com altura definida
    frame_gastos_tipo_container = ttk.Frame(frame_resumo)
    frame_gastos_tipo_container.pack(fill="x", pady=(0, 5))

    canvas_tipos = tk.Canvas(frame_gastos_tipo_container, height=20)
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

    for g in info["gastos"]:
        tipo = g["tipo"]
        gastos_por_tipo[tipo] = gastos_por_tipo.get(tipo, 0) + g["valor"]
    for c in info["cartao_credito"]:
        tipo = c.get("tipo", "Indefinido")
        gastos_por_tipo[tipo] = gastos_por_tipo.get(tipo, 0) + c["valor"]

    for tipo, valor in sorted(gastos_por_tipo.items(), key=lambda x: x[0]):
        ttk.Label(frame_tipos_interno, text=f"{tipo}: {locale.currency(valor, grouping=True)}", font=("Segoe UI", 10)).pack(anchor="w")


    # Atualiza status da janela principal
    app.update()
 
def atualizar_tipo_gasto_combo(combobox):
    combobox["values"] = tipos_gasto
    if tipos_gasto:
        combobox.set(tipos_gasto[0])

def adicionar_valor(titulo, tipo):
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
        janela.destroy()

    ttk.Button(janela, text="Salvar", command=salvar).pack(pady=10)
    janela.bind("<Return>", lambda event: salvar())

def editar_gasto_diario(idx):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    info = inicializar_mes(mes, ano)
    
    if idx < 0 or idx >= len(info["gastos"]):
        messagebox.showerror("Erro", "Índice de gasto inválido")
        return
    
    gasto = info["gastos"][idx]

    janela = tk.Toplevel(app)
    janela.title("Editar Gasto Diário")

    largura = 400
    altura = 200

    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()
    x = (largura_tela // 2) - (largura // 2)
    y = (altura_tela // 2) - (altura // 2)

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

    def salvar(event=None):  # Permite ser chamada pelo botão e pelo evento Enter
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

    btn_salvar = ttk.Button(janela, text="Salvar", command=salvar)
    btn_salvar.pack(pady=10)

    # Liga tecla Enter para salvar
    janela.bind('<Return>', salvar)

    # Opcional: foca no campo descrição para digitar direto
    entry_descricao.focus_set()

def excluir_gasto_diario(idx):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    info = inicializar_mes(mes, ano)

    if idx < 0 or idx >= len(info["gastos"]):
        messagebox.showerror("Erro", "Índice de gasto inválido")
        return

    gasto = info["gastos"][idx]

    resposta = messagebox.askyesno("Confirmação", f"Excluir gasto '{gasto['descricao']}' no dia {gasto['dia']}?")
    if resposta:
        info["gastos"].pop(idx)
        salvar_dados()
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

def adicionar_cartao_credito():
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
    combo_tipo.set(tipos_gasto[0])
    combo_tipo.pack(pady=2)

    ttk.Label(janela, text="Cartão:").pack(pady=2)
    nomes_cartoes = [c["nome"] for c in cartoes]
    cartao_combo = ttk.Combobox(janela, values=nomes_cartoes, state="readonly")
    cartao_combo.set(nomes_cartoes[0])
    cartao_combo.pack(pady=2)

    # Checkbutton para gasto fixo
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

    def salvar():
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

        # Define quantas vezes adicionar o gasto
        if fixo:
            meses_repeticao = 24  # Define por quantos meses repetir
            parcelas = 1  # sobrescreve para garantir que será à vista
        else:
            meses_repeticao = parcelas

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
                "fixo": fixo  # novo campo para identificar
            })

        atualizar_resumo()
        janela.destroy()

    botao_salvar = ttk.Button(janela, text="Salvar", command=salvar)
    botao_salvar.pack(pady=(10, 15))

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

def editar_gasto_cartao(gasto_original):
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
                        g["ano"] == ano_inicial and
                        g.get("fixo", False) == fixo and
                        (fixo or g.get("total_parcelas") == parcelas)
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

    ttk.Button(janela, text="Salvar", command=salvar).pack(pady=(10, 20))
    janela.bind("<Return>", lambda e: salvar())

def excluir_gasto_cartao(gasto):
    resposta = messagebox.askyesno("Excluir Gasto", "Deseja excluir TODAS as parcelas deste gasto?")
    if not resposta:
        return

    fixo = gasto.get("fixo", False)
    parcelas = 24 if fixo else gasto.get("total_parcelas", 1)

    dia = gasto["dia"]
    mes_inicial = gasto["mes"]
    ano_inicial = gasto["ano"]
    cartao = gasto["cartao"]

    for i in range(parcelas):
        mes_fatura = mes_inicial + i
        ano_fatura = ano_inicial + (mes_fatura - 1) // 12
        mes_fatura = (mes_fatura - 1) % 12 + 1

        chave_fatura = (mes_fatura, ano_fatura)
        if chave_fatura in dados:
            nova_lista = []
            for g in dados[chave_fatura]["cartao_credito"]:
                if not (
                    g["descricao"] == gasto["descricao"]
                    and g["cartao"] == cartao
                    and g["dia"] == dia
                    and g["mes"] == mes_inicial
                    and g["ano"] == ano_inicial
                    and g.get("fixo", False) == fixo
                    and (fixo or g["total_parcelas"] == parcelas)
                ):
                    nova_lista.append(g)
            dados[chave_fatura]["cartao_credito"] = nova_lista

    salvar_dados()
    atualizar_resumo()

def exibir_cartao():
    ttk.Label(scroll_frame_credito, text="Faturas Cartão", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(0, 5))

    gastos_cartao_por_nome = {}
    for c in info["cartao_credito"]:
        nome = c["cartao"]
        if nome not in gastos_cartao_por_nome:
            gastos_cartao_por_nome[nome] = []
        gastos_cartao_por_nome[nome].append(c)

    def toggle_detalhes(frame, label_widget, nome, total):
        if frame.winfo_ismapped():
            frame.pack_forget()
            label_widget.config(text=f"💳 {nome}: {locale.currency(total, grouping=True)} ▶", foreground="blue", font=("Segoe UI", 10, "bold"))
            estado_expansao_cartoes[nome] = False
        else:
            frame.pack(fill="x", padx=20, pady=(0, 10))
            label_widget.config(text=f"💳 {nome}: {locale.currency(total, grouping=True)} ▼", foreground="blue", font=("Segoe UI", 10, "bold"))
            estado_expansao_cartoes[nome] = True

    for nome_cartao in sorted(gastos_cartao_por_nome):
        lista = sorted(gastos_cartao_por_nome[nome_cartao], key=lambda x: (x["ano"], x["mes"], x["dia"]))
        total_cartao = sum(g["valor"] for g in lista)

        container_cartao = ttk.Frame(scroll_frame_credito)
        container_cartao.pack(fill="x", padx=10, pady=(8, 0))

        label = ttk.Label(container_cartao,
            text=f"💳 {nome_cartao}: {locale.currency(total_cartao, grouping=True)} ▶",
            foreground="blue", font=("Segoe UI", 10, "bold"), cursor="hand2")
        label.pack(anchor="w", fill="x")

        frame_detalhes = ttk.Frame(container_cartao)

        for c in lista:
            parcela = f"Parcela {c['parcela_atual']}/{c['total_parcelas']}" if c["total_parcelas"] > 1 else "À vista"
            data = f"{c['dia']:02d}/{c['mes']:02d}/{c['ano']}"
            tipo = c.get("tipo", "Indefinido")
            valor_fmt = locale.currency(c["valor"], grouping=True)

            ttk.Label(frame_detalhes,
                text=f"• {data}: {c['descricao']} - {valor_fmt} ({parcela}) - Tipo: {tipo}",
                font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=1)

        label.bind("<Button-1>", lambda e, f=frame_detalhes, l=label, n=nome_cartao, t=total_cartao: toggle_detalhes(f, l, n, t))

        if estado_expansao_cartoes.get(nome_cartao):
            frame_detalhes.pack(fill="x", padx=20, pady=(0, 10))
            label.config(text=f"💳 {nome_cartao}: {locale.currency(total_cartao, grouping=True)} ▼", foreground="blue", font=("Segoe UI", 10, "bold"))

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
        janela_erro = tk.Toplevel(app)
        janela_erro.title("Aviso")
        janela_erro.geometry("320x120")
        janela_erro.attributes("-topmost", True)
        janela_erro.grab_set()
        janela_erro.resizable(False, False)

        ttk.Label(janela_erro, text="Nenhum cartão cadastrado para excluir.", font=("Segoe UI", 10), wraplength=280).pack(pady=20)
        ttk.Button(janela_erro, text="OK", command=janela_erro.destroy).pack(pady=5)

        # Centraliza a janela de erro sobre a janela principal
        janela_erro.update_idletasks()
        w = janela_erro.winfo_width()
        h = janela_erro.winfo_height()
        x = app.winfo_rootx() + (app.winfo_width() // 2) - (w // 2)
        y = app.winfo_rooty() + (app.winfo_height() // 2) - (h // 2)
        janela_erro.geometry(f"+{x}+{y}")

        janela_anterior.destroy()
        return

    largura = 300
    altura = 150
    x = (janela.winfo_screenwidth() // 2) - (largura // 2)
    y = (janela.winfo_screenheight() // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")
    janela.attributes("-topmost", True)
    janela.grab_set()

    ttk.Label(janela, text="Selecione o cartão para excluir:").pack(pady=5)

    nomes_cartoes = [c['nome'] for c in cartoes]
    combo_cartoes = ttk.Combobox(janela, values=nomes_cartoes, state="readonly")
    combo_cartoes.pack(pady=5)
    combo_cartoes.current(0)

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

    def confirmar_exclusao(cartao_nome, ao_confirmar):
        confirm_janela = tk.Toplevel(janela)
        confirm_janela.title("Confirmar Exclusão")
        confirm_janela.geometry("320x140")
        confirm_janela.grab_set()
        confirm_janela.attributes("-topmost", True)

        ttk.Label(confirm_janela, text=f"Excluir o cartão '{cartao_nome}'?\nGastos anteriores permanecerão.", wraplength=280).pack(pady=15)

        botoes = ttk.Frame(confirm_janela)
        botoes.pack()

        def sim():
            confirm_janela.destroy()
            ao_confirmar()

        def nao():
            confirm_janela.destroy()
            janela.lift()
            janela.focus_force()
            janela.grab_set()
            janela.attributes("-topmost", True)

        ttk.Button(botoes, text="Sim", command=sim).pack(side="left", padx=10)
        ttk.Button(botoes, text="Não", command=nao).pack(side="right", padx=10)

        # Centraliza sobre janela principal
        confirm_janela.update_idletasks()
        w = confirm_janela.winfo_width()
        h = confirm_janela.winfo_height()
        x = janela.winfo_rootx() + (janela.winfo_width() // 2) - (w // 2)
        y = janela.winfo_rooty() + (janela.winfo_height() // 2) - (h // 2)
        confirm_janela.geometry(f"+{x}+{y}")

    def excluir():
        idx = combo_cartoes.current()
        if idx == -1:
            mostrar_erro_toplevel("Selecione um cartão.")
            return

        cartao_excluir = cartoes[idx]

        confirmar_exclusao(cartao_excluir['nome'], lambda: [
            cartoes.remove(cartao_excluir),
            atualizar_resumo(),
            janela.destroy()
        ])

    ttk.Button(janela, text="Excluir", command=excluir).pack(pady=10)

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
    # Mantém a janela sempre em primeiro plano e bloqueia interação com outras janelas
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
        except:
            messagebox.showerror("Erro", "Valor inválido.")
            return
        try:
            vencimento = int(entrada_venc.get())
            if not (1 <= vencimento <= 31):
                raise ValueError
        except:
            messagebox.showerror("Erro", "Dia de vencimento inválido (deve ser 1 a 31).")
            return
        if not descricao:
            messagebox.showerror("Erro", "Descrição não pode ser vazia.")
            return

        nova = {"descricao": descricao, "valor": valor, "vencimento": vencimento, "status": "Aberto"}
        contas_fixas_modelo.append(nova)

        for ano in range(2023, 2031):
            for mes in range(1, 13):
                chave = get_chave(mes, ano)
                if chave in dados:
                    dados[chave]["despesas_fixas"].append(nova.copy())

        atualizar_resumo()
        janela.destroy()

    ttk.Button(janela, text="Salvar", command=salvar).pack(pady=10)
    janela.bind("<Return>", lambda event: salvar())

def excluir_despesa_fixa(indice):
    mes = combo_mes.current() + 1
    ano = int(combo_ano.get())
    chave = get_chave(mes, ano)
    info = inicializar_mes(mes, ano)

    despesa = info["despesas_fixas"][indice]
    descricao_alvo = despesa["descricao"]

    confirmar = messagebox.askyesno("Excluir Despesa Fixa", f"Deseja excluir a despesa '{descricao_alvo}' deste mês e dos próximos?")
    if not confirmar:
        return

    # Remove do mês atual
    del info["despesas_fixas"][indice]

    # Remove dos próximos 11 meses com a mesma descrição
    for i in range(1, 12):
        mes_futuro = mes + i
        ano_futuro = ano
        if mes_futuro > 12:
            mes_futuro -= 12
            ano_futuro += 1

        info_futuro = inicializar_mes(mes_futuro, ano_futuro)

        info_futuro["despesas_fixas"] = [
            d for d in info_futuro["despesas_fixas"] if d["descricao"] != descricao_alvo
        ]

    salvar_dados()
    atualizar_resumo()

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
combo_mes.current(datetime.now().month - 1)
combo_mes.pack(side="left", padx=5)

anos = [str(y) for y in range(2025, 2050)]
combo_ano = ttk.Combobox(frame_selecao, values=anos, state="readonly", width=6)
combo_ano.set(str(datetime.now().year))
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

def criar_area_com_scroll(frame_pai, altura=180):
    canvas = tk.Canvas(frame_pai, height=altura)
    scrollbar = ttk.Scrollbar(frame_pai, orient="vertical", command=canvas.yview)
    scroll_frame = ttk.Frame(canvas)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    return canvas, scrollbar, scroll_frame

canvas_receitas, scrollbar_receitas, scroll_frame_receitas = criar_area_com_scroll(frame_receitas)
canvas_despesas, scrollbar_despesas, scroll_frame_despesas = criar_area_com_scroll(frame_despesas)
canvas_gastos, scrollbar_gastos, scroll_frame_gastos = criar_area_com_scroll(frame_gastos)
canvas_credito, scrollbar_credito, scroll_frame_credito = criar_area_com_scroll(frame_credito)

# Inicializa dados para o mês atual
atualizar_resumo()
app.mainloop()