"""Majora Memory Studio 0.7.1: songs and Scarecrow, PAL NZSP rev1."""
from pathlib import Path
import sys,importlib.util,json,zipfile,hashlib
ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
def module(name,file):
 spec=importlib.util.spec_from_file_location(name,ROOT/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
ui=module('studio06','Majora-Memory-Editor-v0.6.py')
songs=module('song_writer','Majora-songs.py')
config=json.loads((ROOT/'Majora-song-config.json').read_text(encoding='utf8'))
SONATA=bytes.fromhex(config['sonata_signature'])
def original_edit(name,data,money,nuts,extra):
 extra=dict(extra);groups={k.removeprefix('complete_') for k,v in extra.items() if k.startswith('complete_') and v}
 extra={k:v for k,v in extra.items() if not k.startswith('complete_')}
 if extra.get('healthCapacity')==320:groups.add('hearts')
 try:result,changes=ui.base.edit(name,data,money,nuts,extra)
 except ValueError as e:
  if str(e)!='No hay cambios que guardar.':raise
  result,changes=data,[]
 if groups:
  report=ui.base.core.inspector.inspect(name,result)
  result,flags,_=ui.collections.apply(result,report,groups);changes+=flags
 if not changes:raise ValueError('No hay cambios que guardar.')
 return result,changes
def edit(name,data,money,nuts,extra=None):
 extra=dict(extra or {});musical={k:extra.pop(k) for k in list(extra) if k in ('song_bits','scarecrow_notes','scarecrow_active')}
 try:result,changes=original_edit(name,data,money,nuts,extra)
 except ValueError as e:
  if str(e)!='No hay cambios que guardar.':raise
  result,changes=data,[]
 report=ui.base.core.inspector.inspect(name,result)
 profile=report['detected_profile'];key=f"{profile['cartridge']}:{profile['revision']}"
 selected=config['profiles'].get(key)
 if musical and selected is None:raise ValueError('Songs: unsupported revision.')
 signature=bytes.fromhex(selected['sonata_signature']) if selected else SONATA
 template=bytes.fromhex(selected['recording_template']) if selected else None
 result,more=songs.apply(result,report,musical,signature,template);changes+=more
 if not changes:raise ValueError('No hay cambios que guardar.')
 ui.base.core.inspector.inspect(name,result)
 return result,changes
ui.edit=edit
tk=ui.tk;ttk=ui.ttk
TEXT={
 'tab':('Canciones','Songs','Chants'),
 'help':('Canciones aprendidas y melodía del espantapájaros. Exporta una copia para probarla en Analogue 3D.','Learned songs and Scarecrow melody. Export a copy to test on Analogue 3D.','Chants appris et mélodie de l’épouvantail. Exportez une copie à tester sur Analogue 3D.'),
 'all':('Marcar todas las canciones','Select all learned songs','Sélectionner tous les chants'),
 'derived':('Canción del Tiempo invertida y doble: disponibles con la Canción del Tiempo.','Inverted Song of Time and Song of Double Time: available with Song of Time.','Chant du Temps inversé et Chant du Temps accéléré : disponibles avec le Chant du Temps.'),
 'scare':('Espantapájaros · ocho notas','Scarecrow · eight notes','Épouvantail · huit notes'),
 'choose':('Elegir','Choose','Choisir'),
 'active':('Activa en este ciclo','Active this cycle','Actif dans ce cycle'),
 'retain':('La melodía guardada puede sobrevivir al reinicio; la activación se pierde. Habla con el espantapájaros si aún no está preparado en esa zona.','The stored melody can survive a cycle reset; activation does not. Talk to the Scarecrow if it is not prepared in that area.','La mélodie enregistrée peut survivre au retour au premier jour ; son activation est effacée. Parlez à l’épouvantail si la zone n’est pas encore préparée.'),
 'scopeUSA':('USA retail NZSE 1.0 · estructuras localizadas; edición pendiente de prueba física.','USA retail NZSE 1.0 · structures located; edited export awaits console validation.','USA commercial NZSE 1.0 · structures localisées ; export modifié à valider sur console.'),
 'scope':('PAL retail NZSP 1.1 · estructuras localizadas; edición pendiente de prueba física.','PAL retail NZSP 1.1 · structures located; edited export awaits console validation.','PAL commercial NZSP 1.1 · structures localisées ; export modifié à valider sur console.'),
 'unsupported':('Lectura disponible. Edición de canciones pendiente para esta versión.','Read-only. Song editing is pending for this version.','Lecture seule. Modification des chants en attente pour cette version.'),
 'empty':('No hay ocho notas canónicas guardadas. Elige una secuencia completa para crearla.','No eight canonical notes stored. Choose a complete sequence to create it.','Aucune séquence de huit notes canoniques enregistrée. Choisissez huit notes pour la créer.'),
 'recorded':('Grabación guardada: ','Stored recording: ','Enregistrement conservé : '),
 'learned':('Canciones aprendidas','Learned songs','Chants appris'),
 'melody':('Melodía del espantapájaros','Scarecrow melody','Mélodie de l’épouvantail'),
 'sync':('Sincronización de audio y reconocimiento','Audio and recognition synchronization','Synchronisation audio et reconnaissance'),
 'checksum':('Checksum de partida','Save checksum','Somme de contrôle de sauvegarde'),
}
NAMES_ES=['Sonata del Despertar','Nana Goron','Bossa Nova de las Olas','Elegía al Vacío','Oda al Orden','Canción del Tiempo','Canción de Curación','Canción de Epona','Canción del Vuelo','Canción de las Tormentas','Introducción de la Nana Goron']
NAMES_FR=['Sonate de l’Éveil','Berceuse des Gorons','Bossa Nova des Flots','Hymne du Vide','Ode de l’Appel','Chant du Temps','Chant de l’Apaisement','Chant d’Epona','Chant de l’Envol','Chant des Tempêtes','Introduction de la Berceuse des Gorons']
DISPLAY=('A','C↓','C→','C←','C↑')

class App(ui.App):
 def st(self,key):
  if key=='scope' and self.data is not None and self.report['detected_profile']['cartridge']=='NZSE':key='scopeUSA'
  return TEXT[key][self.language]
 def error_text(self,error):
  messages={
   'Scarecrow: choose exactly eight notes.':('Elige las ocho notas del espantapájaros.','Choose all eight Scarecrow notes.','Choisissez les huit notes de l’épouvantail.'),
   'Scarecrow: all eight notes cannot be identical.':('Las ocho notas no pueden ser iguales.','The eight notes cannot all be identical.','Les huit notes ne peuvent pas toutes être identiques.'),
   'Scarecrow: sequence contains a reserved song.':('La secuencia contiene una canción reservada del juego.','The sequence contains a reserved game song.','La séquence contient un chant réservé du jeu.'),
   'Scarecrow: audio signature is missing or ambiguous.':('No se han identificado de forma única las tablas de audio.','Audio tables could not be uniquely identified.','Les tables audio n’ont pas été identifiées de façon unique.'),
   'Scarecrow: live song pointer not verified.':('No se ha verificado el puntero de la canción activa.','The live song pointer could not be verified.','Le pointeur du chant actif n’a pas pu être vérifié.'),
   'Scarecrow: altered pitches require native recording.':('Esta grabación usa notas alteradas; vuelve a grabarla en el juego.','This recording uses altered pitches; record it again in the game.','Cet enregistrement utilise des notes altérées ; réenregistrez-le dans le jeu.'),
  }
  if str(error) in messages:return messages[str(error)][self.language]
  return super().error_text(error)
 def build(self):
  self.songvars={};self.notevars=[];self.scare_active=None
  super().build();self.root.title('Majora · Memory Studio 0.7.1')
  page=ttk.Frame(self.book,padding=16);self.book.add(page,text=self.st('tab'))
  ttk.Label(page,text=self.st('help'),wraplength=950).pack(anchor='w',pady=(0,10))
  grid=ttk.Frame(page);grid.pack(anchor='w')
  for i,(bit,name) in enumerate(songs.SONGS):
   label=[NAMES_ES[i],name,NAMES_FR[i]][self.language]
   v=tk.BooleanVar();self.songvars[bit]=v
   ttk.Checkbutton(grid,text=label,variable=v,command=self.update_preview).grid(row=i%6,column=i//6,sticky='w',padx=(0,45),pady=4)
  self.all_songs=ttk.Button(page,text=self.st('all'),command=self.select_songs);self.all_songs.pack(anchor='w',pady=8)
  ttk.Label(page,text=self.st('derived'),wraplength=940,foreground='#c3a66a').pack(anchor='w')
  box=ttk.LabelFrame(page,text=self.st('scare'),padding=14);box.pack(fill='x',pady=(15,10))
  self.song_info=ttk.Label(box,wraplength=910);self.song_info.pack(anchor='w',pady=(0,10))
  row=ttk.Frame(box);row.pack(anchor='w')
  for i in range(8):
   col=ttk.Frame(row);col.pack(side='left',padx=(0,10))
   ttk.Label(col,text=str(i+1),foreground='#c3a66a').pack()
   combo=ttk.Combobox(col,values=[self.st('choose')]+list(DISPLAY),state='readonly',width=7)
   combo.current(0);combo.pack();combo.bind('<<ComboboxSelected>>',lambda event:self.update_preview());self.notevars.append(combo)
  self.scare_active=tk.BooleanVar()
  self.active_button=ttk.Checkbutton(box,text=self.st('active'),variable=self.scare_active,command=self.update_preview);self.active_button.pack(anchor='w',pady=10)
  ttk.Label(box,text=self.st('retain'),wraplength=910,foreground='#bac6d4').pack(anchor='w')
  self.song_scope=ttk.Label(page,wraplength=940,foreground='#c3a66a');self.song_scope.pack(anchor='w',pady=5)
  self.populate();self.update_preview()
 def populate(self):
  super().populate()
  if not self.songvars or self.scare_active is None:return
  ready=self.data is not None
  enabled=ready and songs.supported(self.report)
  self.all_songs.configure(state='normal' if enabled else 'disabled')
  self.active_button.configure(state='normal' if enabled else 'disabled')
  for w in self.notevars:w.configure(state='readonly' if enabled else 'disabled')
  # Disable the learned-song checkboxes as well when the profile is unverified.
  for w in self.all_songs.master.winfo_children():
   if isinstance(w,ttk.Frame):
    for child in w.winfo_children():
     if isinstance(child,ttk.Checkbutton):child.configure(state='normal' if enabled else 'disabled')
  if not ready:
   for v in self.songvars.values():v.set(False)
   for w in self.notevars:w.current(0)
   self.scare_active.set(False);self.song_info.configure(text=self.st('empty'));self.song_scope.configure(text=self.st('unsupported'));return
  q=self.extra.get('song_bits',self.value(0xbc,4))
  for bit,v in self.songvars.items():v.set(bool(q&(1<<bit)))
  b=int(self.report['rdram_png_offset'],16)+int(self.report['save_ram_offset'],16)
  delta=0x384 if self.report['detected_profile']['layout']=='jp-1.1' else 0
  raw=self.data[b+0xf66+delta:b+0xfe6+delta]
  try:notes,_=songs.decode(raw)
  except ValueError:notes=[]
  notes=self.extra.get('scarecrow_notes',notes)
  for i,w in enumerate(self.notevars):w.current(notes[i]+1 if len(notes)==8 else 0)
  self.scare_active.set(self.extra.get('scarecrow_active',bool(self.value(0xf65+delta))))
  self.song_info.configure(text=self.st('recorded')+'  ·  '.join(DISPLAY[n] for n in notes) if len(notes)==8 else self.st('empty'))
  self.song_scope.configure(text=self.st('scope') if enabled else self.st('unsupported'))
 def collect(self):
  extra,money,nuts=super().collect()
  if self.data is None or not self.songvars or self.scare_active is None or not songs.supported(self.report):return extra,money,nuts
  bits=sum(1<<bit for bit,v in self.songvars.items() if v.get())
  if bits!=self.value(0xbc,4)&songs.MASK:extra['song_bits']=bits
  selected=[w.current()-1 for w in self.notevars]
  b=int(self.report['rdram_png_offset'],16)+int(self.report['save_ram_offset'],16)
  try:old,_=songs.decode(self.data[b+0xf66:b+0xfe6])
  except ValueError:old=[]
  if any(n>=0 for n in selected) and selected!=old:
   if any(n<0 for n in selected):raise ValueError('Scarecrow: choose exactly eight notes.')
   extra['scarecrow_notes']=selected
  if self.scare_active.get()!=bool(self.value(0xf65)):extra['scarecrow_active']=self.scare_active.get()
  return extra,money,nuts
 def select_songs(self):
  for v in self.songvars.values():v.set(True)
  self.update_preview()
 def change_language(self,event=None):
  selected=[w.current() for w in self.notevars];bits={k:v.get() for k,v in self.songvars.items()};active=self.scare_active.get() if self.scare_active is not None else False
  super().change_language(event)
  for w,i in zip(self.notevars,selected):w.current(i)
  for bit,value in bits.items():self.songvars[bit].set(value)
  if self.scare_active is not None:self.scare_active.set(active)
  self.update_preview()
 def maximum(self):
  super().maximum()
  if self.data is not None and songs.supported(self.report):self.select_songs()
 def describe(self,change):
  field=change['campo']
  if field=='Learned songs':
   a=int(change['antes'],16);b=int(change['despues'],16)
   return self.st('learned'),str(sum(bool(a&(1<<bit))for bit,_ in songs.SONGS)),str(sum(bool(b&(1<<bit))for bit,_ in songs.SONGS))
  if field=='Scarecrow recording':
   def fmt(raw):
    try:n,_=songs.decode(bytes.fromhex(raw));return ' '.join(DISPLAY[i]for i in n)
    except ValueError:return '—'
   return self.st('melody'),fmt(change['antes']),fmt(change['despues'])
  if field=='Scarecrow active this cycle':return self.st('active'),str(int(change['antes'],16)),str(int(change['despues'],16))
  if field in ('Scarecrow live audio','Scarecrow recognition'):return self.st('sync'),'—','✓'
  if field=='Save checksum':return self.st('checksum'),change['antes'],change['despues']
  return super().describe(change)
 def save(self):
  if self.data is None:return
  try:
   if hashlib.sha256(self.source.read_bytes()).hexdigest()!=self.source_hash:raise ValueError(self.t('changedSource'))
   e,money,nuts=self.collect();patched,changes=edit(self.choice_name,self.data,money,nuts,e)
   self.book.select(5)
   dest=ui.filedialog.asksaveasfilename(title=self.t('export'),initialfile=Path(self.choice_name).stem+' - copy-v071.zip',defaultextension='.zip',filetypes=[('ZIP','*.zip'),('PNG','*.png')])
   if not dest:return
   ui.base.core.export_copy(self.source,dest,self.choice_name,patched)
   self.status.set(self.t('saved')+': '+dest)
   ui.messagebox.showinfo(self.t('saved'),self.t('savedBody')+'\n\n'+self.st('scope'))
  except Exception as e:ui.messagebox.showerror(self.t('error'),self.error_text(e))

if __name__=='__main__':
 root=tk.Tk()
 if len(sys.argv)==4 and sys.argv[1]=='--self-test':
  root.withdraw();app=App(root)
  with zipfile.ZipFile(sys.argv[2])as z:
   name='antes.png' if 'antes.png' in z.namelist() else next(n for n in z.namelist() if n.endswith('.png'))
   data=z.read(name)
  app.memories={name:data};app.choice.configure(values=[name]);app.choice.current(0);app.select()
  notes=[0,1,2,4,0,3,1,2]
  for w,n in zip(app.notevars,notes):w.current(n+1)
  app.scare_active.set(True);app.select_songs()
  e,money,nuts=app.collect();result,changes=edit(name,data,money,nuts,e)
  for lang in range(3):app.extra=e;app.language=lang;app.build();root.update_idletasks();assert app.valid
  Path(sys.argv[3]).write_text(json.dumps(dict(version='0.7.1',languages=3,changes=len(changes),checksum=ui.base.core.inspector.inspect(name,result)['active_save_checksum'])),encoding='utf8')
  root.destroy()
 else:App(root);root.mainloop()
