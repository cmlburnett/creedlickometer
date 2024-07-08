import csv
import datetime
import os

from matplotlib import pyplot
import matplotlib

def load(fname):
	lefts = []
	rights = []

	lefts_bout_durations = []
	lefts_interbout_durations = []

	rights_bout_durations = []
	rights_interbout_durations = []

	# Plot # of bouts per minute of time
	left_vstime = {}
	right_vstime = {}

	# Cumulative bout time
	left_cumulative_time = 0.0
	left_cumulative = []
	right_cumulative_time = 0.0
	right_cumulative = []

	with open(fname, 'r') as f:
		r = csv.reader(f)
		header = None
		for row in r:
			if header is None:
				header = r
				continue

			dt = datetime.datetime.strptime(row[0], '%m/%d/%Y %H:%M')
			ms = int(row[1])
			devid = int(row[2])
			left = int(row[3])
			right = int(row[4])

			#print([dt, ms, devid, left, right])

			if not len(lefts) and not len(rights):
				if left == 1 and right == 1:
					lefts.append( (dt,ms,False) )
					rights.append( (dt,ms,False) )
				else:
					# Need to find a (1,1) row indicating neither are blocked
					continue
			else:
				# Scenarios:
				#  1) Beam open (False) and still is open (1)
				#  2) Beam open (False) and is closed (0) [MOUSE STARTS DRINKING]
				#  3) Beam closed (True) and is open (1) [MOUSE STOPS DRINKING]
				#  4) Beam closed (True) and still is closed (0)

				# (2)
				if lefts[-1][2] == False and left == 0:
					delta = ms - lefts[-1][1]
					lefts_interbout_durations.append(delta)
					lefts.append( (dt,ms,True, delta) )

					left_cumulative.append( (dt,left_cumulative_time) )

				# (3)
				elif lefts[-1][2] == True and left == 1:
					delta = ms - lefts[-1][1]
					lefts_bout_durations.append(delta)
					lefts.append( (dt,ms,False, delta) )

					if dt not in left_vstime:
						left_vstime[dt] = []
					left_vstime[dt].append(delta)

					left_cumulative_time += delta
					left_cumulative.append( (dt,left_cumulative_time) )
				else:
					pass

				# (2)
				if rights[-1][2] == False and right == 0:
					delta = ms - rights[-1][1]
					rights_interbout_durations.append(delta)
					rights.append( (dt,ms,True, delta) )

					right_cumulative.append( (dt,right_cumulative_time) )

				# (3)
				elif rights[-1][2] == True and right == 1:
					delta = ms - rights[-1][1]
					rights_bout_durations.append(delta)
					rights.append( (dt,ms,False, delta) )

					if dt not in right_vstime:
						right_vstime[dt] = []
					right_vstime[dt].append(delta)

					right_cumulative_time += delta
					right_cumulative.append( (dt,right_cumulative_time) )
				else:
					pass

	lefts_bout_durations.sort()
	lefts_interbout_durations.sort()
	rights_bout_durations.sort()
	rights_interbout_durations.sort()

	if False:
		print("================ LEFT BOUTS ================")
		for z in lefts_bout_durations:
			print(z)
		print("================ RIGHT BOUTS ================")
		for z in rights_bout_durations:
			print(z)

		print("================ LEFT INTER BOUTS ================")
		for z in lefts_interbout_durations:
			print(z)
		print("================ RIGHT INTER BOUTS ================")
		for z in rights_interbout_durations:
			print(z)
	if True:
		print("================ LEFT BOUTS ================")
		print(lefts_bout_durations)
		print("================ RIGHT BOUTS ================")
		print(rights_bout_durations)
		print("================ LEFT INTER BOUTS ================")
		print(lefts_interbout_durations)
		print("================ RIGHT INTER BOUTS ================")
		print(rights_interbout_durations)

	print("================ N =================")
	print("Left bout N:              %d" % len(lefts_bout_durations))
	print("Left inter bout N:        %d" % len(lefts_interbout_durations))
	print("Right bout N:             %d" % len(rights_bout_durations))
	print("Right inter bout N:       %d" % len(rights_interbout_durations))

	print("================ MIN/MAX =================")
	if len(lefts_bout_durations):
		print("Left bout MIN/MAX:        %d, %d" % (min(lefts_bout_durations),max(lefts_bout_durations)))
		print("Left inter bout MIN/MAX:  %d, %d" % (min(lefts_interbout_durations),max(lefts_interbout_durations)))
	if len(rights_bout_durations):
		print("Right bout MIN/MAX:       %d, %d" % (min(rights_bout_durations),max(rights_bout_durations)))
		print("Right inter bout MIN/MAX: %d, %d" % (min(rights_interbout_durations),max(rights_interbout_durations)))

	print("================ MEAN =================")
	if len(lefts_bout_durations):
		print("Left bout mean:           %.2f ms" % (sum(lefts_bout_durations)/len(lefts_bout_durations)))
		print("Left inter bout mean:     %.2f ms" % (sum(lefts_interbout_durations)/len(lefts_interbout_durations)))

	if len(rights_bout_durations):
		print("Right bout mean:          %.2f ms" % (sum(rights_bout_durations)/len(rights_bout_durations)))
		print("Right inter bout mean:    %.2f ms" % (sum(rights_interbout_durations)/len(rights_interbout_durations)))

	print("================ MEDIAN =================")
	if len(lefts_bout_durations):
		if len(lefts_bout_durations) % 2 == 0:
			_ = len(lefts_bout_durations)
			print("Left bout median:        %.2f ms" % (sum(lefts_bout_durations[_-1:_+1])/2))
		else:
			_ = len(lefts_bout_durations)
			print("Left bout median:        %.2f ms" % lefts_bout_durations[(_-1)//2])

		if len(lefts_interbout_durations) % 2 == 0:
			_ = len(lefts_interbout_durations)
			print("Left inter bout median:  %.2f ms" % (sum(lefts_interbout_durations[_-1:_+1])/2))
		else:
			_ = len(lefts_interbout_durations)
			print("Left inter bout median:  %.2f ms" % lefts_interbout_durations[(_-1)//2])

	if len(rights_bout_durations):
		if len(rights_bout_durations) % 2 == 0:
			_ = len(rights_bout_durations)
			print("Right bout median:        %.2f ms" % (sum(rights_bout_durations[_-1:_+1])/2))
		else:
			_ = len(rights_bout_durations)
			print("Right bout median:        %.2f ms" % rights_bout_durations[(_-1)//2])

		if len(rights_interbout_durations) % 2 == 0:
			_ = len(rights_interbout_durations)
			print("Right inter bout median:  %.2f ms" % (sum(rights_interbout_durations[_-1:_+1])/2))
		else:
			_ = len(rights_interbout_durations)
			print("Right inter bout median:  %.2f ms" % rights_interbout_durations[(_-1)//2])

	fig,axes = pyplot.subplots(2)

	axes[0].set_ylabel("Left (# Bouts)")
	axes[1].set_ylabel("Right (# Bouts)")
	axes[1].set_xlabel("Time (min)")
	fig.autofmt_xdate()

	# --------------------------------------------------------------------------------------
	# Plot # of bouts per time
	start = None
	if len(left_vstime.keys()):
		start = min(left_vstime.keys())
	if len(right_vstime.keys()):
		if start is None:
			start = min(right_vstime.keys())
		else:
			start = min(start, min(right_vstime.keys()))

	end = None
	if len(left_vstime.keys()):
		end = max(left_vstime.keys())
	if len(right_vstime.keys()):
		if end is None:
			end = max(right_vstime.keys())
		else:
			end = max(end, max(right_vstime.keys()))

	keys = list(left_vstime.keys())
	keys.sort()

	x = []
	y = []
	for minute in range(0, int((end-start).total_seconds()/60)+1):
		dt = start + datetime.timedelta(minutes=minute)
		x.append(dt)
		if dt in keys:
			y.append(len(left_vstime[dt]))
		else:
			y.append(0)

	axes[0].plot(x, y)

	keys = list(right_vstime.keys())
	keys.sort()
	x = []
	y = []
	for minute in range(0, int((end-start).total_seconds()/60)+1):
		dt = start + datetime.timedelta(minutes=minute)
		x.append(dt)
		if dt in keys:
			y.append(len(right_vstime[dt]))
		else:
			y.append(0)
	axes[1].plot(x, y)

	fig_fname = fname + "-vstime.png"
	fig.savefig(fig_fname)

	# --------------------------------------------------------------------------------------
	# --------------------------------------------------------------------------------------
	# Plot cumulative times

	fig,axes = pyplot.subplots(1)
	fig.autofmt_xdate()

	axes.set_xlabel("Time (ms)")
	axes.set_ylabel("Cumulative Time (ms)")

	x = [_[0] for _ in left_cumulative]
	y = [_[1] for _ in left_cumulative]
	axes.plot(x,y, 'r', label="Left")

	x = [_[0] for _ in right_cumulative]
	y = [_[1] for _ in right_cumulative]
	axes.plot(x,y, 'b', label="Right")

	axes.legend(loc="lower right")

	fig_fname = fname + "-cumulative.png"
	fig.savefig(fig_fname)



fnames = [_ for _ in os.listdir("../../test/") if not _.startswith('.') and _.lower().endswith('.csv')]
fnames.sort()

pyplot.rcParams["figure.figsize"] = [10.0, 4.0]
pyplot.rcParams["figure.autolayout"] = True
pyplot.rcParams["xtick.labelsize"] = 'small'

for fname in fnames:
	print("\n\n")
	print(fname)
	load("../../test/" + fname)

