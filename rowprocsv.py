"""
Module for reading and exporting csv files exported from Concept2 RowPro
"""

import datetime
from dateutil import tz
import tcx


local_tz = tz.tzlocal()


def str_ms2seconds(val):
    """
    Convert time in milliseconds to float seconds
    :type val: str or int
    :rtype: float
    """
    return int(val)/1000.0


def str2bool(val):
    return True if val == 'True' else False


def str2datetime(val, format='%d/%m/%Y %H:%M:%S'):
    dt = None
    try:
        dt = datetime.datetime.strptime(val, format)
    except Exception as ex:
        print 'Error parsing date {}: {}'.format(val, ex)
    dt = dt.replace(tzinfo=local_tz)
    return dt


class RowProCSV:

    HEADER_SUMMARY = 'Date,TotalTime,TotalDistance,'
    FIELDS_SUMMARY = [
        ('date', str2datetime),
        ('total_time', str_ms2seconds),
        ('total_distance', float),
        ('avg_pace', float),
        ('unit', int),
        ('origin', int),
        ('total_cals', float),
        ('duty_cycle', float),
        ('type', int),
        ('format', None),
        ('slide', str2bool),
        ('session_id', float),
        ('rowfile_id', None),
        ('avg_hr', int),
        ('last_hr', int),
        ('offset', None),
    ]

    HEADER_SAMPLES = 'Time,Distance,Pace,Watts,Cals,SPM,HR,DutyCycle,Rowfile_Id'
    FIELDS_SAMPLES = [
        ('time', str_ms2seconds),
        ('distance', float),
        ('pace', float),
        ('watts', float),
        ('cals', float),
        ('spm', int),
        ('hr', int),
        ('duty_cycle', float),
        ('rowfile_id', None),
    ]

    date = None
    total_time = None
    total_distance = None
    avg_pace = None
    total_cals = None
    slide = False
    avg_hr = None
    last_hr = None
    samples = []

    def __init__(self, filename):
        lines = []
        try:
            with open(filename, 'r') as fp:
                lines = fp.read().split("\r\n")
        except IOError as e:
            print 'Could not read file {}: {}'.format(filename, e)

        summary_found = False
        samples_found = False
        while len(lines):
            line = lines.pop(0)
            if not line:
                continue

            if line.startswith(self.HEADER_SUMMARY):
                line = lines.pop(0)
                summary_data = line.split(',')
                if len(summary_data) != len(self.FIELDS_SUMMARY):
                    print 'Warning: summary line only has {} fields, {} expected'.format(len(summary_data),
                                                                                         len(self.FIELDS_SUMMARY))
                for field, field_type in self.FIELDS_SUMMARY:
                    # skip fields we don't need
                    if hasattr(self, field) is None:
                        continue

                    val = summary_data.pop(0) if len(summary_data) else None

                    if field_type is not None and val is not None:
                        # convert the field using the specified function
                        try:
                            val = field_type(val)
                        except ValueError:
                            print 'Error converting field {} value "{}" to {}'.format(field, val, str(field_type))

                    setattr(self, field, val)

                summary_found = True
                continue

            elif line.startswith(self.HEADER_SAMPLES):
                while len(lines):
                    line = lines.pop(0).strip()
                    if not line:
                        break

                    sample_data = line.split(',')

                    sample = {}
                    for field, field_type in self.FIELDS_SAMPLES:
                        val = sample_data.pop(0) if len(sample_data) else None

                        if field_type is not None and val is not None:
                            # convert time from milliseconds to fractional seconds
                            try:
                                val = field_type(val)
                            except ValueError:
                                print 'Error converting field {} value "{}" to {}'.format(field, val, str(field_type))

                        sample[field] = val

                    self.samples.append(sample)
                    samples_found = True

                break

        if not summary_found:
            print 'Warning: summary section not found in file'
        if not samples_found:
            print 'Warning: samples section not found in file'

    def get_data(self):
        return {
            'date': self.date,
            'total_time': self.total_time,
            'total_distance': self.total_distance,
            'avg_pace': self.avg_pace,
            'total_cals': self.total_cals,
            'slide': self.slide,
            'avg_hr': self.avg_hr,
            'last_hr': self.last_hr,
            'samples': self.samples,
        }

    def get_tcx(self, sport='Rowing'):
        """
        Return a TCX file constructed from the RowPro file
        :rtype: tcx.TCX
        """
        track = tcx.Track()
        for sample in self.samples:
            tp = self.sample_to_trackpoint(self.date, sample)
            track.add_point(tp)
        lap = tcx.Lap(start_time=self.datetime, track=track)
        act = tcx.Activity(time=self.datetime, sport=sport, lap=lap)
        tcxf = tcx.TCX(activity=act)

        return tcxf

    @staticmethod
    def sample_to_trackpoint(start_time, sample):
        """
        Return a TCX Trackpoint instance from a RowPro CSV sample
        :type start_time: datetime.datetime
        :type sample: dict
        :rtype: Trackpoint
        """
        return tcx.Trackpoint(
            time=start_time + datetime.timedelta(seconds=sample['time']),
            distance=sample['distance'],
            speed=sample['pace'] * 60.0,
            cadence=sample['spm'],
            heart_rate=sample['hr'],
            power=sample['watts']
        )
