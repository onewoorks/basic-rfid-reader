import crcmod.predefined
import serial
import sys
import time
from rethinkdb import RethinkDB
import binascii


class UHFReader18:
    PROTO_6B = "ISO18000-6B"
    PROTO_6C = "ISO18000-6C"

    IFACE_WIEGAND = "wiegand"
    IFACE_SERIAL = "RS232/RS485"
    IFACE_SYRIS = "SYRIS485"

    MSB = "msb"
    LSB = "lsb"

    WIEGAND_26 = "wiegand26"
    WIEGAND_34 = "wiegand34"

    STORAGE_PASSWD = "password"
    STORAGE_EPC = "epc"
    STORAGE_TID = "tid"
    STORAGE_USER = "user"
    STORAGE_MULTI_QUERY = "multi query"
    STORAGE_ONE_QUERY = "one query"
    STORAGE_EAS = "eas"

    MODE_ANSWER = "answer"
    MODE_ACTIVE = "active"
    MODE_TRIG_LOW = "trigger low"
    MODE_TRIG_HIGH = "trigger high"

    ON = "on"
    OFF = "off"

    ADDR_BYTE = "byte"
    ADDR_WORD = "word"

    GET_READER_INFO = 0x21
    SET_FREQ = 0x22
    SET_SCAN_TIME = 0x25
    SET_POWER = 0x2f
    GET_WORK_MODE = 0x36
    ADDR_BROADCAST = 0xff
    GET_INVENTORY = 0x01

    def get_crc(self, msg):
        crc = self.crc.new()
        crc.update(msg)
        return crc.digest()

    def open_port(self, path, baud):
        self.port = path
        self.sr = serial.Serial()
        self.sr.baudrate = baud
        self.sr.port = path
        self.sr.open()
        self.crc = crcmod.predefined.Crc('crc-16-mcrf4xx')
    
    def get_inventory(self,):
        print('--------------------------')
        print("SCANNING IN PROGRESS")
        print('--------------------------')
        # self.read_single_time()
        self.read_multiple_times()
       
    def read_multiple_times(self):
        items_found = []
        t_end = time.time() + 10 * 3
        while time.time() < t_end:
            self.send(self.ADDR_BROADCAST, 0x01)
            response        = self.recv()
            response        = response[4:-2]
            epcs            = self.epc_string(response)
            for i in epcs:
                if i not in items_found:
                    items_found.append(i)
        self.clean_found_items(items_found)

    def read_single_time(self):
        self.send(self.ADDR_BROADCAST, 0x01)
        output          = self.sr.read(1)
        response        = self.sr.read(output[0])
        total_found     = response[3]
        response        = response[4:-2]
        epcs            = self.epc_string(response)
        print("Total Tags Read : {}\n".format( total_found if total_found != 242 else "ralat"))
        self.clean_found_items(epcs)

    def clean_found_items(self, items_found):
        data = items_found
        print('--------------------------')
        print('FINAL SCANNED RESULT : ')
        print('--------------------------')
        for i in data:
            print(i)
        print('--------------------------')
        print("TOTAL ITEMS FOUND : {}".format(len(data)))
        print('--------------------------')

    def send(self, addr, cmd, args=bytes([])):
        self.sr.flushInput()
        self.sr.flushOutput()
        time.sleep(1)
        msg = bytes([addr, cmd]) + args
        msg = bytes([len(msg) + 2]) + msg
        crc = self.get_crc(msg)
        msg = msg + bytes([crc[1], crc[0]])
        self.sr.write(msg)

    def epc_string(self, payload):
        r = RethinkDB()
        r.connect('127.0.0.1', 28015).repl()
        items = []
        payload = payload.hex().upper()
        n = 26
        x = [payload[i:i + n] for i in range(0, len(payload), n)]
        for a in x:
            r.db('spe').table('uhf_rfid').insert({
                "epc": a
            }).run()
            if a not in items:
                items.append(a)
        return items
        # return []
    
    def recv(self):
        count = self.sr.read(1)
        data = self.sr.read(count[0])
        crc = data[-2:]
        calcCrc = self.get_crc(count + data[:-2])
        if crc[0] != calcCrc[1] or crc[1] != calcCrc[0]:
            raise Exception("CRC failed: " + (count + data).hex())
        return data

if len(sys.argv) != 2:
    print("usage: uhf TTY_SERIAL")
    sys.exit(2)

if __name__ == '__main__':
    uhfr = UHFReader18()
    uhfr.open_port(sys.argv[1], 57600)
    uhfr.get_inventory()
    # UI(uhfr).run()