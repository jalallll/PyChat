import socket
import signal
import os
import sys
import selectors

# Main function
def main():
    global sel, client_list
    # Initialize selector
    sel = selectors.DefaultSelector()
    # list of clients connected (username, socket)
    client_list = []
    
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
    sel.register(server_socket, selectors.EVENT_READ, )

    # Keep the server running forever, waiting for connections or messages.
    while(True):
        events = sel.select(timeout=None)
        for key, mask in events:
            # Need to accept connection from new listening socket
            if key.data is None:
                accept_client(key.fileobj, mask)
            # Accept msg from pre-connected socket
            else:
                accept_message(key.fileobj, mask)


# send response to all connected clients
def message_all(msg):
    for client in client_list:
        client[1].send(msg.encode())

# forward msg from specified socket to other sockets
def forward_message(sock, msg):
    for client in client_list:
        if client[1]!=sock:
            conn = client[1]
            conn.send(msg.encode())

# Remove client socket by username
def remove_by_username(user_name):
    for client in client_list:
        if client[0] == user_name:
            client_list.remove(client)

# handle ctrl + c
def signal_handler(signum, frame):
    print("Interruption received, shutting down server")
    message = "DISCONNECT CHAT/1.0\n"
    for client in client_list:
        sock = client[1]
        sock.send(message.encode())
    sys.exit()

# Get client socket given the username
def get_socket_by_username(user_name):
    for client in client_list:
        if client[0] == user_name:
            return client[1]
    return None

# Get client username given the socket
def get_username_by_socket(sock):
    for client in client_list:
        if client[1] == sock:
            return client[0]
    return None

# Accept message from client socket
def accept_message(sock, mask):
    msg = sock.recv(1024).decode() 
    # If message received is not empty
    if msg:
        user_name = get_username_by_socket(sock)
        words = msg.split(' ')
        print(msg)
        # Check for disconnect message
        if (words[1]=='DISCONNECT'):
            # Send DC response to all clients connected 
            dc_res = f"Disconnecting @{user_name}\n"
            print(dc_res)
            msg = "DISCONNECT".encode()
            sock.send(msg)
            remove_by_username(user_name)
            sel.unregister(sock)
            sock.close()
        # check for help msg    
        elif (words[1].strip('\n')=='help'):
            msg = "[SERVER]:Help:"
            sock.send(msg.encode())
        else:
            # Send the message to every client (except the sender)
            forward_message(sock, msg)


# Add a client to the client list 
def add_client(user_name, user_socket):
    client_list.append((user_name, user_socket))

# Accept new inbound client connections
def accept_client(sock, mask):
    # Accept connection
    client_sock, addr = sock.accept()
    # Set client socket to non blocking
    client_sock.setblocking(False)
    print(f"\nNew client connected from: {addr}")

    # Read message from socket and split between spaces
    msg = client_sock.recv(1024).decode()
    msg_split = msg.split(' ')

    # Registration message not proper format (send error response)
    if(len(msg_split) != 3) or (msg_split[0] != 'REGISTER') or (msg_split[2].strip('\n') != 'CHAT/1.0'):
        print("Registration wrong format")
        print(f"split {msg_split}")
        res = "400 invalid response"
        client_sock.send(res.encode())
        client_sock.close()
    # Registration msg in proper format
    else:
        user_name = msg_split[1]
        # If username is unique
        if get_socket_by_username(user_name) == None:
            # Append client object to client_list
            add_client(user_name, client_sock )
            # Send registration message to client and print to server 
            welcome_msg = f"@Server: Welcome {user_name}!"
            message_all(welcome_msg)
            print(welcome_msg)
            res = "200 registration successful\n"
            client_sock.send(res.encode())
            # Register client socket and wait for read events (inbound messages from client)
            sel.register(client_sock, selectors.EVENT_READ, accept_message)
        else:
            res = "401 user already registered\n"
            print(res)
            client_sock.send(res.encode())
            client_sock.close()


if __name__ == '__main__':
    main()