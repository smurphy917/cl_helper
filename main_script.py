import sys
import main
from threading import Thread

def run_main(args=None):
    sys.argv = ['','runserver']
    t = Thread(target=main.manager.run)
    t.daemon = True
    t.start()
    m = main.Main()
    m.open_page()

if __name__ == '__main__':
    run_main()