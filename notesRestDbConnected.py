import json
import socket
import sys
import threading
from queue import Queue

import MySQLdb

from notesRest import Server


class DBManager:

    def __init__(self, host, port, user, password, db_name):
        self.db_connection = None
        self.cursor = None
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db_name = db_name

    def __enter__(self):
        self.cursor = self.db_connection.cursor()
        return self

    def connect(self):
        self.db_connection = MySQLdb.connect(host=self.host,
                                             port=self.port,
                                             user=self.user,
                                             password=self.password,
                                             database=self.db_name,
                                             charset='utf8')

    def make_request(self, request):
        self.cursor.execute(request)
        response = self.cursor.fetchall()
        return response

    def get_last_id(self):
        query = """SELECT LAST_INSERT_ID()"""
        self.cursor.execute(query)
        return self.cursor.fetchall()[0][0]

    def generate_table(self):
        query = """CREATE TABLE notes (id INT AUTO_INCREMENT PRIMARY KEY, 
                                      note VARCHAR(120) NOT NULL, 
                                      description TEXT(1024) NOT NULL, CONSTRAINT id UNIQUE (id))"""
        self.make_request(query)

    def __exit__(self, *args):
        if args[0] is None:
            self.db_connection.commit()
        if self.cursor is not None:
            self.cursor.close()

    def __del__(self):
        if self.db_connection is not None:
            self.db_connection.close()


class ServerDBConnected(Server):
    table_name = None

    def __init__(self, db_params, queue):
        super().__init__(queue)
        self.db_params = db_params
        self.db_manager = DBManager(self.db_params.get('host'),
                                    self.db_params.get('port'),
                                    self.db_params.get('user'),
                                    self.db_params.get('password'),
                                    self.db_params.get('db_name'))
        self.table_name = db_params.get('table_name')

    def connect_to_db(self):
        try:
            self.db_manager.connect()
            with self.db_manager as mgr:
                if self.table_name == '':
                    try:
                        mgr.generate_table()
                    except Exception:
                        pass
                    self.table_name = 'notes'
            return self
        except Exception as e:
            print(e)

    def run(self):
        super().run()

    def post(self, request):
        print("POST request processing")
        query = """INSERT INTO notes(note, description) VALUES('{}', '{}')"""
        data = json.loads(self.get_notes_data(request))
        with self.db_manager as mgr:
            mgr.make_request(query.format(data.get('note'), data.get('description')))
            note_id = mgr.get_last_id()
            self.send_response(201, json.dumps({"id": str(note_id)}))

    def get(self, request):
        print("GET request processing")
        request_dest = request.split()[1]
        with self.db_manager as mgr:
            if request_dest.split('/')[-1:][0] == '':
                query = """SELECT id, note FROM {}""".format(self.table_name)
                response = mgr.make_request(query)
                result = [{"id": str(note[0]),
                           "note": note[1]} for note in response]
            else:
                query = """SELECT id, note, description FROM {} WHERE id = {}""".format(self.table_name,
                                                                                        request_dest.split('/')[-1:][0])
                response = mgr.make_request(query)
                if len(response) == 0:
                    raise KeyError
                result = {"id": str(response[0][0]),
                          "note": response[0][1],
                          "description": response[0][2]}
            self.send_response(200, str(result))

    def delete(self, request):
        print("DELETE request processing")
        note_id = request.split()[1].split('/')[-1:][0]
        query = """DELETE FROM {} WHERE id = {}""".format(self.table_name, int(note_id))
        with self.db_manager as mgr:
            mgr.make_request(query)
            self.send_response(200, '')

    def put(self, request):
        print("PUT request processing")
        note_id = request.split()[1].split('/')[-1:][0]
        data = json.loads(self.get_notes_data(request))
        query = """UPDATE {} SET note = '{}', description = '{}' WHERE id = '{}'""".format(self.table_name,
                                                                                           data.get('note'),
                                                                                           data.get('description'),
                                                                                           int(note_id))
        with self.db_manager as mgr:
            mgr.make_request(query)
            self.send_response(200, '')


db_manager = None
server_port = 5577
worker_queue = Queue()
LOCK = threading.RLock()


def start_server(params):
    global server_port, db_manager
    threads_count = 5
    sock = socket.socket()
    try:
        sock.bind(('', server_port))
        for _ in range(threads_count):
            ServerDBConnected(params, worker_queue).connect_to_db().start()
        sock.listen(5)
        print('Server started')
        while True:
            worker_queue.put(sock.accept())
    except KeyboardInterrupt:
        print("Server stopped")
        for _ in range(threads_count):
            worker_queue.put(None)
        exit(0)
    except Exception as e:
        print("Can't start server", e)


host, port = input("MySql DB required!\nhost:port: ").split(':')
user = input("mysql_user: ")
password = input("{}'s password: ".format(user))
db_name = input('db name: ')
table_name = input("table name(nothing if not exists): ")
db_params_out = {'host': host,
                 'port': int(port),
                 'user': user,
                 'password': password,
                 'db_name': db_name,
                 'table_name': table_name
                 }
if __name__ == '__main__':
    if len(sys.argv) == 3:
        server_port = sys.argv[2]
    start_server(db_params_out)
