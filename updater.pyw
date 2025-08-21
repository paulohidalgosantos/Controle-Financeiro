import sys, os, time, shutil, subprocess

# Verifica argumentos
if len(sys.argv) < 3:
    sys.exit(1)

app_atual = sys.argv[1]  # caminho do app principal
novo_exe = sys.argv[2]   # caminho do novo executável baixado

# Espera o app fechar
while True:
    tasklist = os.popen("tasklist").read()
    if os.path.basename(app_atual) not in tasklist:
        break
    time.sleep(1)

# Faz backup do app antigo
backup = app_atual + ".bak"
if os.path.exists(app_atual):
    shutil.move(app_atual, backup)

# Copia o novo executável
shutil.copy(novo_exe, app_atual)

# Inicia app atualizado sem abrir console
subprocess.Popen([app_atual], creationflags=subprocess.CREATE_NO_WINDOW)

# Limpa arquivos temporários
try:
    os.remove(novo_exe)
    os.remove(backup)
except:
    pass
