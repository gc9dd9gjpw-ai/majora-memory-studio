"""Majora Memory Editor v0.3.1: preset Todo al maximo, solo copias."""
from pathlib import Path
import sys,importlib.util,json,zlib,zipfile,hashlib
ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
spec=importlib.util.spec_from_file_location('core',ROOT/'Majora-Memory-Editor.py');core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
_ispec=importlib.util.spec_from_file_location('regional_inspector',ROOT/'Majora-regional-inspector.py');_inspector=importlib.util.module_from_spec(_ispec);_ispec.loader.exec_module(_inspector);core.inspector=_inspector
tk=core.tk;ttk=core.ttk;messagebox=core.messagebox;filedialog=core.filedialog
NORMAL=['Ocarina','Arco','Flechas de fuego','Flechas de hielo','Flechas de luz','Intercambio: escrituras','Bombas','Bombchus','Palos Deku','Nueces Deku','Judias magicas','Intercambio: llave / carta','Barril de polvora','Camara','Lente de la verdad','Gancho','Espada de la Gran Hada','Intercambio: Kafei']+['Botella '+str(i) for i in range(1,7)]
MASK_NAMES=['Cartero','Trasnochar','Explosiva','Piedra','Gran Hada','Deku','Keaton','Bremen','Conejo','Don Gero','Aromas','Goron','Romani','Circo','Kafei','Pareja','Verdad','Zora','Kamaro','Gibdo','Garo','Capitan','Gigante','Fiera Deidad']
MASK_IDS=[0x3e,0x38,0x47,0x45,0x40,0x32,0x3a,0x46,0x39,0x42,0x48,0x33,0x3c,0x3d,0x37,0x3f,0x36,0x34,0x43,0x41,0x3b,0x44,0x49,0x35]
OPTIONS={i:[255,i] for i in range(18)}
OPTIONS.update({0:[255,0,5],5:[255,0x28,0x29,0x2a,0x2b,0x2c],11:[255,0x2d,0x2e],17:[255,0x2f,0x30]})
for i in range(18,24):OPTIONS[i]=[255]+list(range(0x12,0x28))
for i,v in enumerate(MASK_IDS,24):OPTIONS[i]=[255,v]
ITEM_LABELS={255:'Vacio',0:'Ocarina del Tiempo',5:'Ocarina de hada',0x12:'Botella vacia',0x13:'Pocion roja',0x14:'Pocion verde',0x15:'Pocion azul',0x16:'Hada',0x17:'Princesa Deku',0x18:'Leche',0x19:'Media leche',0x1a:'Pez',0x1b:'Bicho',0x1c:'Fuego azul',0x1d:'Poe',0x1e:'Gran Poe',0x1f:'Agua',0x20:'Agua caliente',0x21:'Huevo Zora',0x22:'Polvo de oro',0x23:'Seta',0x24:'Caballito de mar',0x25:'Chateau Romani',0x26:'Locha Hyliana',0x27:'Bebida especial',0x28:'Lagrima lunar',0x29:'Escritura terrestre',0x2a:'Escritura del pantano',0x2b:'Escritura montana',0x2c:'Escritura oceano',0x2d:'Llave de habitacion',0x2e:'Carta a mama',0x2f:'Carta a Kafei',0x30:'Colgante de recuerdos'}
for i in range(1,17):
 if i not in (5,11):ITEM_LABELS[i]=NORMAL[i]
for name,v in zip(MASK_NAMES,MASK_IDS):ITEM_LABELS[v]='Mascara '+name
AMMO={1:('Flechas',0,[0,30,40,50]),6:('Bombas',3,[0,20,30,40]),7:('Bombchus',None,[50]),8:('Palos Deku',17,[0,10,20,30]),9:('Nueces Deku',20,[0,20,30,40]),10:('Judias',None,[20])}

UPGRADE_MASK=7 | (7<<3) | (3<<12) | (7<<17) | (7<<20)
def maximum_preset(data,report):
 base=int(report['rdram_png_offset'],16)+int(report['save_ram_offset'],16)
 old=int.from_bytes(data[base+0xb8:base+0xbc],'big')
 upgrades=(old & ~UPGRADE_MASK) | 3 | (3<<3) | (2<<12) | (3<<17) | (3<<20)
 extra=dict(healthCapacity=320,health=320,magicMode=2,magicCurrent=96,upgrades=upgrades)
 for i in range(48):
  current=data[base+0x70+i]
  # Preserve choices already held (bottle contents / trading sequence).
  if current==255:
   value=MASK_IDS[i-24] if i>=24 else (0x16 if i>=18 else OPTIONS[i][1])
   extra[f'item_{i}']=value
 for i,(_,_,caps) in AMMO.items():extra[f'ammo_{i}']=max(caps)
 return 500,40,extra

def edit(name,data,rupees,nuts,extra=None):
 extra=dict(extra or {});report=core.inspector.inspect(name,data);start=int(report['rdram_png_offset'],16);base=start+int(report['save_ram_offset'],16)
 result=bytearray(data);changes=[];pending=[]
 def val(off,n=1):return int.from_bytes(data[base+off:base+off+n],'big')
 old_upgrade=val(0xb8,4);upgrade=extra.get('upgrades',old_upgrade)
 if not isinstance(upgrade,int) or not 0<=upgrade<=0xffffffff or (upgrade^old_upgrade)&~UPGRADE_MASK:raise ValueError('Mejoras no compatibles.')
 for shift,mask,maxlevel in [(0,7,3),(3,7,3),(12,3,2),(17,7,3),(20,7,3)]:
  if 'upgrades' in extra and ((upgrade>>shift)&mask)>maxlevel:raise ValueError('Nivel de mejora fuera de rango.')
 if 'upgrades' in extra:pending.append(('Mejoras de capacidad',0xb8,4,upgrade))
 wallet=[99,200,500,500][(upgrade>>12)&3]
 if not 0<=rupees<=wallet:raise ValueError(f'Rupias: 0–{wallet}.')
 pending += [('Rupias',0x3a,2,rupees)]
 extra['ammo_9']=nuts
 known={'health','healthCapacity','magicMode','magicCurrent','upgrades'}|{f'item_{i}' for i in range(48)}|{f'ammo_{i}' for i in AMMO}
 if set(extra)-known:raise ValueError('Campo de edicion desconocido.')
 health=extra.get('health',val(0x36,2));maxhp=extra.get('healthCapacity',val(0x34,2))
 if 'health' in extra or 'healthCapacity' in extra:
  if not 48<=maxhp<=320 or maxhp%16 or not 0<health<=maxhp or health%4:raise ValueError('Salud: 3–20 corazones maximos; salud actual en cuartos y mayor que cero.')
  pending += [('Salud maxima',0x34,2,maxhp),('Salud actual',0x36,2,health)]
 if 'magicMode' in extra:
  mode=extra['magicMode']
  if mode not in (0,1,2):raise ValueError('Nivel de magia incorrecto.')
  current=extra.get('magicCurrent',mode*48)
  if not 0<=current<=mode*48:raise ValueError('Magia fuera de capacidad.')
  # Let Interface_Update initialize runtime capacity and fill through the game's own state machine.
  pending += [('Reinicializar barra de magia',0x38,1,0),('Magia actual',0x39,1,current),('Magia adquirida',0x40,1,int(mode>0)),('Magia doble',0x41,1,int(mode==2))]
 elif 'magicCurrent' in extra:
  if not val(0x40) or not 0<=extra['magicCurrent']<=48*(2 if val(0x41) else 1):raise ValueError('No hay magia adquirida o excede su capacidad.')
  pending += [('Magia actual',0x39,1,extra['magicCurrent'])]
 for i in range(48):
  key=f'item_{i}'
  if key not in extra:continue
  v=extra[key]
  if v not in OPTIONS[i]:raise ValueError(f'Objeto no permitido en slot {i}.')
  old=val(0x70+i)
  if v!=old and old!=255 and old in data[base+0x4c:base+0x5c]:raise ValueError('Desequipa el objeto dentro del juego antes de reemplazarlo o quitarlo.')
  pending += [(('Objeto ' if i<24 else 'Mascara ')+str(i),0x70+i,1,v)]
 for i,(label,shift,caps) in AMMO.items():
  key=f'ammo_{i}'
  if key not in extra:continue
  v=extra[key]
  if v==val(0xa0+i):continue
  level=0 if shift is None else (upgrade>>shift)&7
  cap=caps[level] if level<len(caps) else 0
  item=extra.get(f'item_{i}',val(0x70+i))
  if item==255 and v!=0:raise ValueError(f'{label}: adquiere el objeto primero.')
  if not 0<=v<=cap:raise ValueError(f'{label}: cantidad permitida 0–{cap}, segun mejora actual.')
  pending += [(label,0xa0+i,1,v)]
 for label,off,n,v in pending:
  if not isinstance(v,int):raise ValueError('Los valores deben ser enteros.')
  before=data[base+off:base+off+n];after=v.to_bytes(n,'big')
  if before!=after:result[base+off:base+off+n]=after;changes.append(dict(campo=label,offset_png=hex(base+off),antes=before.hex(),despues=after.hex()))
 if not changes:raise ValueError('No hay cambios que guardar.')
 p=8
 while p+12<=len(result):
  n=int.from_bytes(result[p:p+4],'big')
  if result[p+4:p+8]==b'apmd':crc=p+8+n;result[crc:crc+4]=(zlib.crc32(result[p+4:crc])&0xffffffff).to_bytes(4,'big');break
  p+=n+12
 else:raise ValueError('Falta apmd.')
 core.inspector.inspect(name,bytes(result));allowed=set(range(crc,crc+4))
 for c in changes:
  off=int(c['offset_png'],16);allowed.update(range(off,off+len(bytes.fromhex(c['antes']))))
 if len(result)!=len(data) or any(i not in allowed for i,(a,b) in enumerate(zip(data,result)) if a!=b):raise ValueError('Cambio inesperado.')
 return bytes(result),changes

class App(core.App):
 def __init__(self,root):
  super().__init__(root);root.title('Majora Memory Editor · 0.3.1');root.geometry('920x780')
  self.extra={}
  parent=self.save_button.master
  maxbar=ttk.Frame(parent);maxbar.pack(before=self.save_button,fill='x',pady=(0,8))
  ttk.Button(maxbar,text='Todo al maximo',command=self.maximum).pack(side='left')
  ttk.Label(maxbar,text='20 corazones · magia doble · 500 rupias · inventario · capacidades y municion',wraplength=710).pack(side='left',padx=12)
  toolbar=ttk.Frame(parent);toolbar.pack(before=self.save_button,fill='x',pady=(0,10))
  for label,callback in [('Salud y magia…',self.vitals),('Objetos y mascaras…',self.inventory),('Municion…',self.ammo),('Restablecer cambios',self.reset)]:ttk.Button(toolbar,text=label,command=callback).pack(side='left',padx=(0,8))
  for w in parent.winfo_children():
   if isinstance(w,ttk.Label):
    text=str(w.cget('text'))
    if text.startswith('Version comercial'):w.configure(text='Rupias validadas · Salud, magia e inventario en prueba')
    if text.startswith('Mapa de lectura'):w.configure(text='Mapa de lectura · los cambios pendientes se guardan en una copia')
 def select(self):
  self.extra={};super().select()
 def reset(self):
  if self.data is not None:self.select()
 def maximum(self):
  if self.data is None:messagebox.showinfo('Abre un Memory','Selecciona una captura compatible primero.');return
  try:
   money,nuts,extra=maximum_preset(self.data,self.report)
   edit(self.choice.get(),self.data,money,nuts,extra)
   self.extra=extra;self.rupees.set(str(money));self.nuts.set(str(nuts));self.re.configure(to=500);self.ne.configure(to=40,state='normal')
   self.summary.configure(text='Pendiente: 20 corazones, magia doble\nMonedero: 500 · Nueces: 40')
   self.status.set('Todo al maximo preparado. Guarda una copia para aplicar; Restablecer cambios lo deshace.')
   messagebox.showinfo('Todo al maximo preparado','20 corazones completos, magia doble llena, 500 rupias, todas las mascaras y slots de objetos completos.\n\nCapacidades y municion: 50 flechas, 40 bombas, 50 bombchus, 30 palos, 40 nueces y 20 judias.\n\nLas botellas vacias se rellenan como nuevos slots con hadas. Los objetos y contenidos ya adquiridos se conservan. Guarda una copia para aplicar. Las misiones, canciones, equipo e historia conservan sus valores.')
  except Exception as e:messagebox.showerror('No se pudo preparar',str(e))
 def value(self,off,n=1):
  base=int(self.report['rdram_png_offset'],16)+int(self.report['save_ram_offset'],16);return int.from_bytes(self.data[base+off:base+off+n],'big')
 def dialog(self,title):
  if self.data is None:messagebox.showinfo('Abre un Memory','Selecciona una captura compatible primero.');return None
  top=tk.Toplevel(self.root);top.title(title);top.transient(self.root);top.grab_set();return top
 def vitals(self):
  top=self.dialog('Salud y magia · funciones en prueba')
  if top is None:return
  box=ttk.Frame(top,padding=20);box.pack(fill='both',expand=True)
  hp=tk.StringVar(value=str(self.extra.get('health',self.value(0x36,2))/16));maxhp=tk.StringVar(value=str(self.extra.get('healthCapacity',self.value(0x34,2))//16))
  mode=tk.StringVar(value='Conservar');mg=tk.StringVar(value=str(self.extra.get('magicCurrent',self.value(0x39))))
  for row,(text,var,low,high,step) in enumerate([('Corazones actuales',hp,0.25,20,.25),('Corazones maximos',maxhp,3,20,1),('Magia actual (unidades)',mg,0,96,1)]):
   ttk.Label(box,text=text).grid(row=row,column=0,sticky='w',pady=8);ttk.Spinbox(box,textvariable=var,from_=low,to=high,increment=step,width=12).grid(row=row,column=1,padx=12)
  ttk.Label(box,text='Adquisicion de magia').grid(row=3,column=0,sticky='w');ttk.Combobox(box,textvariable=mode,values=['Conservar','Sin magia','Normal (48)','Doble (96)'],state='readonly',width=20).grid(row=3,column=1)
  ttk.Label(box,text='Prueba primero salud por separado.\nAl cargar, el juego reinicializa la barra y la rellena hasta el valor elegido.').grid(row=4,column=0,columnspan=2,pady=12)
  def apply():
   try:
    candidate=dict(self.extra);h=float(hp.get())*16;m=float(maxhp.get())*16
    if not h.is_integer() or not m.is_integer():raise ValueError('Salud no valida.')
    if int(h)!=self.value(0x36,2) or int(m)!=self.value(0x34,2) or 'health' in candidate:candidate.update(health=int(h),healthCapacity=int(m))
    selected={'Sin magia':0,'Normal (48)':1,'Doble (96)':2}.get(mode.get())
    if selected is not None:candidate.update(magicMode=selected,magicCurrent=int(mg.get()))
    elif int(mg.get())!=self.value(0x39):candidate['magicCurrent']=int(mg.get())
    self.validate_pending(candidate);self.extra=candidate;self.status.set('Salud / magia preparada. Guarda una copia para aplicar.');top.destroy()
   except Exception as e:messagebox.showerror('Revisa los valores',str(e),parent=top)
  ttk.Button(box,text='Aplicar a la copia pendiente',command=apply).grid(row=5,column=0,columnspan=2)
 def validate_pending(self,candidate):
  try:edit(self.choice.get(),self.data,int(self.rupees.get()),int(self.nuts.get()),candidate)
  except ValueError as e:
   if str(e)!='No hay cambios que guardar.':raise
 def inventory(self):
  top=self.dialog('Objetos y mascaras · funciones en prueba')
  if top is None:return
  top.geometry('600x590');canvas=tk.Canvas(top,highlightthickness=0);scroll=ttk.Scrollbar(top,orient='vertical',command=canvas.yview);canvas.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');canvas.pack(fill='both',expand=True);box=ttk.Frame(canvas,padding=14);canvas.create_window((0,0),window=box,anchor='nw');box.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
  vars={};choices={}
  ttk.Label(box,text='Cada objeto usa su slot. No equipa ni altera la historia.').grid(row=0,column=0,columnspan=2,pady=8)
  for i,label in enumerate(NORMAL+MASK_NAMES):
   current=self.extra.get(f'item_{i}',self.value(0x70+i));options=list(OPTIONS[i])
   if current not in options:options.append(current)
   labels={f'{ITEM_LABELS.get(v,"Objeto")} [{v:02X}]':v for v in options};choices[i]=labels
   var=tk.StringVar(value=next(k for k,v in labels.items() if v==current));vars[i]=var
   ttk.Label(box,text=label).grid(row=i+1,column=0,sticky='w',pady=3);ttk.Combobox(box,textvariable=var,values=list(labels),state='readonly',width=33).grid(row=i+1,column=1,padx=10)
  def apply():
   try:
    candidate=dict(self.extra)
    for i,var in vars.items():
     v=choices[i][var.get()]
     if v!=self.value(0x70+i):candidate[f'item_{i}']=v
     else:candidate.pop(f'item_{i}',None)
    self.validate_pending(candidate);self.extra=candidate;self.status.set('Inventario preparado. Guarda una copia para aplicar.');top.destroy()
   except Exception as e:messagebox.showerror('No se pudo aplicar',str(e),parent=top)
  ttk.Button(box,text='Aplicar a la copia pendiente',command=apply).grid(row=50,column=0,columnspan=2,pady=16)
 def ammo(self):
  top=self.dialog('Municion · funciones en prueba')
  if top is None:return
  box=ttk.Frame(top,padding=20);box.pack();variables={};upgrade=self.extra.get('upgrades',self.value(0xb8,4))
  for row,(i,(label,shift,caps)) in enumerate(AMMO.items()):
   level=0 if shift is None else (upgrade>>shift)&7;cap=caps[level] if level<len(caps) else 0
   var=tk.StringVar(value=str(int(self.nuts.get()) if i==9 else self.extra.get(f'ammo_{i}',self.value(0xa0+i))));variables[i]=var
   ttk.Label(box,text=f'{label} (0–{cap})').grid(row=row,column=0,sticky='w',pady=5);ttk.Spinbox(box,textvariable=var,from_=0,to=cap,width=10).grid(row=row,column=1,padx=12)
  def apply():
   try:
    candidate=dict(self.extra)
    for i,var in variables.items():
     if i!=9:candidate[f'ammo_{i}']=int(var.get())
    edit_nuts=int(variables[9].get());edit(self.choice.get(),self.data,int(self.rupees.get()),edit_nuts,candidate)
    self.extra=candidate;self.nuts.set(str(edit_nuts));self.status.set('Municion preparada. Guarda una copia para aplicar.');top.destroy()
   except Exception as e:messagebox.showerror('Revisa las cantidades',str(e),parent=top)
  ttk.Button(box,text='Aplicar a la copia pendiente',command=apply).grid(row=8,column=0,columnspan=2,pady=12)
 def save(self):
  try:
   if self.data is None:return
   if hashlib.sha256(self.source.read_bytes()).hexdigest()!=self.source_hash:raise ValueError('El origen cambio. Vuelve a abrirlo.')
   patched,changes=edit(self.choice.get(),self.data,int(self.rupees.get()),int(self.nuts.get()),self.extra)
   dest=filedialog.asksaveasfilename(initialfile=Path(self.choice.get()).stem+' - copia-v031.zip',defaultextension='.zip',filetypes=[('ZIP','*.zip'),('PNG','*.png')])
   if not dest:return
   core.export_copy(self.source,dest,self.choice.get(),patched);self.status.set('Copia guardada: '+dest)
   messagebox.showinfo('Copia guardada','Original conservado. Cambios:\n'+ '\n'.join(c['campo'] for c in changes)+'\n\nComprueba los valores y el cambio de zona en Analogue.')
  except Exception as e:messagebox.showerror('No se pudo guardar',str(e))
if __name__=='__main__':
 root=tk.Tk()
 if len(sys.argv)==4 and sys.argv[1]=='--self-test':
  root.withdraw();app=App(root)
  with zipfile.ZipFile(sys.argv[2]) as z:name=z.namelist()[-1];data=z.read(name)
  app.memories={name:data};app.choice['values']=[name];app.choice.current(0);app.select();root.update_idletasks()
  money,nuts,extra=maximum_preset(data,app.report);result,_=edit(name,data,money,nuts,extra);summary=core.inspector.inspect(name,result)['summary'];root.destroy()
  with Path(sys.argv[3]).open('x') as f:json.dump(dict(health=summary['health_raw'],rupees=summary['rupees'],nuts=summary['deku_nuts']),f)
 else:App(root);root.mainloop()
