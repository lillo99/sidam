# Mouse Recorder (AutoHotkey v2, portable)

Registra movimenti, click e rotellina del mouse e li riproduce, anche in loop.
Non richiede installazione né diritti di amministratore.

## Preparazione (una volta sola)

1. Scarica **AutoHotkey v2 – Portable .ZIP** dal sito ufficiale:
   https://www.autohotkey.com/download
2. Estrai lo zip e copia `AutoHotkey64.exe` in questa cartella, accanto a
   `mouse_recorder.ahk` e `avvia_mouse_recorder.bat`.
3. Doppio clic su `avvia_mouse_recorder.bat`.

## Comandi

| Tasto      | Azione                                   |
|------------|------------------------------------------|
| F9         | Avvia / ferma la registrazione           |
| F10        | Riproduci / ferma la riproduzione        |
| F11        | Attiva / disattiva il loop continuo      |
| Ctrl+F12   | Chiudi il programma                      |

Lo stato compare in alto a sinistra dello schermo. La registrazione viene salvata
in `registrazione.txt` e ricaricata al successivo avvio.

## Impostazioni

In cima a `mouse_recorder.ahk` puoi cambiare:

- `Speed` – velocità di riproduzione (2.0 = doppia, 0.5 = metà)
- `LoopPauseMs` – pausa tra una ripetizione e l'altra
- `PollMs` – precisione con cui vengono registrati i movimenti

## Note

- Le coordinate sono assolute: riproduci con la stessa risoluzione e le
  finestre nella stessa posizione di quando hai registrato.
- Se sul PC aziendale l'exe viene bloccato, chiedi all'IT invece di aggirare il
  blocco.
