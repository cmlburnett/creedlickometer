import datetime
import functools
import os
import re
import subprocess

from matplotlib import pyplot
from pycreedlickometer import CreedLickometer, VolumeData, TimeData


def printstats(o):
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


pyplot.rcParams["figure.figsize"] = [10.0, 4.0]
pyplot.rcParams["figure.autolayout"] = True
pyplot.rcParams["xtick.labelsize"] = 'small'

def fnameparse(fname):
	r = re.compile("sip(\d+)_(\d{2})(\d{2})(\d{2})_(\d+)\.csv", flags=re.IGNORECASE)
	m = r.match(fname)

	devid = int(m.group(1))
	month = int(m.group(2))
	day = int(m.group(3))
	year = int(m.group(4))
	seq = int(m.group(5))

	return {
		'filename': fname, 
		'device': devid,
		'year': 2000 + year,
		'month': month,
		'day': day,
		'seq': seq,
		'sortkey': '%04d%02d%02d%04d' % (year,month,day,seq),
	}

def allfiles():
	# Volume data to include
	v = VolumeData()
	dt = datetime.datetime(2024,7,15, 13,35)
	v.AddFill(dt, 1, 13.0, 13.0)
	v.AddFill(dt, 3, 12.0, 13.5)
	v.AddFill(dt, 5, 13.0, 13.0)
	v.AddFill(dt, 6, 13.75, 12.5)
	v.AddFill(dt, 7, 13.5, 13.5)
	v.AddFill(dt, 8, 13.5, 13.5)
	v.AddFill(dt, 9, 13.0, 13.0)
	v.AddFill(dt, 12,13.5, 13.0)

	dt = datetime.datetime(2024,7,16, 11,00)
	v.AddMeasurement(dt, 1, 11.5, 11.0)
	v.AddMeasurement(dt, 3, 9.75, 11.75)
	v.AddMeasurement(dt, 5, 9.5, 12.5)
	v.AddMeasurement(dt, 6, 13.0, 10.0)
	v.AddMeasurement(dt, 7, 12.0, 12.5)
	v.AddMeasurement(dt, 8, 11.5, 12.5)
	v.AddMeasurement(dt, 9, 11.75, 10.5)
	v.AddMeasurement(dt, 12,13.0, 8.5)

	dt = datetime.datetime(2024,7,17, 11,00)
	v.AddMeasurement(dt, 1, 9.5, 10.5)
	v.AddMeasurement(dt, 3, 7.5, 10.5)
	v.AddMeasurement(dt, 5, 6.25, 12.5)
	v.AddMeasurement(dt, 6, 10.5, 8.5)
	v.AddMeasurement(dt, 7, 10.0, 12.5)
	v.AddMeasurement(dt, 8, 8.5, 12.5)
	v.AddMeasurement(dt, 9, 9.5, 10.0)
	v.AddMeasurement(dt, 12,13.0, 3.0)
	v.AddFill(dt, 12, None, 13.75)

	# Add light/dark cycle information
	tz = TimeData()
	tz.AddLightPhase( datetime.time(5,0,0), datetime.time(19,0,0) )
	tz.AddDarkPhase( datetime.time(19,0,0), datetime.time(5,0,0) )
	tz.Process()


	fnames = [_ for _ in os.listdir("./data/") if not _.startswith('.') and _.lower().endswith('.csv') and 'truncated' not in _]
	fnames.sort()

	found = {}
	for fname in fnames:
		z = fnameparse(fname)
		dev = z['device']

		if dev not in found:
			found[dev] = []
		found[dev].append(z)

	data = {}
	merged = []
	print('-'*80)
	print("Original data files:")
	for dev in sorted(found.keys()):
		print(dev)
		files = sorted(found[dev], key=lambda _:_['sortkey'])

		data[dev] = []

		for f in files:
			print("", f)
			o = CreedLickometer('./data/' + f['filename'])
			o.AddVolumeData(v)
			o.AddTimeData(tz)
			data[dev].append(o)

		# Get min/max dates for merged file names
		mind = min( [_['sortkey'] for _ in files] )
		maxd = max( [_['sortkey'] for _ in files] )

		m = functools.reduce(CreedLickometer.Merge, data[dev])
		m.Filename = "merged/SIP_%03d_%s-%s.csv" % (m.DeviceID, mind,maxd)
		m.Save()
		merged.append(m)

	print('-'*80)
	print("Merged files:")
	for m in merged:
		print('', m)
	print('-'*80)

	fnames = []
	for o in merged:
		print("\n\n")
		print(o.Filename)
		o.Process()

		#printstats(o)

		fname = o.Filename
		fnames.append(fname)
		o.PlotVsTime(fname + "-vstime.png")
		o.PlotBoutRepetitions(fname + "-boutrepititions.png")
		o.PlotCumulativeBoutTimes(fname + "-cumulativebouttimes.png")
		o.PlotCumulativeNormalizedVolume(fname + "-cumulativevolume.png")
		o.PlotBoutBoxplot(fname + '-boxplot.png')
		o.PlotBoutHistogram_Overlap(fname + '-bouthisto-overlap.png')
		o.PlotBoutHistogram_SideBySide(fname + '-bouthisto-sidebyside.png')
		o.PlotInterboutHistogram_Overlap(fname + '-interbouthisto-overlap.png')
		o.PlotInterboutHistogram_SideBySide(fname + '-interbouthisto-sidebyside.png')

	# Combine all plots together vertically (-append rather than +append)
	plots = ['vstime.png', 'boutrepititions.png', 'cumulativebouttimes.png', 'cumulativevolume.png', 'boxplot.png', 'bouthisto-overlap.png', 'bouthisto-sidebyside.png', 'interbouthisto-overlap.png', 'interbouthisto-sidebyside.png']
	for plot in plots:
		args = ['convert'] + ['%s-%s' % (_,plot)  for _ in fnames] + ['-append', plot]
		print(args)
		subprocess.run(args)

	# Combine stats into a table
	CreedLickometer.PlotStatsTable('stats.xlsx', *merged)

if __name__ == '__main__':
	allfiles()

