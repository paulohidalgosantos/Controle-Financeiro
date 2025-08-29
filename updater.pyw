import sys, os, time, shutil

if len(sys.argv) < 3:
    sys.exit(1)

app_antigo = sys.argv[1]  # exe atual
novo_exe = sys.argv[2]    # exe baixado

print(f"Atualizando {app_antigo}...")

# Espera o app antigo ser liberado (não estar em uso)
while True:
    try:
        with open(app_antigo, "rb"):
            break
    except Exception:
        time.sleep(1)

backup = app_antigo + ".bak"

try:
    # Cria backup
    if os.path.exists(backup):
        os.remove(backup)
    if os.path.exists(app_antigo):
        shutil.move(app_antigo, backup)

    # Substitui pelo novo
    shutil.move(novo_exe, app_antigo)
    print("✔ Atualização concluída!")

    # Remove backup (opcional: pode manter se quiser segurança extra)
    if os.path.exists(backup):
        os.remove(backup)

except Exception as e:
    print(f"[ERRO] {e}")
    # Se der erro, restaura backup
    if os.path.exists(backup):
        shutil.move(backup, app_antigo)
