"""International native equipment fields confirmed in decomp; physical editing pending."""
import importlib.util,sys,hashlib
from pathlib import Path
ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
s=importlib.util.spec_from_file_location('native_names',ROOT/'Majora-Native-Name-Editor.py');names=importlib.util.module_from_spec(s);s.loader.exec_module(names)
def read(block):
 eq=int.from_bytes(block[0x6c:0x6e],'big')
 return dict(sword=eq&15,shield=(eq>>4)&15,durability=int.from_bytes(block[0x3c:0x3e],'big'),defense=block[0x42],defense_hearts=block[0xd3],human_B=block[0x4c])
def edit(raw,slot,changes):
 if slot not in (1,2):raise ValueError('Invalid slot')
 if set(changes)-{'sword','shield','defense','durability'}:raise ValueError('Unknown equipment field')
 for k,v in changes.items():
  if type(v)!=int or v not in (range(1,4) if k=='sword' else range(3) if k=='shield' else range(2) if k=='defense' else range(1,101)):raise ValueError('Invalid equipment value')
 order,data,slots=names.inspect(raw);records=slots[slot-1]
 if not all(r['valid'] for r in records[:2]):raise ValueError('Valid normal and backup saves required')
 out=bytearray(data);allowed=set();report=[]
 for r in records:
  if not r['valid']:continue
  base=r['offset'];before=read(data[base:base+r['size']]);eq=int.from_bytes(out[base+0x6c:base+0x6e],'big')
  def put(off,values):
   out[base+off:base+off+len(values)]=values;allowed.update(range(base+off,base+off+len(values)))
  if 'sword' in changes:
   sword=changes['sword'];eq=(eq&~15)|sword;put(0x4c,bytes([0x4c+sword]))
   if sword==2 and before['sword']!=2:put(0x3c,(100).to_bytes(2,'big'))
  if 'shield' in changes:eq=(eq&~0xf0)|(changes['shield']<<4)
  if 'sword' in changes or 'shield' in changes:put(0x6c,eq.to_bytes(2,'big'))
  if 'durability' in changes:
   if eq&15!=2:raise ValueError('Durability is only editable for Razor Sword')
   put(0x3c,changes['durability'].to_bytes(2,'big'))
  if 'defense' in changes:
   put(0x42,bytes([changes['defense']]));put(0xd3,bytes([20 if changes['defense'] else 0]))
  put(0x100a,names.checksum(out[base:base+r['size']]).to_bytes(2,'big'))
  assert names.valid(out,base,r['size'],int(r['owl']))
  report.append(dict(offset=hex(base),owl=r['owl'],before=before,after=read(out[base:base+r['size']])))
 assert all(i in allowed for i,(a,b) in enumerate(zip(data,out)) if a!=b)
 result=bytes(out) if order=='big-endian' else names.swap32(out)
 return result,dict(operation='native_equipment',slot=slot,records=report,input_sha256=hashlib.sha256(raw).hexdigest(),output_sha256=hashlib.sha256(result).hexdigest(),validation='CONFIRMED IN DECOMP; software checks only; physical validation PENDING')
