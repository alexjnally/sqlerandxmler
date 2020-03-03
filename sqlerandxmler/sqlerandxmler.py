"""
Created on Mon Feb 10 14:42:44 2020

@author: Alex Nally @ Genesis Financial Solutions
"""

import pandas as pd
import os
import pyodbc
from xml.etree.ElementTree import fromstring, ElementTree
from time import time
pd.set_option('max_columns', 30)
pd.set_option('max_colwidth', 25)



class xmler:
    def __init__(self, xml, xmlcol):
        self.xml = xml
        self.xmlcol = xmlcol
        if self.xml is None:
            self.root = None
        elif self.xmlcol in ('InterConnectResponse', 'InterConnectRequest', 'Request', 'Response', 'RawSoapResponse', 'RawSoapRequest'):
            self.root = ElementTree(fromstring(xml)).getroot()
            self.ns = None
        else:
            raise TypeError('This XML type might not be supported')
#        self.attrs = [(elem.tag) if self.root is not None else '' for elem in self.root.iter()]
#        self.attrs = attr_sorter(self.root, self.root_ns, LOB, PL_Request)


    def find_xpath(self, xpath):

        def reconfigure_xpath(xpath):
            if xpath[0] != '.':
                xpath = ".//ns:" + xpath
                return xpath
            elif xpath[0] == '.':
                if xpath[0:3] != r'.//':
                    raise ValueError(r'Non-singular Xpaths must start .//')
                else:
                    split = xpath.split('//')
                    xpath = '.'
                    for chunk in split[1:]:
                        xpath = xpath + '//ns:' + chunk
                        i = xpath.find('[')
                    if i > 0:
                        xpath = xpath[0:i + 1] + 'ns:' + xpath[i + 1:]
                    return xpath
            else:
                return xpath

        if self.root is not None:

            if self.xmlcol in ('InterConnectResponse', 'InterConnectRequest', 'Request', 'Response'):
                list1 = [elem.text for elem in self.root.findall(reconfigure_xpath(xpath), namespaces={'ns': 'http://xml.equifax.com/XMLSchema/InterConnect'})]
            elif self.xmlcol in ('RawSoapResponse', 'RawSoapRequest'):
                list1 = [elem.text for elem in self.root.findall(xpath)]
            shorten = lambda list1: list1 if len(list1) > 1 else (list1[0] if len(list1) == 1 else None)
            return shorten(list1)

        elif self.root is None:
            return None


class sqler:

    def __init__(self, query_text, database='SQL12'):
        self.c1 = time()
        self.conn = pyodbc.connect(r"DSN={};table=RetailerLendingPortal; Trusted_Connection=yes".format(database))
        self.c2 = time()
        self.ctime = self.c2 - self.c1
        self.db = database
        self.text = query_text
        self.tic = time()
        self.data = pd.read_sql(self.text, self.conn)
        self.toc = time()
        self.etime = self.toc - self.tic
        self.conn.close()
        print('\n=======================\nConnection Time: ' + str(self.ctime)[:4] + ' s\nExecution Time:  ' + str(self.etime)[:4] + ' s')
        self.ptime = 0
        self.stime = 0

    def parse(self, xpaths, xmlcol='InterConnectResponse'):
        """This does that."""
        self.xmlcol = xmlcol
        self.xpaths = xpaths
        self.p1 = time()
        if self.xmlcol is None:
            raise ValueError('No XML column defined. Define XML column or delete q.parse()')

        elif type(self.xmlcol) != str:
            raise TypeError('xml_col must be string')

        elif isinstance(self.xpaths, list):
            for tag in self.xpaths:
                if isinstance(tag, dict):
                    if len(tag) > 1:
                        raise TypeError('Dict must be length 1')
                    else:
                        self.data[str(list(tag.values())[0]) + '_py'] = (self.data[xmlcol].apply(lambda xml: xmler(xml, self.xmlcol) if xml is not None else None)).apply(lambda col: col.find_xpath(list(tag.keys())[0]) if col is not None else None)
                else:
                    splitter = tag.split('//')
                    if splitter[-1] in ('Code'):
                        colname = splitter[-2] + '/' + splitter[-1] + '_py'
                        
                    elif splitter[-1] in ('Description'):
                        colname = splitter[-2] + '/' + splitter[-1] + '_py'

                    elif splitter[-1] in ('AttributeValue', 'Value'):
                        colname = tag.split('"')[-2] + '_py'

                    else:
                        colname = splitter[-1] + '_py'

                    self.data[colname] = (self.data[xmlcol].apply(lambda xml: xmler(xml, self.xmlcol) if xml is not None else None)).apply(lambda col: col.find_xpath(tag) if col is not None else None)

#         del self.data['Root']   ##################

        else:
            raise TypeError('Xpaths must be of type list')

        self.p2 = time()
        self.ptime = self.p2 - self.p1
        print('Parsing Time:    ' + str(self.ptime)[:4] + ' s')


    def save(self, to_file='QueryResults/PythonQueryResults.csv'):
        """
        This does that.
        """
        self.s1 = time()
        import xlsxwriter
        to_file = to_file.replace(' ', '')
        if to_file[-4:] == '.csv':
            ftype = 1
        elif to_file[-5:] == '.xlsx':
            ftype = 2
        else:
            to_file = to_file + '.csv'
            ftype = 1

        for col in ('InterConnectResponse', 'InterConnectRequest', 'Response', 'Request', 'RawSoapResponse', 'RawSoapRequest'):
            if col in self.data.columns:
                del self.data[col]

        def try_to_save(_to_file, _ftype, _data, _counter):
            try:
                if _ftype == 1:
                    _data.to_csv(_to_file)
                elif _ftype == 2:
                    _data.to_excel(_to_file)
                excel_path = 'start EXCEL.EXE ' + _to_file
                os.system(excel_path)
                self.s2 = time()
                self.stime = self.s2 - self.s1
                print('Save File Time:  ' + str(self.stime)[:4] + ' s\n========================')

            except (xlsxwriter.exceptions.FileCreateError, PermissionError):
                _counter += 1
                if _ftype == 1:
                    _to_file = _to_file.replace('.csv', '').replace('_v{}'.format(_counter - 1), '') + '_v{}.csv'.format(_counter)
                elif _ftype == 2:
                    _to_file = _to_file.replace('.xlsx', '').replace('_v{}'.format(_counter - 1), '') + '_v{}.xlsx'.format(_counter)
                try_to_save(_to_file, _ftype, _data, _counter)

        try_to_save(to_file, ftype, self.data, 1)

        print('TOTAL TIME:      ' + str(self.etime + self.ctime + self.stime + self.ptime)[:4] + ' s\n========================')
        print('Saved! \nOpening Excel...')
