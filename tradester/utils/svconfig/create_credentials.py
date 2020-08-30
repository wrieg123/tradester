import os
import json

def create_credentials():
    print("Welcome to the credentail creator. This script helps create different json credentials for server connectivity. While rudementary, it works! For ease of use, the default save location is the user's root directory.")
    run = True

    while run:
        print("Beginning creation of new credential ... ")
        server_type = input("database type (currently accepted: mysql or postgres): ")
        user = input("username: ")
        pwd = input("password: ")
        host = input("ip addr: ")
        port = input("port: ")
        database = input("database: ")
        
        config = {"s_type":server_type, "user":user, "password":pwd, "host":host, "port":port, "database":database}
        
        fname = input("filename: ") + '.json'
        fname = os.path.expanduser('~').replace('\\','/') + '/'  + fname
        with open(fname, 'w') as f:
            json.dump(config, f)
        print("File saved to ", fname)
        print()
    
if __name__ == '__main__':
    create_credentials()
