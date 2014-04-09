#!/usr/bin/python2
# -*- coding: utf-8 -*-
import gtk, math, copy

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
			'stammwuerze': 13,
			'maischen': {
				'schuettung': [
					(0.62, 'Wiener'),
					(0.2, 'Münchner'),
					(0.06, 'Carahell'),
					(0.06, 'Melanoidin'),
					(0.06, 'Rauch')
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
	schuettung = 0
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
		menge = gtk.TreeViewColumn("Anteil in %", gtk.CellRendererText(), text=0)
		typ = gtk.TreeViewColumn("Typ", gtk.CellRendererText(), text=1)
		farbe = gtk.TreeViewColumn("Farbe in EBC", gtk.CellRendererText(), text=2)
		self.obj("treeview2").append_column(menge)
		self.obj("treeview2").append_column(typ)
		self.obj("treeview2").append_column(farbe)
		self.model_schuettung = gtk.ListStore(str, str, str)
		self.obj("treeview2").set_model(self.model_schuettung)
		self.obj("treeview2").get_selection().connect("changed", self.on_treeview_selection2_changed)
		# Rasten-Treeview initialisieren:
		temp = gtk.TreeViewColumn("Temperatur in °C", gtk.CellRendererText(), text=0)
		typ = gtk.TreeViewColumn("Typ", gtk.CellRendererText(), text=1)
		dauer = gtk.TreeViewColumn("Dauer in Minuten", gtk.CellRendererText(), text=2)
		self.obj("treeview3").append_column(temp)
		self.obj("treeview3").append_column(typ)
		self.obj("treeview3").append_column(dauer)
		self.model_rasten = gtk.ListStore(str, str, str)
		self.obj("treeview3").set_model(self.model_rasten)
		self.obj("treeview3").get_selection().connect("changed", self.on_treeview_selection3_changed)
		# Hopfengaben-Treeview initialisieren:
		menge = gtk.TreeViewColumn("Menge in g", gtk.CellRendererText(), text=0)
		typ = gtk.TreeViewColumn("Typ", gtk.CellRendererText(), text=1)
		kochdauer = gtk.TreeViewColumn("Kochdauer in Minuten", gtk.CellRendererText(), text=2)
		self.obj("treeview4").append_column(menge)
		self.obj("treeview4").append_column(typ)
		self.obj("treeview4").append_column(kochdauer)
		self.model_hopfengaben = gtk.ListStore(str, str, str)
		self.obj("treeview4").set_model(self.model_hopfengaben)
		self.obj("treeview4").get_selection().connect("changed", self.on_treeview_selection4_changed)
		# Malz-Treeview initialisieren:
		name = gtk.TreeViewColumn("Name", gtk.CellRendererText(), text=0)
		farbe = gtk.TreeViewColumn("Farbe in EBC", gtk.CellRendererText(), text=1)
		anteil = gtk.TreeViewColumn("max. Anteil in %", gtk.CellRendererText(), text=2)
		self.obj("treeview1").append_column(name)
		self.obj("treeview1").append_column(farbe)
		self.obj("treeview1").append_column(anteil)
		self.model_malze = gtk.ListStore(str, str, str)
		self.obj("treeview1").set_model(self.model_malze)
		for item in self.malze:
			self.model_malze.append([item[0], "%.1f" % (item[1]), "%d" % (item[2])])
		# Hopfen-Treeview initialisieren:
		art = gtk.TreeViewColumn("Art", gtk.CellRendererText(), text=0)
		name = gtk.TreeViewColumn("Name", gtk.CellRendererText(), text=1)
		land = gtk.TreeViewColumn("Land", gtk.CellRendererText(), text=2)
		gehalt = gtk.TreeViewColumn("Bitterstoffgehalt in %", gtk.CellRendererText(), text=3)
		aroma = gtk.TreeViewColumn("Aroma", gtk.CellRendererText(), text=4)
		self.obj("treeview5").append_column(art)
		self.obj("treeview5").append_column(name)
		self.obj("treeview5").append_column(land)
		self.obj("treeview5").append_column(gehalt)
		self.obj("treeview5").append_column(aroma)
		self.model_hopfen = gtk.ListStore(str, str, str, str, str)
		self.obj("treeview5").set_model(self.model_hopfen)
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
		# image2 anzeigen:
		self.set_image2(0)
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
		# Schüttungsmenge berechnen:
		self.schuettung = (self.masspercent_to_af(self.rezept['stammwuerze'])*self.ausschlagmenge)/self.ausbeute
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
		self.obj("entry9").set_text("%d" % self.rezept['gaeren']['temperatur'])
		self.obj("entry12").set_text("%.2f" % self.rezept['gaeren']['druck'])
		# Lagern:
		self.obj("entry13").set_text("%d" % self.rezept['lagern']['temperatur'])
		self.obj("entry14").set_text("%d" % self.rezept['lagern']['dauer'])
	def get_fields(self):
		# Schroten & Maischen:
		try:
			self.rezept['maischen']['hg'] = float(self.obj("entry2").get_text())/self.ausschlagmenge
		except ValueError:
			self.show_msg("Ungültige Eingabe!", "Der Wert für den Hauptguss darf nur Zahlen enthalten.", gtk.MESSAGE_WARNING)
			return False
		if self.rezept['maischen']['hg'] < 0:
			self.show_msg("Ungültige Eingabe!", "Der Wert für den Hauptguss muss positiv sein.", gtk.MESSAGE_WARNING)
			return False
		##
		try:
			self.rezept['maischen']['ein'] = int(self.obj("entry3").get_text())
		except ValueError:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Einmaischtemperatur darf nur ganze Zahlen enthalten.", gtk.MESSAGE_WARNING)
			return False
		if self.rezept['maischen']['ein'] < 0 or self.rezept['maischen']['ein'] > 100:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Einmaischtemperatur muss zwischen 0 und 100 liegen.", gtk.MESSAGE_WARNING)
			return False
		##
		try:
			self.rezept['maischen']['ab'] = int(self.obj("entry10").get_text())
		except ValueError:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Abmaischtemperatur darf nur ganze Zahlen enthalten.", gtk.MESSAGE_WARNING)
			return False
		if self.rezept['maischen']['ab'] < 0 or self.rezept['maischen']['ab'] > 100:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Abmaischtemperatur muss zwischen 0 und 100 liegen.", gtk.MESSAGE_WARNING)
			return False
		# Läutern:
		try:
			self.rezept['laeutern']['ruhe'] = int(self.obj("entry4").get_text())
		except ValueError:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Läuterruhe darf nur ganze Zahlen enthalten.", gtk.MESSAGE_WARNING)
			return False
		if self.rezept['laeutern']['ruhe'] < 0:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Läuterruhe muss positiv sein.", gtk.MESSAGE_WARNING)
			return False
		##
		try:
			self.rezept['laeutern']['ng'] = float(self.obj("entry5").get_text())/self.ausschlagmenge
		except ValueError:
			self.show_msg("Ungültige Eingabe!", "Der Wert für den Nachguss darf nur Zahlen enthalten.", gtk.MESSAGE_WARNING)
			return False
		if self.rezept['laeutern']['ng'] < 0:
			self.show_msg("Ungültige Eingabe!", "Der Wert für den Nachguss muss positiv sein.", gtk.MESSAGE_WARNING)
			return False
		##
		try:
			self.rezept['laeutern']['ng_t'] = int(self.obj("entry6").get_text())
		except ValueError:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Nachgusstemperatur darf nur ganze Zahlen enthalten.", gtk.MESSAGE_WARNING)
			return False
		if self.rezept['laeutern']['ng_t'] < 0 or self.rezept['laeutern']['ng_t'] > 100:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Nachgusstemperatur muss zwischen 0 und 100 liegen.", gtk.MESSAGE_WARNING)
			return False
		# Kochen:
		try:
			self.rezept['kochen']['dauer'] = int(self.obj("entry7").get_text())
		except ValueError:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Kochdauer darf nur ganze Zahlen enthalten.", gtk.MESSAGE_WARNING)
			return False
		if self.rezept['kochen']['dauer'] < 0:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Kochdauer muss positiv sein.", gtk.MESSAGE_WARNING)
			return False
		# Gären:
		i = self.obj("combobox2").get_active()
		if i < len(self.hefe_ug):
			# UG
			self.rezept['gaeren']['hefe'] = (0, self.hefe_ug[i][0])
			self.rezept['gaeren']['evg'] = self.hefe_ug[i][3]
		else:
			# OG
			self.rezept['gaeren']['hefe'] = (1, self.hefe_og[i-len(self.hefe_ug)][0])
			self.rezept['gaeren']['evg'] = self.hefe_og[i-len(self.hefe_ug)][3]
		##
		try:
			self.rezept['gaeren']['temperatur'] = int(self.obj("entry9").get_text())
		except ValueError:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Gärtemperatur darf nur ganze Zahlen enthalten.", gtk.MESSAGE_WARNING)
			return False
		if self.rezept['gaeren']['temperatur'] < 1 or self.rezept['gaeren']['temperatur'] > 100:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Gärtemperatur muss zwischen 1 und 100 liegen.", gtk.MESSAGE_WARNING)
			return False
		##
		try:
			self.rezept['gaeren']['druck'] = float(self.obj("entry12").get_text())
		except ValueError:
			self.show_msg("Ungültige Eingabe!", "Der Wert für den Spundungsdruck darf nur Zahlen enthalten.", gtk.MESSAGE_WARNING)
			return False
		if self.rezept['gaeren']['druck'] < 0:
			self.show_msg("Ungültige Eingabe!", "Der Wert für den Spundungsdruck muss positiv sein.", gtk.MESSAGE_WARNING)
			return False
		# Lagern:
		try:
			self.rezept['lagern']['temperatur'] = int(self.obj("entry13").get_text())
		except ValueError:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Lagertemperatur darf nur ganze Zahlen enthalten.", gtk.MESSAGE_WARNING)
			return False
		if self.rezept['lagern']['temperatur'] < 0 or self.rezept['lagern']['temperatur'] > 100:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Lagertemperatur muss zwischen 0 und 100 liegen.", gtk.MESSAGE_WARNING)
			return False
		##
		try:
			self.rezept['lagern']['dauer'] = int(self.obj("entry14").get_text())
		except ValueError:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Lagerdauer darf nur ganze Zahlen enthalten.", gtk.MESSAGE_WARNING)
			return False
		if self.rezept['lagern']['dauer'] < 0:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Lagerdauer muss positiv sein.", gtk.MESSAGE_WARNING)
			return False
		return True
	def set_image2(self, nr):
		imgs = [
			"img/schroten.png",
			"img/maischen.png",
			"img/laeutern.png",
			"img/kochen.png",
			"img/anstellen.png",
			"img/gaeren.png",
			"img/lagern.png"
		]
		texte = [
			"""Unter dem Schroten versteht man die Zerkleinerung des Malzes, die nötig ist,
um während des Maischens an die Korninhaltsstoffe zu gelangen.
Dabei ist es wichtig, die richtige Schrotqualität zu treffen.
Das Malzkorn darf weder zu fein noch zu grob zerkleinert werden.

Um mit dem Schroten zu beginnen, wählen Sie die gewünschten Malzsorten aus.""",

			"""Der Maischevorgang ist für die Bierherstellung grundlegend,
da er über die Farbe und die Vergärbarkeit der späteren Würze entscheidet.
Während des Maischens lösen sich im Malz enthaltene Enzyme,
wobei Stärke aus dem Malz und der Rohfrucht in Zucker umgewandelt wird.
Wird nicht alle Stärke abgebaut, entsteht nicht genug löslicher Zucker, 
weshalb das Bier nicht richtig vergären kann und einen mehligen Geschmack entwickelt.
Beim Einmeischen wird das Malzschrot gründlich mit dem Hauptguss vermengt. 
Die sogenannte Kesselmaische bezeichnet ein Verfahren, bei dem sich die gesamte Maische
in einem beheizbaren Kessel befindet. Diese wird unter Rühren von Rast zu Rast weiter aufgeheizt.
Eine Rast bezeichnet eine Temperaturstufe. Welche Rast zum Einsatz kommt, hängt von den eingesetzten
Malz - und Getreidesorten und von den gewünschten Würzeeigenschaften (Vergärbarkeit, Schaumverhalten) ab.

Rastenübersicht:
Glucanaserast: Abbau von ß-Glucan durch Glucanasemit hohem Glukanantteil (z.B. Roggenmalz)
Ferulasäurerast: Bildung von Ferulasäure (Vorläufer von Nelke- und Bananenaromen bei Weizenbier)		
Eiweißrast: Spaltung von langkettigen Proteinen
Maltoserast: Abbau von Stärke zu vergärbarer Maltose
Verzuckerungsrast: Abbau von Stärke zu nicht-vergärbaren Dextrinen

Wählen Sie nun die Menge des Hauptgusses, die Temperatur, bei der das Malz zugegeben wird, die einzelnen
Rasten und die Temperatur, bei der das Maischen beendet ist.""",

			"""Das Läutern bezeichnet die Filtration des ausgekochten Malzes aus der Maische.
Das Läutern beginnt, indem die Maische in einen Läuterbottich gegeben wird.
Dieser ist ein Gefäß über dessem Boden noch ein Siebboden mit feinen Schlitzen liegt.
Dabei läuft die Würze durch das Sieb ab. Die festen Maischebestandteile (Treber) bleiben im Bottich zurück,
weshalb sie mit Wasser ausgewaschen werden (Nachguss), um möglichst alle Inhaltsstoffe herauszubekommen. 
Ergebnis dieses etwa 3 Stunden dauernden Prozesses ist die Würze, in der noch Aromastoffe und andere Substanzen
(z.B. Eiweiß) gelöst sind, die für den Geschmack des Bieres bedeutsam sind. Die Zuckerkonzentration des Würze 
bestimmt außerdem den späteren Alkoholgehalt.

Wählen Sie nun, wie lange die Maische vor dem Abläutern ruhen soll, die Menge des Wassers, das hier noch
dazu gegeben wird (Nachguss) und die Temperatur dieses Wassers (normalerweise 78 °C).""",

			"""Nach dem Abläufern wird die Würze ca. 60 - 90 Minuten gekocht. Der Hopfen soll zum Geschmack des Bieres beitragen
und es haltbar machen. Je länger Hopfen kocht, deste mehr Gerb - und Bitterstoffe gibt er ab. Dabei nimmt allerdings
das feine Hopfenaroma ab. 
Im Whirlpool wird die Würze durch kräftiges Rühren in einen Strudel versetzt. Dabei bilden Schwebstoffe in der
Mitte des Kesselbodens einen Trubkegel. Kommt die Flüssigkeit wieder zur Ruhe, wird die Würze abgepumpt.

Wählen Sie jetzt bitte die Dauer des Kochvorgangs und die verschiedenen Hopfengaben. Vorderwürze bedeutet, dass
der Hopfen noch vor dem Kochen zugegeben wird, wodurch ein besonderes Aroma entsteht.""",

			"""Im nächsten Schritt wird die klare Würze mit Brau - und Eiswasser auf ca. 6°C heruntergekühlt. 
In diesem Zustand wird Bierhefe zugegeben und diese durch Rühren belüftet. 
Danach word der Gärbehälter nahezu luftdicht abgeschlossen und an einem Ort ohne Temperaturschwankungen 
abgestellt. Die Hefe von obergärigem (OG) Bier braucht ca. 15 - 20 °C, die von untergärigem (UG) Bier nur ca. 5 - 10 °C.

Wählen Sie nun die Hefe, die Sie für Ihr Bier verwenden möchten.""",

			"""Die Dauer des Gärungsprozesses hängt von der Biersorte und der Sorte der Hefe ab. Zu Beginn der Gärung
verarbeitet Hefe Sauerstoff bis dieser aufgebraucht ist. Danach setzt die Umwandlung von Malzzucker 
in Alkohol und Kohlensäure ein. Dabei bildet sich weißer Schaum (Kräusen) aus Rückständen der Gärung,
der in den nächsten Tagen dicker wird und das Bier vor Bakterien schützt. Die Hauptgärung ist beendet,
wenn die Kräusen eingefallen sind.

Wählen Sie bitte die Temperatur, bei der vergoren werden soll, und den Druck, unter dem das Fass stehen soll.
Beide Faktoren beeinflussen den CO2-Gehalt des Biers.""",

			"""Beim Lagern ist zu beachten, dass das Bier kalt und dunkel steht. Flaschen sollten generell stehend gelagert werden,
da sich so ggf. Hefereste am Flaschenboden ablagern können. Desweiteren sollten die Flaschen in den ersten Tagen
nach der Abfüllung kurz entlüftet werden, damit ein hoher CO2-Druck vermieden werden kann, der zur Explosion
einer Flasche führen kann. Untergärige Biere müssen sofort nach der Abfüllung kühl gelagert werden, obergärige erst 
3-4 Tage danach.

Wählen Sie nun bitte die Temperatur und Dauer der Lagerung. Wenn Sie damit fertig sind, klicken Sie bitte auf den Button
\"Brauprozess abschließen\" ganz unten, um das Ergebnis zu sehen."""
		]
		self.obj("image2").set_from_file(imgs[nr])
		self.obj("textbuffer2").set_text(texte[nr])
	def fill_model_schuettung(self):
		self.model_schuettung.clear()
		for item in self.rezept['maischen']['schuettung']:
			self.model_schuettung.append(["%.1f" % (item[0]*100), item[1], "%.1f" % (self.malzinfo_from_name(item[1])[1])])
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
	def hopfeninfo_from_name(self, name):
		for item in self.hopfen_bitter:
			if item[0] == name:
				return item
		for item in self.hopfen_aroma:
			if item[0] == name:
				return item
		return None
	def masspercent_to_sg(self, mp):
		return (mp/250.)+1
	def masspercent_to_af(self, mp):
		return mp*self.masspercent_to_sg(mp)
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
		self.rezept = copy.deepcopy(self.rezepte[self.obj("combobox1").get_active()])
		self.start_simulator()
		self.set_fields()
	# Button Start eigenes Rezept
	def on_button4_clicked(self, widget, *args):
		# Stammwürze einlesen:
		try:
			sw = float(self.obj("entry8").get_text())
		except ValueError:
			self.show_msg("Ungültige Eingabe!", "Der Wert für den Stammwürzegehalt darf nur Zahlen enthalten.", gtk.MESSAGE_WARNING)
			return
		if sw < 0:
			self.show_msg("Ungültige Eingabe!", "Der Wert für den Stammwürzegehalt muss positiv sein.", gtk.MESSAGE_WARNING)
			return
		self.rezept = {
			'stammwuerze': sw,
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
	def on_notebook2_switch_page(self, widget, page, page_num, *args):
		self.set_image2(page_num)
	def on_treeview_selection2_changed(self, selection):
		if selection.count_selected_rows() is 1:
			self.obj("button5").set_sensitive(True)
		else:
			self.obj("button5").set_sensitive(False)
	# Button Malz hinzufügen
	def on_button3_clicked(self, widget, *args):
		self.obj("window5").show()
	# Button Malz entfernen
	def on_button5_clicked(self, widget, *args):
		row = self.obj("treeview2").get_selection().get_selected()
		i = row[0].get_path(row[1])[0]
		self.rezept['maischen']['schuettung'].pop(i)
		self.fill_model_schuettung()
	def on_treeview_selection3_changed(self, selection):
		if selection.count_selected_rows() is 1:
			self.obj("button7").set_sensitive(True)
		else:
			self.obj("button7").set_sensitive(False)
	# Button Rast hinzufügen
	def on_button6_clicked(self, widget, *args):
		self.obj("window4").show()
	# Button Rast entfernen
	def on_button7_clicked(self, widget, *args):
		row = self.obj("treeview3").get_selection().get_selected()
		i = row[0].get_path(row[1])[0]
		self.rezept['maischen']['rasten'].pop(i)
		self.fill_model_rasten()
	def on_treeview_selection4_changed(self, selection):
		if selection.count_selected_rows() is 1:
			self.obj("button9").set_sensitive(True)
		else:
			self.obj("button9").set_sensitive(False)
	# Button Hopfen hinzufügen
	def on_button8_clicked(self, widget, *args):
		self.obj("window6").show()
	# Button Hopfen entfernen
	def on_button9_clicked(self, widget, *args):
		row = self.obj("treeview4").get_selection().get_selected()
		i = row[0].get_path(row[1])[0]
		self.rezept['kochen']['hopfen'].pop(i)
		self.fill_model_hopfengaben()
	# Button Brauprozess abschließen
	def on_button13_clicked(self, widget, *args):
		# Daten einlesen:
		if not self.get_fields():
			return
		# Stammwürze berechnen:
		### !!! self.rezept['stammwuerze'] setzen !!!
		if self.rezept['stammwuerze'] < 7:
			gattung = 'Einfachbier'
		elif self.rezept['stammwuerze'] < 11:
			gattung = 'Schankbier'
		elif self.rezept['stammwuerze'] < 16:
			gattung = 'Vollbier'
		else:
			gattung = 'Starkbier'
		self.obj("label52").set_text("%.1f %%" % (self.rezept['stammwuerze']))
		self.obj("label62").set_markup("<i>%s</i>" % (gattung))
		# Restextrakt berechnen:
		restextrakt = self.rezept['stammwuerze']*(1-(self.rezept['gaeren']['evg']/100.))
		self.obj("label36").set_text("%.1f %%" % (restextrakt))
		# Farbe berechnen:
		farbe = 0
		for item in self.rezept['maischen']['schuettung']:
			farbe += self.malzinfo_from_name(item[1])[1] * item[0]
		farbe *= self.rezept['stammwuerze']/10.
		if farbe < 8:
			farbeindruck = 'hell'
		elif farbe < 12:
			farbeindruck = 'gold'
		elif farbe < 20:
			farbeindruck = 'bernstein'
		elif farbe < 35:
			farbeindruck = 'kupfer'
		elif farbe < 60:
			farbeindruck = 'braun'
		else:
			farbeindruck = 'schwarz'
		self.obj("label54").set_text("%d EBC" % (farbe))
		self.obj("label61").set_markup("<i>%s</i>" % (farbeindruck))
		# Bitterkeit berechnen:
		bitterkeit = 0
		for item in self.rezept['kochen']['hopfen']:
			if item[2] is -1:
				dauer = self.rezept['kochen']['dauer']
			elif item[2] is -2:
				dauer = 0
			else:
				dauer = item[2]
			menge = item[1]*self.ausschlagmenge
			alpha = self.hopfeninfo_from_name(item[0])[2]
			bitterkeit += ((menge*alpha*10)/self.ausschlagmenge) * (1.65*(0.000125**(0.004*self.rezept['stammwuerze']))) * ((1-(math.e**(-0.04*dauer)))/4.15)
		bitterkeit_rel = bitterkeit/self.rezept['stammwuerze']
		if bitterkeit_rel < 1:
			bitterkeit_eindruck = 'sehr mild'
		elif bitterkeit_rel < 1.5:
			bitterkeit_eindruck = 'mild'
		elif bitterkeit_rel < 2.5:
			bitterkeit_eindruck = 'ausgewogen'
		elif bitterkeit_rel < 3.0:
			bitterkeit_eindruck = 'moderat herb'
		else:
			bitterkeit_eindruck = 'sehr herb'
		self.obj("label56").set_text("%d IBU" % (bitterkeit))
		self.obj("label63").set_text("%.2f IBU pro %% Stammwürze" % (bitterkeit_rel))
		self.obj("label64").set_markup("<i>%s</i>" % (bitterkeit_eindruck))
		# Alkoholgehalt berechnen:
		alkoholgehalt = (0.405*(self.rezept['stammwuerze']-restextrakt))/0.795
		self.obj("label58").set_text("%.2f %%vol" % (alkoholgehalt))
		# CO2-Gehalt berechnen:
		co2 = (self.rezept['gaeren']['druck']+1)*(0.0015461*(self.rezept['gaeren']['temperatur']**2) + 0.10711*self.rezept['gaeren']['temperatur'] + 3.1962)/3.
		self.obj("label60").set_text("%.2f g/l" % co2)
		# Aromen berechnen:
		aromen = []
		for item in self.rezept['kochen']['hopfen']:
			a = self.hopfeninfo_from_name(item[0])[3]
			for aroma in a:
				if not aroma in aromen:
					aromen.append(aroma)
		self.obj("label49").set_text(", ".join(aromen))
		# Bild setzen:
		if farbe <= 4:
			f = "img/farbe/01.png"
		elif farbe <= 8:
			f = "img/farbe/02.png"
		elif farbe <= 12:
			f = "img/farbe/03.png"
		elif farbe <= 20:
			f = "img/farbe/04.png"
		elif farbe <= 35:
			f = "img/farbe/05.png"
		elif farbe <= 60:
			f = "img/farbe/06.png"
		else:
			f = "img/farbe/07.png"
		self.obj("image3").set_from_file(f)
		# Ergebnis-Fenster anzeigen:
		self.obj("window2").hide()
		self.obj("window3").show()
		self.obj("window3").maximize()
	###############
	### window3 ### (Ergebnis)
	###############
	def on_window3_delete_event(self, *args):
		self.obj("window3").hide()
		self.obj("window2").show()
		self.obj("window2").maximize()
		return True
	###############
	### window4 ### (Rast hinzufügen)
	###############
	def on_window4_delete_event(self, *args):
		self.obj("window4").hide()
		return True
	def on_radiobutton6_toggled(self, widget, *args):
		if widget.get_active():
			self.obj("entry16").set_sensitive(True)
		else:
			self.obj("entry16").set_sensitive(False)
	def on_button11_clicked(self, widget, *args):
		# Dauer einlesen:
		try:
			dauer = int(self.obj("entry15").get_text())
		except ValueError:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Dauer darf nur ganze Zahlen enthalten.", gtk.MESSAGE_WARNING)
			return
		if dauer < 1:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Dauer muss >= 1 sein.", gtk.MESSAGE_WARNING)
			return
		# Typ einlesen:
		if self.obj("radiobutton1").get_active():
			typ = 'glucanase'
			temp = 37
		elif self.obj("radiobutton2").get_active():
			typ = 'ferula'
			temp = 44
		elif self.obj("radiobutton3").get_active():
			typ = 'eiweiss'
			temp = 57
		elif self.obj("radiobutton4").get_active():
			typ = 'maltose'
			temp = 62
		elif self.obj("radiobutton5").get_active():
			typ = 'zucker'
			temp = 72
		else:
			typ = ''
			# Temperatur einlesen:
			try:
				temp = int(self.obj("entry16").get_text())
			except ValueError:
				self.show_msg("Ungültige Eingabe!", "Der Wert für die Temperatur darf nur ganze Zahlen enthalten.", gtk.MESSAGE_WARNING)
				return
			if temp < 1 or temp > 100:
				self.show_msg("Ungültige Eingabe!", "Der Wert für die Temperatur muss zwischen 1 und 100 liegen.", gtk.MESSAGE_WARNING)
				return
		# Rast hinzufügen:
		self.rezept['maischen']['rasten'].append((typ, temp, dauer))
		self.fill_model_rasten()
		# Fenster ausblenden:
		self.obj("window4").hide()
	###############
	### window5 ### (Malz hinzufügen)
	###############
	def on_window5_delete_event(self, *args):
		self.obj("window5").hide()
		return True
	def on_button12_clicked(self, widget, *args):
		# Anteil einlesen:
		try:
			anteil = float(self.obj("entry18").get_text())
		except ValueError:
			self.show_msg("Ungültige Eingabe!", "Der Wert für den Malzanteil darf nur Zahlen enthalten.", gtk.MESSAGE_WARNING)
			return
		if anteil < 0 or anteil > 100:
			self.show_msg("Ungültige Eingabe!", "Der Wert für den Malzanteil muss zwischen 0 und 100 liegen.", gtk.MESSAGE_WARNING)
			return
		# bisherige Schüttung summieren:
		gesamt = 0
		for item in self.rezept['maischen']['schuettung']:
			gesamt += item[0]*100
		gesamt += anteil
		if gesamt > 100:
			self.show_msg("Ungültige Eingabe!", "Insgesamt können nur 100% Schüttung aufgeteilt werden.", gtk.MESSAGE_WARNING)
			return
		# Typ einlesen:
		if self.obj("treeview1").get_selection().count_selected_rows() != 1:
			self.show_msg("Ungültige Eingabe!", "Es wurde kein Malztyp ausgewählt.", gtk.MESSAGE_WARNING)
			return
		row = self.obj("treeview1").get_selection().get_selected()
		typ = row[0].get_value(row[1], 0)
		# Malz hinzufügen:
		self.rezept['maischen']['schuettung'].append((anteil/100., typ))
		self.fill_model_schuettung()
		# Fenster ausblenden:
		self.obj("window5").hide()
	###############
	### window6 ### (Hopfen hinzufügen)
	###############
	def on_window6_delete_event(self, *args):
		self.obj("window6").hide()
		return True
	def on_radiobutton8_toggled(self, widget, *args):
		if widget.get_active():
			self.obj("entry20").set_sensitive(True)
		else:
			self.obj("entry20").set_sensitive(False)
	def on_button14_clicked(self, widget, *args):
		# Menge einlesen:
		try:
			menge = float(self.obj("entry19").get_text())
		except ValueError:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Hopfenmenge darf nur Zahlen enthalten.", gtk.MESSAGE_WARNING)
			return
		if menge < 0:
			self.show_msg("Ungültige Eingabe!", "Der Wert für die Hopfenmenge muss positiv sein.", gtk.MESSAGE_WARNING)
			return
		# Typ einlesen:
		if self.obj("treeview5").get_selection().count_selected_rows() != 1:
			self.show_msg("Ungültige Eingabe!", "Es wurde kein Hopfentyp ausgewählt.", gtk.MESSAGE_WARNING)
			return
		row = self.obj("treeview5").get_selection().get_selected()
		typ = row[0].get_value(row[1], 1)
		# Kochzeit einlesen:
		if self.obj("radiobutton7").get_active():
			zeit = -1
		elif self.obj("radiobutton8").get_active():
			try:
				zeit = int(self.obj("entry20").get_text())
			except ValueError:
				self.show_msg("Ungültige Eingabe!", "Der Wert für die Kochzeit darf nur ganze Zahlen enthalten.", gtk.MESSAGE_WARNING)
				return
			if zeit < 0:
				self.show_msg("Ungültige Eingabe!", "Der Wert für die Kochzeit muss positiv sein.", gtk.MESSAGE_WARNING)
				return
		else:
			zeit = -2
		# Hopfen hinzufügen:
		self.rezept['kochen']['hopfen'].append((typ, menge/self.ausschlagmenge, zeit))
		self.fill_model_hopfengaben()
		# Fenster ausblenden:
		self.obj("window6").hide()
if __name__ == '__main__':
	bs = Biersimulator()
	bs.run()
