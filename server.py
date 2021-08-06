"""Server-side commandline application to communicate and exchange data with a client via TCP sockets

Author: George Fraser

-Parameters:
    Accepts via stdin binding port number (integer) between 1024 and 64000 inclusive
        If the port number doesnt conform to these conditions the server will print an error message and terminate
"""
import sys
import socket



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
            sys.exit("Port number must be in range 1024 - 64000 inclusive")

        self.host = '127.0.0.1' #Local host
        

    def create_bind_accept(self):

        current_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        current_socket.bind((self.host, self.port_number))

        try:
            #WILL THIS EVER STOP?
            current_socket.listen()
        except socket.error:
            current_socket.close()
            sys.exit("Failed to connect to Client")
        
        #not accepting connection
        connection, address = current_socket.accept()
        print(f"SUCCESFULLY CONNECTED TO CLIENT ON {self.port_number}")


def run_server():
    serv_ = Server()  # Start Server instance

    serv_.create_bind_accept() #create socket, bind to port and accept connection


if __name__ == "__main__":
    run_server()


