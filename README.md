# Telegram To-Do Bot

## Italiano

Bot Telegram personale per gestire una to-do list, con persistenza su SQLite.

**Stack:** Python · python-telegram-bot · SQLite · systemd (deploy)

### Descrizione

Bot Telegram ad uso privato per tenere traccia delle proprie attività: permette di aggiungere, elencare, completare ed eliminare task direttamente dalla chat, con un bottone inline per completare rapidamente ogni task mostrata. L'accesso è limitato a un singolo utente autorizzato tramite il proprio ID Telegram numerico. Il codice è organizzato in moduli separati (configurazione, database, middleware, handler, utilità) e include un file di unit systemd di esempio per l'esecuzione come servizio persistente.

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

3. Compila `.env` con `TELEGRAM_BOT_TOKEN` (ottenuto da [@BotFather](https://t.me/BotFather)) e `TELEGRAM_USER_ID` (il tuo ID numerico Telegram, unico utente autorizzato).

4. Avvia il bot:
   ```
   python src/bot.py
   ```
   Il database SQLite (`todo.db`, nella root del progetto) e lo schema vengono creati automaticamente al primo avvio.

Per un deploy come servizio persistente è incluso un file di unit systemd in `ops/`: va adattato (utente e percorsi) e installato con `systemctl` per far partire il bot automaticamente all'avvio e riavviarlo in caso di crash. Il comando di avvio nell'unit deve puntare a `src/bot.py`, usando il Python del virtualenv.

### Funzionalità principali

- Autenticazione a singolo utente: solo l'ID Telegram configurato in `TELEGRAM_USER_ID` può usare il bot; ogni altro utente riceve un rifiuto generico ("Non autorizzato"), senza rivelare ulteriori dettagli sul bot
- Comandi: `/add` (crea una task), `/list` (mostra le task aperte), `/today` (task create oggi), `/done ID` (completa), `/delete ID` (elimina), `/help`
- Elenco limitato a 20 task, dalla più vecchia alla più recente, con l'indicazione di quante ne sono mostrate sul totale ("mostro N di M"); i titoli lunghi vengono abbreviati a 80 caratteri nella lista
- Completamento rapido tramite bottone inline associato a ciascuna voce di `/list` e `/today`: dopo ogni click compare una notifica e la lista si aggiorna sul posto, mantenendo i bottoni delle altre task
- `/add` preserva spazi e a capo interni al testo e funziona anche con la forma `/add@nomebot`
- Persistenza su SQLite, con vincolo di lunghezza sul titolo (1-500 caratteri), indice dedicato sulle task aperte e connessioni chiuse correttamente dopo ogni operazione
- `/today` usa il fuso orario locale del sistema su cui gira il bot
- Comandi del bot registrati automaticamente su Telegram (menu nativo) all'avvio
- Logging centralizzato (livello INFO) e gestione degli errori dedicata, con messaggio di avviso all'utente in caso di errore imprevisto
- Deploy come servizio systemd con hardening (`ProtectSystem=strict`, `NoNewPrivileges`, `PrivateTmp`, `UMask=0077`) e riavvio automatico in caso di crash

### Struttura del progetto

```
todolist/
├── ops/                          # Configurazione per il deploy (unit systemd)
├── src/
│   ├── bot.py                    # Entry point: crea l'applicazione, registra handler e comandi
│   ├── config/
│   │   └── constants.py          # Caricamento di .env, token, ID utente autorizzato, percorso del DB
│   ├── db/
│   │   ├── connection.py         # Connessione SQLite (context manager)
│   │   ├── schema.py             # Creazione di tabella e indice all'avvio
│   │   └── repositories/
│   │       ├── tasks.py          # Operazioni sulle task (aggiungi, elenca, conta, completa, elimina)
│   │       └── users.py          # Accesso ai dati degli utenti
│   ├── middleware/
│   │   ├── auth.py               # Controllo dell'utente autorizzato
│   │   └── log.py                # Configurazione del logging
│   ├── services/
│   │   └── handlers.py           # Handler dei comandi, dei bottoni inline e degli errori
│   └── utils/
│       └── helper.py             # Funzioni di supporto (es. parsing dell'ID di una task)
├── requirements.txt              # Dipendenze Python
├── .env.example                  # Template delle variabili d'ambiente richieste
├── .env                          # Configurazione locale (non va nel repository)
└── todo.db                       # Database SQLite, creato al primo avvio (non va nel repository)
```

### Note

Il file di unit systemd incluso in `ops/` contiene un utente e dei percorsi segnaposto (`TUO_UTENTE`, `/home/TUO_UTENTE/todo-telegram`) da sostituire con i propri prima dell'uso. Il bot è pensato per un singolo utente autorizzato e non supporta la condivisione tra più persone. Gli import interni usano percorsi relativi a `src/` (es. `from config.constants import TOKEN`), quindi il bot va avviato come script (`python src/bot.py`) e non come pacchetto.

### Licenza

MIT

---

## English

A personal Telegram bot for managing a to-do list, backed by SQLite.

**Stack:** Python · python-telegram-bot · SQLite · systemd (deployment)

### Description

A private-use Telegram bot for tracking personal tasks: it lets you add, list, complete and delete tasks directly from the chat, with an inline button to quickly complete any task shown. Access is restricted to a single authorized user via their numeric Telegram ID. The code is split into separate modules (configuration, database, middleware, handlers, utilities) and includes a sample systemd unit file for running it as a persistent service.

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

3. Fill in `.env` with `TELEGRAM_BOT_TOKEN` (obtained from [@BotFather](https://t.me/BotFather)) and `TELEGRAM_USER_ID` (your numeric Telegram ID, the only authorized user).

4. Start the bot:
   ```
   python src/bot.py
   ```
   The SQLite database (`todo.db`, in the project root) and schema are created automatically on first run.

For a persistent service deployment, a systemd unit file is included in `ops/`: it needs to be adapted (user and paths) and installed with `systemctl` so the bot starts automatically on boot and restarts on crash. The start command in the unit must point to `src/bot.py`, using the virtualenv's Python.

### Key features

- Single-user authentication: only the Telegram ID set in `TELEGRAM_USER_ID` can use the bot; any other user receives a generic "Not authorized" reply, with no further details about the bot revealed
- Commands: `/add` (create a task), `/list` (show open tasks), `/today` (tasks created today), `/done ID` (complete), `/delete ID` (delete), `/help`
- Lists are capped at 20 tasks, oldest first, with a count of how many are shown out of the total ("showing N of M"); long titles are shortened to 80 characters in the list
- Quick completion via an inline button attached to each entry in `/list` and `/today`: after every click a notification appears and the list refreshes in place, keeping the buttons of the remaining tasks
- `/add` preserves inner spaces and line breaks in the text and also works with the `/add@botname` form
- SQLite persistence, with a length constraint on the title (1-500 characters), a dedicated index on open tasks, and connections properly closed after each operation
- `/today` uses the local time zone of the system running the bot
- Bot commands automatically registered with Telegram (native menu) on startup
- Centralized logging (INFO level) and dedicated error handling, with a notice sent to the user on unexpected errors
- Deployed as a systemd service with hardening (`ProtectSystem=strict`, `NoNewPrivileges`, `PrivateTmp`, `UMask=0077`) and automatic restart on crash

### Project structure

```
todolist/
├── ops/                          # Deployment configuration (systemd unit)
├── src/
│   ├── bot.py                    # Entry point: builds the application, registers handlers and commands
│   ├── config/
│   │   └── constants.py          # Loads .env, token, authorized user ID, DB path
│   ├── db/
│   │   ├── connection.py         # SQLite connection (context manager)
│   │   ├── schema.py             # Creates the table and index on startup
│   │   └── repositories/
│   │       ├── tasks.py          # Task operations (add, list, count, complete, delete)
│   │       └── users.py          # User data access
│   ├── middleware/
│   │   ├── auth.py               # Authorized-user check
│   │   └── log.py                # Logging configuration
│   ├── services/
│   │   └── handlers.py           # Command, inline-button and error handlers
│   └── utils/
│       └── helper.py             # Helper functions (e.g. parsing a task ID)
├── requirements.txt              # Python dependencies
├── .env.example                  # Template for the required environment variables
├── .env                          # Local configuration (not committed)
└── todo.db                       # SQLite database, created on first run (not committed)
```

### Notes

The systemd unit file included in `ops/` contains a placeholder user and paths (`TUO_UTENTE`, `/home/TUO_UTENTE/todo-telegram`) that need to be replaced with real ones before use. The bot is designed for a single authorized user and does not support sharing between multiple people. Internal imports are relative to `src/` (e.g. `from config.constants import TOKEN`), so the bot must be started as a script (`python src/bot.py`) rather than as a package.

### License

MIT