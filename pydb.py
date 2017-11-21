#!/usr/bin/env python
"""A simple DB to store and retrieve key value pairs via HTTP
"""

import socket
import argparse
import datetime
from textwrap import dedent

class DBServer:
  """Class for database server objects

  Binds a socket to a passed IP address or locahost string and port,
  and either stores or retrieves key values passed via HTTP

  Args:
    server_address (str): Address to bind the server socket to
    server_port (int): Port to bind the server socket to

  Attributes:
    server_address (str): Address to bind the server socket to
    server_port (int): Port to bind the server socket to
    key_value_db (dict): Dictionary used to store key value pairs
    server_socket (socket): The socket created by the DBServer instance
  """
  address_family = socket.AF_INET
  socket_type = socket.SOCK_STREAM
  request_queue_size = 1
  def __init__(self, server_address, server_port):
    self.server_address = server_address
    self.server_port = server_port
    self.key_value_db = {}

    #Create a socket and try to bind to it
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
    """Infinite loop to listen for client connections and route to request_handler"""
    while True:
      self.server_socket.listen(self.request_queue_size)
      client_connection, client_address = self.server_socket.accept()
      self.request_handler(client_connection)

  def request_handler(self, client_connection):
    """Accepts incoming connections, routes them to the parser and sends
    responses to send_response()

    Args:
      client_connection (socket): Socket used for the client's requests
    """
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
    """Method to parse requests by path, route them to the correct getter or
    setter and return a response and HTTP status code

    Args:
      request (string): The data recieved from the client via the socket_type

    Returns:
      response (string): The text to display in the HTTP response
      http_code (int): The HTTP status code to include in the response
    """
    response=''
    http_code = 200

    request_line = request.splitlines()[0]
    request_method, path, request_version = request_line.split()

    #Try to split path into it's components: the operation requested and the keyvalue
    try:
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

    except ValueError: #Catch any paths that don't match the form we're interested in
        response = dedent("""Incorrect path (%s)
                   Requested URL must take the form http://%s:%s/[operation]?[value]""" % (path, self.server_address, self.server_port))
        http_code = 400
        return response, http_code

    return response, http_code

  def get_value(self, request_key):
    """Getter to retrieve value for a passed key from the DB

    Args:
      request_key (string): The key to get the corresponding value for

    Returns:
      result (string): The text to display in the HTTP response
      http_code (int): The HTTP status code to include in the response
    """

    if request_key in self.key_value_db:
      result = 'The value for <b>%s</b> is <b>%s</b>' % (request_key, self.key_value_db[request_key])
      http_code = 200
    else:
      result = 'The requested key (<b>%s</b>) does not exist' % request_key
      http_code = 404

    return result, http_code

  def set_value(self, request_key, request_value):
    """Setter to set the value for a passed key in the DB

    Args:
      request_key (string): The key to set the value of
      request_value (string): The value to store

    Returns:
      response (string): The text to display in the HTTP response
      http_code (int): The HTTP status code to include in the response
    """

    self.key_value_db[request_key] = request_value
    response = 'Stored the value <b>%s</b> for the key <b>%s</b>' % (request_value, request_key)
    http_code = 200

    return response, http_code

  def gen_headers(self, http_code):
    """Generate HTTP headers from passed HTTP response code

    Args:
      http_code (int): The HTTP status code to include in the response

    Returns:
      http_headers (string): The headers to include in the HTTP response
    """

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
    """Generate HTML body from passed test to display

    Args:
      response (string): The text to display in the HTTP response
      http_code (int): The HTTP status code to include in the response

    Returns:
      html_body (string): The HTML body to include in the HTTP response
    """

    #enclose the response in an html paragraph tag
    response = '<p class="lead">%s</p>' % response

    #If we are returning any sort of error, prepend response with appropriate header
    if http_code > 200:
        response = "<h1>Error: %d</h1>\n%s" % (http_code, response)

    #Generate the rest of the HTML
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
    """Sends a response to the client and closes the socket for this request

    Args:
      client_connection (socket): Socket used for the client's requests
      response (string): The text to display in the HTTP response
      http_code (int): The HTTP status code to include in the response
    """

    #Construct the http response by concat'ing the generated headers and body
    http_response = self.gen_headers(http_code) + self.gen_body(response, http_code)

    client_connection.sendall(http_response)
    client_connection.close()

def make_dbserver(server_address, server_port):
  """Make an instance of DBServer on the passed IP and port

  Args:
    server_address (str): Address to bind the server socket to
    server_port (int): Port to bind the server socket to

  Returns:
    server (DBServer): The instance of DBServer with a socket bound to the passed address and port
  """
  server = DBServer(server_address, server_port)

  return server

def parse_args():
    """Parse arguments passed at the command line

    Returns:
      parser.parse_args() (argparse.Namespace): The parsed set of arguments
    """
    parser = argparse.ArgumentParser(description='Create a database server to save and return key pair values')
    parser.add_argument('--ip', type=str, required=False, default='localhost', help='IP for server to listen on')
    parser.add_argument('--port', type=int, required=False, default=4000, help='Port for server to listen on')

    return parser.parse_args()

if __name__ == '__main__':
  args = parse_args()
  httpd = make_dbserver(args.ip, args.port)
  httpd.serve_requests()
