# Oracle REPL — Cheat Sheet (per `oracle-shell.py`)

Guida pratica in **Markdown** da incollare in un file `.md`.

---

## Avvio

```bat
# Attiva venv (Windows)
venv\Scripts\activate.bat

# Avvia REPL
python oracle-shell.py

# Esegui query da file
python oracle-shell.py --file C:\percorso\script.sql
```

---

## Note operative

* Termina **ogni istruzione** con `;` per eseguirla.
* Le **DML** (`INSERT` / `UPDATE` / `DELETE` / `MERGE`) **non** si salvano da sole: usa `COMMIT;` per confermare o `ROLLBACK;` per annullare.
* Le query possono essere **su più righe**: l’esecuzione avviene al `;` finale.

> ℹ️ Le **DDL** (`CREATE`, `ALTER`, `DROP`, `TRUNCATE`) in Oracle eseguono **commit implicito** prima e dopo.

---

## Comandi speciali del REPL (non SQL)

```
\help                     → mostra aiuto
\q                        → esci
\schemas                  → elenca gli schemi
\tables                   → elenca tutte le tabelle visibili
\tables %DEV%             → filtra le tabelle con LIKE (es. contiene "DEV")
\d NOME_TABELLA           → descrive colonne (cerca su tutti gli owner)
\d OWNER.NOME_TABELLA     → descrive colonne per tabella specifica
\find %CODICE%            → trova colonne che contengono "CODICE" nel nome
```

---

## Ispezione rapida dello schema (SQL)

```sql
-- Chi sono?
SELECT USER FROM DUAL;

-- Tutte le tabelle di uno schema (es. SIUDEVICE)
SELECT TABLE_NAME
FROM ALL_TABLES
WHERE OWNER = 'SIUDEVICE'
ORDER BY TABLE_NAME;

-- Prime 50 righe di una tabella
SELECT *
FROM SIUDEVICE.DEV_STRUMENTI
FETCH FIRST 50 ROWS ONLY;

-- Conta righe in tabella
SELECT COUNT(*) AS CNT
FROM SIUDEVICE.DEV_STRUMENTI;

-- Elenco colonne con tipo e nullabilità
SELECT COLUMN_ID, COLUMN_NAME, DATA_TYPE, DATA_LENGTH, DATA_PRECISION, DATA_SCALE, NULLABLE
FROM ALL_TAB_COLUMNS
WHERE OWNER = 'SIUDEVICE'
  AND TABLE_NAME = 'DEV_STRUMENTI'
ORDER BY COLUMN_ID;

-- Cerca colonne per nome (case-insensitive)
SELECT OWNER, TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM ALL_TAB_COLUMNS
WHERE UPPER(COLUMN_NAME) LIKE UPPER('%CODICE%')
ORDER BY OWNER, TABLE_NAME, COLUMN_NAME;

-- Colonne di tipo data/timestamp
SELECT OWNER, TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM ALL_TAB_COLUMNS
WHERE DATA_TYPE IN ('DATE','TIMESTAMP(6)','TIMESTAMP')
ORDER BY OWNER, TABLE_NAME, COLUMN_NAME;

-- Chiavi primarie della tabella
SELECT acc.COLUMN_NAME
FROM ALL_CONSTRAINTS ac
JOIN ALL_CONS_COLUMNS acc
  ON ac.OWNER = acc.OWNER AND ac.CONSTRAINT_NAME = acc.CONSTRAINT_NAME
WHERE ac.OWNER='SIUDEVICE'
  AND ac.TABLE_NAME='DEV_STRUMENTI'
  AND ac.CONSTRAINT_TYPE='P'
ORDER BY acc.POSITION;

-- Vincoli di tipo FOREIGN KEY della tabella
SELECT ac.CONSTRAINT_NAME, acc.COLUMN_NAME, ac_r.TABLE_NAME AS REF_TABLE
FROM ALL_CONSTRAINTS ac
JOIN ALL_CONS_COLUMNS acc
  ON ac.OWNER=acc.OWNER AND ac.CONSTRAINT_NAME=acc.CONSTRAINT_NAME
LEFT JOIN ALL_CONSTRAINTS ac_r
  ON ac.R_OWNER=ac_r.OWNER AND ac.R_CONSTRAINT_NAME=ac_r.CONSTRAINT_NAME
WHERE ac.OWNER='SIUDEVICE'
  AND ac.TABLE_NAME='DEV_STRUMENTI'
  AND ac.CONSTRAINT_TYPE='R'
ORDER BY ac.CONSTRAINT_NAME, acc.POSITION;

-- Indici definiti sulla tabella
SELECT INDEX_NAME, UNIQUENESS
FROM ALL_INDEXES
WHERE OWNER='SIUDEVICE'
  AND TABLE_NAME='DEV_STRUMENTI'
ORDER BY INDEX_NAME;

-- Colonne degli indici della tabella
SELECT ic.INDEX_NAME, ic.COLUMN_POSITION, ic.COLUMN_NAME
FROM ALL_IND_COLUMNS ic
WHERE ic.TABLE_OWNER='SIUDEVICE'
  AND ic.TABLE_NAME='DEV_STRUMENTI'
ORDER BY ic.INDEX_NAME, ic.COLUMN_POSITION;

-- Oggetti (viste, procedure, ecc.) che dipendono da una tabella
SELECT OWNER, NAME, TYPE
FROM ALL_DEPENDENCIES
WHERE REFERENCED_OWNER='SIUDEVICE'
  AND REFERENCED_NAME='DEV_STRUMENTI'
ORDER BY TYPE, OWNER, NAME;
```

---

## Query dati — esempi tipici

```sql
-- Selezione colonne specifiche con filtro
SELECT STRU_MATRICOLA, STRU_DESCRIZIONE
FROM SIUDEVICE.DEV_STRUMENTI
WHERE STRU_MATRICOLA IS NOT NULL;

-- Ricerca testuale case-insensitive
SELECT *
FROM SIUDEVICE.DEV_STRUMENTI
WHERE UPPER(STRU_DESCRIZIONE) LIKE UPPER('%CONTATORE%')
FETCH FIRST 100 ROWS ONLY;

-- Valori distinti di una colonna
SELECT DISTINCT STRU_TIPO
FROM SIUDEVICE.DEV_STRUMENTI
ORDER BY STRU_TIPO;

-- Ordinamento multiplo
SELECT STRU_TIPO, STRU_MATRICOLA, STRU_DESCRIZIONE
FROM SIUDEVICE.DEV_STRUMENTI
ORDER BY STRU_TIPO, STRU_MATRICOLA;

-- Gestione NULL (NVL) e COALESCE
SELECT NVL(STRU_DESCRIZIONE, '— nessuna descrizione —') AS DESCR
FROM SIUDEVICE.DEV_STRUMENTI
FETCH FIRST 20 ROWS ONLY;

-- Filtro su date — ultimi 7 giorni (colonna DATA_RIF di tipo DATE)
SELECT *
FROM SIUDEVICE.DEV_STRUMENTI
WHERE DATA_RIF >= TRUNC(SYSDATE) - 7
ORDER BY DATA_RIF DESC;

-- Filtro per intervallo di date (inclusivo)
SELECT *
FROM SIUDEVICE.DEV_STRUMENTI
WHERE DATA_RIF BETWEEN DATE '2025-01-01' AND DATE '2025-12-31';

-- Formattazione date e numeri
SELECT TO_CHAR(DATA_RIF, 'YYYY-MM-DD HH24:MI') AS DATA_FMT,
       TO_CHAR(VALORE,   '999G999D99')          AS VAL_FMT
FROM SIUDEVICE.DEV_STRUMENTI
FETCH FIRST 20 ROWS ONLY;

-- Aggregazioni e raggruppamenti
SELECT STRU_TIPO, COUNT(*) AS QUANTI
FROM SIUDEVICE.DEV_STRUMENTI
GROUP BY STRU_TIPO
ORDER BY QUANTI DESC;

-- Join tra due tabelle (esempio generico)
SELECT s.STRU_MATRICOLA, s.STRU_TIPO, d.DESC_ESTESA
FROM SIUDEVICE.DEV_STRUMENTI s
JOIN SIUDEVICE.DEV_TIPI d
  ON d.TIPO = s.STRU_TIPO
FETCH FIRST 100 ROWS ONLY;

-- Paginazione (OFFSET/FETCH)
SELECT STRU_MATRICOLA, STRU_TIPO
FROM SIUDEVICE.DEV_STRUMENTI
ORDER BY STRU_MATRICOLA
OFFSET 0 ROWS FETCH NEXT 100 ROWS ONLY;
```

---

## DML — modifiche ai dati

*(ricorda: `COMMIT;` o `ROLLBACK;`)*

```sql
-- UPDATE con verifica preliminare
SELECT COUNT(*) AS CANDIDATI
FROM SIUDEVICE.DEV_STRUMENTI
WHERE STRU_TIPO = 'X';

UPDATE SIUDEVICE.DEV_STRUMENTI
SET STRU_TIPO = 'Y'
WHERE STRU_TIPO = 'X';

COMMIT;   -- oppure ROLLBACK;

-- DELETE sicura (prima conta, poi elimina)
SELECT COUNT(*) AS DA_ELIMINARE
FROM SIUDEVICE.DEV_STRUMENTI
WHERE STRU_MATRICOLA LIKE 'TMP_%';

DELETE FROM SIUDEVICE.DEV_STRUMENTI
WHERE STRU_MATRICOLA LIKE 'TMP_%';
COMMIT;   -- oppure ROLLBACK;

-- INSERT di esempio
INSERT INTO SIUDEVICE.DEV_STRUMENTI (ID, STRU_MATRICOLA, STRU_TIPO, STRU_DESCRIZIONE)
VALUES (123456, 'TEST123', 'DEMO', 'Record di test');
COMMIT;   -- oppure ROLLBACK;

-- MERGE (upsert) di esempio
MERGE INTO SIUDEVICE.DEV_STRUMENTI t
USING (SELECT 'TEST123' AS MAT, 'DEMO' AS TIPO FROM DUAL) s
ON (t.STRU_MATRICOLA = s.MAT)
WHEN MATCHED THEN
  UPDATE SET t.STRU_TIPO = s.TIPO
WHEN NOT MATCHED THEN
  INSERT (ID, STRU_MATRICOLA, STRU_TIPO) VALUES (123456, s.MAT, s.TIPO);
COMMIT;
```

---

## DDL — operazioni di schema

*(attenzione: commit implicito)*

```sql
-- Crea tabella di prova
CREATE TABLE SIUDEVICE.TB_DEMO (
  ID         NUMBER PRIMARY KEY,
  NOME       VARCHAR2(100),
  CREATO_IL  DATE DEFAULT SYSDATE
);

-- Aggiungi indice
CREATE INDEX SIUDEVICE.IX_TB_DEMO_NOME
  ON SIUDEVICE.TB_DEMO (NOME);

-- Elimina tabella di prova (DROP è definitivo)
DROP TABLE SIUDEVICE.TB_DEMO PURGE;
```

---

## Performance / Explain Plan

```sql
-- Genera piano di esecuzione
EXPLAIN PLAN FOR
SELECT * FROM SIUDEVICE.DEV_STRUMENTI
WHERE STRU_MATRICOLA LIKE '19E4E5%';

-- Visualizza piano (richiede DBMS_XPLAN)
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);
```

---

## Utili vari

```sql
-- Estrai solo l'anno/mese da una data
SELECT EXTRACT(YEAR  FROM DATA_RIF) AS ANNO,
       EXTRACT(MONTH FROM DATA_RIF) AS MESE,
       COUNT(*) AS CNT
FROM SIUDEVICE.DEV_STRUMENTI
GROUP BY EXTRACT(YEAR FROM DATA_RIF), EXTRACT(MONTH FROM DATA_RIF)
ORDER BY ANNO DESC, MESE DESC;

-- Conversioni e confronti robusti su DATE
SELECT *
FROM SIUDEVICE.DEV_STRUMENTI
WHERE TO_DATE(TO_CHAR(DATA_RIF, 'YYYY-MM-DD'), 'YYYY-MM-DD') >= DATE '2025-01-01';

-- Confronto numerico dopo cast
SELECT *
FROM SIUDEVICE.DEV_STRUMENTI
WHERE TO_NUMBER(VALORE_NUMERICO) > 1000;
```

---

## Trovare colonne che contengono “IBAN”

### REPL (più rapido)

```
\find %IBAN%
```

### SQL (ricerche più mirate)

```sql
-- Colonne con 'IBAN' nel nome, in qualsiasi tabella/viste accessibili
SELECT OWNER, TABLE_NAME, COLUMN_NAME, DATA_TYPE, DATA_LENGTH
FROM ALL_TAB_COLUMNS
WHERE UPPER(COLUMN_NAME) LIKE '%IBAN%'
ORDER BY OWNER, TABLE_NAME, COLUMN_ID;

-- Solo tabelle (no viste): join con ALL_TABLES
SELECT c.OWNER, c.TABLE_NAME, c.COLUMN_NAME, c.DATA_TYPE
FROM ALL_TAB_COLUMNS c
JOIN ALL_TABLES t
  ON t.OWNER = c.OWNER AND t.TABLE_NAME = c.TABLE_NAME
WHERE UPPER(c.COLUMN_NAME) LIKE '%IBAN%'
ORDER BY c.OWNER, c.TABLE_NAME, c.COLUMN_ID;

-- Limita a uno schema specifico (es. SIUDEVICE)
SELECT OWNER, TABLE_NAME, COLUMN_NAME
FROM ALL_TAB_COLUMNS
WHERE OWNER = 'SIUDEVICE'
  AND UPPER(COLUMN_NAME) LIKE '%IBAN%'
ORDER BY TABLE_NAME, COLUMN_ID;

-- Escludi schemi di sistema più comuni
SELECT OWNER, TABLE_NAME, COLUMN_NAME
FROM ALL_TAB_COLUMNS
WHERE UPPER(COLUMN_NAME) LIKE '%IBAN%'
  AND OWNER NOT IN ('SYS','SYSTEM','XDB','MDSYS','CTXSYS','OUTLN','ORDSYS','APPQOSSYS','LBACSYS')
ORDER BY OWNER, TABLE_NAME, COLUMN_ID;

-- Versione REGEX (cattura varianti tipo I_BAN / I-BAN / IBAN, case-insensitive)
SELECT OWNER, TABLE_NAME, COLUMN_NAME
FROM ALL_TAB_COLUMNS
WHERE REGEXP_LIKE(COLUMN_NAME, 'I[_-]?B[_-]?A[_-]?N', 'i')
ORDER BY OWNER, TABLE_NAME, COLUMN_ID;

-- Cerca anche nelle descrizioni delle colonne (commenti)
SELECT c.OWNER, c.TABLE_NAME, c.COLUMN_NAME, com.COMMENTS
FROM ALL_TAB_COLUMNS c
LEFT JOIN ALL_COL_COMMENTS com
  ON com.OWNER = c.OWNER
 AND com.TABLE_NAME = c.TABLE_NAME
 AND com.COLUMN_NAME = c.COLUMN_NAME
WHERE UPPER(c.COLUMN_NAME) LIKE '%IBAN%'
   OR (com.COMMENTS IS NOT NULL AND UPPER(com.COMMENTS) LIKE '%IBAN%')
ORDER BY c.OWNER, c.TABLE_NAME, c.COLUMN_ID;

-- Riassunto per schema: quante colonne con 'IBAN' per owner
SELECT OWNER, COUNT(*) AS NUM_COLONNE_IBAN
FROM ALL_TAB_COLUMNS
WHERE UPPER(COLUMN_NAME) LIKE '%IBAN%'
GROUP BY OWNER
ORDER BY NUM_COLONNE_IBAN DESC;
```

---

## Uscire

```
\q
```

Buon lavoro! 🚀



Boom, ottimo risultato. Ora che hai l’elenco delle colonne con “IBAN”, ti lascio subito comandi pratici per ispezionare valori, validare formato, trovare duplicati e verificare indici. Tutto ASCII-safe.

---

## Query pronte (copiale nel REPL)

### 1) Anteprima valori IBAN puliti e mascherati (per una tabella)

```sql
-- Sostituisci OWNER.TABELLA e NOME_COLONNA
WITH t AS (
  SELECT REPLACE(REPLACE(UPPER(TRIM(NOME_COLONNA)), ' ', ''), '-', '') AS IBAN
  FROM OWNER.TABELLA
  WHERE NOME_COLONNA IS NOT NULL
)
SELECT
  IBAN,
  CASE
    WHEN LENGTH(IBAN) >= 8
      THEN SUBSTR(IBAN,1,4) || RPAD('*', GREATEST(LENGTH(IBAN)-8,0), '*') || SUBSTR(IBAN,-4)
    ELSE IBAN
  END AS IBAN_MASK
FROM t
FETCH FIRST 20 ROWS ONLY;
```

### 2) Conteggio righe non nulle e non vuote (per tabella)

```sql
-- Sostituisci OWNER.TABELLA e NOME_COLONNA
SELECT COUNT(*) AS CNT
FROM OWNER.TABELLA
WHERE NOME_COLONNA IS NOT NULL
  AND TRIM(NOME_COLONNA) <> '';
```

### 3) Duplicati di IBAN nella stessa tabella

```sql
-- Sostituisci OWNER.TABELLA e NOME_COLONNA
WITH t AS (
  SELECT REPLACE(REPLACE(UPPER(TRIM(NOME_COLONNA)), ' ', ''), '-', '') AS IBAN_NORM
  FROM OWNER.TABELLA
  WHERE NOME_COLONNA IS NOT NULL
)
SELECT IBAN_NORM, COUNT(*) AS OCCORRENZE
FROM t
GROUP BY IBAN_NORM
HAVING COUNT(*) > 1
ORDER BY OCCORRENZE DESC;
```

### 4) Validazione di base (pattern IBAN generico)

```sql
-- Sostituisci OWNER.TABELLA e NOME_COLONNA
WITH t AS (
  SELECT REPLACE(REPLACE(UPPER(TRIM(NOME_COLONNA)), ' ', ''), '-', '') AS IBAN
  FROM OWNER.TABELLA
  WHERE NOME_COLONNA IS NOT NULL
)
SELECT
  IBAN,
  CASE
    WHEN REGEXP_LIKE(IBAN, '^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$')
      THEN 'OK_PATTERN'
    ELSE 'KO_PATTERN'
  END AS ESITO
FROM t
FETCH FIRST 50 ROWS ONLY;
```

### 5) Validazione struttura IBAN italiana (27 char)

```sql
-- Sostituisci OWNER.TABELLA e NOME_COLONNA
WITH t AS (
  SELECT REPLACE(REPLACE(UPPER(TRIM(NOME_COLONNA)), ' ', ''), '-', '') AS IBAN
  FROM OWNER.TABELLA
  WHERE NOME_COLONNA IS NOT NULL
)
SELECT
  IBAN
FROM t
WHERE NOT REGEXP_LIKE(
  IBAN,
  '^IT[0-9]{2}[A-Z0-9]{1}[0-9]{5}[0-9]{5}[A-Z0-9]{12}$'
);
-- Se zero righe: tutti gli IBAN rispettano il formato base "IT"
```

> Nota: il check “vero” dell’IBAN richiede la verifica MOD 97. Se ti serve, ti passo una funzione PL/SQL pronta all’uso.

### 6) Ricerca di un IBAN specifico in una tabella (normalizzato)

```sql
-- Sostituisci OWNER.TABELLA, NOME_COLONNA e il valore
WITH param AS (SELECT 'IT60X0542811101000000123456' AS VAL FROM DUAL),
t AS (
  SELECT REPLACE(REPLACE(UPPER(TRIM(NOME_COLONNA)), ' ', ''), '-', '') AS IBAN
  FROM OWNER.TABELLA
)
SELECT COUNT(*) AS HITS
FROM t, param
WHERE t.IBAN = param.VAL;
```

### 7) Colonne indicizzate contenenti "IBAN"

```sql
SELECT ic.TABLE_OWNER, ic.TABLE_NAME, ic.COLUMN_NAME, i.INDEX_NAME, i.UNIQUENESS
FROM ALL_IND_COLUMNS ic
JOIN ALL_INDEXES i
  ON i.OWNER = ic.INDEX_OWNER AND i.INDEX_NAME = ic.INDEX_NAME
WHERE UPPER(ic.COLUMN_NAME) LIKE '%IBAN%'
ORDER BY ic.TABLE_OWNER, ic.TABLE_NAME, ic.INDEX_NAME, ic.COLUMN_POSITION;
```

---

## Generatore di SQL per cercare un pattern su tutte le colonne "IBAN"

Questo produce un elenco di SELECT pronte da copiare/eseguire (LIKE su pattern normalizzato). Sostituisci la stringa PATTERN con quello che ti serve, ad es. '%IT60%'.

```sql
SELECT
  'SELECT '''||OWNER||''' AS OWNER, '''||TABLE_NAME||''' AS TABLE_NAME, '''||COLUMN_NAME||''' AS COLUMN_NAME, COUNT(*) AS HITS '||
  'FROM '||OWNER||'.'||TABLE_NAME||' WHERE REGEXP_LIKE(REPLACE(REPLACE(UPPER('||COLUMN_NAME||'), '' '',''''), ''-'',''''), '''||REPLACE('PATTERN','''','''''')||''');'
AS SQL_SNIPPET
FROM ALL_TAB_COLUMNS
WHERE UPPER(COLUMN_NAME) LIKE '%IBAN%'
ORDER BY OWNER, TABLE_NAME, COLUMN_NAME;
```

Copia le righe risultanti e lanciale nel REPL. Per sommare i risultati puoi avvolgerle in UNION ALL e fare una SELECT esterna.

---

## Vuoi farlo con un solo comando nel REPL?

Se ti fa comodo, posso darti una mini patch per aggiungere:

* `\grepiban <pattern>`  -> conta hit per ogni owner.tabella.colonna
* `\ibanfind <IBAN>`     -> match esatto normalizzato su tutte le colonne

(La patch usa bind variables e ignora tabelle in errore, continuando con le altre.)
