#!/usr/bin/python
import socket
import argparse

class DBServer:
  """Class for database server objects
  :param server_address: Address to bind the server socket to
  :param server_port: Port to bind the server socket to
  """
  address_family = socket.AF_INET
  socket_type = socket.SOCK_STREAM
  request_queue_size = 1
  def __init__(self, server_address, server_port):
    #set instance vars
    self.server_address = server_address
    self.server_port = server_port
    self.key_value_db = {}

    #Create socket, bind it and listen
    self.server_socket = socket.socket(self.address_family, self.socket_type)
    self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.server_socket.bind((server_address, server_port))

    print 'Serving HTTP on port %s ...' % server_port

  def serve_requests(self):
    """Main loop to listen for client connections and route to request_handler"""
    while True:
      #print('Listening for new requests')
      self.server_socket.listen(self.request_queue_size)
      #create the client connection
      client_connection, client_address = self.server_socket.accept()
      #call the request handler for the request and then close it and loop back and wait for another
      self.request_handler(client_connection)

  def request_handler(self, client_connection):
    """Accepts incoming connections, routes them to the parser and triggers a response"""
    request = client_connection.recv(1024)

    #Make sure we recieved some data before proceeding
    if not request:
        response = 'Error: detected empty request'
    else:
        response = self.parse_request(request)

    print response
    self.send_response(client_connection, response)

  def parse_request(self, request):
    """Method to parse requests by path"""
    response=''
    try:
        request_line = request.splitlines()[0]
        request_method, path, request_version = request_line.split()
    except IndexError:
        response = 'Error: Empty request'
        return response

    try:
        #split path into it's components: the operation requested and the keyvalue
        request_op, request_keyvalue = path.split('?')
        request_op = request_op[1:]

        #If request is a get we split in a different order than if it's a set
        if request_op == 'get':
          request_value, request_key = request_keyvalue.split('=')
          response = self.get_value(request_key)
        elif request_op == 'set':
          request_key, request_value = request_keyvalue.split('=')
          response = self.set_value(request_key, request_value)
        else:
          #print('Error: unknown operation in URL. Must be either GET or SET.')
          response = 'Error: unknown operation in URL. Must be either GET or SET.'
    except ValueError:
        #Catch any paths requested that don't contain a '?' or an '='
        response = """Error: Incorrect path (%s)
        Requested URL must take the form http://%s:%s/[operation]?[value]""" % (path, self.server_address, self.server_port)
        return response

    return response

  def get_value(self, request_key):
    """Getter to retrieve value for a passed key from the DB"""
    if request_key in self.key_value_db:
      result = self.key_value_db[request_key]
      #print('Value for key %s is %s' % (request_key, self.key_value_db[request_key]))
    else:
      result = 'Error: Key ' + request_key + ' has not been set'
      #print('Key %s has not been set' % request_key)

    return result

  def set_value(self, request_key, request_value):
    """Setter to set the value for a passed key"""
    self.key_value_db[request_key] = request_value
    #print('Setting value of %s to %s' % (request_key, request_value))
    response = 'Key ' + request_key + ' has been set to ' + request_value
    return response

  def send_response(self, client_connection, response):
    """Method to send a response to the client and close the connection"""
    http_response = "HTTP/1.1 200 OK\n\n" + response
    client_connection.sendall(http_response)
    client_connection.close()

def make_dbserver(server_address, server_port):
  """Make an instance of DBServer on the passed IP and port"""
  server = DBServer(server_address, server_port)
  return server

def parse_args():
    """Parse some arguments"""
    parser = argparse.ArgumentParser(description='Create a database server to save and return key pair values')
    parser.add_argument('--ip', type=str, required=False, default='localhost', help='IP for server to listen on')
    parser.add_argument('--port', type=int, required=False, default=4000, help='Port for server to listen on')
    return parser.parse_args()

#define _main_
if __name__ == '__main__':
  args = parse_args()
  httpd = make_dbserver(args.ip, args.port)
  httpd.serve_requests()
