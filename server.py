import socket
import threading
import crc

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

# function to broadcast messages to all clients (send message to all clients except the sender)
def broadcast(message, sender_socket):
    packet = crc.create_packet(message) # create CRC packet
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
        c_name = c_socket.recv(1024).decode()
        client_names.append(c_name)
        clients.append(c_socket)
        
        print(f"{c_name} at '{c_address}' has joined the server")
        
        msg = f"Hi {c_name}! Welcome to the server. Type [bye] to exit."
        c_socket.send(crc.create_packet(msg))
        
        broadcast(f"--- {c_name} has joined the chat ---", c_socket)

        while True:
            recv_packet = c_socket.recv(1024).decode()
            
            is_valid, recv_msg = crc.verify_packet(recv_packet)
            
            if not is_valid:
                print(f"CRC Error from {c_name}. Packet dropped.")
                continue
            
            print(f"{c_name} > {recv_msg}")
            
            if recv_msg == "[bye]":
                break
            
            broadcast(f"{c_name} > {recv_msg}", c_socket)
            
    except Exception as e:
        print(f"Error with client {c_address}: {e}")
    
    finally:  # when loop breaks
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
		