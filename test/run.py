import datetime
import functools
import os
from matplotlib import pyplot
from pycreedlickometer import CreedLickometer, VolumeData, TimeData


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


pyplot.rcParams["figure.figsize"] = [10.0, 4.0]
pyplot.rcParams["figure.autolayout"] = True
pyplot.rcParams["xtick.labelsize"] = 'small'

def _getdata():
	# Volume data to include
	v = VolumeData()
	dt = datetime.datetime(2024,7,2, 14,0,0)
	v.AddFill(dt, 1, 15.0, 15.0)
	v.AddFill(dt, 2, 15.0, 15.0)
	v.AddFill(dt, 3, 14.5, 14.5)
	v.AddFill(dt, 4, 14.5, 14.5)
	v.AddFill(dt, 5, 13.7, 15.0)
	v.AddFill(dt, 6, 15.0, 13.6)

	dt = datetime.datetime(2024,7,3, 9,30,0)
	v.AddMeasurement(dt, 1, 14.0, 9.4)
	v.AddMeasurement(dt, 2, 13.5, 6.7)
	v.AddMeasurement(dt, 3, 14.0, 7.5)
	v.AddMeasurement(dt, 4, 14.5, 14.5)
	v.AddMeasurement(dt, 5, 13.5, 0.5)
	v.AddMeasurement(dt, 6, 15.0, 8.0)

	# Add light/dark cycle information
	tz = TimeData()
	tz.AddLightPhase( datetime.time(5,0,0), datetime.time(19,0,0) )
	tz.AddDarkPhase( datetime.time(19,0,0), datetime.time(5,0,0) )
	tz.Process()

	return v,tz

def allfiles():
	v,tz = _getdata()

	fnames = [_ for _ in os.listdir(".") if not _.startswith('.') and _.lower().endswith('.csv') and 'truncated' not in _ and 'cumulative' not in _]
	fnames.sort()

	for fname in fnames:
		print("\n\n")
		print(fname)
		o = CreedLickometer(fname)
		o.AddVolumeData(v)
		o.AddTimeData(tz)
		o.Load()
		o.Process()

		#printstats(fname, o)

		o.PlotVsTime(fname + "-vstime.png")
		o.PlotBoutRepetitions(fname + "-boutrepititions.png")
		o.PlotCumulativeBoutTimes(fname + "-cumulativebouttimes.png")
		o.PlotCumulativeNormalizedVolume(fname + "-cumulativevolume.png")
		o.PlotBoutBoxplot(fname + '-boxplot.png')
		o.PlotBoutHistogram_Overlap(fname + '-bouthisto-overlap.png')
		o.PlotBoutHistogram_SideBySide(fname + '-bouthisto-sidebyside.png')
		o.PlotInterboutHistogram_Overlap(fname + '-interbouthisto-overlap.png')
		o.PlotInterboutHistogram_SideBySide(fname + '-interbouthisto-sidebyside.png')

def merger():
	v,tz = _getdata()

	fnames = ['7-1 Overnight Device 2 pt 1.CSV', '7-1 Overnight Device 2 pt 2.CSV']

	a = CreedLickometer(fnames[0])
	a.AddVolumeData(v)
	a.AddTimeData(tz)

	b = CreedLickometer(fnames[1])
	b.AddVolumeData(v)
	b.AddTimeData(tz)

	fname = '7-1 Overnight Device 2 merged.CSV'
	c = CreedLickometer.Merge(a,b)

	c.PlotVsTime(fname + "-vstime.png")
	c.PlotBoutRepetitions(fname + "-boutrepititions.png")
	c.PlotCumulativeBoutTimes(fname + "-cumulativebouttimes.png")
	c.PlotCumulativeNormalizedVolume(fname + "-cumulativevolume.png")
	c.PlotBoutBoxplot(fname + '-boxplot.png')
	c.PlotBoutHistogram_Overlap(fname + '-bouthisto-overlap.png')
	c.PlotBoutHistogram_SideBySide(fname + '-bouthisto-sidebyside.png')
	c.PlotInterboutHistogram_Overlap(fname + '-interbouthisto-overlap.png')
	c.PlotInterboutHistogram_SideBySide(fname + '-interbouthisto-sidebyside.png')

def truncate():
	v,tz = _getdata()

	fname = "7-1 Overnight Device 6.CSV"
	a = CreedLickometer(fname)
	a.AddVolumeData(v)
	a.AddTimeData(tz)

	b = a.TrimBefore(datetime.datetime(2024,7,3, 2,0,0))
	b.Process()

	b.Filename = "7-1 Overnight Device 6 truncated.CSV"
	b.Save()

	b.PlotVsTime(fname + "-vstime.png")
	b.PlotBoutRepetitions(fname + "-boutrepititions.png")
	b.PlotCumulativeBoutTimes(fname + "-cumulativebouttimes.png")
	b.PlotCumulativeNormalizedVolume(fname + "-cumulativevolume.png")
	b.PlotBoutBoxplot(fname + '-boxplot.png')
	b.PlotBoutHistogram_Overlap(fname + '-bouthisto-overlap.png')
	b.PlotBoutHistogram_SideBySide(fname + '-bouthisto-sidebyside.png')
	b.PlotInterboutHistogram_Overlap(fname + '-interbouthisto-overlap.png')
	b.PlotInterboutHistogram_SideBySide(fname + '-interbouthisto-sidebyside.png')

if __name__ == '__main__':
	#allfiles()
	merger()
	#truncate()

