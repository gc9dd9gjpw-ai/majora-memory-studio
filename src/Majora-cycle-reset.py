"""USA / PAL 1.1 native Song of Time confirmation request; PAL physical test pending."""
from pathlib import Path
import importlib.util,sys,zlib,json
ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
spec=importlib.util.spec_from_file_location('reset_inspector',ROOT/'Majora-regional-inspector.py');inspector=importlib.util.module_from_spec(spec);spec.loader.exec_module(inspector)
CONFIG=json.loads((ROOT/'Majora-reset-config.json').read_text())
def locate(name,data):
 report=inspector.inspect(name,data);profile=report['detected_profile']
 key=(profile['cartridge'],profile['revision'])
 if key not in [('NZSE',0),('NZSP',1)]:raise ValueError('Reset request supports researched USA 1.0 / PAL 1.1 only')
 pal=key==('NZSP',1)
 start=int(report['rdram_png_offset'],16);ram=data[start:start+0x800000];u=lambda p,n:int.from_bytes(ram[p:p+n],'big')
 cfg=CONFIG['pal11'] if pal else CONFIG
 if pal:
  native=bytes.fromhex(cfg['confirm_code_signature'])
  if ram.count(native)!=1:raise ValueError('PAL native Yes branch missing or ambiguous')
  language=u(int(report['save_ram_offset'],16)+cfg['language_save_offset'],1)
  if str(language) not in cfg['text_length_subtractions']:raise ValueError('Unsupported PAL message language')
 candidates=[];p=0;signature=bytes.fromhex(cfg['player_action_prefix'])
 while (p:=ram.find(signature,p))>=0:
  if p%4==0:
   ptr=(p+0x80000000).to_bytes(4,'big');q=0
   while(q:=ram.find(ptr,q))>=0:
    player=q-0x748
    if q%4==0 and 0<=player<len(ram)-0xaeA and u(player,2)==0 and u(player+2,1)==2 and u(player+0xae8,2)>0:
     first=(player+0x80000000).to_bytes(4,'big');a=0
     while(a:=ram.find(first,a))>=0:
      play=a-0x1ccc
      if a%4==0 and 0<=play<len(ram)-0x18b50 and u(play+0x1cc8,4)==1 and u(play+0xa4,2)==0x6d:candidates.append((play,player))
      a+=1
    q+=1
  p+=1
 if len(candidates)!=1:raise ValueError('Native player/dialog state not uniquely identified')
 play,player=candidates[0];msg=play+0x4908+(4 if pal else 0)
 if (u(msg+0x11f22,1),u(msg+0x12020,1),u(msg+0x1202a,2))!=(0x42,0x10,0x12):raise ValueError('Requires native Song of Time confirmation dialog')
 subtraction=cfg['text_length_subtractions'][str(language)] if pal else 3
 if u(msg+0x12021,1)>1 or not subtraction<=u(msg+0x11ff0,2)<=0x1000:raise ValueError('Invalid confirmation text')
 for off,n in [(0x16f1c,2),(0x18875,1),(0x18b4a,1),(0x18711,1)]:
  if u(play+off,n):raise ValueError('Pause/transition/room load in progress')
 return report,start,msg
def request(name,data):
 report,start,msg=locate(name,data);out=bytearray(data);allowed=set();changes=[]
 def put(label,offset,raw):
  at=start+offset;before=bytes(out[at:at+len(raw)])
  if before!=raw:out[at:at+len(raw)]=raw;allowed.update(range(at,at+len(raw)));changes.append({'field':label,'png_offset':hex(at),'ram_address':hex(0x80000000+offset),'before':before.hex(),'after':raw.hex()})
 # Same assignments as native Yes branch. Do not patch player, Save, flags or Flash.
 put('msgMode NEW_CYCLE_0',msg+0x11f22,b'\x4a')
 at=start+msg+0x11ff0;length=int.from_bytes(data[at:at+2],'big');subtraction=3
 if report['detected_profile']['cartridge']=='NZSP':
  language=data[start+int(report['save_ram_offset'],16)+CONFIG['pal11']['language_save_offset']]
  subtraction=CONFIG['pal11']['text_length_subtractions'][str(language)]
 put('decodedTextLen',msg+0x11ff0,(length-subtraction).to_bytes(2,'big'))
 put('unk120D6',msg+0x120d6,bytes(2));put('unk120D4',msg+0x120d4,bytes(2))
 p=8
 while p+12<=len(out):
  n=int.from_bytes(out[p:p+4],'big')
  if out[p+4:p+8]==b'apmd':
   at=p+8+n;out[at:at+4]=(zlib.crc32(out[p+4:at])&0xffffffff).to_bytes(4,'big');allowed.update(range(at,at+4));break
  p+=n+12
 else:raise ValueError('Missing apmd')
 assert len(out)==len(data) and all(i in allowed for i,(a,b)in enumerate(zip(data,out))if a!=b)
 inspector.inspect(name,bytes(out));return bytes(out),changes
