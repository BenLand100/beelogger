import socket
import machine
import json

class Request:
    
    def __init__(self, server, conn, target, headers, body):
        self.server = server
        self.conn = conn
        self.target = target
        self.headers = headers
        self.body = body
        
    def reply(self, **kwargs):
        self.server._reply(self.conn, **kwargs)
        
    def error(self, msg, code=400):
        self.server._error(self.conn, msg, code=code)

class JSONServer:

    def __init__(self, addr='', port=80, backlog=5):
        self.addr = addr
        self.port = port
        self.backlog = backlog
        self._endpoints = {}
        self.add_endpoint('GET','/hello',lambda req: req.reply(msg='greetings'))
        self.add_endpoint('POST','/hello',lambda req: req.reply(msg='post-greetings'))
        
    def add_endpoint(self, verb, endpoint, handler):
        verb = verb.upper()
        if verb not in self._endpoints:
            self._endpoints[verb] = {}
        if handler is None and handler in self._endpoints[verb]:
            del self._endpoints[verb][endpoint]
        else:
            self._endpoints[verb][endpoint] = handler
        
    def _reply(self, conn, code=200, status='OK', **payload):
        payload['status'] = status
        data = f'{json.dumps(payload)}\n'
        conn.send(f'HTTP/1.1 {code} {status}\r\n')
        conn.send('Server: BeeLogger-ESP32\r\n')
        conn.send('Content-Type: text/json\r\n')
        conn.send(f'Content-Length: {len(data)}\r\n')
        conn.send('Connection: close\r\n\r\n')
        conn.sendall(data)
        conn.close()
        
    def _error(self, conn, msg, code=400):
        print(msg)
        try:
            self._reply(conn, code=400, status='BAD', msg=msg)
        except:
            pass

    def serve(self):
    
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.addr, self.port))
        s.listen(self.backlog)
        
        while True:
            try:
                conn, addr = s.accept()
                print(f'Serving {addr}')
                
                request = conn.readline()
                print('>>',request)
                request = request.decode('utf-8')
                parts = request[:-2].split(' ')
                if len(parts) != 3:
                    print('Malformed HTTP/1.1 request')
                    continue
                    
                verb,target,version = parts
                if version != 'HTTP/1.1':
                    print(f'Unknown protocol version {version}')
                    continue
                    
                headers = {}
                while (header:=conn.readline()) != b'\r\n':
                    print('>>',header)
                    header,payload = header.decode('utf-8').split(':')
                    headers[header] = payload.strip()
                    
                if 'Content-Length' in headers:
                    total_size = int(headers['Content-Length'])
                    body = b''
                    while len(data) < total_size:
                        body += conn.read(total_size-len(data))
                else:
                    body = None
                print('>>',body)
                    
                verb = verb.upper()
                if verb in self._endpoints:
                    verb_handlers = self._endpoints[verb]
                    if target in verb_handlers:
                        verb_handlers[target](Request(self, conn, target, headers, body))
                        continue
                    
                self._reply(conn, code='404', status='NOTFOUND', verb=verb, target=target, **headers)
            except Exception as e:
                print('Internal Error')
                print(e)
