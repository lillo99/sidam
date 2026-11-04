"""XML EUDAMED DTX (DEVICE/POST, MDRDeviceType) per le cannule TD02 pronte: un file per Basic UDI-DI."""
import openpyxl, re, uuid, datetime, collections, sys, os
import pandas as pd
from xml.sax.saxutils import escape as esc
from openpyxl.utils import column_index_from_string as CI
S = sys.argv[1]; OUT = S + '/out/td02/xml/'; os.makedirs(OUT, exist_ok=True)
SRN = 'IT-MF-000027510'
t = pd.read_excel(S + '/out/REF_TD02_completo.xlsx', 'REF TD02', dtype=str).set_index('REF')
ws = openpyxl.load_workbook(S + '/out/td02/MIR-TEM-000588_Rev04_-_Cannule_ARV_TD02_verificato.xlsm')['MAIN']
V = lambda r, c: ws.cell(r, CI(c)).value
def cd(b):
    d = [int(x) for x in b][::-1]; s = sum(v * (3 if i % 2 == 0 else 1) for i, v in enumerate(d)); return str((10 - s % 10) % 10)
BNAME = {'8033178CANCARTBISM3': 'Arterial Cannulae, EasyFlow Aortic', '8033178CANCARTFSD': 'Arterial Cannulae, EasyFlow Duo',
         '8033178CANCPLANTF': 'Cardioplegia Cannulae Aortic Root, Air aspirator', '8033178CANCPLARBIS9F': 'Cardioplegia Cannulae, Aortic Root',
         '8033178CANCPLCSBISAC': 'Cardioplegia Cannulae Coronary Artery Perfusion, Cannula with balloon',
         '8033178CANCPLREUG': 'Cardioplegia Cannulae, Retrograde', '8033178CANCPLVCUQ': 'Cardioplegia Cannulae Vessel, Vessel Cannulae',
         '8033178CANCVENBISPT': 'Vent Catheters', '8033178CANCVENFUD': 'Venous Cannulae, Remote Access Perfusion (RAP) femoral',
         '8033178CANCVENOBISDL': 'Venous Cannulae, Venous return', '8033178CANVENOBISWB': 'Venous Cannulae, Venous return (Right angle, wire reinforced)'}
CERTS = [('2245978TD02', '2029-10-01', '1', 'MDR_TECHNICAL_DOCUMENTATION'), ('2245978CE01', '2028-06-01', '1', 'MDR_QUALITY_MANAGEMENT_SYSTEM')]
CTRY = {'Austria': 'AT', 'Belgium': 'BE', 'Bulgaria': 'BG', 'Croatia': 'HR', 'Cyprus': 'CY', 'Denmark': 'DK', 'Czech Republic': 'CZ', 'Estonia': 'EE',
        'Finland': 'FI', 'France': 'FR', 'Germany': 'DE', 'Greece': 'EL', 'Hungary': 'HU', 'Iceland': 'IS', 'Ireland': 'IE', 'Italy': 'IT', 'Latvia': 'LV',
        'Liechtenstein': 'LI', 'Lithuania': 'LT', 'Luxembourg': 'LU', 'Malta': 'MT', 'Netherlands': 'NL', 'Norway': 'NO', 'Poland': 'PL', 'Portugal': 'PT',
        'Romania': 'RO', 'Slovakia': 'SK', 'Slovenia': 'SI', 'Spain': 'ES', 'Sweden': 'SE', 'Turkey': 'TR', 'Northern Ireland': 'XI'}
SHC = {'fragile, handle with care': 'SHC001', 'keep away from sunlight': 'SHC002', 'keep dry': 'SHC005', 'this way up': 'SHC044'}
CW = {'consult instructions for use': 'CW010', 'do not re-use': 'CW009', 'do not resterilize': 'CW001', 'do not use if package is damaged': 'CW007', 'do not use past indicated date': 'CW032'}
PI = {'lot number': 'BATCH_NUMBER', 'manufacturing date': 'MANUFACTURING_DATE', 'expiration date': 'EXPIRATION_DATE'}
SUB = {'117-81-7': ('Bis(2-ethylhexyl) phthalate (DEHP)', '204-211-0'), '84-75-3': ('Di-n-hexyl phthalate (DnHP)', '201-559-5'),
       '85-68-7': ('Benzyl butyl phthalate (BBP)', '201-622-7'), '80-05-7': ('Bisphenol A (BPA)', '201-245-8')}
CMR_CAT = {'80-05-7': 'CMR_1B'}
def di(tag, code): return f'<{tag}><commondi:DICode>{esc(code)}</commondi:DICode><commondi:issuingEntityCode>GS1</commondi:issuingEntityCode></{tag}>'
def txt(v):
    s = str(v).strip()
    return s.replace('.', ',') if re.fullmatch(r'[\d.]+ mm', s) else s
def basic(b):
    x = ['<basicudi:riskClass>CLASS_III</basicudi:riskClass>',
         f'<basicudi:modelName><commondi:name>{esc(BNAME[b])}</commondi:name></basicudi:modelName>', di('basicudi:identifier', b),
         '<basicudi:animalTissuesCells>false</basicudi:animalTissuesCells><basicudi:humanTissuesCells>false</basicudi:humanTissuesCells>',
         f'<basicudi:MFActorCode>{SRN}</basicudi:MFActorCode><basicudi:deviceCertificateLinks>']
    for n, e, rev, ty in CERTS:
        x.append(f'<links:deviceCertificateLink><links:certificateNumber>{n}</links:certificateNumber><links:expiryDate>{e}</links:expiryDate>'
                 f'<links:NBActorCode>0344</links:NBActorCode><links:certificateRevisionNumber>{rev}</links:certificateRevisionNumber>'
                 f'<links:certificateType>{ty}</links:certificateType></links:deviceCertificateLink>')
    x.append('</basicudi:deviceCertificateLinks><basicudi:humanProductCheck>false</basicudi:humanProductCheck>'
             '<basicudi:medicinalProductCheck>false</basicudi:medicinalProductCheck><basicudi:type>DEVICE</basicudi:type>'
             '<commondi:active>false</commondi:active><commondi:administeringMedicine>false</commondi:administeringMedicine>'
             '<commondi:implantable>false</commondi:implantable><commondi:measuringFunction>false</commondi:measuringFunction><commondi:reusable>false</commondi:reusable>')
    return '<device:MDRBasicUDI>' + ''.join(x) + '</device:MDRBasicUDI>'
def udi(r, ref, b, emdn):
    e = str(V(r, 'E')); g0 = '0' + e; g0 += cd(g0); g3 = '3' + e; g3 += cd(g3)
    assert g0 == t.loc[ref, 'GTIN UDI-DI (GTIN 0)'], ref
    st = '<udidi:status><commondi:code>ON_THE_MARKET</commondi:code></udidi:status>'
    pis = ' '.join(PI[p.strip().lower()] for p in V(r, 'M').split(';'))
    x = [di('udidi:identifier', g0), st, di('udidi:basicUDIIdentifier', b), f'<udidi:MDNCodes>{emdn}</udidi:MDNCodes>',
         f'<udidi:productionIdentifier>{pis}</udidi:productionIdentifier>', f'<udidi:referenceNumber>{esc(ref)}</udidi:referenceNumber>',
         '<udidi:sterile>true</udidi:sterile><udidi:sterilization>false</udidi:sterilization>',
         f'<udidi:tradeNames><lsn:name><lsn:language>EN</lsn:language><lsn:textValue>{esc(str(V(r, "Q")).strip())}</lsn:textValue></lsn:name></udidi:tradeNames>',
         f'<udidi:website>{esc(V(r, "FU"))}</udidi:website>', '<udidi:storageHandlingConditions>']
    x += [f'<commondi:condition><commondi:storageHandlingConditionValue>{SHC[c.strip().lower()]}</commondi:storageHandlingConditionValue></commondi:condition>'
          for c in V(r, 'ES').split(';') if c.strip()]
    x.append('</udidi:storageHandlingConditions>')
    x.append(f'<udidi:packages><udidi:package>{di("udidi:identifier", g3)}{st}{di("udidi:child", g0)}<udidi:numberOfItems>{int(V(r, "L"))}</udidi:numberOfItems></udidi:package></udidi:packages>')
    x.append('<udidi:criticalWarnings>' + ''.join(f'<commondi:warning><commondi:warningValue>{CW[V(r, c).strip().lower()]}</commondi:warningValue></commondi:warning>'
                                                for c in ('FZ', 'GB', 'GD', 'GF', 'GH') if V(r, c)) + '</udidi:criticalWarnings>')
    x.append('<udidi:numberOfReuses>0</udidi:numberOfReuses><udidi:marketInfos>')
    first = V(r, 'AH').strip()
    for c in [first] + [c.strip() for c in V(r, 'AI').split(';') if c.strip() and c.strip() != first]:
        x.append(f'<marketinfo:marketInfo><marketinfo:country>{CTRY[c]}</marketinfo:country>'
                 f'<marketinfo:originalPlacedOnTheMarket>{"true" if c == first else "false"}</marketinfo:originalPlacedOnTheMarket></marketinfo:marketInfo>')
    x.append('</udidi:marketInfos><udidi:baseQuantity>1</udidi:baseQuantity><udidi:latex>false</udidi:latex><udidi:reprocessed>false</udidi:reprocessed>')
    subs = []
    for cas in re.findall(r'CAS_([\d-]+)', V(r, 'GJ') or ''):
        n, ec = SUB[cas]
        subs.append(f'<udidi:substance xsi:type="udidi:CMRSubstanceType"><udidi:names><lsn:name><lsn:language>ANY</lsn:language><lsn:textValue>{esc(n)}</lsn:textValue></lsn:name></udidi:names>'
                    f'<udidi:CASCode>{cas}</udidi:CASCode><udidi:ECCode>{ec}</udidi:ECCode><udidi:type>{CMR_CAT[cas]}</udidi:type></udidi:substance>')
    for cas in re.findall(r'CAS_([\d-]+)', V(r, 'GK') or ''):
        n, ec = SUB[cas]
        subs.append(f'<udidi:substance xsi:type="udidi:EndocrineSubstanceType"><udidi:names><lsn:name><lsn:language>ANY</lsn:language><lsn:textValue>{esc(n)}</lsn:textValue></lsn:name></udidi:names>'
                    f'<udidi:CASCode>{cas}</udidi:CASCode><udidi:ECCode>{ec}</udidi:ECCode></udidi:substance>')
    if subs: x.append('<udidi:substances>' + ''.join(subs) + '</udidi:substances>')
    cs = [(c, code) for c, code in (('DU', 'CST11'), ('DX', 'CST9'), ('DW', 'CST19'), ('DY', 'CST3')) if V(r, c)]
    if cs:
        x.append('<udidi:clinicalSizes>' + ''.join(
            f'<commondi:clinicalSize xsi:type="commondi:TextClinicalSizeType"><commondi:clinicalSizeType>{code}</commondi:clinicalSizeType><commondi:text>{esc(txt(V(r, c)))}</commondi:text></commondi:clinicalSize>'
            for c, code in cs) + '</udidi:clinicalSizes>')
    return '<device:MDRUDIDIData>' + ''.join(x) + '</device:MDRUDIDIData>'
HEAD = open(S + '/scripts/gen_mdr.py').read().split("HEAD = '''")[1].split("'''")[0].replace(
    'xmlns:lsn=', 'xmlns:marketinfo="https://ec.europa.eu/tools/eudamed/dtx/datamodel/Entity/MktInfo/MarketInfo/v1"\n  xmlns:lsn=')
TAIL = f'''  </m:payload>
  <m:sender>
    <m:node><s:nodeActorCode>{SRN}</s:nodeActorCode></m:node>
    <m:service><s:serviceID>DEVICE</s:serviceID><s:serviceOperation>POST</s:serviceOperation></m:service>
  </m:sender>
</m:Push>
'''
groups = collections.defaultdict(list); skipped = []
for r in range(8, ws.max_row + 1):
    ref = V(r, 'B')
    if not ref: continue
    if not str(t.loc[ref, 'Stato dati']).startswith('Completo'): skipped.append((ref, t.loc[ref, 'Stato dati'])); continue
    groups[t.loc[ref, 'BASIC UDI-DI EUDAMED (da NoC 14-26)']].append((r, ref))
rows = []
for b, xs in sorted(groups.items()):
    bx = basic(b); devs = []
    for r, ref in sorted(xs, key=lambda z: z[1]):
        assert V(r, 'AF') == b, (ref, V(r, 'AF'), b)
        devs.append(f'    <device:Device xsi:type="device:MDRDeviceType">{bx}{udi(r, ref, b, t.loc[ref, "EMDN (MIS-001513)"])}</device:Device>\n')
        rows.append((b, ref))
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    fn = f'EUDAMED_MDR_TD02_{b}.xml'
    open(OUT + fn, 'w', encoding='utf-8').write(HEAD.format(c=uuid.uuid4(), r=uuid.uuid4(), t=now, m=uuid.uuid4()) + ''.join(devs) + TAIL)
    print(fn, len(xs))
print('totale', len(rows), 'esclusi', skipped)
