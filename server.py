import json
import os
import socket, threading, time

HOST = '127.0.0.1' # localhost 127.0.0.1
PORT = 51234

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(4)


class SonyServer(threading.Thread):
    def __init__(self, info):
        threading.Thread.__init__(self)
        socket, address = info
        self.socket = socket
        self.address = address

        self.power_stat = ''
        self.input_stat = ''
        self.audio_mute_stat = ''
        self.audio_volume_stat = ''
        self.picture_mute_stat = ''

        if not os.path.exists('sony_stats.json'):
            self.setDefaults()
        else:
            self.getDataFromFile()

        self.inputs = {
            '1': 'hdmi',
            '4': 'component',
            '5': 'scrn-mirror'
        }

        ## DUMMY COMMANDS
        # *SCINPT0000000100000004
        # *SCPOWR0000000000000001
        # *SCPMUT0000000000000000
        # *SCAMUT0000000000000000
        # *SCVOLU0000000000000060

        ## DUMMY ANSWER
        # *SATYPE0000000000000000

        ## DUMMY QUERIES
        # *SEINPT################
        # *SEPOWR################
        # *SEPMUT################
        # *SEAMUT################
        # *SEVOLU################

    def run(self):
        first_run = True
        while True:
            if first_run:
                self.printUpdate()
                first_run = False

            try:
                self.socket.send(b'')
            except Exception as error:
                print("there was an error pinging socket: ", error)
                break

            data = self.waitRecv()

            if not data:
                print("ERROR: emergency break - no data received")
                break

            if len(data) == 24:
                data = data.decode('utf-8')
                self.routeCommand(data)
            else:
                print("Length of data was only: ", len(data))

            time.sleep(0.1)
        self.socket.close()
        print('%s:%s disconnected.' % self.address)
        return

    def waitRecv(self):
        # Had other logic in here previously
        return self.socket.recv(24)

    def routeCommand(self, command=None):
        # print("\ncommand received:", command)
        type = command[2]
        if type == 'C':
            res = self.control(command)
            if res:
                self.updateFile()
                self.printUpdate()
        elif type == 'E':
            self.query(command)
        else:
            print("\nwrong message format: {}\n".format(type))
        return

    def control(self, command):
        type = command[3:7]
        # print("type: ", type)
        if type == 'INPT':
            inpt = command[14]
            setting = command[19:]
            self.input_stat = '*SAINPT0000000{}0000{}'.format(inpt, setting)

        elif type == 'AMUT':
            setting = command[7:]
            self.audio_mute_stat = '*SAAMUT{}'.format(setting)

        elif type == 'VOLU':
            setting = command[7:]
            self.audio_volume_stat = '*SAVOLU{}'.format(setting)

        elif type == 'PMUT':
            setting = command[7:]
            self.picture_mute_stat = '*SAPMUT{}'.format(setting)

        elif type == 'POWR':
            setting = command[7:]
            self.power_stat = '*SAPOWR{}'.format(setting)

        else:
            print("No control type match")
            return False

        self.respond(type)
        return True


    def query(self, command=None):
        type = command[3:7]
        if type == 'INPT':
            data = self.input_stat.encode('utf-8')
            self.socket.send(data)
            # print("Query: ", command, "\n    Sent: ", data)

        elif type == 'AMUT':
            data = self.audio_mute_stat.encode('utf-8')
            self.socket.send(data)
            # print("Query: ", command, "\n    Sent: ", data)

        elif type == 'VOLU':
            data = self.audio_volume_stat.encode('utf-8')
            self.socket.send(data)
            # print("Query: ", command, "\n    Sent: ", data)

        elif type == 'PMUT':
            data = self.picture_mute_stat.encode('utf-8')
            self.socket.send(data)
            # print("Query: ", command, "\n    Sent: ", data)

        elif type == 'POWR':
            data = self.power_stat.encode('utf-8')
            self.socket.send(data)
            # print("Query: ", command, "\n    Sent: ", data)

    def respond(self, type=None):
        if type is None:
            return
        new = None
        if type == 'INPT':
            new = self.input_stat

        elif type == 'AMUT':
            new = self.audio_mute_stat

        elif type == 'VOLU':
            new = self.audio_volume_stat

        elif type == 'PMUT':
            new = self.picture_mute_stat

        elif type == 'POWR':
            new = self.power_stat

        if new:
            notify = new[:2] + 'N' + new[3:]
            answer = '*SA{}0000000000000000'.format(type)

            self.socket.send(answer.encode('utf-8'))
            self.socket.send(notify.encode('utf-8'))
            # print("sent response\n")
            return
        print("no notify sent")

    def setDefaults(self):
        self.power_stat = '*SAPOWR0000000000000000\n'
        self.input_stat = '*SAINPT0000000100000003\n'
        self.audio_mute_stat = '*SAAMUT0000000000000000\n'
        self.audio_volume_stat = '*SAVOLU0000000000000064\n'
        self.picture_mute_stat = '*SAPMUT0000000000000000\n'

    def updateFile(self):
        with open('sony_stats.json', 'w+') as file:
            data = {
                'power_stat': self.power_stat,
                'input_stat': self.input_stat,
                'audio_mute_stat': self.audio_mute_stat,
                'audio_volume_stat': self.audio_volume_stat,
                'picture_mute_stat': self.picture_mute_stat
            }
            file.write(json.dumps(data))

    def getDataFromFile(self):
        with open('sony_stats.json', 'r') as file:
            temp = file.read()
            if temp:
                data = json.loads(temp)
                self.power_stat = data.get('power_stat', '')
                self.input_stat = data.get('input_stat', '')
                self.audio_mute_stat = data.get('audio_mute_stat', '')
                self.audio_volume_stat = data.get('audio_volume_stat', '')
                self.picture_mute_stat = data.get('picture_mute_stat', '')
            else:
                self.setDefaults()


    def printUpdate(self):
        print("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n")
        print('%s:%s connected.' % self.address)
        print("========= SERVER DATA =========")
        print("Power: ", "on" if self.power_stat[-2:-1] == '1' else 'off')
        print("Input: {} {}".format(self.inputs[self.input_stat[14]], self.input_stat[-2:-1]))
        print("Audio Mute: ", 'unmuted' if self.audio_mute_stat[-2:-1] == '0' else 'muted')
        print("Audio Volume: ", self.audio_volume_stat[-4:-1])
        print("Picture Mute: ", 'unmuted' if self.picture_mute_stat[-2:-1] == '0' else 'muted')
        print("===============================")


if __name__ == "__main__":
    first_time = True
    thread = None
    while True:  # wait for socket to connect
        # send socket to SonyServer and start monitoring
        if first_time:
            print("waiting for a client connection to HOST: {} on PORT:{}".format(HOST, PORT))
            first_time = False
        try:
            thread = SonyServer(s.accept())
            thread.start()
        except Exception as error:
            print("Issue in thread: ", error)
        time.sleep(0.1)
