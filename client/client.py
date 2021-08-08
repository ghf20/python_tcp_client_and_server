"""Client-side commandline application to communicate and exchange data with a server via TCP sockets

Author: George Fraser

-Parameters:
    IP ADDRESS:
        Accepts via stdin a valid Ipv4 IP address or host name
    Port Number:
        Accepts via stdin a port number (integer) between 1024 and 64000 inclusive
        If the port number doesnt conform to these conditions the server will print an error message and terminate
    File to transfer
        Accepts via stdin a filename that you wish to transfer from the server as long as there isnt a matching
        file in the current working directory (Perhaps add ability to pipe to another directory)
"""

import socket
import sys
import os


class Client():

    def __init__(self):

        #STILL NEEDS TO MAKE SURE PARAMETERS ARE VALID

        self.socket = None
        self.data = None

        input_string = sys.argv
        if len(input_string) != 4:
            sys.exit("Incorrect amount of arguments")

        try:
            
            self.IP = input_string[1]
            socket.gethostbyname(self.IP)   
        except:
            sys.exit("ERROR: Invaild IP address")

        try:
            self.port_number = int(input_string[2])
        except ValueError:
            sys.exit("ERROR: Value must be an integer")

        
        if self.port_number not in range(1024, 64001):
            sys.exit("ERROR: Port number must be in range 1024 - 64000 inclusive")

        self.file_name = input_string[3]
        if os.path.isfile(self.file_name) and os.access(self.file_name, os.R_OK):
            sys.exit("ERROR: File already exists locally")

    def create_socket(self):
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.socket.connect((self.IP, self.port_number))
            print(f"CONNECTED TO SERVER ON PORT {self.port_number}")
        except:
            self.socket.close()
            sys.exit(f"ERROR: Could not connect to server on Port {self.port_number}, at {self.IP}")

        
    def file_request(self):
        """send request to server in byte form"""
        filename_in_bytes = bytes(self.file_name, 'utf-8')
        filename_len = int.to_bytes(len(filename_in_bytes), 2, byteorder='big')
        magic_number = int.to_bytes(int(0x497E), 2, byteorder='big')
        type_bytes = int.to_bytes(1, 1, byteorder='big')
        message_to_send = bytearray(magic_number+type_bytes+filename_len+filename_in_bytes)
        #time.sleep(2)
        self.socket.send(message_to_send)

        self.data = self.socket.recv(4096)
        print(f"{self.data}")
        self.socket.close()

    def process_response(self):
        print(int.from_bytes(self.data[0:2], byteorder='big'))
        print(int.from_bytes(self.data[2:3], byteorder='big'))
        print(int.from_bytes(self.data[3:4], byteorder='big'))
        #print(int.from_bytes(self.data[5:9], byteorder='big'))

        if int.from_bytes(self.data[0:2], byteorder='big') != 0x497E:
            print(int.from_bytes(self.data[0:2], byteorder='big'))
            sys.exit("magic number didnt match")
        elif int.from_bytes(self.data[2:3], byteorder='big') != 2:
            sys.exit("wrong type")
            
        elif int.from_bytes(self.data[3:4], byteorder='big') not in [0, 1]:
            sys.exit("Incorrect status code, File corrupted")

        elif int.from_bytes(self.data[3:4], byteorder='big') == 0:
            sys.exit("File does not exist")

        else:
            file_length = int.from_bytes(self.data[4:8], byteorder='big')
            print(file_length)
            print(len(self.data))
            print(len(self.data[8:8+file_length]))
            if len(self.data[8:8+file_length]) != file_length:
                sys.exit("Data corrupted")
            else:
                file_data = self.data[8:8+file_length].decode('utf-8')
                temp = open(self.file_name, 'w')
                temp.write(file_data)
                temp.close()
                print("Written to file")



        
        





def run_client():

    client = Client()
    client.create_socket()
    client.file_request()
    client.process_response()

if __name__ == "__main__":
    run_client()

