"""Majora 0.6: tabbed desktop interface, ES/EN/FR, unchanged 0.3.1 writer."""
from pathlib import Path
import sys,importlib.util,zipfile,hashlib,json
ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
def module(name,file):
 spec=importlib.util.spec_from_file_location(name,ROOT/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=module('writer','Majora-regional-writer.py')
words=module('words','Majora-ui-languages.py')
tk=base.tk;ttk=base.ttk;messagebox=base.messagebox;filedialog=base.filedialog
collections=module('collections_writer','Majora-regional-collections.py')
def edit(name,data,money,nuts,extra=None):
 extra=dict(extra or {});groups={key.removeprefix('complete_') for key in list(extra) if key.startswith('complete_') and extra[key]}
 for key in list(extra):
  if key.startswith('complete_'):extra.pop(key)
 report=base.core.inspector.inspect(name,data);b=int(report['rdram_png_offset'],16)+int(report['save_ram_offset'],16)
 if extra.get('healthCapacity',int.from_bytes(data[b+0x34:b+0x36],'big'))==320:groups.add('hearts')
 try:result,changes=base.edit(name,data,money,nuts,extra)
 except ValueError as e:
  if str(e)!='No hay cambios que guardar.':raise
  result=data;changes=[]
 if groups:
  result,flags,context=collections.apply(result,report,groups);changes+=flags
  base.core.inspector.inspect(name,result)
 if not changes:raise ValueError('No hay cambios que guardar.')
 return result,changes
def maximum_preset(data,report):
 money,nuts,e=base.maximum_preset(data,report)
 e.update({'complete_'+key:True for key in ['skull0','skull1','fairy0','fairy1','fairy2','fairy3']})
 return money,nuts,e
AMMO_KEYS={1:'arrows',6:'bombs',7:'bombchus',8:'sticks',9:'nuts',10:'beans'}
UPGRADES=[('quiver',0,7,[0,30,40,50]),('bag',3,7,[0,20,30,40]),('wallet',12,3,[99,200,500]),('sticksCapacity',17,7,[0,10,20,30]),('nutsCapacity',20,7,[0,20,30,40])]
class App:
 def __init__(self,root):
  self.root=root;self.language=0;self.data=None;self.extra={};self.memories={};self.source=None
  self.loading=False;self.signature=None;self.choice_name='';self.preview=[];self.valid=False
  self.theme(root);root.title('Majora · Memory Studio 0.6');root.geometry('1100x850');root.minsize(1020,760)
  self.build();self.root.after(300,self.tick)
 def theme(self,root):
  root.configure(background='#10151d')
  root.option_add('*Font','{Segoe UI} 10')
  root.option_add('*TCombobox*Listbox.background','#202b38')
  root.option_add('*TCombobox*Listbox.foreground','#e8edf4')
  style=ttk.Style(root);style.theme_use('clam')
  style.configure('.',background='#10151d',foreground='#e8edf4',font=('Segoe UI',10))
  style.configure('TFrame',background='#10151d')
  style.configure('TLabel',background='#10151d',foreground='#bac6d4')
  style.configure('TButton',background='#273443',foreground='#e8edf4',borderwidth=0,padding=(16,10))
  style.map('TButton',background=[('active','#384c61'),('disabled','#1a2330')],foreground=[('disabled','#657486')])
  style.configure('Accent.TButton',background='#38cfa0',foreground='#08261f',font=('Segoe UI',10,'bold'))
  style.map('Accent.TButton',background=[('active','#67e2bc'),('disabled','#253c39')])
  style.configure('TLabelframe',background='#10151d',bordercolor='#334355',relief='solid')
  style.configure('TLabelframe.Label',background='#10151d',foreground='#b9a5ff',font=('Segoe UI',10,'bold'))
  style.configure('TEntry',fieldbackground='#202b38',foreground='#ffffff',insertcolor='#ffffff')
  for name in ['TSpinbox','TCombobox']:
   style.configure(name,fieldbackground='#202b38',background='#273443',foreground='#ffffff',arrowcolor='#38cfa0',padding=7)
   style.map(name,fieldbackground=[('readonly','#202b38')],foreground=[('readonly','#ffffff')])
  style.configure('Treeview',background='#18212d',fieldbackground='#18212d',foreground='#d6e0ec',rowheight=29,borderwidth=0)
  style.configure('Treeview.Heading',background='#263446',foreground='#b9a5ff',font=('Segoe UI',10,'bold'),padding=8)
  style.map('Treeview',background=[('selected','#3b3263')],foreground=[('selected','#ffffff')])
  style.configure('TNotebook',background='#10151d',borderwidth=0)
  style.configure('TNotebook.Tab',background='#202b38',foreground='#bac6d4',padding=(18,9))
  style.map('TNotebook.Tab',background=[('selected','#3b3263')],foreground=[('selected','#ffffff')])
 def t(self,key,**values):return words.TEXT[key][self.language].format(**values)
 def itemname(self,value,slot=None):
  if value==255:return self.t('empty')
  if slot is not None and slot>=24 and value==base.MASK_IDS[slot-24]:return words.MASKS[slot-24][self.language]
  if value in words.SPECIAL:return words.SPECIAL[value][self.language]
  if 0x12<=value<=0x27:return words.CONTENTS[value-0x12][self.language]
  if 0<=value<18:return words.NORMAL[value][self.language]
  if value in base.MASK_IDS:return words.MASKS[base.MASK_IDS.index(value)][self.language]
  return self.t('unknown')+f' ({value})'
 def error_text(self,error):
  text=str(error)
  if text in words.TEXT:return self.t(text)
  if self.language:
   for key,value in sorted(words.ERRORS.items(),key=lambda x:-len(x[0])):text=text.replace(key,value[self.language-1])
   for i,key in AMMO_KEYS.items():text=text.replace(base.AMMO[i][0],self.t(key))
  return text
 def label(self,parent,text,**opts):return ttk.Label(parent,text=text,**opts)
 def page(self,key,helpkey):
  page=ttk.Frame(self.book,padding=16);self.book.add(page,text=self.t(key))
  self.label(page,self.t(helpkey),wraplength=970).pack(anchor='w',pady=(0,14))
  return page
 def build(self):
  if hasattr(self,'frame'):self.frame.destroy()
  self.loading=True
  self.frame=ttk.Frame(self.root,padding=22);self.frame.pack(fill='both',expand=True)
  top=ttk.Frame(self.frame);top.pack(fill='x')
  emblem=tk.Canvas(top,width=64,height=58,background='#10151d',highlightthickness=0);emblem.pack(side='left',padx=(0,14))
  emblem.create_polygon(10,17,4,2,22,13,32,6,43,13,60,2,54,17,60,32,47,44,32,55,17,44,4,32,fill='#6f46a6',outline='#b9a5ff',width=2)
  emblem.create_polygon(12,23,28,28,25,38,14,33,fill='#e4bf62');emblem.create_polygon(52,23,36,28,39,38,50,33,fill='#e4bf62')
  emblem.create_oval(18,25,23,35,fill='#ed6c55',outline='');emblem.create_oval(41,25,46,35,fill='#ed6c55',outline='')
  emblem.create_line(32,19,32,47,fill='#38cfa0',width=2)
  self.label(top,'MAJORA  /  MEMORY STUDIO',font=('Segoe UI',24,'bold'),foreground='#f1edff').pack(side='left')
  self.lang=ttk.Combobox(top,values=words.LANGUAGES,state='readonly',width=12);self.lang.current(self.language);self.lang.pack(side='right');self.lang.bind('<<ComboboxSelected>>',self.change_language)
  self.label(self.frame,self.t('subtitle'),foreground='#c3a66a').pack(anchor='w',pady=(4,12))
  bar=ttk.Frame(self.frame);bar.pack(fill='x')
  ttk.Button(bar,text=self.t('open'),command=self.open).pack(side='left')
  self.filelabel=self.label(bar,str(self.source) if self.source else self.t('none'),wraplength=820);self.filelabel.pack(side='left',padx=16)
  self.choice=ttk.Combobox(self.frame,state='readonly',values=list(self.memories));self.choice.pack(fill='x',pady=12)
  if self.choice_name:self.choice.set(self.choice_name)
  self.choice.bind('<<ComboboxSelected>>',lambda e:self.select())
  self.book=ttk.Notebook(self.frame);self.book.pack(fill='both',expand=True)
  self.vars={};self.itemvars={};self.itemchoices={};self.upvars={}
  resource=self.page('resources','resourceHelp');grid=ttk.Frame(resource);grid.pack(anchor='nw')
  row=0
  for key,minimum,maximum,step in [('health',.25,20,.25),('healthCapacity',3,20,1),('rupees',0,500,1),('magicCurrent',0,96,1)]+[(key,0,100,1) for key in AMMO_KEYS.values()]:
   self.label(grid,self.t(key),width=25).grid(row=row,column=0,sticky='w',pady=4)
   var=tk.StringVar();self.vars[key]=var
   ttk.Spinbox(grid,textvariable=var,from_=minimum,to=maximum,increment=step,width=12).grid(row=row,column=1,padx=15)
   row+=1
  self.label(grid,self.t('magic')).grid(row=row,column=0,sticky='w',pady=6)
  self.magic=ttk.Combobox(grid,values=[self.t(k) for k in ['keep','off','normal','double']],state='readonly',width=22);self.magic.grid(row=row,column=1,padx=15);self.magic.current(0)
  improvements=self.page('upgrades','upgradeHelp');grid=ttk.Frame(improvements);grid.pack(anchor='nw')
  for row,(key,shift,mask,caps) in enumerate(UPGRADES):
   self.label(grid,self.t(key),width=25).grid(row=row,column=0,sticky='w',pady=10)
   combo=ttk.Combobox(grid,values=[f'{self.t("level")} {i} · {self.t("capacity")}: {cap}' for i,cap in enumerate(caps)],state='readonly',width=34)
   combo.grid(row=row,column=1,padx=15);self.upvars[key]=combo
  for key,helpkey,indices in [('items','itemHelp',range(24)),('masks','maskHelp',range(24,48))]:
   page=self.page(key,helpkey)
   canvas=tk.Canvas(page,background='#10151d',highlightthickness=0);scroll=ttk.Scrollbar(page,orient='vertical',command=canvas.yview);canvas.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');canvas.pack(fill='both',expand=True)
   content=ttk.Frame(canvas);canvas.create_window((0,0),window=content,anchor='nw');content.bind('<Configure>',lambda event,c=canvas:c.configure(scrollregion=c.bbox('all')))
   for index,i in enumerate(indices):
    group=index//12;row=index%12
    name=words.MASKS[i-24][self.language] if i>=24 else words.NORMAL[i][self.language] if i<18 else self.t('bottle')+f' {i-17}'
    self.label(content,name,width=25,foreground='#c6b7f2' if i>=24 else '#bac6d4').grid(row=row,column=group*2,sticky='w',pady=8,padx=(0,8))
    combo=ttk.Combobox(content,state='readonly',width=24);combo.grid(row=row,column=group*2+1,padx=(0,24),pady=8);self.itemvars[i]=combo
  collection=self.page('collections','collectionHelp');self.collectvars={}
  self.label(collection,self.t('hearts'),foreground='#38cfa0').pack(anchor='w',pady=(2,15))
  for key in ['skull0','skull1','fairy0','fairy1','fairy2','fairy3']:
   v=tk.BooleanVar();self.collectvars[key]=v;ttk.Checkbutton(collection,text=self.t(key),variable=v).pack(anchor='w',pady=8)
  self.label(collection,self.t('collectionNotice'),wraplength=960,foreground='#c3a66a').pack(anchor='w',pady=20)
  review=self.page('review','reviewHelp');self.reviewtree=self.make_tree(review,[('field',self.t('field'),430),('before',self.t('before'),240),('after',self.t('after'),240)])
  tech=self.page('technical','techHelp');self.techtree=self.make_tree(tech,[('field',self.t('field'),430),('ram',self.t('ram'),200),('bytes',self.t('bytes'),250)])
  actions=ttk.Frame(self.frame);actions.pack(fill='x',pady=(14,8))
  ttk.Button(actions,text=self.t('max'),command=self.maximum).pack(side='left')
  ttk.Button(actions,text=self.t('reset'),command=self.reset).pack(side='left',padx=10)
  self.savebutton=ttk.Button(actions,text=self.t('export'),style='Accent.TButton',command=self.save);self.savebutton.pack(side='right')
  self.status=tk.StringVar(value=self.t('ready'));self.label(self.frame,'',textvariable=self.status,wraplength=990).pack(anchor='w')
  self.profilelabel=self.label(self.frame,self.t('notice'),foreground='#c3a66a');self.profilelabel.pack(anchor='w',pady=(5,0))
  self.populate();self.loading=False;self.signature=None;self.update_preview()
 def make_tree(self,parent,columns):
  tree=ttk.Treeview(parent,columns=[c[0] for c in columns],show='headings');scroll=ttk.Scrollbar(parent,orient='vertical',command=tree.yview);tree.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');tree.pack(fill='both',expand=True)
  for key,title,width in columns:tree.heading(key,text=title);tree.column(key,width=width)
  return tree
 def value(self,offset,size=1):
  b=int(self.report['rdram_png_offset'],16)+int(self.report['save_ram_offset'],16);return int.from_bytes(self.data[b+offset:b+offset+size],'big')
 def populate(self):
  if self.data is None:
   for v in self.vars.values():v.set('')
   self.savebutton.configure(state='disabled');return
  e=self.extra
  profile=self.report['detected_profile'];self.filelabel.configure(text=f"{self.source or self.choice_name}\n{profile['cartridge']} · {self.t('region'+profile['cartridge'][3])} · 1.{profile['revision']}");self.profilelabel.configure(text=self.t('profileReal' if profile['validation']=='real-captures' else 'profileStructural')+' · '+self.t('notice'))
  for key,v in self.collectvars.items():v.set(bool(e.get('complete_'+key,False)))
  for key,offset,size,scale in [('health',0x36,2,16),('healthCapacity',0x34,2,16),('rupees',0x3a,2,1),('magicCurrent',0x39,1,1)]:
   self.vars[key].set(str(e.get(key,self.value(offset,size))/scale if scale!=1 else e.get(key,self.value(offset,size))))
  for i,key in AMMO_KEYS.items():self.vars[key].set(str(e.get('ammo_'+str(i),self.value(0xa0+i))))
  self.magic.current(e['magicMode']+1 if 'magicMode' in e else 0)
  upgrades=e.get('upgrades',self.value(0xb8,4))
  for key,shift,mask,caps in UPGRADES:
   level=(upgrades>>shift)&mask
   self.upvars[key].current(level if level<len(caps) else -1)
  for i,combo in self.itemvars.items():
   original=self.value(0x70+i);selected=e.get('item_'+str(i),original);options=list(base.OPTIONS[i])
   if original not in options:options.append(original)
   self.itemchoices[i]=options;combo.configure(values=[self.itemname(v,i) for v in options]);combo.current(options.index(selected))
  self.techtree.delete(*self.techtree.get_children())
  for f in self.report['fields']:self.techtree.insert('','end',values=(f['name'],f['ram_address'],f['bytes']))
  self.savebutton.configure(state='normal')
 def collect(self):
  if self.data is None:return {},0,0
  try:
   extra={};health=float(self.vars['health'].get())*16;capacity=float(self.vars['healthCapacity'].get())*16
   if not health.is_integer() or not capacity.is_integer():raise ValueError(self.t('invalidNumber'))
   for key,off,v in [('health',0x36,int(health)),('healthCapacity',0x34,int(capacity))]:
    if v!=self.value(off,2):extra[key]=v
   mode=self.magic.current()
   current=int(self.vars['magicCurrent'].get())
   if mode>0:extra.update(magicMode=mode-1,magicCurrent=current)
   elif current!=self.value(0x39):extra['magicCurrent']=current
   upgrade=self.value(0xb8,4)
   for key,shift,mask,caps in UPGRADES:
    level=self.upvars[key].current()
    if level>=0:upgrade=(upgrade&~(mask<<shift))|(level<<shift)
   if upgrade!=self.value(0xb8,4):extra['upgrades']=upgrade
   for i,combo in self.itemvars.items():
    selected=combo.current()
    if selected<0:continue
    value=self.itemchoices[i][selected]
    if value!=self.value(0x70+i):extra['item_'+str(i)]=value
   for i,key in AMMO_KEYS.items():
    value=int(self.vars[key].get())
    if value!=self.value(0xa0+i):extra['ammo_'+str(i)]=value
   extra.update({'complete_'+key:True for key,v in self.collectvars.items() if v.get()})
   return extra,int(self.vars['rupees'].get()),int(self.vars['nuts'].get())
  except (ValueError,OverflowError) as e:
   if str(e)==self.t('invalidNumber'):raise
   raise ValueError(self.t('invalidNumber')) from e
 def describe(self,change):
  b=int(self.report['rdram_png_offset'],16)+int(self.report['save_ram_offset'],16);off=int(change['offset_png'],16)-b
  before=int(change['antes'],16);after=int(change['despues'],16)
  if change['campo'] in ['heartFlags','bossHeartFlags','heartRemainder','skull0','skull1','fairy0','fairy1','fairy2','fairy3']:return None
  keys={0x34:'healthCapacity',0x36:'health',0x39:'magicCurrent',0x3a:'rupees'}
  if off in keys:
   if off in (0x34,0x36):before/=16;after/=16
   return self.t(keys[off]),str(before),str(after)
  if 0x70<=off<0xa0:
   i=off-0x70;name=words.MASKS[i-24][self.language] if i>=24 else words.NORMAL[i][self.language] if i<18 else self.t('bottle')+f' {i-17}'
   return name,self.itemname(before,i),self.itemname(after,i)
  if off-0xa0 in AMMO_KEYS:return self.t(AMMO_KEYS[off-0xa0]),str(before),str(after)
  if off==0xb8:return None
  if off in (0x38,0x40,0x41):return None
  return change['campo'],str(before),str(after)
 def upgrade_description(self,number):return ' / '.join(str((number>>shift)&mask) for _,shift,mask,_ in UPGRADES)
 def update_preview(self):
  self.reviewtree.delete(*self.reviewtree.get_children());self.valid=False;self.preview=[]
  if self.data is None:self.status.set(self.t('ready'));return
  try:
   e,money,nuts=self.collect();_,changes=edit(self.choice_name,self.data,money,nuts,e)
   for change in changes:
    b=int(self.report['rdram_png_offset'],16)+int(self.report['save_ram_offset'],16)
    if int(change['offset_png'],16)-b==0xb8:
     old=int(change['antes'],16);new=int(change['despues'],16)
     for key,shift,mask,caps in UPGRADES:
      a=(old>>shift)&mask;c=(new>>shift)&mask
      if a!=c:self.reviewtree.insert('','end',values=(self.t(key),f'{self.t("capacity")}: {caps[a]}' if a<len(caps) else str(a),f'{self.t("capacity")}: {caps[c]}'))
    row=self.describe(change)
    if row:self.reviewtree.insert('','end',values=row)
   if 'magicMode' in e:
    labels=['off','normal','double'];old=0 if not self.value(0x40) else 2 if self.value(0x41) else 1
    self.reviewtree.insert('','end',values=(self.t('magic'),self.t(labels[old]),self.t(labels[e['magicMode']])))
   groups={c['campo'] for c in changes if c['campo'] in ['heartFlags','bossHeartFlags','skull0','skull1','fairy0','fairy1','fairy2','fairy3']}
   counts=collections.progress(self.data,self.report)
   if groups & {'heartFlags','bossHeartFlags'}:self.reviewtree.insert('','end',values=(self.t('hearts'),str(counts['hearts'])+' / 52',self.t('complete')))
   for key in sorted(groups-{'heartFlags','bossHeartFlags'}):self.reviewtree.insert('','end',values=(self.t(key),str(counts[key]),self.t('complete')))
   self.preview=changes;self.valid=True;self.status.set(self.t('pending',n=len(changes)))
  except ValueError as e:
   text=self.t('unchanged') if str(e)=='No hay cambios que guardar.' else self.error_text(e)
   self.status.set(text);self.reviewtree.insert('','end',values=(text,'',''))
 def tick(self):
  if not self.loading:
   sig=(self.language,self.choice_name,tuple(v.get() for v in self.vars.values()),self.magic.current(),tuple(v.current() for v in self.upvars.values()),tuple(v.current() for v in self.itemvars.values()),tuple(v.get() for v in self.collectvars.values()))
   if sig!=self.signature:self.signature=sig;self.update_preview()
  self.root.after(300,self.tick)
 def change_language(self,event=None):
  new=self.lang.current()
  if new==self.language:return
  try:
   e,money,nuts=self.collect()
   if self.data is not None:e.update(rupees=money,ammo_9=nuts)
   self.extra=e
  except ValueError:
   # Preserve unfinished numeric inputs across a language switch too.
   raw={k:v.get() for k,v in self.vars.items()};magic=self.magic.current()
   upgrades={k:v.current() for k,v in self.upvars.items()};items={k:v.current() for k,v in self.itemvars.items()}
   flags={k:v.get() for k,v in self.collectvars.items()}
   self.language=new;self.build()
   for k,v in flags.items():self.collectvars[k].set(v)
   for k,v in raw.items():self.vars[k].set(v)
   self.magic.current(magic)
   for k,v in upgrades.items():self.upvars[k].current(v)
   for k,v in items.items():self.itemvars[k].current(v)
   self.signature=None;self.update_preview()
   return
  self.language=new;self.build()
 def open(self):
  path=filedialog.askopenfilename(title=self.t('open'),filetypes=[('Memory','*.zip *.png')])
  if not path:return
  try:
   source=Path(path);memories={}
   if zipfile.is_zipfile(source):
    with zipfile.ZipFile(source) as z:
     for info in z.infolist():
      if info.filename.lower().endswith('.png') and not info.is_dir():
       if info.file_size>32*1024*1024:raise ValueError(self.t('tooBig'))
       if info.filename in memories:raise ValueError(self.t('duplicate'))
       memories[info.filename]=z.read(info)
   else:
    if source.stat().st_size>32*1024*1024:raise ValueError(self.t('tooBig'))
    memories[source.name]=source.read_bytes()
   if not memories:raise ValueError(self.t('noPNG'))
   self.source=source;self.source_hash=hashlib.sha256(source.read_bytes()).hexdigest();self.memories=memories
   self.choice.configure(values=list(memories));self.choice.current(len(memories)-1);self.filelabel.configure(text=str(source));self.select()
  except Exception as e:messagebox.showerror(self.t('incompatible'),self.error_text(e))
 def select(self):
  self.choice_name=self.choice.get();self.extra={};self.data=None
  try:
   data=self.memories[self.choice_name];self.report=base.core.inspector.inspect(self.choice_name,data);self.data=data
   profile=self.report['detected_profile'];self.filelabel.configure(text=f"{self.source or self.choice_name}\n{profile['cartridge']} · {self.t('region'+profile['cartridge'][3])} · 1.{profile['revision']}")
   self.loading=True;self.populate();self.loading=False;self.signature=None;self.update_preview()
  except Exception as e:
   self.loading=False;self.populate();messagebox.showerror(self.t('incompatible'),self.error_text(e))
 def maximum(self):
  if self.data is None:messagebox.showinfo(self.t('open'),self.t('openFirst'));return
  money,nuts,e=maximum_preset(self.data,self.report);self.extra=dict(e,rupees=money,ammo_9=nuts)
  self.loading=True;self.populate();self.loading=False;self.signature=None;self.update_preview();self.book.select(5)
 def reset(self):
  if self.data is None:return
  self.extra={};self.loading=True;self.populate();self.loading=False;self.signature=None;self.update_preview()
 def save(self):
  if self.data is None:return
  try:
   if hashlib.sha256(self.source.read_bytes()).hexdigest()!=self.source_hash:raise ValueError(self.t('changedSource'))
   e,money,nuts=self.collect()
   try:patched,changes=edit(self.choice_name,self.data,money,nuts,e)
   except ValueError as err:
    if str(err)=='No hay cambios que guardar.':raise ValueError(self.t('noChanges'))
    raise
   self.book.select(5)
   dest=filedialog.asksaveasfilename(title=self.t('export'),initialfile=Path(self.choice_name).stem+' - copy-v06.zip',defaultextension='.zip',filetypes=[('ZIP','*.zip'),('PNG','*.png')])
   if not dest:return
   base.core.export_copy(self.source,dest,self.choice_name,patched);self.status.set(self.t('saved')+': '+dest);messagebox.showinfo(self.t('saved'),self.t('savedBody')+'\n\n'+self.t('collectionSaved'))
  except Exception as e:messagebox.showerror(self.t('error'),self.error_text(e))
if __name__=='__main__':
 root=tk.Tk();app=App(root)
 if len(sys.argv)==4 and sys.argv[1]=='--self-test':
  root.withdraw()
  with zipfile.ZipFile(sys.argv[2]) as z:name=z.namelist()[-1];data=z.read(name)
  app.memories={name:data};app.choice.configure(values=[name]);app.choice.current(0);app.select();app.maximum()
  e,money,nuts=app.collect();result,changes=edit(name,data,money,nuts,e);summ=base.core.inspector.inspect(name,result)['summary']
  for lang in range(3):app.language=lang;app.build();root.update_idletasks();assert app.valid
  Path(sys.argv[3]).write_text(json.dumps(dict(health=summ['health_raw'],rupees=summ['rupees'],nuts=summ['deku_nuts'],languages=3,changes=len(changes))))
  root.destroy()
 else:root.mainloop()
