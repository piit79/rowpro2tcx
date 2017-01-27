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
        :param activity: Activity
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

        return root


class Activity(TCXBase):
    """
    :type time: datetime.datetime
    :type sport: str
    :type laps: list of Lap
    """
    RUNNING = 'Running'
    BIKING = 'Biking'
    OTHER = 'Other'
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
        """
        Return an XML representation of the instance
        :return: etree.Element
        """
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

    def __init__(self, **kwargs):
        self.start_time = kwargs.get('start_time')
        self.total_time = kwargs.get('total_time')
        self.distance = kwargs.get('distance')
        self.avg_speed = kwargs.get('avg_speed')
        self.max_speed = kwargs.get('max_speed')
        self.avg_hr = kwargs.get('avg_hr')
        self.max_hr = kwargs.get('max_hr')
        self.avg_cadence = kwargs.get('avg_cadence')
        self.calories = kwargs.get('calories')
        if 'track' in kwargs:
            self.add_track(kwargs['track'])

    def add_track(self, track):
        """
        Add a track to the lap
        :param track: Track
        """
        self.tracks.append(track)

    def calculate_stats(self):
        """
        Calculate stats that were not provided by the user
        """
        total_time = 0
        distance = None
        avg_spd = None
        max_spd = None
        tot_hr = 0
        num_hr = 0
        max_hr = None
        tot_pwr = 0
        num_pwr = 0
        max_pwr = 0
        max_cad = None
        tot_cad = 0
        num_cad = 0
        for track in self.tracks:
            for tp in track.points:
                if tp.speed is not None and tp.speed > max_spd:
                    max_spd = tp.speed
                if tp.heart_rate is not None:
                    # FIXME: average heart rate calculation assumes equal intervals
                    tot_hr += tp.heart_rate
                    num_hr += 1
                    if tp.heart_rate > max_hr:
                        max_hr = tp.heart_rate
                if tp.power is not None:
                    # FIXME: average power calculation assumes equal intervals
                    tot_pwr += tp.power
                    num_pwr += 1
                    if max_pwr is None or tp.power > max_pwr:
                        max_pwr = tp.power
                if tp.cadence is not None:
                    if max_cad is None or tp.cadence > max_cad:
                        max_cad = tp.cadence
                    # FIXME: average cadence calculation assumes equal intervals
                    tot_cad += tp.cadence
                    num_cad += 1

            first_tp = track.points[0]
            last_tp = track.points[-1]
            if last_tp.distance is not None:
                if distance is None:
                    distance = 0
                distance += last_tp.distance
            total_time += (last_tp.time - first_tp.time).total_seconds()

        if total_time > 0 and distance is not None:
            avg_spd = distance / total_time * 3.6
        avg_hr = tot_hr / num_hr if num_hr > 0 else None
        avg_pwr = tot_pwr / num_pwr if num_pwr > 0 else None
        avg_cad = tot_cad / num_cad if num_cad > 0 else None

        # set the computed stats if not set by the user
        self.total_time = total_time if self.total_time is None else self.total_time
        self.distance = distance if self.distance is None else self.distance
        self.avg_speed = avg_spd if self.avg_speed is None else self.avg_speed
        self.max_speed = max_spd if self.max_speed is None else self.max_speed
        self.avg_hr = avg_hr if self.avg_hr is None else self.avg_hr
        self.max_hr = max_hr if self.max_hr is None else self.max_hr
        self.avg_power = avg_pwr if self.avg_power is None else self.avg_power
        self.max_power = max_pwr if self.max_power is None else self.max_power
        self.avg_cadence = avg_cad if self.avg_cadence is None else self.avg_cadence
        self.max_cadence = max_cad if self.max_cadence is None else self.max_cadence

    def get_xml(self):
        """
        Return an XML representation of the instance
        :return: etree.Element
        """
        self.calculate_stats()
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
        """
        Add a point to the track
        :param point: Trackpoint
        """
        self.points.append(point)

    def get_xml(self):
        """
        Return an XML representation of the instance
        :return: etree.Element
        """
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
    power = None

    tags = {
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
        self.power = kwargs.get('power')

    def get_xml(self):
        """
        Return an XML representation of the instance
        :return: etree.Element
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
