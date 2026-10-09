"""Regression tests using local Memories; reconstructed JP fixture is explicitly labelled."""
from pathlib import Path
import importlib.util,sys,zipfile,hashlib,json
ROOT=Path(__file__).resolve().parents[1];OUTPUT=ROOT/'src'
s=importlib.util.spec_from_file_location('ui122',OUTPUT/'Majora-Memory-Editor-v1.2.2.py');ui=importlib.util.module_from_spec(s);s.loader.exec_module(ui)
if len(sys.argv)!=5:raise SystemExit('Usage: python tests/test_ui.py USA.zip PAL11.zip PAL10.zip JP11.zip')
cases=[(region,Path(path),False) for region,path in zip(['USA','PAL1','PAL0','JP1'],sys.argv[1:])]
results=[]
def output(app):
 if app.regional_panel:
  p=app.regional_panel;money,nuts,extra=p.collect();return app.regional_backend.edit(p.name,p.data,money,nuts,extra)[0]
 extra,money,nuts=app.collect();return ui.edit(app.choice_name,app.data,money,nuts,extra)[0]
for region,path,reconstructed in cases:
 before_hash=hashlib.sha256(path.read_bytes()).hexdigest();root=ui.tk.Tk();root.withdraw();app=ui.App(root);app.source=path;app.source_hash=before_hash
 with zipfile.ZipFile(path) as z:name=next(n for n in z.namelist() if n.endswith('.png'));data=z.read(name)
 app.memories={name:data};app.choice.configure(values=[name]);app.choice.current(0);app.select()
 if app.regional_panel:
  p=app.regional_panel;p.vars['bank'].set('123');p.vars['health'].set('19.75');p.vars['healthCapacity'].set('20');p.vars['playerName'].set('Alex');labels=p.limit_labels
 else:
  app.vars['rupees'].set('49');app.vars['healthCapacity'].set('20');app.vars['health'].set('19.75');labels=app.limit_labels
 expected=output(app)
 for lang in range(4):
  app.lang.current(lang);app.change_language();root.update_idletasks()
  assert output(app)==expected,(region,lang,'language switch changed output')
  assert not any(isinstance(w,ui.tk.Toplevel) for w in root.winfo_children()),'Second window'
  book=app.regional_panel.book if app.regional_panel else app.book
  assert len(book.nav.winfo_children())==len(book.tabs()),'Missing navigation entry'
 # Loading twice must replace the panel, rather than accumulating windows/frames.
 app.select();root.update_idletasks()
 assert not any(isinstance(w,ui.tk.Toplevel) for w in root.winfo_children())
 if app.regional_panel:
  p=app.regional_panel;assert float(p.vars['healthCapacity'].get())==p.value(0x34,2)/16
  p.vars['health'].set('3.01')
  try:p.collect()
  except ValueError:pass
  else:raise AssertionError('Silently rounded health')
  p.vars['health'].set('not finished');app.tick() # An unfinished field must not break the refresh loop.
 else:
  app.upvars['wallet'].current(0);app.upvars['quiver'].current(1);app.refresh_limits()
  assert '99' in app.limit_labels['rupees'].cget('text') and '500' in app.limit_labels['rupees'].cget('text')
  assert '30' in app.limit_labels['arrows'].cget('text') and '50' in app.limit_labels['arrows'].cget('text')
 assert hashlib.sha256(path.read_bytes()).hexdigest()==before_hash,'Original modified'
 results.append({'region':region,'fixture':str(path),'reconstructed_fixture':reconstructed,'one_window':True,'languages_preserve_output':4,'navigation_complete':True,'original_unchanged':True})
 root.destroy()
(ROOT/'test-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8');print('PASS: four profiles; four languages; byte-identical output across languages; originals preserved')
