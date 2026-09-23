# Monitor Case

App per essere avvisati quando compaiono nuovi annunci di case in vendita
in specifiche vie (Lombardia).

## Come si usa

1. Carica **tutti** questi file/cartelle nel tuo repository GitHub
   (mantenendo la struttura, inclusa la cartella `.github/workflows`).
2. Verifica in **Settings → Pages** che GitHub Pages sia attivo sul branch
   `main`, cartella root.
3. Apri il link della Pages (es. `https://tuonome.github.io/monitor-case/`).
4. Alla prima apertura ti chiederà repository (formato `utente/nome-repo`)
   e il token: inseriscili, restano salvati solo nel tuo browser.
5. Aggiungi le vie che vuoi monitorare dal form in alto.
6. Lo script automatico (`scraper.py`) gira da solo ogni 6 ore tramite
   GitHub Actions e aggiorna `annunci.json`. Ogni volta che apri l'app
   vedrai evidenziati in verde gli annunci nuovi dall'ultima visita.

## Avviare un controllo subito (senza aspettare le 6 ore)

Nel repo, vai su **Actions → Monitor annunci case → Run workflow**.

## Manutenzione

I portali immobiliari cambiano periodicamente struttura. Se un portale
smette di restituire risultati, i selettori in `scraper.py` vanno
aggiornati (sono commentati per portale, così è facile isolare il
problema). Gli altri portali continuano a funzionare comunque, perché
ogni ricerca è isolata in un blocco try/except a sé.
