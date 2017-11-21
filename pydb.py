#!/usr/bin/python
import socket
import argparse
import datetime
from textwrap import dedent

class DBServer:
  """Class for database server objects
  :param server_address: Address to bind the server socket to
  :param server_port: Port to bind the server socket to
  """
  address_family = socket.AF_INET
  socket_type = socket.SOCK_STREAM
  request_queue_size = 1
  def __init__(self, server_address, server_port):
    self.server_address = server_address
    self.server_port = server_port
    self.key_value_db = {}

    #Create socket, bind it and listen
    self.server_socket = socket.socket(self.address_family, self.socket_type)
    self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        self.server_socket.bind((server_address, server_port))
    except:
        print 'Error: Couldn\'t bind to port %s on %s.  Please make sure it\'s not already in use.' % (server_port, server_address)
        import sys
        sys.exit(1)

    print 'Serving HTTP on %s:%s' % (server_address, server_port)

  def serve_requests(self):
    """Main loop to listen for client connections and route to request_handler"""
    while True:
      self.server_socket.listen(self.request_queue_size)
      client_connection, client_address = self.server_socket.accept()
      self.request_handler(client_connection)

  def request_handler(self, client_connection):
    """Accepts incoming connections, routes them to the parser and triggers a response"""
    request = client_connection.recv(1024)

    #Make sure we recieved some data before proceeding
    if not request:
        response = 'Empty request'
        http_code = 400
    else:
        response, http_code = self.parse_request(request)

    #print response
    self.send_response(client_connection, response, http_code)

  def parse_request(self, request):
    """Method to parse requests by path"""
    response=''
    http_code = 200

    request_line = request.splitlines()[0]
    request_method, path, request_version = request_line.split()

    try:
        #split path into it's components: the operation requested and the keyvalue
        request_op, request_keyvalue = path.split('?')
        request_op = request_op[1:]

        #If request is a get we split in a different order than if it's a set
        if request_op == 'get':
          request_value, request_key = request_keyvalue.split('=')
          response, http_code = self.get_value(request_key)
        elif request_op == 'set':
          request_key, request_value = request_keyvalue.split('=')
          response, http_code = self.set_value(request_key, request_value)
        else:
          response = 'Unknown operation in URL. Must be either GET or SET.'
          http_code = 400
    except ValueError:
        #Catch any paths requested that don't contain a '?' or an '='
        response = dedent("""Incorrect path (%s)
                   Requested URL must take the form http://%s:%s/[operation]?[value]""" % (path, self.server_address, self.server_port))
        http_code = 400
        return response, http_code

    return response, http_code

  def get_value(self, request_key):
    """Getter to retrieve value for a passed key from the DB"""
    if request_key in self.key_value_db:
      result = 'The value for <b>%s</b> is <b>%s</b>' % (request_key, self.key_value_db[request_key])
      http_code = 200
      #print('Value for key %s is %s' % (request_key, self.key_value_db[request_key]))
    else:
      result = 'The requested key (<b>%s</b>) does not exist' % request_key
      http_code = 404
      #print('Key %s has not been set' % request_key)

    return result, http_code

  def set_value(self, request_key, request_value):
    """Setter to set the value for a passed key"""
    self.key_value_db[request_key] = request_value
    #print('Setting value of %s to %s' % (request_key, request_value))
    response = 'Stored the value <b>%s</b> for the key <b>%s</b>' % (request_key, request_value)
    http_code = 200
    return response, http_code

  def gen_headers(self, http_code):
    """Generate HTTP headers from passed http code"""
    if http_code == 200:
      http_headers = "HTTP/1.1 200 OK\n"
    elif http_code == 400:
      http_headers = "HTTP/1.1 400 Bad Request\n"
    elif http_code == 404:
      http_headers = "HTTP/1.1 404 Not Found\n"

    utc_datetime = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S")
    http_headers += dedent("""\
                    Date: %s GMT
                    Content-type: text/html; charset=UTF-8
                    Server: pydb.py
                    Connection: close\n\n""" % utc_datetime)
    return http_headers

  def gen_body(self, response, http_code):
    """Generate HTML body from passed content"""
    #enclose the response in an html paragraph tag
    response = '<p class="lead">%s</p>' % response
    #If we are returning any sort of error, prepend response with appropriate header
    if http_code > 200:
        response = "<h1>Error: %d</h1>\n%s" % (http_code, response)

    html_body = dedent("""\
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>PyDB</title>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css">
      </head>
      <body>
      <header class="bg-primary text-white">
        <div class="container text-center">
          <h1>PyDB</h1>
          <p class="lead">A simple key value pair DB written in Python.</p>
        </div>
      </header>
      <div class="col-lg-8 mx-auto">
        %s
      </div>
      </body>
    </html>""" % response)
    #print html_body
    return html_body

  def send_response(self, client_connection, response, http_code):
    """Method to send a response to the client and close the connection"""
    http_response = self.gen_headers(http_code) + self.gen_body(response, http_code)
    #http_response = "HTTP/1.1 200 OK\n\n" + self.gen_body(response)
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
