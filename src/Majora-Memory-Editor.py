"""Majora Memory Editor 0.1 — experimental, Windows, solo copias."""
from pathlib import Path
import json,zipfile,zlib,hashlib,importlib.util,sys,os,tempfile
import tkinter as tk
from tkinter import ttk,filedialog,messagebox

ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
spec=importlib.util.spec_from_file_location('inspector',ROOT/'Majora-inspector.py')
inspector=importlib.util.module_from_spec(spec);spec.loader.exec_module(inspector)

def patch_memory(name,data,rupees,nuts):
 report=inspector.inspect(name,data)
 fields={f['name']:f for f in report['fields']}
 ram_start=int(report['rdram_png_offset'],16)
 upgrade=int.from_bytes(data[ram_start+0x1e6fa8:ram_start+0x1e6fac],'big')
 wallet=[99,200,500,500][(upgrade>>12)&3]
 nut_level=(upgrade>>20)&7
 nut_cap=[0,20,30,40][nut_level] if nut_level<4 else None
 if not 0<=rupees<=wallet:raise ValueError(f'Rupias: permitido 0–{wallet} con el monedero actual.')
 old_nuts=report['summary']['deku_nuts']
 if nuts!=old_nuts:
  if report['summary']['deku_nut_item']!='0x9':raise ValueError('Esta captura no tiene nueces Deku. Esta version no agrega objetos.')
  if nut_cap is None or not 0<=nuts<=nut_cap:raise ValueError(f'Cantidad de nueces fuera de capacidad ({nut_cap}).')
 result=bytearray(data);changes=[]
 for label,offset,value,size in [('Rupias',int(fields['rupees']['png_offset'],16),rupees,2),('Nueces',ram_start+0x1e6f99,nuts,1)]:
  before=data[offset:offset+size];after=value.to_bytes(size,'big')
  if before!=after:result[offset:offset+size]=after;changes.append(dict(campo=label,offset_png=hex(offset),antes=before.hex(),despues=after.hex()))
 if not changes:raise ValueError('No hay cambios que guardar.')
 p=8
 while p+12<=len(result):
  n=int.from_bytes(result[p:p+4],'big');tag=result[p+4:p+8]
  if tag==b'apmd':
   crc_pos=p+8+n;result[crc_pos:crc_pos+4]=(zlib.crc32(result[p+4:crc_pos])&0xffffffff).to_bytes(4,'big');break
  p+=n+12
 else:raise ValueError('Falta apmd.')
 verified=inspector.inspect(name,bytes(result))
 assert verified['summary']['rupees']==rupees and verified['summary']['deku_nuts']==nuts
 allowed=set(range(crc_pos,crc_pos+4))
 for c in changes:
  offset=int(c['offset_png'],16);allowed.update(range(offset,offset+len(bytes.fromhex(c['antes']))))
 if len(result)!=len(data) or any(i not in allowed for i,(a,b) in enumerate(zip(data,result)) if a!=b):raise ValueError('Cambio inesperado fuera de campos autorizados.')
 return bytes(result),changes

def export_copy(source,dest,name,patched):
 source=Path(source).resolve();dest=Path(dest).resolve()
 if source==dest:raise ValueError('El destino debe ser una copia distinta del original.')
 if dest.exists():raise ValueError('El destino ya existe. Elige otro nombre para conservarlo.')
 # Exclusive creation prevents accidental overwriting. Keep the internal Memory filename.
 created=False
 try:
  with dest.open('xb') as stream:
   created=True
   if dest.suffix.lower()=='.zip':
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:z.writestr(name,patched)
   elif dest.suffix.lower()=='.png':stream.write(patched)
   else:raise ValueError('Elige una extension .zip o .png.')
 except Exception:
  if created and dest.exists():dest.unlink()
  raise

class App:
 def __init__(self,root):
  self.root=root;self.source=None;self.memories={};self.data=None
  root.title('Majora Memory Editor · 0.1');root.geometry('860x650');root.minsize(740,560)
  style=ttk.Style();style.theme_use('clam')
  frame=ttk.Frame(root,padding=20);frame.pack(fill='both',expand=True)
  ttk.Label(frame,text='Majora Memory Editor',font=('Segoe UI',22,'bold')).pack(anchor='w')
  ttk.Label(frame,text='Version comercial compatible · Rupias y nueces Deku',font=('Segoe UI',11)).pack(anchor='w',pady=(2,10))
  ttk.Label(frame,text='Experimental: la copia editada requiere prueba en Analogue 3D.\nEl editor conserva el original; la miniatura sigue mostrando la captura original.',foreground='#8b4b00').pack(anchor='w',pady=(0,12))
  ttk.Button(frame,text='Abrir ZIP o PNG…',command=self.open).pack(anchor='w')
  self.file_label=ttk.Label(frame,text='Ningun archivo abierto',wraplength=780);self.file_label.pack(anchor='w',pady=8)
  self.choice=ttk.Combobox(frame,state='readonly');self.choice.pack(fill='x');self.choice.bind('<<ComboboxSelected>>',lambda e:self.select())
  box=ttk.LabelFrame(frame,text='Cambios',padding=12);box.pack(fill='x',pady=12)
  self.rupees=tk.StringVar();self.nuts=tk.StringVar()
  ttk.Label(box,text='Rupias').grid(row=0,column=0,sticky='w');self.re=ttk.Spinbox(box,textvariable=self.rupees,from_=0,to=99,width=10);self.re.grid(row=0,column=1,padx=15)
  ttk.Label(box,text='Cantidad de nueces Deku').grid(row=1,column=0,sticky='w',pady=8);self.ne=ttk.Spinbox(box,textvariable=self.nuts,from_=0,to=20,width=10);self.ne.grid(row=1,column=1,padx=15)
  self.summary=ttk.Label(box,text='');self.summary.grid(row=0,column=2,rowspan=2,sticky='w',padx=12)
  self.save_button=ttk.Button(frame,text='Guardar copia editada…',command=self.save,state='disabled');self.save_button.pack(anchor='w',pady=(0,10))
  ttk.Label(frame,text='Mapa de lectura · los demas campos no se editan en esta version').pack(anchor='w')
  tableframe=ttk.Frame(frame);tableframe.pack(fill='both',expand=True,pady=6)
  self.tree=ttk.Treeview(tableframe,columns=('campo','ram','valor'),show='headings')
  for c,title,width in [('campo','Campo / slot',300),('ram','Direccion RAM',150),('valor','Bytes actuales',280)]:self.tree.heading(c,text=title);self.tree.column(c,width=width)
  scroll=ttk.Scrollbar(tableframe,orient='vertical',command=self.tree.yview);self.tree.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');self.tree.pack(fill='both',expand=True)
  self.status=tk.StringVar(value='Abre una captura para empezar.');ttk.Label(frame,textvariable=self.status,wraplength=780).pack(anchor='w',pady=5)
 def open(self):
  path=filedialog.askopenfilename(filetypes=[('Memories','*.zip *.png')])
  if not path:return
  try:
   source=Path(path);memories={}
   if zipfile.is_zipfile(source):
    with zipfile.ZipFile(source) as z:
     for i in z.infolist():
      if i.filename.lower().endswith('.png') and not i.is_dir():
       if i.file_size>32*1024*1024:raise ValueError('PNG demasiado grande.')
       if i.filename in memories:raise ValueError('ZIP con nombres duplicados.')
       memories[i.filename]=z.read(i)
   else:
    if source.stat().st_size>32*1024*1024:raise ValueError('Archivo demasiado grande.')
    memories[source.name]=source.read_bytes()
   if not memories:raise ValueError('ZIP sin PNG.')
   self.source=source;self.memories=memories;self.source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
   self.choice['values']=list(memories);self.choice.current(len(memories)-1);self.file_label.configure(text=str(source));self.select()
  except Exception as e:messagebox.showerror('No se pudo abrir',str(e))
 def select(self):
  self.save_button.configure(state='disabled');self.tree.delete(*self.tree.get_children());self.data=None
  try:
   name=self.choice.get();data=self.memories[name];report=inspector.inspect(name,data);self.data=data;self.report=report
   s=report['summary'];self.rupees.set(str(s['rupees']));self.nuts.set(str(s['deku_nuts']));self.re.configure(to=s['wallet_capacity'])
   off=int(report['rdram_png_offset'],16)+0x1e6fa8;upgrade=int.from_bytes(data[off:off+4],'big');level=(upgrade>>20)&7;cap=[0,20,30,40][level] if level<4 else 0
   self.ne.configure(to=cap,state='normal' if s['deku_nut_item']=='0x9' else 'disabled')
   self.summary.configure(text=f"Salud: {s['health_raw']} / {s['health_capacity_raw']} (unidades)\nMonedero: {s['wallet_capacity']} · Capacidad de nueces: {cap}")
   for f in report['fields']:self.tree.insert('', 'end',values=(f['name'],f['ram_address'],f['bytes']))
   self.save_button.configure(state='normal');self.status.set('CRC y version comprobados. Edita un campo y guarda una copia.')
  except Exception as e:self.status.set(str(e));messagebox.showerror('Memory no compatible',str(e))
 def save(self):
  try:
   if self.data is None:return
   if hashlib.sha256(self.source.read_bytes()).hexdigest()!=self.source_hash:raise ValueError('El archivo de origen cambio. Vuelve a abrirlo.')
   patched,changes=patch_memory(self.choice.get(),self.data,int(self.rupees.get()),int(self.nuts.get()))
   dest=filedialog.asksaveasfilename(initialfile=Path(self.choice.get()).stem+' - copia-editada.zip',defaultextension='.zip',filetypes=[('ZIP de Memory','*.zip'),('PNG de Memory','*.png')])
   if not dest:return
   export_copy(self.source,dest,self.choice.get(),patched)
   self.status.set('Copia guardada: '+str(dest))
   messagebox.showinfo('Copia guardada','Original conservado.\n\nCambios: '+', '.join(c['campo'] for c in changes)+'\n\nPrueba la copia en Analogue 3D y comprueba el valor y el cambio de zona. El ZIP contiene solo el Memory seleccionado, con su nombre original.')
  except Exception as e:messagebox.showerror('No se pudo guardar',str(e))
if __name__=='__main__':
 if len(sys.argv)==4 and sys.argv[1]=='--self-test':
  root=tk.Tk();root.withdraw();app=App(root)
  with zipfile.ZipFile(sys.argv[2]) as archive:
   name=[n for n in archive.namelist() if n.lower().endswith('.png')][-1];data=archive.read(name)
  app.memories={name:data};app.choice['values']=[name];app.choice.current(0);app.select();root.update_idletasks()
  patched,_=patch_memory(name,data,50,int(app.nuts.get()))
  check=dict(gui_fields=len(app.tree.get_children()),rupees=inspector.inspect(name,patched)['summary']['rupees'])
  root.destroy()
  with Path(sys.argv[3]).open('x',encoding='utf-8') as output:json.dump(check,output)
 else:
  root=tk.Tk();App(root);root.mainloop()
