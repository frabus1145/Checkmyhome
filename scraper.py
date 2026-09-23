#!/usr/bin/env python3
"""
scraper.py
----------
Legge le vie da monitorare da config.json, cerca annunci di case in
vendita su un gruppo di portali immobiliari italiani, e aggiorna
annunci.json con i nuovi annunci trovati (quelli non ancora visti in
precedenza).

NOTA IMPORTANTE:
I portali immobiliari cambiano spesso la struttura delle loro pagine
e possono introdurre protezioni anti-bot. I selettori qui sotto sono
un punto di partenza ragionevole ma vanno verificati e probabilmente
aggiustati nel tempo. Se un sito smette di restituire risultati,
controlla prima se ha cambiato la struttura HTML (con gli strumenti
sviluppatore del browser, tasto destro -> Ispeziona su un annuncio).
"""

import json
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

CONFIG_PATH = Path("config.json")
ANNUNCI_PATH = Path("annunci.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "it-IT,it;q=0.9",
}

TIMEOUT = 20


def normalizza(testo: str) -> str:
    """Toglie accenti/maiuscole per confronti robusti tra stringhe."""
    testo = testo.lower().strip()
    testo = unicodedata.normalize("NFKD", testo)
    testo = "".join(c for c in testo if not unicodedata.combining(c))
    testo = re.sub(r"\s+", " ", testo)
    return testo


def testo_contiene_via(testo: str, via: str) -> bool:
    return normalizza(via) in normalizza(testo)


def get_soup(url: str):
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"  [errore richiesta] {url} -> {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------
# Un "cercatore" per portale. Ognuno riceve (via, comune) e restituisce
# una lista di dict: {"titolo", "url", "prezzo", "portale"}
# Ogni funzione è isolata in try/except a monte, così se un portale
# fallisce (o cambia struttura) gli altri continuano a funzionare.
# ---------------------------------------------------------------------

def cerca_immobiliare(via: str, comune: str):
    query = quote_plus(f"{via} {comune}")
    url = f"https://www.immobiliare.it/vendita-case/{quote_plus(comune.lower())}/?criterio=rilevanza&noAgenzie=0&q={query}"
    soup = get_soup(url)
    if not soup:
        return []
    risultati = []
    for card in soup.select("[class*='nd-mediaObject'], [class*='in-listingCard']"):
        titolo_tag = card.select_one("a")
        if not titolo_tag:
            continue
        titolo = titolo_tag.get_text(strip=True)
        href = titolo_tag.get("href", "")
        if href and not href.startswith("http"):
            href = "https://www.immobiliare.it" + href
        blocco_testo = card.get_text(" ", strip=True)
        if testo_contiene_via(blocco_testo, via):
            prezzo_tag = card.select_one("[class*='price']")
            risultati.append({
                "portale": "Immobiliare.it",
                "titolo": titolo or blocco_testo[:80],
                "url": href,
                "prezzo": prezzo_tag.get_text(strip=True) if prezzo_tag else "",
            })
    return risultati


def cerca_casa_it(via: str, comune: str):
    query = quote_plus(f"{via} {comune}")
    url = f"https://www.casa.it/vendita/residenziale/{quote_plus(comune.lower())}/?q={query}"
    soup = get_soup(url)
    if not soup:
        return []
    risultati = []
    for card in soup.select("[class*='listing-item'], article"):
        titolo_tag = card.select_one("a")
        if not titolo_tag:
            continue
        href = titolo_tag.get("href", "")
        if href and not href.startswith("http"):
            href = "https://www.casa.it" + href
        blocco_testo = card.get_text(" ", strip=True)
        if testo_contiene_via(blocco_testo, via):
            prezzo_tag = card.select_one("[class*='price']")
            risultati.append({
                "portale": "Casa.it",
                "titolo": blocco_testo[:80],
                "url": href,
                "prezzo": prezzo_tag.get_text(strip=True) if prezzo_tag else "",
            })
    return risultati


def cerca_idealista(via: str, comune: str):
    # idealista.it ha protezioni anti-bot piuttosto aggressive: questa
    # funzione potrebbe restituire pochi/nessun risultato dietro CAPTCHA.
    query = quote_plus(f"{comune}")
    url = f"https://www.idealista.it/vendita-case/{quote_plus(comune.lower())}-{quote_plus(comune.lower())}/"
    soup = get_soup(url)
    if not soup:
        return []
    risultati = []
    for card in soup.select("article[class*='item']"):
        titolo_tag = card.select_one("a[class*='item-link']")
        if not titolo_tag:
            continue
        href = titolo_tag.get("href", "")
        if href and not href.startswith("http"):
            href = "https://www.idealista.it" + href
        blocco_testo = card.get_text(" ", strip=True)
        if testo_contiene_via(blocco_testo, via):
            prezzo_tag = card.select_one("[class*='price']")
            risultati.append({
                "portale": "Idealista.it",
                "titolo": blocco_testo[:80],
                "url": href,
                "prezzo": prezzo_tag.get_text(strip=True) if prezzo_tag else "",
            })
    return risultati


def cerca_subito(via: str, comune: str):
    query = quote_plus(f"{via} {comune}")
    url = f"https://www.subito.it/annunci-lombardia/vendita/appartamenti/?q={query}"
    soup = get_soup(url)
    if not soup:
        return []
    risultati = []
    for card in soup.select("[class*='item-key'], article"):
        titolo_tag = card.select_one("a")
        if not titolo_tag:
            continue
        href = titolo_tag.get("href", "")
        blocco_testo = card.get_text(" ", strip=True)
        if testo_contiene_via(blocco_testo, via):
            prezzo_tag = card.select_one("[class*='price']")
            risultati.append({
                "portale": "Subito.it",
                "titolo": blocco_testo[:80],
                "url": href,
                "prezzo": prezzo_tag.get_text(strip=True) if prezzo_tag else "",
            })
    return risultati


PORTALI = [cerca_immobiliare, cerca_casa_it, cerca_idealista, cerca_subito]


def main():
    if not CONFIG_PATH.exists():
        print("config.json non trovato, esco.", file=sys.stderr)
        sys.exit(1)

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    vie = config.get("vie", [])

    if ANNUNCI_PATH.exists():
        stato = json.loads(ANNUNCI_PATH.read_text(encoding="utf-8"))
    else:
        stato = {"ultimo_controllo": None, "annunci": []}

    url_gia_visti = {a["url"] for a in stato.get("annunci", [])}
    annunci_correnti = list(stato.get("annunci", []))

    if not vie:
        print("Nessuna via configurata in config.json, niente da cercare.")
    for voce in vie:
        via = voce.get("via", "").strip()
        comune = voce.get("comune", "").strip()
        if not via or not comune:
            continue
        print(f"Controllo: {via}, {comune}")
        for cerca in PORTALI:
            try:
                trovati = cerca(via, comune)
            except Exception as e:
                print(f"  [errore portale {cerca.__name__}] {e}", file=sys.stderr)
                trovati = []
            for annuncio in trovati:
                if not annuncio.get("url") or annuncio["url"] in url_gia_visti:
                    continue
                annuncio["via_cercata"] = f"{via}, {comune}"
                annuncio["trovato_il"] = datetime.now(timezone.utc).isoformat()
                annunci_correnti.append(annuncio)
                url_gia_visti.add(annuncio["url"])
                print(f"  + nuovo annuncio: {annuncio['titolo']} ({annuncio['portale']})")
            time.sleep(2)  # ritmo gentile tra una richiesta e l'altra

    stato["ultimo_controllo"] = datetime.now(timezone.utc).isoformat()
    stato["annunci"] = annunci_correnti
    ANNUNCI_PATH.write_text(
        json.dumps(stato, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Fatto. Totale annunci in archivio: {len(annunci_correnti)}")


if __name__ == "__main__":
    main()
