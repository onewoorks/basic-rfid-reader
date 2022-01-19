import crcmod.predefined
import serial
import sys
import time
from rethinkdb import RethinkDB


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
    
    def get_inventory(self):
        r = RethinkDB()
        r.connect('127.0.0.1', 28015).repl()
        # spe = r.db('spe').table('uhf_rfid')
        print('----------------------------------------------------------------')
        print("SCANNING IN PROGRESS")
        print('----------------------------------------------------------------')
        items_found = []
        t_end = time.time() + 2
        while time.time() < t_end:
            self.send(self.ADDR_BROADCAST, 0x01)
            recv = self.recv()
            out = list(recv)
            epcs = out[4:-2]
            n = 13
            x = [epcs[i:i + n] for i in range(0, len(epcs), n)] 
            for a in x:
                scanned = ""
                for y in a:
                    scanned += "{}".format(str(y).zfill(3))
                r.db('spe').table("uhf_rfid").insert({
                        "rfid_hexa":scanned
                        }).run()
                print('scanned: {}'.format(scanned))
                items_found.append(scanned)
        self.clean_found_items(items_found)
    
    def clean_found_items(self, items_found):
        data = items_found
        unique_epc = []
        for i in data:
            if i not in unique_epc:
                unique_epc.append(i)
        print('SCANNED RESULT : ')
        print('----------------------------------------------------------------')
        for n in unique_epc:
            print(n)
        print('----------------------------------------------------------------')
        print("TOTAL ITEMS FOUND : {}".format(len(unique_epc)))
        print('----------------------------------------------------------------')

    def send(self, addr, cmd, args=bytes([])):
        self.sr.flushInput()
        self.sr.flushOutput()
        time.sleep(1)
        msg = bytes([addr, cmd]) + args
        msg = bytes([len(msg) + 2]) + msg
        crc = self.get_crc(msg)
        msg = msg + bytes([crc[1], crc[0]])
        self.sr.write(msg)
    
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