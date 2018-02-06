import datetime
import json
import random

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


def generate_post_request():
    global data
    try:
        response = json.loads(requests.post(HOST, data.encode('utf-8')).text)
        available_ids.add(int(response.get('id')))
        return True
    except json.JSONDecodeError:
        global errors
        errors += 1
        return False


def generate_delete_request():
    try:
        id = random.sample(available_ids, len(available_ids))[0]
        available_ids.remove(id)
        requests.delete(HOST + str(id))
    except Exception:
        return False
    return True


data = """{
    "note":"ыдловплыотавплдоывпалдоывталдоптывлдоатплдывоатплоывтаплоывалпотвыадлоптывщопывпафывпкаываплотиловапывапыва",
     "description":"ыдловплыотавплдоывпалдоывталдоптывлдоатплдывоатплоывтаплоывалпотвыадлоптывщопывпафывпкаываплотилова\
                    пывапывапвыапвыапывапыдловплыотавплдоывпалдоывталдоптывлдоатплдывоатплоывтаплоывалпотвыадлоптывщопы\
                    впафывпкаываплотиловапывапывапвыапвыапывапыдловплыотавплдоывпалдоывталдоптывлдоатплдывоатплоывтапло\
                    ывалпотвыадлоптывщопывпафывпкаываплотиловапывапывапвыапвыапывапыдловплыотавплдоывпалдоывталдоптывлд\
                    апывапыдловплыотавплдоывпалдоывтал"} """

errors = 0
print('port: ', end='')
HOST = 'http://localhost:{}/notes/'.format(input())
available_ids = set()
print("Number of checks: ", end='')
checks_counter = int(input())
print("Add/Delete: ", end='')
add, delete = map(lambda x: int(x), input().split('/'))
add = (checks_counter * add) // (add + delete)
delete = checks_counter - add
operations = list(generate_post_request for _ in range(add))
operations.extend(list(generate_delete_request for _ in range(delete)))
timer = Timer()
operations_counter = 0
with timer:
    for operation in random.sample(operations, len(operations)):
        if operation():
            operations_counter += 1
print('Mean: {} seconds\nOperations completed: {}\nErrors: {}\nBytes sent: {}'.format(
    timer.get_time() / operations_counter,
    operations_counter,
    errors,
    data.__sizeof__() * operations_counter))
