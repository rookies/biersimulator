#!/usr/bin/python2
# -*- coding: utf-8 -*-
import gtk

class Biersimulator (object):
	#################
	### DATENBANK ###
	#################
	hefe_ug = [
		# Name, Tmin, Tmax, EVG, t, T, Sed., Bier
		('Fermentis SafLager W34/70',	9,	15,	78,	16,	9,	'sehr gut',	'sehr klar'),
		('Fermentis SafLager S-23',		12,	15,	80,	7,	16,	'gut',		'recht klar')
	]
	hefe_og = [
		# Name, Tmin, Tmax, EVG, t, T, Sed., Bier
		('Fermentis SafAle S-04',		15,	24,	80,	3,	23,	'sehr gut',	'extrem klar'),
		('Fermentis SafBrew S-33',		15,	24,	63,	1,	23,	'gut',		'klar'),
		('Fermentis SafBrew T-58',		15,	24,	79,	3,	23,	'gut',		'klar'),
		('Fermentis SafAle US-05',		15,	24,	79,	3,	23,	'mäßig',	'relativ trüb'),
		('Danstar Nottingham',			14,	21,	79,	3,	23,	'sehr gut',	'sehr klar'),
		('Danstar Windsor',				14,	21,	67,	2,	23,	'mäßig',	'relativ trüb'),
		('Brewferm Top',				18,	25,	69,	3,	22,	'gut',		'klar'),
		('Muttons Premium Gold',		17,	21,	73,	6,	21,	'sehr gut',	'sehr klar')
	]
	malze = [
		# Name, Farbe, max. Anteil
		('Pilsener',	  3.5,	100),
		('Pale Ale',	  6.5,	100),
		('Wiener',		  8.0,	100),
		('Münchner',	 18.5,	 85),
		('Carahell',	 25.0,	 30),
		('Melanoidin',	 70.0,	 20),
		('Rauch',		  4.5,	100)
	]
	hopfen_bitter = [
		# Name, Land, alpha-Gehalt, Aroma
		('Magnum',			'DE',	13.5,	[]),
		('Northern Brewer',	'DE',	 8.0,	[]),
		('Nugget',			'USA',	11.0,	[]),
		('Taurus',			'DE',	13.5,	[])
	]
	hopfen_aroma = [
		# Name, Land, alpha-Gehalt, Aroma
		('Spalter Select',	'DE',	 4.75,	['würzig', 'blumig'])
	]
	rezepte = [
		{
			'typ': 'Mild Ale',
			'name': 'Fuffzich',
			'maischen': {
				'schuettung': [
					(0.129, 'Wiener'),
					(0.042, 'Münchner'),
					(0.013, 'Carahell'),
					(0.013, 'Melanoidin'),
					(0.013, 'Rauch')
				],
				'hg': 0.625,
				'ein': 60,
				'rasten': [
					('eiweiss', 57, 10),
					('maltose', 63, 35),
					('zucker', 73, 20)
				],
				'ab': 78,
			},
			'laeutern': {
				'ruhe': 30,
				'ng': 0.75,
				'ng_t': 78
			},
			'kochen': {
				'dauer': 90,
				'hopfen': [
					('Spalter Select', 1.292, -1),
					('Magnum', 0.292, 70),
					('Spalter Select', 1.208, 10)
				]
			},
			'gaeren': {
				'hefe': (1, 'Danstar Nottingham'),
				'evg': 77,
				'temperatur': 21,
				'druck': 2.1
			},
			'lagern': {
				'temperatur': 10,
				'dauer': 7
			}
		}
	]
	#################
	### VARIABLEN ###
	#################
	builder = None
	ausbeute = 0
	ausschlagmenge = 0
	model_rezepte = None
	model_schuettung = None
	model_rasten = None
	model_hopfengaben = None
	model_malze = None
	model_hopfen = None
	model_hefe = None
	rezept = {}
	##################
	### FUNKTIONEN ###
	##################
	def __init__ (self):
		# GUI laden:
		self.builder = gtk.Builder()
		self.builder.add_from_file("gui.glade")
		self.builder.connect_signals(self)
		# Rezept-Liste füllen:
		self.model_rezepte = gtk.ListStore(str)
		self.obj("combobox1").set_model(self.model_rezepte)
		cell = gtk.CellRendererText()
		self.obj("combobox1").pack_start(cell, True)
		self.obj("combobox1").add_attribute(cell, 'text', 0)
		for r in self.rezepte:
			self.obj("combobox1").append_text('%s "%s"' % (r['typ'], r['name']))
		self.obj("combobox1").set_active(0)
		# Schüttungs-Treeview initialisieren:
		menge = gtk.TreeViewColumn("Menge in kg", gtk.CellRendererText(), text=0)
		typ = gtk.TreeViewColumn("Typ", gtk.CellRendererText(), text=1)
		farbe = gtk.TreeViewColumn("Farbe in EBC", gtk.CellRendererText(), text=2)
		self.builder.get_object("treeview2").append_column(menge)
		self.builder.get_object("treeview2").append_column(typ)
		self.builder.get_object("treeview2").append_column(farbe)
		self.model_schuettung = gtk.ListStore(str, str, str)
		self.builder.get_object("treeview2").set_model(self.model_schuettung)
		# Rasten-Treeview initialisieren:
		temp = gtk.TreeViewColumn("Temperatur in °C", gtk.CellRendererText(), text=0)
		typ = gtk.TreeViewColumn("Typ", gtk.CellRendererText(), text=1)
		dauer = gtk.TreeViewColumn("Dauer in Minuten", gtk.CellRendererText(), text=2)
		self.builder.get_object("treeview3").append_column(temp)
		self.builder.get_object("treeview3").append_column(typ)
		self.builder.get_object("treeview3").append_column(dauer)
		self.model_rasten = gtk.ListStore(str, str, str)
		self.builder.get_object("treeview3").set_model(self.model_rasten)
		# Hopfengaben-Treeview initialisieren:
		menge = gtk.TreeViewColumn("Menge in g", gtk.CellRendererText(), text=0)
		typ = gtk.TreeViewColumn("Typ", gtk.CellRendererText(), text=1)
		kochdauer = gtk.TreeViewColumn("Kochdauer in Minuten", gtk.CellRendererText(), text=2)
		self.builder.get_object("treeview4").append_column(menge)
		self.builder.get_object("treeview4").append_column(typ)
		self.builder.get_object("treeview4").append_column(kochdauer)
		self.model_hopfengaben = gtk.ListStore(str, str, str)
		self.builder.get_object("treeview4").set_model(self.model_hopfengaben)
		# Malz-Treeview initialisieren:
		name = gtk.TreeViewColumn("Name", gtk.CellRendererText(), text=0)
		farbe = gtk.TreeViewColumn("Farbe in EBC", gtk.CellRendererText(), text=1)
		anteil = gtk.TreeViewColumn("max. Anteil in %", gtk.CellRendererText(), text=2)
		self.builder.get_object("treeview1").append_column(name)
		self.builder.get_object("treeview1").append_column(farbe)
		self.builder.get_object("treeview1").append_column(anteil)
		self.model_malze = gtk.ListStore(str, str, str)
		self.builder.get_object("treeview1").set_model(self.model_malze)
		for item in self.malze:
			self.model_malze.append([item[0], "%.1f" % (item[1]), "%d" % (item[2])])
		# Hopfen-Treeview initialisieren:
		art = gtk.TreeViewColumn("Art", gtk.CellRendererText(), text=0)
		name = gtk.TreeViewColumn("Name", gtk.CellRendererText(), text=1)
		land = gtk.TreeViewColumn("Land", gtk.CellRendererText(), text=2)
		gehalt = gtk.TreeViewColumn("Bitterstoffgehalt in %", gtk.CellRendererText(), text=3)
		aroma = gtk.TreeViewColumn("Aroma", gtk.CellRendererText(), text=4)
		self.builder.get_object("treeview5").append_column(art)
		self.builder.get_object("treeview5").append_column(name)
		self.builder.get_object("treeview5").append_column(land)
		self.builder.get_object("treeview5").append_column(gehalt)
		self.builder.get_object("treeview5").append_column(aroma)
		self.model_hopfen = gtk.ListStore(str, str, str, str, str)
		self.builder.get_object("treeview5").set_model(self.model_hopfen)
		for item in self.hopfen_bitter:
			self.model_hopfen.append(['Bitter', item[0], item[1], "%.2f" % (item[2]), ", ".join(item[3])])
		for item in self.hopfen_aroma:
			self.model_hopfen.append(['Aroma', item[0], item[1], "%.2f" % (item[2]), ", ".join(item[3])])
		# Hefe-Liste füllen:
		self.model_hefe = gtk.ListStore(str)
		self.obj("combobox2").set_model(self.model_hefe)
		cell = gtk.CellRendererText()
		self.obj("combobox2").pack_start(cell, True)
		self.obj("combobox2").add_attribute(cell, 'text', 0)
		for item in self.hefe_ug:
			self.obj("combobox2").append_text('%s (UG)' % (item[0]))
		for item in self.hefe_og:
			self.obj("combobox2").append_text('%s (OG)' % (item[0]))
		self.obj("combobox2").set_active(0)
		# window1 anzeigen:
		self.obj("window1").show()
	
	def __del__ (self):
		pass
	def run (self):
		try:
			gtk.main()
		except KeyboardInterrupt:
			pass
	def obj (self, name):
		return self.builder.get_object(name)
	def quit(self):
		gtk.main_quit()
	def restart(self):
		self.obj("window1").show()
		self.obj("window2").hide()
	def show_msg(self, text1, text2, t=gtk.MESSAGE_INFO, parent="window2"):
		dlg = gtk.MessageDialog(
			parent=self.obj(parent),
			buttons=gtk.BUTTONS_OK,
			type=t,
			message_format=text1
		)
		dlg.format_secondary_text(text2)
		dlg.run()
		dlg.destroy()
	def start_simulator(self):
		# Sudhausausbeute einlesen:
		try:
			self.ausbeute = int(self.obj("entry1").get_text())
		except ValueError:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Sudhausausbeute darf nur ganze Zahlen enthalten.", gtk.MESSAGE_WARNING, "window1")
			return
		if self.ausbeute < 1 or self.ausbeute > 100:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Sudhausausbeute muss zwischen 1 und 100 liegen.", gtk.MESSAGE_WARNING, "window1")
			return
		# Biermenge einlesen:
		try:
			self.ausschlagmenge = float(self.obj("entry17").get_text())
		except ValueError:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Biermenge darf nur Zahlen enthalten.", gtk.MESSAGE_WARNING, "window1")
			return
		if self.ausschlagmenge < 1 or self.ausschlagmenge > 10000:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Biermenge muss zwischen 1 und 10.000 liegen.", gtk.MESSAGE_WARNING, "window1")
			return
		# Fenster wechseln:
		self.obj("window1").hide()
		self.obj("window2").show()
		self.obj("window2").maximize()
	def set_fields(self):
		# Schroten & Maischen:
		self.fill_model_schuettung()
		self.obj("entry2").set_text("%.2f" % (self.ausschlagmenge*self.rezept['maischen']['hg']))
		self.obj("entry3").set_text("%d" % self.rezept['maischen']['ein'])
		self.fill_model_rasten()
		self.obj("entry10").set_text("%d" % self.rezept['maischen']['ab'])
		# Läutern:
		self.obj("entry4").set_text("%d" % self.rezept['laeutern']['ruhe'])
		self.obj("entry5").set_text("%.2f" % (self.ausschlagmenge*self.rezept['laeutern']['ng']))
		self.obj("entry6").set_text("%d" % self.rezept['laeutern']['ng_t'])
		# Kochen:
		self.obj("entry7").set_text("%d" % self.rezept['kochen']['dauer'])
		self.fill_model_hopfengaben()
		# Gären:
		if self.rezept['gaeren']['hefe'][0] is 0:
			# UG
			i = 0
			for item in self.hefe_ug:
				if item[0] == self.rezept['gaeren']['hefe'][1]:
					break
				else:
					i += 1
		else:
			# OG
			i = len(self.hefe_ug)
			for item in self.hefe_og:
				if item[0] == self.rezept['gaeren']['hefe'][1]:
					break
				else:
					i += 1
		self.obj("combobox2").set_active(i)
		self.obj("entry11").set_text("%d" % self.rezept['gaeren']['evg'])
		self.obj("entry9").set_text("%d" % self.rezept['gaeren']['temperatur'])
		self.obj("entry12").set_text("%.2f" % self.rezept['gaeren']['druck'])
		# Lagern:
		self.obj("entry13").set_text("%d" % self.rezept['lagern']['temperatur'])
		self.obj("entry14").set_text("%d" % self.rezept['lagern']['dauer'])
		# Abfüllen:
		# adjustments (abfuellen)
	def get_fields(self):
		# Schroten & Maischen:
		self.rezept['maischen']['hg'] = float(self.obj("entry2").get_text())/self.ausschlagmenge
		self.rezept['maischen']['ein'] = int(self.obj("entry3").get_text())
		self.rezept['maischen']['ab'] = int(self.obj("entry10").get_text())
		# Läutern:
		self.rezept['laeutern']['ruhe'] = int(self.obj("entry4").get_text())
		self.rezept['laeutern']['ng'] = float(self.obj("entry5").get_text())/self.ausschlagmenge
		self.rezept['laeutern']['ng_t'] = int(self.obj("entry6").get_text())
		# Kochen:
		self.rezept['kochen']['dauer'] = int(self.obj("entry7").get_text())
		# Gären:
		i = self.obj("combobox2").get_active()
		if i < len(self.hefe_ug):
			# UG
			self.rezept['gaeren']['hefe'] = (0, self.hefe_ug[i][0])
		else:
			# OG
			self.rezept['gaeren']['hefe'] = (1, self.hefe_og[i-len(self.hefe_ug)][0])
		self.rezept['gaeren']['evg'] = int(self.obj("entry11").get_text())
		self.rezept['gaeren']['temperatur'] = int(self.obj("entry9").get_text())
		self.rezept['gaeren']['druck'] = float(self.obj("entry12").get_text())
		# Lagern:
		self.rezept['lagern']['temperatur'] = int(self.obj("entry13").get_text())
		self.rezept['lagern']['dauer'] = int(self.obj("entry14").get_text())
		# Abfüllen:
		# adjustments (abfuellen)
	def fill_model_schuettung(self):
		self.model_schuettung.clear()
		for item in self.rezept['maischen']['schuettung']:
			self.model_schuettung.append(["%.3f" % (item[0]*self.ausschlagmenge), item[1], "%.1f" % (self.malzinfo_from_name(item[1])[1])])
	def fill_model_rasten(self):
		self.model_rasten.clear()
		for item in self.rezept['maischen']['rasten']:
			if item[0] == 'glucanase':
				typ = 'Glucanaserast'
			elif item[0] == 'ferula':
				typ = 'Ferulasäurerast'
			elif item[0] == 'eiweiss':
				typ = 'Eiweißrast'
			elif item[0] == 'maltose':
				typ = 'Maltoserast'
			elif item[0] == 'zucker':
				typ = 'Verzuckerungsrast'
			else:
				typ = 'eigene Rast'
			self.model_rasten.append(["%d" % (item[1]), typ, "%d" % (item[2])])
	def fill_model_hopfengaben(self):
		self.model_hopfengaben.clear()
		for item in self.rezept['kochen']['hopfen']:
			if item[2] is -1:
				dauer = 'Vorderwürze'
			elif item[2] is -2:
				dauer = 'Whirlpool'
			else:
				dauer = "%d" % (item[2])
			self.model_hopfengaben.append(["%.3f" % (item[1]*self.ausschlagmenge), item[0], dauer])
	def malzinfo_from_name(self, name):
		for item in self.malze:
			if item[0] == name:
				return item
		return None
	###############
	### window1 ### (Rezept auswählen)
	###############
	def on_window1_delete_event(self, *args):
		self.quit()
		return False
	# Button Hilfe
	def on_button1_clicked(self, widget, *args):
		self.obj("messagedialog1").show()
	# Button Start fertiges Rezept
	def on_button2_clicked(self, widget, *args):
		self.rezept = self.rezepte[self.obj("combobox1").get_active()]
		self.start_simulator()
		self.set_fields()
	# Button Start eigenes Rezept
	def on_button4_clicked(self, widget, *args):
		self.rezept = {
			'typ': '',
			'name': '',
			'maischen': {
				'schuettung': [],
				'hg': 0,
				'ein': 0,
				'rasten': [],
				'ab': 0,
			},
			'laeutern': {
				'ruhe': 0,
				'ng': 0,
				'ng_t': 0
			},
			'kochen': {
				'dauer': 0,
				'hopfen': []
			},
			'gaeren': {
				'hefe': (0, ''),
				'evg': 0,
				'temperatur': 0,
				'druck': 0
			},
			'lagern': {
				'temperatur': 0,
				'dauer': 0
			}
		}
		self.start_simulator()
		self.set_fields()
	######################
	### messagedialog1 ### (Hilfe Sudhausausbeute)
	######################
	def on_messagedialog1_delete_event(self, *args):
		self.obj("messagedialog1").hide()
		return True
	# Button OK
	def on_button10_clicked(self, widget, *args):
		self.obj("messagedialog1").hide()
	###############
	### window2 ### (Hauptfenster)
	###############
	def on_window2_delete_event(self, *args):
		self.restart()
		return True
	# Button Malz hinzufügen
	def on_button3_clicked(self, widget, *args):
		self.obj("window5").show()
	# Button Malz entfernen
	def on_button5_clicked(self, widget, *args):
		pass
	# Button Rast hinzufügen
	def on_button6_clicked(self, widget, *args):
		self.obj("window4").show()
	# Button Rast entfernen
	def on_button7_clicked(self, widget, *args):
		pass
	# Button Hopfen hinzufügen
	def on_button8_clicked(self, widget, *args):
		self.obj("window6").show()
	# Button Hopfen entfernen
	def on_button9_clicked(self, widget, *args):
		pass
	# Button Brauprozess abschließen
	def on_button13_clicked(self, widget, *args):
		# Daten einlesen:
		self.get_fields()
		# Stammwürze berechnen:
		# Farbe berechnen:
		# Bitterkeit berechnen:
		# Alkoholgehalt berechnen:
		# CO2-Gehalt berechnen:
		co2 = (self.rezept['gaeren']['druck']+1)*(0.0015461*(self.rezept['gaeren']['temperatur']**2) + 0.10711*self.rezept['gaeren']['temperatur'] + 3.1962)
		self.obj("label60").set_text("%.2f" % co2)
		# Biertyp berechnen:
		# Ergebnis-Fenster anzeigen:
		self.obj("window3").show()
		print(self.rezept)
	###############
	### window3 ###
	###############
	def on_window3_delete_event(self, *args):
		self.obj("window3").hide()
		return True
	###############
	### window4 ### (Rast hinzufügen)
	###############
	def on_window4_delete_event(self, *args):
		self.obj("window4").hide()
		return True
	###############
	### window5 ### (Malz hinzufügen)
	###############
	def on_window5_delete_event(self, *args):
		self.obj("window5").hide()
		return True
	###############
	### window6 ### (Hopfen hinzufügen)
	###############
	def on_window6_delete_event(self, *args):
		self.obj("window6").hide()
		return True
if __name__ == '__main__':
	bs = Biersimulator()
	bs.run()
