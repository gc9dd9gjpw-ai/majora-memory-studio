"""Japan 1.1 Memory adapter. Source-backed offsets; console edit validation pending."""
from pathlib import Path
import importlib.util,sys,json,zlib,hashlib,zipfile
ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
def load(n,f):
 s=importlib.util.spec_from_file_location(n,ROOT/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
writer=load('jpwriter','Majora-regional-writer.py');songs=load('jpsongs','Majora-songs.py')
reset_writer=load('jp_native_reset','Majora-Japan-reset.py')
extras_writer=load('regional_extras','Majora-Regional-Extras.py')
CATALOG=json.loads((ROOT/'Majora-collections-catalog.json').read_text(encoding='utf8'))
FIELDS=json.loads((ROOT/'Majora-progress-v1-config.json').read_text(encoding='utf8'))['fields']
CHARS={int(k):v for k,v in json.loads((ROOT/'Majora-Japan-characters.json').read_text(encoding='utf8'))['characters'].items()}
SONATA=bytes.fromhex(json.loads((ROOT/'Majora-song-config.json').read_text(encoding='utf8'))['profiles']['NZSE:0']['sonata_signature'])
def item(v):
 if v==255:return v
 if v<0x24:return v
 if v<=0x26:return v+2
 if v<=0x2c:return v+8
 if v<=0x2e:return v+13
 if v<=0x30:return v+21
 return v+28
OPTIONS={i:[item(v) for v in values] for i,values in writer.OPTIONS.items()}
LABELS={item(v):label for v,label in writer.ITEM_LABELS.items()}
def offset(off):return off+(0x384 if off>=0xf64 else 0)
def decode_name(raw):return ''.join(CHARS.get(v,'\ufffd') for v in raw).rstrip()
def encode_name(value):
 reverse={v:k for k,v in CHARS.items()}
 if not 1<=len(value)<=8 or any(c not in reverse for c in value):raise ValueError('Name: 1–8 characters from the Japanese game alphabet')
 return bytes([reverse[c] for c in value]+[0xdf]*(8-len(value)))
def inspect(name,data):
 r=writer.core.inspector.inspect(name,data)
 if (r['detected_profile']['cartridge'],r['detected_profile']['revision'])!=('NZSJ',1):raise ValueError('Japan 1.1 only')
 return r
def edit(name,data,money,nuts,extra):
 extra=dict(extra);reset=extra.pop('cycleReset',False);r=inspect(name,data);b=int(r['rdram_png_offset'],16)+int(r['save_ram_offset'],16)
 advanced=extra.pop('advanced',{});progress=extra.pop('progress',{});song=extra.pop('songs',{});bank=extra.pop('bank',None);namevalue=extra.pop('playerName',None);code=extra.pop('bomberCode',None);lottery=extra.pop('lotteryCodes',None)
 # Base writes only common Save prefix fields. Regional IDs are supplied explicitly.
 prior=writer.OPTIONS;writer.OPTIONS=OPTIONS
 try:
  try:out,changes=writer.edit(name,data,money,nuts,extra)
  except ValueError as e:
   if str(e)!='No hay cambios que guardar.':raise
   out,changes=data,[]
 finally:writer.OPTIONS=prior
 out=bytearray(out)
 def put(label,off,raw):
  at=b+off;before=bytes(out[at:at+len(raw)])
  if before!=raw:out[at:at+len(raw)]=raw;changes.append(dict(campo=label,offset_png=hex(at),antes=before.hex(),despues=raw.hex()))
 for key,value in progress.items():
  f=next((f for f in FIELDS if f['key']==key and f['group']!='Lectura'),None)
  if f is None or type(value)!=int or not f['minimum']<=value<=f['maximum']:raise ValueError('Invalid progress field')
  off=offset(f['offset'])
  if f['mask'] is not None:
   current=int.from_bytes(out[b+off:b+off+f['size']],'big');value=current|f['mask'] if value else current&~f['mask']
  put('progress:'+key,off,value.to_bytes(f['size'],'big',signed=f['signed']))
 if bank is not None:
  if type(bank)!=int or not 0<=bank<=9999:raise ValueError('Bank: 0–9999')
  put('Bank',0xede,bank.to_bytes(2,'big'))
 if namevalue is not None:put('Player name',0x2c,encode_name(namevalue))
 if code is not None:
  if len(code)!=5 or set(code)!=set('12345'):raise ValueError('Bomber code: permutation of 12345')
  put('Bomber code',offset(0xffb),bytes(map(int,code)))
 if lottery is not None:
  if len(lottery)!=9 or any(c not in '0123456789' for c in lottery):raise ValueError('Lottery: nine digits')
  put('Lottery',offset(0xfec),bytes(map(int,lottery)))
 if song:
  updated,c=songs.apply(bytes(out),r,song,SONATA);out=bytearray(updated);changes+=c
 if advanced:
  updated,c=extras_writer.apply(bytes(out),r,advanced,CATALOG);out=bytearray(updated);changes+=c
 if not changes and not reset:raise ValueError('No hay cambios que guardar.')
 if changes:
  block=bytearray(out[b:b+0x1390]);block[0x138e:0x1390]=bytes(2);put('Save checksum',0x138e,(sum(block)&65535).to_bytes(2,'big'))
 p=8
 while p+12<=len(out):
  n=int.from_bytes(out[p:p+4],'big')
  if out[p+4:p+8]==b'apmd':crc=p+8+n;out[crc:crc+4]=(zlib.crc32(out[p+4:crc])&0xffffffff).to_bytes(4,'big');break
  p+=n+12
 else:raise ValueError('Missing apmd')
 allowed=set(range(crc,crc+4))
 for c in changes:
  at=int(c['offset_png'],16);allowed.update(range(at,at+len(bytes.fromhex(c['antes']))))
 if len(out)!=len(data) or any(i not in allowed for i,(a,c) in enumerate(zip(data,out)) if a!=c):raise ValueError('Unexpected change')
 inspect(name,bytes(out))
 if reset:
  out,c=reset_writer.request(name,bytes(out));changes+=c
 return bytes(out),changes

class Panel:
 def __init__(self,parent,name,data):
  self.parent=parent;self.name=name;self.data=data;self.report=inspect(name,data);self.source=parent.source;self.source_hash=parent.source_hash
  tk=writer.tk;ttk=writer.ttk;self.tk=tk;self.ttk=ttk;self.resetvar=tk.BooleanVar();self.collection_patches={};self.photo_hex=None
  self.root=ttk.Frame(parent.frame) if getattr(parent,'embed_regional',False) else tk.Toplevel(parent.root)
  if getattr(parent,'embed_regional',False):self.root.pack(fill='both',expand=True)
  else:self.root.title('MAJORA / MEMORY STUDIO');self.root.geometry('1100x850')
  self.language=3 if getattr(parent,'german',False) else parent.language
  def tr(es,en,fr,de):return (es,en,fr,de)[self.language]
  self.tr=tr
  self.caption=ttk.Label(self.root,text=tr('Japón 1.1 · Edición regional · Localizada en tus 2 Memories; prueba física de cambios pendiente.','Japan 1.1 · Regional editing · Located in your 2 Memories; console edit validation pending.','Japon 1.1 · Modification régionale · Localisé dans vos 2 Memories; test console en attente.','Japan 1.1 · Regionale Bearbeitung · In 2 Memories gefunden; Konsolentest ausstehend.'),wraplength=1050);self.caption.pack(padx=14,pady=12,anchor='w')
  self.book=ttk.Notebook(self.root);self.book.pack(fill='both',expand=True,padx=14)
  self.vars={};self.items={};self.progress={};self.songvars={};self.notevars=[]
  def page(title):
   box=ttk.Frame(self.book);self.book.add(box,text=title);canvas=tk.Canvas(box,bg='#10151d',highlightthickness=0);scroll=ttk.Scrollbar(box,command=canvas.yview);canvas.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');canvas.pack(fill='both',expand=True);body=ttk.Frame(canvas,padding=14);canvas.create_window((0,0),window=body,anchor='nw');body.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')));return body
  def field(body,row,label,key,value):
   ttk.Label(body,text=label).grid(row=row,column=0,sticky='w',pady=4);v=tk.StringVar(value=str(value));widget=ttk.Entry(body,textvariable=v,width=28) if key in ('playerName','bomberCode','lotteryCodes','spiderOrder') else ttk.Spinbox(body,textvariable=v,from_=0,to=9999,increment=.25 if key=='health' else 1,width=12);widget.grid(row=row,column=1,padx=15);self.vars[key]=v
  res=page(tr('Recursos','Resources','Ressources','Ressourcen'));self.original={}
  definitions=[('healthCapacity',0x34,2),('health',0x36,2),('magicCurrent',0x39,1),('rupees',0x3a,2),('bank',0xede,2)]
  for i,(key,off,n) in enumerate(definitions):v=self.value(off,n);self.original[key]=v;field(res,i,key,key,v/16 if key in ('health','healthCapacity') else v)
  row=len(definitions)
  for i,(label,shift,caps) in writer.AMMO.items():key='ammo_'+str(i);v=self.value(0xa0+i);self.original[key]=v;field(res,row,label,key,v);row+=1
  self.original['playerName']=decode_name(self.raw(0x2c,8));field(res,row,tr('Nombre','Name','Nom','Name'),'playerName',self.original['playerName']);row+=1
  self.original['bomberCode']=''.join(str(v) for v in self.raw(offset(0xffb),5));field(res,row,'Bomber code','bomberCode',self.original['bomberCode']);row+=1
  self.original['spiderOrder']=''.join(str(v) for v in self.raw(offset(0xff5),6));field(res,row,'Oceanside color order','spiderOrder',self.original['spiderOrder']);row+=1
  self.original['lotteryCodes']=''.join(str(v) for v in self.raw(offset(0xfec),9));field(res,row,'Lottery','lotteryCodes',self.original['lotteryCodes']);row+=1
  self.upgrade_vars=[]
  for label,shift,mask,maximum in [('Quiver',0,7,3),('Bomb bag',3,7,3),('Wallet',12,3,2),('Sticks',17,7,3),('Nuts',20,7,3)]:
   ttk.Label(res,text=label).grid(row=row,column=0,sticky='w');v=tk.StringVar(value=str((self.value(0xb8,4)>>shift)&mask));ttk.Combobox(res,textvariable=v,values=list(range(maximum+1)),state='readonly').grid(row=row,column=1);self.upgrade_vars.append((shift,mask,v));row+=1
  self.magic=tk.StringVar(value='Keep');ttk.Label(res,text='Magic level').grid(row=row,column=0);ttk.Combobox(res,textvariable=self.magic,values=['Keep','None','Normal','Double'],state='readonly').grid(row=row,column=1)
  inv=page(tr('Objetos y máscaras','Items and masks','Objets et masques','Gegenstände und Masken'))
  for i,label in enumerate(writer.NORMAL+writer.MASK_NAMES):
   current=self.value(0x70+i);options=list(OPTIONS[i]);options+=[] if current in options else [current];labels=[f'{LABELS.get(v,"Unknown")} [{v:02X}]' for v in options];ttk.Label(inv,text=label).grid(row=i,column=0,sticky='w');combo=ttk.Combobox(inv,values=labels,width=40,state='readonly');combo.grid(row=i,column=1,pady=3);combo.current(options.index(current));self.items[i]=(combo,options)
  songpage=page(tr('Canciones','Songs','Chants','Lieder'))
  for row,(bit,label) in enumerate(songs.SONGS):v=tk.BooleanVar(value=bool(self.value(0xbc,4)&(1<<bit)));ttk.Checkbutton(songpage,text=label,variable=v).grid(row=row,column=0,sticky='w');self.songvars[bit]=v
  raw=self.raw(offset(0xf66),128)
  try:notes,_=songs.decode(raw)
  except ValueError:notes=[]
  self.original_notes=notes;self.scarecrow=tk.BooleanVar(value=bool(self.value(offset(0xf65))));self.original_active=self.scarecrow.get();ttk.Checkbutton(songpage,text="Scarecrow active this cycle",variable=self.scarecrow).grid(row=12,column=0,sticky='w')
  for i in range(8):combo=ttk.Combobox(songpage,values=['A','C↓','C→','C←','C↑'],state='readonly',width=5);combo.grid(row=13,column=i,pady=15);combo.current(notes[i] if len(notes)==8 else 0);self.notevars.append(combo)
  self.edit_notes=tk.BooleanVar();ttk.Checkbutton(songpage,text='Replace eight-note melody',variable=self.edit_notes).grid(row=14,column=0,columnspan=5,sticky='w')
  for group in sorted(set(f['group'] for f in FIELDS if f['group']!='Lectura')):
   body=page(group)
   for row,f in enumerate(f for f in FIELDS if f['group']==group):
    v=self.value(offset(f['offset']),f['size']);v=int(bool(v&f['mask'])) if f['mask'] is not None else v
    if f['signed'] and v>=128:v-=256
    var=tk.StringVar(value=str(v));ttk.Label(body,text=f['label']).grid(row=row,column=0,sticky='w');ttk.Spinbox(body,textvariable=var,from_=f['minimum'],to=f['maximum'],width=12).grid(row=row,column=1,pady=3,padx=20);self.progress[f['key']]=(var,v)
  collectionpage=page(tr('Coleccionables individuales','Individual collections','Collectes individuelles','Einzelne Sammelobjekte'))
  self.individual=ttk.Treeview(collectionpage,columns=('name','owned'),show='headings',height=20);self.individual.heading('name',text='Collectible');self.individual.heading('owned',text='0 / 1');self.individual.column('name',width=650);self.individual.column('owned',width=70);self.individual.pack(fill='both',expand=True);self.collection_original={}
  def add(key,label,on):self.collection_original[key]=int(on);self.individual.insert('','end',iid=key,values=(label,int(on)))
  for i,h in enumerate(CATALOG['hearts']):add('heart:'+str(i),h['name'],bool(self.value(h['offset'])&(1<<h['bit'])))
  for i,scene in enumerate(CATALOG['bosses']):add('boss:'+str(i),'Boss container '+str(i+1),bool(self.value(0xf8+scene*28+16,4)&0x80000000))
  for i,f in enumerate(CATALOG['fairies']):add('fairy:'+str(i),'Fairy '+str(f['group']+1)+' / '+str(i+1),bool(self.value(0xf8+f['scene']*28+extras_writer.loc.PERM[f['field']],4)&(1<<f['flag'])))
  for entry in CATALOG['skulls']:
   for i in range(30):add('skull:'+str(entry['group']*30+i),'Skulltula '+str(entry['group']+1)+' / '+str(i+1),bool(self.value(0xf8+entry['scene']*28,4)&(1<<i)))
  self.individual.bind('<Double-1>',self.toggle_collection)
  photo=page(tr('Fotografía','Photo','Photographie','Foto'))
  ttk.Button(photo,text=tr('Importar PNG/PGM 160 × 112','Import PNG/PGM 160 × 112','Importer PNG/PGM 160 × 112','PNG/PGM 160 × 112 importieren'),command=self.import_photo).pack(anchor='w')
  ttk.Button(photo,text=tr('Exportar fotografía PGM','Export photo PGM','Exporter photo PGM','Foto als PGM exportieren'),command=self.export_photo).pack(anchor='w',pady=10)
  ttk.Label(photo,text=tr('Los píxeles importados no validan el sujeto para misiones.','Imported pixels do not establish quest subject validity.','Les pixels importés ne valident pas le sujet des quêtes.','Importierte Pixel bestätigen kein Quest-Motiv.'),wraplength=1000).pack(anchor='w')
  tech=page(tr('Ciclo y datos técnicos','Cycle and technical data','Cycle et données techniques','Zyklus und technische Daten'))
  info=f"NZSJ 1.1\nSaveContext {self.report['detected_profile']['save_address']}\nSave size 0x1390 / checksum +0x138E\nDay {self.value(0x18,4)} / time 0x{self.value(0xc,2):04X}\nScarecrow +0x12E9 / recording +0x12EA\nMagic runtime +0x42AC / cycleSceneFlags +0x42F4\n"
  info+=tr('Avance del ciclo: pendiente. Reinicio nativo disponible desde el diálogo. Recarga de escena/equipo: pendiente. Colecciones individuales disponibles. Todo al máximo conserva flags de misiones y recogida.','Cycle advance: pending. Native reset available from confirmation dialog. Scene reload/equipment: pending. Individual collection flags available. Maximum resources preserves quest and pickup flags.','Avance et retour du cycle: recherche japonaise en attente. Collectes individuelles: en attente. Maximum conserve les événements.','Zyklus und einzelne Sammelobjekte: japanische Prüfung ausstehend. Maximum erhält Quest- und Sammelflags.')
  ttk.Label(tech,text=info,wraplength=1000).pack(anchor='w')
  self.resetbutton=ttk.Checkbutton(tech,text=tr('Volver al primer día · confirmación nativa','Return to first day · native confirmation','Retour au premier jour · confirmation native','Zum ersten Tag · native Bestätigung'),variable=self.resetvar)
  self.resetbutton.pack(anchor='w',pady=12)
  try:reset_writer.locate(name,data)
  except ValueError:self.resetbutton.configure(state='disabled')
  ttk.Label(tech,text=tr('Requiere una captura en el diálogo Sí/No de la Canción del Tiempo. Reproduce la rama nativa; el botón editado aún no se ha probado en consola.','Requires a capture at the Song of Time YES/NO dialog. Uses the native branch; edited button output has not been console tested.','Capture au dialogue Oui/Non requise; sortie du bouton non testée sur console.','Aufnahme beim Ja/Nein-Dialog erforderlich; Button-Ausgabe noch nicht auf Konsole geprüft.'),wraplength=1000).pack(anchor='w')
  self.review=writer.ttk.Treeview(self.book,columns=('field','before','after'),show='headings');self.book.add(self.review,text=tr('Révision','Review','Révision','Prüfung'))
  for key in ('field','before','after'):self.review.heading(key,text=key)
  toolbar=ttk.Frame(self.root,padding=14);toolbar.pack(fill='x');ttk.Button(toolbar,text=tr('Recursos al máximo','Maximum resources','Ressources au maximum','Maximale Ressourcen'),command=self.maximum).pack(side='left');ttk.Button(toolbar,text=tr('Revisar cambios','Review changes','Vérifier','Änderungen prüfen'),command=self.preview).pack(side='left',padx=10);ttk.Button(toolbar,text=parent.t('export'),command=self.save).pack(side='right')
 def raw(self,off,n):b=int(self.report['rdram_png_offset'],16)+int(self.report['save_ram_offset'],16);return self.data[b+off:b+off+n]
 def value(self,off,n=1):return int.from_bytes(self.raw(off,n),'big')
 def collect(self):
  ext={}
  for k,v in self.vars.items():
   value=v.get() if k in ('playerName','bomberCode','lotteryCodes','spiderOrder') else int(float(v.get())*16) if k in ('health','healthCapacity') else int(v.get())
   if k in ('health','healthCapacity') and float(v.get())*16!=value:raise ValueError('Heart amount must use exact quarter-heart units')
   if value!=self.original[k] and k!='rupees':ext[k]=value
  upgrades=self.value(0xb8,4)
  for shift,mask,var in self.upgrade_vars:upgrades=(upgrades&~(mask<<shift))|(int(var.get())<<shift)
  if upgrades!=self.value(0xb8,4):ext['upgrades']=upgrades
  if self.magic.get()!='Keep':ext['magicMode']=['None','Normal','Double'].index(self.magic.get());ext['magicCurrent']=int(self.vars['magicCurrent'].get())
  for i,(combo,options) in self.items.items():
   v=options[combo.current()]
   if v!=self.value(0x70+i):ext['item_'+str(i)]=v
  patches={k:int(v.get()) for k,(v,orig) in self.progress.items() if int(v.get())!=orig}
  if patches:ext['progress']=patches
  bits=sum(1<<bit for bit,var in self.songvars.items() if var.get());song={}
  if bits!=(self.value(0xbc,4)&songs.MASK):song['song_bits']=bits
  if self.edit_notes.get():song['scarecrow_notes']=[c.current() for c in self.notevars]
  if self.scarecrow.get()!=self.original_active:song['scarecrow_active']=self.scarecrow.get()
  if song:ext['songs']=song
  advanced={}
  if 'spiderOrder' in ext:advanced['spiderOrder']=ext.pop('spiderOrder')
  if self.collection_patches:advanced['collections']=dict(self.collection_patches)
  if self.photo_hex:advanced['photo']=self.photo_hex
  if advanced:ext['advanced']=advanced
  if self.resetvar.get():ext['cycleReset']=True
  return int(self.vars['rupees'].get()),int(self.vars['ammo_9'].get()),ext
 def toggle_collection(self,event):
  key=self.individual.identify_row(event.y)
  if not key:return
  values=self.individual.item(key,'values');v=1-int(values[1]);self.individual.item(key,values=(values[0],v))
  if v==self.collection_original[key]:self.collection_patches.pop(key,None)
  else:self.collection_patches[key]=v
 def import_photo(self):
  path=writer.filedialog.askopenfilename(filetypes=[('PNG / PGM','*.png *.pgm')],parent=self.root.winfo_toplevel())
  if not path:return
  try:
   image=self.tk.PhotoImage(file=path)
   if (image.width(),image.height())!=(160,112):raise ValueError('160 × 112 required')
   pixels=[]
   for y in range(112):
    for x in range(160):
     c=image.get(x,y)
     if isinstance(c,str):c=tuple(map(int,c.split()))
     pixels.append((int(c[0])*299+int(c[1])*587+int(c[2])*114)*31//255000)
   raw=bytearray()
   for i in range(0,len(pixels),8):
    v=0
    for n in pixels[i:i+8]:v=(v<<5)|n
    raw.extend(v.to_bytes(5,'big'))
   self.photo_hex=raw.hex();self.preview()
  except Exception as e:writer.messagebox.showerror(self.parent.t('error'),str(e),parent=self.root.winfo_toplevel())
 def export_photo(self):
  off=0x1390 if self.report['detected_profile']['layout']=='jp-1.1' else 0x10e0;raw=self.raw(off,11200);pixels=bytearray()
  for i in range(0,len(raw),5):
   v=int.from_bytes(raw[i:i+5],'big')
   for shift in range(35,-1,-5):pixels.append(((v>>shift)&31)*255//31)
  path=writer.filedialog.asksaveasfilename(initialfile='Majora-photo.pgm',defaultextension='.pgm',parent=self.root.winfo_toplevel())
  if path:
   try:
    with Path(path).open('xb') as f:f.write(b'P5\n160 112\n255\n'+pixels)
   except Exception as e:writer.messagebox.showerror(self.parent.t('error'),str(e),parent=self.root.winfo_toplevel())
 def maximum(self):
  for k,v in {'healthCapacity':20,'health':20,'magicCurrent':96,'rupees':500,'ammo_1':50,'ammo_6':40,'ammo_7':50,'ammo_8':30,'ammo_9':40,'ammo_10':20}.items():self.vars[k].set(str(v))
  self.magic.set('Double')
  for key in self.collection_original:
   if key.startswith(('heart:','boss:')):
    self.collection_patches[key]=1;values=self.individual.item(key,'values');self.individual.item(key,values=(values[0],1))
  for shift,mask,var in self.upgrade_vars:var.set('2' if shift==12 else '3')
  for i,(combo,options) in self.items.items():
   if self.value(0x70+i)==255:combo.current(options.index(item(writer.MASK_IDS[i-24]) if i>=24 else (0x16 if i>=18 else OPTIONS[i][1])))
  self.preview()
 def preview(self):
  try:
   money,nuts,ext=self.collect();out,changes=edit(self.name,self.data,money,nuts,ext);self.review.delete(*self.review.get_children())
   for c in changes:self.review.insert('','end',values=(c['campo'],c['antes'],c['despues']))
   self.book.select(self.review);return out
  except Exception as e:writer.messagebox.showerror(self.parent.t('error'),str(e),parent=self.root.winfo_toplevel())
 def save(self):
  out=self.preview()
  if out is None:return
  try:
   if hashlib.sha256(self.source.read_bytes()).hexdigest()!=self.source_hash:raise ValueError('Source changed')
   path=writer.filedialog.asksaveasfilename(initialfile=Path(self.name).stem+' - JP copy.zip',defaultextension='.zip',filetypes=[('ZIP','*.zip'),('PNG','*.png')],parent=self.root.winfo_toplevel())
   if path:writer.core.export_copy(self.source,path,self.name,out);writer.messagebox.showinfo(self.parent.t('saved'),str(path),parent=self.root.winfo_toplevel())
  except Exception as e:writer.messagebox.showerror(self.parent.t('error'),str(e),parent=self.root.winfo_toplevel())
