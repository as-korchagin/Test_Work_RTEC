import json
import sys

import MySQLdb

from notesRest import Server


class DBManager:

    def __init__(self):
        self.db_connection = None
        self.cursor = None

    def __enter__(self):
        if self.db_connection is not None:
            self.cursor = self.db_connection.cursor()
        return self

    def connect(self, host, port, user, password, db_name):
        self.db_connection = MySQLdb.connect(host=host, port=port, user=user, password=password,
                                             database=db_name, charset='utf8')
        if self.cursor is None:
            self.cursor = self.db_connection.cursor()

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

    def __init__(self, port):
        super().__init__(port)
        self.db_manager = DBManager()

    def connect_to_db(self, host, port, user, password, db_name):
        with self.db_manager as mgr:
            mgr.connect(host, port, user, password, db_name)
            print("table name(nothing if not exists): ", end='')
            self.table_name = input()
            if self.table_name == '':
                mgr.generate_table()
                self.table_name = 'notes'
                print("Table 'notes' has been created")
            self.start_server()

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

    def stop_server(self):
        del self.db_manager
        super().stop_server()


print("MySql DB required!", "host:port: ", sep='\n', end='')
host, port = input().split(':')
print("mysql_user: ", end='')
user = input()
print("{}'s password: ".format(user), end='')
password = input()
print('db name: ', end='')
db_name = input()
if __name__ == '__main__':
    ServerDBConnected(sys.argv[2] if len(sys.argv) == 3 else 5577).connect_to_db(host,
                                                                                 int(port),
                                                                                 user,
                                                                                 password,
                                                                                 db_name)
