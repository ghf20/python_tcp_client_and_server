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
        if len(input_port_number) > 2:
            sys.exit("ERROR: Too many arguments")        

        try:
            self.port_number = int(input_port_number[1])
        except ValueError:
            sys.exit("Value must be an integer")

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

        self.socket.bind((self.host, self.port_number))

        try:
            #WILL THIS EVER STOP?
            self.socket.listen()
        except socket.error:
            self.socket.close()
            sys.exit("Failed to connect to Client")
        
    def accept_connection(self, timetimeout=1):

        self.connection, self.connection_address = self.socket.accept()
        self.connection.settimeout(1.0) #Started connection timeout at 1.0 seconds
        temp_time = time.localtime()
        current_time = time.strftime("%a, %d %b %Y %H:%M:%S", temp_time)
        print(f"Connected to client at IP: {self.connection_address[0]} on Port: {self.port_number} at {current_time}")
        
        self.data = self.connection.recv(1029)
        self.connection.settimeout(None)
        

        #check data is valid
        if int.from_bytes(self.data[0:2], byteorder='big') != 0x497E:
            print(int.from_bytes(self.data[0:2], byteorder='big'))
            sys.exit("magic number didnt match")
        elif int.from_bytes(self.data[2:3], byteorder='big') != 1:
            print(int.from_bytes(self.data[2:3], byteorder='big'))
            sys.exit("wrong type")
            
        elif int.from_bytes(self.data[3:5], byteorder='big') not in range(1, 1025):
            sys.exit("File not correct size")
        size_of_message = int.from_bytes(self.data[3:5], byteorder='big')
        
        file_to_send = self.data[5:5+size_of_message].decode('utf-8')
        
        if not(os.path.isfile(file_to_send) and os.access(file_to_send, os.R_OK)) or len(self.data) != 5+size_of_message:
            self.status_code = 0
        else:
            self.file_to_send = file_to_send
        

    def send_respose(self):
        
        magic_number = int.to_bytes(int(0x497E), 2, byteorder='big')
        type_byte = int.to_bytes(2, 1, byteorder='big')
        status_code = int.to_bytes(self.status_code, 1, byteorder='big')
        if self.status_code != 0:
            data_length = int.to_bytes(os.path.getsize(self.file_to_send), 4, byteorder='big')
        else:
            data_length = int.to_bytes(0, 4, byteorder='big')

     
        file_data = str.encode(open(self.file_to_send).read(), encoding='utf-8') if self.status_code != 0 else None
        if file_data is not None:
            print([magic_number, type_byte ,status_code, data_length, file_data])
            response = magic_number + type_byte + status_code + data_length + file_data
            print(response)
        else:
            response = magic_number + type_byte + status_code + data_length
        
        self.connection.sendall(response)
        self.socket.close()
        print("respose sent")
        
        

def run_server():
    serv_ = Server()  # Start Server instance
    serv_.create_bind() #create socket, bind to port and accept connection
    serv_.accept_connection()
    serv_.send_respose() 
    


if __name__ == "__main__":
    run_server()


