import sys
import main
from threading import Thread

sys.argv = ['','runserver']
t = Thread(target=main.manager.run)
t.daemon = True
t.start()
m = main.Main()
m.open_page()