from lxml import etree


class TCXBase(object):

    NS1 = 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'
    NS2 = 'http://www.garmin.com/xmlschemas/UserProfile/v2'
    NS3 = 'http://www.garmin.com/xmlschemas/ActivityExtension/v2'
    NS4 = 'http://www.garmin.com/xmlschemas/ProfileExtension/v1'
    NS5 = 'http://www.garmin.com/xmlschemas/ActivityGoals/v1'
    XSI = 'http://www.w3.org/2001/XMLSchema-instance'

    NSMAP = {None: NS1, 'ns2': NS2, 'ns3': NS3, 'ns4': NS4, 'ns5': NS5, 'xsi': XSI}

    def __init__(self):
        pass

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
    """
    :type activities: list of Activity
    :type author: Author
    """
    activities = []
    author = None

    def __init__(self, activity=None, author=None):
        """
        :type activity: Activity
        :type author: Author
        """
        super(TCX, self).__init__()
        if activity is not None:
            self.add_activity(activity)
        self.author = author

    def add_activity(self, activity):
        """
        Add an activity to the TCX file
        :type activity: Activity
        """
        self.activities.append(activity)

    def get_xml(self):
        """
        Return an XML representation of the instance
        :return: etree.Element
        """
        root = etree.Element('TrainingCenterDatabase', nsmap=self.NSMAP)
        root.attrib['{{{}}}schemaLocation'.format(self.XSI)] = (
            'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 '
            'http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd'
        )
        activities = etree.SubElement(root, 'Activities')
        for activity in self.activities:
            activities.append(activity.get_xml())

        if self.author is not None:
            root.append(self.author.get_xml())

        return root


class Version(TCXBase):
    """
    :type version: str
    """
    version = None

    def __init__(self, version):
        super(Version, self).__init__()
        self.version = version

    def get_xml(self):
        """
        Return an XML representation of the instance
        :return: etree.Element
        """
        root = etree.Element('Version', nsmap=self.NSMAP)
        if self.version is not None:
            # ensure at least 2 elements in the version
            ver = self.version.split('.') + ['0']
            etree.SubElement(root, 'VersionMajor').text = ver[0]
            etree.SubElement(root, 'VersionMinor').text = ver[1]
            if len(ver) > 2:
                etree.SubElement(root, 'BuildMajor').text = ver[2]
            if len(ver) > 3:
                etree.SubElement(root, 'BuildMinor').text = ver[3]

        return root


class Build(Version):

    def __init__(self, version):
        super(Build, self).__init__(version)

    def get_xml(self):
        """
        Return an XML representation of the instance
        :return: etree.Element
        """
        root = etree.Element('Build', nsmap=self.NSMAP)
        root.append(super(Build, self).get_xml())

        return root


class Author(Build):
    """
    :type name: str
    :type lang: str
    :type part_number: str
    """
    name = None
    lang = None
    part_number = None

    def __init__(self, name, version=None, lang=None, part_number=None):
        super(Author, self).__init__(version)
        self.name = name
        self.lang = lang
        self.part_number = part_number

    def get_xml(self):
        """
        Return an XML representation of the instance
        :return: etree.Element
        """
        root = etree.Element('Author', nsmap=self.NSMAP)
        root.attrib['{{{}}}type'.format(self.XSI)] = 'Application_t'
        etree.SubElement(root, 'Name').text = self.name
        if self.version is not None:
            root.append(super(Author, self).get_xml())
        if self.lang is not None:
            etree.SubElement(root, 'LangID').text = self.lang
        if self.part_number is not None:
            etree.SubElement(root, 'PartNumber').text = self.part_number

        return root


class Creator(TCXBase):
    """
    :type name: str
    :type unit_id: str
    :type product_id: str
    :type version: str
    """
    name = None
    unit_id = None
    product_id = None
    version = None

    def __init__(self, name, unit_id=None, product_id=None, version=None):
        super(Creator, self).__init__()
        self.name = name
        self.unit_id = unit_id
        self.product_id = product_id
        self.version = version

    def get_xml(self):
        """
        Return an XML representation of the instance
        :return: etree.Element
        """
        root = etree.Element('Creator', nsmap=self.NSMAP)
        root.attrib['{{{}}}type'.format(self.XSI)] = 'Device_t'
        etree.SubElement(root, 'Name').text = self.name
        if self.unit_id is not None:
            etree.SubElement(root, 'UnitID').text = self.unit_id
        if self.product_id is not None:
            etree.SubElement(root, 'ProductID').text = self.product_id
        if self.version is not None:
            root.append(Version(self.version).get_xml())

        return root


class Activity(TCXBase):
    """
    :type time: datetime.datetime
    :type sport: str
    :type laps: list of Lap
    :type creator: dict
    """
    RUNNING = 'Running'
    BIKING = 'Biking'
    OTHER = 'Other'
    time = None
    sport = None
    laps = []
    creator = None

    def __init__(self, time=None, sport=None, lap=None, creator={}):
        """
        :param time: datetime.datetime
        :param sport: str
        :param lap: Lap
        """
        super(Activity, self).__init__()
        self.time = time
        self.sport = sport
        if lap is not None:
            self.add_lap(lap)
        self.creator = creator

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

        if 'name' in self.creator or 'version' in self.creator or 'unit_id' in self.creator or \
                'product_id' in self.creator:
            root.append(Creator(name=self.creator.get('name'), unit_id=self.creator.get('unit_id'),
                                product_id=self.creator.get('product_id'),
                                version=self.creator.get('version')).get_xml())

        return root


class Lap(TCXBase):
    """
    :type start_time: datetime.datetime
    :type total_time: float
    :type distance: float
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
        super(Lap, self).__init__()
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
        super(Track, self).__init__()

    def add_point(self, point):
        self.points.append(point)

    def get_xml(self):
        root = etree.Element('Track')
        for point in self.points:
            root.append(point.get_xml())

        return root


class Position(TCXBase):
    """
    :type latitude: float
    :type longitude: float
    """
    latitude = None
    longitude = None

    def __init__(self, latitude, longitude):
        super(Position, self).__init__()
        self.latitude = latitude
        self.longitude = longitude

    def get_xml(self):
        """
        Return an XML representation of the instance
        :return: etree.Element
        """
        root = etree.Element('Position')
        etree.SubElement(root, 'LatitudeDegrees').text = self.latitude
        etree.SubElement(root, 'LongitudeDegrees').text = self.longitude

        return root


class Trackpoint(Position):
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

    def __init__(self, time=None, distance=None, latitude=None, longitude=None, altitude=None, cadence=None,
                 heart_rate=None, speed=None, power=None):
        super(Trackpoint, self).__init__(latitude, longitude)
        self.time = time
        self.distance = distance
        self.altitude = altitude
        self.cadence = cadence
        self.heart_rate = heart_rate
        self.speed = speed
        self.power = power

    def get_xml(self):
        """
        Return an XML representation of the instance
        :return: etree.Element
        """
        root = etree.Element('Trackpoint')
        if self.latitude is not None and self.longitude is not None:
            root.append(super(Trackpoint, self).get_xml())
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
