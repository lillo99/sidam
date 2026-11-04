"""Converte l'export JSON di EUDAMED (eudamed_export.js) in XML DTX per Swissdamed.

Uso: python3 json2xml.py export.json out.xml SRN [--cert BASIC=NUM;TIPO;NB;REV;SCADENZA ...] [--only BASIC,BASIC]
Un file con tutte le Basic UDI-DI richieste (Swissdamed accetta più Basic UDI-DI per file).
I certificati vengono da EUDAMED (deviceCertificateInfoList); --cert li aggiunge o li completa.
"""
import json, sys, uuid, datetime, argparse
from xml.sax.saxutils import escape as esc

RISK = {'class-i': 'CLASS_I', 'class-iia': 'CLASS_IIA', 'class-iib': 'CLASS_IIB', 'class-iii': 'CLASS_III'}
STATUS = {'on-the-market': 'ON_THE_MARKET', 'not-intended-for-eu-market': 'NOT_INTENDED_FOR_EU_MARKET',
          'no-longer-placed-on-the-market': 'NO_LONGER_PLACED_ON_THE_MARKET'}
CERT = {'technical-documentation': 'MDR_TECHNICAL_DOCUMENTATION', 'quality-management-system': 'MDR_QUALITY_MANAGEMENT_SYSTEM',
        'quality-assurance': 'MDR_QUALITY_ASSURANCE', 'product-verification': 'MDR_PRODUCT_VERIFICATION', 'type-examination': 'MDR_TYPE_EXAMINATION'}
PI = [('batchNumber', 'BATCH_NUMBER'), ('serializationNumber', 'SERIALISATION_NUMBER'), ('manufacturingDate', 'MANUFACTURING_DATE'),
      ('expirationDate', 'EXPIRATION_DATE'), ('softwareIdentification', 'SOFTWARE_IDENTIFICATION')]
tail = lambda c: (c or {}).get('code', '').split('.')[-1]
b = lambda v: 'true' if v else 'false'


def di(tag, code):
    return f'<{tag}><commondi:DICode>{esc(code)}</commondi:DICode><commondi:issuingEntityCode>GS1</commondi:issuingEntityCode></{tag}>'


def txt(tag, text, lang='EN'):
    return f'<{tag}><lsn:name><lsn:language>{lang}</lsn:language><lsn:textValue>{esc(text)}</lsn:textValue></lsn:name></{tag}>'


def basic_xml(bd, srn, extra_certs):
    x = [f"<basicudi:riskClass>{RISK[tail(bd['riskClass'])]}</basicudi:riskClass>"]
    if bd.get('deviceModel') and bd.get('deviceName'):
        x.append(f"<basicudi:modelName><commondi:model>{esc(bd['deviceModel'])}</commondi:model><commondi:name>{esc(bd['deviceName'])}</commondi:name></basicudi:modelName>")
    elif bd.get('deviceName'):
        x.append(f"<basicudi:modelName><commondi:name>{esc(bd['deviceName'])}</commondi:name></basicudi:modelName>")
    else:
        x.append(f"<basicudi:model>{esc(bd['deviceModel'])}</basicudi:model>")
    x += [di('basicudi:identifier', bd['basicUdi']['code']),
          f"<basicudi:animalTissuesCells>{b(bd['animalTissues'])}</basicudi:animalTissuesCells>",
          f"<basicudi:humanTissuesCells>{b(bd['humanTissues'])}</basicudi:humanTissuesCells>",
          f"<basicudi:MFActorCode>{srn}</basicudi:MFActorCode>"]
    certs = {}
    for c in bd.get('deviceCertificateInfoList') or []:
        certs[c['certificateNumber']] = dict(num=c['certificateNumber'], typ=CERT[tail(c['certificateType'])], nb=c['notifiedBody']['srn'],
                                             rev=c.get('certificateRevision'), exp=(c.get('certificateExpiry') or '')[:10] or None)
    for c in extra_certs:
        certs[c['num']] = {**certs.get(c['num'], {}), **{k: v for k, v in c.items() if v}}
    if certs:
        x.append('<basicudi:deviceCertificateLinks>' + ''.join(
            '<links:deviceCertificateLink>' + f"<links:certificateNumber>{esc(c['num'])}</links:certificateNumber>"
            + (f"<links:expiryDate>{c['exp']}</links:expiryDate>" if c.get('exp') else '')
            + f"<links:NBActorCode>{c['nb']}</links:NBActorCode>"
            + (f"<links:certificateRevisionNumber>{esc(str(c['rev']))}</links:certificateRevisionNumber>" if c.get('rev') not in (None, '') else '')
            + f"<links:certificateType>{c['typ']}</links:certificateType></links:deviceCertificateLink>" for c in certs.values())
            + '</basicudi:deviceCertificateLinks>')
    x += [f"<basicudi:humanProductCheck>{b(bd['humanProduct'])}</basicudi:humanProductCheck>",
          f"<basicudi:medicinalProductCheck>{b(bd['medicinalProduct'])}</basicudi:medicinalProductCheck>",
          f"<basicudi:type>{'DEVICE' if bd.get('deviceCriterion') == 'STANDARD' else bd.get('basicUdiType') or 'DEVICE'}</basicudi:type>",
          f"<commondi:active>{b(bd['active'])}</commondi:active>",
          f"<commondi:administeringMedicine>{b(bd['administeringMedicine'])}</commondi:administeringMedicine>",
          f"<commondi:implantable>{b(bd['implantable'])}</commondi:implantable>",
          f"<commondi:measuringFunction>{b(bd['measuringFunction'])}</commondi:measuringFunction>",
          f"<commondi:reusable>{b(bd['reusable'])}</commondi:reusable>"]
    return '<device:MDRBasicUDI>' + ''.join(x) + '</device:MDRBasicUDI>'


def packages(root, status):
    out = []
    def walk(node):
        for c in node.get('containedItems') or []:
            out.append((c['itemIdentifier']['code'], node['itemIdentifier']['code'], c['numberOfItems'],
                        STATUS.get(tail(c.get('itemStatus')).replace('contained-item-status', ''), status)))
            walk(c)
    if root:
        walk(root)
    return out


def subst(s, xsitype, cmr_type=None):
    name = (s.get('name') or {}).get('texts') or []
    x = f'<udidi:substance xsi:type="udidi:{xsitype}">'
    if name:
        x += txt('udidi:names', name[0]['text'], 'ANY')
    if s.get('casNumber'):
        x += f"<udidi:CASCode>{s['casNumber']}</udidi:CASCode>"
    if s.get('ecNumber'):
        x += f"<udidi:ECCode>{s['ecNumber']}</udidi:ECCode>"
    if cmr_type:
        x += f'<udidi:type>{cmr_type}</udidi:type>'
    return x + '</udidi:substance>'


def udi_xml(t, basic_code):
    st = STATUS[tail(t['deviceStatus']['type'])]
    x = [di('udidi:identifier', t['primaryDi']['code']), f'<udidi:status><commondi:code>{st}</commondi:code></udidi:status>']
    ad = ((t.get('additionalDescription') or {}).get('texts') or [])
    if ad:
        x.append('<udidi:additionalDescription>' + ''.join(
            f"<lsn:name><lsn:language>{(a.get('language') or {}).get('isoCode', 'en').upper()}</lsn:language><lsn:textValue>{esc(a['text'])}</lsn:textValue></lsn:name>"
            for a in ad) + '</udidi:additionalDescription>')
    x += [di('udidi:basicUDIIdentifier', basic_code),
          f"<udidi:MDNCodes>{' '.join(c['code'] for c in t['cndNomenclatures'])}</udidi:MDNCodes>",
          f"<udidi:productionIdentifier>{' '.join(v for k, v in PI if (t.get('udiPiType') or {}).get(k))}</udidi:productionIdentifier>",
          f"<udidi:referenceNumber>{esc(t['reference'])}</udidi:referenceNumber>",
          f"<udidi:sterile>{b(t['sterile'])}</udidi:sterile>",
          f"<udidi:sterilization>{b(t['sterilization'])}</udidi:sterilization>"]
    tn = (t.get('tradeName') or {}).get('texts') or []
    if tn:
        x.append(txt('udidi:tradeNames', tn[0]['text']))
    if t.get('additionalInformationUrl'):
        x.append(f"<udidi:website>{esc(t['additionalInformationUrl'])}</udidi:website>")
    sh = t.get('storageHandlingConditions') or []
    if sh:
        x.append('<udidi:storageHandlingConditions>' + ''.join(
            '<commondi:condition>' + (txt('commondi:comments', s['description'], 'ANY') if s.get('description') else '')
            + f"<commondi:storageHandlingConditionValue>{s['typeCode'].split('.')[-1]}</commondi:storageHandlingConditionValue></commondi:condition>"
            for s in sh) + '</udidi:storageHandlingConditions>')
    pk = packages(t.get('containedItem'), st)
    if pk:
        x.append('<udidi:packages>' + ''.join(
            f'<udidi:package>{di("udidi:identifier", g)}<udidi:status><commondi:code>{s}</commondi:code></udidi:status>'
            f'{di("udidi:child", ch)}<udidi:numberOfItems>{n}</udidi:numberOfItems></udidi:package>' for g, ch, n, s in pk) + '</udidi:packages>')
    cw = t.get('criticalWarnings') or []
    if cw:
        x.append('<udidi:criticalWarnings>' + ''.join(
            '<commondi:warning>' + (txt('commondi:comments', w['description'], 'ANY') if w.get('description') else '')
            + f"<commondi:warningValue>{w['typeCode'].split('.')[-1]}</commondi:warningValue></commondi:warning>" for w in cw)
            + '</udidi:criticalWarnings>')
    reuses = 0 if t.get('singleUse') else (t['maxNumberOfReuses'] if t.get('maxNumberOfReusesApplicable') and t.get('maxNumberOfReuses') is not None else -1)
    x.append(f'<udidi:numberOfReuses>{reuses}</udidi:numberOfReuses>')
    if t.get('directMarking'):
        dm = (t.get('directMarkingDi') or {}).get('code') or t['primaryDi']['code']
        x.append('<udidi:deviceMarking>' + di('udidi:directMarkingDI', dm) + '</udidi:deviceMarking>')
    x.append(f"<udidi:baseQuantity>{t.get('baseQuantity') or 1}</udidi:baseQuantity>")
    x += [f"<udidi:latex>{b(t['latex'])}</udidi:latex>", f"<udidi:reprocessed>{b(t['reprocessed'])}</udidi:reprocessed>"]
    subs = [subst(s, 'CMRSubstanceType', 'CMR_' + str(s.get('cmrType') or s.get('substanceCategory') or '1B').upper().replace('CMR_', ''))
            for s in t.get('cmrSubstances') or []]
    subs += [subst(s, 'EndocrineSubstanceType') for s in t.get('endocrineDisruptingSubstances') or []]
    if subs:
        x.append('<udidi:substances>' + ''.join(subs) + '</udidi:substances>')
    cs = []
    for c in t.get('clinicalSizes') or []:
        typ = c['type']['code'].split('.')[-1]
        desc = ''
        if c.get('clinicalSizeTypeDescription'):
            desc = txt('commondi:clinicalSizeDescription', c['clinicalSizeTypeDescription']['texts'][0]['text'])
        prec = tail(c['precision'])
        if prec == 'text':
            cs.append(f'<commondi:clinicalSize xsi:type="commondi:TextClinicalSizeType"><commondi:clinicalSizeType>{typ}</commondi:clinicalSizeType>{desc}<commondi:text>{esc(c["text"])}</commondi:text></commondi:clinicalSize>')
        elif prec == 'range':
            cs.append(f'<commondi:clinicalSize xsi:type="commondi:RangeClinicalSizeType"><commondi:clinicalSizeType>{typ}</commondi:clinicalSizeType>{desc}<commondi:maximum>{c["maximumValue"]}</commondi:maximum><commondi:minimum>{c["minimumValue"]}</commondi:minimum><commondi:valueUnit>{tail(c["metricOfMeasurement"])}</commondi:valueUnit></commondi:clinicalSize>')
        else:
            cs.append(f'<commondi:clinicalSize xsi:type="commondi:ValueClinicalSizeType"><commondi:clinicalSizeType>{typ}</commondi:clinicalSizeType>{desc}<commondi:value>{c["value"]}</commondi:value><commondi:valueUnit>{tail(c["metricOfMeasurement"])}</commondi:valueUnit></commondi:clinicalSize>')
    if cs:
        x.append('<udidi:clinicalSizes>' + ''.join(cs) + '</udidi:clinicalSizes>')
    return '<device:MDRUDIDIData>' + ''.join(x) + '</device:MDRUDIDIData>'


HEAD = '''<?xml version="1.0" encoding="UTF-8"?>
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
  <m:conversationID>{c}</m:conversationID>
  <m:correlationID>{r}</m:correlationID>
  <m:creationDateTime>{t}</m:creationDateTime>
  <m:messageID>{m}</m:messageID>
  <m:recipient>
    <m:node><s:nodeActorCode>EUDAMED</s:nodeActorCode><s:nodeID>eDelivery:EUDAMED</s:nodeID></m:node>
    <m:service><s:serviceID>DEVICE</s:serviceID><s:serviceOperation>POST</s:serviceOperation></m:service>
  </m:recipient>
  <m:payload>
'''
TAIL = '''  </m:payload>
  <m:sender>
    <m:node><s:nodeActorCode>{srn}</s:nodeActorCode></m:node>
    <m:service><s:serviceID>DEVICE</s:serviceID><s:serviceOperation>POST</s:serviceOperation></m:service>
  </m:sender>
</m:Push>
'''

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('export'); ap.add_argument('out'); ap.add_argument('srn')
    ap.add_argument('--cert', action='append', default=[], help='BASIC=NUM;TIPO;NB;REV;SCADENZA')
    ap.add_argument('--only', default='')
    a = ap.parse_args()
    d = json.load(open(a.export))
    only = set(filter(None, a.only.split(',')))
    extra = {}
    for c in a.cert:
        bc, v = c.split('=', 1)
        num, typ, nb, rev, exp = (v.split(';') + [''] * 5)[:5]
        extra.setdefault(bc, []).append(dict(num=num, typ=typ, nb=nb, rev=rev, exp=exp))
    devs = []
    for x in sorted(d['devices'], key=lambda x: (x['basic']['basicUdi']['code'], x['detail']['reference'])):
        bc = x['basic']['basicUdi']['code']
        if only and bc not in only:
            continue
        devs.append(f'    <device:Device xsi:type="device:MDRDeviceType">{basic_xml(x["basic"], a.srn, extra.get(bc, []))}{udi_xml(x["detail"], bc)}</device:Device>\n')
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    open(a.out, 'w', encoding='utf-8').write(HEAD.format(c=uuid.uuid4(), r=uuid.uuid4(), t=now, m=uuid.uuid4()) + ''.join(devs) + TAIL.format(srn=a.srn))
    print(a.out, len(devs), 'device')
