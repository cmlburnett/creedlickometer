import csv
import datetime
import itertools
import os

import openpyxl
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from matplotlib import pyplot
import matplotlib

import numpy as np

__all__ = ['StatBot', 'CreedLickometer']

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

		self.IsMerged = False
		self.IsLoaded = False
		self.IsProcessed = False

	def __repr__(self):
		return "<%s device=%s file=%s>" % (self.__class__.__name__, self.DeviceID, self.Filename)

	def Save(self, fname=None):
		"""
		Save the data to CSV file.
		Optional file name to save to (using this saves a copy and leaves self.Filename alone).
		Battery voltage data is discarded, so update original data files at your own peril.
		"""

		rows = []
		if not len(self.Rights) and not len(self.Lefts):
			# No data to write
			pass

		# No rights, just lefts
		elif not len(self.Rights):
			for row in self.Lefts:
				l = int(not row[2])
				r = 1
				rows.append( [row[0], row[1], self.DeviceID, l, r, 0.0] )

		# No lefts, only rights
		elif not len(self.Lefts):
			for row in self.Rights:
				l = 1
				r = int(not row[2])
				rows.append( [row[0], row[1], self.DeviceID, l, r, 0.0] )

		else:
			# Combine left and rights
			combo = [[dt,ms,int(not beam),None] for dt,ms,beam,delta in self.Lefts]
			combo +=[[dt,ms,None,int(not beam)] for dt,ms,beam,delta in self.Rights]
			# Sort by milliseconds
			combo.sort(key=lambda _:_[1])

			# Keep track of last left/right values to copy on rows in which it doesn't change
			l = 1
			r = 1
			for row in combo:
				# Update left/right value depending on if it was set or not
				if row[2] is not None:
					l = row[2]
				if row[3] is not None:
					r = row[3]

				rows.append((
					row[0].strftime("%Y-%m-%d %H:%M:%S"),
					row[1],
					self.DeviceID,
					l,
					r,
					0.0
				))

		header = ['YYYY-MM-DD hh:mm:ss', 'Millseconds', 'Device', 'LeftState', 'RightState', 'BatteryVoltage']

		# Overwrite file
		if fname is None:
			fname = self.Filename

		with open(fname, 'w') as f:
			w = csv.writer(f)
			w.writerow(header)

			for row in rows:
				w.writerow(row)

	def Load(self):
		"""
		Load a CSV data file without processing
		"""

		lefts = []
		rights = []

		with open(self.Filename, 'r') as f:
			r = csv.reader(f)
			for row in r:
				# Header row, disregard
				if row[0].startswith("YYYY"):
					continue

				try:
					dt = datetime.datetime.strptime(row[0], '%m/%d/%Y %H:%M')
				except ValueError:
					dt = datetime.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')

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
		self.IsLoaded = True

	def TrimBefore(self, truncate_dt):
		"""
		Trim all data before datetime @truncate_dt.
		"""

		if not self.IsLoaded:
			self.Load()

		# Pull out trimmed entries
		lefts = []
		rights = []

		for dt,ms,beam,delta in self.Lefts:
			if dt >= truncate_dt:
				lefts.append( (dt,ms,beam,delta) )
		for dt,ms,beam,delta in self.Rights:
			if dt >= truncate_dt:
				rights.append( (dt,ms,beam,delta) )

		# Edge case of the truncation date being in the middle of a bout
		# If it starts in the beam broken state ([2] == True) then exclude it
		if lefts[0][2]:
			del lefts[0]
		if rights[0][2]:
			del rights[0]

		# Create new container for the data, assign it, and pretend it's loaded
		o = CreedLickometer(None)
		o.DeviceID = self.DeviceID
		o.Lefts = lefts
		o.Rights = rights
		o.IsLoaded = True
		o.IsMerged = True

		return o

	def TrimAfter(self, truncate_dt):
		"""
		Trim all data after datetime @truncate_dt.
		"""

		if not self.IsLoaded:
			self.Load()

		# Pull out trimmed entries
		lefts = []
		rights = []

		for dt,ms,beam,delta in self.Lefts:
			if dt <= truncate_dt:
				lefts.append( (dt,ms,beam,delta) )
		for dt,ms,beam,delta in self.Rights:
			if dt <= truncate_dt:
				rights.append( (dt,ms,beam,delta) )

		# Edge case of the truncation date being in the middle of a bout
		# If it starts in the beam broken state ([2] == True) then exclude it
		if lefts[-1][2]:
			lefts.pop()
		if rights[-1][2]:
			rights.pop()

		# Create new container for the data, assign it, and pretend it's loaded
		o = CreedLickometer(None)
		o.DeviceID = self.DeviceID
		o.Lefts = lefts
		o.Rights = rights
		o.IsLoaded = True
		o.IsMerged = True

		return o

	@staticmethod
	def Merge(a, b):
		"""
		Merge two data files @a and @b and return a new CreedLickometer instance
		"""

		# Ensure files are loaded
		if not a.IsLoaded:
			a.Load()
		if not b.IsLoaded:
			b.Load()

		# Ensure files are processed (I'm lazy and don't want to calculate Spandt myself)
		if not a.IsProcessed:
			a.Process()
		if not b.IsProcessed:
			b.Process()

		# Why would you merge files from different devices other than by accident?
		if a.DeviceID != b.DeviceID:
			raise ValueError("Merging files from two different devices (%d and %d)" % (a.DeviceID, b.DeviceID))

		# Flip file order if wrong
		if b.Spandt[0] >= a.Spandt[1]:
			# a <= b is correctly ordered as expected
			pass
		elif a.Spandt[0] > b.Spandt[1]:
			# b < a so swap them
			a,b = b,a
		else:
			raise ValueError("Unrecognized ordering of files: a=%s, b=%s" % (a.Spandt, b.Spandt))

		# Time gap between files
		gap = b.Spandt[0] - a.Spandt[1]

		# Not a halting error, just disregard data we can't finish processing
		if a.Lefts[-1][2]:
			print("First file (%s) left ends with beam broken, popping this off" % a.Filename)
			a.Lefts.pop()
		if b.Lefts[0][2]:
			print("Second file (%s) left starts with a beam broken, dequeueing it" % b.Filename)
			del b.Lefts[0]

		if a.Rights[-1][2]:
			print("First file (%s) right ends with beam broken, popping this off" % a.Filename)
			a.Rights.pop()
		if b.Rights[0][2]:
			print("Second file (%s) right starts with a beam broken, dequeueing it" % b.Filename)
			del b.Rights[0]

		# Expected gap given gap in seconds
		gapms = int(gap.total_seconds() * 1000 + 1000)
		startms = gapms + a.Spanms[1]
		deltams = startms - b.Spanms[0]

		# Aggregate lefts & rights together
		lefts = list(a.Lefts)
		rights = list(a.Rights)

		# Merge left & right data and adjust @b's milliseconds to account for the gap
		# This ensures that millseconds is increasing across the merged data sets
		for dt,ms,beam,delta in b.Lefts:
			lefts.append( (dt,ms+deltams,beam,delta) )
		for dt,ms,beam,delta in b.Rights:
			rights.append( (dt,ms+deltams,beam,delta) )

		# Create new container for the data, assign it, and pretend it's loaded
		o = CreedLickometer(None)
		o.DeviceID = a.DeviceID
		o.Lefts = lefts
		o.Rights = rights
		o.IsLoaded = True
		o.IsMerged = True
		o.Process()

		return o

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

		self.IsProcessed = True

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
		"""
		Plot bouts as a box plot.
		@limitextremes, if True, then the ultra extreme outliers are chopped off by fixing the y-axis limits.
		"""

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

			# Fudge the bounds a little just to add some padding
			ymin *= 0.95
			ymax *= 1.05

			axes.set_ylim((ymin,ymax))

		else:
			pass

		# SAVE IT
		fig.savefig(fname)
		pyplot.close()

	def PlotBoutHistogram_Overlap(self, fname, bins=25):
		"""
		Plot bouts as a histogram with @bins of data.
		Left and right data plots are shown on the same axes (overlapping).
		"""

		fig,axes = pyplot.subplots(1)
		fig.autofmt_xdate()
		fig.suptitle("Bout Histogram for %s" % fname)

		colors = ['blue', 'orange']
		axes.hist( [self.LeftBouts, self.RightBouts], bins=bins, color=colors, label=['Left', 'Right'])
		axes.set_xlabel('Bins of Time (ms)')
		axes.legend(loc='upper right')

		# SAVE IT
		fig.savefig(fname)
		pyplot.close()

	def PlotBoutHistogram_SideBySide(self, fname, bins=25):
		"""
		Plot bouts as a histogram with @bins of data.
		Left and right data plots are shown side-by-side as separate plots.
		"""

		fig,axes = pyplot.subplots(1,2)
		fig.autofmt_xdate()
		fig.suptitle("Bout Histogram for %s" % fname)

		axes[0].set_xlabel('Left (Bins of Time (ms))')
		axes[1].set_xlabel('Right (Bins of Time (ms))')
		axes[0].hist(self.LeftBouts, bins=bins, color='blue')
		axes[1].hist(self.RightBouts, bins=bins, color='orange')

		# SAVE IT
		fig.savefig(fname)
		pyplot.close()

	def PlotInterboutHistogram_Overlap(self, fname, bins=25):
		"""
		Plot interbouts as a histogram with @bins of data.
		Left and right data plots are shown on the same axes (overlapping).
		"""

		fig,axes = pyplot.subplots(1)
		fig.autofmt_xdate()
		fig.suptitle("Interbout Histogram for %s" % fname)

		colors = ['blue', 'orange']
		axes.hist( [self.LeftInterbouts, self.RightInterbouts], bins=bins, color=colors, label=['Left', 'Right'])
		axes.set_xlabel('Bins of Time (ms)')
		axes.legend(loc='upper right')

		# SAVE IT
		fig.savefig(fname)
		pyplot.close()

	def PlotInterboutHistogram_SideBySide(self, fname, bins=25):
		"""
		Plot interbouts as a histogram with @bins of data.
		Left and right data plots are shown side-by-side as separate plots.
		"""

		fig,axes = pyplot.subplots(1,2)
		fig.autofmt_xdate()
		fig.suptitle("Interbout Histogram for %s" % fname)

		axes[0].set_xlabel('Left (Bins of Time (ms))')
		axes[1].set_xlabel('Right (Bins of Time (ms))')
		axes[0].hist(self.LeftInterbouts, bins=bins, color='blue')
		axes[1].hist(self.RightInterbouts, bins=bins, color='orange')

		# SAVE IT
		fig.savefig(fname)
		pyplot.close()

	@staticmethod
	def PlotStatsTable(fname, *objs):
		wb = Workbook()
		ws = wb.active
		ws.title = "Stats"

		# Section labels
		ws['A1'] = 'Bouts'
		ws['A23'] = 'Interbouts'

		# Same row headers for bouts and interbouts
		header = ['N', 'Sum', 'Min', 'Max', 'Mean', 'Q25', 'Q50', 'Q75', 'IQR']

		# Put in device IDs as columns for each section
		for pos in ([2,5], [24,5]): # E2 and E24
			for obj in objs:
				ws.cell(pos[0],pos[1]+0).value = obj.DeviceID
				pos[1] += 1

		# Make headers for each section
		for pos in ([3,2], [25,2]): #B3 and B25
			for h in header:
				# Header info
				ws.cell(pos[0]+0, pos[1]).value = h
				ws.cell(pos[0]+0, pos[1]+1).value = 'Left'
				ws.cell(pos[0]+1, pos[1]+1).value = 'Right'

				col_a = get_column_letter(pos[1]+2+1)
				col_b = get_column_letter(pos[1]+2+1 + len(objs)-1)

				#ws.cell(pos[0]+0, pos[1]+2).value = '=ttest(%s%d:%s%d, %s%d:%s%d, 2,1)' % (col_a,pos[0]+0, col_b,pos[0]+0, col_a,pos[0]+1, col_b,pos[0]+1)

				pos[0] += 2

		# Inject data
		for cnt,obj in enumerate(objs):
			# Increment row for each object
			pos = [3,5+cnt] # E3

			idx = 0

			left = obj.LeftBoutStats
			right = obj.RightBoutStats

			attrs = ['Length', 'Sum', 'Minimum', 'Maximum', 'Mean', 'Quartile25', 'Median', 'Quartile75', 'IQR']
			possnull = ['Minimum', 'Maximum', 'Mean', 'Quartile25', 'Median', 'Quartile75', 'IQR']
			for attr in attrs:
				l = getattr(left, attr)
				r = getattr(right, attr)

				if attr in possnull:
					ws.cell(pos[0]+idx+0, pos[1]).value = l or ""
					ws.cell(pos[0]+idx+1, pos[1]).value = r or ""
				else:
					ws.cell(pos[0]+idx+0, pos[1]).value = l
					ws.cell(pos[0]+idx+1, pos[1]).value = r
				idx += 2

		# Inject data
		for cnt,obj in enumerate(objs):
			# Increment row for each object
			pos = [25,5+cnt] # E3

			idx = 0

			left = obj.LeftInterboutStats
			right = obj.RightInterboutStats

			attrs = ['Length', 'Sum', 'Minimum', 'Maximum', 'Mean', 'Quartile25', 'Median', 'Quartile75', 'IQR']
			possnull = ['Minimum', 'Maximum', 'Mean', 'Quartile25', 'Median', 'Quartile75', 'IQR']
			for attr in attrs:
				l = getattr(left, attr)
				r = getattr(right, attr)

				if attr in possnull:
					ws.cell(pos[0]+idx+0, pos[1]).value = l or ""
					ws.cell(pos[0]+idx+1, pos[1]).value = r or ""
				else:
					ws.cell(pos[0]+idx+0, pos[1]).value = l
					ws.cell(pos[0]+idx+1, pos[1]).value = r
				idx += 2

		try:
			os.unlink(fname)
		except:
			pass
		wb.save(fname)
