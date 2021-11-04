import socket
import signal
import os
import sys
import selectors

# Default messages
CLIENT_DISCONNECT_MSG = "DISCONNECT CHAT/1.0"
SERVER_DISCONNECT_RES = "Server: Disconnecting user"
SERVER_EMPTY_MSG_RES = "DO NOT SEND BLANK MESSAGES"

# Selector to help select incoming data and connections from multiple sources
sel = selectors.DefaultSelector()

# list of clients connected
client_list = []

# send response to all connected clients
def message_all(msg):
    for client in client_list:
        client[1].send(msg.encode())



# Remove client socket
def remove_client(sock):
    for client in client_list:
        if client[1] == sock:
            client_list.remove(client)


def signal_handler(signum, frame):
    print("Interruption received, shutting down server")
    message = "DISCONNECT CHAT/1.0\n"
    for client in client_list:
        sock = client[1]
        sock.send(message.encode())
    sys.exit()

# Get client socket given the username
def get_client_socket(user_name):
    for client in client_list:
        if client[0] == user_name:
            return client[1]
    return None

# Get client username given the socket
def get_client_user_name(sock):
    for client in client_list:
        if client[1] == sock:
            return client[0]
    return None

# Accept message from client socket
def accept_message(sock, mask):
    msg = read_line(sock)

    # Check if message received is empty
    if msg == '':
        print('Closing connection')
        sel.unregister(sock)
        sock.close()
    # If message received is not empty
    else:
        user_name = get_client_user_name(sock)
        words = msg.split(' ')
        print(msg)
        # Check for disconnect message
        print(f"words[0]: {words}")
        if (words[1]=='DISCONNECT'):
            # Send DC response to all clients connected 
            dc_res = f"Disconnecting @{user_name}\n"
            print(dc_res)
            remove_client(user_name)
            sel.unregister(sock)
            sock.close()
        else:
            # Send the message to every client (except the sender)
            for client in client_list:
                if client[0] == user_name:
                    continue
                client_sock = client[1]
                print(f"line 81 msg: {msg}")
                fwd_msg = f"{msg}\n"
                client_sock.send(fwd_msg.encode())

            


# Add a client to the client list 
def add_client(user_name, user_socket):
    client_list.append((user_name, user_socket))

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


# Accept new inbound client connections
def accept_client(sock, mask):

    # Accept connection
    client_sock, addr = sock.accept()

    print(f"\nNew client connected from: {addr}")

    # Read message from socket and split between spaces
    msg = read_line(client_sock)
    print(f"line 117 {msg}")
    msg_split = msg.split(' ')

    # Registration message not proper format (send error response)
    if(len(msg_split) != 3) or (msg_split[0] != 'REGISTER') or (msg_split[2] != 'CHAT/1.0'):
        print("Registration wrong format")
        res = "400 invalid response"
        client_sock.send(res.encode())
        client_sock.close()
    # Registration msg in proper format
    else:
        user_name = msg_split[1]
        print(f"line 124: username {user_name}")
        # If username is unique
        if get_client_socket(user_name) == None:
            # Append client object to client_list
            print(f"line 130: {len(client_list)}")
            add_client(user_name, client_sock )
            print(f"line 132: {len(client_list)}")

            # Send registration message to client and print to server 
            welcome_msg = f"@Server: Welcome {user_name}!"
            print(welcome_msg)
            res = "200 registration successful\n"
            client_sock.send(res.encode())

            # Set client socket to non blocking
            client_sock.setblocking(False)
            print("sel reg")
            # Register client socket and wait for read events (inbound messages from client)
            sel.register(client_sock, selectors.EVENT_READ, accept_message)
        else:
            res = "401 user already registered\n"
            print(res)
            client_sock.send(res.encode())
            client_sock.close()

# Main function
def main():

    # signal handler for ctrl + c event
    signal.signal(signal.SIGINT, signal_handler)
    # create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # bind socket to any interface and free port
    server_socket.bind(('', 0))
    # Print message indicating server host and port
    print(f"~ ~ ~ \nWaiting for clients at \nHost:{server_socket.getsockname()[0]} \nPort: {server_socket.getsockname()[1]}\n~ ~ ~")

    # Listen for 100 connections
    server_socket.listen(100)

    # make server socket non blocking
    server_socket.setblocking(False)

    # Register server socket for read operations
    sel.register(server_socket, selectors.EVENT_READ, accept_client)

    # Keep the server running forever, waiting for connections or messages.
    while(True):
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)    


if __name__ == '__main__':
    main()