import etl
import os
import json


def set_default():
    print("To create a default insert the name of an existing credential")
    default = input("-> ")
    config = {'default':default}

    fname = os.path.expanduser('~').replace('\\','/') + '/default.json'
    with open(fname, 'w') as f:
        json.dump(config, f)
    print("Saved default file: ", fname)
