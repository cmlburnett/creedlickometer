import csv
import datetime
import os

from matplotlib import pyplot
import matplotlib

import numpy as np

class StatBot:
	"""
	Do a bunch of basic stats on data
	"""
	def __init__(self, dat):
		self.Data = list(dat)
		self.Length = len(self.Data)
		self.Sum = sum(self.Data)

		if self.Length == 0:
			self.Minimum = None
			self.Maximum = None
			self.MinMax = None
			self.Span = None

			self.Mean = None
			self.Quartile25 = None
			self.Median = None
			self.Quartile75 = None
		else:
			self.Minimum = min(self.Data)
			self.Maximum = max(self.Data)
			self.MinMax = (self.Minimum, self.Maximum)
			self.Span = self.Maximum - self.Minimum
			self.Mean = self.Sum / self.Length

			q = np.quantile(self.Data, [0.25,0.5,0.75])
			self.Quartile25 = q[0]
			self.Median = q[1]
			self.Quartile75 = q[2]

class CreedLickometer:
	def __init__(self, fname):
		self.Filename = fname

		# Integer of the programmed device ID
		self.DeviceID = None

		# Tuples of (minimum,maximum) values for datetime and milliseconds values
		self.Spandt = None
		self.Spanms = None

		# Raw data of (datetime, milliseconds integer, Beam open, delta)
		# where Beam open is True == beam opened, False == beam closed
		# and delta == change from prior state (either a bout time or interbout time)
		self.Lefts = None
		self.Rights = None

		# List of bout deltas
		self.LeftBouts = None
		self.RightBouts = None

		# List of intebout deltas
		self.LeftInterbouts = None
		self.RightInterbouts = None

		# Dictionary mapping datetime by minute to bout deltas
		self.LeftVsTime = None
		self.RightVsTime = None

		# Cumulative data
		self.LeftCumulative = None
		self.RightCumulative = None

		# Define the boundaries of time
		self.MinimumDatetime = None
		self.MinimumMillseconds = None
		self.MaximumDatetime = None
		self.MaximumMillseconds = None

	def Load(self):
		"""
		Load a CSV data file without processing
		"""

		lefts = []
		rights = []

		with open(self.Filename, 'r') as f:
			r = csv.reader(f)
			header = None
			for row in r:
				if header is None:
					header = r
					continue

				dt = datetime.datetime.strptime(row[0], '%m/%d/%Y %H:%M')
				ms = int(row[1])
				self.DeviceID = int(row[2])
				left = int(row[3])
				right = int(row[4])

				if not len(lefts) and not len(rights):
					if left == 1 and right == 1:
						lefts.append( (dt,ms,False,None) )
						rights.append( (dt,ms,False,None) )
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
						lefts.append( (dt,ms,True, delta) )

					# (3)
					elif lefts[-1][2] == True and left == 1:
						delta = ms - lefts[-1][1]
						lefts.append( (dt,ms,False, delta) )
					else:
						pass

					# (2)
					if rights[-1][2] == False and right == 0:
						delta = ms - rights[-1][1]
						rights.append( (dt,ms,True, delta) )

					# (3)
					elif rights[-1][2] == True and right == 1:
						delta = ms - rights[-1][1]
						rights.append( (dt,ms,False, delta) )
					else:
						pass

		self.Lefts = lefts
		self.Rights = rights

	def TrimBefore(self, dt):
		"""Trime all data before datetime @dt"""
		raise NotImplementedError

	@staticmethod
	def Merge(self, a, b):
		raise NotImplementedError

	def Process(self):
		"""
		Process the raw data in Lefts & Rights into the various parts.
		"""

		self.LeftBouts = []
		self.RightBouts = []

		self.LeftInterbouts = []
		self.RightInterbouts = []

		self.LeftVsTime = {}
		self.RightVsTime = {}

		self.LeftCumulative = []
		self.RightCumulative = []

		# Process Bout, Interbout, VsTimes and Cumulative data
		left_t = 0.0
		right_t = 0.0
		for dt,ms,beam,delta in self.Lefts:
			if delta is None: continue

			# Make sure both start at time zero
			if not len(self.LeftCumulative):
				self.LeftCumulative.append( (dt,left_t) )

			if beam == True:
				self.LeftInterbouts.append(delta)
				self.LeftCumulative.append( (dt,left_t) )
			else:
				self.LeftBouts.append(delta)

				left_t += delta
				self.LeftCumulative.append( (dt,left_t) )
				if dt not in self.LeftVsTime:
					self.LeftVsTime[dt] = []
				self.LeftVsTime[dt].append(delta)

		for dt,ms,beam,delta in self.Rights:
			if delta is None: continue

			if not len(self.RightCumulative):
				self.RightCumulative.append( (dt,right_t) )

			if beam == True:
				self.RightInterbouts.append(delta)
				self.RightCumulative.append( (dt,right_t) )
			else:
				self.RightBouts.append(delta)

				right_t += delta
				self.RightCumulative.append( (dt,right_t) )
				if dt not in self.RightVsTime:
					self.RightVsTime[dt] = []
				self.RightVsTime[dt].append(delta)

		# Not the most efficient way but easy to write
		mindt = min(map(lambda _:_[0], self.Lefts + self.Rights))
		maxdt = max(map(lambda _:_[0], self.Lefts + self.Rights))
		minms = min(map(lambda _:_[1], self.Lefts + self.Rights))
		maxms = max(map(lambda _:_[1], self.Lefts + self.Rights))

		# Set the spans of the time data
		self.Spandt = (mindt, maxdt)
		self.Spanms = (minms, maxms)

		# Ensure start and end are the same
		self.LeftCumulative.insert(0, (mindt, 0.0) )
		self.LeftCumulative.append( (maxdt, left_t) )
		self.RightCumulative.insert(0, (mindt, 0.0) )
		self.RightCumulative.append( (maxdt, right_t) )

		# Sort the data
		self.LeftBouts.sort()
		self.LeftInterbouts.sort()
		self.RightBouts.sort()
		self.RightInterbouts.sort()

		# Calculate all the stats
		self.LeftBoutStats = StatBot(self.LeftBouts)
		self.LeftInterboutStats = StatBot(self.LeftInterbouts)

		self.RightBoutStats = StatBot(self.RightBouts)
		self.RightInterboutStats = StatBot(self.RightInterbouts)

	def PlotVsTime(self, fname):
		fig,axes = pyplot.subplots(2)

		axes[0].set_ylabel("Left (# Bouts)")
		axes[1].set_ylabel("Right (# Bouts)")
		axes[1].set_xlabel("Time (min)")
		fig.autofmt_xdate()

		start = self.Spandt[0]
		end = self.Spandt[1]

		keys = list(self.LeftVsTime.keys())
		keys.sort()

		x = []
		y = []
		for minute in range(0, int((end-start).total_seconds()/60)+1):
			dt = start + datetime.timedelta(minutes=minute)
			x.append(dt)
			if dt in keys:
				y.append(len(self.LeftVsTime[dt]))
			else:
				y.append(0)

		axes[0].plot(x, y)

		keys = list(self.RightVsTime.keys())
		keys.sort()
		x = []
		y = []
		for minute in range(0, int((end-start).total_seconds()/60)+1):
			dt = start + datetime.timedelta(minutes=minute)
			x.append(dt)
			if dt in keys:
				y.append(len(self.RightVsTime[dt]))
			else:
				y.append(0)
		axes[1].plot(x, y)

		fig.savefig(fname)

	def PlotCumulative(self, fname):
		fig,axes = pyplot.subplots(1)
		fig.autofmt_xdate()

		axes.set_xlabel("Time (ms)")
		axes.set_ylabel("Cumulative Time (min)")

		x = [_[0] for _ in self.LeftCumulative]
		y = [_[1] for _ in self.LeftCumulative]
		axes.plot(x,y, 'r', label="Left")

		x = [_[0] for _ in self.RightCumulative]
		y = [_[1] for _ in self.RightCumulative]
		axes.plot(x,y, 'b', label="Right")

		axes.legend(loc="lower right")

		fig.savefig(fname)

def foo(fname, o):
	if True:
		print("================ LEFT BOUTS ================")
		print(o.LeftBouts)
		print("================ RIGHT BOUTS ================")
		print(o.RightBouts)
		print("================ LEFT INTER BOUTS ================")
		print(o.LeftInterbouts)
		print("================ RIGHT INTER BOUTS ================")
		print(o.RightInterbouts)

	print("================ N =================")
	print("Left bout N:              %d" % o.LeftBoutStats.Length)
	print("Left inter bout N:        %d" % o.LeftInterboutStats.Length)
	print("Right bout N:             %d" % o.RightBoutStats.Length)
	print("Right inter bout N:       %d" % o.RightInterboutStats.Length)

	print("================ MIN/MAX =================")
	if o.LeftBoutStats.Length:
		print("Left bout MIN/MAX:        %d, %d" % o.LeftBoutStats.MinMax)
		print("Left inter bout MIN/MAX:  %d, %d" % o.LeftInterboutStats.MinMax)
	if o.RightBoutStats.Length:
		print("Right bout MIN/MAX:       %d, %d" % o.RightBoutStats.MinMax)
		print("Right inter bout MIN/MAX: %d, %d" % o.RightInterboutStats.MinMax)

	print("================ MEAN =================")
	if o.LeftBoutStats.Length:
		print("Left bout mean:           %.2f ms" % o.LeftBoutStats.Mean)
		print("Left inter bout mean:     %.2f ms" % o.LeftInterboutStats.Mean)

	if o.RightBoutStats.Length:
		print("Right bout mean:          %.2f ms" % o.RightBoutStats.Mean)
		print("Right inter bout mean:    %.2f ms" % o.RightInterboutStats.Mean)

	print("================ MEDIAN =================")
	if o.LeftBoutStats.Length:
		print("Left bout median:        %.2f ms" % o.LeftBoutStats.Median)
		print("Left inter bout median:  %.2f ms" % o.LeftInterboutStats.Median)

	if o.RightBoutStats.Length:
		print("Right bout median:        %.2f ms" % o.RightBoutStats.Median)
		print("Right inter bout median:  %.2f ms" % o.RightInterboutStats.Median)



fnames = [_ for _ in os.listdir("../../test/") if not _.startswith('.') and _.lower().endswith('.csv')]
fnames.sort()

pyplot.rcParams["figure.figsize"] = [10.0, 4.0]
pyplot.rcParams["figure.autolayout"] = True
pyplot.rcParams["xtick.labelsize"] = 'small'

for fname in fnames:
	fname = '../../test/' + fname
	print("\n\n")
	print(fname)
	o = CreedLickometer(fname)
	o.Load()
	o.Process()

	foo(fname, o)

	o.PlotVsTime(fname + "-vstime.png")
	o.PlotCumulative(fname + "-cumulative.png")

