import os
from threading import Semaphore

# Shared global data for the application

jobs = {}

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
downloadDIR = os.path.join(BASE_DIR, "downloads")
chromeDriverPath = r""#change this to your chromedriver path
semaphore = Semaphore(5)#max number of threads

