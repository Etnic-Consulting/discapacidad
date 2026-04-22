"""Seed initial users for SMT-ONIC auth.

Run inside the api container:
    docker exec -it smt-onic-api python -m scripts.seed_auth
"""
import hashlib
import secrets
import sys

from sqlalchemy import create_engine, text

DATABASE_URL_SYNC = "postgresql://smt_admin:smt_onic_2026@db:5432/smt_onic"


def hash_password(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return digest, salt


USERS = [
    {"username": "admin", "password": "admin123", "nombre": "Administrador SMT", "email": "admin@onic.org.co", "rol": "admin"},
    {"username": "dinamizador1", "password": "smt2026", "nombre": "Dinamizador Nacional", "email": "dinamizador1@onic.org.co", "rol": "dinamizador"},
    {"username": "wilson", "password": "wilson2026", "nombre": "Wilson Herrera", "email": "poblacion@onic.org.co", "rol": "coordinador"},
]


def main() -> int:
    engine = create_engine(DATABASE_URL_SYNC)
    with engine.begin() as conn:
        for u in USERS:
            existing = conn.execute(text("SELECT id FROM smt.usuarios WHERE username = :u"), {"u": u["username"]}).first()
            if existing is not None:
                print(f"[skip] ya existe: {u['username']}")
                continue
            h, salt = hash_password(u["password"])
            conn.execute(text("""
                INSERT INTO smt.usuarios (username, password_hash, salt, nombre, email, rol, activo)
                VALUES (:username, :h, :salt, :nombre, :email, :rol, TRUE)
            """), {**u, "h": h, "salt": salt})
            print(f"[ok] creado: {u['username']} / pass={u['password']} (rol={u['rol']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
