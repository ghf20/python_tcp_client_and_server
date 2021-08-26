"""Server-side commandline application to communicate and exchange data with a client via TCP sockets

Author: George Fraser

-Parameters:
    Accepts via stdin binding port number (integer) between 1024 and 64000 inclusive
        If the port number doesnt conform to these conditions the server will print an error message and terminate

Example command to start server.py is: 
    python3 server.py <portnumber>

Things to note:
    - Only configured to run on localhost 127.0.0.1
    - Will only transfer file if it exists in the same directory as server.py
"""
import sys
import socket
import time
import os

class Server():

    def __init__(self):
        
        input_port_number = sys.argv
        if len(input_port_number) != 2:
            sys.exit("ERROR: Incorrect number of arguments")        

        try:
            self.port = int(input_port_number[1])
        except ValueError: #CATCHES INSTANCE WHERE PORT NUMBER IS NOT AN INTEGER
            sys.exit("ERROR: Port number must be an integer")

        #Checks port inrange 1024-64000 inclusive
        if self.port not in range(1024, 64001):  
            sys.exit("ERROR: Port number must be in range 1024-64000 inclusive")

        self.host = '127.0.0.1' #Local host
        self.socket = None
        self.conn = None #socket connection
        self.con_add = None  #address of connected client
        self.data = None #file data to transfer
        self.file_to_send = None #filename for file transfer
        self.status_code = 1
        
    def create_bind(self):

        #CREATE SOCKET WITH IPV4 AND TCP PROTOCOLS
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #Allows user to connect to same port after connection is closed 
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 

        try:
            self.socket.bind((self.host, self.port))
        except socket.error:
            self.socket.close()
            sys.exit(f"ERROR: Failed to bind to Client on {self.host}:{self.port}")
        
        try:
            self.socket.listen()
        except socket.error:
            self.socket.close()
            sys.exit(f"ERROR: Failed to connect on {self.host}:{self.port}") 

    def accept_connection(self):
        
        #ACCEPTS INCOMING CONNECTION ON SPECIFIED IP AND PORT
        self.conn, self.con_add = self.socket.accept() 

        try:
            self.conn.settimeout(1.0) #Started connection timeout at 1.0 seconds
            temp_time = time.localtime() #EXTRACT LOCAL TIME FROM SERVER
            current_time = time.strftime("%a, %d %b %Y %H:%M:%S", temp_time)
            print(f"Connected to client at {self.con_add[0]}:{self.port} at {current_time}")
            self.data = self.conn.recv(1029) #RECIEVE FILE REQUEST FROM CLIENT
            self.conn.settimeout(None)
            
        except socket.timeout: #IF FILE REQUEST FAILS, SOCKET CLOSES AND LISTENS AGAIN
            self.conn.close()
            print("ERROR: Connection timed out")
            
        
    def process_request(self):
        """Processes incoming file request from server. 
            - If fuction returns 0, file request was invalid. Will close connection. 
                Response sent only if file does not exist or filename is corrupt
            - If returns 1, file requsest was valid. Will continue to send file"""

        #ENSURE FILE REQUEST HEADER MATCHES MAGIC NUMBER (0x487E)
        if int.from_bytes(self.data[0:2], byteorder='big') != 0x497E: 
            print("ERROR: Magic number didnt match CONNECTION CLOSED")
            self.conn.close()
            return 0 

        #ENSURE TYPE FIELD IS EQUAL TO 1
        if int.from_bytes(self.data[2:3], byteorder='big') != 1: 
            print("ERROR: WRONG TYPE, CONNECTION CLOSED")
            self.conn.close()
            return 0

        #ENSURE THAT 1 <= FILENAME LEN<= 1024 BYTES    
        if int.from_bytes(self.data[3:5], byteorder='big') not in range(1, 1025): 
            print("ERROR: File not correct size")
            self.conn.close()
            return 0
        
        size_of_message = int.from_bytes(self.data[3:5], byteorder='big') #FILENAME LEN
        file_to_send = self.data[5:5+size_of_message].decode('utf-8') #DECODE THE FILENAME
        
        
        if not(os.access(file_to_send, os.R_OK)): #CHECKING IF FILE EXISTS LOCALLY
            self.status_code = 0 #SET TO ZERO AS FILE DOESNT EXIST LOCALLY
            print(f"ERROR: {file_to_send} does not exist on server")
        
        #CHECK THAT THE LEN(FILENAME) == FILENAME LEN i.e has not been corrupted
        elif len(self.data) != 5+size_of_message: 
            self.status_code = 0
        
        else: #DATA IS VALID SO CONTINUE TO SENDING DATA TO CLIENT
            self.file_to_send = file_to_send
        return 1
        

    def send_respose(self):
        
        magic_number = int.to_bytes(int(0x497E), 2, byteorder='big')
        type_byte = int.to_bytes(2, 1, byteorder='big')
        status_code = int.to_bytes(self.status_code, 1, byteorder='big')
        file_data = None

        if self.status_code != 0:
            try: 
                data_len = int.to_bytes(os.path.getsize(self.file_to_send), 4, byteorder='big')
                file = open(self.file_to_send, 'rb')
                file_data = file
                response = magic_number + type_byte + status_code + data_len
                
            except OverflowError: #datalength field overflow
                print("ERROR: Filesize must be <= 4GB, file not transfered")
                data_len = int.to_bytes(1, 4, byteorder='big') #show transfer is corrupted
                response = magic_number + type_byte + status_code + data_len 
                file_data = None
        
        else: #WILL ONLY HAPPEN IF FILE DOES NOT EXIST OR FILENAME WAS CORRUPTED
            data_len = int.to_bytes(0, 4, byteorder='big')
            response = magic_number + type_byte + status_code + data_len
        

        self.conn.sendall(response)
        if file_data is not None:
            self.conn.sendfile(file_data)
            print(f"{len(response)+os.path.getsize(self.file_to_send)} bytes sent to {self.con_add[0]}")
        else:
            print(f"{len(response)} bytes sent to {self.con_add[0]}")
        self.conn.close()
        
        
def run_server():
    try:
        serv_ = Server()  # Start Server instance
        serv_.create_bind() #create socket, bind to port and accept connection
        
        while True: #CREATES INFINITE LOOP LISTENING ON ENTERED PORT NUMBER
            serv_.accept_connection()
            processing_code = serv_.process_request()

            #LOOPS UNTIL AN UNCORRUPTED FILE REQUEST IS MADE BY THE CLIENT
            while processing_code == 0: 
                serv_.accept_connection()
                processing_code = serv_.process_request()
            try:
                serv_.send_respose() #SEND FILERESPONSE INCLUDING FILE DATA TO CLIENT
            except BrokenPipeError:
                print("ERROR: Client timed out, Transfer aborted")
    
    except KeyboardInterrupt:
        serv_.socket.close()
        sys.exit("\nERROR: Keyboard interupt, CONNECTION CLOSED")
        

if __name__ == "__main__":
    run_server()

