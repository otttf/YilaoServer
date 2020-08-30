from base import app
from resource import *

register_api_1_0()

if __name__ == '__main__':
    app.run(host='0.0.0.0', use_reloader=False, debug=True)
