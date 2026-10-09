"""Runtime operations derived from the five supplied retail ROMs; no simulated native transitions."""
from pathlib import Path
import importlib.util,sys,json,zlib
ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
def module(n,f):
 s=importlib.util.spec_from_file_location(n,ROOT/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
inspector=module('revision_inspector','Majora-regional-inspector.py');advanced=module('revision_play','Majora-Advanced.py')
PROFILES=json.loads((ROOT/'Majora-Revision-Profiles.json').read_text(encoding='utf8'))
def context(name,data):
 report=inspector.inspect(name,data);p=report['detected_profile'];key=p['cartridge']+':'+str(p['revision'])
 if key not in PROFILES:raise ValueError('Unsupported revision: '+key)
 cfg=PROFILES[key];start=int(report['rdram_png_offset'],16);ram=data[start:start+0x800000]
 if ram.count(bytes.fromhex(cfg['code_prefix']))!=1:raise ValueError('ROM code identity missing or ambiguous for '+key)
 play,scene=advanced.find_play(ram);return report,cfg,start,ram,play,scene

def reset_plan(name,data):
 report,cfg,start,ram,play,scene=context(name,data);u=lambda o,n=4:int.from_bytes(ram[o:o+n],'big')
 if ram.count(bytes.fromhex(cfg['confirm_native_code']))!=1:raise ValueError('Revision native YES branch missing or ambiguous')
 player=u(play+0x1ccc)-0x80000000;action=u(player+0x748)-0x80000000;prefix=bytes.fromhex(cfg['player_confirmation_prefix'])
 if not 0<=action<len(ram)-len(prefix) or ram[action:action+len(prefix)]!=prefix:raise ValueError('Capture the native Song of Time YES/NO dialog')
 delta=cfg['runtime']['msg_field_delta'];msg=play+cfg['runtime']['msg_base']+delta
 if (u(msg+0x11f22,1),u(msg+0x12020,1),u(msg+0x1202a,2))!=(0x42,0x10,0x12) or u(msg+0x12021,1)>1:raise ValueError('Native confirmation dialog state required')
 subtract=3
 if report['detected_profile']['cartridge']=='NZSP':
  b=int(report['save_ram_offset'],16);language=u(b+0x3f42,1)
  if language>4:raise ValueError('Unknown PAL message language')
  subtract={0:3,1:3,2:5,3:4,4:3}[language]
 length=u(msg+0x11ff0,2)
 if not subtract<=length<=0x1000:raise ValueError('Invalid confirmation text length')
 plan=[('Native Song of Time confirmation',msg+0x11f22,b'\x4a'),('Native confirmation text length',msg+0x11ff0,(length-subtract).to_bytes(2,'big'))]
 if 'reset_aux_globals' in cfg:plan.extend(('Native message auxiliary',a,bytes(1)) for a in cfg['reset_aux_globals'])
 else:plan.extend(('Native message auxiliary',msg+off,bytes(2)) for off in (0x120d4,0x120d6))
 return report,plan

def safe_gameplay(ram,play,cfg):
 u=lambda o,n=1:int.from_bytes(ram[o:o+n],'big');rt=cfg['runtime']
 for field,n in [('pause_state',2),('transition_trigger',1),('transition_mode',1),('room_status',1),('song_cutscene',1)]:
  if u(play+rt[field],n):raise ValueError('Close pause, dialogue, cutscene and room transition before editing active state')
 msg=play+rt['msg_base']+rt['msg_field_delta']
 if u(msg+0x11f22):raise ValueError('Close the active message before editing character/time')
 setup=u(play+rt['setup_actors'],2)
 if setup<0x8000 and setup>0:raise ValueError('Actor setup in progress')

def advance_plan(name,data):
 report,cfg,start,ram,play,scene=context(name,data);safe_gameplay(ram,play,cfg);u=lambda o,n=1:int.from_bytes(ram[o:o+n],'big');b=int(report['save_ram_offset'],16);prefix=bytes.fromhex(cfg['cycle_action_prefix']);actors=[]
 # En_Test4 must be the live switch-category actor, linked to this PlayState.
 actor=u(play+0x1cb4,4)-0x80000000;seen=set()
 while 0<=actor<len(ram)-0x154 and actor not in seen:
  seen.add(actor)
  if u(actor,2)==0x15a and u(actor+2)==0:
   action=u(actor+0x150,4)-0x80000000
   if 0<=action<len(ram)-len(prefix) and ram[action:action+len(prefix)]==prefix and u(actor+0x128,4)==u(actor+0x12c,4)==0:actors.append(actor)
  actor=u(actor+0x124,4)-0x80000000
 if len(actors)!=1:raise ValueError('Native three-day event actor is not in its normal update state')
 actor=actors[0];day=u(b+0x18,4);time=u(b+0xc,2);night=u(b+0x10,4)
 if day not in (1,2,3) or night not in (0,1) or night!=int(time<0x4000 or time>=0xc000):raise ValueError('Cycle is in a transition state')
 if day==3 and night:raise ValueError('The final night ends at moon impact; use native Song of Time reset')
 if u(actor+0x144)!=1-night or u(actor+0x145) not in (0,60):raise ValueError('Native day/night actor state inconsistent')
 if u(play+0x1cac,2)!=1<<(9-2*day-night):raise ValueError('Half-day actor flags inconsistent')
 target=0x4000 if night else 0xc000
 if target==time:raise ValueError('Already at the transition boundary')
 # Only the time boundary is changed. Native En_Test4 handles day, events and transitions.
 return report,[('Native morning/night boundary',b+0xc,target.to_bytes(2,'big'))]

def apply_plan(data,report,plan,checksum=False):
 start=int(report['rdram_png_offset'],16);b=start+int(report['save_ram_offset'],16);out=bytearray(data);changes=[];allowed=set()
 def put(label,off,raw):
  at=start+off;before=bytes(out[at:at+len(raw)])
  if before!=raw:out[at:at+len(raw)]=raw;allowed.update(range(at,at+len(raw)));changes.append(dict(campo=label,offset_png=hex(at),antes=before.hex(),despues=raw.hex()))
 for label,off,raw in plan:put(label,off,raw)
 if checksum:
  p=report['detected_profile'];block=bytearray(out[b:b+p['save_length']]);block[p['checksum_offset']:p['checksum_offset']+2]=bytes(2);put('Save checksum',b-start+p['checksum_offset'],(sum(block)&65535).to_bytes(2,'big'))
 pos=8
 while pos+12<=len(out):
  n=int.from_bytes(out[pos:pos+4],'big')
  if out[pos+4:pos+8]==b'apmd':at=pos+8+n;out[at:at+4]=(zlib.crc32(out[pos+4:at])&0xffffffff).to_bytes(4,'big');allowed.update(range(at,at+4));break
  pos+=n+12
 else:raise ValueError('Missing apmd')
 if len(out)!=len(data) or any(i not in allowed for i,(a,c) in enumerate(zip(data,out)) if a!=c):raise ValueError('Unexpected runtime change')
 inspector.inspect(report['name'],bytes(out));return bytes(out),changes

def request_reset(name,data):
 report,plan=reset_plan(name,data);return apply_plan(data,report,plan)
def request_advance(name,data):
 report,plan=advance_plan(name,data);return apply_plan(data,report,plan,True)
