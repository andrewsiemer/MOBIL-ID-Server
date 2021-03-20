import threading
import time
import requests
import json

def get(index: int):
    r = requests.get('http://98.172.196.167:8000/experiment')
    data = r.json()
    if r.status_code == 200:
        print(str(index) + ': ' + data['client'])
    else:
        print(str(index) + ': ' + 'ERROR')

if __name__ == "__main__":
    num_clients = 100 # CHANGE THIS NUMBER

    threads = list()
    start = time.time()
    for index in range(num_clients):
        x = threading.Thread(target=get, args=(index,))
        threads.append(x)
        x.start()

    for index, thread in enumerate(threads):
        thread.join()

    print(str(num_clients) + " clients completed in " + str(round(((time.time() - start)*1000), 2)) + ' ms')
