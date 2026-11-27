import re, glob, uuid, datetime, sys
S=sys.argv[1]; D=S+'/out/td02/'
done={'8033178CANCPLANTF':['AX-30321'],'8033178CANCPLARBIS9F':['AR-11012']}   # gia' registrati in EUDAMED
files=sorted(glob.glob(D+'xml/*.xml'))
head=None; step1=[]; step2=[]; rep=[]
for f in files:
    s=open(f,encoding='utf-8').read()
    if head is None:
        head=s.split('<m:payload>')[0]+'<m:payload>\n'; tail='  </m:payload>'+s.split('</m:payload>')[1]
    devs=re.findall(r'    <device:Device .*?</device:Device>\n',s,re.S)
    b=re.search(r'<basicudi:identifier><commondi:DICode>([^<]+)',s).group(1)
    refs=[re.search(r'<udidi:referenceNumber>([^<]+)',d).group(1) for d in devs]
    if b in done: first=None; rest=[d for d,r in zip(devs,refs) if r not in done[b]]
    else: first=devs[0]; rest=devs[1:]
    if first: step1.append(first); rep.append((b,'STEP1',refs[0]))
    for d in rest:
        u=re.search(r'<device:MDRUDIDIData>(.*)</device:MDRUDIDIData>',d,re.S).group(1)
        step2.append(f'    <device:UDIDIData xsi:type="device:MDRUDIDIDataType">{u}</device:UDIDIData>\n')
        rep.append((b,'STEP2',re.search(r'<udidi:referenceNumber>([^<]+)',d).group(1)))
def write(fn,body,service):
    now=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    h=re.sub(r'<m:conversationID>[^<]*',f'<m:conversationID>{uuid.uuid4()}',head)
    h=re.sub(r'<m:correlationID>[^<]*',f'<m:correlationID>{uuid.uuid4()}',h)
    h=re.sub(r'<m:messageID>[^<]*',f'<m:messageID>{uuid.uuid4()}',h)
    h=re.sub(r'<m:creationDateTime>[^<]*',f'<m:creationDateTime>{now}',h)
    t=tail
    if service!='DEVICE':
        h=h.replace('<s:serviceID>DEVICE</s:serviceID>',f'<s:serviceID>{service}</s:serviceID>'); t=t.replace('<s:serviceID>DEVICE</s:serviceID>',f'<s:serviceID>{service}</s:serviceID>')
    open(D+'step/'+fn,'w',encoding='utf-8').write(h+''.join(body)+t)
write('STEP1_EUDAMED_TD02_BasicUDI_e_primo_UDI-DI.xml',step1,'DEVICE')
write('STEP2_EUDAMED_TD02_UDI-DI_per_Basic_esistenti.xml',step2,'UDI_DI')
import collections
c=collections.Counter((b,s) for b,s,_ in rep)
for k,v in sorted(c.items()): print(k,v)
print('STEP1',len(step1),'STEP2',len(step2))
open(D+'step/elenco.txt','w').write('\n'.join(f'{s}\t{b}\t{r}' for b,s,r in rep))
