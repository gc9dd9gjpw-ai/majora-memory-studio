"""Conservative native owl recovery; no promotion to normal save."""
import importlib.util,sys,hashlib
from pathlib import Path
ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
s=importlib.util.spec_from_file_location('names',ROOT/'Majora-Native-Name-Editor.py');names=importlib.util.module_from_spec(s);s.loader.exec_module(names)
def progress(block):
 return dict(name=names.decode(block[0x2c:0x34]),hearts=int.from_bytes(block[0x34:0x36],'big')/16,masks=sum(v!=255 for v in block[0x88:0xa0]),day=int.from_bytes(block[0x18:0x1c],'big'),time=int.from_bytes(block[0xc:0xe],'big'),warp=block[0x44])
def consumed(block):
 if len(block)!=0x3ca0 or block[0x23]!=0 or block[0x24:0x2a]!=bytes(6):return False
 if int.from_bytes(block[0x100a:0x100c],'big')!=names.checksum(block):return False
 p=progress(block)
 return 3<=p['hearts']<=20 and 0<int.from_bytes(block[0x36:0x38],'big')<=int.from_bytes(block[0x34:0x36],'big') and 1<=p['day']<=3 and 0<=p['warp']<10 and all(v<len(names.CHARS) for v in block[0x2c:0x34])
def overview(raw,slot):
 if slot not in (1,2):raise ValueError('Invalid slot')
 order,data,slots=names.inspect(raw);records=slots[slot-1];result=[]
 for record in records:
  base=record['offset'];block=data[base:base+record['size']]
  state='valid' if record['valid'] else 'consumed' if record['owl'] and consumed(block) else 'empty' if block[:0x100c] in (bytes(0x100c),bytes([255])*0x100c) else 'invalid'
  result.append(dict(record,state=state,progress=progress(block) if state in ('valid','consumed') else None))
 pair=result[2:];a=pair[0]['offset'];b=pair[1]['offset']
 eligible=all(r['valid'] for r in records[:2]) and all(r['state']=='consumed' for r in pair) and data[a:a+0x3ca0]==data[b:b+0x3ca0]
 return dict(order=order,records=result,recovery_available=eligible)
def recover(raw,slot):
 info=overview(raw,slot)
 if not info['recovery_available']:raise ValueError('No matching checksum-valid consumed owl pair; recovery blocked.')
 order,data,slots=names.inspect(raw);out=bytearray(data);allowed=set()
 for record in slots[slot-1][2:]:
  base=record['offset'];out[base+0x23]=1;out[base+0x24:base+0x2a]=b'ZELDA3'
  out[base+0x100a:base+0x100c]=names.checksum(out[base:base+0x3ca0]).to_bytes(2,'big')
  assert names.valid(out,base,0x3ca0,1)
  assert progress(out[base:base+0x3ca0])==progress(data[base:base+0x3ca0])
  allowed.add(base+0x23);allowed.update(range(base+0x24,base+0x2a));allowed.update(range(base+0x100a,base+0x100c))
 assert all(i in allowed for i,(a,b) in enumerate(zip(data,out)) if a!=b)
 result=bytes(out) if order=='big-endian' else names.swap32(out)
 return result,dict(operation='reactivate_consumed_owl',slot=slot,progress_preserved=True,normal_save_unchanged=True,input_sha256=hashlib.sha256(raw).hexdigest(),output_sha256=hashlib.sha256(result).hexdigest(),validation='Physical method validated for user PAL 1.1; other profiles pending')
