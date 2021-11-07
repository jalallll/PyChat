import socket
import argparse
import select
from urllib.parse import urlparse
import sys
import signal


def main():
    global client_socket, USER
    # init client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    signal.signal(signal.SIGINT, signal_handler)
    USER, HOST, PORT = parser()
    print(USER)
    
    # Attempt connection to server
    try:
        print(f"\nAttempting Connection\n[Host: {HOST}]\n[Port:{PORT}]")     
        client_socket.connect((HOST,PORT))
        client_socket.setblocking(False)
    except ConnectionRefusedError:
        print("\nThe connection was refused\n")
        sys.exit(1)
    
    
    #register
    reg_msg = f"REGISTER {USER} CHAT/1.0\n"
    print(reg_msg)
    client_socket.send(reg_msg.encode())

    # Set up our selector.
    while 1:
        readers, writers, errors = select.select([sys.stdin, client_socket], [], [])
        for reader in readers:
            if reader is client_socket:
                res = reader.recv(2000).decode()
                response = res.split(' ')
                if response[0] == "400" or response[0] == "401":
                    print("error")
                    sys.exit(1)
                print(res)
            else:
                msg = sys.stdin.readline()
                send_msg = f"@{USER}: {msg}"
                client_socket.send(send_msg.encode())

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


if __name__ == '__main__':
    main()