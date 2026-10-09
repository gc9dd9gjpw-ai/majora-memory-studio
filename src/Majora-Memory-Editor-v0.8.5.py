"""Experimental boundary advance; native En_Test4 handles the transition on resume."""
from pathlib import Path
import sys,importlib.util,json,zlib,zipfile
ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
s=importlib.util.spec_from_file_location('cycle081',ROOT/'Majora-Memory-Editor-v0.8.1.py');old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
tk=old.tk;ttk=old.ttk
CONFIG=json.loads((ROOT/'Majora-cycle-config.json').read_text())
def plan(name,data):
 report=old.studio.studio.ui.base.core.inspector.inspect(name,data);profile=report['detected_profile']
 profile_key=(profile['cartridge'],profile['revision'])
 if profile_key not in [('NZSE',0),('NZSP',1)]:raise ValueError('cycleScope')
 scene=0x6f if profile_key==('NZSE',0) else 0x34
 start=int(report['rdram_png_offset'],16);base=int(report['save_ram_offset'],16);ram=data[start:start+0x800000]
 def u(p,n):return int.from_bytes(ram[p:p+n],'big')
 candidates=[];p=0
 while (p:=ram.find(bytes.fromhex('015a00'),p))>=0:
  if p%4==0 and p+0x154<len(ram) and u(p+0x128,4)==u(p+0x12c,4)==0:
   action=u(p+0x150,4)-0x80000000
   if 0<=action<=len(ram)-32 and ram[action:action+32].hex()==CONFIG['handle_events_prefix']:candidates.append(p)
  p+=1
 pairs=[]
 for actor in candidates:
  ptr=(actor+0x80000000).to_bytes(4,'big');p=0
  while (p:=ram.find(ptr,p))>=0:
   play=p-0x1cb4
   if p%4==0 and 0<=play<len(ram)-0x18b50 and u(play+0x1cb0,4)==1 and u(play+0xa4,2) in (scene,0x6d):pairs.append((actor,play))
   p+=1
 if len(pairs)!=1:raise ValueError('cycleScope')
 actor,play=pairs[0]
 for off,n in [(0x16f1c,2),(0x1682a,1),(0x18875,1),(0x18b4a,1),(0x18711,1),(0x1f2c,1)]:
  if u(play+off,n)!=0:raise ValueError('cycleState')
 setup=u(play+0x18846,2);setup=setup-65536 if setup&32768 else setup
 if setup>0:raise ValueError('cycleState')
 day=u(base+0x18,4);time=u(base+0xc,2);night=u(base+0x10,4)
 if day not in (1,2,3) or night not in (0,1) or night!=int(time<0x4000 or time>=0xc000):raise ValueError('cycleState')
 if day==3 and night:raise ValueError('cycleDay3')
 if u(actor+0x144,1)!=1-night or u(actor+0x145,1) not in (0,60):raise ValueError('cycleState')
 bit=1<<(9-2*day-night)
 if u(play+0x1cac,2)!=bit:raise ValueError('cycleState')
 target=0x4000 if night else 0xc000
 if time==target:raise ValueError('cycleState')
 return report,target
prior=old.studio.edit
def edit(name,data,money,nuts,extra=None):
 extra=dict(extra or {});advance=extra.pop('cycleAdvance',False)
 if type(advance)!=bool:raise ValueError('cycleState')
 if advance:plan(name,data)
 try:result,changes=prior(name,data,money,nuts,extra)
 except ValueError as e:
  if str(e)!='No hay cambios que guardar.':raise
  result,changes=data,[]
 if advance:
  report,target=plan(name,result);b=int(report['rdram_png_offset'],16)+int(report['save_ram_offset'],16);out=bytearray(result);allowed=set()
  def put(label,at,raw):
   before=bytes(out[at:at+len(raw)])
   if before!=raw:out[at:at+len(raw)]=raw;allowed.update(range(at,at+len(raw)));changes.append(dict(campo=label,offset_png=hex(at),antes=before.hex(),despues=raw.hex()))
  put('cycleAdvance',b+0xc,target.to_bytes(2,'big'))
  block=bytearray(out[b:b+0x100c]);block[0x100a:0x100c]=b'\0\0';put('Save checksum',b+0x100a,(sum(block)&65535).to_bytes(2,'big'))
  p=8
  while p+12<=len(out):
   n=int.from_bytes(out[p:p+4],'big')
   if out[p+4:p+8]==b'apmd':
    at=p+8+n;out[at:at+4]=(zlib.crc32(out[p+4:at])&0xffffffff).to_bytes(4,'big');allowed.update(range(at,at+4));break
   p+=n+12
  else:raise ValueError('Missing apmd')
  assert len(out)==len(result) and all(i in allowed for i,(a,b2) in enumerate(zip(result,out))if a!=b2)
  result=bytes(out);old.studio.studio.ui.base.core.inspector.inspect(name,result)
 if not changes:raise ValueError('No hay cambios que guardar.')
 return result,changes
old.studio.edit=edit;old.studio.studio.ui.edit=edit
TEXT={
 'advance':('Avanzar a la siguiente mañana/noche','Advance to next morning/night','Avancer au prochain matin/soir'),
 'help':('Avance probado en capturas de Analogue 3D para USA 1.0 y PAL 1.1, en las zonas investigadas y días 1–2 y mañana del día 3. Al cargar la copia, el juego actualiza el día y sus eventos.','Advance tested with Analogue 3D captures for USA 1.0 and PAL 1.1, researched areas and days 1–2 and day 3 morning. Loading the copy lets the game update the day and its events.','Avance testée avec des captures Analogue 3D pour USA 1.0 et PAL 1.1, zones étudiées et jours 1–2 et matin du jour 3. Le jeu actualise le jour et ses événements au chargement de la copie.'),
 'cycleScope':('Avance experimental limitado a USA 1.0 / PAL 1.1 y la zona investigada.','Experimental advance requires USA 1.0 / PAL 1.1 and the researched area.','Avance expérimentale limitée à USA 1.0 / PAL 1.1 et à la zone étudiée.'),
 'cycleState':('El estado vivo no permite solicitar un avance seguro. Cierra diálogos y pausa, y crea otro Memory durante el juego normal.','Live state does not pass advance checks. Close dialogs and pause; capture normal gameplay.','État actif incompatible. Fermez dialogues et pause ; capturez le jeu normal.'),
 'cycleDay3':('No se permite avanzar desde la noche del tercer día: llevaría a la caída de la Luna.','Advancing from day 3 night is blocked: it would trigger moon crash.','Avance bloquée depuis la nuit du jour 3 : elle déclencherait la chute de la Lune.')}
TEXT['help']=tuple(text+' '+notice for text,notice in zip(TEXT['help'],('La ampliación al día 3 y a esta nueva zona está pendiente de prueba física.','Day 3 and the additional area await console validation.','Le jour 3 et la zone supplémentaire attendent une validation console.')))
old.TEXT['pending']=('Lectura del Memory actual. El avance está validado para las pruebas USA 1.0 y PAL 1.1; conserva las restricciones de versión, zona y estado.', 'Current Memory values. Advance is validated for the USA 1.0 and PAL 1.1 tests; version, area and state restrictions remain.', 'Valeurs du Memory actuel. Avance validée pour les tests USA 1.0 et PAL 1.1 ; restrictions de version, zone et état conservées.')
def destination(day,night,language):
 day=day+1 if night else day
 return [('Día '+str(day)+' · '+('06:00 · mañana' if night else '18:00 · noche')),('Day '+str(day)+' · '+('06:00 · morning' if night else '18:00 · night')),('Jour '+str(day)+' · '+('06:00 · matin' if night else '18:00 · soir'))][language]
class App(old.App):
 def xt(self,key):return TEXT[key][self.language]
 def build(self):
  self.advancevar=None;self.targetlabel=None;super().build();self.root.title('Majora · Memory Studio 0.8.5')
  page=self.book.nametowidget(self.book.tabs()[-1]);self.advancevar=tk.BooleanVar(value=bool(self.extra.get('cycleAdvance',False)))
  self.advancebutton=ttk.Checkbutton(page,text=self.xt('advance'),variable=self.advancevar,command=self.update_preview);self.advancebutton.pack(anchor='w',pady=8)
  ttk.Label(page,text=self.xt('help'),wraplength=950,foreground='#c3a66a').pack(anchor='w')
  self.targetlabel=ttk.Label(page,wraplength=950);self.targetlabel.pack(anchor='w',pady=10);self.populate()
 def populate(self):
  super().populate()
  if self.advancevar is None:return
  self.advancevar.set(bool(self.extra.get('cycleAdvance',False)));enabled=False
  reason=''
  if self.data:
   try:plan(self.choice_name,self.data);enabled=True
   except ValueError as e:reason=self.error_text(e)
  if self.targetlabel is not None:
   prefix=['Destino al cargar la copia: ','Destination on loading the copy: ','Destination au chargement : '][self.language]
   self.targetlabel.configure(text=prefix+destination(self.value(0x18,4),bool(self.value(0x10,4)),self.language) if enabled else reason)
  self.advancebutton.configure(state='normal' if enabled else 'disabled')
 def collect(self):
  extra,money,nuts=super().collect()
  if self.advancevar is not None and self.advancevar.get():extra['cycleAdvance']=True
  return extra,money,nuts
 def error_text(self,e):return self.xt(str(e)) if str(e) in TEXT else super().error_text(e)
 def describe(self,c):
  if c['campo']=='cycleAdvance':return self.xt('advance'),str(self.value(0x18,4))+' · '+old.clock(int(c['antes'],16)),destination(self.value(0x18,4),bool(self.value(0x10,4)),self.language)
  return super().describe(c)
 def save(self):
  original=old.studio.studio.ui.filedialog.asksaveasfilename
  def dialog(*a,**kw):
   if 'initialfile'in kw:kw['initialfile']=kw['initialfile'].replace('copy-v071','copy-v085').replace('copy-v08.zip','copy-v085.zip').replace('copy-v081','copy-v085')
   return original(*a,**kw)
  old.studio.studio.ui.filedialog.asksaveasfilename=dialog
  try:super().save()
  finally:old.studio.studio.ui.filedialog.asksaveasfilename=original
if __name__=='__main__':
 root=tk.Tk()
 if len(sys.argv)==4 and sys.argv[1]=='--self-test':
  root.withdraw();app=App(root)
  with zipfile.ZipFile(sys.argv[2])as z:name='despues.png';data=z.read(name)
  app.memories={name:data};app.choice.configure(values=[name]);app.choice.current(0);app.select();app.advancevar.set(True);app.update_preview();assert app.valid
  e,m,n=app.collect();edited,changes=edit(name,data,m,n,e)
  for language in range(3):app.extra=e;app.language=language;app.build();root.update_idletasks();assert app.advancevar.get()
  Path(sys.argv[3]).write_text(json.dumps({'version':'0.8.5','languages':3,'changes':len(changes),'hardware':'days1-2 tested; day3 and scene6D advance pending'}));root.destroy()
 else:App(root);root.mainloop()
