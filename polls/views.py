from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic

import datetime as dt

from .models import Scheduling, Arm2300, Arm2800, Time, Apu, Kone

def IndexView(request):
	fix_arms = Arm2300.objects.all()
	fix_time = Kone.objects.get(nimi= "kone_2300").kaynnistysaika
	fix_start = Time(fix_time.hour, fix_time.minute, fix_time.second)
	fix_index = Kone.objects.get(nimi= "kone_2300").aloitusindeksi
	fix_siirto = Kone.objects.get(nimi= "kone_2300").siirtyman_kesto

	ind_arms = Arm2800.objects.all()
	ind_time = Kone.objects.get(nimi= "kone_2800").kaynnistysaika
	ind_start = Time(ind_time.hour, ind_time.minute, ind_time.second)
	ind_index = Kone.objects.get(nimi= "kone_2800").aloitusindeksi
	ind_siirto = Kone.objects.get(nimi= "kone_2300").siirtyman_kesto
	helps = Apu.objects.all()

	fix_schedule = Scheduling.create_fix_schedule(fix_arms, fix_start, fix_index, fix_siirto)
#	print("FIX" , fix_schedule[1])
	ind_schedule = Scheduling.create_ind_schedule(ind_arms, ind_start, ind_index, ind_siirto)
#	print("IND" , ind_schedule[1])
	schedules = Scheduling.add_conflicts_to_schedules(fix_schedule[0], ind_schedule[0], fix_arms, ind_arms)
	conflicts = Scheduling.get_conflicts(fix_schedule[0], ind_schedule[0], helps)
	json = "{\"conflicts\":" + conflicts[1] + ",\"fix\":" + schedules[0] + ",\"ind\":" + schedules[1] + "}"
	print(json)
	return render(request, 'polls/main.html', {'data': json}) 

