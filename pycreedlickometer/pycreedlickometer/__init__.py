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
			self.IQR = None
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
			self.IQR = q[2]-q[0]

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
		"""
		Merge two data files @a and @b and return a new CreedLickometer instance
		"""
		raise NotImplementedError

	def Process(self):
		"""
		Process the raw data in Lefts & Rights into the various parts.
		"""

		# Clear everything
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

	def PlotVsTime(self, fname, minutes=1):
		"""
		Plot bouts against time. Bouts are grouped by the minute.
		Set @minutes to something other than 1 to pre-group them into larger groups
		"""

		fig,axes = pyplot.subplots(2)
		fig.suptitle("VsTime for %s" % fname)

		axes[0].set_ylabel("Left (# Bouts)")
		axes[1].set_ylabel("Right (# Bouts)")
		axes[1].set_xlabel("Time (min)")
		fig.autofmt_xdate()

		if minutes != 1:
			raise NotImplementedError("Minutes group not implemented yet")

		start = self.Spandt[0]
		end = self.Spandt[1]

		# -------- LEFT --------
		# Get all the datetime objects and sort them
		keys = list(self.LeftVsTime.keys())
		keys.sort()

		# X data is datetime values
		# Y data is bout counts per time
		xl = []
		yl = []
		# Iterate over the whole time so that zeroes can be injected to plot nicely
		for minute in range(0, int((end-start).total_seconds()/60)+1):
			dt = start + datetime.timedelta(minutes=minute)
			xl.append(dt)
			if dt in keys:
				yl.append(len(self.LeftVsTime[dt]))
			else:
				# If there isn't a data point at this time, then there were zero bouts
				yl.append(0)


		# -------- RIGHT --------
		# Should mirror left except by the use of RightVsTime instead
		keys = list(self.RightVsTime.keys())
		keys.sort()

		xr = []
		yr = []
		for minute in range(0, int((end-start).total_seconds()/60)+1):
			dt = start + datetime.timedelta(minutes=minute)
			xr.append(dt)
			if dt in keys:
				yr.append(len(self.RightVsTime[dt]))
			else:
				yr.append(0)

		# Want y-axis on both to match
		maxy = max(max(yl), max(yr))
		axes[0].set_ylim(0,maxy)
		axes[1].set_ylim(0,maxy)

		axes[0].plot(xl, yl)
		axes[1].plot(xr, yr)

		# SAVE IT
		fig.savefig(fname)
		pyplot.close()

	def PlotBoutRepetitions(self, fname, minutes=1):
		"""
		Plot a cumulative bout count for each tube that is reset when the other tube is used.
		"""

		fig,axes = pyplot.subplots(2)
		fig.suptitle("Bout Repititions for %s" % fname)

		axes[0].set_ylabel("Left (# Bouts)")
		axes[1].set_ylabel("Right (# Bouts)")
		axes[1].set_xlabel("Time (min)")
		fig.autofmt_xdate()

		if minutes != 1:
			raise NotImplementedError("Minutes group not implemented yet")

		start = self.Spandt[0]
		end = self.Spandt[1]

		# -------- LEFT vs RIGHT --------
		# Count number of left bouts that is reset when a right bout is encountered
		# Get all the datetime objects and sort them
		lkeys = list(self.LeftVsTime.keys())
		lkeys.sort()
		rkeys = list(self.RightVsTime.keys())
		rkeys.sort()

		# X data is datetime values
		# Y data is bout counts per time
		xl = []
		yl = []
		# Iterate over the whole time so that zeroes can be injected to plot nicely
		cnt = 0
		for minute in range(0, int((end-start).total_seconds()/60)+1):
			dt = start + datetime.timedelta(minutes=minute)
			xl.append(dt)
			if dt in rkeys:
				cnt = 0
				yl.append(cnt)

			elif dt in lkeys:
				cnt += 1
				yl.append(cnt)

			else:
				# If there isn't a data point at this time, then there were zero bouts
				yl.append(cnt)


		# -------- RIGHT vs LEFT --------
		# Count number of right bouts that is reset when a left bout is encountered
		# X data is datetime values
		# Y data is bout counts per time
		xr = []
		yr = []
		# Iterate over the whole time so that zeroes can be injected to plot nicely
		cnt = 0
		for minute in range(0, int((end-start).total_seconds()/60)+1):
			dt = start + datetime.timedelta(minutes=minute)
			xr.append(dt)
			if dt in lkeys:
				cnt = 0
				yr.append(cnt)

			elif dt in rkeys:
				cnt += 1
				yr.append(cnt)

			else:
				# If there isn't a data point at this time, then there were zero bouts
				yr.append(cnt)

		# Want y-axis on both to match
		maxy = max(max(yl), max(yr))
		axes[0].set_ylim(0,maxy)
		axes[1].set_ylim(0,maxy)

		axes[0].plot(xl, yl)
		axes[1].plot(xr, yr)

		# SAVE IT
		fig.savefig(fname)
		pyplot.close()

	def PlotCumulativeBoutTimes(self, fname):
		"""
		Plot cumulative bout times.
		"""

		fig,axes = pyplot.subplots(1)
		fig.autofmt_xdate()
		fig.suptitle("Cumulative Bout Times for %s" % fname)

		axes.set_xlabel("Time (ms)")
		axes.set_ylabel("Cumulative Time (min)")

		x = [_[0] for _ in self.LeftCumulative]
		y = [_[1] for _ in self.LeftCumulative]
		axes.plot(x,y, 'r', label="Left")

		x = [_[0] for _ in self.RightCumulative]
		y = [_[1] for _ in self.RightCumulative]
		axes.plot(x,y, 'b', label="Right")

		axes.legend(loc="lower right")

		# SAVE IT
		fig.savefig(fname)
		pyplot.close()

	def PlotBoutBoxplot(self, fname, limitextremes=True):
		fig,axes = pyplot.subplots(1)
		fig.autofmt_xdate()
		fig.suptitle("Box Plot for %s" % fname)

		axes.set_ylabel('BoutTime (ms)')
		axes.boxplot( [self.LeftBouts, self.RightBouts], labels=['Left', 'Right'])

		if limitextremes:
			# With extreme outliers, the box plot gets squished into nohting so this limits the y-axis
			# to the min/max data point or no more than the definition of "extreme outlier" of Q25-3*IQR or Q75+3*IQR
			# This will remove outliers from the plot bu that makes the plot more useful

			if self.LeftBoutStats.Length != 0 and self.RightBoutStats.Length != 0:
				ymin_l = max(self.LeftBoutStats.Minimum, self.LeftBoutStats.Quartile25 - 3*self.LeftBoutStats.IQR)
				ymin_r = max(self.RightBoutStats.Minimum, self.RightBoutStats.Quartile25 - 3*self.RightBoutStats.IQR)
				ymin = min(ymin_l, ymin_r)

				ymax_l = min(self.LeftBoutStats.Maximum, self.LeftBoutStats.Quartile75 + 3*self.LeftBoutStats.IQR)
				ymax_r = min(self.RightBoutStats.Maximum, self.RightBoutStats.Quartile75 + 3*self.RightBoutStats.IQR)
				ymax = max(ymax_l, ymax_r)

			elif self.LeftBoutStats.Length == 0:
				ymin = max(self.RightBoutStats.Minimum, self.RightBoutStats.Quartile25 - 3*self.RightBoutStats.IQR)
				ymax = min(self.RightBoutStats.Maximum, self.RightBoutStats.Quartile75 + 3*self.RightBoutStats.IQR)
			elif self.RightBoutStats.Length == 0:
				ymin = max(self.RightBoutStats.Minimum, self.RightBoutStats.Quartile25 - 3*self.RightBoutStats.IQR)
				ymax = min(self.RightBoutStats.Maximum, self.RightBoutStats.Quartile75 + 3*self.RightBoutStats.IQR)
			else:
				raise NotImplementedError("Plotting no data?")

			ymin *= 0.95
			ymax *= 1.05

			axes.set_ylim((ymin,ymax))

		else:
			pass

		# SAVE IT
		fig.savefig(fname)
		pyplot.close()

def printstats(fname, o):
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

	printstats(fname, o)

	o.PlotVsTime(fname + "-vstime.png")
	o.PlotBoutRepetitions(fname + "-boutrepititions.png")
	o.PlotCumulativeBoutTimes(fname + "-cumulativebouttimes.png")
	o.PlotBoutBoxplot(fname + '-boxplot.png')

