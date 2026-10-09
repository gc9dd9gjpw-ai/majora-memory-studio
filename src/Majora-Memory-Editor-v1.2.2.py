"""Light desktop presentation; preserves the v1.2.1 editing operations."""
from pathlib import Path
import importlib.util,sys,json,zipfile,hashlib
ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
s=importlib.util.spec_from_file_location('studio121',ROOT/'Majora-Memory-Editor-v1.2.1.py');legacy=importlib.util.module_from_spec(s);s.loader.exec_module(legacy)
tk=legacy.tk;ttk=legacy.ttk
edit=legacy.edit

class App(legacy.InternationalApp):
 def __init__(self,root):
  self.regional_panel=None;self.embed_regional=True;self.hidden_widgets=[];self.limit_labels={}
  super().__init__(root);root.title('Majora · Memory Studio 1.2.2');root.geometry('1240x950');root.minsize(1080,820)
 def theme(self,root):
  super().theme(root);root.configure(background='#f5f6f8');style=ttk.Style(root)
  root.option_add('*TCombobox*Listbox.background','#ffffff');root.option_add('*TCombobox*Listbox.foreground','#222632')
  for name in ('.','TFrame','TLabel','TLabelframe','TLabelframe.Label','TNotebook'):
   style.configure(name,background='#f5f6f8',foreground='#222632')
  style.configure('TButton',background='#e8ebf0',foreground='#222632',borderwidth=1,padding=(10,7))
  style.map('TButton',background=[('active','#ded7ed'),('disabled','#eef0f3')],foreground=[('disabled','#87909b')])
  style.configure('Accent.TButton',background='#6f46a6',foreground='white')
  style.map('Accent.TButton',background=[('active','#8355b9'),('disabled','#ddd4e8')],foreground=[('disabled','#77717e')])
  style.configure('Nav.TButton',padding=(8,6));style.configure('Selected.Nav.TButton',background='#ddd0ef',foreground='#452771')
  for name in ('TEntry','TSpinbox','TCombobox'):
   style.configure(name,fieldbackground='white',background='#e8ebf0',foreground='#222632',insertcolor='#222632',arrowcolor='#6f46a6',padding=4)
   style.map(name,fieldbackground=[('readonly','white'),('disabled','#eef0f3')],foreground=[('readonly','#222632'),('disabled','#87909b')])
  style.configure('Treeview',background='white',fieldbackground='white',foreground='#222632',rowheight=27)
  style.configure('Treeview.Heading',background='#e8ebf0',foreground='#543382')
  style.map('Treeview',background=[('selected','#ddd0ef')],foreground=[('selected','#222632')])
  style.configure('TNotebook.Tab',background='#e8ebf0',foreground='#222632',padding=(9,7))
  style.map('TNotebook.Tab',background=[('selected','#ddd0ef')],foreground=[('selected','#452771')])
  style.layout('Wrapped.TNotebook.Tab',[])
 def build(self):
  self.limit_labels={};self.regional_panel=None;self.hidden_widgets=[]
  super().build();self.root.title('Majora · Memory Studio 1.2.2');self.light_widgets(self.frame);self.navigation(self.book);self.add_main_limits()
 def light_widgets(self,w):
  if isinstance(w,tk.Canvas):w.configure(background='#f5f6f8')
  if isinstance(w,ttk.Label):
   color=str(w.cget('foreground'))
   if color and color!='#222632':w.configure(foreground='#543382' if color in ('#b9a5ff','#c6b7f2','#c3a66a','#f1edff') else '#394352')
  for child in w.winfo_children():self.light_widgets(child)
 def navigation(self,book):
  if hasattr(book,'nav'):book.nav.destroy()
  book.configure(style='Wrapped.TNotebook');nav=ttk.Frame(book.master);book.nav=nav
  nav.pack(fill='x',before=book,pady=(0,5));buttons=[]
  # Full names remain visible in two or more rows at every supported window size.
  for i,tab in enumerate(book.tabs()):
   button=ttk.Button(nav,text=book.tab(tab,'text'),style='Nav.TButton',command=lambda tab=tab:book.select(tab))
   button.grid(row=i//6,column=i%6,sticky='ew',padx=2,pady=2);buttons.append((tab,button));nav.columnconfigure(i%6,weight=1)
  def selected(event=None):
   for tab,button in buttons:button.configure(style='Selected.Nav.TButton' if book.select()==tab else 'Nav.TButton')
  book.bind('<<NotebookTabChanged>>',selected,add='+');selected()
 def limit_text(self,capacity,maximum):
  lang=3 if self.german else self.language
  capacity=str(capacity).removesuffix('.0');maximum=str(maximum).removesuffix('.0')
  return ('Capacidad: {c} · Máximo: {m}','Capacity: {c} · Maximum: {m}','Capacité : {c} · Maximum : {m}','Kapazität: {c} · Maximum: {m}')[lang].format(c=capacity,m=maximum)
 def add_main_limits(self):
  mapping={str(var):key for key,var in self.vars.items()}
  def visit(w):
   if isinstance(w,ttk.Spinbox) and str(w.cget('textvariable')) in mapping:
    key=mapping[str(w.cget('textvariable'))]
    if key in {'health','healthCapacity','magicCurrent','rupees','arrows','bombs','bombchus','sticks','nuts','beans'}:
     grid=w.grid_info();label=ttk.Label(w.master);label.grid(row=grid['row'],column=int(grid['column'])+1,sticky='w',padx=(10,0));self.limit_labels[key]=label
   for child in list(w.winfo_children()):visit(child)
  visit(self.book);self.refresh_limits()
 def refresh_limits(self):
  if self.regional_panel:return self.refresh_regional_limits()
  def level(key,default=0):
   box=self.upvars.get(key);i=box.current() if box else default;return max(0,i)
  def cap(key,values):return values[min(level(key),len(values)-1)]
  hp=20
  try:hp=float(self.vars['healthCapacity'].get())
  except ValueError:pass
  mode=self.magic.current()
  mc=96
  if mode>0:mc=(mode-1)*48
  elif self.data:mc=48*(2 if self.value(0x41) else 1) if self.value(0x40) else 0
  capacities={'health':(hp,20),'healthCapacity':(20,20),'magicCurrent':(mc,96),'rupees':(cap('wallet',[99,200,500]),500),'arrows':(cap('quiver',[0,30,40,50]),50),'bombs':(cap('bag',[0,20,30,40]),40),'bombchus':(50,50),'sticks':(cap('sticksCapacity',[0,10,20,30]),30),'nuts':(cap('nutsCapacity',[0,20,30,40]),40),'beans':(20,20)}
  for key,label in self.limit_labels.items():label.configure(text=self.limit_text(*capacities[key]))
 def update_preview(self):
  super().update_preview()
  if hasattr(self,'limit_labels'):self.refresh_limits()
 def tick(self):
  if self.regional_panel:
   try:self.refresh_regional_limits()
   except (ValueError,tk.TclError):pass
   self.root.after(300,self.tick)
  else:super().tick()
 def clear_regional(self):
  if self.regional_panel:self.regional_panel.root.destroy();self.regional_panel=None
  for w,info in self.hidden_widgets:
   if w.winfo_exists():w.pack(**info)
  self.hidden_widgets=[]
 def select(self):
  self.clear_regional();name=self.choice.get();data=self.memories.get(name)
  if data:
   try:report=legacy.ui.base.core.inspector.inspect(name,data)
   except ValueError:return super().select()
   p=report['detected_profile']
   backend=legacy.japan if (p['cartridge'],p['revision'])==('NZSJ',1) else legacy.pal10 if (p['cartridge'],p['revision'])==('NZSP',0) else None
   if backend:
    self.data=None;self.extra={};self.choice_name=name;self.filelabel.configure(text=str(self.source or name)+'\n'+p['cartridge']+' · 1.'+str(p['revision']))
    children=self.frame.pack_slaves();start=children.index(self.book.nav)
    for w in children[start:]:info=w.pack_info();info.pop('in',None);self.hidden_widgets.append((w,info));w.pack_forget()
    self.regional_backend=backend;self.regional_panel=backend.Panel(self,name,data);self.decorate_regional();return
  return super().select()
 def decorate_regional(self):
  panel=self.regional_panel;self.light_widgets(panel.root);self.navigation(panel.book);panel.limit_labels={}
  names={'healthCapacity':self.t('healthCapacity'),'health':self.t('health'),'magicCurrent':self.t('magicCurrent'),'rupees':self.t('rupees'),'bank':self.pt('Rupias del banco','Bank rupees','Rubis en banque')}
  for i,key in {1:'arrows',6:'bombs',7:'bombchus',8:'sticks',9:'nuts',10:'beans'}.items():names['ammo_'+str(i)]=self.t(key)
  variable_keys={str(v):key for key,v in panel.vars.items()}
  def visit(w):
   if isinstance(w,ttk.Entry) and str(w.cget('textvariable')) in variable_keys:
    key=variable_keys[str(w.cget('textvariable'))]
    if key in names:
     info=w.grid_info();row=info['row'];column=info['column']
     for label in w.master.grid_slaves(row=row,column=0):
      if isinstance(label,ttk.Label):label.configure(text=names[key])
     label=ttk.Label(w.master);label.grid(row=row,column=int(column)+1,padx=10,sticky='w');panel.limit_labels[key]=label
   for child in list(w.winfo_children()):visit(child)
  visit(panel.book);self.refresh_regional_limits()
 def refresh_regional_limits(self):
  panel=self.regional_panel
  if not panel or not hasattr(panel,'limit_labels'):return
  levels={shift:int(v.get()) for shift,mask,v in panel.upgrade_vars if v.get().isdigit()};mode=panel.magic.get()
  magic={'None':0,'Normal':48,'Double':96}.get(mode,48*(2 if panel.value(0x41) else 1) if panel.value(0x40) else 0)
  caps={'healthCapacity':(20,20),'health':(float(panel.vars['healthCapacity'].get() or 0),20),'magicCurrent':(magic,96),'rupees':([99,200,500,500][min(levels.get(12,0),3)],500),'bank':(9999,9999)}
  for i,(label,shift,values) in self.regional_backend.writer.AMMO.items():
   lev=levels.get(shift,0) if shift is not None else 0;caps['ammo_'+str(i)]=(values[min(lev,len(values)-1)],max(values))
  for key,label in panel.limit_labels.items():
   c,m=caps[key];label.configure(text=self.limit_text(c,m))
 def change_language(self,event=None):
  if not self.regional_panel:
   chosen=self.lang.current()
   if self.data:
    try:
     extra,money,nuts=self.collect();self.extra=dict(extra,rupees=money,ammo_9=nuts)
    except ValueError as e:
     legacy.ui.messagebox.showerror(self.t('error'),self.error_text(e));self.lang.current(3 if self.german else self.language);return
   self.german=chosen==3;self.language=1 if self.german else chosen;self.build();return
  panel=self.regional_panel
  # Preserve pending edits, including unfinished text, when rebuilding regional labels.
  state={'vars':{k:v.get() for k,v in panel.vars.items()},'items':{k:v[0].current() for k,v in panel.items.items()},'progress':{k:v[0].get() for k,v in panel.progress.items()},'songs':{k:v.get() for k,v in panel.songvars.items()},'notes':[v.current() for v in panel.notevars],'upgrades':[v.get() for _,_,v in panel.upgrade_vars],'magic':panel.magic.get(),'active':panel.scarecrow.get(),'edit':panel.edit_notes.get(),'reset':panel.resetvar.get(),'patches':dict(panel.collection_patches),'photo':panel.photo_hex}
  backend=self.regional_backend;name=panel.name;data=panel.data;chosen=self.lang.current();self.german=chosen==3;self.language=1 if self.german else chosen
  self.build();self.choice.set(name);self.select();panel=self.regional_panel
  for k,v in state['vars'].items():panel.vars[k].set(v)
  for k,v in state['items'].items():panel.items[k][0].current(v)
  for k,v in state['progress'].items():panel.progress[k][0].set(v)
  for k,v in state['songs'].items():panel.songvars[k].set(v)
  for box,v in zip(panel.notevars,state['notes']):box.current(v)
  for (_,_,var),v in zip(panel.upgrade_vars,state['upgrades']):var.set(v)
  panel.magic.set(state['magic']);panel.scarecrow.set(state['active']);panel.edit_notes.set(state['edit']);panel.resetvar.set(state['reset']);panel.collection_patches=state['patches'];panel.photo_hex=state['photo']
  for key,v in state['patches'].items():values=panel.individual.item(key,'values');panel.individual.item(key,values=(values[0],v))
  self.refresh_regional_limits()

if __name__=='__main__':
 root=tk.Tk();app=App(root)
 if len(sys.argv)==4 and sys.argv[1]=='--ui-self-test':
  root.withdraw();app.source=Path(sys.argv[2]);app.source_hash=hashlib.sha256(app.source.read_bytes()).hexdigest()
  with zipfile.ZipFile(app.source) as z:name=next(n for n in z.namelist() if n.endswith('.png'));data=z.read(name)
  app.memories={name:data};app.choice.configure(values=[name]);app.choice.current(0);app.select()
  for language in range(4):app.lang.current(language);app.change_language();root.update_idletasks();assert not any(isinstance(w,tk.Toplevel) for w in root.winfo_children())
  panel=app.regional_panel;labels=panel.limit_labels if panel else app.limit_labels
  assert len(labels)>=10 and all('Maxim' in str(l.cget('text')) for l in labels.values())
  Path(sys.argv[3]).write_text(json.dumps({'version':'1.2.2','one_window':True,'languages':4,'visible_limits':len(labels),'light_background':root.cget('background')}),encoding='utf8');root.destroy()
 else:root.mainloop()
