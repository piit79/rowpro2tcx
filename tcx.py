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
        return etree.tostring(el, encoding='UTF-8', xml_declaration=True, pretty_print=pretty_print)

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

    def __init__(self, activity=None):
        """
        :type activity: Activity
        """
        if activity is not None:
            self.add_activity(activity)

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
        activities = etree.SubElement(root, 'Activities')
        for activity in self.activities:
            activities.append(activity.get_xml())

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

    def __init__(self, time=None, sport=None, lap=None):
        """
        :param time: datetime.datetime
        :param sport: str
        :param lap: Lap
        """
        self.time = time
        self.sport = sport
        if lap is not None:
            self.add_lap(lap)

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
    :type total_time: int
    :type distance: int
    :type avg_speed: float
    :type max_speed: float
    :type avg_hr: int
    :type max_hr: int
    :type avg_power: float
    :type max_power: float
    :type avg_cadence: int
    :type max_cadence: int
    :type calories: float
    :type tracks: list of Track
    """
    start_time = None
    total_time = None
    distance = None
    avg_speed = None
    max_speed = None
    avg_hr = None
    max_hr = None
    avg_power = None
    max_power = None
    avg_cadence = None
    max_cadence = None
    calories = None
    tracks = []

    tags = {
        'TotalTimeSeconds': {'src': 'total_time'},
        'DistanceMeters': {'src': 'distance'},
        'MaximumSpeed': {'src': 'max_speed'},
        'AverageHeartRateBpm': {'src': 'avg_hr', 'sub_el': 'Value'},
        'MaximumHeartRateBpm': {'src': 'max_hr', 'sub_el': 'Value'},
        'Cadence': {'src': 'avg_cadence'},
        'Calories': {'src': 'calories'},
    }

    def __init__(self, start_time=None, total_time=None, distance=None, avg_speed=None, max_speed=None,
                 avg_hr=None, max_hr=None, avg_cadence=None, calories=None, track=None):
        self.start_time = start_time
        self.total_time = total_time
        self.distance = distance
        self.avg_speed = avg_speed
        self.max_speed = max_speed
        self.avg_hr = avg_hr
        self.max_hr = max_hr
        self.avg_cadence = avg_cadence
        self.calories = calories
        if track is not None:
            self.add_track(track)

    def add_track(self, track):
        self.tracks.append(track)

    def get_xml(self):
        root = etree.Element('Lap')
        root.attrib['StartTime'] = self.start_time.isoformat()
        for tag_name in self.tags:
            tag = self.tags[tag_name]
            if getattr(self, tag['src'], None) is not None:
                el = etree.SubElement(root, tag_name)
                if tag.get('sub_el') is not None:
                    value_el = etree.SubElement(el, tag.get('sub_el'))
                else:
                    value_el = el
                value_el.text = self.format_val(tag_name, getattr(self, tag['src']))

        # extensions
        if self.avg_speed is not None or self.max_cadence is not None or \
                self.avg_power is not None or self.max_power is not None:
            ext = etree.SubElement(root, 'Extensions')
            lx = etree.SubElement(ext, '{{{}}}LX'.format(self.NS3))
            if self.avg_speed is not None:
                avg_spd = etree.SubElement(lx, '{{{}}}AvgSpeed'.format(self.NS3))
                avg_spd.text = str(self.avg_speed)
            if self.avg_power is not None:
                avg_pwr = etree.SubElement(lx, '{{{}}}AvgWatts'.format(self.NS3))
                avg_pwr.text = str(self.avg_power)
            if self.max_power is not None:
                max_pwr = etree.SubElement(lx, '{{{}}}MaxWatts'.format(self.NS3))
                max_pwr.text = str(self.max_power)
            if self.max_cadence is not None:
                max_cad = etree.SubElement(lx, '{{{}}}MaxBikeCadence'.format(self.NS3))
                max_cad.text = str(self.max_cadence)

        for track in self.tracks:
            root.append(track.get_xml())

        return root

    @staticmethod
    def format_val(tag_name, value):
        return str(value)


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
    :type distance: float
    :type altitude: float
    :type cadence: int
    :type heart_rate: int
    :type speed: float
    :type power: int
    """
    time = None
    distance = None
    altitude = None
    cadence = None
    heart_rate = None
    speed = None
    power = None

    tags = {
        'Time': {'src': 'time'},
        'DistanceMeters': {'src': 'distance'},
        'AltitudeMeters': {'src': 'altitude'},
        'Cadence': {'src': 'cadence'},
        'HeartRateBpm': {'src': 'heart_rate', 'sub_el': 'Value'},
    }

    def __init__(self, time=None, distance=None, altitude=None, cadence=None, heart_rate=None, speed=None, power=None):
        self.time = time
        self.distance = distance
        self.altitude = altitude
        self.cadence = cadence
        self.heart_rate = heart_rate
        self.speed = speed
        self.power = power

    def get_xml(self):
        """
        :return: Element
        """
        root = etree.Element('Trackpoint')
        for tag_name in self.tags:
            tag = self.tags[tag_name]
            if getattr(self, tag['src'], None) is not None:
                el = etree.SubElement(root, tag_name)
                if tag.get('sub_el') is not None:
                    value_el = etree.SubElement(el, tag.get('sub_el'))
                else:
                    value_el = el
                value_el.text = self.format_val(tag_name, getattr(self, tag['src']))

        # add extensions
        if self.speed is not None or self.power is not None:
            ext = etree.SubElement(root, 'Extensions', nsmap=self.NSMAP)
            tpx = etree.SubElement(ext, '{{{}}}TPX'.format(self.NS3))
            if self.speed is not None:
                spd = etree.SubElement(tpx, '{{{}}}Speed'.format(self.NS3))
                spd.text = str(self.speed)
            if self.power is not None:
                pwr = etree.SubElement(tpx, '{{{}}}Watts'.format(self.NS3))
                pwr.text = str(self.power)

        return root

    @staticmethod
    def format_val(tag_name, value):
        if tag_name == 'Time':
            return value.isoformat()
        else:
            return str(value)
