# C:\Users\gianluca.pelliccioli\Documents\p7_neta_ws\esercizio
# macchina ponte 10.249.112.88
# attivazione venv: venv\Scripts\activate.bat

import oracledb
import argparse
import os
import sys
import re
from typing import List, Optional

# --- Lettore .env minimalista (funziona anche senza python-dotenv) ---
def load_env_file(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                # non sovrascrivere se già definita a livello di ambiente
                if k and (k not in os.environ):
                    os.environ[k] = v
    except Exception as e:
        print("Errore nel parsing del file .env:", e)
        # non usciamo: continuiamo con le variabili eventualmente già in ambiente

def env_or_fail(key: str, default: str = None, required: bool = False) -> str:
    val = os.getenv(key, default)
    if required and (val is None or val == ""):
        print(f"Variabile d'ambiente mancante: {key}")
        sys.exit(1)
    return val

# Carica .env dalla directory corrente
load_env_file(".env")

# --- CONFIGURAZIONE (da .env) ---
INSTANT_CLIENT_PATH = env_or_fail("ORACLE_IC_PATH", r"C:\Oracle\instantclient_11_2")
USERNAME = env_or_fail("ORACLE_USER", required=True)
PASSWORD = env_or_fail("ORACLE_PASSWORD", required=True)
HOST     = env_or_fail("ORACLE_HOST", "10.146.213.109")
PORT     = int(env_or_fail("ORACLE_PORT", "1521"))
SERVICE_NAME = env_or_fail("ORACLE_SERVICE", "METQUANDB1")

# Consenti override completo del DSN via ORACLE_DSN, altrimenti costruiscilo
DSN = env_or_fail("ORACLE_DSN", f"{HOST}:{PORT}/{SERVICE_NAME}")

BANNER = """\
Oracle SQL REPL (thick mode). Comandi speciali:
  \\q                      esci
  \\help                   aiuto
  \\tables [pattern]       elenca tabelle (ALL_TABLES), opz. filtro LIKE
  \\schemas                elenca schemi disponibili
  \\d <owner.table|table>  descrivi colonne tabella (ALL_TAB_COLUMNS)
  \\find <pattern>         cerca colonne per nome (ALL_TAB_COLUMNS)
Note: termina le query con ';'. Usa COMMIT; o ROLLBACK; per DML.
"""

def init_client():
    try:
        oracledb.init_oracle_client(lib_dir=INSTANT_CLIENT_PATH)
    except Exception as e:
        print("❌ Errore inizializzazione client Oracle:", e)
        sys.exit(1)

def connect():
    try:
        conn = oracledb.connect(user=USERNAME, password=PASSWORD, dsn=DSN)
        print("✅ Connessione riuscita (thick mode)")
        return conn
    except Exception as e:
        print("❌ Errore di connessione:", e)
        sys.exit(1)

def print_table(headers: List[str], rows: List[tuple], limit: int = 200):
    # Calcola larghezze colonna
    widths = [len(h or "") for h in headers]
    shown = 0
    for r in rows:
        for i, v in enumerate(r):
            s = "" if v is None else str(v)
            if len(s) > widths[i]:
                widths[i] = len(s)
    # Stampa header
    line = " | ".join((h or "").ljust(widths[i]) for i, h in enumerate(headers))
    sep  = "-+-".join("-" * widths[i] for i in range(len(headers)))
    print(line)
    print(sep)
    # Stampa righe (limitate)
    for r in rows:
        if limit and shown >= limit:
            break
        print(" | ".join(("" if v is None else str(v)).ljust(widths[i]) for i, v in enumerate(r)))
        shown += 1
    if limit and len(rows) > limit:
        print(f"... ({len(rows)-limit} righe non mostrate, usa --limit 0 per tutte)")

def exec_sql(cur, conn, sql: str, limit: int):
    sql_stripped = sql.strip().rstrip(";").strip()
    if not sql_stripped:
        return
    upper = sql_stripped.upper()

    # Gestione COMMIT/ROLLBACK espliciti
    if upper == "COMMIT":
        conn.commit()
        print("✔ COMMIT eseguito.")
        return
    if upper == "ROLLBACK":
        conn.rollback()
        print("↩ ROLLBACK eseguito.")
        return

    cur.execute(sql_stripped)

    if cur.description:  # SELECT o simili con result set
        rows = cur.fetchall()
        headers = [d[0] for d in cur.description]
        print_table(headers, rows, limit=limit)
        print(f"\n({len(rows)} righe)")
    else:
        affected = cur.rowcount
        print(f"🛠 Eseguito. Righe interessate: {affected}.")
        print("Suggerimento: usa COMMIT; per confermare, ROLLBACK; per annullare.")

def meta_tables(cur, pattern: Optional[str], limit:int):
    if pattern:
        cur.execute("""
            SELECT OWNER, TABLE_NAME
            FROM ALL_TABLES
            WHERE TABLE_NAME LIKE :p
            ORDER BY OWNER, TABLE_NAME
        """, [pattern.upper()])
    else:
        cur.execute("""
            SELECT OWNER, TABLE_NAME
            FROM ALL_TABLES
            ORDER BY OWNER, TABLE_NAME
        """)
    rows = cur.fetchall()
    print_table(["OWNER","TABLE_NAME"], rows, limit=limit)
    print(f"\n({len(rows)} tabelle)")

def meta_schemas(cur):
    cur.execute("""
        SELECT USERNAME AS OWNER
        FROM ALL_USERS
        ORDER BY USERNAME
    """)
    rows = cur.fetchall()
    print_table(["OWNER"], rows, limit=0)
    print(f"\n({len(rows)} schemi)")

def meta_describe(cur, target: str):
    # target può essere "owner.table" o solo "table"
    if "." in target:
        owner, table = target.split(".", 1)
    else:
        owner, table = "%", target
    cur.execute("""
        SELECT OWNER,
               TABLE_NAME,
               COLUMN_ID,
               COLUMN_NAME,
               DATA_TYPE,
               DATA_LENGTH,
               DATA_PRECISION,
               DATA_SCALE,
               NULLABLE
        FROM ALL_TAB_COLUMNS
        WHERE TABLE_NAME = UPPER(:t)
          AND OWNER LIKE NVL(:o, OWNER)
        ORDER BY OWNER, TABLE_NAME, COLUMN_ID
    """, [table.upper(), None if owner == "%" else owner.upper()])
    rows = cur.fetchall()
    if not rows:
        print("Nessuna colonna trovata (controlla OWNER/TABLE).")
        return
    print_table(
        ["OWNER","TABLE","POS","COLUMN","TYPE","LEN","PREC","SCALE","NULL?"],
        rows, limit=0
    )
    print(f"\n({len(rows)} colonne)")

def meta_find(cur, pattern: str, limit:int):
    cur.execute("""
        SELECT c.OWNER, c.TABLE_NAME, c.COLUMN_NAME, c.DATA_TYPE
        FROM ALL_TAB_COLUMNS c
        WHERE c.COLUMN_NAME LIKE :p
        ORDER BY c.OWNER, c.TABLE_NAME, c.COLUMN_ID
    """, [pattern.upper()])
    rows = cur.fetchall()
    print_table(["OWNER","TABLE","COLUMN","TYPE"], rows, limit=limit)
    print(f"\n({len(rows)} corrispondenze)")

def handle_meta(cur, conn, line: str, limit:int) -> bool:
    # Restituisce True se era un comando meta
    parts = line.strip().split()
    cmd = parts[0]
    args = parts[1:]

    if cmd in ("\\q", "\\quit", "\\exit"):
        print("Bye.")
        sys.exit(0)
    if cmd in ("\\help", "\\h"):
        print(BANNER)
        return True
    if cmd == "\\tables":
        meta_tables(cur, args[0] if args else None, limit)
        return True
    if cmd == "\\schemas":
        meta_schemas(cur)
        return True
    if cmd in ("\\d", "\\desc", "\\describe"):
        if not args:
            print("Uso: \\d <table> oppure \\d <owner.table>")
            return True
        meta_describe(cur, args[0])
        return True
    if cmd in ("\\find", "\\search"):
        if not args:
            print("Uso: \\find <pattern>   (usa % come wildcard, es. %CODICE%)")
            return True
        meta_find(cur, args[0], limit)
        return True
    return False

def read_statements_from_file(path:str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    # Split ingenuo su ';' non dentro stringhe -> semplice fallback: spezza su ';' fine riga
    # Per semplicità: accettiamo che i PL/SQL complessi vadano eseguiti da REPL riga per riga.
    stmts = []
    buff = []
    in_single = False
    in_double = False
    for ch in text:
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        if ch == ";" and not in_single and not in_double:
            stmts.append("".join(buff).strip())
            buff = []
        else:
            buff.append(ch)
    if buff:
        tail = "".join(buff).strip()
        if tail:
            stmts.append(tail)
    return [s for s in stmts if s.strip()]

def repl(conn, limit:int):
    print(BANNER)
    cur = conn.cursor()
    buffer: List[str] = []
    try:
        while True:
            prompt = "SQL> " if not buffer else " ... "
            line = input(prompt)
            if not buffer and line.strip().startswith("\\"):
                if handle_meta(cur, conn, line, limit):
                    continue
            # Accumula finché troviamo ';' non tra apici
            buffer.append(line)
            joined = "\n".join(buffer)
            # Controllo quote semplice
            open_single = joined.count("'") % 2 == 1
            open_double = joined.count('"') % 2 == 1
            if not open_single and not open_double and re.search(r";\s*$", joined):
                sql = re.sub(r";\s*$", "", joined, flags=re.S)
                try:
                    exec_sql(cur, conn, sql + ";", limit)
                except oracledb.Error as e:
                    print("❌ Errore Oracle:", e)
                buffer = []
    except (KeyboardInterrupt, EOFError):
        print("\n↩ Interrotto.")
    finally:
        cur.close()

def run_file(conn, path:str, limit:int):
    cur = conn.cursor()
    stmts = read_statements_from_file(path)
    for i, s in enumerate(stmts, 1):
        print(f"\n-- [{i}/{len(stmts)}] Eseguo:")
        print(s.strip() + ";")
        try:
            exec_sql(cur, conn, s + ";", limit)
        except oracledb.Error as e:
            print("❌ Errore Oracle:", e)
            # continua col successivo
    cur.close()

def main():
    parser = argparse.ArgumentParser(description="CLI per eseguire query Oracle in sequenza.")
    parser.add_argument("--file", "-f", help="Esegui tutte le query da file (separate da ';').")
    parser.add_argument("--limit", "-l", type=int, default=200, help="Limite righe in output (0 = tutte).")
    args = parser.parse_args()

    init_client()
    conn = connect()

    try:
        if args.file:
            run_file(conn, args.file, args.limit if args.limit >= 0 else 0)
        else:
            repl(conn, args.limit if args.limit >= 0 else 0)
    finally:
        try:
            conn.close()
        except:
            pass

if __name__ == "__main__":
    main()
