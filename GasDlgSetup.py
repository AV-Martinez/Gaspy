from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from math import trunc

import GasConfig
import GasFuncs
import GasDlgTable
import GasLangs
_ = GasLangs.Translate

class ProgressText(Toplevel):
	
	def __init__(self, parent, source):
		Toplevel.__init__(self, parent)
		self.parent = parent
		self.resizable(False,False)
		
		self.title(source)
		pgeom = parent.geometry()
		pgeom_w = int(pgeom.split("x")[0])
		pgeom_h = int(pgeom.split("x")[1].split("+")[0])
		pgeom_x = int(pgeom.split("+")[1])
		pgeom_y = int(pgeom.split("+")[2])
		self.geometry("+{}+{}".format(trunc(pgeom_x+pgeom_w/2), trunc(pgeom_y+pgeom_h/2)))
		body = Frame(self); body.pack(padx=5, pady=5, expand=True, fill=BOTH)
		Label(body, text=_("Getting gas stations information")).pack(side=TOP, anchor=CENTER)
		self.ctrl_msg = Label(body); self.ctrl_msg.pack(side=TOP, anchor=CENTER)
		
	def on_progress(self, text):
		self.ctrl_msg.configure(text=text)
		self.update_idletasks()
		
class EntryDialog(Toplevel):
	
	def __init__(self, parent, mode, entity, instance):
		Toplevel.__init__(self, parent)
		self.parent   = parent
		self.mode     = mode
		self.entity   = entity
		self.instance = instance
		
		self.resizable(False,False)
		self.title(_(mode) + " " + _(entity))
		self.protocol("WM_DELETE_WINDOW", self.on_close)
		self.geometry("+"+GasConfig.Cfg["Window Geometry"].get("entry", GasConfig.Cfg["Default Window Position"]).split("+",1)[1])

		body = Frame(self); body.pack(padx=5, pady=5, expand=True, fill=BOTH)
		frame_fields  = Frame(body); frame_fields.pack(side=TOP, anchor=W, expand=True, padx=2, pady=2)
		frame_buttons = Frame(body); frame_buttons.pack(side=TOP, padx=2, pady=2)
		
		self.values = []
		for i in range(0,len(GasConfig.Entities[entity])+1): 
			self.values.append(StringVar(body))
		
		Label(frame_fields, text=_("Name:")).grid(row=0, column=0, sticky=E, padx=2, pady=1)
		e = Entry(frame_fields, textvariable=self.values[0]); e.grid(row=0, column=1, stick=W, padx=2, pady=1); e.focus_set()
		ix = 1
		for fieldspec in GasConfig.Entities[entity]:
			Label(frame_fields, text=fieldspec[0]+":").grid(row=ix, column=0, sticky=E, padx=2, pady=1)
			frame_val = Frame(frame_fields); frame_val.grid(row=ix, column=1, sticky=W, pady=1)
			if isinstance(fieldspec[2], str):
				Entry(frame_val, textvariable=self.values[ix]).pack(side=LEFT)
			elif isinstance(fieldspec[2], list):
				ttk.Combobox(frame_val, textvariable=self.values[ix], values=fieldspec[2], state="readonly").pack(side=LEFT)
				if mode == "New": self.values[ix].set(fieldspec[2][0])
			Label(frame_val, text=fieldspec[4]+" ").pack(side=LEFT, padx=2)
			ix += 1
		Button(frame_buttons, text=_("Ok"), width=20, command=self.on_ok).pack(side=LEFT, padx=5, pady=2)
		Button(frame_buttons, text=_("Cancel"), width=20, command=self.on_close).pack(side=LEFT, padx=5, pady=2)
		
		self.bind("<Return>", self.on_ok)
		self.Ok = False

		if mode == "Edit":
			self.values[0].set(instance)
			data = GasConfig.Cfg[entity+"s"][instance]
			ix = 1
			for datum in data:
				self.values[ix].set(datum)
				ix += 1
		
		""" Set modal """
		self.transient(parent)
		self.grab_set()
		self.wait_window(self)
		
	def on_ok(self, event=None):
		delete_previous_instance = False
		if self.mode == "New":
			(ok, item) = self.check_value(self.values[0].get().strip(), "entityname")
			if not ok: return
		elif self.mode == "Edit":
			if self.instance != self.values[0].get().strip():
				(ok, item) = self.check_value(self.values[0].get().strip(), "entityname")
				if not ok: return
				delete_previous_instance = True
			else:
				item = self.values[0].get().strip()
		data = []
		for i in range(1, len(GasConfig.Entities[self.entity])+1):
			(ok, value) = self.check_value(self.values[i].get().strip(), GasConfig.Entities[self.entity][i-1][2])
			if not ok: return
			data.append(value)
		GasConfig.Cfg[self.entity+"s"][item] = data
		if delete_previous_instance: GasConfig.Cfg[self.entity+"s"].pop(self.instance, None)
		self.Ok = True
		self.on_close()

	def on_close(self):
		GasConfig.Cfg["Window Geometry"]["entry"] = self.geometry()
		GasConfig.Save()
		self.parent.focus_set()
		self.destroy()

	def check_value(self, value, typeof):
		if value == "": 
			messagebox.showerror(_("Error"), _("Field can't be empty."), parent=self)
			return (False, value)
		if isinstance(typeof, list):
			return (True, value)
		elif typeof == "entityname":
			if any(x in value for x in "("): 
				messagebox.showerror(_("Error"), _("Can't use character \"(\" in name."), parent=self)
				return (False, value)
			if value in GasConfig.Cfg[self.entity+"s"]:
				messagebox.showerror(_("Error"), _("Name already exists."), parent=self)
				return (False, value)
			return (True, value)
		else:
			try:
				if typeof == "int":
					n = int(value)
				elif typeof == "float":
					n = float(value)
				return (True, n)
			except ValueError:
				messagebox.showerror(_("Error"), _("Bad number format."), parent=self)
				return (False, value)
		
class Chooser(Frame):

	def __init__(self, parent, entity):
		Frame.__init__(self, parent)
		self.entity = entity
		self.parent = parent
		
		frame_body = Label(self); frame_body.pack(expand=True, fill=X)
		self.list = Listbox(frame_body, height=5); self.list.pack(side=LEFT, expand=True, fill=X)
		frame_buttons = Frame(frame_body); frame_buttons.pack(side=LEFT)
		self.list.bind("<Button-3>", self.on_rightclick)

		self.load_items()
		
	def load_items(self):
		self.list.delete(0, END)
		items_list = []
		items = GasConfig.Cfg["{}s".format(self.entity)]
		for item, vals in items.items():
			specs = GasConfig.Entities[self.entity]
			line = ""
			for ix in range(0,len(vals)):
				line += specs[ix][1]+":"+str(vals[ix])+specs[ix][3]+" "
			items_list.append(item +  " (" + line[:-1] + ")")
		self.list.insert(0, *items_list)
		self.list.select_set(0)
		
	def on_rightclick(self, event):
		cs = len(self.list.curselection())
		menu = Menu(tearoff=0)
		menu.add_command(label=_("New")+"...", command=self.on_new, state="normal")
		menu.add_command(label=_("Edit")+"...", command=self.on_edit, state="normal" if cs != 0 else "disabled")
		menu.add_command(label=_("Delete")+"...", command=self.on_delete, state="normal" if cs != 0 else "disabled")
		menu.tk_popup(event.x_root, event.y_root, 0)
		
	def on_new(self):
		clicked = EntryDialog(self.parent, "New", self.entity, "")
		if clicked.Ok: self.load_items()
		
	def on_edit(self):
		selection = self.list.get(self.list.curselection()[0])
		key = selection.split("(")[0].strip()
		clicked = EntryDialog(self.parent, "Edit", self.entity, key)
		if clicked.Ok: self.load_items()
		
	def on_delete(self):
		if self.entity != "Discount" and self.list.index(END) == 1: 
			messagebox.showerror(_("Error"), _("Can't delete last item in list."), parent=self)
			return
		selection = self.list.get(self.list.curselection()[0])
		key = selection.split("(")[0].strip()
		GasConfig.Cfg[self.entity+"s"].pop(key)
		GasConfig.Save()
		self.load_items()
			
class GasDlgSetup(Toplevel):
	
	def __init__(self, parent):
		Toplevel.__init__(self, parent)
		self.parent = parent
		
		self.resizable(False,False)
		self.title(_("Setup"))
		self.protocol("WM_DELETE_WINDOW", self.on_close)
		self.geometry("+"+GasConfig.Cfg["Window Geometry"].get("setup", GasConfig.Cfg["Default Window Position"]).split("+",1)[1])

		body = Frame(self); body.pack(side=TOP, padx=5, pady=5, expand=True, fill=BOTH)
		
		ctrl_notebook = ttk.Notebook(body); ctrl_notebook.pack(expand=True, fill=BOTH)
		for entity, fields in GasConfig.Entities.items():
			ctrl_notebook.add(Chooser(ctrl_notebook, entity), text=" "+_("{}s".format(entity))+" ")
			
		frame_params = Frame(body); frame_params.pack(side=TOP, anchor=W, pady=(6,2))
		self.language = StringVar(frame_params)
		self.data_source = StringVar(frame_params)
		Label(frame_params, text=_("Language: ")).grid(row=0, column=0, sticky=E, padx=2, pady=1)
		ttk.Combobox(frame_params, textvariable=self.language, values=list(GasConfig.Languages.values()), state="readonly").grid(row=0, column=1, padx = 2, pady=1, sticky=W)
		Label(frame_params, text=_("Prices to use: ")).grid(row=1, column=0, sticky=E, padx=2, pady=1)
		
		frame_gassrc = Frame(frame_params); frame_gassrc.grid(row=1, column=1, padx=2, pady=1, sticky=W)
		self.ctrl_sources = ttk.Combobox(frame_gassrc, textvariable=self.data_source, values=list(GasConfig.Sources.keys()), state="readonly"); self.ctrl_sources.pack(side=LEFT)
		Button(frame_gassrc, text=_("Available fuel types")+"...", command=self.on_available_fuel_types).pack(side=LEFT)
		self.language.set(GasConfig.Languages[GasConfig.Cfg["Default Language"]])
		self.data_source.set(GasConfig.Cfg["Default Source"])
		
		Label(frame_params, text=_("Max. oldness in price data: ")).grid(row=2, column=0, padx=2, pady=1, sticky=E)
		frame_maxo = Frame(frame_params); frame_maxo.grid(row=2, column=1, padx=2, pady=1, sticky=W)
		self.max_oldness = StringVar(frame_params)
		Entry(frame_maxo, width=3, textvariable=self.max_oldness).pack(side=LEFT)
		Label(frame_maxo, text=_("hours")).pack(side=LEFT)
		self.max_oldness.set(GasConfig.Cfg["Max hours for Source"])
		
		Label(frame_params, text=_("Distance correction: ")).grid(row=3, column=0, padx=2, pady=1, sticky=E)
		frame_dstc = Frame(frame_params); frame_dstc.grid(row=3, column=1, padx=2, pady=1, sticky=W)
		self.distance_correction = StringVar(frame_params)
		Entry(frame_dstc, width=3, textvariable=self.distance_correction).pack(side=LEFT)
		Label(frame_dstc, text=_("% increment over straight line value")).pack(side=LEFT)
		self.distance_correction.set(GasConfig.Cfg["Distance Correction"])

		self.ctrl_sources.bind('<<ComboboxSelected>>', self.set_fuel_types_domain)
		self.set_fuel_types_domain()

		frame_buttons = Frame(body); frame_buttons.pack(side=TOP, pady=2)
		Button(frame_buttons, text=_("Ok"), width=20, command=self.on_ok).pack(side=LEFT, padx=5, pady=2)
		Button(frame_buttons, text=_("Cancel"), width=20, command=self.on_close).pack(side=LEFT, padx=5, pady=2)

		""" Set modal """
		self.transient(parent)
		self.grab_set()
		self.wait_window(self)
		
	def set_fuel_types_domain(self, event=None): 
		""" Set domain for the Profile's fuel type combobox. Warn on inconsistencies """
		fuel_types = GasConfig.Sources[self.data_source.get()]["fuel_types"]
		GasConfig.Entities["Profile"][2][2] = fuel_types
		
		errors = []
		for profile_name, data in GasConfig.Cfg["Profiles"].items():
			fuel_type = data[2]
			if fuel_type not in fuel_types:
				errors.append(profile_name)
		if len(errors) > 0:
			if len(errors) == 1:
				msg = _("Profile \"{}\" specifies a fuel type which is not supported in the current price source (\"{}\")").format(errors[0], self.data_source.get())
			else:
				msg = _("Profiles {} specify a fuel type which is not supported in the current price source (\"{}\")").format(errors, self.data_source.get())
			messagebox.showerror(_("Error"), msg, parent=self)
		return len(errors)
		
	def on_available_fuel_types(self):
		progress_dlg = ProgressText(self, self.data_source.get())
		(fuels, num_stations) = GasFuncs.AnalyzePrices(self.data_source.get(), progress_dlg)
		progress_dlg.destroy()
		if num_stations == 0: 
			messagebox.showerror(_("Error"), _("There has been an error processing the source. No data is available."), parent=self)
			return
		info = {}
		info["title"]   = _("Available fuel types")
		info["text"]    = _("{} stations in source data:").format(num_stations)
		info["columns"] = [_("Fuel"), _("Availability (%)"), _("Maximum (€/L)"), _("Minimum (€/L)"), _("Average (€/L)")]
		info["lines"]   = []
		for fuel, finfo in fuels.items():
			info["lines"].append([fuel, int(100*finfo["count"]/num_stations), finfo["max"]/1000, finfo["min"]/1000, "{:.3f}".format(finfo["sum"]/1000/finfo["count"])])
		GasDlgTable.GasDlgTable(self, info, "table_fuels")
		
	def on_ok(self):
		if self.set_fuel_types_domain() > 0: return
		if not GasFuncs.CheckInteger(self.max_oldness.get(), _("Bad max. oldness value."), self): return
		if not GasFuncs.CheckInteger(self.distance_correction.get(), _("Bad distance correction percentage."), self): return
		GasConfig.Cfg["Default Language"] 	  = [k for k in GasConfig.Languages if GasConfig.Languages[k]==self.language.get()][0]
		GasConfig.Cfg["Default Source"] 	  = self.data_source.get()
		GasConfig.Cfg["Max hours for Source"] = int(self.max_oldness.get())
		GasConfig.Cfg["Distance Correction"]  = int(self.distance_correction.get())
		self.on_close()

	def on_close(self):
		GasConfig.Cfg["Window Geometry"]["setup"] = self.geometry()
		GasConfig.Save()
		self.parent.focus_set()
		self.destroy()

