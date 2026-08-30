import time

def timer_start():
    return time.time()

def timer_end(start):
    return round(time.time() - start, 2)