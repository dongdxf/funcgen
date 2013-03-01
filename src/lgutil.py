#!/usr/bin/env python
# -*- Encoding: UTF-8 -*-
# -*- Filename: lgutil.py -*-
# -*- Datetime: 2011-10-03 20:20:20 -*-


import os
import re
import sys
import platform
import datetime
import logging
import logging.config

from jinja2 import Environment, FileSystemLoader

from glbvar import SYSID, OPRS, OPERATIONS, OPDICT


if 'Windows' == platform.system():
    logging.config.fileConfig(os.path.join('config', 'logger.cfg.win'))
else:
    logging.config.fileConfig(os.path.join('config', 'logger.cfg.unix'))
logger = logging.getLogger('lgutil')


class Table(object):
    
    def __init__(self, name, flag, columns, funcs):
        self.name = name
        self.flag = flag
        self.columns = columns
        self.funcs = funcs
    
    def setFlag(self, flag):
        self.flag = flag


class Column(object):
    
    def __init__(self, name, type, size):
        self.name = name
        self.type = type
        self.size = size


class Func(object):
    
    def __init__(self, type, macro, name, targs, conds):
        self.type = type
        self.macro = macro
        self.name = name
        self.targs = targs
        self.conds = conds


class Macro(object):
    
    def __init__(self, name, value, comstr):
        self.name = name
        self.value = value
        self.comstr = comstr


class DDLAnalyzer(object):
    
    def __init__(self):
        pass
    
    def _convTypeAndSize(self, ctype, csize):
        _type = ''
        _size = 0
        if ctype == 'char' or ctype == 'character' or ctype == 'varchar':
            _type = 'char'
            _size = csize
        elif ctype == 'timestamp':
            _type = 'char'
            _size = 26
        elif ctype == 'date':
            _type = 'char'
            _size = 10
        elif ctype == 'time':
            _type = 'char'
            _size = 8
        elif ctype == 'decimal':
            _type = 'double'
        elif ctype == 'double':
            _type = 'double'
        elif ctype == 'real':
            _type = 'float'
        elif ctype == 'smallint':
            _type = 'short'
        elif ctype == 'integer':
            _type = 'int'
        elif ctype == 'bigint':
            _type = 'long'
        else:
            logger.error('暂不支持此字段类型[%s]!' % ctype)
            return (_type, _size)    # (_type = '', _size = 0)
        return (_type, _size)
    
    def analyze(self, file):
        tables = []
        errmsg = ''
        _tblnames = []
        _columns = []
        _flag = 0
        _tblinflg = 0
        
        try:
            fp = open(file, 'r')
        except IOError:
            errmsg = '打开DDL文件[%s]错误!' % file
            logger.error(errmsg)
            return (tables, errmsg)
        
        for line in fp.readlines():
            line = line.strip().lower()
            if line == '':
                continue    # skip blank lines
            if line[:2] == '--':
                continue    # skip comments
            words = line.split()
            if len(words) < 2:
                if ';' in line and 1 == _tblinflg:
                    _tblinflg = 0
                    if len(_columns) > 0:
                        tables.append(Table(_tblnames[-1], 1, _columns, []))    # ');'单起一行结束表定义
                    _columns = []
                continue
            if words[0] == 'create' and words[1] == 'table':
                tblname = words[2]    # words[2].split('.')[1]
                if tblname[-1:] == '(':
                    tblname = tblname[:-1]
                tblname = tblname.replace('"', '')
                if tblname[-3:].isdigit():    # Multiple table (<1000)
                    _flag = int(tblname[-3:])
                    tblname = tblname[:-3]
                elif tblname[-2:].isdigit():    # Multiple table (<100)
                    _flag = int(tblname[-2:])
                    tblname = tblname[:-2]
                elif tblname[-1:].isdigit():    # Multiple table (<10)
                    _flag = int(tblname[-1:])
                    tblname = tblname[:-1]
                if tblname not in _tblnames:
                    _tblnames.append(tblname)
                    _tblinflg = 1
                else:
                    for idx, table in enumerate(tables):
                        if tblname == table.name:
                            tables[idx].setFlag(_flag)
                continue
            if _tblinflg == 1:
                if 'constraint' in line:
                    _tblinflg = 0
                    if len(_columns) > 0:
                        tables.append(Table(_tblnames[-1], 1, _columns, []))    # 'constraint'结束表定义
                    _columns = []
                    continue
                lst = re.findall('\w+', line)
                colname = lst[0]
                if len(lst) == 2:
                    (coltype, colsize) = self._convTypeAndSize(lst[1], 0)
                else:
                    (coltype, colsize) = self._convTypeAndSize(lst[1], lst[2])
                if '' == coltype and 0 == colsize:
                    fp.close()
                    tables = []
                    errmsg = '转换表[%s]字段[%s]的类型[%s]和其长度错误!' % (_tblnames[-1], lst[0], lst[1])
                    logger.error(errmsg)
                    return (tables, errmsg)
                _columns.append(Column(colname, coltype, colsize))
                if ';' in line:
                    _tblinflg = 0
                    if len(_columns) > 0:
                        tables.append(Table(_tblnames[-1], 1, _columns, []))    #最后一列后跟');'结束表定义
                    _columns = []
                    continue
        fp.close()
        if 0 == len(tables):
            errmsg = 'DDL文件[%s]中未找到任何表定义!' % file
            logger.error(errmsg)
            return (tables, errmsg)
        return (tables, errmsg)


def main():
    exit_code = 0
    
    if len(sys.argv) < 2:
        sys.exit('Usage: %s DDLFileName [...]' % sys.argv[0])
    
    ddla = DDLAnalyzer()
    env = Environment(loader=FileSystemLoader('templates', encoding='ascii'), trim_blocks=True)
    htmplt = env.get_template('tblnm.h')
    h_tmplt = env.get_template('tbl_nm.h')
    dt = datetime.datetime.now()
    year = dt.strftime('%Y')
    nowdt = dt.strftime('%Y/%m/%d')
    
    for arg in sys.argv[1:]:
        ddlf = os.path.join('input', arg)
        (tables, errmsg) = ddla.analyze(ddlf)
        if 0 == len(tables):
            print('解析DDL文件[%s]错误! 错误原因: %s' % (ddlf, errmsg))
            exit_code = 1
            continue
        
        for table in tables:
            tblname = table.name.split('.')[1]
            
            tabmacro = tblname.replace('_', '').upper() + '_H'
            rndred_htmplt = htmplt.render(cr_year=year,
                                          crt_time=nowdt,
                                          tabmacro=tabmacro,
                                          columns=table.columns,
                                          tbl_name=tblname)
            headfile = os.path.join('output', 'include', (tblname.replace('_', '') + '.h'))
            with open(headfile, 'wb') as fp:
                if sys.version_info[0] < 3:
                    fp.write(rndred_htmplt)
                else:
                    fp.write(bytes(rndred_htmplt, 'gbk'))
            
            tab_macro = tblname.upper() + '_H'
            macros = [func.macro for func in table.funcs]
            lflgs = list(range(1, table.flag+1))
            rndred_h_tmplt = h_tmplt.render(cr_year=year,
                                            crt_time=nowdt,
                                            tabmacro=tab_macro,
                                            columns=table.columns,
                                            tbl_name=tblname,
                                            macros=macros,
                                            oprs=OPRS,
                                            tbl_flag=table.flag,
                                            flags=lflgs)
            head_file = os.path.join('output', 'include', (tblname + '.h'))
            with open(head_file, 'wb') as fp:
                if sys.version_info[0] < 3:
                    fp.write(rndred_h_tmplt)
                else:
                    fp.write(bytes(rndred_h_tmplt, 'gbk'))
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
