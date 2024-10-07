import pickle
import os

config_file 	= "./Gas.pickle"
config_defaults	= {	 	
					"Default Mode": 	 		"around_location", 							# "around_location" or "along_route"
					"Default Max Distance": 	{"around_location":10, "along_route":2},	# max distance from station to reference (location or route)
					"Default Prices Source":	1, 											# index on ["Get new data", "Use existing data"] 
					"Default Route":			"",											# gpx file for route
					"Default Language":			"es",										# language
					"Default Source":			"Gasolineras ES",							# index on Sources
					"Max hours for Source":		6,											# Maximum oldness for source file
					"Default Location":  		"Default",									# name of default location spec
					"Default Profile":	 		"Default",									# name of default profile spec
					"Filter Brands":			"",											# these brands are the only shown in result list
					"Distance Correction":		40,											# Percentage to increase straight-line distances to obtain road distances
					"Locations": 		 		{"Default": [40.416691, -3.703791]},  		# available locations
					"Profiles":			 		{"Default": [50, 6.5, "Gasolina 95 E5"]},	# available profiles
					"Discounts":				{},											# available discounts
					"Window Geometry":	 		{},											# windows' sizes and positions
					"Column Widths":			{},											# column widths for tree view control
				  }

if not os.path.isfile(config_file):
	with open(config_file, "wb") as f:
		pickle.dump(config_defaults, f, pickle.HIGHEST_PROTOCOL)				 

with open(config_file, "rb") as f:
	Cfg = pickle.load(f)

import GasFuncs
import GasLangs
_ = GasLangs.Translate

""" Manage translation of "Default" locations and profiles """
for entity in ["Location", "Profile"]:
	value  = Cfg["Default {}".format(entity)]
	values = Cfg["{}s".format(entity)]
	if Cfg["Default Language"] != "en":
		if value == "Default" and value in values: 
			values[_("Default")] = values.pop("Default")
			Cfg["Default {}".format(entity)] = _("Default")
	else:
		for lang, translation in GasLangs.Translations("Default").items():
			if translation in values: 
				values["Default"] = values.pop(translation)
				Cfg["Default {}".format(entity)] = "Default"
				break

ResultColumns 	= {"around_location": [_("Distance (Kms)"),_("Cost (€)"),_("Brand"),_("Updated"),_("Price (€/L)"),_("Address")],
				   "along_route":     [_("Distance (Kms)"),_("Route point (Kms)"),_("Cost (€)"),_("Brand"),_("Updated"),_("Price (€/L)"),_("Address")]}
Languages 	  	= {"en": _("English"), "es": _("Spanish")}
Entities		= {"Location": [	[_("Latitude"), 	_("Lat"),   "float", 	"º", 			_("degrees")],
									[_("Longitude"), 	_("Lon"),   "float", 	"º", 			_("degrees")] ],
				   "Profile":  [ 	[_("Tank capacity"),_("Tank"),  "int",   	_("L"), 		_("liters")],
									[_("Consumption"), 	_("Cons"),  "float", 	_("L/100Kms"), 	_("liters per 100 Kms")],
									[_("Fuel type"),	_("Fuel"),  [], 		"",				"" ] ],
				   "Discount": [ 	[_("Percentage"),	_("Pct"),  "float", "%", "%"] ] }
Sources	  	  	= {"Gasolineras ES": 	{"fuel_types":["Gasolina 95 E5","Gasolina 95 E5 Premium","Gasolina 98 E5","Gasóleo A","Gasóleo Premium","Gasóleo B","GLP","GNC"], "url":"https://geoportalgasolineras.es/resources/files/preciosEESS_es.xls", "file_extension":"xls"},
				   "Combustivels PT":	{"fuel_types":["Gasóleo colorido","Gasóleo simples","Gasóleo especial","Gasolina simples 95","Gasolina especial 95","Gasolina 98","Gasolina especial 98","GPL Auto","Biodiesel B15"], "url":"https://precoscombustiveis.dgeg.gov.pt/api/PrecoComb/PesquisarPostos?idsTiposComb=&idMarca=&idTipoPosto=&idDistrito=&idsMunicipios=&qtdPorPagina=", "file_extension":"json"} }

def Save():
	with open(config_file, "wb") as f:
		pickle.dump(Cfg, f, pickle.HIGHEST_PROTOCOL)		
		
