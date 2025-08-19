# oracle-shell

Shell interattiva per Oracle Database, pensata per ispezioni rapide e l’esecuzione di query da riga di comando su Windows.
Progetto per il portfolio di **Antonio Trento** — [antoniotrento.net](https://antoniotrento.net)

---

## Caratteristiche

* REPL SQL con esecuzione a terminazione `;`
* Comandi meta per esplorare lo schema (`\tables`, `\schemas`, `\d`, `\find`)
* Esecuzione batch da file `.sql` (`--file`)
* Output tabellare leggibile con limite righe configurabile (`--limit`)
* Ricerca veloce di colonne tramite pattern (es. per trovare campi **IBAN**)
* Configurazione tramite `.env` (niente credenziali in chiaro nel codice)

---

## Requisiti

* Windows (testato su Windows 8/10/11)
* Python **3.7+** (consigliato 3.10+)
* Oracle Instant Client (versione compatibile con l’architettura Python, es. 64-bit)
* Libreria Python: `oracledb`

---

## Installazione

```bat
:: nella cartella del progetto
py -m venv venv
venv\Scripts\activate.bat
pip install oracledb
```

---

## Configurazione (.env)

Crea un file **`.env`** accanto a `oracle-shell.py` con valori **placeholder** (non inserire dati sensibili nel repo):

```env
# Oracle client
ORACLE_IC_PATH=C:\Oracle\instantclient_<VERSIONE>

# Credenziali
ORACLE_USER=<USERNAME>
ORACLE_PASSWORD=<PASSWORD>

# Endpoint
ORACLE_HOST=<DB_HOST>
ORACLE_PORT=1521
ORACLE_SERVICE=<SERVICE_NAME>

# (opzionale) override DSN completo (se presente, sovrascrive host/port/service)
# ORACLE_DSN=<HOST:PORT/SERVICE>
```

> Suggerito: aggiungi `.env` al `.gitignore`.

---

## Avvio

```bat
venv\Scripts\activate.bat
chcp 65001
python oracle-shell.py
```

Esecuzione da file:

```bat
python oracle-shell.py --file C:\percorso\script.sql
```

Opzioni utili:

* `--limit N` → limita le righe mostrate (default 200; usa 0 per tutte)
* `--file PATH` → esegue istruzioni separate da `;` lette dal file

---

## Uso del REPL

* Termina ogni istruzione SQL con **`;`** per eseguirla.
* Le **DML** (`INSERT`, `UPDATE`, `DELETE`, `MERGE`) **non** fanno commit automatico:

  * `COMMIT;` salva le modifiche
  * `ROLLBACK;` annulla le modifiche
* Le **DDL** (`CREATE`, `ALTER`, `DROP`, `TRUNCATE`) fanno commit **implicito**.

### Comandi speciali (non SQL)

```
\help                     -> aiuto
\q                        -> esci
\schemas                  -> elenca gli schemi
\tables [pattern]         -> elenca tabelle (LIKE opzionale, es. %DEV%)
\d NOME_TABELLA           -> descrive colonne (ALL_TAB_COLUMNS)
\d OWNER.NOME_TABELLA     -> descrive colonne specificando lo schema
\find %TESTO%             -> cerca colonne per nome (ALL_TAB_COLUMNS)
```

---

## Esempi rapidi

```sql
-- Chi sono
SELECT USER FROM DUAL;

-- Prime 50 righe
SELECT * FROM <SCHEMA>.<TABELLA> FETCH FIRST 50 ROWS ONLY;

-- Conta
SELECT COUNT(*) FROM <SCHEMA>.<TABELLA>;

-- Describe (dal REPL)
\d <SCHEMA>.<TABELLA>

-- Cerca colonne con "IBAN"
\find %IBAN%

-- Intervallo date
SELECT *
FROM <SCHEMA>.<TABELLA>
WHERE <COLONNA_DATA> BETWEEN DATE '2025-01-01' AND DATE '2025-12-31';

-- Aggregazione
SELECT <COL_GRUPPO>, COUNT(*) AS QUANTI
FROM <SCHEMA>.<TABELLA>
GROUP BY <COL_GRUPPO>
ORDER BY QUANTI DESC;

-- DML con commit
UPDATE <SCHEMA>.<TABELLA> SET <COLONNA>='VAL' WHERE <FILTRO>;
COMMIT;
```

---

## Ricerca IBAN su tutto il DB (strategia generica)

1. Inserisci a frontend un **IBAN fittizio** (anche formattato con spazi/trattini).
2. Cerca dove finisce nel DB **normalizzando** (maiuscolo, senza spazi e trattini).

Generatore di query (produce `SELECT ... COUNT(*) AS HITS` su tutte le colonne che contengono “IBAN”):

```sql
WITH p AS (
  SELECT REPLACE(REPLACE(UPPER('<IBAN_FRONTEND>'), ' ', ''), '-', '') AS TARGET FROM DUAL
)
SELECT
  'SELECT '''||c.OWNER||''' AS OWNER, '''||c.TABLE_NAME||''' AS TABLE_NAME, '''||c.COLUMN_NAME||''' AS COLUMN_NAME, COUNT(*) AS HITS '||
  'FROM '||c.OWNER||'.'||c.TABLE_NAME||
  ' WHERE REPLACE(REPLACE(UPPER('||c.COLUMN_NAME||'), '' '',''''), ''-'','''') = (SELECT TARGET FROM p);'
AS SQL_SNIPPET
FROM ALL_TAB_COLUMNS c
WHERE UPPER(c.COLUMN_NAME) LIKE '%IBAN%'
ORDER BY c.OWNER, c.TABLE_NAME, c.COLUMN_ID;
```

* Copia l’output (tante `SELECT ... HITS`) e incollalo nel REPL.
* Le righe con `HITS > 0` indicano le colonne candidate. Verifica poi i record:

```sql
SELECT *
FROM <OWNER>.<TABELLA>
WHERE REPLACE(REPLACE(UPPER(<COLONNA_IBAN>), ' ', ''), '-', '') = 'IT60X0542811101000000123456';
```

> Opzionale: si possono aggiungere al REPL comandi custom come `\ibanfind <IBAN>` (match esatto normalizzato) e `\grepiban <pattern>` (LIKE normalizzato).

---

## Troubleshooting

* **SyntaxError Non-UTF-8 / PEP 263**
  Salva `oracle-shell.py` in UTF-8 e aggiungi in testa:

  ```python
  # -*- coding: utf-8 -*-
  ```

  In Notepad++: *Encoding → Convert to UTF-8 (without BOM)*.

* **Caratteri strani nel prompt**
  Esegui `chcp 65001` prima di lanciare Python.

* **Impossibile caricare l’Instant Client**
  Verifica `ORACLE_IC_PATH`, coerenza 32/64-bit e runtime VC++ richiesti.

* **ORA-12154 / ORA-12514**
  Controlla host, porta, service name o usa `ORACLE_DSN=<HOST:PORT/SERVICE>`.

---

## Sicurezza

* Non committare il file **`.env`**.
* Ruota periodicamente le password.
* Evita `SELECT *` su dati sensibili in ambienti condivisi.
* Esegui le modifiche su ambienti di **test** quando possibile.

---

## Limitazioni

* Il parser per `--file` separa gli statement sul `;` e **non** gestisce blocchi PL/SQL complessi; per quelli usa il REPL.
* L’output è pensato per il terminale; per export CSV/Excel usa script dedicati.

---

## Struttura del progetto

```
oracle-shell.py    # script principale (REPL + comandi meta)
.env               # variabili di connessione (non committare)
README.md          # documentazione del progetto
```

---

## Licenza

MIT (o altra a tua scelta). Inserisci il file `LICENSE` nel repository.

---

**Autore:** Antonio Trento — [antoniotrento.net](https://antoniotrento.net)
