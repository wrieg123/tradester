import os
import json
import sqlalchemy
import psycopg2
import mysql.connector as mysql

try:
    import pyodbc
except:
    pass


class connector():
    """
    Serves as point of reference for connection to internal database, currently supports mysql and postgres
    
    ...
    Parameters
    ----------
    cred_name : string, optional
        name of credentials to connect from, if None uses 'default' (see: set_default())
    """
    def __init__(self, cred_name = None):
        if cred_name is None:
            with open(os.path.expanduser('~').replace('\\', '/') + '/default.json') as df:
                cred_name = json.load(df)['default']
        with open(os.path.expanduser('~').replace('\\','/') + '/' + cred_name + '.json', 'r') as f:
            self.credentials = json.load(f)
        self.user = self.credentials['user']
        self.password = self.credentials['password']
        self.host = self.credentials['host']
        self.port = self.credentials['port']
        self.db = self.credentials['database']
        self.s_type = self.credentials['s_type']

    def get_credentials(self):
        return self.credentials

    def cnx(self):
        """
        returns connection relative to type of server type, either a mysql.connector or psycopg2
        """
        if self.credentials['s_type'] == 'postgres':
            return psycopg2.connect(**{x:v for x, v in self.credentials.items() if x != 's_type'})
        elif self.credentials['s_type'] == 'mysql':
            return mysql.connect(**{x:v for x, v in self.credentials.items() if x != 's_type'})
        elif self.credentials['s_type'] == 'mssql+pyodbc':
            return pyodbc.connect(f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.credentials['host']};DATABASE={self.credentials['database']};UID={self.credentials['user']};PWD={self.credentials['password']}")

    def engine(self):
        """
        return sqlalchemy engine object using the connection parameters 
        """
        if self.credentials['s_type'] == 'mssql+pyodbc':
            import urllib
            params = urllib.parse.quote_plus(f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.credentials['host']};DATABASE={self.credentials['database']};UID={self.credentials['user']};PWD={self.credentials['password']}")
            return sqlalchemy.create_engine("mssql+pyodbc:///?odbc_connect=%s" % params)
        else:
            return sqlalchemy.create_engine(f"{self.s_type}://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}")
