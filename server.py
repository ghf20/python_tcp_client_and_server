"""Server-side commandline application to communicate and exchange data with a client via TCP sockets

Author: George Fraser

-Parameters:
    Accepts via stdin binding port number (integer) between 1024 and 64000 inclusive
        If the port number doesnt conform to these conditions the server will print an error message and terminate
"""
import sys
import socket
import time
import os



class Server():

    def __init__(self):
        """Gets the Port Number from stdin. if it doesnt meet the parameters set out then it throws an error and terminates"""
        input_port_number = sys.argv
        if len(input_port_number) != 2:
            sys.exit("ERROR: Incorrect number of arguments. Enter port number between 1024 and 64000 must be entered")        

        try:
            self.port_number = int(input_port_number[1])
        except ValueError:
            sys.exit("ERROR: Port number must be an integer")

        #Checks the necessary condition of being in the range 1024-64000 inclusive
        if self.port_number not in range(1024, 64001):
            sys.exit("ERROR: Port number must be in range 1024 - 64000 inclusive")

        self.host = '127.0.0.1' #Local host
        self.socket = None
        self.connection = None
        self.connection_address = None
        self.data = None
        self.file_to_send = None
        self.status_code = 1
        
    def create_bind(self):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #Allows socket to be reuse port if an error occurs and doesnt close correctly

        try:
            self.socket.bind((self.host, self.port_number))
        except socket.error as error_message:
            self.socket.close()
            sys.exit(f"ERROR: Failed to connect to Client, Error code: {error_message[0]}, Message: {error_message[1]}")
        
        self.socket.listen()

    def accept_connection(self, timetimeout=1):
        
        print(f"Listenting for connection on {self.port_number}")
        self.connection, self.connection_address = self.socket.accept()
        self.connection.settimeout(1.0) #Started connection timeout at 1.0 seconds
        temp_time = time.localtime()
        current_time = time.strftime("%a, %d %b %Y %H:%M:%S", temp_time)
        print(f"Connected to client at IP: {self.connection_address[0]} on Port: {self.port_number} at {current_time}")
        
        self.data = self.connection.recv(1029)
        self.connection.settimeout(None)
        

        #check data is valid
        if int.from_bytes(self.data[0:2], byteorder='big') != 0x497E:
            print("ERROR: Magic number didnt match CONNECTION CLOSED")
            self.connection.close()
            return 0

        elif int.from_bytes(self.data[2:3], byteorder='big') != 1:
            print("wrong type")
            self.connection.close()
            return 0
            
        elif int.from_bytes(self.data[3:5], byteorder='big') not in range(1, 1025):
            print("File not correct size")
            self.connection.close()
            return 0
        
        size_of_message = int.from_bytes(self.data[3:5], byteorder='big')
        file_to_send = self.data[5:5+size_of_message].decode('utf-8')

        if not(os.path.isfile(file_to_send) and os.access(file_to_send, os.R_OK)):
            print(f"{file_to_send} does not exist CONNECTION CLOSED")
            self.connection.close()
            return 0
        
        elif len(self.data) != 5+size_of_message:
            self.status_code = 0
        else:
            self.file_to_send = file_to_send
        return 1
        

    def send_respose(self):
        
        magic_number = int.to_bytes(int(0x497E), 2, byteorder='big')
        type_byte = int.to_bytes(2, 1, byteorder='big')
        status_code = int.to_bytes(self.status_code, 1, byteorder='big')
        if self.status_code != 0:
            data_length = int.to_bytes(os.path.getsize(self.file_to_send), 4, byteorder='big')
        else:
            data_length = int.to_bytes(0, 4, byteorder='big')

        with open(self.file_to_send, 'rb') as file:
            file_data = file.read() if self.status_code != 0 else None
            if file_data is not None:
                
                response = magic_number + type_byte + status_code + data_length + file_data
                
            else:
                response = magic_number + type_byte + status_code + data_length
            file.close()
        
        self.connection.sendall(response)
        print(f"{len(response)} bytes transfered to {self.connection_address[0]}")
        self.connection.close()
        
        
        

def run_server():
    try:
        serv_ = Server()  # Start Server instance
        serv_.create_bind() #create socket, bind to port and accept connection
        
        while True:
            processing_code = serv_.accept_connection()
            while processing_code == 0:
                processing_code = serv_.accept_connection()
            
            serv_.send_respose()
    except KeyboardInterrupt:
        serv_.socket.close()
        sys.exit("\nERROR: Keyboard interupt, CONNECTION CLOSED")
        

if __name__ == "__main__":
    run_server()


