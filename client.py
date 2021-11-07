import socket
import argparse
import selectors
from urllib.parse import urlparse
import sys
import signal

sel = selectors.DefaultSelector()

# client tcp socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
USER = ''

def handle_keyboard_input(sock, mask):
    line=sys.stdin.readline()
    message = f'@{USER}: {line}'
    client_socket.send(message.encode())
    do_prompt()


# Display a prompt for the client to type messages
def do_prompt(skip_line=False):
    if (skip_line):
        print("")
    print("> ", end='', flush=True)

# Read each char from the connection
# Return the line at \n character and remove \r character
def read_line(sock):
    done = False
    line = ''
    while (not done):
        char = sock.recv(1).decode()
        if (char == '\r'):
            pass
        elif (char == '\n'):
            done = True
        else:
            line = line + char
    return line


# Handle messages from server
def handle_server_msgs(sock, mask):
    msg = read_line(sock)
    msg_split = msg.split(' ')
    if(msg_split[0]=='DISCONNECT'):
        print("\n[DISCONNECTING FROM SERVER]\n")
        sys.exit(0)
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


    
def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    message=f'DISCONNECT {USER} CHAT/1.0\n'
    client_socket.send(message.encode())
    sys.exit(0)

def main():
    global client_socket
    global USER
    signal.signal(signal.SIGINT, signal_handler)

    USER, HOST, PORT = parser()



    try:
        print(f"\nAttempting Connection\n[Host: {HOST}]\n[Port:{PORT}]")     
        client_socket.connect((HOST,PORT))
    except ConnectionRefusedError:
        print("\nThe connection was refused\n")
        sys.exit(1)
    
    
    # Successful Connection, register new user
    print("Connection Successful!")
    reg_msg = f"REGISTER {USER} CHAT/1.0\n"
    client_socket.send(reg_msg.encode())

    # Receive server response
    server_res = read_line(client_socket)
    response = server_res.split(' ')

    if response[0] != '200':
        print('Error:  An error response was received from the server.  Details:\n')
        print(f"[Server Response]: [{server_res}]")
        print('Exiting now ...')
        sys.exit(1)   
    else:
        print('Registration successful.  Ready for messaging!')
    
    # Set up our selector.

    client_socket.setblocking(False)
    sel.register(client_socket, selectors.EVENT_READ , handle_server_msgs)
    sel.register(sys.stdin, selectors.EVENT_READ| selectors.EVENT_WRITE, handle_keyboard_input)
    
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