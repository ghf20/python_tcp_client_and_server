"""Client-side commandline application to communicate and exchange 
    data with a server via TCP sockets

Author: George Fraser

-Parameters:
    IP ADDRESS:
        Accepts via stdin a valid Ipv4 IP address or hostname i.e localhost
    Port Number:
        Accepts via stdin a port number (integer) between 1024 and 64000 inclusive

        If the port number doesnt conform to these conditions 
            the server will print an error message and terminate
    File to transfer
        Accepts via stdin a filename that you wish to transfer 
            from the server

Example command to start client.py is: 
    python3 client.py 127.0.0.1 <port_number> <filename>

Things to note:
    - server.py must be running first before client.py in order to transfer files
    - Only configured to run on localhost 127.0.0.1
    - Will only transfer file if file does not exist in the directory containing client.py
    - Port number must match port listening on server.py
    - filename must not exceed 1024 bytes
    - can only transfer one file at a time
"""

import socket
import sys
import os


class Client():

    def __init__(self):

        self.socket = None
        self.data = bytearray()

        input_string = sys.argv
        if len(input_string) != 4:
            sys.exit("Incorrect amount of arguments")

        try:
            self.IP = socket.gethostbyname(input_string[1]) #for IPV4 addresses  
        except socket.error:
            sys.exit("ERROR: Invaild IP address, must be IPv4 Address")

        try:
            self.port_number = int(input_string[2])
        except ValueError:
            sys.exit("ERROR: Value must be an integer")

        
        if self.port_number not in range(1024, 64001):
            sys.exit("ERROR: Port number must be in range 1024 - 64000 inclusive")

        self.file_name = input_string[3]
        if os.access(self.file_name, os.R_OK):
            sys.exit("ERROR: File already exists is current local directory")

    def create_socket(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error:
            sys.exit("ERROR: Could not create socket")

        self.socket.settimeout(1) #SOCKET WILL TIMEOUT IF FAILS TO CONNECT
        
        try:
            self.socket.connect((self.IP, self.port_number))
            print(f"CONNECTED TO SERVER ON PORT {self.port_number}")

        except (socket.error, socket.timeout):
            self.socket.close()
            sys.exit(f"ERROR: Could not connect to server on {self.IP}:{self.port_number}")
        self.socket.settimeout(None)
        
    def file_request(self):
        """send request to server in byte form"""
        magic_number = int.to_bytes(int(0x497E), 2, byteorder='big') 
        type_bytes = int.to_bytes(1, 1, byteorder='big')
        filename_in_bytes = bytes(self.file_name, 'utf-8') #ENCODE FILENAME IN BYTES
        filename_len = int.to_bytes(len(filename_in_bytes), 2, byteorder='big') 
       
        message_to_send = bytearray(magic_number+type_bytes+filename_len+filename_in_bytes)
        self.socket.send(message_to_send)
        
        #WAIT FOR FILE RESPONSE FROM SERVER
        try:
            self.socket.settimeout(1)
            while True: #CREATE INFINITE LOOP TO RECIEVE DATA IN CHUNKS <= 4096 BYTES
                data = self.socket.recv(4096)
                if data:
                    self.data += data
                else:
                    break

            self.socket.settimeout(None)
            self.socket.close()

        except socket.timeout:
            self.socket.close()
            sys.exit("ERROR: Connection timed out")
        


    def process_response(self):

        if int.from_bytes(self.data[0:2], byteorder='big') != 0x497E:
            sys.exit("ERROR: magic number didnt match 0x497E")
        elif int.from_bytes(self.data[2:3], byteorder='big') != 2:
            sys.exit("ERROR: Wrong type in file response. Needs to equal 1")
            
        elif int.from_bytes(self.data[3:4], byteorder='big') not in [0, 1]:
            sys.exit("ERROR: Incorrect status code, File corrupted")

        elif int.from_bytes(self.data[3:4], byteorder='big') == 0:
            sys.exit("ERROR: File does not exist on server")

        else:
            file_length = int.from_bytes(self.data[4:8], byteorder='big')

            #CHECKING THE FILE IS EXACTLY AS BIG AS IT IS SUPPOSED TO BE
            if len(self.data[8:8+file_length]) != file_length:
                sys.exit("ERROR: File is incorrect lenth, data corrupted") 
            else:
                file_data = self.data[8:8+file_length]
                temp = open(self.file_name, 'wb')
                temp.write(file_data)
                temp.close()
                print(f"{len(self.data)} bytes recieved. Written to file '{self.file_name}'")




def run_client():

    client = Client()
    client.create_socket()
    client.file_request()
    client.process_response()

if __name__ == "__main__":
    run_client()

