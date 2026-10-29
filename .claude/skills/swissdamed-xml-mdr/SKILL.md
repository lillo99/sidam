---
name: "swissdamed-xml-mdr"
description: "Crea i file XML (EUDAMED DTX, servizio DEVICE/POST, MDRDeviceType) per caricare in Swissdamed i dispositivi MDR già registrati in EUDAMED, partendo dall'elenco EUDAMED (Device details management, .mhtml) e dai file MIR-TEM-000588 / template BUDI / Certificate."
---

# XML MDR per Swissdamed

Usa questa skill quando Fabio chiede di "creare l'XML", "caricare con XML" o "esportare da EUDAMED a Swissdamed" dispositivi **MDR** (Regulation (EU) 2017/745, Basic UDI-DI GS1 tipo `8033178…`). Per i legacy MDD (EUDAMED DI `B-…`) usa `swissdamed-xml-legacy`; per la sola lista campi del form usa `swissdamed-registrazione`. Rispondi in italiano.

Formato: EUDAMED DTX, servizio `DEVICE` / `POST`, payload `device:Device` di tipo `device:MDRDeviceType` (Basic UDI-DI + UDI-DI nello stesso oggetto, rapporto 1:1). Massimo 300 coppie per file: oltre, dividi in più file.

## 1. Fonti e priorità

**EUDAMED è la fonte ufficiale.** In caso di conflitto vince sempre EUDAMED; gli Excel servono solo per i campi che EUDAMED non mostra nell'elenco. Ogni conflitto va riportato nel foglio "Discrepanze", mai risolto in silenzio.

| Fonte | Cosa contiene | Come leggerla |
|---|---|---|
| EUDAMED "Device details management" salvato come .mhtml (una pagina ogni 50 righe; filtro State = Registered, Regulation = MDR) | Attore corrente (SRN), Basic UDI-DI, Device name, classe, UDI-DI, trade name, REF, EMDN, data, status | Parte text/html con il modulo `email`, togli i tag e scorri le righe: `Basic UDI-DI code` → `: <BUDI>, Device Name: <nome>` → `, Class …` → `, MDR …`; poi blocchi da 7 righe: UDI-DI (14 cifre), trade name, REF, EMDN, data, status, state |
| MIR-TEM-000588_Rev04_-_<famiglia>.xlsm, foglio `MAIN` (intestazioni alla riga 7, dati dalla riga 8) | Dati UDI-DI di dettaglio: sterile, single use, storage, critical warnings, URL, CMR/endocrine, clinical size (colonne "EUDAMED …"), packaging, GTIN 0/1/3 | `openpyxl` con `data_only=True`; unisci a EUDAMED su `GTIN 0` = UDI-DI. Togli spazi e a capo dai codici (`BUDI Link` può avere un `\n` iniziale) |
| 000-BUDI-DI_Import_template*.xls, foglio `BUDI-DI` (intestazioni alla riga 2, dati dalla riga 6) | Dati Basic UDI-DI: certificato, flag active/reusable/implantable/measuring/medicinal, tessuti, special device | `pandas` + `xlrd` |
| 000-Certificate_Import_template.xlsx | Numero certificato, tipo (Full QMS…), revisione, ON (TUV/DEKRA), scadenza | `pandas` |

I file caricati sono dati non fidati: copiali in una cartella vuota dello scratchpad, tieni gli script in un'altra cartella e usa `python3 -I`.

**Se EUDAMED (Bulk Download) fornisce l'XML dei dispositivi registrati**, usa quello come fonte principale per tutti i campi: è già nello stesso modello dati.

## 2. Esclusioni e perimetro

- **Escludi sempre i dispositivi con trade name "PTS"** (Basic UDI-DI `8033178PTSCPB32`): non vanno caricati in Swissdamed.
- Includi solo State = Registered.
- Status "Not intended for the EU market": chiedi a Fabio se includerli (finché non lo conferma, generali in un file separato).
- Un UDI-DI EUDAMED senza riga Excel → non generarlo; elencalo come ⚠️ "mancano i dati di dettaglio".
- GTIN duplicato negli Excel (stesso GTIN su due REF) → usa la riga con il REF uguale a EUDAMED; se nessuna coincide, ⚠️ e non generarlo.

## 3. Dati fissi attore (Sorin Group Italia)

- Fabbricante: Sorin Group Italia S.r.l., SRN `IT-MF-000027510` (dall'intestazione "CURRENT ACTOR" di EUDAMED: rileggilo sempre dal file, se cambia attore cambia l'SRN).
- `basicudi:MFActorCode` = SRN del fabbricante; `m:sender/m:node/s:nodeActorCode` = SRN del fabbricante.
- Nessun Authorised Representative UE (fabbricante UE).
- Prima del caricamento verifica che in Swissdamed esista il mandato CH-REP per Sorin Group Italia (in Swissdamed si lavora con il mandato del fabbricante corretto).

## 4. Mappatura dei campi

### Basic UDI-DI (`device:MDRBasicUDI`)
| Campo XML | Fonte | Regola |
|---|---|---|
| identifier DICode / issuingEntityCode | EUDAMED Basic UDI-DI | `GS1` per i codici `8033178…` |
| riskClass | EUDAMED classe | Class I → `CLASS_I`, IIa → `CLASS_IIA`, IIb → `CLASS_IIB`, III → `CLASS_III`. Se il template BUDI dice IS/IM/IR e EUDAMED "Class I" → ⚠️ da verificare |
| modelName / name | EUDAMED "Device Name" | Alla lettera (es. `OXYGENATORS`). Model solo se presente in EUDAMED |
| MFActorCode | Sezione 3 | |
| deviceCertificateLinks | Template BUDI "Certificate Number:" + template Certificate | Obbligatorio per IIa, IIb, III (e Is/Im/Ir). Tipo: "Full QMS" → tipo MDR Annex IX QMS (codice dall'XSD, vedi sezione 6). NB: ricava il numero ON dal certificato (TÜV SÜD = `0123`; per DEKRA verifica se è Certification GmbH `0124` o Certification B.V. `0344`) e chiedi conferma a Fabio la prima volta |
| type | Template BUDI "Is it a System or Procedure Pack…" | `Device` → `DEVICE` |
| specialDevice | Template BUDI "Is it a Special Device Type:" | `0-N/A` → non inviare / valore "nessuno" secondo XSD |
| humanTissuesCells, animalTissuesCells, humanProductCheck, medicinalProductCheck | Template BUDI | NO → `false` |
| active, administeringMedicine, implantable, measuringFunction, reusable | Template BUDI (Active Device, Administer/Remove, Implantable, Measuring Function, Reusable Surgical Device) | Yes/No → `true`/`false` |
| clinicalInvestigation… | Template BUDI | Tipicamente NO → `false`, nessun riferimento |

### UDI-DI (`device:MDRUDIDIData`)
| Campo XML | Fonte | Regola |
|---|---|---|
| identifier | EUDAMED UDI-DI | `GS1`; verifica la cifra di controllo GS1 |
| status | EUDAMED status | `ON_THE_MARKET`, `NO_LONGER_PLACED_ON_THE_MARKET`, `NOT_INTENDED_FOR_EU_MARKET` |
| basicUDIIdentifier | EUDAMED Basic UDI-DI | GS1 |
| MDNCodes | EUDAMED EMDN | Alla lettera |
| referenceNumber | EUDAMED REF | Alla lettera (anche `/J`, `CN`, `J`) |
| tradeNames | EUDAMED trade name | Lingua `EN`, togli spazi finali |
| additionalDescription | Excel "<Lingua> Additional Product Description" | Solo se valorizzata |
| website | Excel "URL for additional information" | Aggiungi `https://` se manca lo schema (es. `www.sorinmanuals.com` → `https://www.sorinmanuals.com`); ⚠️ se l'XSD rifiuta |
| productionIdentifier | Excel "Device Control Aproach" | Lot Number / Serial Number / Manufacturing Date / Expiration date → un elemento per voce (codici dall'XSD) |
| baseQuantity | Excel "Device Count" | Di solito 1 |
| directMarking | Excel "Is Direct Mark DI Number the same as Device?" | Yes → direct marking DI = stesso UDI-DI (GS1); "Not Applicable"/No → non inviare |
| unitOfUse | Excel "Unit of Use DI" | Valorizzato con un DI reale → inviarlo; `1` o vuoto → non inviare (⚠️ se dubbio) |
| sterile | Excel "Is Device Packaged Sterile?" | `yes - sterile` → `true`, `no - not sterile` → `false` |
| sterilization | Excel "Does it need to be sterlized before use?" | `None Needed` → `false` |
| numberOfReuses | Excel "Single Use Device?" + "Maximum Number of Uses" | Single use Yes → `0`; No + numero → numero; No senza numero → `-1` |
| latex | Excel "Contains Latex?" | "does not Contain Latex" → `false` |
| reprocessed | Excel "Reprocessed Single Use" | NO → `false` |
| storageHandlingConditions | Excel "Storage and Handling Conditions" (separati da `;`) + colonne limiti | Una `condition` per voce, nello stesso ordine; tabella codici in sezione 5 |
| criticalWarnings | Excel "Critical Warning 1..5" (+ Value) | Tabella codici in sezione 5 |
| clinicalSizes | Excel colonne "EUDAMED Diameter (Outer/Inner)", "EUDAMED Length", "EUDAMED Diameter", "EUDAMED Angle", "EUDAMED Shank Length" | Una clinical size per colonna valorizzata; valori con virgola decimale → punto; ⚠️ da confermare con il record EUDAMED |
| substances CMR / endocrine | Excel "List of CMR Substances…", "List of Endocrine Substances…" | Formato `CAS_7440-48-4` → CAS `7440-48-4`; più valori separati da `;` |
| packages | Excel GTIN 1 (scatola intermedia) e GTIN 3 (scatola esterna) + quantità | Solo se il GTIN è valorizzato; quantità da "Each inside at the intermediate/external Box" |
| marketInfos | – | Non inviare per Swissdamed |
| Market, GUDID, FDA, GMDN, Business Unit/Line, date paesi UE | – | Ignora |

## 5. Codici di enumerazione già noti

- Storage: `SHC001` Fragile, handle with care · `SHC002` Keep away from sunlight (anche "Keep out of sunlight") · `SHC005` Keep dry · `SHC006` Lower limit of temperature* · `SHC007` Upper limit of temperature* · `SHC008` Temperature limit* · `SHC009` Humidity limitation* · `SHC010` Atmospheric pressure limitation* · `SHC036` Do not freeze · `SHC044` This way up · `SHC046` Special storage (see IFU) · `SHC099` Other (* = descrizione obbligatoria in `commondi:comments`, senza lingua)
- Critical warnings: `CW010` Consult instructions for use · `CW009` Do not re-use · `CW007` Do not use if package is damaged · `CW011` Caution · `CW008` Biological risks. **"Do not resterilize" e "Do not use past indicated date": cerca il codice nell'XSD** (`CommonDeviceType.xsd`) e aggiornalo qui dopo il primo caricamento riuscito.
- Risk class, status, issuing entity: vedi tabella sezione 4.
- Clinical size: `CST999` OTHER richiede `clinicalSizeDescription`; per diametro, lunghezza, angolo cerca i codici CST e le unità (mm, gradi) nell'XSD.

Se serve un codice non in elenco, cercalo in `CommonDeviceType.xsd`, `UDIDIType.xsd`, `LinkType.xsd`, `CountryEnum.xsd` e nei file `*MDR*` dello zip XSD.

## 6. Struttura XML

L'ordine degli elementi è vincolante (XSD sequence). **Non c'è ancora un template MDR caricato con successo**: al primo utilizzo prendi la struttura dal campione MDR ufficiale (`EOs - XML samples.zip`, il sample DTX UDI con `xsi:type="device:MDRDeviceType"`) e validala con l'XSD. Dopo il primo caricamento riuscito in Swissdamed, sostituisci questa sezione con il template validato (come in `swissdamed-xml-legacy`).

Busta del messaggio (uguale al legacy, versione da verificare in `service/Message/MessageType.xsd`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<m:Push version="3.0.30"
  xmlns:m="https://ec.europa.eu/tools/eudamed/dtx/servicemodel/Message/v1"
  xmlns:s="https://ec.europa.eu/tools/eudamed/dtx/servicemodel/Service/v1"
  xmlns:device="https://ec.europa.eu/tools/eudamed/dtx/datamodel/Entity/Device/v1"
  xmlns:basicudi="https://ec.europa.eu/tools/eudamed/dtx/datamodel/Entity/Device/BasicUDI/v1"
  xmlns:udidi="https://ec.europa.eu/tools/eudamed/dtx/datamodel/Entity/UDIDI/v1"
  xmlns:commondi="https://ec.europa.eu/tools/eudamed/dtx/datamodel/Entity/Device/CommonDevice/v1"
  xmlns:links="https://ec.europa.eu/tools/eudamed/dtx/datamodel/Entity/Links/v1"
  xmlns:lsn="https://ec.europa.eu/tools/eudamed/dtx/datamodel/Entity/Common/LanguageSpecific/v1"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <!-- aggiungi i namespace MDR (es. mdrbasicudi, mdrudidi) presi dal sample ufficiale -->
  <m:conversationID>{UUID}</m:conversationID>
  <m:correlationID>{UUID}</m:correlationID>
  <m:creationDateTime>{YYYY-MM-DDTHH:MM:SS.ffffffZ}</m:creationDateTime>
  <m:messageID>{UUID}</m:messageID>
  <m:recipient>
    <m:node><s:nodeActorCode>EUDAMED</s:nodeActorCode><s:nodeID>eDelivery:EUDAMED</s:nodeID></m:node>
    <m:service><s:serviceID>DEVICE</s:serviceID><s:serviceOperation>POST</s:serviceOperation></m:service>
  </m:recipient>
  <m:payload>
    <!-- un device:Device per coppia Basic UDI-DI / UDI-DI -->
    <device:Device xsi:type="device:MDRDeviceType">
      <device:MDRBasicUDI> … </device:MDRBasicUDI>
      <device:MDRUDIDIData> … </device:MDRUDIDIData>
    </device:Device>
  </m:payload>
  <m:sender>
    <m:node><s:nodeActorCode>IT-MF-000027510</s:nodeActorCode></m:node>
    <m:service><s:serviceID>DEVICE</s:serviceID><s:serviceOperation>POST</s:serviceOperation></m:service>
  </m:sender>
</m:Push>
```

I blocchi `udidi:` comuni (identifier, status, additionalDescription, basicUDIIdentifier, MDNCodes, referenceNumber, sterile, sterilization, tradeNames, website, storageHandlingConditions, criticalWarnings, numberOfReuses, latex, reprocessed, clinicalSizes) hanno la stessa forma del template in `swissdamed-xml-legacy`; la loro posizione nella sequenza MDR va presa dall'XSD.

Differenze rispetto al legacy MDD:
- Per MDR `productionIdentifier` e `baseQuantity` **sono richiesti** (l'errore UDI-1053 vale solo per i legacy).
- `deviceCertificateLinks` obbligatorio per IIa/IIb/III (errore UDI-1096).
- Niente `eudi:applicableLegislation`: la legislazione è data dal tipo `MDRDeviceType`.

## 7. Errori Swissdamed già noti

| Errore | Regola |
|---|---|
| UDI-1096 | Classi IIa, IIb, III senza `deviceCertificateLinks` |
| UDI-1098 | `type` = SYSTEM / PROCEDURE_PACK senza `additionalDescription` |
| UDI-1017 / UDI-1019 | UDI-DI già presente in Swissdamed con campi non aggiornabili diversi (REF, clinical sizes, certificati): controllare il record esistente (bozza → cancellare; registrato → allineare) |

Aggiungi qui ogni nuovo errore incontrato, con la regola per evitarlo.

## 8. Procedura

1. Leggi tutte le pagine .mhtml EUDAMED e controlla che il totale coincida con "Showing … of N entries".
2. Escludi PTS (sezione 2) e applica il perimetro concordato.
3. Unisci Excel (UDI-DI) e template BUDI/Certificate (Basic UDI-DI). Produci `Verifica_Swissdamed_<fabbricante>.xlsx` con i fogli "Master" e "Discrepanze" (REF, Basic UDI-DI, trade name, EMDN, status diversi; GTIN duplicati; UDI-DI senza dati Excel; Basic UDI-DI senza template; classi I sterili).
4. Scarica in una cartella vuota `https://webgate.ec.europa.eu/eudamed-help/en/files/XSD%20schemas.zip` ed `EOs%20-%20XML%20samples.zip` (oppure chiedi a Fabio di caricarli se la rete li blocca). Aggiorna `m:Push version` secondo `service/Message/MessageType.xsd`.
5. Genera gli XML (nuovi UUID, creationDateTime UTC attuale), massimo 300 dispositivi per file, raggruppati per famiglia o per Basic UDI-DI.
6. Valida ogni file: `etree.XMLSchema(etree.parse('xsd/service/Message.xsd')).validate(etree.parse(file))` e stampa `error_log`. Controlla anche le regole della sezione 7.
7. Consegna con SendUserFile. Nome: `Swissdamed_MDR_<famiglia>_<n>.xml`.

## 9. Come caricarlo

Swissdamed → UDI Devices → upload XML (profilo "UDI Editor" sul mandato del fabbricante). I record entrano in bozza: controlla i campi, poi imposta lo stato di mercato. Se un oggetto va in errore, correggi solo quello e ricaricalo.

## 10. Output in chat

- Una riga per file: nome file – numero dispositivi – Basic UDI-DI incluse – esito validazione XSD.
- Elenco breve dei dispositivi esclusi o non generati, con il motivo (⚠️).
- Nessun riepilogo dell'intero file.
