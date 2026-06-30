import bcrypt
import getpass

password = getpass.getpass("Entre le mot de passe à hasher : ")
confirm = getpass.getpass("Confirme le mot de passe : ")

if password != confirm:
    exit(1)

hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

print(f"DASHBOARD_PASSWORD_HASH={hashed.decode()}")