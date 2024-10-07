from tkinter import *
from tkinter import ttk

import GasConfig
import GasLangs
_ = GasLangs.Translate

class GasDlgTable(Toplevel):
	
	def __init__(self, parent, data, table_name):
		Toplevel.__init__(self, parent)
		self.parent      = parent
		self.table_name  = table_name
		self.num_columns = len(data["columns"])
		
		self.resizable(True,False)
		self.title(data["title"])
		self.protocol("WM_DELETE_WINDOW", self.on_close)
		self.geometry("+"+GasConfig.Cfg["Window Geometry"].get(self.table_name, GasConfig.Cfg["Default Window Position"]).split("+",1)[1])

		body = Frame(self); body.pack(side=TOP, padx=5, pady=5, expand=True, fill=BOTH)

		Label(body, text=data["text"]).pack(side=TOP, anchor=W, padx=2, pady=1)

		frame_table = Frame(body); frame_table.pack(side=TOP, anchor=W, expand=True, fill=BOTH, padx=5, pady=2)
		ctrl_vbar = ttk.Scrollbar(frame_table)
		self.ctrl_treev = ttk.Treeview(frame_table, show="headings", columns=list(x for x in range(self.num_columns)))
		self.ctrl_treev.configure(yscrollcommand=ctrl_vbar.set)
		ctrl_vbar.configure(command=self.ctrl_treev.yview) 
		ctrl_vbar.pack(side=RIGHT,fill=BOTH)
		self.ctrl_treev.pack(side=LEFT, expand=True, fill=BOTH) 

		for c, col in zip(list(x for x in range(self.num_columns)), data["columns"]):
			self.ctrl_treev.heading(c, text=col, anchor=W)
			cwidths = GasConfig.Cfg["Column Widths"].get(self.table_name, [])
			if len(cwidths) != 0:
				self.ctrl_treev.column(c, width=cwidths[c], anchor=W)
			else:
				self.ctrl_treev.column(c, width=90, anchor=W)
			
		for line in data["lines"]:
			self.ctrl_treev.insert("", END, values=line)

		frame_buttons = Frame(body); frame_buttons.pack(side=TOP, pady=2)
		Button(frame_buttons, text=_("Ok"), width=20, command=self.on_close).pack(side=LEFT, padx=5, pady=2)
		
		""" Set modal """
		self.transient(parent)
		self.grab_set()
		self.wait_window(self)
		
	def on_close(self):
		cws = []
		for i in range(self.num_columns): cws.append(self.ctrl_treev.column(i,"width"))

		GasConfig.Cfg["Column Widths"][self.table_name] = cws
		GasConfig.Cfg["Window Geometry"][self.table_name] = self.geometry()
		self.parent.focus_set()
		self.destroy()

