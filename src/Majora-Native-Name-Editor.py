"""International Majora native 128 KiB Flash name editor. Never overwrites input."""
import argparse, hashlib, json
from pathlib import Path
CHARS='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz -.'

def swap32(data):
    return b''.join(data[i:i+4][::-1] for i in range(0,len(data),4))

def checksum(block):
    b=bytearray(block); b[0x100a:0x100c]=b'\0\0'
    return sum(b)&65535

def valid(data,base,size,owl):
    b=data[base:base+size]
    return len(b)==size and b[0x24:0x2a]==b'ZELDA3' and b[0x23]==owl and int.from_bytes(b[0x100a:0x100c],'big')==checksum(b)

def decode(b):
    return ''.join(CHARS[v] if v<len(CHARS) else '[%02X]'%v for v in b).rstrip()

def inspect(raw):
    if len(raw)!=0x20000: raise ValueError('Se requiere Flash nativo completo de 131072 bytes; PNG, SRM y GCI no son entradas compatibles.')
    candidates=[]
    for order,data in [('big-endian',raw),('word32-reversed',swap32(raw))]:
        slots=[]
        for slot in range(2):
            bases=[(slot*0x4000,0x100c,0),(slot*0x4000+0x2000,0x100c,0),(0x8000+slot*0x8000,0x3ca0,1),(0xc000+slot*0x8000,0x3ca0,1)]
            records=[{'offset':base,'size':size,'owl':bool(owl),'valid':valid(data,base,size,owl),'name':decode(data[base+0x2c:base+0x34])} for base,size,owl in bases]
            slots.append(records)
        if any(r['valid'] and not r['owl'] for records in slots for r in records): candidates.append((order,data,slots))
    if len(candidates)!=1: raise ValueError('Estructura internacional o orden de bytes ambiguo/no reconocido. No se escribe nada.')
    return candidates[0]

def rename(raw,slot,name):
    if slot not in (1,2): raise ValueError('Partida: 1 o 2.')
    if not 1<=len(name)<=8 or not name.strip() or any(c not in CHARS for c in name): raise ValueError('Nombre: 1-8 caracteres A-Z, a-z, 0-9, espacio, guion o punto.')
    order,data,slots=inspect(raw)
    records=slots[slot-1]
    if not all(r['valid'] for r in records[:2]): raise ValueError('El guardado normal y su respaldo deben ser validos; no se reparan ni se reconstruyen automaticamente.')
    encoded=bytes(CHARS.index(c) for c in name.ljust(8))
    out=bytearray(data); changes=[]; allowed=set()
    for r in records:
        if not r['valid']: continue
        base=r['offset']; out[base+0x2c:base+0x34]=encoded
        out[base+0x100a:base+0x100c]=checksum(out[base:base+r['size']]).to_bytes(2,'big')
        allowed.update(range(base+0x2c,base+0x34));allowed.update(range(base+0x100a,base+0x100c))
        assert valid(out,base,r['size'],int(r['owl']))
        changes.append(dict(r,new_name=name))
    assert all(i in allowed for i,(a,b) in enumerate(zip(data,out)) if a!=b)
    result=bytes(out) if order=='big-endian' else swap32(out)
    return result,{'byte_order':order,'region':'International structure; exact region/revision requires external identification','slot':slot,'changes':changes,'input_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashlib.sha256(result).hexdigest(),'physical_validation':'PENDING'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path);p.add_argument('--slot',type=int,choices=[1,2]);p.add_argument('--name');p.add_argument('--output',type=Path);a=p.parse_args()
    raw=a.input.read_bytes()
    if a.name is None:
        order,data,slots=inspect(raw);print(json.dumps({'byte_order':order,'slots':slots},indent=2));return
    if a.slot is None or a.output is None: p.error('--name requires --slot and --output')
    if a.input.resolve()==a.output.resolve(): p.error('El original no se sobrescribe.')
    result,report=rename(raw,a.slot,a.name)
    with a.output.open('xb') as f:f.write(result)
    report_path=a.output.with_name(a.output.name+'.report.json')
    report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    assert a.input.read_bytes()==raw
    print(json.dumps(report,indent=2))
if __name__=='__main__': main()

