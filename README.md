# Telegram To-Do Bot

## Italiano

Bot Telegram per gestire una to-do list, con persistenza su SQLite, più utenti autorizzati e liste separate per ciascun utente.

**Stack:** Python · python-telegram-bot · SQLite · systemd (deploy)

### Descrizione

Bot Telegram ad uso privato per tenere traccia delle proprie attività: permette di aggiungere, elencare, completare ed eliminare task direttamente dalla chat, con un bottone inline per completare rapidamente ogni task mostrata. L'accesso è limitato agli utenti autorizzati tramite il loro ID Telegram numerico: un amministratore (configurato nel file `.env`) può aggiungere e rimuovere utenti direttamente dalla chat. Ogni utente vede e gestisce soltanto le proprie task. Il codice è organizzato in moduli separati (configurazione, database, middleware, handler, utilità) e include un file di unit systemd di esempio per l'esecuzione come servizio persistente.

### Come si esegue

1. Crea un virtualenv e installa le dipendenze:
   ```
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copia il template in `.env`:
   ```
   cp .env.example .env
   ```

3. Compila `.env` con `TELEGRAM_BOT_TOKEN` (ottenuto da [@BotFather](https://t.me/BotFather)) e `TELEGRAM_USER_ID_ADMIN` (il tuo ID numerico Telegram: sarà l'amministratore). Facoltativamente imposta `TODO_DB_PATH` con il percorso del database (default: `todo.db` nella root del progetto).

4. Avvia il bot:
   ```
   python src/bot.py
   ```
   Il database SQLite e lo schema vengono creati automaticamente al primo avvio nel percorso indicato da `TODO_DB_PATH` (default: `todo.db` nella root del progetto); l'amministratore viene inserito tra gli utenti autorizzati. La cartella che contiene il database deve esistere ed essere scrivibile dall'utente che esegue il bot.

Per un deploy come servizio persistente è incluso un file di unit systemd in `ops/`: va adattato (utente e percorsi) e installato con `systemctl` per far partire il bot automaticamente all'avvio e riavviarlo in caso di crash. Il comando di avvio nell'unit deve puntare a `src/bot.py`, usando il Python del virtualenv (`venv/bin/python`).

Poiché l'unit usa `ProtectSystem=strict`, per il servizio il filesystem è in sola lettura. `ReadWritePaths` deve quindi puntare alla cartella che contiene il database (non al solo file, perché SQLite crea accanto file di journal), che deve esistere prima dell'avvio e appartenere all'utente del servizio. `RequiresMountsFor` impedisce l'avvio finché il disco non è montato, evitando di scrivere sulla scheda SD.

### Funzionalità principali

- Accesso multiutente: possono usare il bot solo l'amministratore (`TELEGRAM_USER_ID_ADMIN`) e gli utenti presenti nel database; ogni altro utente riceve un rifiuto generico ("Non autorizzato"), senza rivelare ulteriori dettagli sul bot
- Gestione utenti riservata all'amministratore: `/adduser USER_ID`, `/deleteuser USER_ID`, `/listuser`. L'amministratore non può essere rimosso e risulta sempre autorizzato
- Liste separate per utente: ogni utente vede, completa ed elimina soltanto le proprie task. Il controllo è fatto a livello di query, quindi non è aggirabile nemmeno con callback costruite a mano
- Comandi per le task: `/add` (crea una task), `/list` (mostra le task aperte), `/today` (task create oggi), `/done ID` (completa), `/delete ID` (elimina), `/help`
- `/help` mostra i comandi di amministrazione solo all'amministratore, e il menu nativo di Telegram li propone solo a lui
- Elenco limitato a 20 task, dalla più vecchia alla più recente, con l'indicazione di quante ne sono mostrate sul totale ("mostro N di M"); i titoli lunghi vengono abbreviati a 80 caratteri nella lista
- Completamento rapido tramite bottone inline associato a ciascuna voce di `/list` e `/today`: dopo ogni click compare una notifica e la lista si aggiorna sul posto, mantenendo i bottoni delle altre task
- `/add` preserva spazi e a capo interni al testo e funziona anche con la forma `/add@nomebot`
- Persistenza su SQLite, con vincolo di lunghezza sul titolo (1-500 caratteri), indice dedicato sulle task aperte di ciascun utente e connessioni chiuse correttamente dopo ogni operazione
- `/today` usa il fuso orario locale del sistema su cui gira il bot
- Comandi del bot registrati automaticamente su Telegram (menu nativo) all'avvio
- Logging centralizzato (livello INFO) e gestione degli errori dedicata, con messaggio di avviso all'utente in caso di errore imprevisto
- Deploy come servizio systemd con hardening (`ProtectSystem=strict`, `NoNewPrivileges`, `PrivateTmp`, `UMask=0077`), riavvio automatico in caso di crash e avvio condizionato al montaggio del disco che ospita il database

### Struttura del progetto

```
todolist/
├── ops/                          # Configurazione per il deploy (unit systemd)
├── src/
│   ├── bot.py                    # Entry point: crea l'applicazione, registra handler e comandi
│   ├── config/
│   │   └── constants.py          # Caricamento di .env, token, ID dell'amministratore, percorso del DB
│   ├── db/
│   │   ├── connection.py         # Connessione SQLite (context manager)
│   │   ├── schema.py             # Creazione di tabelle e indice all'avvio, inserimento dell'admin
│   │   └── repositories/
│   │       ├── tasks.py          # Operazioni sulle task di un utente (aggiungi, elenca, conta, completa, elimina)
│   │       └── users.py          # Gestione degli utenti autorizzati (aggiungi, rimuovi, verifica, elenca)
│   ├── middleware/
│   │   ├── auth.py               # Controlli di autorizzazione (utente e amministratore)
│   │   └── log.py                # Configurazione del logging
│   ├── services/
│   │   └── handlers.py           # Handler dei comandi, dei bottoni inline e degli errori
│   └── utils/
│       └── helper.py             # Funzioni di supporto (es. parsing di un intero positivo)
├── requirements.txt              # Dipendenze Python
├── .env.example                  # Template delle variabili d'ambiente (token, ID admin, percorso del DB opzionale)
├── .env                          # Configurazione locale (non va nel repository)
└── LICENSE                       # Licenza MIT
```

Il database SQLite (`todo.db`) non fa parte del repository: viene creato al primo avvio nel percorso indicato da `TODO_DB_PATH`.

### Note

Il file di unit systemd incluso in `ops/` contiene un utente e dei percorsi segnaposto (`TUO_UTENTE`, `/home/TUO_UTENTE/todo-telegram`, `/mnt/wd1tb/todo-bot-telegram`) da sostituire con i propri prima dell'uso. Se imposti o cambi `TODO_DB_PATH` nel `.env`, aggiorna di conseguenza anche `ReadWritePaths` e `RequiresMountsFor` nell'unit, altrimenti il servizio non riuscirà ad aprire il database (`unable to open database file`). Gli import interni usano percorsi relativi a `src/` (es. `from config.constants import TOKEN`), quindi il bot va avviato come script (`python src/bot.py`) e non come pacchetto.

Rimuovendo un utente con `/deleteuser` le sue task **non** vengono eliminate: restano nel database e ricompaiono se lo stesso ID viene riaggiunto. Gli ID delle task sono un unico contatore per tutto il database, quindi nella lista di un utente possono comparire numeri non consecutivi.

### Licenza

MIT

---

## English

A Telegram bot for managing a to-do list, backed by SQLite, with multiple authorized users and a separate list for each user.

**Stack:** Python · python-telegram-bot · SQLite · systemd (deployment)

### Description

A private-use Telegram bot for tracking personal tasks: it lets you add, list, complete and delete tasks directly from the chat, with an inline button to quickly complete any task shown. Access is restricted to authorized users via their numeric Telegram ID: an administrator (set in the `.env` file) can add and remove users straight from the chat. Each user sees and manages only their own tasks. The code is split into separate modules (configuration, database, middleware, handlers, utilities) and includes a sample systemd unit file for running it as a persistent service.

### How to run

1. Create a virtualenv and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copy the template to `.env`:
   ```
   cp .env.example .env
   ```

3. Fill in `.env` with `TELEGRAM_BOT_TOKEN` (obtained from [@BotFather](https://t.me/BotFather)) and `TELEGRAM_USER_ID_ADMIN` (your numeric Telegram ID: you will be the administrator). Optionally set `TODO_DB_PATH` to the database path (default: `todo.db` in the project root).

4. Start the bot:
   ```
   python src/bot.py
   ```
   The SQLite database and schema are created automatically on first run at the path given by `TODO_DB_PATH` (default: `todo.db` in the project root); the administrator is added to the authorized users. The folder that holds the database must exist and be writable by the user running the bot.

For a persistent service deployment, a systemd unit file is included in `ops/`: it needs to be adapted (user and paths) and installed with `systemctl` so the bot starts automatically on boot and restarts on crash. The start command in the unit must point to `src/bot.py`, using the virtualenv's Python (`venv/bin/python`).

Because the unit uses `ProtectSystem=strict`, the filesystem is read-only for the service. `ReadWritePaths` must therefore point to the folder that holds the database (not just the file, since SQLite creates journal files next to it), which must exist before startup and be owned by the service user. `RequiresMountsFor` prevents the service from starting until the disk is mounted, which avoids writing to the SD card.

### Key features

- Multi-user access: only the administrator (`TELEGRAM_USER_ID_ADMIN`) and the users stored in the database can use the bot; any other user receives a generic "Not authorized" reply, with no further details about the bot revealed
- Administrator-only user management: `/adduser USER_ID`, `/deleteuser USER_ID`, `/listuser`. The administrator cannot be removed and is always authorized
- Separate lists per user: each user sees, completes and deletes only their own tasks. Ownership is enforced in the queries, so it cannot be bypassed even with hand-crafted callbacks
- Task commands: `/add` (create a task), `/list` (show open tasks), `/today` (tasks created today), `/done ID` (complete), `/delete ID` (delete), `/help`
- `/help` shows the admin commands only to the administrator, and Telegram's native command menu lists them only for them
- Lists are capped at 20 tasks, oldest first, with a count of how many are shown out of the total ("showing N of M"); long titles are shortened to 80 characters in the list
- Quick completion via an inline button attached to each entry in `/list` and `/today`: after every click a notification appears and the list refreshes in place, keeping the buttons of the remaining tasks
- `/add` preserves inner spaces and line breaks in the text and also works with the `/add@botname` form
- SQLite persistence, with a length constraint on the title (1-500 characters), a dedicated index on each user's open tasks, and connections properly closed after each operation
- `/today` uses the local time zone of the system running the bot
- Bot commands automatically registered with Telegram (native menu) on startup
- Centralized logging (INFO level) and dedicated error handling, with a notice sent to the user on unexpected errors
- Deployed as a systemd service with hardening (`ProtectSystem=strict`, `NoNewPrivileges`, `PrivateTmp`, `UMask=0077`), automatic restart on crash, and startup conditioned on the disk that holds the database being mounted

### Project structure

```
todolist/
├── ops/                          # Deployment configuration (systemd unit)
├── src/
│   ├── bot.py                    # Entry point: builds the application, registers handlers and commands
│   ├── config/
│   │   └── constants.py          # Loads .env, token, administrator ID, DB path
│   ├── db/
│   │   ├── connection.py         # SQLite connection (context manager)
│   │   ├── schema.py             # Creates tables and index on startup, inserts the admin
│   │   └── repositories/
│   │       ├── tasks.py          # Per-user task operations (add, list, count, complete, delete)
│   │       └── users.py          # Authorized-user management (add, remove, check, list)
│   ├── middleware/
│   │   ├── auth.py               # Authorization checks (user and administrator)
│   │   └── log.py                # Logging configuration
│   ├── services/
│   │   └── handlers.py           # Command, inline-button and error handlers
│   └── utils/
│       └── helper.py             # Helper functions (e.g. parsing a positive integer)
├── requirements.txt              # Python dependencies
├── .env.example                  # Template for the environment variables (token, admin ID, optional DB path)
├── .env                          # Local configuration (not committed)
└── LICENSE                       # MIT license
```

The SQLite database (`todo.db`) is not part of the repository: it is created on first run at the path given by `TODO_DB_PATH`.

### Notes

The systemd unit file included in `ops/` contains a placeholder user and paths (`TUO_UTENTE`, `/home/TUO_UTENTE/todo-telegram`, `/mnt/wd1tb/todo-bot-telegram`) that need to be replaced with real ones before use. If you set or change `TODO_DB_PATH` in `.env`, update `ReadWritePaths` and `RequiresMountsFor` in the unit accordingly, otherwise the service will fail to open the database (`unable to open database file`). Internal imports are relative to `src/` (e.g. `from config.constants import TOKEN`), so the bot must be started as a script (`python src/bot.py`) rather than as a package.

Removing a user with `/deleteuser` does **not** delete their tasks: they stay in the database and reappear if the same ID is added again. Task IDs come from a single counter shared by the whole database, so the IDs in a user's list may not be consecutive.

### License

MIT