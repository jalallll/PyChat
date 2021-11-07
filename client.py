import socket
import argparse
import select
from urllib.parse import urlparse
import sys
import signal


error_msgs = {
    'INVALID_REG': '[SERVER]: 400 invalid response',
    'USER_EXISTS': '[SERVER]: 401 user already registered',
    'SERVER_DC': '[SERVER]: DISCONNECT CHAT/1.0'
}

def main():
    global client_socket, USER
    # init client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    USER, HOST, PORT = parser()
    print(USER)

    # Attempt connection to server
    try:
        print(f"\nAttempting Connection\n[Host: {HOST}]\n[Port:{PORT}]")     
        client_socket.connect((HOST,PORT))
    except ConnectionRefusedError:
        print("\nThe connection was refused\n")
        sys.exit()
    
    client_socket.setblocking(False)
    #register
    reg_msg = f"REGISTER {USER} CHAT/1.0"
    print(reg_msg)
    client_socket.send(reg_msg.encode())

    # Watch for ctrl+ c events
    def signal_handler(sig, frame):
        print('\nInterrupt received, shutting down ...')
        message=f'DISCONNECT {USER} CHAT/1.0'
        message.strip('\n')
        client_socket.send(message.encode())
        
    
    # Initialize signal
    signal.signal(signal.SIGINT, signal_handler)

    
    # Set up the selector.
    while 1:
        try:
            while 1:
                client_socket.setblocking(False)
                readers, writers, errors = select.select([sys.stdin, client_socket], [], [])
                for reader in readers:
                    # We can read from client socket
                    if reader == client_socket:
                        response = reader.recv(1024)
                        words = response.decode().split()
                        res = response.decode().strip('\n')
                        if res in error_msgs.values():
                            print(res)
                            client_socket.close()
                            print("Exiting...")
                            sys.exit()
                        # if words[1]=='!attach':
                        #     file = open(f"new_client_{words[2]}", 'wb')
                        #     chunk = reader.recv(1024)
                        #     while chunk:
                        #         file.write(chunk)
                        #         chunk = reader.recv(1024)
                        #     file.close()
                        print(f"{res}\n")

                    # We can read from standard input
                    else:
                        msg = sys.stdin.readline()
                        words = msg.split()
                        if words[0]=="!attach":
                            send_msg = f"@{USER}: {msg}"
                            client_socket.send(send_msg.encode())
                            name = words[1]
                            file = open(name, 'rb')
                            data = file.read(1024)
                            while data:
                                client_socket.send(data)
                                data = file.read(1024)
                            file.close()
                        else:
                            send_msg = f"@{USER}: {msg}"
                            client_socket.send(send_msg.encode())
                        print('\n')
        except BlockingIOError as e: 
            pass
        except Exception as e: 
            print(e) 
            sys.exit()

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
        sys.exit()




if __name__ == '__main__':
    main()