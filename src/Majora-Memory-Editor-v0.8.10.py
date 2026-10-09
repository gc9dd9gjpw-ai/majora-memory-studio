"""Memory equipment inspection, double defense and Razor durability; original-cartridge workflow."""
from pathlib import Path
import importlib.util,sys,json,zipfile,zlib
ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
def module(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=module('studio089','Majora-Memory-Editor-v0.8.9.py');gear=module('gear','Majora-Native-Equipment.py')
tk=old.tk;ttk=old.ttk;ui=old.ui;native=old.native;recovery=old.recovery;decode=old.decode
previous=old.edit
def edit(name,data,money,nuts,extra=None):
 extra=dict(extra or {});defense=extra.pop('doubleDefense',None);durability=extra.pop('razorDurability',None)
 try:result,changes=previous(name,data,money,nuts,extra)
 except ValueError as e:
  if str(e)!='No hay cambios que guardar.':raise
  result,changes=data,[]
 if defense is None and durability is None:
  if not changes:raise ValueError('No hay cambios que guardar.')
  return result,changes
 report=ui.base.core.inspector.inspect(name,result);p=report['detected_profile']
 if (p['cartridge'],p['revision']) not in [('NZSE',0),('NZSP',1)]:raise ValueError('equipmentProfile')
 b=int(report['rdram_png_offset'],16)+int(report['save_ram_offset'],16);out=bytearray(result);allowed=set()
 def put(label,offset,value):
  at=b+offset;before=bytes(out[at:at+len(value)])
  if before!=value:out[at:at+len(value)]=value;allowed.update(range(at,at+len(value)));changes.append(dict(campo=label,offset_png=hex(at),antes=before.hex(),despues=value.hex()))
 if defense is not None:
  if type(defense)!=int or defense not in (0,1):raise ValueError('equipmentRange')
  put('doubleDefense',0x42,bytes([defense]));put('defenseHearts',0xd3,bytes([20 if defense else 0]))
 if durability is not None:
  eq=int.from_bytes(out[b+0x6c:b+0x6e],'big')
  if eq&15!=2 or type(durability)!=int or not 1<=durability<=100:raise ValueError('razorRange')
  put('razorDurability',0x3c,durability.to_bytes(2,'big'))
 if out!=result:
  block=bytearray(out[b:b+0x100c]);block[0x100a:0x100c]=bytes(2);put('Save checksum',0x100a,(sum(block)&65535).to_bytes(2,'big'))
  pos=8
  while pos+12<=len(out):
   n=int.from_bytes(out[pos:pos+4],'big')
   if out[pos+4:pos+8]==b'apmd':
    at=pos+8+n;out[at:at+4]=(zlib.crc32(out[pos+4:at])&0xffffffff).to_bytes(4,'big');allowed.update(range(at,at+4));break
   pos+=n+12
  else:raise ValueError('Missing apmd')
  assert all(i in allowed for i,(a,c) in enumerate(zip(result,out)) if a!=c);result=bytes(out);ui.base.core.inspector.inspect(name,result)
 if not changes:raise ValueError('No hay cambios que guardar.')
 return result,changes
old.edit=edit;ui.edit=edit
class App(old.App):
 def et(self,es,en,fr):return (es,en,fr)[self.language]
 def build(self):
  self.equipment_ready=False;super().build();self.root.title('Majora · Memory Studio 0.8.10')
  page=ttk.Frame(self.book,padding=18);self.book.add(page,text=self.et('Equipo','Equipment','Équipement'))
  self.equipment_summary=tk.StringVar();ttk.Label(page,textvariable=self.equipment_summary,font=('Segoe UI',11,'bold'),wraplength=900).pack(anchor='w',pady=8)
  row=ttk.Frame(page);row.pack(anchor='w',pady=8)
  ttk.Label(row,text=self.et('Defensa','Defense','Défense'),width=22).grid(row=0,column=0,sticky='w',pady=6)
  self.defense_box=ttk.Combobox(row,state='readonly',values=[self.et('Conservar','Keep','Conserver'),self.et('Normal','Normal','Normale'),self.et('Doble','Double','Double')],width=18);self.defense_box.current(0);self.defense_box.grid(row=0,column=1,pady=6);self.defense_box.bind('<<ComboboxSelected>>',lambda event:self.update_preview())
  ttk.Label(row,text=self.et('Usos restantes de Espada Afilada','Razor Sword uses left','Usages restants de l’épée Rasoir'),width=32).grid(row=1,column=0,sticky='w',pady=6)
  self.razor_var=tk.StringVar();self.vars['razorDurability']=self.razor_var;self.razor_box=ttk.Spinbox(row,textvariable=self.razor_var,from_=1,to=100,width=16);self.razor_box.grid(row=1,column=1,pady=6)
  ttk.Label(page,text=self.et('Defensa doble: daño reducido y corazones con borde. Cambia el estado activo del Memory; no completa la misión de la Gran Hada. Confirmado en decomp y localizado en Memory; edición física pendiente.','Double defense: reduced damage and outlined hearts. Changes active Memory state; does not complete the Great Fairy quest. Confirmed in decomp and located in Memory; physical edit validation pending.','Double défense : dégâts réduits et cœurs bordés. Modifie l’état actif du Memory ; ne termine pas la quête de la Grande Fée. Confirmé dans la decomp et localisé ; validation physique en attente.'),wraplength=900,foreground='#c3a66a').pack(anchor='w',pady=15)
  ttk.Label(page,text=self.et('Espada y escudo se muestran en lectura. Su sustitución en un Memory requiere sincronizar el personaje, el botón B y los modelos/iconos. No se usa un .sav para estas opciones.','Sword and shield are displayed read-only. Replacing them in a Memory requires synchronizing player, B button and models/icons. These options do not use a .sav.','Épée et bouclier affichés en lecture seule. Leur remplacement exige la synchronisation du personnage, du bouton B et des modèles/icônes. Ces options n’utilisent pas de .sav.'),wraplength=900).pack(anchor='w',pady=8)
  self.equipment_ready=True;self.populate();self.update_preview()
 def populate(self):
  super().populate()
  if not getattr(self,'equipment_ready',False):return
  if not self.data:
   self.equipment_summary.set('—');self.defense_box.configure(state='disabled');self.razor_box.configure(state='disabled');return
  b=int(self.report['rdram_png_offset'],16)+int(self.report['save_ram_offset'],16);p=gear.read(self.data[b:b+0x100c]);self.equipment_data=p
  swords=[self.et('Ninguna','None','Aucune'),'Kokiri',self.et('Afilada','Razor','Rasoir'),self.et('Dorada','Gilded','Dorée')];shields=[self.et('Ninguno','None','Aucun'),self.et('Héroe','Hero','Héros'),self.et('Espejo','Mirror','Miroir')]
  sword=swords[p['sword']] if p['sword']<4 else str(p['sword']);shield=shields[p['shield']] if p['shield']<3 else str(p['shield'])
  self.equipment_summary.set(self.et('Espada: ','Sword: ','Épée : ')+sword+self.et(' · Escudo: ',' · Shield: ',' · Bouclier : ')+shield+self.et(' · Defensa doble: ',' · Double defense: ',' · Double défense : ')+str(p['defense']))
  enabled=(self.report['detected_profile']['cartridge'],self.report['detected_profile']['revision']) in [('NZSE',0),('NZSP',1)]
  self.defense_box.configure(state='readonly' if enabled else 'disabled');self.defense_box.current(self.extra.get('doubleDefense',-1)+1)
  self.razor_var.set(str(self.extra.get('razorDurability',p['durability'])));self.razor_box.configure(state='normal' if enabled and p['sword']==2 else 'disabled')
 def collect(self):
  extra,money,nuts=super().collect()
  if not getattr(self,'equipment_ready',False) or not self.data:return extra,money,nuts
  i=self.defense_box.current()
  if i>0:extra['doubleDefense']=i-1
  if self.equipment_data['sword']==2:
   try:v=int(self.razor_var.get())
   except ValueError:raise ValueError('razorRange')
   if v!=self.equipment_data['durability']:extra['razorDurability']=v
  return extra,money,nuts
 def describe(self,c):
  names={'doubleDefense':self.et('Defensa doble','Double defense','Double défense'),'defenseHearts':self.et('Corazones con defensa','Defense hearts','Cœurs protégés'),'razorDurability':self.et('Usos de Espada Afilada','Razor Sword uses','Usages de l’épée Rasoir')}
  if c['campo'] in names:return names[c['campo']],str(int(c['antes'],16)),str(int(c['despues'],16))
  return super().describe(c)
 def error_text(self,e):
  if str(e)=='equipmentProfile':return self.et('Equipo editable para USA 1.0 y PAL 1.1 investigados.','Equipment editing supports researched USA 1.0 and PAL 1.1.','Équipement modifiable pour USA 1.0 et PAL 1.1 étudiés.')
  if str(e)=='razorRange':return self.et('La durabilidad exige Espada Afilada y un valor de 1 a 100.','Durability requires Razor Sword and a value from 1 to 100.','Durabilité : épée Rasoir requise et valeur de 1 à 100.')
  return super().error_text(e)
if __name__=='__main__':
 root=tk.Tk()
 if len(sys.argv)==4 and sys.argv[1]=='--self-test':
  root.withdraw();app=App(root)
  with zipfile.ZipFile(sys.argv[2]) as z:name='despues.png';data=z.read(name)
  app.memories={name:data};app.choice.configure(values=[name]);app.choice.current(0);app.select();app.defense_box.current(2);app.update_preview();assert app.valid
  for lang in range(3):app.extra=app.collect()[0];app.language=lang;app.build();root.update_idletasks();assert app.defense_box.current()==2 and app.valid
  Path(sys.argv[3]).write_text(json.dumps({'version':'0.8.10','languages':3,'Memory_equipment':'PASS'}));root.destroy()
 else:App(root);root.mainloop()
