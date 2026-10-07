; =============================================================================
;  Mouse Recorder - AutoHotkey v2 (versione portable, nessuna installazione)
; -----------------------------------------------------------------------------
;  F9        Avvia / ferma la registrazione (movimenti, click, rotellina)
;  F10       Riproduci / ferma la riproduzione
;  F11       Attiva / disattiva la ripetizione continua (loop)
;  Ctrl+F12  Chiudi il programma
;
;  La registrazione viene salvata in "registrazione.txt" accanto allo script
;  e ricaricata automaticamente al prossimo avvio.
; =============================================================================
#Requires AutoHotkey v2.0
#SingleInstance Force

CoordMode "Mouse", "Screen"
CoordMode "ToolTip", "Screen"
SendMode "Input"
SetMouseDelay -1

; ---- Impostazioni modificabili ----------------------------------------------
global PollMs      := 10      ; ogni quanti ms campionare la posizione del mouse
global LoopPauseMs := 500     ; pausa tra una ripetizione e l'altra (loop)
global Speed       := 1.0     ; 2.0 = doppia velocita', 0.5 = meta' velocita'
global SaveFile    := A_ScriptDir "\registrazione.txt"
; -----------------------------------------------------------------------------

global Events    := []
global Recording := false
global Playing   := false
global LoopMode  := false
global RecStart  := 0
global LastX     := ""
global LastY     := ""
global HeldDown  := Map()     ; pulsanti premuti durante la riproduzione

LoadRecording()
ShowTip("Mouse Recorder pronto (" Events.Length " eventi caricati)`n"
    . "F9 = registra   F10 = riproduci   F11 = loop   Ctrl+F12 = esci", 5000)

F9::ToggleRecording()
F10::TogglePlayback()
F11::ToggleLoop()
^F12::ExitApp()

; ---- Registrazione ----------------------------------------------------------
ToggleRecording() {
    global Events, Recording, Playing, RecStart, LastX, LastY, PollMs
    if Playing
        return
    if !Recording {
        Events := []
        LastX := "", LastY := ""
        RecStart := A_TickCount
        Recording := true
        SetTimer(PollMouse, PollMs)
        ShowTip("● REC  -  premi F9 per fermare")
    } else {
        Recording := false
        SetTimer(PollMouse, 0)
        SaveRecording()
        ShowTip("Registrazione salvata: " Events.Length " eventi", 2500)
    }
}

PollMouse() {
    global Events, RecStart, LastX, LastY
    MouseGetPos(&x, &y)
    if (x != LastX || y != LastY) {
        Events.Push({t: A_TickCount - RecStart, k: "M", x: x, y: y})
        LastX := x, LastY := y
    }
}

AddEvent(kind) {
    global Events, RecStart, LastX, LastY
    MouseGetPos(&x, &y)
    Events.Push({t: A_TickCount - RecStart, k: kind, x: x, y: y})
    LastX := x, LastY := y
}

; Il prefisso ~ lascia passare il click all'applicazione: si registra e basta.
#HotIf Recording
~*LButton::AddEvent("LD")
~*LButton Up::AddEvent("LU")
~*RButton::AddEvent("RD")
~*RButton Up::AddEvent("RU")
~*MButton::AddEvent("MD")
~*MButton Up::AddEvent("MU")
~*WheelUp::AddEvent("WU")
~*WheelDown::AddEvent("WD")
#HotIf

; ---- Riproduzione -----------------------------------------------------------
TogglePlayback() {
    global Events, Recording, Playing
    if Recording
        return
    if Playing {
        Playing := false          ; il ciclo di riproduzione si fermera' da solo
        return
    }
    if Events.Length = 0 {
        ShowTip("Nessuna registrazione: premi F9 per registrare", 2500)
        return
    }
    Playing := true
    SetTimer(PlayRun, -1)
}

ToggleLoop() {
    global LoopMode
    LoopMode := !LoopMode
    ShowTip("Loop " (LoopMode ? "ATTIVO" : "disattivato"), 1500)
}

PlayRun() {
    global Playing, LoopMode, LoopPauseMs
    n := 0
    Loop {
        n++
        ShowTip("▶ Riproduzione" (LoopMode ? " (ciclo " n ")" : "") "  -  F10 per fermare")
        if !PlayOnce() || !LoopMode
            break
        if !WaitUntil(A_TickCount + LoopPauseMs)
            break
    }
    ReleaseHeld()
    Playing := false
    ShowTip("Riproduzione terminata", 1500)
}

PlayOnce() {
    global Events, Speed
    start := A_TickCount
    for e in Events {
        if !WaitUntil(start + Round(e.t / Speed))
            return false
        DoEvent(e)
    }
    return true
}

; Attende fino all'istante indicato restando interrompibile con F10.
WaitUntil(target) {
    global Playing
    while (A_TickCount < target) {
        if !Playing
            return false
        Sleep(Min(target - A_TickCount, 20))
    }
    return Playing
}

DoEvent(e) {
    global HeldDown
    static btn := Map("L", "Left", "R", "Right", "M", "Middle")
    switch e.k {
        case "M":
            MouseMove(e.x, e.y, 0)
        case "WU":
            MouseMove(e.x, e.y, 0)
            Click("WheelUp")
        case "WD":
            MouseMove(e.x, e.y, 0)
            Click("WheelDown")
        default:
            b := btn[SubStr(e.k, 1, 1)]
            if SubStr(e.k, 2, 1) = "D" {
                Click(e.x, e.y, b, "Down")
                HeldDown[b] := true
            } else {
                Click(e.x, e.y, b, "Up")
                HeldDown.Delete(b)
            }
    }
}

; Se la riproduzione viene fermata a meta' di un trascinamento, rilascia i tasti.
ReleaseHeld() {
    global HeldDown
    for b in HeldDown
        Click(b, "Up")
    HeldDown := Map()
}

; ---- Salvataggio / caricamento ----------------------------------------------
SaveRecording() {
    global Events, SaveFile
    out := ""
    for e in Events
        out .= e.t "|" e.k "|" e.x "|" e.y "`n"
    try FileDelete(SaveFile)
    FileAppend(out, SaveFile, "UTF-8-RAW")
}

LoadRecording() {
    global Events, SaveFile
    if !FileExist(SaveFile)
        return
    Events := []
    Loop Read SaveFile {
        p := StrSplit(Trim(A_LoopReadLine), "|")
        if p.Length != 4
            continue
        try Events.Push({t: Integer(p[1]), k: p[2], x: Integer(p[3]), y: Integer(p[4])})
    }
}

; ---- Utilita' ---------------------------------------------------------------
ShowTip(text, ms := 0) {
    ToolTip(text, 10, 10)
    SetTimer(HideTip, ms ? -ms : 0)   ; 0 = annulla un'eventuale chiusura in sospeso
}
HideTip() => ToolTip()
