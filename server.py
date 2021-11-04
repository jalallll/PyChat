import socket
import signal
import os
import sys
import selectors

# Selector to help select incoming data and connections from multiple sources
sel = selectors.DefaultSelector()

# list of clients connected
client_list = []

def signal_handler(signum, frame):
    print("Interruption received, shutting down server")
    message = "DISCONNECT CHAT/1.0\n"
    for client in client_list:
        client[1].send(message.encode())
    sys.exit()

# Find client socket given the username
def find_client_socket(user_name):
    for client in client_list:
        if client[0].equals(user_name):
            return client
    return None

# Add a client to the client list 
def add_client(user_name, user_socket):
    client_list.append((user_name, user_socket))

def accept_client():


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


if __name__ == '__main__':
    main()