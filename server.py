import socket
import signal
import os
import sys
import selectors



# Main function
def main():
    global sel, client_list, SERVER_RESPONSES, SERVER_COMMANDS, server_socket

    # Initialize selector
    sel = selectors.DefaultSelector()

    # list of clients connected (username, socket)
    client_list = []

    # list of server responses
    SERVER_RESPONSES = {
    'INVALID_REG': '400 invalid response',
    'USER_EXISTS': '401 user already registered',
    'SERVER_DC': 'DISCONNECT CHAT/1.0',
    'REG_SUCCESS': '200 registration successful'
    }
    SERVER_COMMANDS = {
        '!list': 'List all users',
        '!follow term': 'Follow the specific term (if you are NOT currently following it)' ,
        '!unfollow term': 'Unfollow the specific term (if you are currently following it)',
        '!follow @user': 'Follow the specific user (if you are NOT currently following it)',
        '!unfollow @user': 'Unfollow the specific user (if you are currently following it',
        '!attach filename @user': 'Send filename to user',
        '!attach filename term': 'Send filename to everyone following a specific term'
    }
    
    
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


    # handle ctrl + c
    def signal_handler(signum, frame):
        print("\nShutting down server due to ctrl+c event...")
        message_all(SERVER_RESPONSES['SERVER_DC'])
        sys.exit()
    
    # signal handler for ctrl + c event
    signal.signal(signal.SIGINT, signal_handler)

    # Register server socket for read operations
    sel.register(server_socket, selectors.EVENT_READ, )

    # Keep the server running forever, waiting for connections or messages.
    while(True):
        try:
            events = sel.select(timeout=None)
            for key, mask in events:
                # Need to accept connection from new listening socket
                if key.data is None:
                    accept_client(key.fileobj, mask)
                # Accept msg from pre-connected socket
                else:
                    accept_message(key.fileobj, mask)
        except BlockingIOError as e:
            pass
        except Exception as e:
            print(e)


# Accept message from client socket
def accept_message(sock, mask):
    msg = sock.recv(1024).decode().strip('\n')
    following = get_Following(sock)

    # If message received is not empty
    if msg:
        user_name = get_username_by_socket(sock)
        words = msg.split()
        print(f"\n{msg}")
        # Check for disconnect message
        if (words[0]=='DISCONNECT' and words[1]==user_name and words[2]=='CHAT/1.0'):
            remove_sock(sock)
            sel.unregister(sock)
            dc_res = f"Disconnected @{user_name}\n"
            message_all(dc_res)
            sock.close()
        elif (words[1].startswith('!')):
        # check for help command    
            if (words[1]=='!help'):
                for key in SERVER_COMMANDS:
                    msg = f"{key}: {SERVER_COMMANDS[key]}"
                    message(sock, msg)
            # check for !list command
            elif (words[1]=='!list'):
                list_res = getAll()
                message(sock, list_res)
            # check for !exit command
            elif words[1]=='!exit':
                remove_sock(sock)
                message_all(f"Disconnected @{user_name}")
            # check for !attach command
            elif words[1]=='!attach' and words[2]!="" and words[3]!="":
                sock.setblocking(True)
                file_name = words[2]
                users=[]
                terms = []
                # find users in !attach command string (@ prefix)
                # if word starts with @ then its a username, else the word is a term
                for x in range(3, len(words)):
                    if x!="":
                        if words[x].startswith("@"):
                            users.append(words[x])
                        else: terms.append(words[x])
                print(f"writing file {file_name}")
                file = open(f"{file_name}", 'wb')
                chunk = sock.recv(1024)
                while chunk:
                    file.write(chunk)
                    chunk = sock.recv(1024)
                file.close()
                f = open(f"{file_name}", 'rb')
                data = f.read(1024)
                while data:
                    conn = get_socket_by_username(words[3].strip("@"))
                    conn.send(data)
                    data = file.read(1024)
                sock.setblocking(False)

                file.close()
                f.close()
            # check for !follow? command
            elif (words[1]=='!follow?'):
                if following is not None:
                    following_str = ""
                    for follow in following:
                        if follow != "" or follow!= " ":
                            following_str += follow + " "
                    following_str.rstrip(" ")
                    following_str.replace(' ', ',')
                    message(sock, following_str)
            # check for !follow or !unfollow command
            elif ((words[1]=="!follow" or words[1]=="!unfollow")):
                term = words[2]
                # Can't follow or unfollow @all
                if term == "@all":
                    message(sock, f"Can not perform {words[1]} on {term}")
                # if username doesnt exist
                elif term.startswith("@") and get_socket_by_username(term.lstrip("@")) is None:
                    message(sock, "USER DOES NOT EXIST!")
                # Can't perform follow or unfollow on yourself
                elif term == f"@{user_name}":
                    message(sock, f"Can not perform {words[1]} on yourself")
                # if user exists
                else:
                    if words[1]=="!follow":
                        if term in following in following:
                            message(sock, f"You are already following {term}")
                        else:  
                            following.append(term)
                            message(sock, f"You are now following {term}")
                    elif words[1]=="!unfollow":
                        print(following)
                        if term not in following:
                            message(sock, f"You are not following {term}")
                        if term == "@all":
                            message(sock, f"You can not unfollow {term}")
                        else:
                            following.remove(term)
                            message(sock, f"You have unfollowed {term}")
            else:
                message(sock, f"Unknown command: {words[1]}. Type !help.")
        else:
            # extract username
            user = words[0].strip(":")
            # Remove username from msg
            words.remove(words[0])
            # list containing recipient usernames
            broadcast = []
            # list containing terms
            terms = []
            # append the usernames of recipients
            for word in words:
                if word.startswith("@"):
                    broadcast.append(word)
                else:
                    terms.append(word)
            # send the message to each recipient in the broadcast list
            for id in broadcast:
                # get username without @ symbol
                name = id.strip("@")
                print(f"line 156 {name}")
                # get socket corresponding to username
                sock = get_socket_by_username(name)
                # if the list contains @all then send to every recipient
                if(id=="@all"):
                    forward_message(get_socket_by_username(user), msg)
                elif(sock!= None):
                    sock.send(msg.encode())
            
            # send message to every client following that user
            for client in client_list:
                following_list = client[2]
                client_name = "@"+client[0]
                if user in following_list and user!=client_name:
                    sock = client[1]
                    sock.send(msg.encode())
                # send msg to every client following a term in the sentence
                for term in terms:
                    if term in following_list:
                        sock = client[1]
                        sock.send(msg.encode())


# get list of all usernames connected 
def getAll():
    list_res = ""
    for client in client_list:
        if(client[0]!=""):
            list_res += client[0] + ", "
    return list_res.strip(', ')

    

# Accept new inbound client connections
def accept_client(sock, mask):
    # Accept connection
    client_sock, addr = sock.accept()
    # Set client socket to non blocking
    client_sock.setblocking(False)
    
    # Read message from socket and split between spaces
    msg = client_sock.recv(1024).decode()
    msg_split = msg.split(' ')

    user_name = msg_split[1].strip('\n')
    if (user_name=='all'):
        message(client_sock, SERVER_RESPONSES['INVALID_REG'])
        client_sock.close()
        sel.register(client_sock, selectors.EVENT_READ, accept_message)
    # If username is unique
    elif get_socket_by_username(user_name) == None:
        print(f"\nNew client connected from: {addr}")
        
        # Append client object to client_list
        client_list.append((user_name, client_sock, ['@all', f"@{user_name}"]))
        # Send registration message to client and print to server 
        welcome_msg = f"Welcome {user_name}!"
        message_all(welcome_msg)
        message(client_sock, SERVER_RESPONSES['REG_SUCCESS'])
        # Register client socket and wait for read events (inbound messages from client)
        sel.register(client_sock, selectors.EVENT_READ, accept_message)
    else:
        message(client_sock, SERVER_RESPONSES['USER_EXISTS'])
        client_sock.close()
        sel.register(client_sock, selectors.EVENT_READ, accept_message)




# send response to all connected clients
def message_all(msg):
    res = f"[SERVER]: {msg}"
    for client in client_list:
        client[1].send(res.encode())
    print(f"\n{res}")

def message(sock, msg):
    res = f"\n[SERVER]: {msg}"
    sock.send(res.encode())
    print(f"\n{res}")

# forward msg from specified socket to other sockets
def forward_message(sock, msg):
    for client in client_list:
        if client[1]!=sock:
            conn = client[1]
            conn.send(msg.encode())
            print(f"\n{msg}")

# Remove client socket
def remove_sock(sock):
    for client in client_list:
        if client[1] == sock:
            user_name = get_username_by_socket(sock)
            message(sock,SERVER_RESPONSES['SERVER_DC'])
            client_list.remove(client)
                        
#  get following count corresponding to client socket
def get_Following(sock):
    for client in client_list:
        if client[1]==sock:
            list = client[2]
            return list
    return None

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

def check_reg_msg(client_sock):
    # Read message from socket and split between spaces
    msg = client_sock.recv(1024).decode()
    msg_split = msg.split(' ')

    user_name = msg_split[1]

    # If username is unique
    if get_socket_by_username(user_name) == None:
        # Append client object to client_list
        client_list.append((user_name, client_sock))
        # Send registration message to client and print to server 
        welcome_msg = f"Welcome {user_name}!"
        message_all(welcome_msg)
        message(client_sock, SERVER_RESPONSES['REG_SUCCESS'])
        # Register client socket and wait for read events (inbound messages from client)
        sel.register(client_sock, selectors.EVENT_READ, accept_message)
    else:
        message(client_sock, SERVER_RESPONSES['USER_EXISTS'])
        client_sock.close()
        sel.register(client_sock, selectors.EVENT_READ, accept_message)



if __name__ == '__main__':
    main()