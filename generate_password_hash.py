import bcrypt
import getpass

password = getpass.getpass("Enter password : ")
confirm = getpass.getpass("Confirm password : ")

if password != confirm:
    exit(1)

hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

print(f"DASHBOARD_PASSWORD_HASH={hashed.decode()}")