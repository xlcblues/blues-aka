import os
from blues_aka import create_app

config_name = os.environ.get('FLASK_CONFIG') or 'Dev'
app = create_app(config_name)

if __name__ == '__main__':
    app.run()

