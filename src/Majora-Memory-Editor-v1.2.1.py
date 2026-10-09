"""Majora 0.9: experimental Memory progress suite based on documented international Save fields."""
from pathlib import Path
import importlib.util,sys,json,zipfile,zlib
ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
s=importlib.util.spec_from_file_location('studio0810',ROOT/'Majora-Memory-Editor-v0.8.10.py');old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
tk=old.tk;ttk=old.ttk;ui=old.ui;decode=old.decode
CONFIG=json.loads((ROOT/'Majora-progress-v1-config.json').read_text());FIELDS={f['key']:f for f in CONFIG['fields']}
CATALOG=json.loads((ROOT/'Majora-collections-catalog.json').read_text())
previous=old.edit

def edit(name,data,money,nuts,extra=None):
 extra=dict(extra or {});patches=extra.pop('progress',{});code=extra.pop('bomberCode',None);lottery=extra.pop('lotteryCodes',None)
 try:result,changes=previous(name,data,money,nuts,extra)
 except ValueError as e:
  if str(e)!='No hay cambios que guardar.':raise
  result,changes=data,[]
 if not patches and code is None and lottery is None:
  if not changes:raise ValueError('No hay cambios que guardar.')
  return result,changes
 report=ui.base.core.inspector.inspect(name,result);p=report['detected_profile']
 if (p['cartridge'],p['revision']) not in [('NZSE',0),('NZSP',1)]:raise ValueError('progressProfile')
 b=int(report['rdram_png_offset'],16)+int(report['save_ram_offset'],16);out=bytearray(result);allowed=set()
 def put(label,off,raw):
  at=b+off;before=bytes(out[at:at+len(raw)])
  if before!=raw:out[at:at+len(raw)]=raw;allowed.update(range(at,at+len(raw)));changes.append(dict(campo=label,offset_png=hex(at),antes=before.hex(),despues=raw.hex()))
 for key,value in patches.items():
  if key not in FIELDS or FIELDS[key]['group']=='Lectura':raise ValueError('Unknown progress field')
  f=FIELDS[key]
  if type(value)!=int or not f['minimum']<=value<=f['maximum']:raise ValueError('progressRange')
  if f['mask'] is not None:
   v=int.from_bytes(out[b+f['offset']:b+f['offset']+f['size']],'big');value=(v|f['mask']) if value else (v&~f['mask'])
  put('progress:'+key,f['offset'],value.to_bytes(f['size'],'big',signed=f['signed']))
 if code is not None:
  if type(code)!=str or len(code)!=5 or set(code)!=set('12345'):raise ValueError('bomberRange')
  put('Bomber code',0xffb,bytes(int(c) for c in code))
 if lottery is not None:
  if type(lottery)!=str or len(lottery)!=9 or any(c not in '0123456789' for c in lottery):raise ValueError('lotteryRange')
  put('Lottery codes',0xfec,bytes(int(c) for c in lottery))
 if out!=result:
  block=bytearray(out[b:b+0x100c]);block[0x100a:0x100c]=bytes(2);put('Save checksum',0x100a,(sum(block)&65535).to_bytes(2,'big'))
  pos=8
  while pos+12<=len(out):
   n=int.from_bytes(out[pos:pos+4],'big')
   if out[pos+4:pos+8]==b'apmd':at=pos+8+n;out[at:at+4]=(zlib.crc32(out[pos+4:at])&0xffffffff).to_bytes(4,'big');allowed.update(range(at,at+4));break
   pos+=n+12
  else:raise ValueError('Missing apmd')
  assert len(out)==len(result) and all(i in allowed for i,(a,c) in enumerate(zip(result,out)) if a!=c);result=bytes(out);ui.base.core.inspector.inspect(name,result)
 if not changes:raise ValueError('No hay cambios que guardar.')
 return result,changes
old.edit=edit;old.old.edit=edit;ui.edit=edit
class App(old.App):
 def pt(self,es,en,fr):return (es,en,fr)[self.language]
 def build(self):
  self.progress_ready=False;super().build();self.root.title('Majora · Memory Studio 1.2.1')
  self.progress_vars={};page=ttk.Frame(self.book,padding=12);self.book.add(page,text=self.pt('Progreso','Progress','Progrès'))
  ttk.Label(page,text=self.pt('Nuevas ediciones experimentales · confirmado en decomp; prueba física pendiente.','New experimental edits · confirmed in decomp; physical testing pending.','Nouvelles modifications expérimentales · confirmées dans la decomp ; tests physiques en attente.'),wraplength=950,foreground='#c3a66a').pack(anchor='w',pady=6)
  self.subbook=ttk.Notebook(page);self.subbook.pack(fill='both',expand=True)
  groups=[('Templos','Temples','Temples'),('Búhos','Owls','Statues'),('Notebook','Notebook','Journal'),('Recompensas','Rewards','Récompenses'),('Estadísticas','Statistics','Statistiques'),('Regiones','Regions','Régions')]
  self.group_pages={}
  for group,en,fr in groups:
   frame=ttk.Frame(self.subbook,padding=8);self.subbook.add(frame,text=self.pt(group,en,fr));self.group_pages[group]=frame
   canvas=tk.Canvas(frame,background='#10151d',highlightthickness=0);scroll=ttk.Scrollbar(frame,orient='vertical',command=canvas.yview);canvas.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');canvas.pack(fill='both',expand=True);content=ttk.Frame(canvas);canvas.create_window((0,0),window=content,anchor='nw');content.bind('<Configure>',lambda event,c=canvas:c.configure(scrollregion=c.bbox('all')))
   if group=='Notebook':ttk.Label(content,text=self.pt('Las marcas del diario no completan las misiones ni entregan sus recompensas.','Notebook marks do not complete quests or grant rewards.','Les marques du journal ne terminent pas les quêtes et ne donnent pas les récompenses.'),wraplength=850).pack(anchor='w',pady=6)
   if group=='Templos':ttk.Label(content,text=self.pt('Restos permanentes ≠ jefe vencido en este ciclo. Las llaves pequeñas y el progreso temporal se reinician con la Canción del Tiempo.','Permanent remains ≠ boss defeated this cycle. Small keys and temporary progress reset with Song of Time.','Vestiges permanents ≠ boss vaincu dans ce cycle. Petites clés et progrès temporaires sont réinitialisés par le Chant du Temps.'),wraplength=850).pack(anchor='w',pady=6)
   for f in CONFIG['fields']:
    if f['group']!=group:continue
    row=ttk.Frame(content);row.pack(anchor='w',fill='x',pady=3)
    ttk.Label(row,text=f['label'],width=56).pack(side='left')
    var=tk.StringVar();self.progress_vars[f['key']]=var;self.vars['progress_'+f['key']]=var
    if f['mask'] is not None:box=ttk.Combobox(row,textvariable=var,values=['0','1'],state='readonly',width=8)
    else:box=ttk.Spinbox(row,textvariable=var,from_=f['minimum'],to=f['maximum'],width=8)
    box.pack(side='left',padx=8)
  stats=self.group_pages['Estadísticas']
  self.code_var=tk.StringVar();self.lottery_var=tk.StringVar();self.vars['bomberCode']=self.code_var;self.vars['lotteryCodes']=self.lottery_var
  row=ttk.Frame(stats);row.pack(anchor='w',pady=6);ttk.Label(row,text=self.pt('Código Bomber (1–5 sin repetir)','Bomber code (1–5, no repeats)','Code des Bombers (1–5 sans répétition)'),width=42).pack(side='left');ttk.Entry(row,textvariable=self.code_var,width=16).pack(side='left')
  row=ttk.Frame(stats);row.pack(anchor='w',pady=6);ttk.Label(row,text=self.pt('Lotería: 3 números por día (9 dígitos)','Lottery: 3 numbers per day (9 digits)','Loterie : 3 nombres par jour (9 chiffres)'),width=42).pack(side='left');ttk.Entry(row,textvariable=self.lottery_var,width=16).pack(side='left')
  frame=ttk.Frame(self.subbook,padding=8);self.subbook.add(frame,text=self.pt('Colecciones','Collections','Collections'));self.collection_list=ttk.Treeview(frame,columns=('place','state'),show='headings',height=10);self.collection_list.heading('place',text=self.pt('Pieza / contenedor','Piece / container','Fragment / réceptacle'));self.collection_list.heading('state',text=self.pt('Recogido','Collected','Collecté'));self.collection_list.column('place',width=650);self.collection_list.column('state',width=90);scroll=ttk.Scrollbar(frame,orient='vertical',command=self.collection_list.yview);self.collection_list.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');self.collection_list.pack(fill='both',expand=True)
  frame=ttk.Frame(self.subbook,padding=8);self.subbook.add(frame,text=self.pt('Foto y estado','Photo and status','Photo et état'));self.state_read=tk.StringVar();ttk.Label(frame,textvariable=self.state_read,wraplength=900).pack(anchor='w');ttk.Button(frame,text=self.pt('Exportar foto PGM…','Export photo PGM…','Exporter la photo PGM…'),command=self.export_photo).pack(anchor='w',pady=10)
  ttk.Label(frame,text=self.pt('Foto: exportación I5; importación disponible en Avanzado. La recarga de personaje es experimental.','Photo: I5 export. Import and experimental character/clock editing are available in Advanced.','Photo : export I5. Import et changements expérimentaux de personnage/heure disponibles dans Avancé.'),wraplength=900,foreground='#c3a66a').pack(anchor='w',pady=10)
  self.progress_ready=True;self.populate();self.update_preview()
 def populate(self):
  super().populate()
  if not getattr(self,'progress_ready',False):return
  if not self.data:
   for var in self.progress_vars.values():var.set('')
   self.state_read.set('—');return
  patches=self.extra.get('progress',{})
  for key,var in self.progress_vars.items():
   f=FIELDS[key];v=self.value(f['offset'],f['size'])
   if f['signed'] and v>=128:v-=256
   if f['mask'] is not None:v=int(bool(v&f['mask']))
   var.set(str(patches.get(key,v)))
  b=int(self.report['rdram_png_offset'],16)+int(self.report['save_ram_offset'],16)
  self.code_var.set(self.extra.get('bomberCode',''.join(str(v) for v in self.data[b+0xffb:b+0x1000])))
  self.lottery_var.set(self.extra.get('lotteryCodes',''.join(str(v) for v in self.data[b+0xfec:b+0xff5])))
  self.collection_list.delete(*self.collection_list.get_children())
  for f in CATALOG['hearts']:self.collection_list.insert('','end',values=(f['name'],int(bool(self.data[b+f['offset']]&(1<<f['bit'])))))
  for scene in CATALOG['bosses']:
   off=0xf8+scene*28+16;self.collection_list.insert('','end',values=('Boss heart · scene '+str(scene),int(bool(self.value(off,4)&0x80000000))))
  counts=[self.value(0xd4+i) for i in range(4)]
  self.state_read.set(self.pt('Hadas por templo: ','Fairies per temple: ','Fées par temple : ')+str(counts)+'\nSwamp/Ocean Skulltulas: '+str(self.value(0xec0,2))+' / '+str(self.value(0xec2,2))+'\n'+self.pt('Orden máscaras Oceanside: ','Oceanside mask order: ','Ordre masques Océan : ')+str(list(self.data[b+0xff5:b+0xffb]))+'\n'+self.pt('Estados: decomp confirmada; nuevas escrituras pendientes de prueba física.','Status: decomp confirmed; new writes await physical testing.','État : decomp confirmée ; nouvelles écritures en attente de test physique.'))
 def collect(self):
  extra,money,nuts=super().collect()
  if not getattr(self,'progress_ready',False) or not self.data:return extra,money,nuts
  patches={}
  for key,var in self.progress_vars.items():
   f=FIELDS[key]
   try:v=int(var.get())
   except ValueError:raise ValueError('progressRange')
   current=self.value(f['offset'],f['size'])
   if f['signed'] and current>=128:current-=256
   if f['mask'] is not None:current=int(bool(current&f['mask']))
   if v!=current:patches[key]=v
  if patches:extra['progress']=patches
  b=int(self.report['rdram_png_offset'],16)+int(self.report['save_ram_offset'],16)
  for key,var,off,n in [('bomberCode',self.code_var,0xffb,5),('lotteryCodes',self.lottery_var,0xfec,9)]:
   raw=''.join(str(v) for v in self.data[b+off:b+off+n])
   if var.get()!=raw:extra[key]=var.get()
  return extra,money,nuts
 def describe(self,c):
  if c['campo'].startswith('progress:'):
   f=FIELDS[c['campo'].split(':',1)[1]];a=int(c['antes'],16);b=int(c['despues'],16)
   if f['mask'] is not None:a=int(bool(a&f['mask']));b=int(bool(b&f['mask']))
   if f['signed']:a=a-256 if a>=128 else a;b=b-256 if b>=128 else b
   return f['label'],str(a),str(b)
  if c['campo'] in ('Bomber code','Lottery codes'):return c['campo'],' '.join(str(v) for v in bytes.fromhex(c['antes'])),' '.join(str(v) for v in bytes.fromhex(c['despues']))
  return super().describe(c)
 def error_text(self,e):
  if str(e)=='progressProfile':return self.pt('Nuevas ediciones limitadas a USA 1.0 / PAL 1.1 investigados.','New edits limited to researched USA 1.0 / PAL 1.1.','Nouvelles modifications limitées aux USA 1.0 / PAL 1.1 étudiés.')
  if str(e) in ('progressRange','bomberRange','lotteryRange'):return self.pt('Revisa rangos, código Bomber (12345 sin repetir) y lotería (9 dígitos).','Check ranges, Bomber code (12345 without repeats) and lottery (9 digits).','Vérifiez les limites, le code Bombers (12345 sans répétition) et la loterie (9 chiffres).')
  return super().error_text(e)
 def export_photo(self):
  if not self.data:return
  try:
   p=self.report['detected_profile']
   if (p['cartridge'],p['revision']) not in [('NZSE',0),('NZSP',1)]:raise ValueError('progressProfile')
   b=int(self.report['rdram_png_offset'],16)+int(self.report['save_ram_offset'],16);raw=self.data[b+0x10e0:b+0x10e0+11200];pixels=bytearray()
   for i in range(0,len(raw),5):
    v=int.from_bytes(raw[i:i+5],'big')
    for shift in range(35,-1,-5):pixels.append(((v>>shift)&31)*255//31)
   assert len(pixels)==160*112
   path=ui.filedialog.asksaveasfilename(initialfile='Majora-photo.pgm',defaultextension='.pgm',filetypes=[('PGM','*.pgm')])
   if path:
    with Path(path).open('xb') as f:f.write(b'P5\n160 112\n255\n'+pixels)
  except Exception as e:ui.messagebox.showerror(self.t('error'),self.error_text(e))
# The extra writer is deliberately separate from the existing proven operations.
s=importlib.util.spec_from_file_location('advanced',ROOT/'Majora-Advanced.py');advanced=importlib.util.module_from_spec(s);s.loader.exec_module(advanced)
s=importlib.util.spec_from_file_location('german',ROOT/'Majora-German.py');german=importlib.util.module_from_spec(s);s.loader.exec_module(german)
base_edit=edit

def edit(name,data,money,nuts,extra=None):
 extra=dict(extra or {});options=extra.pop('advanced',{})
 if extra.get('cycleReset') and any(k in options for k in ('clock','sword','shield','form')):raise ValueError('Do not combine native cycle reset with character/clock reload')
 try:result,changes=base_edit(name,data,money,nuts,extra)
 except ValueError as e:
  if str(e)!='No hay cambios que guardar.':raise
  result,changes=data,[]
 if options:
  report=ui.base.core.inspector.inspect(name,result);result,added=advanced.apply(result,report,options,CATALOG);changes+=added;ui.base.core.inspector.inspect(name,result)
 if not changes:raise ValueError('No hay cambios que guardar.')
 return result,changes
old.edit=edit;old.old.edit=edit;ui.edit=edit
BaseApp=App
class App(BaseApp):
 def __init__(self,root):self.german=False;super().__init__(root)
 def tr(self,text):return german.translate(text) if self.german else text
 def t(self,key,**values):
  if self.german:return german.translate(ui.words.TEXT[key][1]).format(**values)
  return super().t(key,**values)
 def pt(self,es,en,fr):return self.tr((es,en,fr)[self.language])
 def et(self,es,en,fr):return self.tr((es,en,fr)[self.language])
 def build(self):
  self.advanced_ready=False;super().build();self.root.title('Majora · Memory Studio 1.2.1')
  # Remove superseded read-only equipment warning and update photo help.
  for tabid in self.book.tabs():
   frame=self.root.nametowidget(tabid)
   for w in frame.winfo_children():
    try:
     if str(w.cget('text')).startswith(('Sword and shield are displayed read-only.','Espada y escudo se muestran en lectura.','Épée et bouclier affichés en lecture seule.')):w.destroy()
    except (tk.TclError,KeyError):pass
  page=ttk.Frame(self.book,padding=12);self.book.add(page,text=self.pt('Avanzado / Experimental','Advanced / Experimental','Avancé / Expérimental'))
  ttk.Label(page,text=self.pt('Cambiar personaje/hora recarga el acceso actual. Captura sin pausa ni diálogo. Cambiar la hora no ejecuta Canción del Tiempo ni reinicia misiones. Experimental.','Character/clock edits reload the current entrance. Close pause and dialogs before capturing. Clock editing does not perform Song of Time or reset quests. Experimental.','Les changements de personnage/heure rechargent l’entrée actuelle. Capture sans pause ni dialogue. Changer l’heure ne lance pas le Chant du Temps et ne réinitialise pas les quêtes. Expérimental.'),wraplength=920,foreground='#c3a66a').pack(anchor='w',pady=6)
  row=ttk.Frame(page);row.pack(anchor='w');self.char_boxes={}
  for column,(key,label,choices) in enumerate([('sword',('Espada','Sword','Épée'),['Keep','Kokiri','Razor','Gilded']),('shield',('Escudo','Shield','Bouclier'),['Keep','None','Hero','Mirror']),('form',('Forma','Form','Forme'),['Keep','Goron','Zora','Deku','Human'])]):
   ttk.Label(row,text=self.pt(*label)).grid(row=0,column=column,padx=10);box=ttk.Combobox(row,values=[self.tr(x) for x in choices],state='readonly',width=18);box.current(0);box.grid(row=1,column=column,padx=10);box.bind('<<ComboboxSelected>>',lambda e:self.update_preview());self.char_boxes[key]=box
  row=ttk.Frame(page);row.pack(anchor='w',pady=12);self.clock_vars={}
  for col,(key,label,maxv) in enumerate([('day',('Día','Day','Jour'),3),('hour',('Hora','Hour','Heure'),23),('minute',('Minuto','Minute','Minute'),59)]):
   ttk.Label(row,text=self.pt(*label)).grid(row=0,column=col,padx=10);v=tk.StringVar();self.clock_vars[key]=v;self.vars['clock_'+key]=v;ttk.Spinbox(row,textvariable=v,from_=1 if key=='day' else 0,to=maxv,width=8).grid(row=1,column=col,padx=10)
  self.clock_on=tk.IntVar();ttk.Checkbutton(row,text=self.pt('Aplicar edición de hora','Apply clock edit','Appliquer l’heure'),variable=self.clock_on,command=self.update_preview).grid(row=1,column=3,padx=10)
  self.spider_var=tk.StringVar();self.vars['spiderOrder']=self.spider_var;ttk.Label(page,text=self.pt('Orden Oceanside: 6 colores (0–3, adyacentes distintos)','Oceanside order: 6 colors (0–3, adjacent colors differ)','Ordre Océan : 6 couleurs (0–3, voisines différentes)')).pack(anchor='w');ttk.Entry(page,textvariable=self.spider_var,width=18).pack(anchor='w',pady=4)
  self.photo_info=tk.StringVar();ttk.Label(page,textvariable=self.photo_info).pack(anchor='w');ttk.Button(page,text=self.pt('Importar foto PNG/PGM…','Import photo PNG/PGM…','Importer une photo PNG/PGM…'),command=self.import_photo).pack(anchor='w',pady=4);ttk.Button(page,text=self.pt('Quitar foto importada','Remove imported photo','Retirer la photo importée'),command=self.remove_photo).pack(anchor='w',pady=4)
  ttk.Label(page,text=self.pt('Importar píxeles no certifica el sujeto fotografiado. Se borran los flags de validación del sujeto.','Imported pixels do not prove the photographed subject. Subject validation flags are cleared.','Importer des pixels ne valide pas le sujet photographié. Les flags de validation du sujet sont effacés.'),wraplength=920).pack(anchor='w',pady=6)
  frame=ttk.Frame(self.subbook,padding=8);self.subbook.add(frame,text=self.pt('Coleccionables individuales','Individual collectibles','Collections individuelles'))
  ttk.Label(frame,text=self.pt('Recogido: doble clic para alternar','Collected: double-click to toggle','Collecté : double-clic pour modifier')).pack(anchor='w')
  ttk.Label(frame,text=self.pt('Los flags de corazones recalculan la capacidad según catálogo (3 iniciales + piezas + contenedores). Los contadores de hadas y Skulltulas siguen sus flags.','Individual heart flags recalculate capacity from the catalog (3 initial hearts + pieces + boss containers). Fairy and Skulltula counters follow their flags.','Les flags de cœurs recalculent la capacité selon le catalogue (3 initiaux + fragments + réceptacles). Les compteurs de fées et Skulltulas suivent leurs flags.'),wraplength=900).pack(anchor='w')
  self.individual=ttk.Treeview(frame,columns=('name','state'),show='headings',height=10);self.individual.heading('name',text=self.t('field'));self.individual.heading('state',text=self.pt('Recogido','Collected','Collecté'));self.individual.column('name',width=690);self.individual.column('state',width=100);scroll=ttk.Scrollbar(frame,orient='vertical',command=self.individual.yview);self.individual.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');self.individual.pack(fill='both',expand=True);self.individual.bind('<Double-1>',self.toggle_collection)
  self.advanced_ready=True;self.populate();self.lang.configure(values=['Español','English','Français','Deutsch']);self.lang.current(3 if self.german else self.language);self.translate_widgets();self.update_preview()
 def translate_widgets(self):
  if not self.german:return
  def visit(w):
   if isinstance(w,ttk.Notebook):
    for tabid in w.tabs():w.tab(tabid,text=self.tr(w.tab(tabid,'text')))
   try:
    if 'text' in w.keys() and w.cget('text'):w.configure(text=self.tr(w.cget('text')))
    if isinstance(w,ttk.Combobox) and w is not self.lang:
     index=w.current();w.configure(values=[self.tr(x) for x in w.cget('values')]);
     if index>=0:w.current(index)
    if isinstance(w,ttk.Treeview):
     for col in w['columns']:w.heading(col,text=self.tr(w.heading(col,'text')))
     for item in w.get_children():w.item(item,values=[self.tr(x) for x in w.item(item,'values')])
   except tk.TclError:pass
   for child in w.winfo_children():visit(child)
  visit(self.root)
 def change_language(self,event=None):
  chosen=self.lang.current()
  if self.data:
   try:self.extra=self.collect()[0]
   except ValueError as e:ui.messagebox.showerror(self.t('error'),self.error_text(e));self.lang.current(3 if self.german else self.language);return
  self.german=chosen==3;self.language=1 if self.german else chosen;self.build()
 def populate(self):
  super().populate()
  if not getattr(self,'advanced_ready',False):return
  opts=self.extra.get('advanced',{});self.photo_hex=opts.get('photo');self.photo_info.set(self.tr('Photo imported' if self.photo_hex else 'No photo imported'));self.collection_patches=dict(opts.get('collections',{}));self.individual.delete(*self.individual.get_children())
  if not self.data:return
  for key,box in self.char_boxes.items():
   v=opts.get(key);box.current(0 if v is None else v+1 if key=='shield' else v)
  self.spider_original=''.join(str(self.value(0xff5+i)) for i in range(6));self.spider_var.set(opts.get('spiderOrder',self.spider_original))
  t=self.value(0xc,2)*1440//65536;clock=opts.get('clock',[self.value(0x18,4),t//60,t%60]);self.clock_on.set(int('clock' in opts))
  for key,v in zip(['day','hour','minute'],clock):self.clock_vars[key].set(str(v))
  self.collection_original={}
  def add(key,label,on):self.collection_original[key]=int(on);self.individual.insert('','end',iid=key,values=(self.tr(label),self.collection_patches.get(key,int(on))))
  for i,h in enumerate(CATALOG['hearts']):add('heart:'+str(i),h['name'],bool(self.value(h['offset'])&(1<<h['bit'])))
  for i,scene in enumerate(CATALOG['bosses']):add('boss:'+str(i),'Boss container · '+str(i+1),bool(self.value(0xf8+scene*28+16,4)&0x80000000))
  for i,f in enumerate(CATALOG['fairies']):add('fairy:'+str(i),'Fairy · '+str(f['group']+1)+' / '+str(i+1),bool(self.value(0xf8+f['scene']*28+advanced.loc.PERM[f['field']],4)&(1<<f['flag'])))
  for entry in CATALOG['skulls']:
   for i in range(30):add('skull:'+str(entry['group']*30+i),'Skulltula · '+('Swamp' if entry['group']==0 else 'Ocean')+' / '+str(i+1),bool(self.value(0xf8+entry['scene']*28,4)&(1<<i)))
  self.translate_widgets()
 def collect(self):
  extra,money,nuts=super().collect()
  if not getattr(self,'advanced_ready',False) or not self.data:return extra,money,nuts
  opts={}
  for key,box in self.char_boxes.items():
   i=box.current()
   if i>0:opts[key]=i-1 if key=='shield' else i
  if self.clock_on.get():opts['clock']=[int(self.clock_vars[k].get()) for k in ['day','hour','minute']]
  if self.collection_patches:opts['collections']=dict(self.collection_patches)
  if self.photo_hex:opts['photo']=self.photo_hex
  if self.spider_var.get()!=self.spider_original:opts['spiderOrder']=self.spider_var.get()
  if opts:extra['advanced']=opts
  return extra,money,nuts
 def toggle_collection(self,event):
  key=self.individual.identify_row(event.y)
  if not key:return
  v=1-int(self.individual.item(key,'values')[1])
  if v==self.collection_original[key]:self.collection_patches.pop(key,None)
  else:self.collection_patches[key]=v
  values=self.individual.item(key,'values');self.individual.item(key,values=(values[0],v));self.update_preview()
 def import_photo(self):
  path=ui.filedialog.askopenfilename(filetypes=[('PNG / PGM','*.png *.pgm')])
  if not path:return
  try:
   img=tk.PhotoImage(file=path)
   if (img.width(),img.height())!=(160,112):raise ValueError('Photo size must be 160 × 112')
   pixels=[]
   for y in range(112):
    for x in range(160):
     color=img.get(x,y)
     if isinstance(color,str):color=tuple(map(int,color.split()))
     pixels.append((int(color[0])*299+int(color[1])*587+int(color[2])*114)*31//255000)
   raw=bytearray()
   for i in range(0,len(pixels),8):
    v=0
    for n in pixels[i:i+8]:v=(v<<5)|n
    raw.extend(v.to_bytes(5,'big'))
   self.photo_hex=raw.hex();self.photo_info.set(self.tr('Photo imported'));self.update_preview()
  except Exception as e:ui.messagebox.showerror(self.t('error'),self.error_text(e))
 def remove_photo(self):self.photo_hex=None;self.photo_info.set(self.tr('No photo imported'));self.update_preview()
 def error_text(self,e):return self.tr(super().error_text(e))

jp_spec=importlib.util.spec_from_file_location('japan',ROOT/'Majora-Japan.py');japan=importlib.util.module_from_spec(jp_spec);jp_spec.loader.exec_module(japan)
pal_spec=importlib.util.spec_from_file_location('pal10',ROOT/'Majora-PAL10.py');pal10=importlib.util.module_from_spec(pal_spec);pal_spec.loader.exec_module(pal10)
InternationalApp=App
class App(InternationalApp):
 def select(self):
  name=self.choice.get();data=self.memories.get(name)
  if data:
   try:report=ui.base.core.inspector.inspect(name,data)
   except Exception:return super().select()
   if report['detected_profile']['layout']=='jp-1.1' or (report['detected_profile']['cartridge'],report['detected_profile']['revision'])==('NZSP',0):
    self.data=None;self.extra={};self.savebutton.configure(state='disabled');self.filelabel.configure(text=str(self.source or name)+'\n'+report['detected_profile']['cartridge']+' · 1.'+str(report['detected_profile']['revision']));self.status.set('Regional editor · '+report['detected_profile']['cartridge']);self.regional_panel=(japan if report['detected_profile']['layout']=='jp-1.1' else pal10).Panel(self,name,data);self.japan_panel=self.regional_panel;return
  return super().select()

if __name__=='__main__':
 root=tk.Tk()
 if len(sys.argv)==4 and sys.argv[1] in ('--japan-self-test','--pal10-self-test'):
  root.withdraw();app=App(root);app.source=Path(sys.argv[2]);import hashlib
  app.source_hash=hashlib.sha256(app.source.read_bytes()).hexdigest()
  with zipfile.ZipFile(sys.argv[2]) as z:name=next(n for n in z.namelist() if n.endswith('.png'));data=z.read(name)
  app.memories={name:data};app.choice.configure(values=[name]);app.choice.current(0);app.select();panel=app.japan_panel;panel.maximum();money,nuts,extra=panel.collect();backend=japan if sys.argv[1]=='--japan-self-test' else pal10;result,changes=backend.edit(name,data,money,nuts,extra)
  assert len(panel.items)==48 and len(panel.individual.get_children())==176;backend.inspect(name,result)
  Path(sys.argv[3]).write_text(json.dumps({'version':'1.2.1-experimental','regional_packaged_UI':'PASS','mode':sys.argv[1],'changes':len(changes)}),encoding='utf8');root.destroy()
 elif len(sys.argv)==4 and sys.argv[1] in ('--self-test','--pal-reset-self-test'):
  root.withdraw();app=App(root)
  with zipfile.ZipFile(sys.argv[2]) as z:name=next(n for n in z.namelist() if n.endswith('.png'));data=z.read(name)
  app.memories={name:data};app.choice.configure(values=[name]);app.choice.current(0);app.select()
  if sys.argv[1]=='--pal-reset-self-test':
   assert str(app.resetbutton.cget('state'))=='normal';app.resetvar.set(True);app.choose_reset()
  else:app.progress_vars['owl_0'].set(str(1-int(app.progress_vars['owl_0'].get())));app.update_preview()
  assert app.valid
  for lang in range(4):
   app.lang.current(lang);app.change_language();root.update_idletasks();assert app.valid
  assert app.lang.get()=='Deutsch';assert app.t('open')=='Memory öffnen…'
  Path(sys.argv[3]).write_text(json.dumps({'version':'1.2.1-experimental','languages':4,'progress_fields':len(FIELDS),'individual_fields':len(app.individual.get_children()),'ui':'PASS'}));root.destroy()
 else:App(root);root.mainloop()
