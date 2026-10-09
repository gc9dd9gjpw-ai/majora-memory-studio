"""Majora Memory Studio 0.8: bank balance, separate from carried rupees."""
from pathlib import Path
import sys,importlib.util,zlib,json,zipfile
ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
spec=importlib.util.spec_from_file_location('studio071',ROOT/'Majora-Memory-Editor-v0.7.1.py');studio=importlib.util.module_from_spec(spec);spec.loader.exec_module(studio)
tk=studio.tk;ttk=studio.ttk
previous_edit=studio.edit
def edit(name,data,money,nuts,extra=None):
 extra=dict(extra or {});bank=extra.pop('bankRupees',None)
 try:result,changes=previous_edit(name,data,money,nuts,extra)
 except ValueError as e:
  if str(e)!='No hay cambios que guardar.':raise
  result,changes=data,[]
 if bank is not None:
  report=studio.ui.base.core.inspector.inspect(name,result)
  if not studio.songs.supported(report):raise ValueError('bankProfile')
  if type(bank)!=int or not 0<=bank<=5499:raise ValueError('bankRange')
  b=int(report['rdram_png_offset'],16)+int(report['save_ram_offset'],16)
  out=bytearray(result);allowed=set()
  def put(label,at,raw):
   before=bytes(out[at:at+len(raw)])
   if before!=raw:
    out[at:at+len(raw)]=raw;allowed.update(range(at,at+len(raw)))
    changes.append(dict(campo=label,offset_png=hex(at),antes=before.hex(),despues=raw.hex()))
  put('Bank rupees',b+0xede,bank.to_bytes(2,'big'))
  if bytes(out)!=result:
   block=bytearray(out[b:b+0x100c]);block[0x100a:0x100c]=b'\0\0'
   put('Save checksum',b+0x100a,(sum(block)&65535).to_bytes(2,'big'))
   p=8
   while p+12<=len(out):
    n=int.from_bytes(out[p:p+4],'big')
    if out[p+4:p+8]==b'apmd':
     crc=p+8+n;out[crc:crc+4]=(zlib.crc32(out[p+4:crc])&0xffffffff).to_bytes(4,'big');allowed.update(range(crc,crc+4));break
    p+=n+12
   else:raise ValueError('Missing apmd')
   if any(i not in allowed for i,(a,c)in enumerate(zip(result,out))if a!=c):raise ValueError('Unexpected bank edit')
   result=bytes(out);studio.ui.base.core.inspector.inspect(name,result)
 if not changes:raise ValueError('No hay cambios que guardar.')
 return result,changes
studio.edit=edit;studio.ui.edit=edit
TEXT={
 'bank':('Rupias del banco','Bank rupees','Rubis en banque'),
 'help':('El saldo del banco sobrevive a la Canción del Tiempo. No modifica las rupias de la cartera ni concede recompensas del banquero. Todo al máximo conserva este saldo. Edición pendiente de prueba física.','The bank balance survives Song of Time. Editing it does not change carried rupees or grant banker rewards. The maximum preset preserves this balance. Console validation is pending.','Le solde bancaire survit au Chant du Temps. Sa modification ne change pas les rubis portés et n’accorde pas les récompenses du banquier. Le réglage maximum conserve ce solde. Validation sur console en attente.'),
 'bankRange':('Banco: introduce un entero entre 0 y 5499.','Bank: enter an integer from 0 to 5499.','Banque : saisissez un entier de 0 à 5499.'),
 'bankProfile':('La edición del banco está habilitada para los perfiles PAL y USA investigados.','Bank editing is enabled for the researched PAL and USA profiles.','La modification bancaire est disponible pour les profils PAL et USA étudiés.'),
}
class App(studio.App):
 def bt(self,k):return TEXT[k][self.language]
 def error_text(self,e):return self.bt(str(e)) if str(e) in TEXT else super().error_text(e)
 def build(self):
  self.bankvar=None;super().build();self.root.title('Majora · Memory Studio 0.8')
  page=self.book.nametowidget(self.book.tabs()[0]);grid=next(w for w in page.winfo_children()if isinstance(w,ttk.Frame))
  row=grid.grid_size()[1]
  self.bankvar=tk.StringVar();self.vars['bankRupees']=self.bankvar
  ttk.Label(grid,text=self.bt('bank'),width=25).grid(row=row,column=0,sticky='w',pady=8)
  self.bankentry=ttk.Spinbox(grid,textvariable=self.bankvar,from_=0,to=5499,width=12);self.bankentry.grid(row=row,column=1,padx=15)
  ttk.Label(grid,text=self.bt('help'),wraplength=650,foreground='#c3a66a').grid(row=row+1,column=0,columnspan=3,sticky='w',pady=8)
  self.populate();self.update_preview()
 def populate(self):
  super().populate()
  if self.bankvar is None:return
  self.bankvar.set(str(self.extra.get('bankRupees',self.value(0xede,2))) if self.data is not None else '')
  enabled=self.data is not None and studio.songs.supported(self.report)
  self.bankentry.configure(state='normal' if enabled else 'disabled')
 def collect(self):
  extra,money,nuts=super().collect()
  if self.bankvar is not None and self.data is not None and studio.songs.supported(self.report):
   try:bank=int(self.bankvar.get())
   except ValueError:raise ValueError('bankRange')
   if bank!=self.value(0xede,2):extra['bankRupees']=bank
  return extra,money,nuts
 def describe(self,c):
  if c['campo']=='Bank rupees':return self.bt('bank'),str(int(c['antes'],16)),str(int(c['despues'],16))
  return super().describe(c)
 def maximum(self):
  bank=self.bankvar.get() if self.bankvar is not None else None
  super().maximum()
  if bank is not None:self.bankvar.set(bank);self.update_preview()
 def save(self):
  original=studio.ui.filedialog.asksaveasfilename
  def dialog(*args,**kwargs):
   if 'initialfile' in kwargs:kwargs['initialfile']=kwargs['initialfile'].replace('copy-v071','copy-v08')
   return original(*args,**kwargs)
  studio.ui.filedialog.asksaveasfilename=dialog
  try:super().save()
  finally:studio.ui.filedialog.asksaveasfilename=original

if __name__=='__main__':
 root=tk.Tk()
 if len(sys.argv)==4 and sys.argv[1]=='--self-test':
  root.withdraw();app=App(root)
  with zipfile.ZipFile(sys.argv[2])as z:name=next(n for n in z.namelist()if n.endswith('.png'));data=z.read(name)
  app.memories={name:data};app.choice.configure(values=[name]);app.choice.current(0);app.select();app.bankvar.set('5075');app.update_preview();assert app.valid
  e,money,nuts=app.collect();out,changes=edit(name,data,money,nuts,e)
  for language in range(3):app.extra=e;app.language=language;app.build();root.update_idletasks();assert app.bankvar.get()=='5075'
  Path(sys.argv[3]).write_text(json.dumps(dict(version='0.8',bank=5075,languages=3,changes=len(changes))));root.destroy()
 else:App(root);root.mainloop()
