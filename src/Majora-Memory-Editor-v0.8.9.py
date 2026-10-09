"""Player name editing using international native filename character table."""
from pathlib import Path
import sys,importlib.util,json,zipfile,zlib
ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
s=importlib.util.spec_from_file_location('studio086',ROOT/'Majora-Memory-Editor-v0.8.6.py');old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
tk=old.tk;ttk=old.ttk;ui=old.old.old.studio.studio.ui
s=importlib.util.spec_from_file_location('native_names',ROOT/'Majora-Native-Name-Editor.py');native=importlib.util.module_from_spec(s);s.loader.exec_module(native)
s=importlib.util.spec_from_file_location('recovery',ROOT/'Majora-Native-Recovery.py');recovery=importlib.util.module_from_spec(s);s.loader.exec_module(recovery)
CHARS='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz -.'
def decode(raw):return ''.join(CHARS[b]if b<len(CHARS)else f'[{b:02X}]'for b in raw).rstrip(' ')
def encode(text):
 if type(text)!=str or not 1<=len(text)<=8 or not text.strip() or any(c not in CHARS for c in text):raise ValueError('nameRange')
 return bytes(CHARS.index(c)for c in text.ljust(8))
previous=old.edit
def edit(name,data,money,nuts,extra=None):
 extra=dict(extra or {});playername=extra.pop('playerName',None)
 try:result,changes=previous(name,data,money,nuts,extra)
 except ValueError as e:
  if str(e)!='No hay cambios que guardar.':raise
  result,changes=data,[]
 if playername is not None:
  report=ui.base.core.inspector.inspect(name,result);p=report['detected_profile']
  if (p['cartridge'],p['revision'])not in [('NZSE',0),('NZSP',1)]:raise ValueError('nameProfile')
  raw=encode(playername);b=int(report['rdram_png_offset'],16)+int(report['save_ram_offset'],16);out=bytearray(result);allowed=set()
  def put(label,at,raw):
   before=bytes(out[at:at+len(raw)])
   if before!=raw:out[at:at+len(raw)]=raw;allowed.update(range(at,at+len(raw)));changes.append(dict(campo=label,offset_png=hex(at),antes=before.hex(),despues=raw.hex()))
  put('playerName',b+0x2c,raw)
  if out!=result:
   block=bytearray(out[b:b+0x100c]);block[-2:]=bytes(2);put('Save checksum',b+0x100a,(sum(block)&65535).to_bytes(2,'big'))
   p=8
   while p+12<=len(out):
    n=int.from_bytes(out[p:p+4],'big')
    if out[p+4:p+8]==b'apmd':at=p+8+n;out[at:at+4]=(zlib.crc32(out[p+4:at])&0xffffffff).to_bytes(4,'big');allowed.update(range(at,at+4));break
    p+=n+12
   else:raise ValueError('Missing apmd')
   assert len(out)==len(result)and all(i in allowed for i,(a,c)in enumerate(zip(result,out))if a!=c)
   result=bytes(out);ui.base.core.inspector.inspect(name,result)
 if not changes:raise ValueError('No hay cambios que guardar.')
 return result,changes
old.edit=edit;ui.edit=edit
TEXT={
 'name':('Nombre del jugador','Player name','Nom du joueur'),
 'help':('Nombre activo del Memory. El menú lee el guardado normal del cartucho. En flashcart puedes renombrar el .sav en Guardado nativo. En cartucho original, la Canción del Tiempo guarda el nombre normal y reinicia el ciclo; guardar en un búho no actualiza ese nombre.','Active Memory name. The menu reads the cartridge normal save. For flashcarts, rename the .sav in Native save. For original cartridges, Song of Time writes the normal name and resets the cycle; owl saving does not update that name.','Nom actif du Memory. Le menu lit la sauvegarde normale de la cartouche. Sur flashcart, renommez le .sav dans Sauvegarde native. Sur cartouche originale, le Chant du Temps enregistre le nom normal et réinitialise le cycle ; une sauvegarde à la statue ne met pas ce nom à jour.'),
 'nameRange':('Nombre: usa de 1 a 8 caracteres permitidos; no puede contener solo espacios.','Name: use 1–8 supported characters; spaces alone are not allowed.','Nom : utiliser 1 à 8 caractères autorisés ; pas uniquement des espaces.'),
 'nameProfile':('Edición del nombre disponible para USA 1.0 y PAL 1.1 investigados.','Name editing supports researched USA 1.0 and PAL 1.1.','Nom modifiable pour USA 1.0 et PAL 1.1 étudiés.')}
class App(old.App):
 def nt(self,key):return TEXT[key][self.language]
 def build(self):
  self.native_path=getattr(self,'native_path',None);self.native_raw=getattr(self,'native_raw',None)
  pending=self.native_name.get() if hasattr(self,'native_name') else ''
  restore=self.native_restore.get() if hasattr(self,'native_restore') else False
  self.namevar=None;super().build();self.root.title('Majora · Memory Studio 0.8.9')
  page=self.book.nametowidget(self.book.tabs()[0]);grid=next(w for w in page.winfo_children()if isinstance(w,ttk.Frame));row=grid.grid_size()[1]
  self.namevar=tk.StringVar();self.vars['playerName']=self.namevar
  ttk.Label(grid,text=self.nt('name'),width=25).grid(row=row,column=0,sticky='w',pady=8)
  self.nameentry=ttk.Entry(grid,textvariable=self.namevar,width=18);self.nameentry.grid(row=row,column=1,padx=15)
  ttk.Label(grid,text=self.nt('help'),wraplength=650,foreground='#c3a66a').grid(row=row+1,column=0,columnspan=3,sticky='w',pady=5)
  self.populate();self.update_preview();self.build_native(pending,restore)
 def name_raw(self):
  b=int(self.report['rdram_png_offset'],16)+int(self.report['save_ram_offset'],16);return self.data[b+0x2c:b+0x34]
 def populate(self):
  super().populate()
  if self.namevar is None:return
  self.namevar.set(self.extra.get('playerName',decode(self.name_raw()))if self.data else '')
  enabled=self.data and (self.report['detected_profile']['cartridge'],self.report['detected_profile']['revision'])in [('NZSE',0),('NZSP',1)]
  self.nameentry.configure(state='normal'if enabled else 'disabled')
 def collect(self):
  extra,money,nuts=super().collect()
  if self.namevar is not None and self.data:
   name=self.namevar.get()
   if name!=decode(self.name_raw()):encode(name);extra['playerName']=name
  return extra,money,nuts
 def maximum(self):
  name=self.namevar.get()if self.namevar is not None else None;super().maximum()
  if name is not None:self.namevar.set(name);self.update_preview()
 def describe(self,c):
  if c['campo']=='playerName':return self.nt('name'),decode(bytes.fromhex(c['antes'])),decode(bytes.fromhex(c['despues']))
  return super().describe(c)
 def error_text(self,e):return self.nt(str(e))if str(e)in TEXT else super().error_text(e)
 def save(self):
  if self.data is None:return
  try:
   import hashlib
   if hashlib.sha256(self.source.read_bytes()).hexdigest()!=self.source_hash:raise ValueError(self.t('changedSource'))
   extra,money,nuts=self.collect();patched,changes=edit(self.choice_name,self.data,money,nuts,extra)
   self.book.select(5)
   dest=ui.filedialog.asksaveasfilename(title=self.t('export'),initialfile=Path(self.choice_name).stem+' - copy-v089.zip',defaultextension='.zip',filetypes=[('ZIP','*.zip'),('PNG','*.png')])
   if not dest:return
   ui.base.core.export_copy(self.source,dest,self.choice_name,patched)
   self.status.set(self.t('saved')+': '+dest);ui.messagebox.showinfo(self.t('saved'),self.t('savedBody'))
  except Exception as e:ui.messagebox.showerror(self.t('error'),self.error_text(e))
 def native_text(self,es,en,fr):return (es,en,fr)[self.language]
 def build_native(self,pending,restore):
  page=ttk.Frame(self.book,padding=18);self.book.add(page,text=self.native_text('Guardado nativo','Native save','Sauvegarde native'))
  ttk.Label(page,text=self.native_text('Nombre de la selección de partida · Flashcart .sav','File-selection name · Flashcart .sav','Nom du menu de sélection · Flashcart .sav'),font=('Segoe UI',12,'bold')).pack(anchor='w')
  ttk.Label(page,text=self.native_text('Abre un Flash nativo internacional de 128 KB. Se exporta una copia; no se sobrescribe el original. La región exacta no se identifica a partir del .sav.','Open an international 128 KB native Flash save. Exports a copy; the original is preserved. Exact region cannot be identified from the .sav.','Ouvrez une sauvegarde Flash internationale de 128 Ko. Export en copie ; original conservé. La région exacte ne peut pas être identifiée dans le .sav.'),wraplength=900).pack(anchor='w',pady=8)
  ttk.Button(page,text=self.native_text('Abrir .sav…','Open .sav…','Ouvrir .sav…'),command=self.open_native).pack(anchor='w')
  self.native_file=tk.StringVar(value=str(self.native_path or ''));ttk.Label(page,textvariable=self.native_file,wraplength=900).pack(anchor='w',pady=6)
  row=ttk.Frame(page);row.pack(fill='x',pady=8)
  self.native_slot=ttk.Combobox(row,state='readonly',values=[self.native_text('Partida 1','File 1','Fichier 1'),self.native_text('Partida 2','File 2','Fichier 2')],width=12);self.native_slot.current(getattr(self,'native_index',0));self.native_slot.pack(side='left');self.native_slot.bind('<<ComboboxSelected>>',self.native_refresh)
  self.native_name=tk.StringVar(value=pending);ttk.Entry(row,textvariable=self.native_name,width=18).pack(side='left',padx=14)
  ttk.Button(row,text=self.native_text('Usar nombre del Memory','Use Memory name','Utiliser le nom du Memory'),command=self.native_use_memory).pack(side='left')
  self.native_summary=tk.StringVar();ttk.Label(page,textvariable=self.native_summary,wraplength=900).pack(anchor='w',pady=8)
  self.native_review=tk.StringVar();ttk.Label(page,textvariable=self.native_review,wraplength=900,foreground='#c3a66a').pack(anchor='w',pady=8)
  self.native_restore=tk.BooleanVar(value=restore)
  self.native_restore_button=ttk.Checkbutton(page,text=self.native_text('Recuperar partida de búho consumida (no reinicia el ciclo)','Recover consumed owl save (does not reset cycle)','Récupérer la sauvegarde à la statue consommée (sans réinitialiser le cycle)'),variable=self.native_restore,command=self.native_refresh);self.native_restore_button.pack(anchor='w',pady=5)
  self.native_export=ttk.Button(page,text=self.native_text('Exportar copia .sav…','Export .sav copy…','Exporter une copie .sav…'),command=self.save_native,style='Accent.TButton');self.native_export.pack(anchor='w',pady=8)
  ttk.Label(page,text=self.native_text('Solo cambia nombres y checksums de la partida elegida. Conserva corazones, máscaras, inventario y ciclo. La recuperación exige datos coherentes y dos bloques de búho idénticos con checksum válido. Para instalar la copia en el flashcart, conserva el nombre y la carpeta del .sav original.','Only names and checksums in the selected file change. Hearts, masks, inventory and cycle are preserved. Recovery requires coherent data and two identical checksum-valid owl records. To install on a flashcart, preserve the original .sav filename and folder.','Seuls les noms et checksums du fichier choisi changent. Cœurs, masques, inventaire et cycle sont conservés. La récupération exige des données cohérentes et deux blocs identiques avec checksum valide. Pour installer sur flashcart, conservez le nom et le dossier du .sav original.'),wraplength=900).pack(anchor='w',pady=12)
  self.native_name.trace_add('write',lambda *args:self.native_refresh())
  self.native_refresh()
 def open_native(self):
  path=ui.filedialog.askopenfilename(filetypes=[('Native Flash save','*.sav *.bin *.fla'),('All files','*.*')])
  if not path:return
  try:
   raw=Path(path).read_bytes();native.inspect(raw)
   self.native_path=Path(path);self.native_raw=raw;self.native_file.set(path);self.native_slot.current(0);self.native_index=0;self.native_restore.set(False)
   self.native_refresh();self.native_name.set(self.native_records[0]['name'])
  except Exception as e:ui.messagebox.showerror(self.t('error'),str(e))
 def native_use_memory(self):
  if self.data:self.native_name.set(self.namevar.get())
 def native_refresh(self,event=None):
  self.native_index=self.native_slot.current();self.native_export.configure(state='disabled');self.native_restore_button.configure(state='disabled');self.native_review.set('')
  if event is not None:self.native_restore.set(False)
  if self.native_raw is None:
   self.native_summary.set(self.native_text('Aún no hay un .sav abierto.','No .sav open yet.','Aucun .sav ouvert.'));return
  order,data,slots=native.inspect(self.native_raw);records=slots[self.native_index];self.native_records=records
  if not all(r['valid'] for r in records[:2]):
   self.native_summary.set(self.native_text('Guardado normal o respaldo vacío/no válido. No se reconstruye desde el Memory.','Normal save or backup empty/invalid. Not reconstructed from the Memory.','Sauvegarde normale ou secours vide/invalide. Pas de reconstruction depuis le Memory.'));return
  info=recovery.overview(self.native_raw,self.native_index+1)
  states={'valid':self.native_text('válido','valid','valide'),'consumed':self.native_text('consumido','consumed','consommé'),'empty':self.native_text('vacío','empty','vide'),'invalid':self.native_text('no válido','invalid','invalide')}
  rows=[]
  labels=[self.native_text('Normal','Normal','Normale'),self.native_text('Respaldo normal','Normal backup','Secours normal'),self.native_text('Búho','Owl','Statue'),self.native_text('Respaldo búho','Owl backup','Secours statue')]
  for label,r in zip(labels,info['records']):
   text=label+': '+states[r['state']];p=r['progress']
   if p:text+=' · '+p['name']+self.native_text(' · corazones ',' · hearts ',' · cœurs ')+str(p['hearts'])+self.native_text(' · máscaras ',' · masks ',' · masques ')+str(p['masks'])+self.native_text(' · día ',' · day ',' · jour ')+str(p['day'])
   rows.append(text)
  self.native_summary.set('\n'.join(rows))
  if info['recovery_available']:self.native_restore_button.configure(state='normal')
  elif self.native_restore.get():self.native_restore.set(False)
  try:
   result,report=self.native_plan()
   if result==self.native_raw:return
   names=' / '.join(r['name'] for r in records[:2])
   self.native_review.set(self.native_text('Nombre del menú: ','Menu name: ','Nom du menu : ')+names+' → '+self.native_name.get()+(self.native_text(' · Recuperar búho conservando su progreso y ciclo.',' · Recover owl progress and cycle.',' · Récupérer le progrès et le cycle de la statue.') if self.native_restore.get() else ''))
   self.native_export.configure(state='normal')
  except ValueError:pass
 def native_plan(self):
  raw=self.native_raw;recovered=None
  if self.native_restore.get():raw,recovered=recovery.recover(raw,self.native_index+1)
  result,report=native.rename(raw,self.native_index+1,self.native_name.get())
  if recovered:report['recovery']=recovered
  return result,report
 def save_native(self):
  try:
   if self.native_raw is None:return
   if self.native_path.read_bytes()!=self.native_raw:raise ValueError(self.t('changedSource'))
   result,report=self.native_plan()
   dest=ui.filedialog.asksaveasfilename(initialfile=self.native_path.stem+' - renamed.sav',defaultextension='.sav',filetypes=[('Native Flash save','*.sav')])
   if not dest:return
   path=Path(dest)
   if path.resolve()==self.native_path.resolve():raise ValueError(self.native_text('Exporta a otro archivo; el original se conserva.','Export to a different file; preserve the original.','Exportez vers un autre fichier ; conservez l’original.'))
   with path.open('xb') as f:f.write(result)
   assert path.read_bytes()==result;native.inspect(result)
   path.with_name(path.name+'.report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
   ui.messagebox.showinfo(self.t('saved'),self.native_text('Copia .sav exportada. Instálala en el flashcart con el nombre del original; conserva un respaldo.','Exported .sav copy. Install on flashcart under the original filename; keep a backup.','Copie .sav exportée. Installez-la sur flashcart sous le nom original ; gardez une copie de secours.'))
  except Exception as e:ui.messagebox.showerror(self.t('error'),str(e))
if __name__=='__main__':
 root=tk.Tk()
 if len(sys.argv)==4 and sys.argv[1]=='--self-test':
  root.withdraw();app=App(root)
  with zipfile.ZipFile(sys.argv[2])as z:name='despues.png';data=z.read(name)
  app.memories={name:data};app.choice.configure(values=[name]);app.choice.current(0);app.select();app.namevar.set('Alex');app.update_preview();assert app.valid
  e,m,n=app.collect();edited,changes=edit(name,data,m,n,e)
  for lang in range(3):app.extra=e;app.language=lang;app.build();root.update_idletasks();assert app.namevar.get()=='Alex'and app.valid
  import tempfile,hashlib
  app.source=Path(sys.argv[2]);app.source_hash=hashlib.sha256(app.source.read_bytes()).hexdigest()
  errors=[];orig_dialog=ui.filedialog.asksaveasfilename;orig_info=ui.messagebox.showinfo;orig_error=ui.messagebox.showerror
  with tempfile.TemporaryDirectory()as folder:
   dest=Path(folder)/'export.zip';ui.filedialog.asksaveasfilename=lambda **kw:str(dest);ui.messagebox.showinfo=lambda *a,**kw:None;ui.messagebox.showerror=lambda *a,**kw:errors.append(a)
   try:app.save()
   finally:ui.filedialog.asksaveasfilename=orig_dialog;ui.messagebox.showinfo=orig_info;ui.messagebox.showerror=orig_error
   assert not errors,errors
   assert dest.is_file()
   with zipfile.ZipFile(dest)as z:exported=z.read(name)
   assert exported==edited
  assert hashlib.sha256(app.source.read_bytes()).hexdigest()==app.source_hash
  Path(sys.argv[3]).write_text(json.dumps({'version':'0.8.9','languages':3,'playerName':'Alex','changes':len(changes),'actual_export':'passed','source_unchanged':True}));root.destroy()
 else:App(root);root.mainloop()

