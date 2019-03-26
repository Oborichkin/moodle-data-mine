
import sys
from queue import Queue
from threading import Thread, Lock
from lxml import html
from bs4 import BeautifulSoup
import requests

payload = {
    "username": "***",
    "password": "***"
}

lock = Lock()
session_requests = requests.session()

login_url = "https://dl2.spbstu.ru/login/index.php"
result = session_requests.post(
    login_url, 
    data = payload, 
    headers = dict(referer=login_url)
)

class Worker(Thread):
    """ Thread executing tasks from a given tasks queue """
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as e:
                # An exception happened in this thread
                print(e)
            finally:
                # Mark this task as done, whether an exception happened or not
                self.tasks.task_done()


class ThreadPool:
    """ Pool of threads consuming tasks from a queue """
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """ Add a task to the queue """
        self.tasks.put((func, args, kargs))

    def map(self, func, args_list):
        """ Add a list of tasks to the queue """
        for args in args_list:
            self.add_task(func, args)

    def wait_completion(self):
        """ Wait for completion of all the tasks in the queue """
        self.tasks.join()


def parse_question(sess, url, f):
    r = sess.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    a = soup.find("span", {"class": "answer"}).find("input")["value"]
    q = soup.find("div", {"class": "qtext"}).find("p").text
    with lock:
        f.write(str(q) + '|' + str(a) + '\n')

if __name__ == "__main__":

    # Instantiate a thread pool with 5 worker threads
    with open('test1.txt', 'r') as f:
        urls = f.readlines()
    
    pool = ThreadPool(10)

    # Add the jobs in bulk to the thread pool. Alternatively you could use
    # `pool.add_task` to add single jobs. The code will block here, which
    # makes it possible to cancel the thread pool with an exception when
    # the currently running batch of workers is finished.
    with open('results.csv', "w") as f:
        for u in urls:
            pool.add_task(parse_question, session_requests, u, f)
        pool.wait_completion()