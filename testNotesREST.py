import datetime
import json
import queue
import random
import threading

import requests


class Timer:
    time_in = 0
    time_out = 0

    def __enter__(self):
        self.time_in = datetime.datetime.now()
        return self

    def __exit__(self, *args):
        self.time_out = (datetime.datetime.now() - self.time_in).total_seconds()

    def get_time(self):
        return self.time_out


class Client(threading.Thread):

    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            item = main_queue.get()
            if item is not None:
                main_queue.task_done()
                item()
            else:
                return

    @staticmethod
    def generate_post_request():
        global data
        try:
            response = json.loads(requests.post(HOST, data.format(random.randint(0, 20)).encode('utf-8')).text)
            available_ids.add(int(response.get('id')))
            return True
        except json.JSONDecodeError:
            global errors
            errors += 1
            return False

    @staticmethod
    def generate_delete_request():
        try:
            id = random.sample(available_ids, len(available_ids))[0]
            available_ids.remove(id)
            requests.delete(HOST + str(id))
        except Exception:
            global valid_operations
            valid_operations -= 1
            return False
        return True


data = """{{
    "note":"{}kkkkыдловплыотавплдоывпалдоывталдоптывлдоатплдывоатплоывтаплоывалпотвыадлоптывщопывпафывпкаываплотиловапыва",
    "description":"ыдловплыотавплдоывпалдоывталдоптывлдоатплдывоатплоывтаплоывалпотjвыадлоптывщопывпафывпкаываплотилова\
                    пывапывапвыапвыапывапыдловплыотавплдоывпалдоывталдоптывлдоатплдывоатплоывтаплоывалпотвыадлоптывщопы\
                    впафывпкаываплотиловапывапывапвыапвыапывапыдловплыотавплдоывпалдоывталдоптывлдоатплдывоатплоывтапло\
                    ывалпотвыадлоптывщопывпафывпкаываплотиловапывапывапвыапвыапывапыдловплыотавплдоывпалдоывталдоптывлд\
                    апывапыдловплыотавплдоывпалоывтал"}} """

errors = 0
HOST = 'http://localhost:{}/notes/'.format(input('port: '))
available_ids = set()
checks_counter = int(input("Number of checks: "))
add, delete = map(lambda x: int(x), input("Add/Delete: ").split('/'))
add = (checks_counter * add) // (add + delete)
delete = checks_counter - add
operations = list(Client.generate_post_request for _ in range(add))
operations.extend(list(Client.generate_delete_request for _ in range(delete)))
valid_operations = checks_counter
timer = Timer()
main_queue = queue.Queue()
threads_count = 3
for i in random.sample(operations, len(operations)):
    main_queue.put(i)
with timer:
    for _ in range(threads_count):
        Client().start()
    main_queue.join()
print('Mean: {} seconds\nOperations completed: {}\nErrors: {}\nBytes sent: {}'.format(
    timer.get_time() / valid_operations,
    valid_operations,
    errors,
    data.__sizeof__() * valid_operations))
for _ in range(threads_count):
    main_queue.put(None)
