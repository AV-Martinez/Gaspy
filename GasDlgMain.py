from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import os
import webbrowser

import GasConfig
import GasFuncs
import GasDlgSetup
import GasDlgTable
import GasDlgAbout
import GasLangs
_ = GasLangs.Translate

class GasDlgMain(Frame):
	
	def __init__(self, parent):
		super().__init__()
		self.parent = parent
		
		parent.title(_("Gas station finder"))
		parent.protocol("WM_DELETE_WINDOW", self.on_close)
		parent.geometry(GasConfig.Cfg["Window Geometry"].get("main", GasConfig.Cfg["Default Window Position"]))
		self.parent.iconphoto(False, PhotoImage(file="./Gas.png")) # icon from flaticon.com
		
		""" Menu composition """
		menubar = Menu(parent)
		parent.config(menu=menubar)
		menu_file = Menu(menubar, tearoff=0)
		menu_file.add_command(label=_("Setup")+"...", command=self.on_setup)
		menu_file.add_separator()
		menu_file.add_command(label=_("Exit"), command=self.on_close)
		menubar.add_cascade(label=_("File"), menu=menu_file)
		menu_help = Menu(menubar, tearoff=0)
		menu_help.add_command(label=_("Help")+"...", command=self.on_help)
		menu_help.add_separator()
		menu_help.add_command(label=_("About")+"...", command=self.on_about)
		menubar.add_cascade(label=_("Help"), menu=menu_help)

		""" Body composition """
		frame_body   = Frame(parent); frame_body.pack(fill=BOTH, expand=True)
		frame_mode 	 = LabelFrame(frame_body, text=_("Reference: ")); frame_mode.pack(side=TOP, anchor=W, expand=False, fill=X, padx=5, pady=5)
		frame_params = Frame(frame_body); frame_params.pack(side=TOP, anchor=W, expand=False, fill=X, padx=5, pady=5)
		Button(frame_body, text=_("Search"), command=self.on_calculate).pack(side=TOP, anchor=W, expand=False, fill=X, padx=5, pady=5)
		self.ctrl_progress = Label(frame_body); self.ctrl_progress.pack(side=TOP, anchor=W, padx=5)
		frame_table  = Frame(frame_body); frame_table.pack(side=TOP, anchor=W, expand=True, fill=BOTH, padx=5, pady=5)

		""" frame_mode composition """
		self.mode     = StringVar(frame_mode)
		self.location = StringVar(frame_mode)
		self.route	  = StringVar(frame_mode)
		ttk.Radiobutton(frame_mode, text=_("Around location: "), variable=self.mode, value="around_location", command=self.on_mode_changed).grid(row=0, column=0, sticky=W, padx=5)
		ttk.Radiobutton(frame_mode, text=_("Along route: "),  variable=self.mode, value="along_route", command=self.on_mode_changed).grid(row=1, column=0, sticky=W, padx=5)
		self.ctrl_location = ttk.Combobox(frame_mode, textvariable=self.location, values=list(GasConfig.Cfg["Locations"].keys()), state="readonly", width=40); self.ctrl_location.grid(row=0, column=1, sticky=W)
		frame_filespec = Frame(frame_mode); frame_filespec.grid(row=1, column=1, sticky=W)
		Entry(frame_filespec, textvariable=self.route, width=40).pack(side=LEFT)
		Button(frame_filespec, text=_("Choose..."), command=self.on_file_choose).pack(side=LEFT)
		self.ctrl_button_info = Button(frame_filespec, text=_("Info..."), command=self.on_file_info); self.ctrl_button_info.pack(side=LEFT)

		""" frame_params composition """
		self.distance 	   = StringVar(frame_params)
		self.profile  	   = StringVar(frame_params)
		self.refresh_data  = IntVar(frame_params)
		self.filter_brands = StringVar(frame_params)
		Label(frame_params, text=_("Max. distance to reference: ")).grid(row=0, column=0, sticky=W, pady=1)
		frame_dstframe = Frame(frame_params); frame_dstframe.grid(row=0, column=1, sticky=W, pady=1)
		Entry(frame_dstframe, textvariable=self.distance, width=5).pack(side=LEFT)
		Label(frame_dstframe, text=_(" Kms.")).pack(side=LEFT)
		Label(frame_params, text=_("Vehicle profile: ")).grid(row=1, column=0, sticky=W, pady=1)
		self.ctrl_profile = ttk.Combobox(frame_params, textvariable=self.profile, values=list(GasConfig.Cfg["Profiles"].keys()), state="readonly", width=40); self.ctrl_profile.grid(row=1, column=1, sticky=W, pady=1)
		Label(frame_params, text=_("Prices to use: ")).grid(row=2, column=0, sticky=W, pady=1)
		self.ctrl_data_source = ttk.Combobox(frame_params, values=[_("Get new data"), _("Use existing data")], state="readonly", width=40); self.ctrl_data_source.grid(row=2, column=1, sticky=W, pady=1)
		Label(frame_params, text=_("Show brands: ")).grid(row=3, column=0, sticky=W, pady=1)
		Entry(frame_params, textvariable=self.filter_brands).grid(row=3, column=1, sticky=W, pady=1)
		
		""" frame_table composition """
		ctrl_vbar = ttk.Scrollbar(frame_table)
		self.ctrl_treev = ttk.Treeview(frame_table, show="headings", selectmode="browse")
		self.ctrl_treev.configure(yscrollcommand=ctrl_vbar.set)
		ctrl_vbar.configure(command=self.ctrl_treev.yview) 
		ctrl_vbar.pack(side=RIGHT,fill=BOTH)
		self.ctrl_treev.pack(side=LEFT, expand=True, fill=BOTH) 
		self.ctrl_treev.bind("<ButtonRelease-3>", self.on_menu_result_popup)

		""" init controls """
		self.mode.set(GasConfig.Cfg["Default Mode"])
		self.location.set(GasConfig.Cfg["Default Location"])
		self.profile.set(GasConfig.Cfg["Default Profile"])
		self.ctrl_data_source.current(GasConfig.Cfg["Default Prices Source"])
		self.distance.set(GasConfig.Cfg["Default Max Distance"][self.mode.get()])
		self.filter_brands.set(GasConfig.Cfg["Filter Brands"])
		if os.path.isfile(GasConfig.Cfg["Default Route"]):
			self.ctrl_button_info.configure(state=NORMAL)
			self.route.set(GasConfig.Cfg["Default Route"])
		else:
			self.ctrl_button_info.configure(state=DISABLED)
			self.route.set(GasConfig.Cfg["Default Route"])
			GasConfig.Cfg["Default Route"] = ""
		self.set_result_columns()
			
	def set_result_columns(self):
		mode = self.mode.get()
		self.ctrl_treev["columns"] = ()
		self.ctrl_treev.configure(columns=list(x for x in range(len(GasConfig.ResultColumns[mode]))))
		cwidths = GasConfig.Cfg["Column Widths"].get(mode, [])
		for col in range(len(GasConfig.ResultColumns[mode])):
			if len(cwidths) != 0:
				self.ctrl_treev.column(col, width=cwidths[col], anchor=W)
			else:
				self.ctrl_treev.column(col, width=90, anchor=W)
			self.ctrl_treev.heading(col, text=GasConfig.ResultColumns[mode][col], anchor=W, command=lambda _col=col: self.on_sort_column(_col,False))
			
	def on_sort_column(self, col, reverse_mode):
		l = [(self.ctrl_treev.set(k,col),k) for k in self.ctrl_treev.get_children("")]
		try: # if the column is string, this will fail. If it's number, will work
			l.sort(reverse=reverse_mode, key=lambda x: float(x[0]))
		except:
			l.sort(reverse=reverse_mode)
		for index, (val, k) in enumerate(l):
			self.ctrl_treev.move(k, "", index)
		self.ctrl_treev.heading(col, command=lambda _col=col: self.on_sort_column(_col, not reverse_mode))
		self.ctrl_treev.selection_set(self.ctrl_treev.get_children()[0])

	def on_close(self):
		GasConfig.Cfg["Window Geometry"]["main"] = self.parent.geometry()
		self.save_defaults()
		self.parent.quit()
		
	def on_help(self):
		f = os.path.realpath("./GasHelp_{}.html".format(GasConfig.Cfg["Default Language"]))
		webbrowser.open("file://"+ f)
		
	def on_about(self):
		GasDlgAbout.GasDlgAbout(self)
		
	def on_mode_changed(self):
		self.distance.set(GasConfig.Cfg["Default Max Distance"][self.mode.get()])
		self.ctrl_treev.delete(*self.ctrl_treev.get_children())
		self.on_progress("")
		self.set_result_columns()
		
	def on_setup(self):
		previous_source   = GasConfig.Cfg["Default Source"]
		previous_language = GasConfig.Cfg["Default Language"]
		
		GasDlgSetup.GasDlgSetup(self.parent)
		
		if previous_source != GasConfig.Cfg["Default Source"]:
			csrc = GasConfig.Cfg["Default Source"]
			filename = GasFuncs.GetSourceFilename(csrc)
			if os.path.isfile(filename): os.remove(filename)
			messagebox.showwarning(_("Warning"), _("Data source has changed.")+"\n"+_("New data will be downloaded on next search."), parent=self)
		
		if previous_language != GasConfig.Cfg["Default Language"]:
			messagebox.showwarning(_("Warning"), _("Language has changed, restart is required."), parent=self)
			self.on_close()
		
		keys_loc  = list(GasConfig.Cfg["Locations"].keys())
		keys_prof = list(GasConfig.Cfg["Profiles"].keys())
		self.ctrl_location.configure(values=keys_loc)
		self.ctrl_profile.configure(values=keys_prof)
		if self.location.get() not in GasConfig.Cfg["Locations"]: self.location.set(keys_loc[0])
		if self.profile.get()  not in GasConfig.Cfg["Profiles"]:  self.profile.set(keys_prof[0])
			
	def on_calculate(self):
		if not GasFuncs.CheckInteger(self.distance.get(), _("Bad max. distance value."), self): return
		GasConfig.Cfg["Filter Brands"] = self.filter_brands.get().strip()

		self.save_defaults()
		self.ctrl_treev.delete(*self.ctrl_treev.get_children())
		result = GasFuncs.Run(self)
		for row in result["data_rows"]:
			self.ctrl_treev.insert("", END, values=row["data"], iid=row["id"])
		if len(result["data_rows"]) != 0:
			self.on_progress(_("{} stations found (out of {}):").format(len(result["data_rows"]), result["station_count"]))
			self.ctrl_treev.selection_set(self.ctrl_treev.get_children()[0])
		else:
			self.on_progress(_("No stations found (out of {})").format(result["station_count"]))
			
	def on_menu_result_popup(self, event):
		if len(self.ctrl_treev.get_children()) == 0: return
		menu = Menu(tearoff=0)
		menu.add_command(label=_("Cost breakdown")+"...", command=lambda: self.on_menu_action("Breakdown"))
		menu.add_command(label=_("Show on map")+"...", command=lambda: self.on_menu_action("Show"))
		if self.mode.get() == "around_location":
			menu.add_command(label=_("Directions")+"...", command=lambda: self.on_menu_action("Directions"))
		menu.tk_popup(event.x_root, event.y_root, 0)
		
	def on_menu_action(self, action):
		station = GasFuncs.GetDataOfStationId(self.ctrl_treev.selection()[0])
		if action == "Breakdown":
			info = {}
			info["title"] = _("Cost breakdown information")
			(cost_total, cost_of_tank, cost_of_run, base_price, final_price) = GasFuncs.CostOfRefill(self.ctrl_treev.selection()[0])
			if final_price != base_price:
				info["text"] = _("Initial price is {:.3f} €/L, after discounts it's {:.3f} €/L:").format(base_price/1000, final_price/1000)
			else:
				info["text"] = _("Fuel price is {:.3f} €/L:").format(base_price/1000)
			info["columns"] = [_("Item"), _("Value")]
			info["lines"]   = []
			info["lines"].append([_("To and from station (2x{:.2f} kms):").format(station["distance_to_reference"]), "{:.2f} €".format(cost_of_run)])
			info["lines"].append([_("Tank refill:"), "{:.2f} €".format(cost_of_tank)])
			info["lines"].append([_("Total cost:"), "{:.2f} €".format(cost_of_run + cost_of_tank)])
			GasDlgTable.GasDlgTable(self, info, "table_cost")
		elif action == "Show":
			url = "https://www.google.com/maps/search/?api=1&query={},{}".format(station["lat"], station["lon"])
			webbrowser.open(url)
		elif action == "Directions":
			loc = GasConfig.Cfg["Locations"][GasConfig.Cfg["Default Location"]]
			url = "https://www.google.com/maps/dir/?api=1&travelmode=driving&origin={},{}&destination={},{}".format(loc[0], loc[1], station["lat"], station["lon"])
			webbrowser.open(url)

	def on_file_choose(self):
		f = filedialog.askopenfilename(title=_("Select gpx file"), initialdir=".", filetypes=((_("GPX files"), "*.gpx"),))
		if f != "":	
			self.route.set(f)
			self.mode.set("along_route")
			self.ctrl_button_info.configure(state = NORMAL)
			self.on_mode_changed()
			
	def on_file_info(self):
		data = GasFuncs.GetGPXInfo(self.route.get(), True)
		if data["status"] != "ok": return
		
		info = {}
		info["title"]   = _("GPX file information")
		info["text"]    = _("{} points along {:.2f} Kms.:").format(len(data["points"]), data["length"])
		info["columns"] = [_("Waypoint"), _("Latitude"), _("Longitude")]
		info["lines"]   = []
		for waypoint in data["waypoints"]:
			info["lines"].append([waypoint["name"], waypoint["lat"], waypoint["lon"]])
		GasDlgTable.GasDlgTable(self, info, "table_gpx")
		
	def on_progress(self, msg):
		self.ctrl_progress.configure(text=msg)
		self.update_idletasks()
		
	def save_defaults(self):
		cws = []
		for i in range(len(GasConfig.ResultColumns[self.mode.get()])): cws.append(self.ctrl_treev.column(i,"width"))
			
		GasConfig.Cfg["Column Widths"][self.mode.get()] 		= cws
		GasConfig.Cfg["Default Mode"] 							= self.mode.get()
		GasConfig.Cfg["Default Location"]  						= self.location.get()
		GasConfig.Cfg["Default Route"]							= self.route.get()
		GasConfig.Cfg["Default Profile"]						= self.profile.get()
		GasConfig.Cfg["Default Prices Source"]					= self.ctrl_data_source.current()
		GasConfig.Cfg["Default Max Distance"][self.mode.get()] 	= int(self.distance.get())
		GasConfig.Cfg["Filter Brands"]							= self.filter_brands.get()
		GasConfig.Save()
