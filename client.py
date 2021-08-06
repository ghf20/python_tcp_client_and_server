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

        input_string = sys.argv
        if len(input_string) != 4:
            sys.exit("Incorrect amount of arguments")

        
        try:
            
            self.IP = input_string[1]
            socket.getaddrinfo(self.IP, None)   
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
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            client_socket.connect((self.IP, self.port_number))
            print(f"CONNECTED TO SERVER ON PORT {self.port_number}")
        except:
            client_socket.close()
            sys.exit(f"ERROR: Could not connect to server on Port {self.port_number}, at {self.IP}")



def run_client():

    client = Client()
    client.create_socket()


if __name__ == "__main__":
    run_client()

