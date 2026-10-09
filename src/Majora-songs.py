"""PAL/USA retail song research implementation. Exports require console validation."""
import struct,zlib
PITCHES=(2,5,9,11,14)
BUTTONS=('A','C-down','C-right','C-left','C-up')
SONGS=[(6,'Sonata of Awakening'),(7,'Goron Lullaby'),(8,'New Wave Bossa Nova'),(9,'Elegy of Emptiness'),(10,'Oath to Order'),(12,'Song of Time'),(13,'Song of Healing'),(14,"Epona's Song"),(15,'Song of Soaring'),(16,'Song of Storms'),(24,'Goron Lullaby Intro')]
MASK=sum(1<<bit for bit,_ in SONGS)
RESERVED=(0,1,2,3,4,6,7,8,9,10,12,13,14,19,20)
SIGNATURE=bytes([7,4,3,4,3,0,2,0,0,8,0,2,3,0,2,3,2,0])

def supported(report):
 p=report['detected_profile']
 return (p['cartridge'],p['revision']) in (('NZSP',1),('NZSE',0),('NZSJ',1),('NZSP',0),('NZSJ',0))

def decode(raw):
 if len(raw)!=128:raise ValueError('Scarecrow: invalid recording length.')
 indices=[];notes=[]
 for i in range(16):
  pitch,_,length,volume,vibrato,bend,flags=struct.unpack('>BBHBBbB',raw[i*8:i*8+8])
  if length==0:return notes,indices
  if pitch==255:continue
  if pitch not in PITCHES or flags or bend or vibrato or volume>127:raise ValueError('Scarecrow: altered pitches require native recording.')
  indices.append(i);notes.append(PITCHES.index(pitch))
 raise ValueError('Scarecrow: missing recording terminator.')

def locate(ram,sonata):
 def unique(pattern):
  at=ram.find(pattern)
  if at<0 or ram.find(pattern,at+1)>=0:raise ValueError('Scarecrow: audio signature is missing or ambiguous.')
  return at
 a=unique(sonata);b=unique(SIGNATURE)
 if a%4 or a+24*160>len(ram) or b+24*9>len(ram):raise ValueError('Scarecrow: invalid audio tables.')
 song=a+22*160
 pointer=(0x80000000+song).to_bytes(4,'big')
 refs=[i for i in range(a+24*160,min(a+24*160+0x2000,len(ram)-4),4) if ram[i:i+4]==pointer]
 if len(refs)!=1:raise ValueError('Scarecrow: live song pointer not verified.')
 for i in range(22):
  row=ram[b+i*9:b+(i+1)*9];n=row[0]
  if not 1<=n<=8 or any(x>4 for x in row[1:n+1]):raise ValueError('Scarecrow: inconsistent song button table.')
 return song,b+22*9,b

def validate(notes,ram,button_base):
 if len(notes)!=8 or any(type(x)!=int or x not in range(5) for x in notes):raise ValueError('Scarecrow: choose exactly eight notes.')
 if len(set(notes))<2:raise ValueError('Scarecrow: all eight notes cannot be identical.')
 for i in RESERVED:
  row=ram[button_base+i*9:button_base+(i+1)*9];seq=list(row[1:1+row[0]])
  if any(notes[j:j+len(seq)]==seq for j in range(9-len(seq))):raise ValueError('Scarecrow: sequence contains a reserved song.')

def compose(raw,notes,template=None):
 try:old,indices=decode(raw)
 except ValueError:old,indices=[],[]
 if len(old)!=8 and template is not None:
  raw=template;old,indices=decode(raw)
  if len(old)!=8:raise ValueError('Scarecrow: invalid regional recording template.')
 if len(old)==8:
  out=bytearray(raw)
  for i,n in zip(indices,notes):out[i*8]=PITCHES[n]
  return bytes(out)
 # Timing and rest flags taken from our accepted native PAL recording.
 lengths=[6,72,9,45,6,63,9,33,10,35,12,159,9,25,9]
 out=bytearray(128)
 for i,length in enumerate(lengths):
  pitch=PITCHES[notes[i//2]] if i%2==0 else 255
  out[i*8:i*8+8]=struct.pack('>BBHBBbB',pitch,0,length,87,0,0,0 if i%2==0 else 0xc0)
 return bytes(out)

def apply(data,report,extra,sonata,template=None):
 if not extra:return data,[]
 if not supported(report):raise ValueError('Songs: editing is enabled only for the researched PAL and USA retail revisions.')
 start=int(report['rdram_png_offset'],16);save=start+int(report['save_ram_offset'],16)
 shift=0x384 if report['detected_profile']['layout'].startswith('jp-') else 0
 ram=data[start:start+0x800000];result=bytearray(data);changes=[];allowed=set()
 def put(label,at,raw):
  before=bytes(result[at:at+len(raw)])
  if before==raw:return
  result[at:at+len(raw)]=raw;allowed.update(range(at,at+len(raw)))
  changes.append(dict(campo=label,offset_png=hex(at),antes=before.hex(),despues=raw.hex()))
 if 'song_bits' in extra:
  bits=extra['song_bits']
  if type(bits)!=int or bits&~MASK:raise ValueError('Songs: invalid learned-song mask.')
  old=int.from_bytes(data[save+0xbc:save+0xc0],'big')
  put('Learned songs',save+0xbc,((old&~MASK)|bits).to_bytes(4,'big'))
 if 'scarecrow_notes' in extra or 'scarecrow_active' in extra:
  audio,buttons,table=locate(ram,sonata)
  original=data[save+0xf66+shift:save+0xfe6+shift]
  if 'scarecrow_notes' in extra:
   notes=extra['scarecrow_notes'];validate(notes,ram,table);recording=compose(original,notes,template)
   put('Scarecrow recording',save+0xf66+shift,recording)
  else:recording=original;notes,_=decode(recording)
  active=extra.get('scarecrow_active',bool(data[save+0xf65+shift]))
  if type(active)!=bool:raise ValueError('Scarecrow: invalid activation flag.')
  if active:
   validate(notes,ram,table)
   put('Scarecrow live audio',start+audio,recording)
   put('Scarecrow recognition',start+buttons,bytes([8]+notes))
  elif 'scarecrow_notes' in extra:
   # Keep the live representation coherent, even with availability disabled.
   put('Scarecrow live audio',start+audio,recording)
   put('Scarecrow recognition',start+buttons,bytes([8]+notes))
  put('Scarecrow active this cycle',save+0xf65+shift,bytes([active]))
 if not changes:return data,[]
 length=report['detected_profile']['save_length'];check=report['detected_profile']['checksum_offset']
 block=bytearray(result[save:save+length]);block[check:check+2]=b'\0\0'
 put('Save checksum',save+check,(sum(block)&65535).to_bytes(2,'big'))
 p=8
 while p+12<=len(result):
  n=int.from_bytes(result[p:p+4],'big')
  if result[p+4:p+8]==b'apmd':
   at=p+8+n;result[at:at+4]=(zlib.crc32(result[p+4:at])&0xffffffff).to_bytes(4,'big');allowed.update(range(at,at+4));break
  p+=n+12
 else:raise ValueError('Songs: missing apmd.')
 if len(result)!=len(data) or any(i not in allowed for i,(a,b)in enumerate(zip(data,result))if a!=b):raise ValueError('Songs: unexpected byte change.')
 return bytes(result),changes
