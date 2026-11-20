"""Génère sept codes confidentiels et les requêtes d'initialisation Supabase."""
from pathlib import Path
import secrets

BASE = Path(__file__).parent
NAMES = [f"Lutin {i}" for i in range(1, 8)]
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

def main():
    sql = BASE / "initialisation_privee.sql"
    codes = BASE / "codes_lutins.txt"
    if sql.exists() or codes.exists():
        raise SystemExit("Fichiers privés déjà présents, aucun écrasement.")
    rows, invitations = [], []
    for name in NAMES:
        code = "".join(secrets.choice(ALPHABET) for _ in range(20))
        rows.append(f"('{name}', encode(extensions.digest('{code}', 'sha256'), 'hex'))")
        invitations.append(f"{name} : {code}")
    sql.write_text("insert into public.members(name, code_hash) values\n" + ",\n".join(rows) + ";\n", encoding="utf-8")
    codes.write_text("CODES CONFIDENTIELS — à transmettre séparément\n\n" + "\n".join(invitations) + "\n", encoding="utf-8")
    print("Créé : initialisation_privee.sql et codes_lutins.txt (NON publiés).")

if __name__ == "__main__":
    main()
