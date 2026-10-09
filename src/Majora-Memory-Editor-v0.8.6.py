"""Cycle reset UI: researched USA native confirmation dialog only."""
from pathlib import Path
import sys,importlib.util,json,zipfile
ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
def load(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=load('studio085','Majora-Memory-Editor-v0.8.5.py');reset=load('native_reset','Majora-cycle-reset.py');tk=old.tk;ttk=old.ttk
previous=old.edit
def edit(name,data,money,nuts,extra=None):
 extra=dict(extra or {});requested=extra.pop('cycleReset',False)
 if type(requested)!=bool:raise ValueError('resetState')
 if requested and extra.get('cycleAdvance'):raise ValueError('resetConflict')
 if requested:
  try:reset.locate(name,data)
  except ValueError:raise ValueError('resetState')
 try:result,changes=previous(name,data,money,nuts,extra)
 except ValueError as e:
  if str(e)!='No hay cambios que guardar.':raise
  result,changes=data,[]
 if requested:
  result,requests=reset.request(name,result)
  for c in requests:changes.append({'campo':'cycleReset' if c['field']=='msgMode NEW_CYCLE_0' else c['field'],'offset_png':c['png_offset'],'antes':c['before'],'despues':c['after']})
 if not changes:raise ValueError('No hay cambios que guardar.')
 return result,changes
old.edit=edit;old.old.studio.studio.ui.edit=edit
TEXT={
 'reset':('Volver al primer día · reinicio nativo','Return to day one · native cycle reset','Revenir au premier jour · cycle natif'),
 'warning':('Al cargar la copia, el juego guardará la partida y reiniciará el ciclo. Perderás los recursos y eventos temporales que elimina normalmente la Canción del Tiempo.','Loading the copy makes the game save and reset the cycle. Temporary resources and events normally removed by Song of Time will be lost.','Le chargement de la copie fera sauvegarder la partie et réinitialiser le cycle. Les ressources et événements temporaires normalement effacés par le Chant du Temps seront perdus.'),
 'ready':('Disponible: diálogo nativo USA 1.0 identificado. Regreso al día 1 probado en Analogue 3D.','Available: native USA 1.0 dialog identified. Return to day 1 tested on Analogue 3D.','Disponible : dialogue natif USA 1.0 identifié. Retour au jour 1 testé sur Analogue 3D.'),
 'required':('Para este reinicio, importa un Memory USA 1.0 capturado con la pregunta de la Canción del Tiempo visible, antes de aceptar. Todavía no está habilitado desde juego normal ni en PAL.','For this reset, import a USA 1.0 Memory captured with the Song of Time confirmation visible, before accepting. Normal gameplay and PAL are not enabled yet.','Pour ce retour, importer un Memory USA 1.0 capturé avec la confirmation du Chant du Temps visible, avant de répondre. Jeu normal et PAL pas encore activés.'),
 'resetState':('No se ha identificado el diálogo USA de reinicio y el estado de ocarina requerido.','The required USA reset dialog and ocarina state were not identified.','Le dialogue USA de retour et l’état d’ocarina requis ne sont pas identifiés.'),
 'resetConflict':('Selecciona avanzar o reiniciar, no ambas operaciones.','Choose advance or reset, not both operations.','Choisir avancer ou réinitialiser, pas les deux opérations.'),
 'day1':('Día 1 · mañana · guardado nativo','Day 1 · morning · native save','Jour 1 · matin · sauvegarde native')}
TEXT['readyPAL']=('Disponible: diálogo nativo PAL 1.1 identificado. Confirmación adaptada al idioma del juego; prueba física pendiente.','Available: native PAL 1.1 dialog identified. Confirmation follows game language; physical test pending.','Disponible : dialogue natif PAL 1.1 identifié. Confirmation adaptée à la langue du jeu ; test physique en attente.')
TEXT['required']=('Importa un Memory USA 1.0 o PAL 1.1 con la pregunta de la Canción del Tiempo visible, antes de aceptar. El reinicio desde juego normal no está habilitado.','Import a USA 1.0 or PAL 1.1 Memory with the Song of Time confirmation visible, before accepting. Reset from normal gameplay is not enabled.','Importer un Memory USA 1.0 ou PAL 1.1 avec la confirmation du Chant du Temps visible, avant de répondre. Retour depuis le jeu normal non activé.')
TEXT['resetState']=('No se ha identificado el diálogo de reinicio USA/PAL y su estado de ocarina requerido.','The required USA/PAL reset dialog and ocarina state were not identified.','Le dialogue USA/PAL de retour et l’état d’ocarina requis ne sont pas identifiés.')
class App(old.App):
 def rt(self,key):return TEXT[key][self.language]
 def build(self):
  self.resetvar=None;self.resetbutton=None;self.resetlabel=None;super().build();self.root.title('Majora · Memory Studio 0.8.6')
  page=self.book.nametowidget(self.book.tabs()[-1]);self.cycle_tree.configure(height=6);ttk.Separator(page).pack(fill='x',pady=8)
  self.resetvar=tk.BooleanVar(value=bool(self.extra.get('cycleReset',False)))
  self.resetbutton=ttk.Checkbutton(page,text=self.rt('reset'),variable=self.resetvar,command=self.choose_reset);self.resetbutton.pack(anchor='w')
  ttk.Label(page,text=self.rt('warning'),foreground='#c3a66a',wraplength=950).pack(anchor='w',pady=5)
  self.resetlabel=ttk.Label(page,wraplength=950);self.resetlabel.pack(anchor='w')
  self.advancebutton.configure(command=self.choose_advance)
  self.populate();self.update_preview()
 def populate(self):
  super().populate()
  if self.resetvar is None:return
  enabled=False
  if self.data:
   try:reset.locate(self.choice_name,self.data);enabled=True
   except ValueError:pass
  self.resetvar.set(bool(self.extra.get('cycleReset',False)))
  self.resetbutton.configure(state='normal' if enabled else 'disabled');self.resetlabel.configure(text=self.rt(('readyPAL' if self.report['detected_profile']['cartridge']=='NZSP' else 'ready') if enabled else 'required'))
 def choose_reset(self):
  if self.resetvar.get():self.advancevar.set(False)
  self.update_preview()
 def choose_advance(self):
  if self.advancevar.get():self.resetvar.set(False)
  self.update_preview()
 def collect(self):
  extra,money,nuts=super().collect()
  if self.resetvar is not None and self.resetvar.get():extra['cycleReset']=True
  return extra,money,nuts
 def error_text(self,e):return self.rt(str(e))if str(e)in TEXT else super().error_text(e)
 def describe(self,c):
  if c['campo']=='cycleReset':return self.rt('reset'),str(self.value(0x18,4))+' · '+old.old.clock(self.value(0xc,2)),self.rt('day1')
  if c['campo']in ('decodedTextLen','unk120D6','unk120D4'):return None
  return super().describe(c)
 def save(self):
  original=old.old.studio.studio.ui.filedialog.asksaveasfilename
  def dialog(*a,**kw):
   if 'initialfile'in kw:kw['initialfile']=kw['initialfile'].replace('copy-v071','copy-v086').replace('copy-v08.zip','copy-v086.zip').replace('copy-v081','copy-v086').replace('copy-v085','copy-v086')
   return original(*a,**kw)
  old.old.studio.studio.ui.filedialog.asksaveasfilename=dialog
  try:super().save()
  finally:old.old.studio.studio.ui.filedialog.asksaveasfilename=original
if __name__=='__main__':
 root=tk.Tk()
 if len(sys.argv)==4 and sys.argv[1]=='--self-test':
  root.withdraw();app=App(root)
  with zipfile.ZipFile(sys.argv[2])as z:name='despues.png';data=z.read(name)
  app.memories={name:data};app.choice.configure(values=[name]);app.choice.current(0);app.select();assert str(app.resetbutton.cget('state'))=='normal'
  app.resetvar.set(True);app.choose_reset();assert app.valid
  e,m,n=app.collect();edited,changes=edit(name,data,m,n,e)
  expected,_=reset.request(name,data);assert edited==expected
  for lang in range(3):app.extra=e;app.language=lang;app.build();root.update_idletasks();assert app.resetvar.get() and app.valid
  Path(sys.argv[3]).write_text(json.dumps({'version':'0.8.6','languages':3,'native_request_matches_tested_copy':True,'changes':len(changes)}));root.destroy()
 else:App(root);root.mainloop()
