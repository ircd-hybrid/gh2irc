import base64
import json
import re
import socket
import ssl
from time import sleep


class Colors(object):


    def __init__(self):
        self.bold         = "\002"
        self.reset        = "\017"
        self.italic       = "\026"
        self.underline    = "\037"
        self.white        = "\0030"
        self.black        = "\0031"
        self.dark_blue    = "\0032"
        self.dark_green   = "\0033"
        self.dark_red     = "\0034"
        self.brown        = "\0035"
        self.dark_purple  = "\0036"
        self.orange       = "\0037"
        self.yellow       = "\0038"
        self.light_green  = "\0039"
        self.dark_teal    = "\00310"
        self.light_teal   = "\00311"
        self.light_blue   = "\00312"
        self.light_purple = "\00313"
        self.dark_gray    = "\00314"
        self.light_gray   = "\00315"


class IRC(object):


    def __init__(self, sslConfig):
        if sslConfig is True:
            self.irc = ssl.wrap_socket(
                socket.socket(socket.AF_INET, socket.SOCK_STREAM),
                ssl_version=ssl.PROTOCOL_TLSv1_2
            )
        else:
            self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        

    def getText(self):
        text=self.irc.recv(2040)
        return text.decode("UTF-8")


    def waitAndSee(self, search):
        tries = 0
        while True:
            text = self.getText().decode("UTF-8")
            '''
            TODO: Maybe have a config of some sort to turn on printing of text
            '''
            if tries > 20:
                raise ConnectionError("Unable to connect to IRC: %s" % text) 
            ack = re.search(search, text, re.MULTILINE)
            if ack:
                return
            sleep(0.25)
            tries += 1


    def authenticate(self, nick, password):
        self.irc.send(bytes("CAP REQ :sasl\n", "UTF-8"))
        self.waitAndSee(r'(.*)CAP(.*)ACK(.*)')
        self.irc.send(bytes("AUTHENTICATE PLAIN\n", "UTF-8"))
        self.waitAndSee(r'(.*)AUTHENTICATE \+(.*)')
        auth = (
            "{nick}\0{nick}\0{password}"
        ).format(
            nick=nick,
            password=password
        )
        auth = base64.encodestring(auth.encode("UTF-8"))
        auth = auth.decode("UTF-8").rstrip("\n")
        self.irc.send(bytes("AUTHENTICATE "+auth+"\n", "UTF-8"))
        self.waitAndSee(r'(.*)903(.*):SASL authentication successful(.*)')
        self.irc.send(bytes("CAP END\n", "UTF-8"))


    def sendMessage(self, channel, message):
        self.irc.send(bytes("PRIVMSG {} :{}\n".format(channel, message), "UTF-8"))


    def sendPing(self, text):
        self.irc.send(bytes(text.replace('PING', 'PONG'), "UTF-8"))


    def connect(self, host, port, channels, nick, password):
        self.irc.connect((host, port))  
        if password != None:
            self.authenticate(nick, password)                                                  
        self.irc.send(bytes("USER {nick} {nick} {nick} {nick}\n".format(nick=nick), "UTF-8"))
        self.irc.send(bytes("NICK {}\n".format(nick), "UTF-8"))
        for channel in channels:          
            self.irc.send(bytes("JOIN {}\n".format(channel), "UTF-8"))
 

    def disconnect(self, channels):
        # don't disconnect too quickly to ensure all messages are sent
        sleep(1)
        for channel in channels:               
            self.irc.send(bytes("PART {}\n".format(channel), "UTF-8"))
        self.irc.send(bytes("QUIT\n", "UTF-8"))
        self.irc.close()
        

def sendMessages(pool, messages):
    try:
        irc = IRC(pool.ssl)
        irc.connect(pool.host, pool.port, pool.channels, pool.nick, pool.password)

        # Wait until connection is established
        while True:    
            text = irc.getText()
            print(text)
            if re.search(r'(.*)End of /NAMES list.(.*)', text, re.MULTILINE):
                break
            elif re.search(r'(.*)PING(.*)', text, re.MULTILINE):
                irc.sendPing(text)
            elif re.search(r'(.*)433(.*)Nickname is already in use(.*)', text, re.MULTILINE):
                raise ConnectionError("Nickname is already in use")
            elif re.search(r'(.*)ERROR :(.*)', text, re.MULTILINE):
                raise ConnectionError(text)
            sleep(0.25)

        for channel in pool.channels:
            for message in messages:
                irc.sendMessage(channel, message)

        irc.disconnect(pool.channels)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "success": True,
                "message": "Messages sent successfully."
            }) 
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "success": False,
                "message": "There was a problem sending messages to IRC:\n%s" % e
            })
        }