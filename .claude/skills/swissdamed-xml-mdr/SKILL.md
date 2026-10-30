---
name: "swissdamed-xml-mdr"
description: "Crea i file XML (EUDAMED DTX, servizio DEVICE/POST, MDRDeviceType) per caricare in Swissdamed i dispositivi MDR già registrati in EUDAMED, partendo dall'elenco EUDAMED (Device details management, .mhtml) e dai file MIR-TEM-000588 / template BUDI / Certificate."
---

# XML MDR per Swissdamed

Usa questa skill quando Fabio chiede di "creare l'XML", "caricare con XML" o "esportare da EUDAMED a Swissdamed" dispositivi **MDR** (Regulation (EU) 2017/745, Basic UDI-DI GS1 tipo `8033178…`). Per i legacy MDD (EUDAMED DI `B-…`) usa `swissdamed-xml-legacy`; per la sola lista campi del form usa `swissdamed-registrazione`. Rispondi in italiano.

Formato: EUDAMED DTX, servizio `DEVICE` / `POST`, payload `device:Device` di tipo `device:MDRDeviceType`.

**Regola Swissdamed (guida ufficiale):** versioni XSD accettate 3.0.25, 3.0.28, 3.0.30, 3.0.32; ogni file deve contenere almeno una Basic UDI-DI con almeno un UDI-DI. **Verificato il 30.10.2026: Swissdamed accetta anche più Basic UDI-DI nello stesso file** (test con 2 Basic, poi file unico BRACKETS con 10 Basic / 26 UDI-DI, tutti passati). Quindi: un file per famiglia (Device name EUDAMED); un file singolo per Basic UDI-DI solo per test o correzioni.

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
- Status "Not intended for the EU market": **includili** (confermato da Fabio).
- Package UDI-DI (GTIN 1 / GTIN 3): **includili**.
- Un file **per famiglia** (Device name EUDAMED), con dentro tutte le sue Basic UDI-DI. Il primo caricamento di un nuovo tipo di dati (nuova classe, certificato, marcatura diretta, clinical size, sostanze) va prima testato con un file piccolo.
- Se una Basic UDI-DI ha UDI-DI bloccati, genera il file con quelli pronti ed elenca i mancanti (andranno aggiunti dopo, con un nuovo file della stessa Basic UDI-DI).
- Un UDI-DI EUDAMED senza riga Excel → non generarlo; elencalo come ⚠️ "mancano i dati di dettaglio".
- GTIN duplicato negli Excel (stesso GTIN su due REF) → usa la riga con il REF uguale a EUDAMED; se nessuna coincide, ⚠️ e non generarlo.

## 3. Dati fissi attore (Sorin Group Italia)

- Fabbricante: Sorin Group Italia S.r.l., SRN `IT-MF-000027510` (dall'intestazione "CURRENT ACTOR" di EUDAMED: rileggilo sempre dal file, se cambia attore cambia l'SRN).
- `basicudi:MFActorCode` = SRN del fabbricante; `m:sender/m:node/s:nodeActorCode` = SRN del fabbricante.
- Nessun Authorised Representative UE (fabbricante UE).
- Mandatario svizzero (CH-REP) già attivo in Swissdamed: CHRN dell'operatore `CHRN-AR-20001377`. Carica con il mandato di Sorin Group Italia.

## 4. Mappatura dei campi

### Basic UDI-DI (`device:MDRBasicUDI`)
| Campo XML | Fonte | Regola |
|---|---|---|
| identifier DICode / issuingEntityCode | EUDAMED Basic UDI-DI | `GS1` per i codici `8033178…` |
| riskClass | EUDAMED classe | Class I → `CLASS_I`, IIa → `CLASS_IIA`, IIb → `CLASS_IIB`, III → `CLASS_III`. Se il template BUDI dice IS/IM/IR e EUDAMED "Class I" → ⚠️ da verificare |
| modelName / name | EUDAMED "Device Name" | Alla lettera (es. `OXYGENATORS`). Model solo se presente in EUDAMED |
| MFActorCode | Sezione 3 | |
| deviceCertificateLinks | Template BUDI "Certificate Number:" + template Certificate | Obbligatorio per IIa, IIb, III (e Is/Im/Ir). Tipo: "Full QMS" → MDR Annex IX QMS; "Technical Documentation Review" → MDR Annex IX valutazione della documentazione tecnica (codici dall'XSD). Classe III: servono entrambi i certificati (QMS + TD); se il template ne riporta uno solo → ⚠️. Numero ON: TÜV SÜD = `0123`; DEKRA (certificati `2245978…`) = `0344`. Revisione e scadenza dai template Certificate (`000-Certificate_Import_template*.xlsx`) |
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
| website | Excel "URL for additional information" | Alla lettera (es. `www.sorinmanuals.com`): il campo non richiede `https://` |
| productionIdentifier | Excel "Device Control Aproach" | Lot Number / Serial Number / Manufacturing Date / Expiration date → un elemento per voce (codici dall'XSD) |
| baseQuantity | Excel "Device Count" | Di solito 1 |
| deviceMarking (direct marking) | EUDAMED "Is the device directly marked?" | Solo se EUDAMED = Yes. **Non usare** la colonna Excel "Is Direct Mark DI Number the same as Device?" da sola: vale "Yes" per i BRACKETS ma in EUDAMED sono "No" (errore scoperto il 30.10.2026, corretto con un re-upload). Dall'Excel serve "Direct Part Marking (DPM)?" = Yes |
| unitOfUse | Excel "Unit of Use DI" | Valorizzato con un DI reale → inviarlo; `1` o vuoto → non inviare (⚠️ se dubbio) |
| sterile | Excel "Is Device Packaged Sterile?" | `yes - sterile` → `true`, `no - not sterile` → `false` |
| sterilization | Excel "Does it need to be sterlized before use?" | `None Needed` → `false` |
| numberOfReuses | Excel "Single Use Device?" + "Maximum Number of Uses" | Single use Yes → `0`; No + numero → numero; No senza numero → `-1` |
| latex | Excel "Contains Latex?" | "does not Contain Latex" → `false` |
| reprocessed | Excel "Reprocessed Single Use" | NO → `false` |
| storageHandlingConditions | Excel "Storage and Handling Conditions" (separati da `;`) + colonne limiti | Una `condition` per voce, nello stesso ordine; tabella codici in sezione 5 |
| criticalWarnings | Excel "Critical Warning 1..5" (+ Value) | Tabella codici in sezione 5 |
| clinicalSizes | Excel colonne "EUDAMED Diameter (Outer/Inner)", "EUDAMED Length", "EUDAMED Diameter", "EUDAMED Angle", "EUDAMED Shank Length" | Una clinical size per colonna valorizzata; valori con virgola decimale → punto; ⚠️ da confermare con il record EUDAMED |
| substances CMR / endocrine | Excel "List of CMR Substances…", "List of Endocrine Substances…" | `CAS_7440-48-4` → CASCode `7440-48-4`; più valori separati da `;`. CMR richiede la categoria (sezione 5) |
| packages | Excel GTIN 1 (scatola intermedia) e GTIN 3 (scatola esterna) + quantità | Solo se il GTIN è valorizzato; quantità da "Each inside at the intermediate/external Box" |
| marketInfos | – | Non inviare per Swissdamed |
| Market, GUDID, FDA, GMDN, Business Unit/Line, date paesi UE | – | Ignora |

## 5. Codici di enumerazione (XSD 3.0.30, verificati)

- Risk class: `CLASS_I`, `CLASS_IIA`, `CLASS_IIB`, `CLASS_III`
- Status: `ON_THE_MARKET`, `NOT_INTENDED_FOR_EU_MARKET`, `NO_LONGER_PLACED_ON_THE_MARKET`
- Type of UDI-PI (`productionIdentifier`, lista separata da spazi): Lot Number → `BATCH_NUMBER`, Serial Number → `SERIALISATION_NUMBER`, Manufacturing Date → `MANUFACTURING_DATE`, Expiration date → `EXPIRATION_DATE`, Software → `SOFTWARE_IDENTIFICATION`
- Certificati MDR: Full QMS → `MDR_QUALITY_MANAGEMENT_SYSTEM`, Technical Documentation Review → `MDR_TECHNICAL_DOCUMENTATION`; altri: `MDR_QUALITY_ASSURANCE`, `MDR_PRODUCT_VERIFICATION`, `MDR_TYPE_EXAMINATION`. `NBActorCode` = 4 cifre (TÜV SÜD `0123`, DEKRA `0344`)
- Storage: `SHC001` Fragile, handle with care (anche "Fragile/Handle with care") · `SHC002` Keep away from sunlight (anche "Keep out of sunlight") · `SHC005` Keep dry · `SHC044` This way up · `SHC006`/`SHC007`/`SHC008`/`SHC009`/`SHC010` limiti temperatura/umidità/pressione (descrizione in `commondi:comments`) · `SHC036` Do not freeze · `SHC046` Special storage · `SHC099` Other
- Critical warnings: `CW010` Consult instructions for use · `CW009` Do not re-use · `CW001` Do not resterilize · `CW007` Do not use if package is damaged · `CW032` Do not use past indicated date · `CW020` Do not sterilize · `CW011` Caution · `CW008` Biological risks
- Clinical size type: `CST11` Diameter (outer) · `CST10` Diameter (inner) · `CST9` Diameter · `CST19` Length · `CST3` Angle · `CST999` OTHER (con `clinicalSizeDescription`). Unità: `MU50` mm · `MU105` gradi (°). Valore numerico → `xsi:type="commondi:ValueClinicalSizeType"` (value, valueUnit); testo (es. "Straight", "Fluted") → `commondi:TextClinicalSizeType` (text)
- Sostanze: CMR → `xsi:type="udidi:CMRSubstanceType"` con `CASCode` (formato `7440-48-4`) e `type` `CMR_1A`/`CMR_1B` (cobalto 7440-48-4 = `CMR_1B`, confermato da Fabio il 30.10.2026); endocrine → `xsi:type="udidi:EndocrineSubstanceType"` con `CASCode`

Per altri codici: `data/Entity/Device/CommonDeviceType.xsd` (storage, warning, clinical size), `RegulationDevice/UDIDIType.xsd` (PI, unità, sostanze), `Links/LinkType.xsd` (certificati).

## 6. Struttura XML (validata con XSD 3.0.30)

`MDRDeviceType` = esattamente **un** `MDRBasicUDI` + **un** `MDRUDIDIData`. Per rispettare la regola Swissdamed (una Basic UDI-DI per file) metti in `m:payload` un `device:Device` per ogni UDI-DI, ripetendo in ciascuno lo stesso blocco `MDRBasicUDI`. Busta, namespace e `sender` come in `swissdamed-xml-legacy` (senza `eudi`, `marketinfo`), con `s:nodeActorCode` del sender = SRN del fabbricante.

Ordine vincolante (elementi opzionali tra parentesi quadre):

```xml
<device:Device xsi:type="device:MDRDeviceType">
  <device:MDRBasicUDI>
    <basicudi:riskClass>CLASS_IIA</basicudi:riskClass>
    <basicudi:modelName><commondi:name>{DEVICE NAME EUDAMED}</commondi:name></basicudi:modelName>
    <basicudi:identifier><commondi:DICode>{BASIC UDI-DI}</commondi:DICode><commondi:issuingEntityCode>GS1</commondi:issuingEntityCode></basicudi:identifier>
    <basicudi:animalTissuesCells>false</basicudi:animalTissuesCells>
    <basicudi:humanTissuesCells>false</basicudi:humanTissuesCells>
    <basicudi:MFActorCode>IT-MF-000027510</basicudi:MFActorCode>
    [<basicudi:deviceCertificateLinks><links:deviceCertificateLink>
        <links:certificateNumber>G15 057574 0075</links:certificateNumber>
        <links:expiryDate>2030-08-27</links:expiryDate>
        <links:NBActorCode>0123</links:NBActorCode>
        <links:certificateRevisionNumber>0</links:certificateRevisionNumber>
        <links:certificateType>MDR_QUALITY_MANAGEMENT_SYSTEM</links:certificateType>
    </links:deviceCertificateLink></basicudi:deviceCertificateLinks>]   <!-- IIa/IIb/III; Classe III: un link per QMS e uno per TD -->
    <basicudi:humanProductCheck>false</basicudi:humanProductCheck>
    <basicudi:medicinalProductCheck>false</basicudi:medicinalProductCheck>
    <basicudi:type>DEVICE</basicudi:type>
    <commondi:active>false</commondi:active>
    <commondi:administeringMedicine>false</commondi:administeringMedicine>
    <commondi:implantable>false</commondi:implantable>
    <commondi:measuringFunction>false</commondi:measuringFunction>
    <commondi:reusable>false</commondi:reusable>
  </device:MDRBasicUDI>
  <device:MDRUDIDIData>
    <udidi:identifier>{UDI-DI, GS1}</udidi:identifier>
    <udidi:status><commondi:code>ON_THE_MARKET</commondi:code></udidi:status>
    [<udidi:additionalDescription>…</udidi:additionalDescription>]
    <udidi:basicUDIIdentifier>{BASIC UDI-DI, GS1}</udidi:basicUDIIdentifier>
    <udidi:MDNCodes>C03010104</udidi:MDNCodes>
    <udidi:productionIdentifier>BATCH_NUMBER MANUFACTURING_DATE EXPIRATION_DATE</udidi:productionIdentifier>
    <udidi:referenceNumber>{REF}</udidi:referenceNumber>
    <udidi:sterile>true</udidi:sterile>
    <udidi:sterilization>false</udidi:sterilization>
    <udidi:tradeNames><lsn:name><lsn:language>EN</lsn:language><lsn:textValue>{TRADE NAME}</lsn:textValue></lsn:name></udidi:tradeNames>
    [<udidi:website>www.sorinmanuals.com</udidi:website>]
    [<udidi:storageHandlingConditions><commondi:condition><commondi:storageHandlingConditionValue>SHC001</commondi:storageHandlingConditionValue></commondi:condition>…</udidi:storageHandlingConditions>]
    [<udidi:packages>
       <udidi:package>
         <udidi:identifier>{GTIN scatola, GS1}</udidi:identifier>
         <udidi:status><commondi:code>ON_THE_MARKET</commondi:code></udidi:status>
         <udidi:child>{DI del livello inferiore: UDI-DI o scatola intermedia}</udidi:child>
         <udidi:numberOfItems>6</udidi:numberOfItems>
       </udidi:package>
     </udidi:packages>]
    [<udidi:criticalWarnings><commondi:warning><commondi:warningValue>CW010</commondi:warningValue></commondi:warning>…</udidi:criticalWarnings>]
    <udidi:numberOfReuses>0</udidi:numberOfReuses>
    [<udidi:deviceMarking><udidi:directMarkingDI>{UDI-DI, GS1}</udidi:directMarkingDI></udidi:deviceMarking>]
    <udidi:baseQuantity>1</udidi:baseQuantity>
    <udidi:latex>false</udidi:latex>
    <udidi:reprocessed>false</udidi:reprocessed>
    [<udidi:substances><udidi:substance xsi:type="udidi:CMRSubstanceType"><udidi:names><lsn:name><lsn:language>ANY</lsn:language><lsn:textValue>Cobalt</lsn:textValue></lsn:name></udidi:names><udidi:CASCode>7440-48-4</udidi:CASCode><udidi:type>CMR_1B</udidi:type></udidi:substance></udidi:substances>]
    [<udidi:clinicalSizes><commondi:clinicalSize xsi:type="commondi:ValueClinicalSizeType"><commondi:clinicalSizeType>CST11</commondi:clinicalSizeType><commondi:value>7.0</commondi:value><commondi:valueUnit>MU50</commondi:valueUnit></commondi:clinicalSize></udidi:clinicalSizes>]
  </device:MDRUDIDIData>
</device:Device>
```

Imballi: GTIN 1 (scatola intermedia) → package con child = UDI-DI e numberOfItems = "Each inside at the intermediate Box"; GTIN 3 (scatola esterna) → package con child = GTIN 1 se esiste, altrimenti UDI-DI, e numberOfItems = "Each inside at the external Box". Status del package = status dell'UDI-DI.

Non inviare per Swissdamed: `marketInfos`, `secondaryIdentifier`, `productDesignerActor`, `annexXVI*`, `specialDevice` (se "0-N/A").

**Esiti Swissdamed (30.10.2026, mandato CHRN-AR-20001377-MF-00001):** passati VBT8 (IIa, certificato TÜV, 1 package), MICRO 40 e KIDS D130 (più UDI-DI per Basic), BRACKETS (Classe I, direct marking, 10 Basic in un file). Tieni lo stato dei caricamenti in `Stato_caricamento_Swissdamed.xlsx` (una riga per Basic UDI-DI: file, stato, data, note).

## 6b. Contesto: cannule Classe III e certificati DEKRA (TD01 / TD02 / TD03)

- EUDAMED **non permette di associare due certificati TD diversi alla stessa Basic UDI-DI** (confermato dall'Helpdesk EUDAMED, settembre 2026). Le cannule Sorin Group Italia avevano Basic UDI-DI condivise fra `2245978TD01` (cannule "MIR") e `2245978TD02` (cannule "LNUS"/ARV).
- Soluzione scelta (opzione 1, mail Luigi Vecchi → DEKRA del 01.09.2026): tenere i certificati separati e dare **nuove Basic UDI-DI "BIS"** alle famiglie del TD02. NoC DEKRA "NoC 14-26" (form 1993:10, firmato 13.09.2026): modifica amministrativa del TD02 (Annex IX, Classe III, Rule 7), rimozione di famiglie dismesse, correzione delle intended purpose. Organismo notificato DEKRA Certification B.V. `0344`.
- Mappatura TD02 (vecchia → nuova Basic UDI-DI):
  - `CANCARTESB` → `CANCARTBISM3` (EasyFlow Aortic 103-200, 103-300)
  - `CANCPLARTP` → `CANCPLARBIS9F` (AR-11112/11114/11116, AR-11012/11014/11016/11018, AR-17012/17014)
  - `CANCPLCSTX` → `CANCPLCSBISAC` (CP-21004…CP-22008, con palloncino); CP-11010…CP-12014 cancellati
  - `CANCVENOUX` → `CANCVENOBISWB` (single stage RV-400xx / RV-410xx), `CANCVENOBISDL` (dual/tri stage RDS-, RTS-), `CANCVENFUD` (RAP femoral 200-100/200-150); LRD- e RV-40012/40014/40038/41012/41014/41038 cancellati, aggiunto RV-40536
  - `CANCVENTV9` → `CANCVENBISPT` (vent catheters VT-)
  - Invariate nel TD02: `CANCARTFSD`, `CANCPLANTF`, `CANCPLREUG`, `CANCPLVCUQ` (solo VC-11100/VC-11110; CA-40030 cancellato)
- Le vecchie Basic UDI-DI restano al TD01 (template BUDI "Classe III - MIR").
- Conseguenza per Swissdamed: **le cannule entrano in Swissdamed solo dopo la riemissione del TD02 e la registrazione in EUDAMED** (scadenza EUDAMED citata: novembre). Fino ad allora non generare XML per le cannule, anche se i file MIR-TEM "Cannule" sono pronti.
- Classe III: in Swissdamed servono il certificato TD (TD01 o TD02, a seconda della Basic UDI-DI) e il certificato QMS `2245978CE01`.

## 7. Errori Swissdamed già noti

| Errore | Regola |
|---|---|
| UDI-1096 | Classi IIa, IIb, III senza `deviceCertificateLinks` |
| UDI-1017 (directMarkingDi) | La marcatura diretta **non è aggiornabile** in Swissdamed: un upload che la toglie o la cambia viene rifiutato. Va giusta al primo caricamento (vedi regola deviceMarking); per correggere bisogna fare discard dell'UDI-DI in Swissdamed e ricaricarlo (caso BRACKETS, 30.10.2026) |
| UDI-1070 | Sostanza CMR (e, per sicurezza, endocrine) senza nome: con CAS va aggiunto `<udidi:names><lsn:name><lsn:language>ANY</lsn:language><lsn:textValue>Cobalt</lsn:textValue></lsn:name></udidi:names>` prima di `CASCode` (una sola voce, lingua `ANY`). Nomi: 7440-48-4 Cobalt; 117-81-7 Bis(2-ethylhexyl) phthalate (DEHP); 85-68-7 Benzyl butyl phthalate (BBP) |
| UDI-1098 | `type` = SYSTEM / PROCEDURE_PACK senza `additionalDescription` |
| UDI-1017 / UDI-1019 | UDI-DI già presente in Swissdamed con campi non aggiornabili diversi (REF, clinical sizes, certificati): controllare il record esistente (bozza → cancellare; registrato → allineare) |

Aggiungi qui ogni nuovo errore incontrato, con la regola per evitarlo.

## 8. Procedura

1. Leggi tutte le pagine .mhtml EUDAMED e controlla che il totale coincida con "Showing … of N entries".
2. Escludi PTS (sezione 2) e applica il perimetro concordato.
3. Unisci Excel (UDI-DI) e template BUDI/Certificate (Basic UDI-DI). Produci `Verifica_Swissdamed_<fabbricante>.xlsx` con i fogli "Master" e "Discrepanze" (REF, Basic UDI-DI, trade name, EMDN, status diversi; GTIN duplicati; UDI-DI senza dati Excel; Basic UDI-DI senza template; classi I sterili).
4. Scarica in una cartella vuota `https://webgate.ec.europa.eu/eudamed-help/en/files/XSD%20schemas.zip` ed `EOs%20-%20XML%20samples.zip` (oppure chiedi a Fabio di caricarli se la rete li blocca). Aggiorna `m:Push version` secondo `service/Message/MessageType.xsd`.
5. Genera gli XML (nuovi UUID, creationDateTime UTC attuale), uno per famiglia. Prima di generarli mostra a Fabio la tabella dei trade name (UDI-DI, On EU / Not EU, classe, Basic UDI-DI, stato pronto/bloccato e motivo).
6. Valida ogni file: `etree.XMLSchema(etree.parse('xsd/service/Message.xsd')).validate(etree.parse(file))` e stampa `error_log`. Controlla anche le regole della sezione 7.
7. Consegna con SendUserFile. Nome: `Swissdamed_MDR_<DeviceName>.xml` (singola Basic: `Swissdamed_MDR_<BasicUDI-DI>_<DeviceName>.xml`).

## 9. Come caricarlo

Swissdamed → UDI Devices → upload XML (profilo "UDI Editor" sul mandato del fabbricante). I record entrano in bozza: controlla i campi, poi imposta lo stato di mercato. Se un oggetto va in errore, correggi solo quello e ricaricalo.

## 10. Output in chat

- Una riga per file: nome file – Basic UDI-DI – trade name inclusi – numero UDI-DI – esito validazione XSD.
- Elenco breve dei dispositivi esclusi o non generati, con il motivo (⚠️).
- Nessun riepilogo dell'intero file.
