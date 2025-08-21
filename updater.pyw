import sys, os, time, shutil

# Verifica se recebeu os argumentos corretos
if len(sys.argv) < 3:
    sys.exit(1)

app_atual = sys.argv[1]   # caminho do app principal
novo_exe = sys.argv[2]    # caminho do novo executável baixado

# Espera o app principal fechar
while True:
    tasklist = os.popen("tasklist").read()
    if os.path.basename(app_atual) not in tasklist:
        break
    time.sleep(1)

# Cria backup do exe antigo
backup = app_atual + ".bak"
if os.path.exists(app_atual):
    try:
        shutil.move(app_atual, backup)
    except Exception as e:
        print(f"Erro ao criar backup: {e}")

# Copia o novo exe para a pasta final
try:
    shutil.copy(novo_exe, app_atual)
except Exception as e:
    print(f"Erro ao copiar novo exe: {e}")

# Limpa arquivos temporários
try:
    if os.path.exists(novo_exe):
        os.remove(novo_exe)
    if os.path.exists(backup):
        os.remove(backup)
    temp_dir = os.path.dirname(novo_exe)
    if os.path.exists(temp_dir):
        os.rmdir(temp_dir)
except Exception:
    pass

# Atualização finalizada
print("Atualização concluída. Abra o aplicativo manualmente.")
