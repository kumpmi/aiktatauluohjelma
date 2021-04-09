import datetime as dt
 
from django.db import models
from django.utils import timezone

import collections

class Apu(models.Model):
	aika = models.TimeField()
	kuvaus = models.CharField(max_length= 15)
	
	def __str__(self):
		return self.aika.strftime("%H:%M:%S") + " " + self.kuvaus

class Kone(models.Model):
	nimi = models.CharField(max_length= 15)
	aloitusindeksi = models.PositiveIntegerField()
	kaynnistysaika = models.TimeField()
	siirtyman_kesto = models.PositiveIntegerField()

	def __str__(self):
		return self.nimi

class Arm2800(models.Model):
	indeksi = models.PositiveIntegerField()

	purkuvaiheen_pituus = models.PositiveIntegerField()
	odotusvaiheen_pituus = models.PositiveIntegerField()
	konevaiheen_pituus = models.PositiveIntegerField()
	jaahdytysvaiheen_pituus = models.PositiveIntegerField()
	purun_aikatarve = models.PositiveIntegerField()
	kaksi = models.BooleanField(default=False)

	def __str__(self):
		return "2800_varsi_" + str(self.indeksi) + "_" + str(self.purkuvaiheen_pituus) + "_" + str(self.odotusvaiheen_pituus) + "_" + str(self.konevaiheen_pituus) + "_" + str(self.purun_aikatarve) + "_" + str(self.kaksi)

class Arm2300(models.Model):
	indeksi = models.PositiveIntegerField()

	vaiheen_pituus = models.PositiveIntegerField()
	purun_aikatarve = models.PositiveIntegerField()
	kaksi = models.BooleanField(default=False)

	def __str__(self):
		return "2300_varsi_" + str(self.indeksi) + "_" + str(self.vaiheen_pituus) + "_" + str(self.purun_aikatarve) + "_" + str(self.kaksi)

class Scheduling():
	@classmethod
	def create_fix_schedule(self, fix_arms, start, index, siirron_kesto):
		indexes = collections.deque(["0", "1", "2"])
		indexes.rotate(-index)
		alku = start
		fix_schedules = collections.deque([[],[],[]])
		fix_schedule = []
		alku = alku.add(Interval(seconds= 0))
		last_finish = alku
		n = 1
		for i in indexes:
			arm_i = int(i)
			arm = fix_arms.get(indeksi= i)	
			manual_time = arm.vaiheen_pituus
			operating_time = arm.vaiheen_pituus*2+3*siirron_kesto
			
			while(last_finish.isEarlierThan(Time(hours= 24))):
				fix_schedules[arm_i].append(Operating_interval(arm_i, last_finish, last_finish.add(Interval(seconds= manual_time)), False, arm.kaksi, "2300", Time(), Time(), ""))
				last_finish = last_finish.add(Interval(seconds= operating_time)).add(Interval(seconds= manual_time))

			last_finish = alku.add(Interval(seconds= (manual_time + operating_time) / 3 * n))
			n += 1

		fix_schedules.rotate(-index)
		i = 0
		while(i < len(fix_schedules[0])-1):
			for schedule in fix_schedules:
				fix_schedule.append(schedule[i])
			i += 1

		string = ""
		string += "["
		for time in fix_schedule:
			string += time.to_json()
			if time != fix_schedule[-1]:
				string += ","
		string += "]"

		return [fix_schedule, string]
	
	@classmethod
	def create_ind_schedule(self, ind_arms, start, index, siirron_kesto):
		indexes = collections.deque(["0", "1", "2", "3"])
		indexes.rotate(-index)
		alku = start
		ind_schedules = collections.deque([[],[],[],[]])
		ind_schedule = []
		alku = alku.add(Interval(seconds= 0))
		last_finish = alku

		n = 1
		for i in indexes:
			arm_i = int(i)
			arm = ind_arms.get(indeksi= i)
			manual_time = arm.purkuvaiheen_pituus
			wait_time = arm.odotusvaiheen_pituus
			operating_time = arm.konevaiheen_pituus + arm.jaahdytysvaiheen_pituus+3*siirron_kesto
			total_time = manual_time + operating_time + wait_time + siirron_kesto

			while(last_finish.isEarlierThan(Time(hours= 24))):
				ind_schedules[arm_i].append(Operating_interval(arm_i, last_finish, last_finish.add(Interval(seconds= manual_time + wait_time)), False, arm.kaksi, "2800", Time(), Time(), ""))
				last_finish = last_finish.add(Interval(seconds= total_time))

			last_finish = alku.add(Interval(seconds= total_time / 4 * n))
			n += 1


		ind_schedules.rotate(-index)
		i = 0
		while(i < len(ind_schedules[0])-2):
			for schedule in ind_schedules:
				ind_schedule.append(schedule[i])
			i += 1

		string = ""
		string += "["
		for time in ind_schedule:
			string += time.to_json()
			if time != ind_schedule[-1]:
				string += ","
		string += "]"

		return [ind_schedule, string]
	
	@classmethod		
	def add_conflicts_to_schedules(self, fix_schedule, ind_schedule, fix_arms, ind_arms):
		operator_time_fix = []
		operator_time_ind = []

		i = 0
		for fix_time in fix_schedule:
			fix_pa = Interval(seconds = fix_arms[fix_time.arm_index].purun_aikatarve)
			if i%2 == 0:
				fix_time.manual_start = fix_time.start
				fix_time.manual_stop = fix_time.start.add(fix_pa)
			else:
				fix_time.manual_start = fix_time.stop.subtract(fix_pa)
				fix_time.manual_stop = fix_time.stop
			operator_time_fix.append([fix_time.manual_start, fix_time.manual_stop, "fix"])
			print(fix_time.manual_start.desc(), fix_time.manual_stop.desc(), fix_time.start.desc(), fix_time.stop.desc())
			i += 1
		operator_time_fix.append([Time(23,59,59), Time(23,59,59), "fix"])
		operator_time_fix.append([Time(23,59,59), Time(23,59,59), "fix"])
		
		for time in operator_time_fix:
			print(time[0].desc() + " - " + time[1].desc() + " " + time[2])

		operator_time_ind.append([Time(00,00,00), Time(00,00,00), "ind"])
		i = 0
		for ind_time in ind_schedule:
			time_found = False
			f_i = 0
			ind_pa = Interval(seconds = ind_arms[ind_time.arm_index].purun_aikatarve)
			j = 0
			for f_i in range(len(fix_schedule)):
				fix_time = fix_schedule[f_i]
				if fix_time.stop.isEarlierThan(ind_time.start):
					print("pass ennen")
					j += 1
					pass
				elif fix_time.start.isLaterThan(ind_time.stop):
					print("pass jälkeen")
					pass
				elif operator_time_fix[j][1].isEarlierThan(ind_time.start) and operator_time_fix[j + 1][0].isLaterThan(ind_time.start.add(ind_pa)) and operator_time_ind[-1][1].add(ind_pa).isEarlierThan(ind_time.stop):
					print("LÖYTYI 1")
					if operator_time_ind[-1][1].isLaterThan(ind_time.start) and operator_time_ind[-1][1].add(ind_pa).isEarlierThan(operator_time_fix[j + 1][0]):
						ind_time.manual_start = operator_time_ind[-1][1]
						ind_time.manual_stop = operator_time_ind[-1][1].add(ind_pa)
						break		
					else:	
						ind_time.manual_start = ind_time.start
						ind_time.manual_stop = ind_time.start.add(ind_pa)	
						time_found = True					
						break
				elif operator_time_fix[j + 1][1].isEarlierThan(ind_time.stop.subtract(ind_pa)) and operator_time_fix[j + 2][0].isLaterThan(ind_time.stop) and operator_time_ind[-1][1].add(ind_pa).isEarlierThan(ind_time.stop):
					print("LÖYTYI 2")
					ind_time.manual_start = ind_time.stop.subtract(ind_pa)
					ind_time.manual_stop = ind_time.stop					
					time_found = True					
					break

			operator_time_ind.append([ind_time.manual_start, ind_time.manual_stop, "ind"])
			operator_time_ind.sort(key= lambda t: Time.seconds_midnight(t[0]))

			if time_found == False:
				if ind_time.kaksi == True:
					ind_time.conflict = True
					print("Konflikti!")	
				ind_time.manual_start = ind_time.start
				ind_time.manual_stop = ind_time.start.add(ind_pa)
			i += 1

		for time in operator_time_ind:
			operator_time_fix.append(time)
		operator_time_fix.sort(key= lambda t: Time.seconds_midnight(t[0]))
		for time in operator_time_fix:
			print(time[0].desc() + " - " + time[1].desc() + " " + time[2] )

		fix_string = ""
		fix_string += "["
		for time in fix_schedule:
			if time != fix_schedule[0]:
				fix_string += ","
			fix_string += time.to_json()
		fix_string += "]"

		ind_string = ""
		ind_string += "["
		for time in ind_schedule:
			if time != ind_schedule[0]:
				ind_string += ","
			ind_string += time.to_json()
		ind_string += "]"

		return [fix_string, ind_string]

	@classmethod
	def get_conflicts(self, fix_schedule, ind_schedule, helps):
		help_conflicts = []
		for apu in helps:
			time = apu.aika
			start = Time(time.hour, time.minute, time.second)
			help_conflicts.append(Operating_interval(999, start, start, True, False, "Muu", start, start, "*" + apu.kuvaus + "*"))
		help_conflicts.sort(key= lambda t: Time.seconds_midnight(t.manual_start))

		ind_conflicts = []
		for time in ind_schedule:
			if time.conflict == True:
				time.info = "Aikataulu"
				ind_conflicts.append(time)
#			if time.kaksi == True:
#				time.info = "Tarvitaan kaksi"
#				ind_conflicts.append(time)

		fix_conflicts = []
		for time in fix_schedule:
			if time.conflict == True:
				time.info = "Aikataulu"
				fix_conflicts.append(time)
#			if time.kaksi == True:
#				time.info = "Tarvitaan kaksi"
#				fix_conflicts.append(time)
		conflicts = []

		while True:
			print(len(fix_conflicts), len(ind_conflicts), len(help_conflicts))
			if len(fix_conflicts) != 0:
				if len(ind_conflicts) != 0:
					if len(help_conflicts) != 0:
						if help_conflicts[0].manual_start.isEarlierThan(fix_conflicts[0].manual_start):
							conflicts.append(help_conflicts.pop(0))
						elif help_conflicts[0].manual_start.isEarlierThan(ind_conflicts[0].manual_start):
							conflicts.append(help_conflicts.pop(0))
						elif fix_conflicts[0].manual_start.isEarlierThan(ind_conflicts[0].manual_start):
							conflicts.append(fix_conflicts.pop(0))
						else:
							conflicts.append(ind_conflicts.pop(0))
					else:
						if fix_conflicts[0].manual_start.isEarlierThan(ind_conflicts[0].manual_start):
							conflicts.append(fix_conflicts.pop(0))
						else:
							conflicts.append(ind_conflicts.pop(0))
				else:
					if len(ind_conflicts) == 0:
						if len(help_conflicts) == 0:
							conflicts.append(fix_conflicts.pop(0))

			else:
				if len(ind_conflicts) != 0:
					if len(help_conflicts) != 0:
						if help_conflicts[0].manual_start.isEarlierThan(ind_conflicts[0].manual_start):
							conflicts.append(help_conflicts.pop(0))
						else:
							conflicts.append(ind_conflicts.pop(0))
					else:
						conflicts.append(ind_conflicts.pop(0))
				else:
					if len(help_conflicts) != 0:
						conflicts.append(help_conflicts.pop(0))
			if len(fix_conflicts) == 0 and len(ind_conflicts) == 0 and len(help_conflicts) == 0:
				break


		string = ""
		string += "["
		for time in conflicts:
			string += time.to_json()
			string += ","
		string = string[:-1]
		string += "]"

		return [conflicts, string]

class Time:
	def __init__(self, hours=0, minutes=0, seconds=0):
		h = hours
		m = minutes
		s = seconds

		smod = s%60
		m += s//60
		s = smod
		mmod = m%60
		h += m//60
		m = mmod

		self.hours = h
		self.minutes = m
		self.seconds = s

	@classmethod
	def now(self):
		n = dt.datetime.now()
		self.hours = n.hour
		self.minutes = n.minute
		self.seconds = n.second

		return self

#Returns a new time object:
	def add(self, Interval):
		h = self.hours + Interval.hours
		m = self.minutes + Interval.minutes
		s = self.seconds + Interval.seconds

		smod = s%60
		m += s//60
		s = smod
		mmod = m%60
		h += m//60
		m = mmod

		return Time(h, m, s)

	def subtract(self, Interval):
		h = self.hours - Interval.hours
		m = self.minutes - Interval.minutes
		s = self.seconds - Interval.seconds

		if s < 0:
			m -= 1
			s += 60 

		if m < 0:
			h -= 1
			m += 60 

		return Time(h, m, s)

	def isLaterThan(self, another_time):
		if self.hours > another_time.hours:
			return True
		elif self.hours == another_time.hours:
			if self.minutes > another_time.minutes:
				return True
			elif self.minutes == another_time.minutes:
				if self.seconds > another_time.seconds:
					return True
		return False

	def isEarlierThan(self, another_time):
		return not self.isLaterThan(another_time)

	def isBetween(self, another_time_1, another_time_2):
		if self.isLaterThan(another_time_1) and self.isEarlierThan(another_time_2):
			return True
		elif self.isEarlierThan(another_time_1) and self.isLaterThan(another_time_2):
			return True
		else:
			return False 

	@classmethod
	def seconds_midnight(self, time):
		return time.hours*60*60 + time.minutes*60 + time.seconds

	def desc(self):
		ret = "{:.0f}".format(self.hours).zfill(2) + ":"
		ret += "{:.0f}".format(self.minutes).zfill(2) + ":"
		ret += "{:.0f}".format(self.seconds).zfill(2)
		return ret

class Interval():
	def __init__(self, hours=0, minutes=0, seconds=0):
		h = hours
		m = minutes
		s = seconds

		smod = s%60
		m += s//60
		s = smod
		mmod = m%60
		h += m//60
		m = mmod

		self.hours = h
		self.minutes = m
		self.seconds = s

	def desc(self):
		return "dt, {:.0f}:{:.0f}:{:.0f}".format(self.hours, self.minutes, self.seconds)

class Operating_interval:
	def __init__(self, arm_index, start, stop, conflict, kaksi, armtype= "", manual_start= Time(), manual_stop= Time(), info= "", help_n = 0):
		self.start = start
		self.stop = stop
		self.manual_start = manual_start
		self.manual_stop = manual_stop
		self.conflict = conflict
		self.kaksi = kaksi
		self.arm_index = arm_index
		self.armtype = armtype
		self.info = info
		self.help_n = help_n

	def to_json(self):
		ret =  "{"
		ret += "\"arm_index\": \"{}\",".format(self.arm_index)
		ret += "\"start\": \"{}\",".format(self.start.desc())
		ret += "\"stop\": \"{}\",".format(self.stop.desc())
		ret += "\"manual_start\": \"{}\",".format(self.manual_start.desc())
		ret += "\"manual_stop\": \"{}\",".format(self.manual_stop.desc())
		ret += "\"kaksi\": \"{}\",".format(self.kaksi)
		ret += "\"info\": \"{}\",".format(self.info)
		ret += "\"help_n\": \"{}\"".format(self.help_n)
		ret += "}"
		return ret

	def desc(self): 
		c = "ei"
		if self.conflict == True:
			c = "kyllä"
		k = "ei"
		if self.kaksi == True:
			k = "kyllä"
		varsi = str(self.arm_index+1) + ", " + self.armtype
		ret =  "Purkuaika:\n" 
		ret += "    Varsi:            {}\n".format(varsi)
		ret += "    Alkaa:            {}\n".format(self.start.desc())
		ret += "    Loppuu:           {}\n".format(self.stop.desc())
		ret += "    Tekeminen alkaa:  {}\n".format(self.manual_start.desc())
		ret += "    Tekeminen loppuu: {}\n".format(self.manual_stop.desc())
		ret += "    Tarvitaan kaksi:  {}\n".format(k)
		ret += "    Konflikti         {}\n".format(c)
		return ret
