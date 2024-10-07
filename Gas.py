from tkinter import *
from tkinter import ttk

import GasConfig
import GasDlgMain

# Dependencies:
# pip install gpxpy -- gpx file management 	https://pypi.org/project/gpxpy/
# pip install xlrd  -- read .xls files 		https://xlrd.readthedocs.io/en/latest/

if __name__ == "__main__":
	root = Tk()
	GasConfig.Cfg["Default Window Position"] = "+{}+{}".format(int(root.winfo_screenwidth()/4), int(root.winfo_screenheight()/4))
	GasDlgMain.GasDlgMain(root)
	root.mainloop()

