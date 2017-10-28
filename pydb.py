#!/usr/bin/python
import socket
import sys

class DBServer:
  """Class for database server objects
  :param server_address: Address to bind the server socket to
  :param server_port: Port to bind the server socket to
  """
  #define socket options
  address_family = socket.AF_INET
  socket_type = socket.SOCK_STREAM
  request_queue_size = 1
  def __init__(self, server_address, server_port):
    #set instance vars
    self.server_address = server_address
    self.server_port = server_port
    #create dict to store key value pairs for this DB
    self.key_value_db = {}

    #Create socket
    self.server_socket = socket.socket(self.address_family, self.socket_type)

    #set socket options to allow resue
    self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    #bind socket
    self.server_socket.bind((server_address, server_port))
    #listen on socket
    self.server_socket.listen(self.request_queue_size)

    print 'Serving HTTP on port %s ...' % server_port
  
  def serve_requests(self):
    server_socket = self.server_socket
    
    #loop to listen for client connections and direct them to the handler
    while True:
      #create the client connection 
      client_connection, client_address = server_socket.accept()
      #call the request handler for the request and then close it and loop back and wait for another
      self.request_handler(client_connection)

  def request_handler(self, client_connection):
    request = client_connection.recv(1024)

    #print the request
    #print self.request

    response = self.parse_request(request)

    self.send_response(client_connection, response)

  def parse_request(self, request):
    response = 'Hello World'
    #we only care about the first line of the request
    request_line = request.splitlines()[0]

    #split the request into it's components
    request_method, path, request_version = request_line.split()

    #split path into it's components
    request_op, request_keyvalue = path.split('?')
    request_op = request_op[1:]
    
    #handle request appropriately depending on operation requested
    if request_op == 'get':
      request_value, request_key = request_keyvalue.split('=')
      response = self.get_value(request_key)
    elif request_op == 'set':
      request_key, request_value = request_keyvalue.split('=')
      response = self.set_value(request_key, request_value)
    else:
      print('Error: unknown operation in URL. Must be either GET or SET.')
 
    #print('Request path is %s so op is %s and key is %s' % (path, request_op, request_key))
    return response

  def get_value(self, request_key):
    if request_key in self.key_value_db:
      result = self.key_value_db[request_key]
      print('Value for key %s is %s' % (request_key, self.key_value_db[request_key]))
    else:
      result = 'Error: Key ' + request_key + ' has not been set'
      print('Key %s has not been set' % request_key)

    return result

  def set_value(self, request_key, request_value):
    self.key_value_db[request_key] = request_value
    print('Setting value of %s to %s' % (request_key, request_value))
    response = 'Key ' + request_key + ' has been set to ' + request_value
    return response
  
  def send_response(self, client_connection, response):
    http_response = "HTTP/1.1 200 OK\n\n" + response
    client_connection.sendall(http_response)
    client_connection.close()


#def funtion to make the server, takes address and port to listen on as param
def make_dbserver(server_address, server_port):
  server = DBServer(server_address, server_port)
  return server

#define _main_
if __name__ == '__main__':
  if len(sys.argv) < 3:
    sys.exit('Must provide an address and port to listen on')
  server_address = sys.argv[1]
  server_port = int(sys.argv[2])
  httpd = make_dbserver(server_address, server_port)
  httpd.serve_requests()
