"""
Module for reading csv files exported from Concept2 RowPro
"""

HEADER_SUMMARY = 'Date,TotalTime,TotalDistance,'
FIELDS_SUMMARY = [
    'date', 'total_time', 'total_distance', 'avg_pace', 'unit', 'origin', 'total_cals', 'duty_cycle', 'type', 'format',
    'slide', 'session_id', 'rowfile_id', 'avg_hr', 'last_hr', 'offset'
]

HEADER_SAMPLES = 'Time,Distance,Pace,Watts,Cals,SPM,HR,DutyCycle,Rowfile_Id'
FIELDS_SAMPLES = ['time', 'distance', 'pace', 'watts', 'cals', 'spm', 'hr', 'duty_cycle', 'rowfile_id']


def load(filename):
    data = {
        'samples': [],
    }

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
        print 'LINE:', line
        if not line:
            continue

        if line.startswith(HEADER_SUMMARY):
            line = lines.pop(0)
            summary_data = line.split(',')
            if len(summary_data) != len(FIELDS_SUMMARY):
                print 'Warning: summary line only has {} fields, {} expected'.format(len(summary_data),
                                                                                     len(FIELDS_SUMMARY))
            for field in FIELDS_SUMMARY:
                if len(summary_data):
                    data[field] = summary_data.pop(0)
            summary_found = True
            continue

        elif line.startswith(HEADER_SAMPLES):
            while len(lines):
                line = lines.pop(0)
                sample_data = line.split(',')

                sample = {}
                for field in FIELDS_SAMPLES:
                    sample[field] = sample_data.pop(0) if len(sample_data) else None

                data['samples'].append(sample)

            samples_found = True
            break

        if not summary_found:
            print 'Warning: summary section not found in file'
        if not samples_found:
            print 'Warning: samples section not found in file'

    return data
