import sys, os, time, shutil

if len(sys.argv) < 3:
    sys.exit(1)

app_atual = sys.argv[1]   # caminho do app principal
novo_exe = sys.argv[2]    # caminho do novo executável baixado

print(f"Atualizando: {app_atual} <- {novo_exe}")

# Aguarda o arquivo antigo ser liberado (app fechado)
while True:
    try:
        with open(app_atual, "rb"):
            break
    except Exception:
        time.sleep(1)

# Cria backup
backup = app_atual + ".bak"
try:
    if os.path.exists(backup):
        os.remove(backup)
    if os.path.exists(app_atual):
        shutil.move(app_atual, backup)
        print("Backup criado.")
except Exception as e:
    print(f"[ERRO] Não foi possível criar backup: {e}")
    sys.exit(1)

# Substitui pelo novo exe
try:
    shutil.move(novo_exe, app_atual)
    print("Novo executável instalado com sucesso.")
except Exception as e:
    print(f"[ERRO] Falha ao mover novo exe: {e}")
    # restaura backup se der erro
    if os.path.exists(backup):
        shutil.move(backup, app_atual)
    sys.exit(1)

# Remove backup só se tudo deu certo
try:
    if os.path.exists(backup):
        os.remove(backup)
except Exception as e:
    print(f"[AVISO] Não foi possível remover backup: {e}")

# Limpa temporários
try:
    temp_dir = os.path.dirname(novo_exe)
    if os.path.exists(temp_dir):
        os.rmdir(temp_dir)
except Exception as e:
    print(f"[AVISO] Não foi possível limpar pasta temporária: {e}")

print("✔ Atualização concluída! Abra o aplicativo manualmente.")
