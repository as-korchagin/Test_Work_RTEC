import json
import re
import socket
import sys
import threading
import time
from queue import Queue


class Server(threading.Thread):

    def __init__(self, queue):
        super().__init__()
        self.methods = {"GET": self.get,
                        "POST": self.post,
                        "PUT": self.put,
                        "DELETE": self.delete}

        self.notes = globals().get('notes')
        self.id_counter = globals().get('id_counter')
        self.id_counter = id_counter
        self.queue = queue
        self.conn = None
        self.addr = None

    def run(self):
        global LOCK
        while True:
            try:
                LOCK.acquire()
                item = self.queue.get()
                LOCK.release()
                if item is None:
                    self.queue.task_done()
                    return
                else:
                    self.conn, self.addr = item
                request = self.conn.recv(4096).decode('utf-8')
                request_method = request.split()[0]
                self.methods.get(request_method)(request)
            except KeyError:
                self.send_response(404, '')
                print('Element not found')
            except Exception as e:
                self.send_response(500, '')
                print("Something went wrong", e)

    def get(self, request):
        request_dest = request.split()[1]
        response = ''
        print("GET request processing")
        if request_dest.split('/')[-1:][0] == '':
            response += str(list(map(lambda x: {"id": str(x[0]), "note": x[1].get('note')}, self.notes.items())))
        else:
            try:
                item = \
                    filter(lambda x: x[0] == int(request_dest.split('/')[-1:][0]), self.notes.items()).__next__()[1]
            except StopIteration:
                raise KeyError
            item["id"] = request_dest.split('/')[-1:][0]
            response = str(item)
        self.send_response(200, response)

    def post(self, request):
        data = self.get_notes_data(request)
        self.notes[self.id_counter[0]] = json.loads(data)
        self.send_response(201, '{{"id":"{}"}}'.format(self.id_counter[0]))
        print("Note with id = {} has been added".format(self.id_counter[0]))
        self.id_counter[0] += 1

    def delete(self, request):
        note_id = request.split()[1].split('/')[-1:]
        del self.notes[int(note_id[0])]
        print("Note with id = {} has been deleted".format(note_id[0]))
        self.send_response(200, '')

    def put(self, request):
        note_id = request.split()[1].split('/')[-1:]
        data = self.get_notes_data(request)
        if self.notes.get(int(note_id[0])) is None:
            raise KeyError
        else:
            self.notes[int(note_id[0])] = json.loads(data)
            self.send_response(200, '')
            print("Note with id = {} as been updated".format(note_id))

    def get_notes_data(self, request):
        length_pattern = r'Content-Length: ([\d]+)'
        data_pattern = r'{[\w\s\t\"\:\,]+}'
        if len(re.findall(data_pattern, request)) != 0:
            data = re.findall(data_pattern, request)
            data = re.sub(r'\n', '', data[0])
        else:
            content_length = re.findall(length_pattern, request)[0]
            data = self.conn.recv(int(content_length) * 8).decode('utf-8')
        return data

    def send_response(self, code, response):
        self.conn.send((self.header_gen(code) + re.sub("\s", '', re.sub(r'\'', '"', response))).encode())
        self.conn.close()
        self.queue.task_done()

    @staticmethod
    def header_gen(status):
        header = ''
        if status == 200:
            header += 'HTTP/1.1 200 OK\n'
        elif status == 201:
            header += 'HTTP/1.1 201 Created\n'
        elif status == 404:
            header += 'HTTP/1.1 404 Not Found\n'
        elif status == 500:
            header += 'HTTP/1.1 500 Internal Server Error\n'
        current_time = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        header += "Date: {}\n".format(current_time)
        header += "Server: notesRest\n"
        header += "Connection: close\n\n"
        return header


worker_queue = Queue()
notes = dict()
id_counter = [1]
LOCK = threading.RLock()
threads_count = 5


def start_server(port):
    sock = socket.socket()
    try:
        sock.bind(('', port))
        sock.listen(5)
        print('Server started')
        for _ in range(threads_count):
            Server(worker_queue).start()
        while True:
            worker_queue.put(sock.accept())
    except KeyboardInterrupt:
        print("Server stopped")
        for _ in range(threads_count):
            worker_queue.put(None)
        exit(0)
    except Exception as e:
        print("Can't start server", e)


if __name__ == '__main__':
    start_server(int(sys.argv[2]) if len(sys.argv) == 3 else 5577)
