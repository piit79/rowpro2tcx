"""
Module for reading and exporting csv files exported from Concept2 RowPro
"""

import datetime
import tcx


class RowProCSV:

    HEADER_SUMMARY = 'Date,TotalTime,TotalDistance,'
    FIELDS_SUMMARY = [
        'date', 'total_time', 'total_distance', 'avg_pace', 'unit', 'origin', 'total_cals', 'duty_cycle', 'type',
        'format', 'slide', 'session_id', 'rowfile_id', 'avg_hr', 'last_hr', 'offset'
    ]

    HEADER_SAMPLES = 'Time,Distance,Pace,Watts,Cals,SPM,HR,DutyCycle,Rowfile_Id'
    FIELDS_SAMPLES = ['time_ms', 'distance', 'pace', 'watts', 'cals', 'spm', 'hr', 'duty_cycle', 'rowfile_id']

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
                for field in self.FIELDS_SUMMARY:
                    if len(summary_data):
                        value = summary_data.pop(0)
                        if hasattr(self, field) is not None:
                            setattr(self, field, value)

                # parse the date
                try:
                    self.datetime = datetime.datetime.strptime(self.date, '%d/%m/%Y %H:%M:%S')
                except Exception as ex:
                    print 'Error parsing date {}: {}'.format(self.date, ex)

                # parse the slide value
                self.slide = True if self.slide == 'True' else False

                summary_found = True
                continue

            elif line.startswith(self.HEADER_SAMPLES):
                while len(lines):
                    line = lines.pop(0)
                    sample_data = line.split(',')

                    sample = {}
                    for field in self.FIELDS_SAMPLES:
                        sample[field] = sample_data.pop(0) if len(sample_data) else None

                    # convert time from milliseconds to fractional seconds
                    try:
                        sample['time'] = float(sample['time_ms']) / 1000.0
                    except ValueError:
                        print 'Error converting "{}" to float'.format(sample['time_ms'])

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
