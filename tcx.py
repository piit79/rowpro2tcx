from lxml import etree


class TCXBase:

    NS1 = 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'
    NS2 = 'http://www.garmin.com/xmlschemas/UserProfile/v'
    NS3 = 'http://www.garmin.com/xmlschemas/ActivityExtension/v2'
    NS4 = 'http://www.garmin.com/xmlschemas/ProfileExtension/v1'
    NS5 = 'http://www.garmin.com/xmlschemas/ActivityGoals/v1'
    XSI = 'http://www.w3.org/2001/XMLSchema-instance'

    NSMAP = {None: NS1, 'ns2': NS2, 'ns3': NS3, 'ns4': NS4, 'ns5': NS5, 'xsi': XSI}

    def get_xml(self):
        pass

    def dumps(self, pretty_print=False):
        """
        Return string representation of the XML subtree
        :type pretty_print: bool
        :rtype: str
        """
        el = self.get_xml()
        return etree.tostring(el, pretty_print=pretty_print)

    def dump(self, filename, pretty_print=False):
        """
        Write the string representation of the XML subtree to a file
        :type filename: str
        :type pretty_print: bool
        :return: True on success, False on failure
        :rtype: bool
        """
        xml = self.dumps(pretty_print=pretty_print)
        try:
            with open(filename, 'w') as fp:
                fp.write(xml)
        except IOError as e:
            print 'Cannot write to {}: {}'.format(filename, e)
            return False

        return True


class TCX(TCXBase):

    activities = []

    def __init__(self, **kwargs):
        if 'activity' in kwargs:
            self.add_activity(kwargs['activity'])

    def add_activity(self, activity):
        """
        Add an activity to the TCX file
        :type activity: Activity
        """
        self.activities.append(activity)

    def get_xml(self):
        root = etree.Element('TrainingCenterDatabase', nsmap=self.NSMAP)
        root.attrib['{{{}}}schemaLocation'.format(self.XSI)] = (
            'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 '
            'http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd'
        )
        for activity in self.activities:
            root.append(activity.get_xml())

        return root


class Activity(TCXBase):
    """
    :type time: datetime.datetime
    :type sport: str
    :type laps: list of Lap
    """
    time = None
    sport = None
    laps = []

    def __init__(self, **kwargs):
        self.time = kwargs.get('time')
        self.sport = kwargs.get('sport')
        if 'lap' in kwargs:
            self.add_lap(kwargs['lap'])

    def add_lap(self, lap):
        """
        Add a lap to the activity
        :type lap: Lap
        """
        self.laps.append(lap)

    def get_xml(self):
        root = etree.Element('Activity')
        root.attrib['Sport'] = self.sport
        id = etree.SubElement(root, 'Id')
        id.text = self.time.isoformat()
        for lap in self.laps:
            root.append(lap.get_xml())

        return root


class Lap(TCXBase):
    """
    :type start_time: datetime.datetime
    :type tracks: list of Track
    """
    start_time = None
    tracks = []

    def __init__(self, **kwargs):
        self.start_time = kwargs.get('start_time')
        if 'track' in kwargs:
            self.add_track(kwargs['track'])

    def add_track(self, track):
        self.tracks.append(track)

    def get_xml(self):
        root = etree.Element('Lap')
        root.attrib['StartTime'] = self.start_time.isoformat()
        for track in self.tracks:
            root.append(track.get_xml())

        return root


class Track(TCXBase):
    """
    :type points: list of Trackpoint
    """
    points = []

    def __init__(self):
        pass

    def add_point(self, point):
        self.points.append(point)

    def get_xml(self):
        root = etree.Element('Track')
        for point in self.points:
            root.append(point.get_xml())

        return root


class Trackpoint(TCXBase):
    """
    :type time: datetime.datetime
    """
    time = None
    distance = None
    altitude = None
    cadence = None
    heart_rate = None
    speed = None
    watts = None

    attributes = {
        'Time': {'src': 'time'},
        'DistanceMeters': {'src': 'distance'},
        'AltitudeMeters': {'src': 'altitude'},
        'Cadence': {'src': 'cadence'},
        'HeartRateBpm': {'src': 'heart_rate', 'sub_el': 'Value'},
    }

    def __init__(self, **kwargs):
        self.time = kwargs.get('time')
        self.distance = kwargs.get('distance')
        self.altitude = kwargs.get('altitude')
        self.cadence = kwargs.get('cadence')
        self.heart_rate = kwargs.get('heart_rate')
        self.speed = kwargs.get('speed')
        self.watts = kwargs.get('watts')

    def get_xml(self):
        """
        :return: Element
        """
        root = etree.Element('Trackpoint')
        for tag_name in self.attributes:
            tag = self.attributes[tag_name]
            if getattr(self, tag['src'], None) is not None:
                el = etree.SubElement(root, tag_name)
                if tag.get('sub_el') is not None:
                    value_el = etree.SubElement(el, tag.get('sub_el'))
                else:
                    value_el = el
                value_el.text = self.format_val(tag_name, getattr(self, tag['src']))
        if self.speed is not None or self.watts is not None:
            ext = etree.SubElement(root, 'Extensions', nsmap=self.NSMAP)
            tpx = etree.SubElement(ext, '{{{}}}TPX'.format(self.NS3))
            if self.speed is not None:
                spd = etree.SubElement(tpx, '{{{}}}Speed'.format(self.NS3))
                spd.text = str(self.speed)
            if self.watts is not None:
                spd = etree.SubElement(tpx, '{{{}}}Watts'.format(self.NS3))
                spd.text = str(self.watts)

        return root

    def format_val(self, tag_name, value):
        if tag_name == 'Time':
            return value.isoformat()
        else:
            return str(value)
