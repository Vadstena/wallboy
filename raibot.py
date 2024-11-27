#!/usr/bin/env python3

# MIT License
# Copyright (c) 2024 Joao Silva
#
# This software is licensed under the MIT License. See the LICENSE file for more details.

import random

# TODO:
# negate literals
# pluses (draw, soul charge)
# account for soul
# P format: optional starter draw, stride/4x drive

r = random.SystemRandom()

def hand2String(hand):
	hand_str = ""
	for cname in hand:
		hand_str += "{}({}), ".format(cname, hand[cname][0])
	return hand_str[:-2]

class Literal():
	def __init__(self, name, n_copies, as_vg, timing):
		self.card_name = name
		self.n_copies = n_copies
		self.as_vg = False #if True -> include the vg in the counting
		if as_vg == 'y':
			self.as_vg = True
		self.timing = timing # <ride, main, end>_phase
		self.value = False

class Card():
	def __init__(self, name, grade, c_type, gift, unique_id):
		self.name = name
		self.grade = grade
		self.type = c_type
		self.gift = gift
		self.id = unique_id

class Game:
	def __init__(self):
		self.deck_info = [None, None] #[<tuple<Card>>, <string with gift type>]
		self.deck = None
		self.hand = {}     # { <card name> : [<# of cards in hand with this name> , <card>] }
		self.turn = 1
		self.vg = None
		self.WALLBOY = Card("Wallboy the Hierophant", 0, "PimPamPum", "ACCEL X", 0)
		self.went_first = None
		self.go_first_preference = None
		self.visibility = False
		self.aggress_mull = False
		self.stats = None

	def pop(self):
		topdeck = self.deck[0]
		del self.deck[0]
		return topdeck

	def draw(self, c):
		if c.name not in self.hand:
			self.hand[c.name] = [0, c]
		self.hand[c.name][0] += 1
		#print("in Draw(): "+ str([(cname, self.hand[cname][0]) for cname in self.hand]))

	def check(self, c):
		if c.type in self.stats:
			self.stats[c.type] += 1
		if c.type == "draw_trigger":
			if self.visibility:
				print("#			draw trigger's draw:" + self.deck[0].name)
			self.draw(self.pop())

	def driveCheck(self):
		drive = self.pop()
		if self.visibility:
			print("#		drive: " + drive.name)
		self.check(drive)
		self.draw(drive)

	def damageCheck(self):
		topdeck = self.pop()
		if self.visibility:
			print("#		damage: " + topdeck.name)
		self.check(topdeck)
		# does not bother storing damage

	def ride(self, c):
		if self.visibility:
			print("#	new VG: " + c.name)
		if self.vg.type == "PimPamPum":
			if self.visibility:
				print("#	starter draw: " + self.deck[0].name)
			self.draw(self.pop())
		if c.gift == "accel" and self.deck_info[1] == "accel2":
			if self.visibility:
				print("#	accel2 draw: " + self.deck[0].name)
			self.draw(self.pop())
		self.vg = c
		if c.name in self.hand: # if not riding from G-Assist
			self.hand[c.name][0] -= 1
			if self.hand[c.name][0] == 0:
				del self.hand[c.name]

	def tryRide(self, targets, offset = 1):
		ride = None
		rides = []
		ok_rides = []
		forced_rides = []
		for v in self.hand.values():
			if v[1].type == "normal_unit" and (v[1].grade == self.vg.grade + offset):
				rides.append(v[1])
		if rides == []:
			return False
		for c in rides:
			if c.name in targets:
				if targets[c.name] == "ride_tg":
					self.ride(c)
					return True
				elif targets[c.name] == None:
					ok_rides.append(c)
				elif targets[c.name] == "call_tg":
					forced_rides.append(c)
			else:
				ok_rides.append(c)
		if self.vg.grade < 3: # if VG is already g3 then only want to ride the best 'ride_tg'
			for c in ok_rides:
				self.ride(c)
				return True
			for c in forced_rides:
				self.ride(c)
				return True
		return False

	def mulligan(self, targets, hard_keep, hard_send):
		grades = [0,0,0,0,0,0] 	# number of kept RIDES for each grade
		surplus = []			# names of 'good' cards that are not hard kept
		keep_names = []			# names of cards being kept
		keep_ids = []			# IDs of cards being kept
		temp_hand = self.deck[:5]
		del self.deck[:5]
		if self.visibility:
			print("# hand b4 Mulligan: " + str([c.name for c in temp_hand]))

		# KEEP hierarchy: hard_keeps > ride_tg > suboptimal rides in targets > suboptimal rides not in targets > any rides still missing > (if hand is good) keep non-triggers
		for c in temp_hand:	# prioritizes hardkeeps
			if c.name in hard_keep and c.name not in keep_names: # user keeps maximum of 1 copy of each card he wants to hard keep
				keep_names.append(c.name)
				keep_ids.append(c.id)
				if targets[c.name] == "ride_tg": # non-'ride_tg' hard keeps are not considered as possible rides
					grades[c.grade] += 1
			elif c.type == "normal_unit" and c.name not in hard_send and (c.grade < 4 or targets[c.name] == "ride_tg"): 
			# if the user wants G0, orders, etc in starting hand he can include them in 'hard_keep'
				surplus.append(c)
		for c in surplus: # prioritizes 'ride_tg'
			if grades[c.grade] == 0 and c.name in targets and targets[c.name] == "ride_tg":
				keep_ids.append(c.id)
				keep_names.append(c.name)
				grades[c.grade] += 1
		for c in surplus: # prioritizes rideable 'targets'
			if grades[c.grade] == 0 and c.name in targets and targets[c.name] != "call_tg":
				keep_ids.append(c.id)
				keep_names.append(c.name)
				grades[c.grade] += 1
		for c in surplus: # prioritizes suboptimal rides
			if grades[c.grade] == 0 and c.name not in targets:
				keep_ids.append(c.id)
				keep_names.append(c.name)
				grades[c.grade] += 1
		for c in surplus: # settles for anything to fill missing rides (except 'hard_send' cards)
			if grades[c.grade] == 0: #
				keep_ids.append(c.id)
				keep_names.append(c.name)
				grades[c.grade] += 1
		if not(self.aggress_mull) or all([(cname in keep_names) for cname in targets if targets[cname] == "ride_tg"]): # all 'ride_tg' in hand or not aggressively looking for them
			if grades[1] > 0 and grades[2] > 0: # if not missing g1 nor g2, prioritizes keeping suboptimal normals units in hand over possibly drawing back triggers
				for c in surplus:
					if c.id not in keep_ids and (c.grade < 3 or (c.name in targets and grades[3] == 1)): # keeps max 1 extra g3 and only if there's already a g3 ride
						keep_ids.append(c.id)
						grades[c.grade] += 1
			if grades[1] == 1:
				for c in surplus:
					if c.grade == 1 and c.name in targets and c.id not in keep_ids:
						keep_ids.append(c.id)
						grades[1] += 1
						break
				for c in surplus:
					if c.grade == 1 and grades[1] == 1 and c.id not in keep_ids:
						keep_ids.append(c.id)
						grades[1] += 1
						break
		cards_kept = [c.name for c in temp_hand if c.id in keep_ids]
		if self.visibility:
			print("# kept: " + str(cards_kept))
		for c in temp_hand:
			if c.id in keep_ids:
				self.draw(c)
			else:
				self.deck.append(c)
		for i in range(5 - len(keep_ids)):
			self.draw(self.pop())

	def gAssist(self, targets): # automatically rides if successful in finding a unit to ride instead of drawing the card for optimization purposes
		ideal_rides = []
		reg_rides = []
		worst_rides = []
		for c in self.deck[:5]:
			if c.grade == 0 or (c.grade == 3 and c.gift == None) or c.type != "normal_unit": # ignores g0s, giftless g3s, and non-normal units
				continue
			if c.grade == self.vg.grade + 1:
				if c.name in targets and targets[c.name] == "ride_tg":
					ideal_rides.append(c)
				elif c.name in targets and targets[c.name] == "call_tg":
					worst_rides.append(c)
				else:
					reg_rides.append(c)
		if ideal_rides:
			self.ride(ideal_rides[0])
		elif reg_rides:
			self.ride(reg_rides[0])
		elif worst_rides:
			self.ride(worst_rides[0])

	def newGame(self):
		self.deck = list(self.deck_info[0])
		r.shuffle(self.deck)
		r.shuffle(self.deck) # shuffle so nice we do it twice
		self.hand = {}
		self.turn = 1
		self.vg = self.WALLBOY
		if self.go_first_preference != None:
			self.went_first = self.go_first_preference
		else:
			self.went_first = r.choice((True,False))
		self.stats = {"heal_trigger": 0, "draw_trigger": 0, "critical_trigger": 0, "front_trigger": 0}

	def runSimulation(self, targets, hard_send, hard_keep, damage_distribution, max_turn, test_turns, sim_n):
		self.newGame()
		if self.visibility:
			turn_priority = "Second"
			if self.went_first:
				turn_priority = "First"
			print("\n# # # # # # #   Game "+ str(sim_n + 1) + " --> went " + turn_priority)
		self.mulligan(targets, hard_keep, hard_send)
		while self.turn <= max_turn:
			# user's turn
			if self.visibility:
				print("# ~ turn " + str(self.turn) + " VG: " + self.vg.name)
				print("# hand: " + hand2String(self.hand))
				print("#	turn draw: " + self.deck[0].name)
			self.draw(self.pop())
			
			updateLiterals(self, test_turns[self.turn], self.hand, self.vg, "ride_phase")

			if self.vg.grade < 3:
				if not(self.tryRide(targets)):
					if self.visibility:
						print("#		failed ride -> attempting G-Assist")
					self.gAssist(targets) # automatically rides if gAssist is successful, bypassing drawing the unit to ride

			elif self.vg.grade >= 3: # mutual exclusivity of 'if/elif' ensures only 1 ride on turn 3
				if not(self.tryRide({k:targets[k] for k in targets if targets[k] == "ride_tg"})): # if it failed ride superior grade 'ride_tg'
					self.tryRide({k:targets[k] for k in targets if targets[k] == "ride_tg"}, offset = 0) # attempts to ride same grade 'ride_tg'
			
			updateLiterals(self, test_turns[self.turn], self.hand, self.vg, "main_phase")
			
			if not(self.went_first and self.turn == 1):
				self.driveCheck()
				if self.vg.grade == 3:
					self.driveCheck()
				if self.vg.grade >= 4:
					self.driveCheck()

			updateLiterals(self, test_turns[self.turn], self.hand, self.vg, "end_phase")

			if self.turn == max_turn:
				break

			# opponent's turn
			for i in range(r.randint(damage_distribution[self.turn][0], damage_distribution[self.turn][1])):
				self.damageCheck()

			self.turn += 1

def updateLiterals(game, literals, hand, vg, timing):
	#print("\nt: " + timing)
	for lit in literals:
		#print("		lit.t: " + lit.timing)
		if lit.timing == timing:
			#print("			evaluating literal. timing: " + timing + ", lit.t: " + lit.timing)
			avail_copies = 0
			if lit.card_name in hand:
				avail_copies += hand[lit.card_name][0]
			if lit.as_vg and vg.name == lit.card_name:
				avail_copies += 1
			if avail_copies >= lit.n_copies:
				lit.value = True

def parseDeck(file):
	GunSaluteDeck = ()
	unique_id = 0
	card_types = {"critical_trigger", "heal_trigger", "draw_trigger", "front_trigger" , "order", "normal_unit"}
	for line in file:
		gift = None
		tokens = line.split() # nr_copies name grade unit_type [gift]
		if len(tokens) == 5:
			gift = tokens[4].lower()
		for i in range(int(tokens[0])):
			unique_id += 1
			if tokens[3] not in card_types:
				print("\n> > {} < < has an invalid card type!! OwO Possible types are: \n".format(tokens[1].upper()), str(card_types))
				raise SystemExit()
			GunSaluteDeck += (Card(tokens[1].lower(), int(tokens[2]), tokens[3], gift, unique_id),)
	return GunSaluteDeck

def parseInput(game):
	targets = {}
	hard_send = []
	hard_keep = []
	inputString = "  Type 'help' for input file formatting specifications; 'about' for tips and guidelines; or the following to run the simulator:\n\n -> <file name> <number of runs> [<seeGame>]\n    E.g. 1: -> PaleMoon.txt 10000\n    E.g. 2: -> royals_gancelot.txt 1 seeGame\n\n -> "
	tokens = input(inputString).split()
	while tokens[0].lower() in ("help", "about", "more"):
		if tokens[0].lower() == "help":
			printHelp()
		elif tokens[0].lower() in ("about", "more"):
			printAbout()
		tokens = input("\n" + inputString).split()
	fname = tokens[0]
	runs  = int(tokens[1])
	if len(tokens) == 3 and tokens[-1].lower() == "seegame":
		game.visibility = True
	
	with open(fname) as file:
		while(True):
			line = file.readline()
			if line == "":
				break
			elif line.lower() == "go_first:\n": # ---------------------> OPTIONAL
				token = file.readline().split()[0]
				if token == "yes":
					game.go_first_preference = True
				elif token == "no":
					game.go_first_preference = False
				elif token == "random":
					game.go_first_preference = None
				else:
					print("\nYou did an oopsie uwu ~ 'go_first' must be 'yes', 'no' or 'random'.")
					raise SystemExit()
			elif line.lower() == "aggress_mull:\n": # -----------------> OPTIONAL
				token = file.readline().split()[0]
				if token == "yes":
					game.aggress_mull = True
				elif token == "no":
					game.aggress_mull = False
				else:
					print("\nYou did an oopsie ummu ~ 'aggress_mull' must be 'yes' or 'no'.")
					raise SystemExit()
			elif line.lower() == "gift:\n": # -------------------------> OPTIONAL
				game.deck_info[1] = file.readline().split()[0].lower()
			elif line.lower() == "keep:\n": # -------------------------> OPTIONAL
				line = file.readline()
				hard_keep = [name.lower() for name in line.split()]
			elif line.lower() == "send:\n": # -------------------------> OPTIONAL
				line = file.readline()
				hard_send = [name.lower() for name in line.split()]
			elif line.lower() == "damage:\n": # -----------------------> NEEDS max_turn, OPTIONAL
				line = file.readline()
				while line != "\n":
					tokens = line.split()
					dam_range = [int(d) for d in tokens[1].split("-")]
					damage_turn = int(tokens[0])
					damage_distribution[damage_turn] = dam_range # damage_distribution created in 'max_turn' section
					line = file.readline()
			elif line.lower() == "test:\n": # -------------------------> NEEDS max_turn, MANDATORY
				test_string = ""
				test_turns = [[] for i in range(max_turn + 1)]
				literals = {}
				id_suffix = 0
				line = file.readline()
				tokens = line.split()
				for t in tokens:
					if t in ("(", ")", "and", "or"):
						token = t
					else:
						lit = t.split("-") #0:card name, 1:by what turn, 2: # desired copies, 3: does the vg count?, 4: <r, m, e>
						id_suffix += 1
						lit_id = "x" + str(id_suffix)
						if lit[4] == 'r':
							lit_timing = "ride_phase"
						elif lit[4] == 'm':
							lit_timing = "main_phase"
						elif lit[4] == 'e':
							lit_timing = "end_phase"
						else:
							print("\nYou did an oopsie owO ~ Timing of literals must be 'r', 'm' or 'e'.")
							raise SystemExit()
						newLit = Literal(lit[0], int(lit[2]), lit[3], lit_timing)
						literals[lit_id] = newLit
						lit_turn = int(lit[1])
						test_turns[lit_turn].append(newLit)
						token = lit_id
					test_string += " " + token
			elif line.lower() == "max_turn:\n": # ---------------------> MANDATORY
				max_turn = int(file.readline().split()[0])
				damage_distribution = [[] for i in range(max_turn)]
			elif line.lower() == "targets:\n":  # ---------------------> OPTIONAL
				line = file.readline()
				while line != "\n":
					tokens = line.split()
					card_name = tokens[0].lower()
					if len(tokens) > 1:
						target_type = tokens[1].lower()
					else:
						target_type = None
					targets[card_name] = target_type
					line = file.readline()
			elif line.lower() == "deck:\n": # --------------------------> needs to be the last entry on the file, MANDATORY
				game.deck_info[0] = parseDeck(file)

	return targets, hard_send, hard_keep, damage_distribution, max_turn, test_string, test_turns, literals, runs

def resetLiterals(literals):
	for lit in literals.values():
		lit.value = False

def evalTest(test_str, literals):
	test_value_str = ""
	tokens = test_str.split()
	for t in tokens:
		if t[0] == "x":
			test_value_str += str(literals[t].value) + " "
		else:
			test_value_str += t + " "
	return eval(test_value_str)

def main():
	printGirl()
	game = Game()
	targets, hard_send, hard_keep, damage_distribution, max_turn, test_string, test_turns, literals, runs = parseInput(game)
	successful_runs = 0
	draws = heals = crits = fronts = 0

	for i in range(runs):
		game.runSimulation(targets, hard_send, hard_keep, damage_distribution, max_turn, test_turns, i)
		if game.visibility:
			print("# # # # # # # #")
		draws += game.stats["draw_trigger"]
		heals += game.stats["heal_trigger"]
		crits += game.stats["critical_trigger"]
		fronts += game.stats["front_trigger"]
		if evalTest(test_string, literals):
			successful_runs += 1
		resetLiterals(literals)
	
	print("\n+ + + + + + + RESULTS:\n+ Total runs: " + str(runs) + ", successful runs: " + "{:.2f}".format((successful_runs*100)/runs) +"%")
	print("+ triggers per game: Draws=" + "{:.2f}".format(draws/runs) + " Heals=" + "{:.2f}".format(heals/runs) + " Crits=" + "{:.2f}".format(crits/runs) + " Fronts=" + "{:.2f}".format(fronts/runs))
	print("+ + + + + + +")
	print("\n  Run me again some other time ~ uwu")

#
def printGirl():
	print("\n        raibot v2.0 by Satou\n        + + + + + + + + + + + + + + + + + + + + +")
	print("        + + + + + + WALLBOY SIMULATOR + + + + + +\n        + + + + + + + + + + + + + + + + + + + + +\n")

	print("                 ░░░░░▄▄░░░░░░░░░░░░░░░░")
	print("                 ░░░▄▀█▓▓█████▓▓▓█░░░░░░")
	print("                 ░░░▄█▓▓█████████▓▓█▌░░░")
	print("                 ░░█▓▓██▓▓▓▓▓▓█████▓█░░░")
	print("                 ░▐███████████▓▓████▓█░░")
	print("                 ░▐▌██▀▐▀▐▀▐█▌▀▌▐▀█▓██░░")
	print("                 ░▐░██░▄▀▀▄░░▄▀▀▄▒█▓█▌░░")
	print("                 ░░░▐▌▌░▐▓▌░░░▐▓▌▒█▓█▌░░")
	print("                 ░░░░░▌░░▀░░░░░▀░▒█▓█▌░░")
	print("                 ░░░░▐█░░░░▌░░░░░▐█▓█▌░░")
	print("                 ░░░░███░░░▄▄░░░▒███▓▌░░")
	print("                 ░░░▐▓███▒░░░░░▒▓███▓█░░")
	print("                 ░░░█▓████▒▓▓▓▓▓█████▓█░")
	print("                 ░░▐▓█████▒▒▒▒▒▓█████▓█▌")
	print("                 ░░█▓████▒▒░░░▒▒▓████▓▓█▌")
	print("\n  Irasshaimase goshujin sama! please enlarge this window ~ uwu\n")

#
def printAbout():
	print("\n+ Welcome to the WALLBOY SIMULATOR uwu.\n"
		  "+ The purpose of this simulator is to estimate the probability of having any given combination of cards (however\n"
		  "+ many copies), at any given combination of game timings, while prioritizing any set of cards, in the same game.\n"
		  "+ E.g. 'odds of having (at least 1) PG by the end of turn 2 AND a grade 3 unit to ride at the start of turn 3', or\n"
		  "+      'odds of having Golden Beast Tamer on turn 3, AND, having either Jumping Jill or Purple Trapezists on turn 4'.\n"
		  "+\n+ For this, the user must provide (at least) a deck and a test (1) to be evaluated. The program will run\n"
		  "+ as many simulations as instructed (2), and then output the percentage of simulations that passed the test.")
	print("+ You can visualize the simulations by including 'seeGame' in the input COMMAND (recommended only for")
	print("+ a small number of runs). E.g. 'royals_gancelot.txt 1 seeGame'.")
	print("+\n+ (1): The test is a propositional formula (from logic). Type 'help' and then 'test' for more details.")
	print("+ (2): 10 000 runs' results deviate 1-2%. 100 000 runs' results deviate <1%.")
	print("+\n+ Though it tries to approximate real games, this is a simple simulator. It does not use AI, and it does not\n"
		  "+ simulate calling rearguards, defending, nor selecting which cards to remove from the game when performing G-assist.\n"
		  "+ It does not use unit effects except for the starter which draws when rode upon (type 'help' then 'deck' for more info),\n"
		  "+ and the gift mechanic, which also draws when riding an 'accel' gifted unit IF the 'gift' in the input file is 'accel2'.\n"
		  "+ Therefore the output probability serves as a baseline that is always lower than that of real games where effects are used.")
	print("+ The purpose of the simulator is then to provide said probabilistic lower limit, but also to get an idea of the")
	print("+ difference of outcome when: varying the # of card copies in a deck (including triggers), varying damage received, softly")
	print("+ prioritizing different cards, and even aggressively looking for key cards during mulligan by sending back decent ones.")
	print("+ ")
	print("+\n+ Usage tips (read the 'help' section first):")
	print("+\n+ ~ During mulligan, at most 1 copy per card name in 'keep' will be kept. E.g. cannot HARD keep 2 'Blaster Blade'.")
	print("+   Grade 4 (G4) 'ride_tg' are kept by default. This can be avoided by including them in 'send' in the input FILE.\n"
		  "+   Other G4, 'order' and G0 cards are sent back by default. This can be changed by including them (E.g. G0 PGs) in 'keep'.")
	print("+\n+ ~ Units in 'keep', 'test' and 'targets' will typically overlap given that players are mostly interested in learning the")
	print("+   probability of seeing key cards, rather than unimportant ones. However, the 3 fields are independent, i.e., users can")
	print("+   estimate the probability of having an unimportant card, X, (including it in 'test') such that it is not a priority")
	print("+   (not in 'targets' nor in 'keep'), while hard keeping Y in the starting hand (including Y in 'keep'). E.g., facing 'Shadow\n"
		  "+   Paladin', you may want to know the probability of having Purple Trapezist when it is NOT prioritized, while hard 'keep'ing\n"
		  "+   a PG and having 'Jumping Jill' in 'targets'.\n+ + + + + + +")

#
def printHelp():
	prompt_str = "\n  Type one of the following field names for more details (type 'back' to GO BACK):\n   'max_turn'  'test'  'damage'  'go_first'  'aggress_mull'  'gift'  'keep'  'send'  'targets'  'deck'\n\n -> "
	print("\n ~ Fields must be separated by an empty line(s). Do NOT leave empty lines within a field, not even after the field's name.")
	print(" ~ Field names must be immediately followed by ':', and then followed by 1+ lines of text relating to that field.")
	print(" ~ Only 'max_turn', 'test' and 'deck' are MANDATORY fields.")
	print(" ~ Including OPTIONAL fields in the input file will further help the simulator approximate real games.")
	print(" ~ Fields included in the input file have to be in the same order as the one shown below (left to right).")
	token = input(prompt_str).lower()
	while(True):
		if token == "max_turn":
			print("\n+ line after 'max_turn:' must contain a number representing the number of (your) turns you want each simulation to last.")
			print("+\n+ > E.g. '3'")
		elif token == "test":
			print("\n+ line after 'test:' must contain an expression comprised of any logical combination of Literals.\n"
				  "+\n+ > E.g. 'L1 and ( L2 or ( L3 and L4 ) )'  ,  where Lx are Literals.\n"
				  "+\n+ Leave spaces between '(' , ')' , 'and' , 'or' and Literals. Format of a Literal: ")
			print("+\n+  	'<CardName>-<Turn>-<Num>-<VG_counts>-<Timing>'\n+")
			print("+ CardName:  card name of your choosing (ought to match a card in the 'deck' field).")
			print("+ Turn:      the turn that this Literal is to be evaluated. Must be LOWER THAN or EQUAL to 'max_turn'.")
			print("+ Num:       minimum number of available 'CardName' copies for the Literal to be 'True'.")
			print("+ VG_counts: can be 'y' (yes) or 'n' (no). If 'y', then the current Vanguard is included\n"
				  "+            when counting the number of available copies with CardName.")
			print("+ Timing:    evaluation moment in the 'Turn'. Can be 'r' ((start of) ride phase) , 'm' (main phase) or 'e' (end phase).")
			print("+\n+ > E.g. 1: 'gbt-4-1-y-r'\n"
				  "+        means: 'having (at least) 1 copy of 'gbt' (golden beast tamer) on turn 4 at the start of the ride phase\n"
				  "+                either in hand or as VG'.")
			print("+\n+ > E.g. 2: '( wonderzl-2-1-y-r and howell-2-1-n-m ) or ( beaumains-2-1-y-m and blondzl-2-1-y-m )'\n"
				  "+        means: 'by turn 2, having\n"
				  "+                1 'wonderzl' in hand or VG in ride phase and 1 'howell' in hand in main phase,\n"
				  "+                OR,\n"
				  "+                1 'beaumains' in hand or VG in main phase and 1 'blondzl' in hand or VG in main phase.' ")
			print("+\n+ > E.g. 3: 'ravenzl-2-1-y-m and ( <E.g. 2> )'\n"
				  "+        means: 'having 1 'ravenzl' by turn 2 in hand or VG in main phase, AND, 'E.g. 2'. ")
			print("+\n+ > E.g. 4: 'presenter-1-1-y-r and juggler-3-2-n-m'\n"
				  "+        LOOSELY: on turn 1, having 1 'presenter' to ride (or already in VG (which is impossible on turn 1, so in\n"
				  "+                 this case including the VG has no effect)), AND, on turn 3, having 2 'jugglers' to call.")
		elif token == "damage":
			print("\n+ OPTIONAL field. If not included, then no damage is taken, thus no damage is checked, thus lowering the chances of")
			print("+ checking draw triggers. With N = 'max_turn', after 'damage:' must follow EXACTLY N-1 lines, each with the following format:")
			print("+ \n+   	'<T> <min_d>-<max_d>'\n+")
			print("+ T: a number from 1 to N-1, referring to the turn.")
			print("+ min_d: minimum amount of damage you'd like to take on turn T.")
			print("+ max_d: maximum amount of damage you'd like to take on turn T.")
			print("+ \n+ > E.g. (with 'max_turn' set to 4 at the beggining of the FILE):")
			print("+\n+ '1 1-1\n+  2 1-2\n+  3 2-2'\n+\n+ means: take 1 damage on turn 1, 1 or 2 damage (evenly randomized) on turn 2, 2 damage on turn 3.")
			print("+ Taking 6+ damage does NOT end the game, each simulations only stops on 'max_turn'.")
			print("+ Choose reasonable values for each min_d/max_d.")
		elif token == "go_first":
			print("\n+ OPTIONAL field. Aka 'player priority', if included, the line after 'go_first:' must be 'yes', 'no' or 'random'.")
			print("+ Not including this field is the same as choosing 'random'.")
		elif token == "aggress_mull":
			print("\n+ OPTIONAL field. If included, the line after 'aggress_mull:' should contain either 'True' or 'False'.")
			print("+ If you don't include this field, 'aggress_mull's value is 'False' by default.")
			print("+ If 'True', extra normal units (whose grades there's already 2+ cards of) are sent back during mulligan,")
			print("+ risking drawing back triggers in order to aggressively look for MISSING 'ride_tg' (if all 'ride_tg' are\n"
				  "+ in hand then it behaves as though it was 'False'). If 'False', it keeps said normal units.")
		elif token == "gift":
			print("\n+ OPTIONAL field. If included, the line after 'gift:' should contain your gift's name.")
			print("+ Only relevant if the gift's name is 'accel2', which draws a card upon riding a gifted unit.")
		elif token == "keep":
			print("\n+ OPTIONAL field. If included, the line after 'keep:' should contain the names of the cards you\n"
				  "+ want to hard keep in your starting hand no matter what during mulligan, separated by spaces.")
			print("+\n+ > E.g. ' gbt midbunny alice '")
		elif token == "send":
			print("\n+ OPTIONAL field. If included, the line after 'send:' should contain the names of the cards you")
			print("+ want to send back into the deck no matter what during mulligan, separated by spaces.")
			print("+\n+ > E.g. ' chimera gunsalute '")
		elif token == "targets":
			print("\n+ OPTIONAL field. If included, after the line with 'targets:', you can have 1+ lines with the following format:")
			print("+\n+  	' <CardName> <Role> '\n+")
			print("+ CardName: the card's name.")
			print("+ Role: OPTIONAL. Can be 'ride_tg' (never want to call to rear), 'call_tg' (last resort to ride if grade stuck)")
			print("+       or blank. If left blank then the card does not fit into either category but is still important.")
			print("+\n+ You should include in 'targets' cards whose 'Role' you can generalize and/or cards that are typically necessary,")
			print("+ e.g. cards that create an advantage or prepare setup. This information helps the simulator approximate real games.")
			print("+\n+ > E.g. 1:\n+ 'gbt     ride_tg \n+  alice   call_tg\n+  midbunny'")
			print("+\n+ > E.g. 2:\n+ 'gancelot  ride_tg\n+  blaster_blade'")
			print("+\n+ > E.g. 3:\n+ 'AzureDragon        ride_tg\n+  IlluminalDragon\n+  ScarletBird        call_tg\n+  BrutalJack'")
		elif token == "deck":
			print("\n+ After the line with 'deck:' should follow 49 lines, one for each card in your deck, except for the starter unit.\n"
				  "+ The starting unit slot is exclusive to")
			print("+\n+  	Wallboy the Hierophant\n+")
			print("+ which draws a card when rode upon. Do NOT include your own starter unless you want the deck to have 51 cards.")
			print("+ Each of the 49 lines must have the following format:")
			print("+\n+  	<NrCopies> <CardName> <grade> <type> [<gift>]\n+")
			print("+   NrCopies: number of copies of this card to include in the deck.")
			print("+   CardName: you guessed it, it's the card's name. Pick a name you like with NO spaces in it.")
			print("+   grade:    you guessed it again, it's the card's grade (0 to 5).")
			print("+   type:     can be 'critical_trigger', 'heal_trigger', 'draw_trigger', 'front_trigger', 'order' or 'normal_unit'.")
			print("+   gift:     can be blank. Only relevant if it is set to 'accel' (and the 'gift' field in the FILE is 'accel2').")
		elif token == 'back':
			print("\n+ I-It's not like i wanted to help you or anything b-baka!!1 >///<")
			break
		else:
			print("\n+ Invalid command baaaaka >///<")
		print("+ + + + + + +")
		token = input(prompt_str).lower()
	print("+ + + + + + +")


if __name__ == '__main__':
	main()
