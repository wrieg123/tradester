import tradester.utils.svconfig as sv
import pandas as pd
import tempfile
import warnings
import subprocess
from datetime import datetime 
import os
from time import sleep

__all__ = ['MetaFeed', 'TSFeed', 'CustomFeed']

class Feed():
    """
    The base class for all  bar : String
        type of string to pulldatatable connection feeds (static).

    ...
    
    Parameters
    ----------
    identifiers : list
        list of identifiers to define Foreign Key within the query
    fields : String 
        list of fields to pull from "select" statement
    datatable : String
        datatable to get data from
    identity_field : String
        field to identify Foreign Key (self.identifiers list)
    credentials : dictionary
        credentials to pass into connector
    optional_id : boolean, optional (default : False)
        ignore identifiers input, pass in empty list from constructor
    
    Attributes
    ----------
    data : pd.DataFrame
        pandas dataframe of output from query
    identifiers_type : [str, list]
        type of identifiers passed in to constructor
    try_tmp_query : boolean
        if len(identifers) > 5, use fast select method from datatable query

    Methods
    -------
    __validate(identifiers : list)
        ensure that identifiers past in is valid entry type, allow try_tmp_query and set type
    __tmp_query(query : String)
        returns pd.DataFrame using a copy into local memory table to create dataframe, works best for large
        amount of data pulled
    __pd_query(query : String)
        returns pd.read_sql_query(query, ...)
    _query(query : String)
        handles potential errors with tmp_query, if error tries pd_query, if another error kills thread

    See Also
    --------
    tradester.utils.svconfig.connector
    """

    def __init__(self, identifiers, fields, datatable, identity_field, credentials, optional_id = False):
        self.optional_id = optional_id
        self.identifiers, self.identifiers_type, self.try_tmp_query = self.__validate(identifiers)
        self.fields = fields
        self.datatable = datatable
        self.identity_field = identity_field
        self.credentials = credentials
        self.connector = sv.connector(credentials)
        self.complete_fields = fields
        self._data = None

    def __validate(self, identifiers):
        if not self.optional_id:
            if type(identifiers) not in [str, list] or len(identifiers) < 1:
                raise ValueError(f'The input for ``identifiers`` (type: {type(identifiers)}) is not valid!')
            else:
                try_tmp = len(identifiers) > 5 if type(identifiers) is list else False
                return identifiers, type(identifiers), try_tmp
        else:
            try_tmp = False
            return identifiers, type(identifiers), try_tmp


    @property
    def data(self):
        if self._data is not None:
            return self._data
        else:
            raise NotImplementedError("You did not set ``_data``")
    


    def __tmp_query(self, query):
        if self.connector.credentials['s_type'] != 'mssql+pyodbc':
            query = query.replace(';','')
            with tempfile.TemporaryFile() as tmpfile:
                copy_sql = "copy ({}) to stdout with csv {}".format(query, "HEADER")
                cnx = self.connector.engine().raw_connection()
                cur = cnx.cursor()
                if self.connector.s_type == 'postgres':
                    cur.copy_expert(copy_sql, file=tmpfile)
                else:
                    cur.copy_export(copy_sql, tmpfile)
                tmpfile.seek(0)
                cnx.close()
                cur.close()
                return pd.read_csv(tmpfile)
        else:
            query = query.replace(';','')
            path = f'c:/users/will/appdata/local/temp/{str(datetime.now().timestamp()).replace(".","-")}.csv'
            command = 'BCP "{}" queryout "{}" -t "," -U "{}" -P "{}" -S "{}" -d production -r \\n -c'.format(
                    query,
                    path,
                    self.connector.credentials['user'],
                    self.connector.credentials['password'],
                    self.connector.credentials['host'],
                    )
            subprocess.call(command, shell = True)
            fields = getattr(self,'complete_fields')
            if fields != '*':
                fields = fields.replace(' ', '').split(',')
            df = pd.read_csv(path, names = fields)
            os.remove(path)
            return df


            

    def __pd_query(self, query):
        cnx = self.connector.cnx()
        return pd.read_sql_query(query, self.connector.cnx()) 


    def _query(self, query):
        if self.try_tmp_query:
            return self.__tmp_query(query)
            try:
                return self.__tmp_query(query)
            except:
                warnings.warn("Unable to use __tmp_query, alternating to pandas.read_sql_query()", RuntimeWarning)
                return self.__pd_query(query)
        else:
            return self.__pd_query(query)



class MetaFeed(Feed):
    """
    The base class for feeds returning all meta information feeds

    ...
    
    Parameters
    ----------
    identifiers : list
        list of identifiers to define Foreign Key within the query
    fields : String 
        list of fields to pull from "select" statement
    datatable : String
        datatable to get data from
    identity_field : String
        field to identify Foreign Key (self.identifiers list)
    credentials : dictionary
        credentials to pass into connector
    query : String, optional (default: None)
        override query parameter
    optional_id : boolean, optional (default : False)
        ignore identifiers input, pass in empty list from constructor
    
    Methods
    -------
    __gather_data(query : String, None)
        returns dictionary where key is self.identity_field, called on class intialization
    """

    def __init__(self, identifiers, fields, datatable, identity_field, credentials, query = None, optional_id = False):
        super().__init__(identifiers, fields, datatable, identity_field, credentials, optional_id = optional_id)
        self._data = self.__gather_data(query)    
    
    def __gather_data(self, query):
        if query is None:
            if self.identifiers_type is list:
                query = "select {} from {} where {} in ({})".format(self.fields, self.datatable, self.identity_field, str(self.identifiers).strip('[]'))
            else:
                query = "select {} from {} where {} = '{}'".format(self.fields, self.datatable, self.identity_field, self.identifiers)
        df = self._query(query).set_index(self.identity_field)
        return df.to_dict(orient='index')
        

class TSFeed(Feed):
    """
    The base class for all time series feeds 

    ...

    Parameters
    ----------
    identifiers : list
        list of identifiers to define Foreign Key within the query
    fields : String 
        list of fields to pull from "select" statement
    datatable : String
        datatable to get data from
    identity_field : String
        field to identify Foreign Key (self.identifiers list)
    credentials : dictionary
        credentials to pass into connector
    bar : String
        type of data resolution to pull
    start_date : String
        a YYYY-MM-DD string related to start date
    end_date : String
        a YYYY-MM-DD string related to end date
    override : Boolean, optional (default : False)
        override gather_data function
    optional_id : boolean, optional (default : False)
        ignore identifiers input, pass in empty list from constructor
    force_fast : boolean, optional (default : False)
        force use of __tmp_query
    
    Methods
    -------
    __gather_data()
        returns dataframe using query type, from the proper datatable format
    """
    

    def __init__(self, identifiers, fields, datatable, identity_field, credentials, bar, start_date, end_date, override = False, optional_id = False, force_fast = False):
        db = f'ts_{bar}_{datatable}' if bar is not None else f'ts_{datatable}'
        super().__init__(identifiers, fields, db, identity_field, credentials, optional_id = optional_id)
        self.bar = bar
        self.try_tmp_query = force_fast or len(identifiers) > 5
        self.start_date = start_date
        self.end_date = end_date
        self._data = None if override else self.__gather_data() 

    def __handle_fields(self, query):
        if self.connector.credentials['s_type'] == 'mssql+pyodbc':
            query = query.replace("open", f"{self.datatable}.[open] as 'open'")
            query = query.replace("high", f"{self.datatable}.[high] as 'high'")
            query = query.replace("low", f"{self.datatable}.[low] as 'low'")
            query = query.replace("close", f"{self.datatable}.[close] as 'close'")
            query = query.replace("volume", f"{self.datatable}.[volume] as 'volume'")
            query = query.replace("open_interest", f"{self.datatable}.[open_interest] as 'open_interest'")
        return query

    def __gather_data(self):
        self.complete_fields = f'date, {self.identity_field}, {self.fields}'
        if self.identifiers_type is list:
            query = "select date, {}, {} from {} where {} in ({})".format(self.identity_field, self.__handle_fields(self.fields), self.datatable, self.identity_field, str(self.identifiers).strip('[]'))
        else:
            query = "select date, {}, {} from {} where {} = '{}'".format(self.identity_field, self.__handle_fields(self.fields), self.datatable, self.identity_field, self.identifiers)
        
        if self.start_date:
            query += " and date >= '{}'".format(self.start_date)
        if self.end_date:
            query += " and date <= '{}'".format(self.end_date)

        date_format = '%Y-%m-%d' if self.bar == 'daily' else '%Y-%m-%d %H:%M'
        df = self._query(query).set_index(['date', self.identity_field]).stack().reset_index()
        df.columns = ['date', self.identity_field, 'field', 'value']

        if self.identifiers_type is list and len(self.identifiers) > 1:
            cols = [self.identity_field, 'field']
        else:
            cols = 'field'
        
        df = df.pivot_table(index = 'date', columns = cols, values = 'value')
        df.index = pd.to_datetime(df.index, format=date_format)

        return df

class CustomFeed(Feed):
    """
    Custom Feeds class (input query) 

    """
    def __init__(self, query, try_tmp = False, credentials = None, override = False, optional_id = True):
        super().__init__(None, "", "", "", credentials, optional_id = optional_id)
        self.query = query
        self.try_tmp_query = try_tmp
        self._data = None if override else self.__gather_data() 
    
    def __gather_data(self):
        return self._query(self.query) 

