from tkinter import messagebox
from math import sin, cos, sqrt, atan2, radians, trunc
import requests
import os
import time
import gpxpy
import xlrd
import json

import GasConfig
import GasLangs
_ = GasLangs.Translate

cached_gas_stations = []

def Run(parent):
	mode 		 		= GasConfig.Cfg["Default Mode"]
	max_straight_dist 	= GasConfig.Cfg["Default Max Distance"][mode] / (1 + GasConfig.Cfg["Distance Correction"]/100)
	fuel_type	 		= GasConfig.Cfg["Profiles"][GasConfig.Cfg["Default Profile"]][2]
	brands 		 		= GasConfig.Cfg["Filter Brands"].split(" ")
	result 		 		= {"data_rows":[], "station_count":0}
		
	""" initialize """
	if mode == "around_location":
		loc_lat = GasConfig.Cfg["Locations"][GasConfig.Cfg["Default Location"]][0]
		loc_lon = GasConfig.Cfg["Locations"][GasConfig.Cfg["Default Location"]][1]
	else:
		gpx_data = GetGPXInfo(GasConfig.Cfg["Default Route"])
		if gpx_data["status"] != "ok": return result
		""" To speed up processing, choose a point in file every dist_minimum """
		dist_minimum 	= GasConfig.Cfg["Default Max Distance"]["along_route"]/3 
		dist_accum   	= 0
		dist_zero   	= 0
		points_in 		= gpx_data["points"]
		num_points_in 	= len(points_in)
		points_out 		= [] 
		for p in range(0, num_points_in):
			if p == 0:
				points_in[0]["acc"] = 0
				points_out.append(points_in[0])
			else:
				dist = distance(points_in[p-1]["lat"], points_in[p-1]["lon"], points_in[p]["lat"], points_in[p]["lon"])
				dist_accum += dist
				dist_zero  += dist
				if dist_zero > dist_minimum:
					points_in[p]["acc"] = dist_accum
					points_out.append(points_in[p])
					dist_zero = 0
		points_in[num_points_in-1]["acc"] = dist_accum
		points_out.append(points_in[num_points_in-1])

	""" explore stations """
	stations = get_prices(GasConfig.Cfg["Default Source"], parent, force_download=False)
	if len(stations) == 0: return result
	result["station_count"] = len(stations)
	stc = 0
	for station in stations:
		stc += 1
		if stc % 100 == 0: parent.on_progress("Processing {}%...".format(trunc(100*stc/len(stations))))

		""" check profile's fuel type is available """
		if station["fuels"][fuel_type]["price"] == 0: continue

		""" check we are interested in station's brand """
		brand_ok = True
		if len(brands) > 0:
			brand_ok = False
			for brand in brands:
				if brand.upper() in station["brand"].upper(): 
					brand_ok = True
					break
		if not brand_ok: continue

		""" check max distance to reference """
		if mode == "around_location":
			dist = distance(loc_lat, loc_lon, station["lat"], station["lon"])
			if dist > max_straight_dist: continue
		else:
			station_ok = False
			for point in points_out:
				dist = distance(point["lat"], point["lon"], station["lat"], station["lon"])
				if dist < GasConfig.Cfg["Default Max Distance"]["along_route"]:
					station["distance_on_route"] = point["acc"]
					station_ok = True
					break
			if not station_ok: continue
		station["distance_to_reference"] = dist * (1 + GasConfig.Cfg["Distance Correction"]/100)
		
		(cost_total, cost_of_tank, cost_of_run, base_price, final_price) = CostOfRefill(station["id"])
		if final_price != base_price:
			price_info = "{:.3f} < {:.3f}".format(final_price/1000, base_price/1000)
		else:
			price_info = "{:.3f}".format(base_price/1000)
	
		if mode == "around_location":
			line = ["{:.2f}".format(station["distance_to_reference"]), "{:.2f}".format(cost_total), station["brand"], station["fuels"][fuel_type]["validon"], price_info, station["addr"]]
		else:
			line = ["{:.2f}".format(station["distance_to_reference"]), "{:.2f}".format(station["distance_on_route"]), "{:.2f}".format(cost_total), station["brand"], station["fuels"][fuel_type]["validon"], price_info, station["addr"]]
		result["data_rows"].append({"id":station["id"], "data":line})
		
	return result

def CostOfRefill(station_id):
	tank_capacity = GasConfig.Cfg["Profiles"][GasConfig.Cfg["Default Profile"]][0]
	consumption   = GasConfig.Cfg["Profiles"][GasConfig.Cfg["Default Profile"]][1]
	fuel_type	  = GasConfig.Cfg["Profiles"][GasConfig.Cfg["Default Profile"]][2]
	
	station     = GetDataOfStationId(station_id)
	base_price  = station["fuels"][fuel_type]["price"]
	final_price = base_price
	for brand, dinfo in GasConfig.Cfg["Discounts"].items():
		if brand.upper() in station["brand"].upper():
			final_price = final_price - base_price * dinfo[0]/100
	cost_of_tank = final_price/1000 * tank_capacity
	cost_of_run  = final_price/1000 * (2 * station["distance_to_reference"] * consumption/100)
	cost_total   = cost_of_tank + cost_of_run
	return (cost_total, cost_of_tank, cost_of_run, base_price, final_price)

def GetGPXInfo(filename, calculate_length=False):
	result = {"status":"ok", "waypoints":[], "points":[], "length":0}

	if not os.path.isfile(filename):
		result["status"] = _("GPX file does not exist.")
	else:
		try:
			gpx = gpxpy.parse(open(filename))
		except:
			result["status"] = _("Error parsing GPX file.")
	if result["status"] != "ok":
		messagebox.showerror(_("Error"), result["status"])
		return result
		
	if len(gpx.tracks) != 1:
		result["status"] = _("File must have one single track. {} found.").format(len(gpx.tracks))
		messagebox.showerror(_("Error"), result["status"])
	else:
		track = gpx.tracks[0]
		for segment in track.segments:
			for point in segment.points:
				result["points"].append({"lat":point.latitude, "lon":point.longitude})		
		for waypoint in gpx.waypoints:
			result["waypoints"].append({"name":waypoint.name, "lat":waypoint.latitude, "lon":waypoint.longitude})
			
	if calculate_length:
		accum = 0
		points = result["points"]
		for p in range(1, len(points)):
			accum += distance(points[p-1]["lat"], points[p-1]["lon"], points[p]["lat"], points[p]["lon"])
		result["length"] = accum
	return result
	
def AnalyzePrices(source_name, parent):
	stations = get_prices(source_name, parent, force_download=True)
	if len(stations) == 0: return ({}, 0)
	
	fuel_types = GasConfig.Sources[source_name]["fuel_types"]
	fuels = {}
	for fuel_type in fuel_types:
		fuels[fuel_type] = {"count":0, "sum":0, "max":0, "min":1000000}

	for station in stations:
		for fuel_type in fuel_types:
			price = station["fuels"][fuel_type]["price"]
			if price != 0:
				fuels[fuel_type]["count"] += 1
				fuels[fuel_type]["sum"]   += price
				if price > fuels[fuel_type]["max"]: fuels[fuel_type]["max"] = price
				if price < fuels[fuel_type]["min"]: fuels[fuel_type]["min"] = price

	return (fuels, len(stations))
	
def GetSourceFilename(source):
	return "GasSource {}.{}".format(source, GasConfig.Sources[source]["file_extension"])
	
def CheckInteger(n, msg, parent):
	try:
		n = int(n)
		return True
	except ValueError:
		messagebox.showerror(_("Error"), msg, parent=parent)
		return False
		
def GetDataOfStationId(idst):
	global cached_gas_stations
	for st in cached_gas_stations:
		if st["id"] == idst: 
			return st
	
def distance(latIni, lonIni, latEnd, lonEnd):
	lat0 = radians(latIni)
	lon0 = radians(lonIni)
	lat1 = radians(latEnd)
	lon1 = radians(lonEnd)
	dlon = lon1 - lon0
	dlat = lat1 - lat0
	a = sin(dlat/2)**2 + cos(lat0) * cos(lat1) * sin(dlon/2)**2
	c = 2 * atan2(sqrt(a), sqrt(1 - a))
	d = 6373.0 * c
	return d

def get_prices(source, parent, force_download):	
	global cached_gas_stations
	filename = GetSourceFilename(source)
	
	if os.path.exists(filename):
		oldness = (time.time() - os.path.getmtime(filename)) / 3600
	else:
		oldness = 0

	if GasConfig.Cfg["Default Prices Source"] == 0 or force_download:
		do_download = True
	else:
		do_download = False
		if os.path.exists(filename):
			if oldness >= GasConfig.Cfg["Max hours for Source"]:
				messagebox.showwarning(_("Warning"), _("New price data will be downloaded since current data is older than allowed in Setup."))
				do_download = True
		else:
			do_download = True
		
	if do_download:
		try:
			parent.on_progress(_("Downloading data..."))
			r = requests.get(GasConfig.Sources[source]["url"], allow_redirects=True, stream=True)
			if r.status_code == 200:
				with open(filename, "wb") as fd:
					k_ctr = 0
					for chunk in r.iter_content(chunk_size=1024):
						k_ctr += 1
						if k_ctr % 1000 == 0: parent.on_progress(_("Downloaded {} Kbytes...").format(k_ctr))
						fd.write(chunk)
			else:
				parent.on_progress(_("Status code {} on request. Check URL.").format(r.status_code))
				return []
		except:
			parent.on_progress(_("Can't access data source. Check URL."))
			return []

	if do_download or cached_gas_stations == []:
		parent.on_progress(_("Reading data..."))			
		source_func = globals()["price_source_"+source.replace(" ","_")]
		cached_gas_stations = source_func(filename, parent)

	return cached_gas_stations
			
""" 
-----------------------------------------------------------------------------------------
The following functions implement gas prices sources as specified in GasConfig.Sources.
Each function name starts with "price_source_" followed by the key in GasConfig.Sources.
The returned result is a list of dictionaries in which each element represents one
gas station. For each gas station, these are the keys:

	"lon", "lat"...: Location of station
	"addr".........: Address of station
	"fuels"........: Fuels on sale
	"brand"........: Station brand
	
"fuels" is a dictionary in which the keys are defined in 
GasConfig.Sources[]["fuel_types"]. For each key, ["price"] holds the
price (times 1000) and ["validon"] the date and time in which the price is valid.
-----------------------------------------------------------------------------------------
"""

def price_source_Gasolineras_ES(filename, parent):
	wb = xlrd.open_workbook(filename)
	datasheet = wb.sheet_by_index(0)
	
	result = []; pr = 4
	for r in range(4, datasheet.nrows):
		pr += 1
		if pr % 1000 == 0 and parent != None: parent.on_progress(_("Reading {}%...").format(trunc(100*pr/datasheet.nrows)))

		prov	 = datasheet.row(r)[0].value
		munic	 = datasheet.row(r)[1].value
		loc		 = datasheet.row(r)[2].value
		direcc	 = datasheet.row(r)[4].value
		addr     = direcc + ". " + loc
		if munic != loc: addr += ". " + munic
		if prov  != munic: addr += ". " + prov
		addr     += " [" + datasheet.row(r)[29].value + "]"
		
		lon 	 = datasheet.row(r)[6].value; lon = float(lon.replace(",","."))
		lat 	 = datasheet.row(r)[7].value; lat = float(lat.replace(",","."))
		validon  = datasheet.row(r)[8].value
		brand	 = datasheet.row(r)[26].value
		hours	 = datasheet.row(r)[17].value
		fuel_col = {"Gasolina 95 E5":9,  	"Gasolina 95 E10":10, 	"Gasolina 95 E5 Premium":11,
					"Gasolina 98 E5":12, 	"Gasolina 98 E10":13, 	"Gasóleo A":14,
					"Gasóleo Premium": 15, 	"Gasóleo B":16,		 	"Gasóleo C":17,
					"Biodiésel":20, 		"GLP":22,				"GNC":23, 
					"GNL":24 }
		fuels = {}
		for fuel in GasConfig.Sources["Gasolineras ES"]["fuel_types"]:
			fuels[fuel] = {}
			fuels[fuel]["validon"] = validon
			v = datasheet.row(r)[fuel_col[fuel]].value
			price = 0 if v == "" else trunc(1000*float(v.replace(",",".")))
			fuels[fuel]["price"] = price
		result.append({"id":str(pr-5),"lon":lon,"lat":lat,"addr":addr,"fuels":fuels,"brand":brand})
	return result

Combustivels_PT_error = {"reported":False, "detected":False, "log":""}
def price_source_Combustivels_PT(filename, parent):
		
	fuel_types = {}
	def collect_fuel_types(comb):
		return False
		fuel_types.setdefault(comb,0)
		fuel_types[comb] += 1
		return True
		
	def collect_error_info(ids, item):
		Combustivels_PT_error["detected"] = True
		Combustivels_PT_error["log"] += _("Found inconsistent {} for id={}.\n").format(item, ids)

	with open(filename, "r") as fh:
		lines = json.loads(fh.read())

	fuel_types_ok = GasConfig.Sources["Combustivels PT"]["fuel_types"]
		
	stations = {}; pr = 0
	for line in lines["resultado"]:
		pr += 1
		if pr % 1000 == 0 and parent != None: parent.on_progress(_("Reading {}%...").format(trunc(100*pr/(len(lines["resultado"])))))

		comb = line["Combustivel"]
		if collect_fuel_types(comb): continue
		if comb not in fuel_types_ok: continue
		
		idx   = line["Id"]
		addr  = line["Morada"] + ". " + line["Localidade"] + ". " + line["Municipio"] + (". " + line["Distrito"] if line["Distrito"] != line["Municipio"] else "")
		lat   = line["Latitude"]
		lon   = line["Longitude"]
		marca = line["Marca"]
		preco = line["Preco"]; price = trunc(1000*float(preco.split(" ")[0].replace(",",".")))
		data  = line["DataAtualizacao"]
		if not idx in stations:
			stations[idx] = {}
			stations[idx]["lon"]   = lon
			stations[idx]["lat"]   = lat
			stations[idx]["addr"]  = addr
			stations[idx]["brand"] = marca
			stations[idx]["fuels"] = {}
			for fuel_type in fuel_types_ok:
				stations[idx]["fuels"][fuel_type] = {}
				stations[idx]["fuels"][fuel_type]["price"] = 0
				stations[idx]["fuels"][fuel_type]["validon"] = ""
			stations[idx]["fuels"][comb]["price"] = price
			stations[idx]["fuels"][comb]["validon"] = data
		else:
			if lon   != stations[idx]["lon"]:   collect_error_info(idx, "lon")
			if lat   != stations[idx]["lat"]:   collect_error_info(idx, "lat")
			if addr  != stations[idx]["addr"]:  collect_error_info(idx, "addr")
			if marca != stations[idx]["brand"]: collect_error_info(idx, "brand")
			stations[idx]["fuels"][comb]["price"] = price
			stations[idx]["fuels"][comb]["validon"] = data
	
	if len(fuel_types) > 0:
		print("fuel_types", fuel_types)
		
	result = []
	for idx, data in stations.items():
		result.append({"id":idx,"lon":data["lon"],"lat":data["lat"],"addr":data["addr"],"fuels":data["fuels"],"brand":data["brand"]})
		
	if Combustivels_PT_error["detected"] and not Combustivels_PT_error["reported"]:
		fn = GetSourceFilename()+".errors"
		with open(fn, "w") as ofile:
			ofile.write(Combustivels_PT_error["log"])
		messagebox.showerror(_("Error in Combustivels_PT"), _("Errors detected, check file \"{}\"".format(fn)))
		Combustivels_PT_error["reported"] = True
			
	return result

