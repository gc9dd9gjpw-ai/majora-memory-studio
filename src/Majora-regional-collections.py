"""Masked collection flags for the editor's gated retail profile. Hardware validation pending."""
from pathlib import Path
import sys,json,struct,zlib,functools
ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
CATALOG=json.loads((ROOT/'Majora-collections-catalog.json').read_text(encoding='utf-8'))
BASE=0x1e6ef0
PERM={'chest':0,'switch0':4,'switch1':8,'collectible':16}
ACTIVE={'chest':16,'switch0':0,'switch1':4,'collectible':28}
def original(scene):return CATALOG['scene_aliases'].get(str(scene),scene)
@functools.lru_cache(maxsize=2)
def find_play(ram):
 candidates=[]
 for index,(pointer,) in enumerate(struct.iter_unpack('>I',ram)):
  a=index*4;b=a-0x800
  if b<0 or b+0x19258>len(ram) or pointer!=0x80000000+b+0x220:continue
  if struct.unpack_from('>I',ram,b+0x2ac)[0]!=0x80000000+b:continue
  if ram[b+0x9b]!=1 or not 0<=struct.unpack_from('>h',ram,b+0xa4)[0]<120:continue
  if not all(0x80000000<=struct.unpack_from('>I',ram,b+off)[0]<0x80800000 for off in (0,4,8)):continue
  candidates.append(b)
 if len(candidates)!=1:raise ValueError('collectionPlay')
 return candidates[0],struct.unpack_from('>h',ram,candidates[0]+0xa4)[0]
def plan(data,report,groups):
 BASE=int(report['save_ram_offset'],16);cycle=report['detected_profile']['cycle_scene_offset']
 start=int(report['rdram_png_offset'],16);ram=data[start:start+0x800000]
 play,scene=find_play(ram);patches={};labels={}
 def read(off,n):return int.from_bytes(data[start+off:start+off+n],'big')
 def setvalue(off,n,v,label):patches[(off,n)]=v;labels[(off,n)]=label
 def bit(off,n,mask,label):setvalue(off,n,patches.get((off,n),read(off,n))|mask,label)
 def scene_flag(target,field,mask,label,permanent=True):
  if permanent:bit(BASE+0xf8+target*28+PERM[field],4,mask,label)
  canonical=target if field=='collectible' and target==0x18 else original(target)
  bit(BASE+cycle+canonical*20+PERM[field],4,mask,label)
  active_scene=scene if field=='collectible' and scene==0x18 else original(scene)
  if canonical==active_scene:bit(play+0x1e58+ACTIVE[field],4,mask,label)
 if 'hearts' in groups:
  if read(BASE+0x34,2)!=320:raise ValueError('collectionHealth')
  for h in CATALOG['hearts']:
   off=h['offset'];mask=1<<h['bit']
   if off>=0xef8:bit(BASE+off,1,mask,'heartFlags')
   else:
    target=(off-0xf8)//28;sub=(off-0xf8)%28
    field=next(k for k,v in PERM.items() if v==sub//4*4)
    scene_flag(target,field,mask<<((3-sub%4)*8),'heartFlags')
  for boss in CATALOG['bosses']:scene_flag(boss,'collectible',1<<31,'bossHeartFlags')
  setvalue(BASE+0xbc,4,read(BASE+0xbc,4)&0x0fffffff,'heartRemainder')
 for entry in CATALOG['skulls']:
  g=entry['group'];key='skull'+str(g)
  if key in groups:
   scene_flag(entry['scene'],'chest',entry['mask'],key)
   setvalue(BASE+0xec0+g*2,2,30,key)
 for g in range(4):
  key='fairy'+str(g)
  if key in groups:
   for f in CATALOG['fairies']:
    if f['group']==g:scene_flag(f['scene'],f['field'],1<<f['flag'],key)
   setvalue(BASE+0xd4+g,1,15,key)
 return start,patches,labels,dict(play=hex(0x80000000+play),scene=hex(scene))
def apply(data,report,groups):
 start,patches,labels,context=plan(data,report,groups);result=bytearray(data);changes=[]
 for (off,n),value in sorted(patches.items()):
  before=data[start+off:start+off+n];after=value.to_bytes(n,'big')
  if before!=after:
   result[start+off:start+off+n]=after;changes.append(dict(campo=labels[(off,n)],offset_png=hex(start+off),antes=before.hex(),despues=after.hex()))
 if not changes:return data,[],context
 p=8
 while p<len(result):
  n=int.from_bytes(result[p:p+4],'big')
  if result[p+4:p+8]==b'apmd':crc=p+8+n;result[crc:crc+4]=(zlib.crc32(result[p+4:crc])&0xffffffff).to_bytes(4,'big');break
  p+=n+12
 else:raise ValueError('collectionCRC')
 allowed=set(range(crc,crc+4))
 for (off,n) in patches:allowed.update(range(start+off,start+off+n))
 if any(i not in allowed for i,(a,b) in enumerate(zip(data,result)) if a!=b):raise ValueError('collectionDiff')
 return bytes(result),changes,context
def progress(data,report):
 start=int(report['rdram_png_offset'],16);b=start+int(report['save_ram_offset'],16)
 def value(off,n=4):return int.from_bytes(data[b+off:b+off+n],'big')
 counts={'hearts':sum(bool(data[b+h['offset']]&(1<<h['bit'])) for h in CATALOG['hearts'])}
 for entry in CATALOG['skulls']:counts['skull'+str(entry['group'])]=(value(0xf8+entry['scene']*28)&entry['mask']).bit_count()
 for g in range(4):counts['fairy'+str(g)]=sum(bool(value(0xf8+f['scene']*28+PERM[f['field']])&(1<<f['flag'])) for f in CATALOG['fairies'] if f['group']==g)
 return counts
