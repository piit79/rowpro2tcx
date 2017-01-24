"""
Module for reading and exporting csv files exported from Concept2 RowPro
"""

import datetime
import tcx


def str2bool(val):
    return True if val == 'True' else False


def str2datetime(val, format='%d/%m/%Y %H:%M:%S'):
    dt = None
    try:
        dt = datetime.datetime.strptime(val, format)
    except Exception as ex:
        print 'Error parsing date {}: {}'.format(val, ex)
    return dt


class RowProCSV:

    HEADER_SUMMARY = 'Date,TotalTime,TotalDistance,'
    FIELDS_SUMMARY = [
        ('date', None),
        ('total_time', int),
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
        ('time_ms', int),
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
    datetime = None
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
                    val = summary_data.pop(0) if len(summary_data) else None

                    if field_type is not None and val is not None:
                        # convert time from milliseconds to fractional seconds
                        try:
                            val = field_type(val)
                        except ValueError:
                            print 'Error converting field {} value "{}" to {}'.format(field, val, str(field_type))

                    if hasattr(self, field) is not None:
                        setattr(self, field, val)

                # parse the date
                self.datetime = str2datetime(self.date)

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

                    # convert time from milliseconds to fractional seconds
                    sample['time'] = sample['time_ms'] / 1000.0

                    self.samples.append(sample)
                    samples_found = True

                break

        if not summary_found:
            print 'Warning: summary section not found in file'
        if not samples_found:
            print 'Warning: samples section not found in file'

    def get_data(self):
        return {
            'datetime': self.datetime,
            'total_time': self.total_time,
            'total_distance': self.total_distance,
            'avg_pace': self.avg_pace,
            'total_cals': self.total_cals,
            'slide': self.slide,
            'avg_hr': self.avg_hr,
            'last_hr': self.last_hr,
            'samples': self.samples,
        }
