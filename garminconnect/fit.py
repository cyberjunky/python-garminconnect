from io import BytesIO
from struct import pack
from struct import unpack
from datetime import datetime
import time


def _calcCRC(crc, byte):
    table = [0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
             0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400]
    # compute checksum of lower four bits of byte
    tmp = table[crc & 0xF]
    crc = (crc >> 4) & 0x0FFF
    crc = crc ^ tmp ^ table[byte & 0xF]
    # now compute checksum of upper four bits of byte
    tmp = table[crc & 0xF]
    crc = (crc >> 4) & 0x0FFF
    crc = crc ^ tmp ^ table[(byte >> 4) & 0xF]
    return crc


class FitBaseType(object):
    """BaseType Definition

    see FIT Protocol Document(Page.20)"""
    enum = {'#': 0, 'endian': 0, 'field': 0x00, 'name': 'enum', 'invalid': 0xFF, 'size': 1}
    sint8 = {'#': 1, 'endian': 0, 'field': 0x01, 'name': 'sint8', 'invalid': 0x7F, 'size': 1}
    uint8 = {'#': 2, 'endian': 0, 'field': 0x02, 'name': 'uint8', 'invalid': 0xFF, 'size': 1}
    sint16 = {'#': 3, 'endian': 1, 'field': 0x83, 'name': 'sint16', 'invalid': 0x7FFF, 'size': 2}
    uint16 = {'#': 4, 'endian': 1, 'field': 0x84, 'name': 'uint16', 'invalid': 0xFFFF, 'size': 2}
    sint32 = {'#': 5, 'endian': 1, 'field': 0x85, 'name': 'sint32', 'invalid': 0x7FFFFFFF, 'size': 4}
    uint32 = {'#': 6, 'endian': 1, 'field': 0x86, 'name': 'uint32', 'invalid': 0xFFFFFFFF, 'size': 4}
    string = {'#': 7, 'endian': 0, 'field': 0x07, 'name': 'string', 'invalid': 0x00, 'size': 1}
    float32 = {'#': 8, 'endian': 1, 'field': 0x88, 'name': 'float32', 'invalid': 0xFFFFFFFF, 'size': 2}
    float64 = {'#': 9, 'endian': 1, 'field': 0x89, 'name': 'float64', 'invalid': 0xFFFFFFFFFFFFFFFF, 'size': 4}
    uint8z = {'#': 10, 'endian': 0, 'field': 0x0A, 'name': 'uint8z', 'invalid': 0x00, 'size': 1}
    uint16z = {'#': 11, 'endian': 1, 'field': 0x8B, 'name': 'uint16z', 'invalid': 0x0000, 'size': 2}
    uint32z = {'#': 12, 'endian': 1, 'field': 0x8C, 'name': 'uint32z', 'invalid': 0x00000000, 'size': 4}
    byte = {'#': 13, 'endian': 0, 'field': 0x0D, 'name': 'byte', 'invalid': 0xFF,
            'size': 1}  # array of byte, field is invalid if all bytes are invalid

    @staticmethod
    def get_format(basetype):
        formats = {
            0: 'B', 1: 'b', 2: 'B', 3: 'h', 4: 'H', 5: 'i', 6: 'I', 7: 's', 8: 'f',
            9: 'd', 10: 'B', 11: 'H', 12: 'I', 13: 'c',
        }
        return formats[basetype['#']]

    @staticmethod
    def pack(basetype, value):
        """function to avoid DeprecationWarning"""
        if basetype['#'] in (1, 2, 3, 4, 5, 6, 10, 11, 12):
            value = int(value)
        fmt = FitBaseType.get_format(basetype)
        return pack(fmt, value)


class Fit(object):
    HEADER_SIZE = 12

    # not sure if this is the mesg_num
    GMSG_NUMS = {
        'file_id': 0,
        'device_info': 23,
        'weight_scale': 30,
        'file_creator': 49,
        'blood_pressure': 51,
    }


class FitEncoder(Fit):
    FILE_TYPE = 9
    LMSG_TYPE_FILE_INFO = 0
    LMSG_TYPE_FILE_CREATOR = 1
    LMSG_TYPE_DEVICE_INFO = 2

    def __init__(self):
        self.buf = BytesIO()
        self.write_header()  # create header first
        self.device_info_defined = False

    def __str__(self):
        orig_pos = self.buf.tell()
        self.buf.seek(0)
        lines = []
        while True:
            b = self.buf.read(16)
            if not b:
                break
            lines.append(' '.join(['%02x' % ord(c) for c in b]))
        self.buf.seek(orig_pos)
        return '\n'.join(lines)

    def write_header(self, header_size=Fit.HEADER_SIZE,
                     protocol_version=16,
                     profile_version=108,
                     data_size=0,
                     data_type=b'.FIT'):
        self.buf.seek(0)
        s = pack('BBHI4s', header_size, protocol_version, profile_version, data_size, data_type)
        self.buf.write(s)

    def _build_content_block(self, content):
        field_defs = []
        values = []
        for num, basetype, value, scale in content:
            s = pack('BBB', num, basetype['size'], basetype['field'])
            field_defs.append(s)
            if value is None:
                # invalid value
                value = basetype['invalid']
            elif scale is not None:
                value *= scale
            values.append(FitBaseType.pack(basetype, value))
        return (b''.join(field_defs), b''.join(values))

    def write_file_info(self, serial_number=None, time_created=None, manufacturer=None, product=None, number=None):
        if time_created is None:
            time_created = datetime.now()

        content = [
            (3, FitBaseType.uint32z, serial_number, None),
            (4, FitBaseType.uint32, self.timestamp(time_created), None),
            (1, FitBaseType.uint16, manufacturer, None),
            (2, FitBaseType.uint16, product, None),
            (5, FitBaseType.uint16, number, None),
            (0, FitBaseType.enum, self.FILE_TYPE, None),  # type
        ]
        fields, values = self._build_content_block(content)

        # create fixed content
        msg_number = self.GMSG_NUMS['file_id']
        fixed_content = pack('BBHB', 0, 0, msg_number, len(content))  # reserved, architecture(0: little endian)

        self.buf.write(b''.join([
            # definition
            self.record_header(definition=True, lmsg_type=self.LMSG_TYPE_FILE_INFO),
            fixed_content,
            fields,
            # record
            self.record_header(lmsg_type=self.LMSG_TYPE_FILE_INFO),
            values,
        ]))

    def write_file_creator(self, software_version=None, hardware_version=None):
        content = [
            (0, FitBaseType.uint16, software_version, None),
            (1, FitBaseType.uint8, hardware_version, None),
        ]
        fields, values = self._build_content_block(content)

        msg_number = self.GMSG_NUMS['file_creator']
        fixed_content = pack('BBHB', 0, 0, msg_number, len(content))  # reserved, architecture(0: little endian)
        self.buf.write(b''.join([
            # definition
            self.record_header(definition=True, lmsg_type=self.LMSG_TYPE_FILE_CREATOR),
            fixed_content,
            fields,
            # record
            self.record_header(lmsg_type=self.LMSG_TYPE_FILE_CREATOR),
            values,
        ]))

    def write_device_info(self, timestamp, serial_number=None, cum_operationg_time=None, manufacturer=None,
                          product=None, software_version=None, battery_voltage=None, device_index=None,
                          device_type=None, hardware_version=None, battery_status=None):
        content = [
            (253, FitBaseType.uint32, self.timestamp(timestamp), 1),
            (3, FitBaseType.uint32z, serial_number, 1),
            (7, FitBaseType.uint32, cum_operationg_time, 1),
            (8, FitBaseType.uint32, None, None),  # unknown field(undocumented)
            (2, FitBaseType.uint16, manufacturer, 1),
            (4, FitBaseType.uint16, product, 1),
            (5, FitBaseType.uint16, software_version, 100),
            (10, FitBaseType.uint16, battery_voltage, 256),
            (0, FitBaseType.uint8, device_index, 1),
            (1, FitBaseType.uint8, device_type, 1),
            (6, FitBaseType.uint8, hardware_version, 1),
            (11, FitBaseType.uint8, battery_status, None),
        ]
        fields, values = self._build_content_block(content)

        if not self.device_info_defined:
            header = self.record_header(definition=True, lmsg_type=self.LMSG_TYPE_DEVICE_INFO)
            msg_number = self.GMSG_NUMS['device_info']
            fixed_content = pack('BBHB', 0, 0, msg_number, len(content))  # reserved, architecture(0: little endian)
            self.buf.write(header + fixed_content + fields)
            self.device_info_defined = True

        header = self.record_header(lmsg_type=self.LMSG_TYPE_DEVICE_INFO)
        self.buf.write(header + values)

    def record_header(self, definition=False, lmsg_type=0):
        msg = 0
        if definition:
            msg = 1 << 6  # 6th bit is a definition message
        return pack('B', msg + lmsg_type)

    def crc(self):
        orig_pos = self.buf.tell()
        self.buf.seek(0)

        crc = 0
        while True:
            b = self.buf.read(1)
            if not b:
                break
            crc = _calcCRC(crc, unpack('b', b)[0])
        self.buf.seek(orig_pos)
        return pack('H', crc)

    def finish(self):
        """re-weite file-header, then append crc to end of file"""
        data_size = self.get_size() - self.HEADER_SIZE
        self.write_header(data_size=data_size)
        crc = self.crc()
        self.buf.seek(0, 2)
        self.buf.write(crc)

    def get_size(self):
        orig_pos = self.buf.tell()
        self.buf.seek(0, 2)
        size = self.buf.tell()
        self.buf.seek(orig_pos)
        return size

    def getvalue(self):
        return self.buf.getvalue()

    def timestamp(self, t):
        """the timestamp in fit protocol is seconds since
        UTC 00:00 Dec 31 1989 (631065600)"""
        if isinstance(t, datetime):
            t = time.mktime(t.timetuple())
        return t - 631065600


class FitEncoderBloodPressure(FitEncoder):
    # Here might be dragons - no idea what lsmg stand for, found 14 somewhere in the deepest web
    LMSG_TYPE_BLOOD_PRESSURE = 14

    def __init__(self):
        super().__init__()
        self.blood_pressure_monitor_defined = False

    def write_blood_pressure(self,
                             timestamp,
                             diastolic_blood_pressure=None,
                             systolic_blood_pressure=None,
                             mean_arterial_pressure=None,
                             map_3_sample_mean=None,
                             map_morning_values=None,
                             map_evening_values=None,
                             heart_rate=None, ):
        # BLOOD PRESSURE FILE MESSAGES
        content = [
            (253, FitBaseType.uint32, self.timestamp(timestamp), 1),
            (0, FitBaseType.uint16, systolic_blood_pressure, 1),
            (1, FitBaseType.uint16, diastolic_blood_pressure, 1),
            (2, FitBaseType.uint16, mean_arterial_pressure, 1),
            (3, FitBaseType.uint16, map_3_sample_mean, 1),
            (4, FitBaseType.uint16, map_morning_values, 1),
            (5, FitBaseType.uint16, map_evening_values, 1),
            (6, FitBaseType.uint8, heart_rate, 1),
        ]
        fields, values = self._build_content_block(content)

        if not self.blood_pressure_monitor_defined:
            header = self.record_header(definition=True, lmsg_type=self.LMSG_TYPE_BLOOD_PRESSURE)
            msg_number = self.GMSG_NUMS['blood_pressure']
            fixed_content = pack('BBHB', 0, 0, msg_number, len(content))  # reserved, architecture(0: little endian)
            self.buf.write(header + fixed_content + fields)
            self.blood_pressure_monitor_defined = True

        header = self.record_header(lmsg_type=self.LMSG_TYPE_BLOOD_PRESSURE)
        self.buf.write(header + values)


class FitEncoderWeight(FitEncoder):
    LMSG_TYPE_WEIGHT_SCALE = 3

    def __init__(self):
        super().__init__()
        self.weight_scale_defined = False

    def write_weight_scale(self, timestamp, weight, percent_fat=None, percent_hydration=None,
                           visceral_fat_mass=None, bone_mass=None, muscle_mass=None, basal_met=None,
                           active_met=None, physique_rating=None, metabolic_age=None,
                           visceral_fat_rating=None, bmi=None):
        content = [
            (253, FitBaseType.uint32, self.timestamp(timestamp), 1),
            (0, FitBaseType.uint16, weight, 100),
            (1, FitBaseType.uint16, percent_fat, 100),
            (2, FitBaseType.uint16, percent_hydration, 100),
            (3, FitBaseType.uint16, visceral_fat_mass, 100),
            (4, FitBaseType.uint16, bone_mass, 100),
            (5, FitBaseType.uint16, muscle_mass, 100),
            (7, FitBaseType.uint16, basal_met, 4),
            (9, FitBaseType.uint16, active_met, 4),
            (8, FitBaseType.uint8, physique_rating, 1),
            (10, FitBaseType.uint8, metabolic_age, 1),
            (11, FitBaseType.uint8, visceral_fat_rating, 1),
            (13, FitBaseType.uint16, bmi, 10),
        ]
        fields, values = self._build_content_block(content)

        if not self.weight_scale_defined:
            header = self.record_header(definition=True, lmsg_type=self.LMSG_TYPE_WEIGHT_SCALE)
            msg_number = self.GMSG_NUMS['weight_scale']
            fixed_content = pack('BBHB', 0, 0, msg_number, len(content))  # reserved, architecture(0: little endian)
            self.buf.write(header + fixed_content + fields)
            self.weight_scale_defined = True

        header = self.record_header(lmsg_type=self.LMSG_TYPE_WEIGHT_SCALE)
        self.buf.write(header + values)
