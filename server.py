import socket
import threading
import zlib

#Set Socket
server = socket.socket()
host_name = socket.gethostname()		#device name
ip = socket.gethostbyname(host_name)		#IP address of device
port = 1234					#Port to listen at for connection
server.bind((ip, port))
print(f"Server has started on address: {ip} and port: {port}") 

# list to store clients and their names
clients = []
client_names=[]

# function to create and send a crc-checked packet
def create_packet(message):
	message_bytes = message.encode()
	checksum = zlib.crc32(message_bytes)
	return f"{message}|{checksum}".encode()

# function to broadcast messages to all clients (send message to all clients except the sender)
def broadcast(message, sender_socket):
    packet = create_packet(message) # create CRC packet
    for client in clients:
        if client != sender_socket:
            try:
                client.send(packet)
            except socket.error:
                # remove disconnected client
                remove_client(client)

# function to remove client
def remove_client(client_socket):
	if client_socket in clients:
		index = clients.index(client_socket)
		clients.remove(client_socket)
		name = client_names.pop(index)
		print(f"{name} has disconnected.")
		broadcast(f"--- {name} has left the chat ---", client_socket)
		client_socket.close()  

def handle_client(c_socket, c_address):
    try:
        # first message is to get the client name
        c_name = c_socket.recv(1024).decode()
        client_names.append(c_name)
        clients.append(c_socket)
        
        print(f"{c_name} at '{c_address}' has joined the server")
        
        msg = f"Hi {c_name}! Welcome to the server. Type [bye] to exit."
        c_socket.send(create_packet(msg)) # to be sent with crc implemented
        
        # broadcast that a new user joined
        broadcast(f"--- {c_name} has joined the chat ---", c_socket)

        # communication Loop 
        while True:
            # receive message
            recv_packet = c_socket.recv(1024).decode() # packet received
            
            # CRC check
            try:
                recv_msg, received_crc = recv_packet.split('|')
                message_bytes = recv_msg.encode()
                local_crc = zlib.crc32(message_bytes)

                if str(local_crc) != received_crc:
                    print(f"CRC Mismatch from {c_name}. Packet dropped.")
                    # send an error back
					#c_socket.send(create_packet("Server > Error: Corrupted message received."))
                    continue # skip message
            
            except (ValueError, IndexError):
                print(f"Received malformed packet from {c_name}. Packet dropped.")
                continue # skip message
            

            print(f"{c_name} > {recv_msg}")
            
            if recv_msg == "[bye]":
                break # jump to finally block
            
            # boadcast the valid message
            broadcast(f"{c_name} > {recv_msg}", c_socket)
            
    except Exception as e:
        print(f"Error with client {c_address}: {e}")
    
    finally:
        # when loop breaks (or error), remove client
        remove_client(c_socket)
		
		
def start_server():
    server.listen()
    print("Waiting for clients... ")
    
    while True:
        # accept new client
        (c_socket, c_address) = server.accept()
        
        # start a new thread to handle this client
        thread = threading.Thread(target=handle_client, args=(c_socket, c_address))
        thread.start()

if __name__ == "__main__":
    start_server()
		