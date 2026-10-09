"""Read-only structural SaveContext detection. Metadata labels never select a RAM address."""
import struct,functools,json,sys
from pathlib import Path
PROFILES=json.loads((Path(getattr(sys,"_MEIPASS",Path(__file__).parent))/"Majora-Revision-Profiles.json").read_text(encoding="utf8"))
REGIONS={'P':'PAL · Europe / Australia','E':'NTSC · Americas','J':'NTSC · Japan'}
def u16(ram,off):return struct.unpack_from('>H',ram,off)[0]
def u32(ram,off):return struct.unpack_from('>I',ram,off)[0]
def signed16(n):return n if n<32768 else n-65536
def valid_prefix(ram,b):
 if b<0 or b+0x5000>len(ram) or b%4:return False
 if ram[b+0x24:b+0x2a]!=b'ZELDA3':return False
 if u32(ram,b+0x10)>1 or u32(ram,b+0x18)>3 or ram[b+0x20]>4:return False
 cap=u16(ram,b+0x34);health=u16(ram,b+0x36)
 if not 48<=cap<=320 or cap%16 or health>cap:return False
 if ram[b+0x38]>2 or ram[b+0x39]>96 or u16(ram,b+0x3a)>500:return False
 if any(ram[b+i]>1 for i in (0x40,0x41,0x42)):return False
 if any(v!=255 and v>0xa4 for v in ram[b+0x70:b+0xa0]):return False
 if any(v>3 for v in [(u32(ram,b+0xb8)>>shift)&7 for shift in (0,3,17,20)]):return False
 return True
def live_reference(ram,b):
 address=0x80000000+b;low=address&65535;high=((address+0x8000)>>16)&65535
 references=[]
 for index,(instruction,) in enumerate(struct.iter_unpack('>I',ram)):
  if instruction>>26!=15 or instruction&65535!=high:continue
  lui_reg=(instruction>>16)&31;p=index*4
  for delta in range(4,20,4):
   if p+delta+4>len(ram):continue
   add=u32(ram,p+delta)
   if add>>26!=9 or (add>>21)&31!=lui_reg or add&65535!=low:continue
   reg=(add>>16)&31
   if not reg:continue
   accesses=[]
   for pos in range(p+delta+4,min(p+delta+40,len(ram)),4):
    op=u32(ram,pos);opcode=op>>26;rs=(op>>21)&31;imm=op&65535
    if rs==reg and opcode in (32,33,36,37,40,41,35,43) and imm in (0x34,0x36,0x38,0x39,0x3a,0x70,0xa0,0xb8):accesses.append((opcode,imm))
   if any(offset==0x3a and opcode in (33,37,41) for opcode,offset in accesses):references.append(hex(0x80000000+p))
 return references
def runtime_valid(ram,b,delta):
 # Live runtime fields distinguish the shared international and Japanese layouts.
 early=0x2b4 if delta else 0
 if u32(ram,b+0x3ca8+early)>1 or u32(ram,b+0x3cac+early)>15:return False
 respawn=u32(ram,b+0x3cb0+early)
 if not (respawn<=8 or respawn>=0xfffffff8):return False
 if u16(ram,b+0x3f28+delta)>12:return False
 if u16(ram,b+0x3f2e+delta)>96 or u16(ram,b+0x3f30+delta)>96:return False
 if ram[b+0x3f42+delta+(8 if delta else 0)]>4:return False
 return True
@functools.lru_cache(maxsize=2)
def detect(ram,cartridge,revision):
 matches=[];pos=0;evidence=[]
 while True:
  pos=ram.find(b'ZELDA3',pos)
  if pos<0:break
  b=pos-0x24;pos+=6
  if not valid_prefix(ram,b):continue
  refs=live_reference(ram,b)
  evidence.append(dict(address=hex(0x80000000+b),live_code_references=refs))
  if refs:matches.append((b,refs))
 if len(matches)!=1:raise ValueError('regionalAmbiguous')
 b,refs=matches[0]
 # Source-backed layout families; unknown cartridge IDs cannot authorize editing.
 if len(cartridge)!=4 or cartridge[:3]!='NZS' or cartridge[3] not in REGIONS:raise ValueError('regionalCartridge')
 japanese=cartridge[3]=='J';delta=0x384 if japanese else 0
 key=cartridge+':'+str(revision)
 if key not in PROFILES:raise ValueError('regionalJapanRevision' if japanese else 'regionalCartridge')
 if japanese and revision==0 and ram.count(bytes.fromhex(PROFILES[key]['code_prefix']))!=1:raise ValueError('regionalRuntime')
 if not runtime_valid(ram,b,delta):raise ValueError('regionalRuntime')
 return dict(save_ram_offset=hex(b),save_address=hex(0x80000000+b),cartridge=cartridge,revision=revision,region=REGIONS[cartridge[3]],layout=('jp-1.'+str(revision)) if japanese else 'international',runtime_delta=delta,cycle_scene_offset=0x3f68+delta+(8 if japanese else 0),save_length=0x1390 if japanese else 0x100c,checksum_offset=0x138e if japanese else 0x100a,code_references=refs,candidates=evidence,validation='real-captures' if cartridge=='NZSP' and revision==1 and b==0x1e6ef0 and ram[0x12183c:0x121844]==bytes.fromhex('3c08801e25086ef0') else 'structural-only')


