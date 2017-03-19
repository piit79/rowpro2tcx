"""
Module for reading and converting DigitalRowing RowPro csv files
See https://www.digitalrowing.com/
"""

import datetime
import dateutil.parser
import tcx


__version__ = '0.1.1'


def str_ms2seconds(val):
    """
    Convert time in milliseconds to float seconds
    :type val: str or int
    :rtype: float
    """
    return int(val) / 1000.0


def str2bool(val):
    """
    Return True for 'True', False otherwise
    :type val: str
    :rtype: bool
    """
    return True if val == 'True' else False


def str2datetime(val):
    """
    Convert ISO 8601 date to datetime
    :type val: str
    :rtype: datetime.datetime
    """
    dt = None
    try:
        dt = dateutil.parser.parse(val)
    except Exception as ex:
        print 'Error parsing date {}: {}'.format(val, ex)
    return dt


class RowProCSV:
    """
    :type date: datetime.datetime
    :type total_time: float
    :type total_distance: float
    :type avg_pace: float
    :type total_cals: int
    :type slide: bool
    :type avg_hr: int
    :type samples: list of dict
    """

    CREATOR = 'DigitalRowing RowPro'

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
    ]

    HEADER_SAMPLES = 'Time,Distance,Pace,Watts,Cals,SPM,HR,DutyCycle,Rowfile_Id'
    FIELDS_SAMPLES = [
        ('time', str_ms2seconds),
        ('distance', float),
        ('pace', float),   # pace is in kilometres per minute
        ('watts', float),
        ('cals', float),
        ('spm', int),
        ('hr', int),
        ('duty_cycle', float),
        ('rowfile_id', None),
    ]

    rowpro_version = None
    date = None
    total_time = None
    total_distance = None
    avg_pace = None
    total_cals = None
    slide = False
    avg_hr = None
    samples = []

    def __init__(self, filename, rowpro_version=None):
        """
        :type filename: str
        """
        self.rowpro_version = rowpro_version
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
                if len(summary_data) < len(self.FIELDS_SUMMARY):
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
        """
        Return all data in a dictionary
        :rtype: dict
        """
        return {
            'date': self.date,
            'total_time': self.total_time,
            'total_distance': self.total_distance,
            'avg_pace': self.avg_pace,
            'total_cals': self.total_cals,
            'slide': self.slide,
            'avg_hr': self.avg_hr,
            'samples': self.samples,
        }

    def get_tcx(self, sport=tcx.Activity.OTHER):
        """
        Return a TCX instance constructed from the RowPro file
        :type sport: str
        :rtype: tcx.TCX
        """
        track = tcx.Track()
        for sample in self.samples:
            tp = self.sample_to_trackpoint(self.date, sample)
            track.add_point(tp)

        lap = tcx.Lap(
            start_time=self.date,
            total_time=self.total_time,
            distance=self.total_distance,
            avg_speed=self.avg_pace * 1000.0 / 60.0,   # kilometres per minute -> metres per second
            calories=self.total_cals,
            avg_hr=self.avg_hr,
            track=track
        )

        creator = {
            'name': self.CREATOR,
        }
        if self.rowpro_version is not None:
            creator['version'] = self.rowpro_version

        act = tcx.Activity(
            time=self.date,
            sport=sport,
            lap=lap,
            creator=creator
        )

        author = tcx.Author(__name__, version=__version__)
        tcxf = tcx.TCX(activity=act, author=author)

        return tcxf

    @staticmethod
    def sample_to_trackpoint(start_time, sample):
        """
        Return a TCX Trackpoint instance from a RowPro CSV sample
        :type start_time: datetime.datetime
        :type sample: dict
        :rtype: tcx.Trackpoint
        """
        return tcx.Trackpoint(
            time=start_time + datetime.timedelta(seconds=sample['time']),
            distance=sample['distance'],
            speed=sample['pace'] * 1000.0 / 60.0,   # kilometres per minute -> metres per second
            cadence=sample['spm'],
            heart_rate=sample['hr'],
            power=sample['watts']
        )
