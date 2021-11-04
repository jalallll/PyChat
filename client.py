import socket
import argparse
import selectors
from urllib.parse import urlparse
import sys

# Username
USER = ''
# Server host
HOST = ''
# Server port
PORT = ''
# client tcp socket
SOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Parse username, server hostname, server port from command line args
def parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("user", help="user name for this user on the chat service")
    parser.add_argument("server", help="Server URL: chat://host:port")
    args = parser.parse_args()
    
    try:
        server_address = urlparse(args.server)
        if ((server_address.scheme != 'chat') or (server_address.port == None) or (server_address.hostname == None)):
            raise ValueError
        HOST = server_address.hostname
        PORT = server_address.port
    except ValueError:
        print('Error:  Invalid server.  Enter a URL of the form: chat://host:port')
        sys.exit(1)
    USER = args.user
    return (USER, HOST, PORT)

# Connect to server
def connect(USER, HOST, PORT):
    try:
        print(f"Attempting Connection\n[Host: {HOST}]\n[Port:{PORT}]")
        SOCK.connect((HOST,PORT))
    except ConnectionRefusedError:
        print("The connection was refused")
    
    

def main():
    global USER
    global SOCK
    global HOST
    global PORT
    USER, HOST, PORT = parser()
    connect(USER, HOST, PORT)
    print("Connection Successful!")
    # Send registration message to server
    reg_msg = f"REGISTER {USER} CHAT/1.0\n"
    SOCK.send(reg_msg.encode())



if __name__ == '__main__':
    main()