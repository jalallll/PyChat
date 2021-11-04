import socket
import argparse
import selectors
from urllib.parse import urlparse
import sys

sel = selectors.DefaultSelector()

 # client tcp socket
SOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
USER = ""

def handle_keyboard_input(sock, mask):
    line=sys.stdin.readline()
    message = f'@{USER}: {line}'
    SOCK.send(message.encode())
    do_prompt()

# Read each char from the connection
# Return the line at \n character and remove \r character
def read_line(sock):
    flag = True
    line = ''
    while flag:
        char = sock.recv(1).decode()
        if char == '\n':
            flag = False
        elif char == '\r':
            pass
        else:
            line = line + char
    return line

# Display a prompt for the client to type messages
def do_prompt(skip_line=False):
    if (skip_line):
        print("")
    print("> ", end='', flush=True)

# Handle messages from server
def handle_server_msgs(sock, mask):
    msg = read_line(sock)
    msg_split = msg.split()
    if(msg_split[0]=='DISCONNECT'):
        print("\n[DISCONNECTING FROM SERVER]\n")
        sys.exit()
    else:
        print(msg)
        do_prompt()

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
        USER = args.user
        return (USER, HOST, PORT)
    except ValueError:
        print('Error:  Invalid server.  Enter a URL of the form: chat://host:port')
        sys.exit(1)

# Connect to server
def connect(USER, HOST, PORT):
    try:
        print(f"\nAttempting Connection\n[Host: {HOST}]\n[Port:{PORT}]")
       
        SOCK.connect((HOST,PORT))

        # Send registration message to server
        reg_msg = f"REGISTER {USER} CHAT/1.0\n"
        SOCK.send(reg_msg.encode())

        server_res = read_line(SOCK)
        reponse = server_res.split(' ')

        if reponse[0] != '200':
            print('Error:  An error response was received from the server.  Details:\n')
            print(reponse)
            print('Exiting now ...')
            sys.exit(1)   
        else:
            print('Registration successful.  Ready for messaging!')
            return SOCK
    except ConnectionRefusedError:
        print("\nThe connection was refused\n")
        sys.exit(1)
    
    

def main():
    global SOCK
    global USER
    USER, HOST, PORT = parser()
    SOCK = connect(USER, HOST, PORT)
    print("Connection Successful!")
    # If an error is returned from the server, we dump everything sent and
    # exit right away.  
    
    

    # Set up our selector.

    SOCK.setblocking(False)
    sel.register(SOCK, selectors.EVENT_READ, handle_server_msgs)
    sel.register(sys.stdin, selectors.EVENT_READ, handle_keyboard_input)
    
    # Prompt the user before beginning.

    do_prompt()

    # Now do the selection.

    while(True):
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)    
    




if __name__ == '__main__':
    main()