"""Documented international Memory edits, experimental runtime scene reload."""
import importlib.util,sys,zlib
from pathlib import Path
ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
s=importlib.util.spec_from_file_location('collection_location',ROOT/'Majora-regional-collections.py');loc=importlib.util.module_from_spec(s);s.loader.exec_module(loc)
def find_play(ram):
 import struct
 candidates=[]
 for index,(pointer,) in enumerate(struct.iter_unpack('>I',ram)):
  b=index*4-0x800
  if b<0 or b+0x19258>len(ram) or pointer!=0x80000000+b+0x220:continue
  u=lambda off,n=4:int.from_bytes(ram[off:off+n],'big')
  if u(b+0x2ac)!=0x80000000+b or ram[b+0x9b]!=1 or not 0<=u(b+0xa4,2)<120:continue
  if not all(0x80000000<=u(b+o)<0x80800000 for o in (4,8)):continue
  gfx=u(b)
  if gfx and not 0x80000000<=gfx<0x80800000:continue
  ptr=u(b+0x1ccc);player=ptr-0x80000000
  if u(b+0x1cc8)!=1 or not 0<=player<=len(ram)-0x144:continue
  if u(player,2)!=0 or u(player+2,1)!=2:continue
  if not all(0x80000000<=u(player+o)<0x80800000 for o in (0x134,0x138)):continue
  candidates.append((b,u(b+0xa4,2)))
 if len(candidates)!=1:raise ValueError('Active PlayState/player not uniquely identified')
 return candidates[0]
def apply(data,report,options,catalog):
 if not options:return data,[]
 if set(options)-{'collections','photo','spiderOrder','sword','shield','form','clock'}:raise ValueError('Unknown advanced edit')
 p=report['detected_profile']
 if (p['cartridge'],p['revision']) not in [('NZSJ',0),('NZSJ',1),('NZSP',0),('NZSP',1),('NZSE',0)]:raise ValueError('progressProfile')
 start=int(report['rdram_png_offset'],16);base=int(report['save_ram_offset'],16);b=start+base;out=bytearray(data);allowed=set();changes=[]
 def put(label,off,raw):
  at=start+off;before=bytes(out[at:at+len(raw)])
  if before!=raw:out[at:at+len(raw)]=raw;allowed.update(range(at,at+len(raw)));changes.append(dict(campo=label,offset_png=hex(at),antes=before.hex(),despues=raw.hex()))
 def value(off,n=4):return int.from_bytes(out[start+off:start+off+n],'big')
 def setv(label,off,n,v):put(label,off,v.to_bytes(n,'big'))
 def flag(label,off,n,mask,on):setv(label,off,n,(value(off,n)|mask) if on else (value(off,n)&~mask))
 reload=any(k in options for k in ('sword','shield','form','clock'))
 play=scene=None
 if reload or options.get('collections'):
  play,scene=find_play(bytes(out[start:start+0x800000]))
 if reload:
  runtime_spec=importlib.util.spec_from_file_location('active_runtime',ROOT/'Majora-Revision-Runtime.py');runtime=importlib.util.module_from_spec(runtime_spec);runtime_spec.loader.exec_module(runtime)
  _,cfg,_,ram,play,_=runtime.context(report['name'],data);runtime.safe_gameplay(ram,play,cfg);rt=cfg['runtime']
  for off,n in [(rt['pause_state'],2),(rt['transition_trigger'],1),(rt['transition_mode'],1),(rt['room_status'],1),(rt['song_cutscene'],1)]:
   if value(play+off,n):raise ValueError('Close pause/dialog/transition before changing character or clock')
  entrance=value(base,4)
  if not 0<=entrance<=65535:raise ValueError('Current entrance cannot be reloaded')
  setv('Scene reload entrance',play+rt['next_entrance'],2,entrance);setv('Scene reload trigger',play+rt['transition_trigger'],1,20);setv('Scene reload fade',play+rt['transition_type'],1,2)
 eq=value(base+0x6c,2)
 if 'sword' in options:
  v=options['sword']
  if type(v)!=int or not 1<=v<=3:raise ValueError('Sword range 1–3')
  eq=(eq&~15)|v;setv('Sword B item',base+0x4c,1,0x4c+v+(0x1f if p['layout'].startswith('jp-') else 0))
  if v==2:setv('Razor durability',base+0x3c,2,100)
 if 'shield' in options:
  v=options['shield']
  if type(v)!=int or not 0<=v<=2:raise ValueError('Shield range 0–2')
  eq=(eq&~0xf0)|(v<<4)
 if 'sword' in options or 'shield' in options:setv('Equipment',base+0x6c,2,eq)
 if 'form' in options:
  v=options['form']
  if type(v)!=int or not 1<=v<=4:raise ValueError('Form must be Goron/Zora/Deku/Human; Fierce Deity is context-sensitive')
  setv('Player form',base+0x20,1,v)
 if 'clock' in options:
  day,hour,minute=options['clock']
  if any(type(v)!=int for v in (day,hour,minute)) or not 1<=day<=3 or not 0<=hour<=23 or not 0<=minute<=59:raise ValueError('Clock range')
  t=((hour*60+minute)*65536)//1440
  setv('Cycle day',base+0x18,4,day);setv('Event day count',base+0x1c,4,day);setv('Internal time',base+0xc,2,t);setv('Night flag',base+0x10,4,int(hour<6 or hour>=18))
 def sf(label,target,field,mask,on):
  flag(label,base+0xf8+target*28+loc.PERM[field],4,mask,on)
  canonical=target if field=='collectible' and target==0x18 else loc.original(target)
  flag(label,base+p['cycle_scene_offset']+canonical*20+loc.PERM[field],4,mask,on)
  active=scene if field=='collectible' and scene==0x18 else loc.original(scene)
  if canonical==active:flag(label,play+0x1e58+loc.ACTIVE[field],4,mask,on)
 for key,on in options.get('collections',{}).items():
  if type(on)!=int or on not in (0,1):raise ValueError('Collection values must be 0/1')
  kind,index=key.split(':');index=int(index)
  if kind=='heart' and 0<=index<len(catalog['hearts']):
   h=catalog['hearts'][index];off=h['offset'];mask=1<<h['bit']
   if off>=0xef8:flag('Heart '+str(index),base+off,1,mask,on)
   else:
    target=(off-0xf8)//28;sub=(off-0xf8)%28;field=next(k for k,v in loc.PERM.items() if v==sub//4*4);sf('Heart '+str(index),target,field,mask<<((3-sub%4)*8),on)
  elif kind=='boss' and 0<=index<len(catalog['bosses']):sf('Boss heart '+str(index),catalog['bosses'][index],'collectible',1<<31,on)
  elif kind=='fairy' and 0<=index<len(catalog['fairies']):
   f=catalog['fairies'][index];sf('Fairy '+str(index),f['scene'],f['field'],1<<f['flag'],on)
  elif kind=='skull' and 0<=index<60:
   group=index//30;entry=next(e for e in catalog['skulls'] if e['group']==group);sf('Skull '+str(index),entry['scene'],'chest',1<<(index%30),on)
  else:raise ValueError('Unknown collection')
 if any(k.startswith(('heart:','boss:')) for k in options.get('collections',{})):
  hearts=sum(bool(value(base+h['offset'],1)&(1<<h['bit'])) for h in catalog['hearts']);bosses=sum(bool(value(base+0xf8+s*28+16)&0x80000000) for s in catalog['bosses']);cap=min(320,(3+hearts//4+bosses)*16)
  setv('Consistent heart capacity',base+0x34,2,cap);setv('Current health clamped',base+0x36,2,max(4,min(cap,value(base+0x36,2))))
  quest=value(base+0xbc);setv('Heart piece remainder',base+0xbc,4,(quest&0x0fffffff)|((hearts%4)<<28))
 if any(k.startswith('fairy:') for k in options.get('collections',{})):
  for g in range(4):
   n=sum(bool(value(base+0xf8+f['scene']*28+loc.PERM[f['field']])&(1<<f['flag'])) for f in catalog['fairies'] if f['group']==g);setv('Fairy count '+str(g),base+0xd4+g,1,min(15,n))
 if any(k.startswith('skull:') for k in options.get('collections',{})):
  for f in catalog['skulls']:setv('Skull count '+str(f['group']),base+0xec0+f['group']*2,2,(value(base+0xf8+f['scene']*28)&f['mask']).bit_count())
 if 'spiderOrder' in options:
  order=options['spiderOrder']
  if type(order)!=str or len(order)!=6 or any(x not in '0123' for x in order) or any(a==c for a,c in zip(order,order[1:])):raise ValueError('Oceanside order: six digits 0–3, adjacent colors differ')
  put('Oceanside mask order',base+0xff5+(0x384 if p['layout'].startswith('jp-') else 0),bytes(map(int,order)))
 if 'photo' in options:
  raw=bytes.fromhex(options['photo'])
  if len(raw)!=11200:raise ValueError('Photo must contain 11200 I5 bytes')
  if value(base+0x7d,1)!=0x0d:raise ValueError('Acquire the Pictograph Box before importing a photo')
  put('Photo I5',base+(0x1390 if p['layout'].startswith('jp-') else 0x10e0),raw)
  flag('Photo present',base+0xbc,4,1<<25,True)
  # Imported pixels do not establish actor subject validity.
  setv('Photo subject cleared',base+0xe78,4,0);setv('Photo errors cleared',base+0xe7c,4,0)
 if out==data:return data,[]
 length=p['save_length'];checksum=p['checksum_offset'];block=bytearray(out[b:b+length]);block[checksum:checksum+2]=bytes(2);setv('Save checksum',base+checksum,2,sum(block)&65535)
 pos=8
 while pos+12<=len(out):
  n=int.from_bytes(out[pos:pos+4],'big')
  if out[pos+4:pos+8]==b'apmd':at=pos+8+n;out[at:at+4]=(zlib.crc32(out[pos+4:at])&0xffffffff).to_bytes(4,'big');allowed.update(range(at,at+4));break
  pos+=n+12
 else:raise ValueError('Missing apmd')
 assert len(out)==len(data) and all(i in allowed for i,(a,c) in enumerate(zip(data,out)) if a!=c)
 return bytes(out),changes
