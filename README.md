# Telegram To-Do Bot

## Italiano

Bot Telegram personale per gestire una to-do list, con persistenza su SQLite.

**Stack:** Python · python-telegram-bot · SQLite · systemd (deploy)

### Descrizione

Bot Telegram ad uso privato per tenere traccia delle proprie attività: permette di aggiungere, elencare, completare ed eliminare task direttamente dalla chat, con un bottone inline per completare rapidamente ogni task mostrata. L'accesso è limitato a un singolo utente autorizzato tramite il proprio ID Telegram numerico. Include un file di unit systemd di esempio per l'esecuzione come servizio persistente.

### Come si esegue

1. Crea un virtualenv e installa le dipendenze:
   ```
   pip install -r requirements.txt
   ```

2. Copia il template in `.env`:
   ```
   cp .env.example .env
   ```

3. Compila `.env` con `TELEGRAM_BOT_TOKEN` (ottenuto da [@BotFather](https://t.me/BotFather)) e `TELEGRAM_USER_ID` (il tuo ID numerico Telegram, unico utente autorizzato).

4. Avvia il bot:
   ```
   python bot.py
   ```
   Il database SQLite (`todo.db`) e lo schema vengono creati automaticamente al primo avvio.

Per un deploy come servizio persistente è incluso un file di unit systemd in `ops/`: va adattato (utente e percorsi) e installato con `systemctl` per far partire il bot automaticamente all'avvio e riavviarlo in caso di crash.

### Funzionalità principali

- Autenticazione a singolo utente: solo l'ID Telegram configurato in `TELEGRAM_USER_ID` può usare il bot; ogni altro utente riceve un rifiuto generico ("Non autorizzato"), senza rivelare ulteriori dettagli sul bot
- Comandi: `/add` (crea una task), `/list` (mostra le task aperte, massimo 20), `/today` (task create oggi), `/done ID` (completa), `/delete ID` (elimina), `/help`
- Completamento rapido delle task tramite bottone inline associato a ciascuna voce mostrata in `/list` e `/today`
- Persistenza su SQLite, con vincolo di lunghezza sul titolo (1-500 caratteri) e indice dedicato sulle task aperte per query più rapide
- Comandi del bot registrati automaticamente su Telegram (menu nativo) all'avvio
- Logging centralizzato (livello INFO) con gestione degli errori dedicata
- Deploy come servizio systemd con hardening (`ProtectSystem=strict`, `NoNewPrivileges`, `PrivateTmp`, `UMask=0077`) e riavvio automatico in caso di crash

### Struttura del progetto

```
todolist/
├── bot.py             # Logica del bot: comandi, handler, accesso al database
├── schema.sql          # Schema della tabella tasks (creato automaticamente anche da bot.py)
├── requirements.txt     # Dipendenze Python
├── .env.example         # Template delle variabili d'ambiente richieste
└── ops/                 # File di configurazione per il deploy (unit systemd)
```

### Note

Il file di unit systemd incluso in `ops/` contiene un utente e dei percorsi segnaposto (`TUO_UTENTE`, `/home/TUO_UTENTE/todo-telegram`) da sostituire con i propri prima dell'uso. Il bot è pensato per un singolo utente autorizzato e non supporta la condivisione tra più persone.

### Licenza

MIT

---

## English

A personal Telegram bot for managing a to-do list, backed by SQLite.

**Stack:** Python · python-telegram-bot · SQLite · systemd (deployment)

### Description

A private-use Telegram bot for tracking personal tasks: it lets you add, list, complete and delete tasks directly from the chat, with an inline button to quickly complete any task shown. Access is restricted to a single authorized user via their numeric Telegram ID. Includes a sample systemd unit file for running it as a persistent service.

### How to run

1. Create a virtualenv and install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Copy the template to `.env`:
   ```
   cp .env.example .env
   ```

3. Fill in `.env` with `TELEGRAM_BOT_TOKEN` (obtained from [@BotFather](https://t.me/BotFather)) and `TELEGRAM_USER_ID` (your numeric Telegram ID, the only authorized user).

4. Start the bot:
   ```
   python bot.py
   ```
   The SQLite database (`todo.db`) and schema are created automatically on first run.

For a persistent service deployment, a systemd unit file is included in `ops/`: it needs to be adapted (user and paths) and installed with `systemctl` so the bot starts automatically on boot and restarts on crash.

### Key features

- Single-user authentication: only the Telegram ID set in `TELEGRAM_USER_ID` can use the bot; any other user receives a generic "Not authorized" reply, with no further details about the bot revealed
- Commands: `/add` (create a task), `/list` (show open tasks, up to 20), `/today` (tasks created today), `/done ID` (complete), `/delete ID` (delete), `/help`
- Quick task completion via an inline button attached to each entry shown in `/list` and `/today`
- SQLite persistence, with a length constraint on the title (1-500 characters) and a dedicated index on open tasks for faster queries
- Bot commands automatically registered with Telegram (native menu) on startup
- Centralized logging (INFO level) with dedicated error handling
- Deployed as a systemd service with hardening (`ProtectSystem=strict`, `NoNewPrivileges`, `PrivateTmp`, `UMask=0077`) and automatic restart on crash

### Project structure

```
todolist/
├── bot.py             # Bot logic: commands, handlers, database access
├── schema.sql          # tasks table schema (also created automatically by bot.py)
├── requirements.txt     # Python dependencies
├── .env.example         # Template for the required environment variables
└── ops/                 # Deployment configuration (systemd unit)
```

### Notes

The systemd unit file included in `ops/` contains a placeholder user and paths (`TUO_UTENTE`, `/home/TUO_UTENTE/todo-telegram`) that need to be replaced with real ones before use. The bot is designed for a single authorized user and does not support sharing between multiple people.

### License

MIT