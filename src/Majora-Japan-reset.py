"""Native Japanese 1.1 Song of Time YES operation, guarded by captured code and state."""
from pathlib import Path
import importlib.util,sys,zlib
ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
def load(n,f):
 s=importlib.util.spec_from_file_location(n,ROOT/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
inspector=load('jp_reset_inspector','Majora-regional-inspector.py');advanced=load('jp_reset_play','Majora-Advanced.py')
YES=bytes.fromhex('3c010001240f004a003f0821a02f1f2296181ff03c010001003f08212719fffda4391ff03c01801ca4201b443c01801c100003d2a4201b40')
ACTION=bytes.fromhex('27bdffa0afb10030afb0002c0080802500a08825afbf003424060004920e0aa50220202550ce001f860e0ae80c04deec260502401040001a240600049218014b')
def locate(name,data):
 report=inspector.inspect(name,data);p=report['detected_profile']
 if (p['cartridge'],p['revision'])!=('NZSJ',1):raise ValueError('Japanese 1.1 only')
 start=int(report['rdram_png_offset'],16);ram=data[start:start+0x800000]
 if ram.count(YES)!=1:raise ValueError('Native Japanese YES branch missing or ambiguous')
 u=lambda p,n=4:int.from_bytes(ram[p:p+n],'big');play,scene=advanced.find_play(ram);player=u(play+0x1ccc)-0x80000000;action=u(player+0x748)-0x80000000
 if not 0<=action<len(ram)-len(ACTION) or ram[action:action+len(ACTION)]!=ACTION:raise ValueError('Native Song of Time player action required')
 # Two native addiu instructions verify MessageContext offset +0x4908.
 if ram.count(bytes.fromhex('263f4908'))<2:raise ValueError('Native message base instructions missing')
 msg=play+0x4908
 if (u(msg+0x11f22,1),u(msg+0x12020,1),u(msg+0x1202a,2))!=(0x42,0x10,0x12):raise ValueError('Capture the Japanese Song of Time YES/NO dialog first')
 if u(msg+0x12021,1)>1 or not 3<=u(msg+0x11ff0,2)<=0x1000:raise ValueError('Invalid native confirmation state')
 return report,start,msg

def request(name,data):
 report,start,msg=locate(name,data);out=bytearray(data);changes=[];allowed=set()
 def put(label,off,raw):
  at=start+off;before=bytes(out[at:at+len(raw)])
  if before!=raw:out[at:at+len(raw)]=raw;allowed.update(range(at,at+len(raw)));changes.append(dict(campo=label,offset_png=hex(at),antes=before.hex(),despues=raw.hex()))
 put('Native Song of Time confirmation',msg+0x11f22,b'\x4a')
 length=int.from_bytes(out[start+msg+0x11ff0:start+msg+0x11ff2],'big');put('Native confirmation text length',msg+0x11ff0,(length-3).to_bytes(2,'big'))
 # These Japanese fields are native globals, not international MessageContext members.
 put('Native message auxiliary 1',0x1c1b44,bytes(1));put('Native message auxiliary 2',0x1c1b40,bytes(1))
 pos=8
 while pos+12<=len(out):
  n=int.from_bytes(out[pos:pos+4],'big')
  if out[pos+4:pos+8]==b'apmd':at=pos+8+n;out[at:at+4]=(zlib.crc32(out[pos+4:at])&0xffffffff).to_bytes(4,'big');allowed.update(range(at,at+4));break
  pos+=n+12
 else:raise ValueError('Missing apmd')
 if len(out)!=len(data) or any(i not in allowed for i,(a,b) in enumerate(zip(data,out)) if a!=b):raise ValueError('Unexpected native reset change')
 inspector.inspect(name,bytes(out));return bytes(out),changes
