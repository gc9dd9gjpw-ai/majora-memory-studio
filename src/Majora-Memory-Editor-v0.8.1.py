"""Cycle inspector. Arbitrary day/time writes are intentionally not implemented."""
from pathlib import Path
import sys,importlib.util,json,zipfile
ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
spec=importlib.util.spec_from_file_location('studio08',ROOT/'Majora-Memory-Editor-v0.8.py');studio=importlib.util.module_from_spec(spec);spec.loader.exec_module(studio)
tk=studio.tk;ttk=studio.ttk
def clock(raw):
 minutes=raw*1440//65536
 return f'{minutes//60:02d}:{minutes%60:02d}'
def remaining(day,raw):
 if day not in (1,2,3):return None
 return max(0,((4-day)*65536-((raw-16384)&65535))*1440//65536)
TEXT={
 'cycle':('Ciclo','Cycle','Cycle'),
 'help':('Datos leídos del Memory. El ciclo comienza a las 06:00; pasar por medianoche no cambia el número de día.','Values read from the Memory. A cycle day starts at 06:00; crossing midnight does not change the day number.','Données lues dans le Memory. Une journée du cycle commence à 06:00 ; passer minuit ne change pas le numéro du jour.'),
 'pending':('Lectura verificada por estructura. Edición de día/hora pendiente de localizar y validar la transición nativa y sus estados vivos.','Structurally verified reading. Day/time editing awaits native-transition and live-state research.','Lecture vérifiée par structure. La modification du jour et de l’heure attend l’étude de la transition native et des états actifs.'),
 'day':('Día del ciclo','Cycle day','Jour du cycle'),
 'time':('Hora interna (24 h)','Internal time (24 h)','Heure interne (24 h)'),
 'night':('Indicador de noche almacenado','Stored night flag','Indicateur de nuit enregistré'),
 'event':('Contador temporal eventDayCount','Temporary eventDayCount','Compteur temporaire eventDayCount'),
 'speed':('Ajuste temporal timeSpeedOffset','Time-speed offset','Décalage de vitesse du temps'),
 'moon':('Tiempo del juego hasta la caída de la Luna','Game time until moon crash','Temps du jeu avant la chute de la Lune'),
 'transition':('0 · transición de inicio del ciclo','0 · cycle-start transition','0 · transition de début du cycle'),
 'unknown':('No aplicable / pendiente','Not applicable / pending','Non applicable / en attente'),
 'field':('Campo','Field','Champ'),
 'value':('Valor','Value','Valeur'),
 'offset':('Offset relativo Save','Relative Save offset','Offset relatif Save'),
}
class App(studio.App):
 def ct(self,k):return TEXT[k][self.language]
 def build(self):
  self.cycle_tree=None;super().build();self.root.title('Majora · Memory Studio 0.8.1')
  page=ttk.Frame(self.book,padding=16);self.book.add(page,text=self.ct('cycle'))
  ttk.Label(page,text=self.ct('help'),wraplength=950).pack(anchor='w',pady=(0,15))
  frame=ttk.Frame(page);frame.pack(fill='both',expand=True)
  self.cycle_tree=self.make_tree(frame,[('field',self.ct('field'),430),('value',self.ct('value'),290),('offset',self.ct('offset'),160)])
  ttk.Label(page,text=self.ct('pending'),wraplength=950,foreground='#c3a66a').pack(anchor='w',pady=12)
  self.populate()
 def populate(self):
  super().populate()
  if self.cycle_tree is None:return
  self.cycle_tree.delete(*self.cycle_tree.get_children())
  if self.data is None:return
  day=self.value(0x18,4);raw=self.value(0xc,2);speed=self.value(0x14,4)
  if speed&0x80000000:speed-=0x100000000
  minutes=remaining(day,raw);moon=self.ct('unknown') if minutes is None else f'{minutes//60} h {minutes%60:02d} min'
  rows=[('day',self.ct('transition') if day==0 else str(day),'+0x18 / s32'),('time',clock(raw)+f' / 0x{raw:04X}','+0x0C / u16'),('night',self.value(0x10,4),'+0x10 / s32'),('event',self.value(0x1c,4),'+0x1C / s32'),('speed',speed,'+0x14 / s32'),('moon',moon,'Derivado / derived')]
  for key,value,offset in rows:self.cycle_tree.insert('','end',values=(self.ct(key),value,offset))
 def save(self):
  original=studio.studio.ui.filedialog.asksaveasfilename
  def dialog(*args,**kwargs):
   if 'initialfile' in kwargs:kwargs['initialfile']=kwargs['initialfile'].replace('copy-v071','copy-v081').replace('copy-v08.zip','copy-v081.zip')
   return original(*args,**kwargs)
  studio.studio.ui.filedialog.asksaveasfilename=dialog
  try:super().save()
  finally:studio.studio.ui.filedialog.asksaveasfilename=original
if __name__=='__main__':
 root=tk.Tk()
 if len(sys.argv)==4 and sys.argv[1]=='--self-test':
  root.withdraw();app=App(root)
  with zipfile.ZipFile(sys.argv[2])as z:name=next(n for n in z.namelist()if n.endswith('.png'));data=z.read(name)
  app.memories={name:data};app.choice.configure(values=[name]);app.choice.current(0);app.select()
  for language in range(3):app.language=language;app.build();root.update_idletasks();assert len(app.cycle_tree.get_children())==6
  Path(sys.argv[3]).write_text(json.dumps(dict(version='0.8.1',languages=3,cycle_rows=6,day=app.value(0x18,4),time=clock(app.value(0xc,2)),cycle_editing=False)));root.destroy()
 else:App(root);root.mainloop()
