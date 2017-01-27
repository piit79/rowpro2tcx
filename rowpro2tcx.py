#/usr/bin/env python

import rowprocsv
import tcx
import datetime
from pprint import pprint

csv = rowprocsv.RowProCSV('samples/row1.csv')
data = csv.get_data()
# pprint(data)

tcxf = csv.get_tcx()
xml = tcxf.dumps(pretty_print=True)
tcxf.dump('samples/row1.tcx', pretty_print=True)
print xml

# fin = FitFile.open("/cygdrive/c/Users/error/Downloads/test.fit")
# for msg in fin:
#     print msg


# tp = tcx.Trackpoint(time=datetime.datetime.now(), distance=2.56, altitude=328.44, cadence=86, heart_rate=138, speed=18.25, power=168.334)
# trk = tcx.Track()
# trk.add_point(tp)
# lap = tcx.Lap(start_time=datetime.datetime.now())
# lap.add_track(trk)
# act = tcx.Activity(time=datetime.datetime.now(), sport='Biking')
# act.add_lap(lap)
# tcx = tcx.TCX()
# tcx.add_activity(act)
# xml = tcx.dumps(pretty_print=True)
# print xml
