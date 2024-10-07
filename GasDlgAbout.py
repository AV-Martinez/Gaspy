from tkinter import *
from tkinter import ttk

import GasConfig
import GasLangs
_ = GasLangs.Translate

class GasDlgAbout(Toplevel):
	
	def __init__(self, parent):
		Toplevel.__init__(self, parent)
		self.parent      = parent
		
		self.resizable(False,False)
		self.title(_("About"))
		self.protocol("WM_DELETE_WINDOW", self.on_close)
		self.geometry("+"+GasConfig.Cfg["Window Geometry"].get("about", GasConfig.Cfg["Default Window Position"]).split("+",1)[1])

		body = Frame(self); body.pack(side=TOP, padx=5, pady=5, expand=True, fill=BOTH)
		
		self.image = PhotoImage(file="./Gas.png")
		self.image = self.image.subsample(10)
		Label(body, image=self.image).pack(side=TOP, anchor=CENTER, pady=10)
		Label(body, text="Gaspy", font="Helvetica 16 bold").pack(side=TOP, anchor=CENTER, pady=5)
		Label(body, text=_("A gas station finder")).pack(side=TOP, anchor=CENTER, pady=5)
		Label(body, text="(c) 2024 avmn").pack(side=TOP, anchor=CENTER, pady=5)
		Label(body, text=_("Licensed under the GNU General Public License")).pack(side=TOP, anchor=CENTER, pady=5)
		Button(body, text=_("Ok"), width=10, command=self.on_close).pack(side=TOP, anchor=CENTER, pady=5)
		
		""" Set modal """
		self.transient(parent)
		self.grab_set()
		self.wait_window(self)
		
	def on_close(self):
		GasConfig.Cfg["Window Geometry"]["about"] = self.geometry()
		self.parent.focus_set()
		self.destroy()

