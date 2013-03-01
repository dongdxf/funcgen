#!/usr/bin/env python
# -*- Encoding: UTF-8 -*-
# -*- Filename: main.py -*-
# -*- Datetime: 2011-10-03 20:20:20 -*-


import os
import sys
import pickle
import platform
import datetime
import hashlib
import logging
import logging.config

from tkinter import *
from tkinter.ttk import *
from tkinter.filedialog import *
from tkinter.messagebox import *

from jinja2 import Environment, FileSystemLoader

from uiutil import *
from glbvar import SYSID, OPRS, OPERATIONS, OPDICT
from lgutil import Table, Column, Func, Macro, DDLAnalyzer


if 'Windows' == platform.system():
    logging.config.fileConfig(os.path.join('config', 'logger.cfg.win'))
else:
    logging.config.fileConfig(os.path.join('config', 'logger.cfg.unix'))
logger = logging.getLogger('root')


class App(Frame):
    
    def __init__(self, root):
        Frame.__init__(self, root)
        root.title('根据DDL文件生成封装函数 | V0.2')
        root.protocol('WM_DELETE_WINDOW', self.onCloseApp)
        
        self.filemd5 = ''
        self.tables = []
        self.tblidx = -1
        self.funidx = -1
        self.errmsg = ''
        self.cnter = dict(zip(OPERATIONS, (0, 0, 0, 0, 0, 0, 0, 0)))
        
        self.fileframe = Frame()
        self.fileframe.pack(fill=X, padx=2, pady=2)
        Separator(orient=HORIZONTAL).pack(fill=X, padx=2, pady=10)
        Separator(orient=HORIZONTAL).pack(fill=X, padx=2, pady=10)
        self.bodyframe = Frame()
        self.bodyframe.pack(fill=X, padx=2, pady=2)
        Separator(orient=HORIZONTAL).pack(fill=X, padx=2, pady=10)
        self.viewframe = Frame()
        self.viewframe.pack(fill=X, padx=2, pady=2)
        
        self.lplcframe = Frame()
        self.lplcframe.place(relwidth=0.6, in_=self.fileframe)
        Label(self.lplcframe, text='请选择DDL文件:').pack(side=LEFT, padx=2, pady=2)
        self.fnentry = Entry(self.lplcframe, justify=LEFT)
        self.fnentry.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        Button(self.lplcframe, text='  浏    览  ', command=self.onSelectFile).pack(side=LEFT, padx=2, pady=2)
        self.rplcframe = Frame()
        self.rplcframe.place(relx=0.6, relwidth=0.4, in_=self.fileframe)
        Label(self.rplcframe, text=' '*20+'请选择表:').pack(side=LEFT, padx=2, pady=2)
        self.tblcombox = Combobox(self.rplcframe, values=[], state='readonly', height=5)
        self.tblcombox.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.tblcombox.bind('<<ComboboxSelected>>', self.onSwitchTable)
        
        self.leftframe = Frame()
        self.leftframe.pack(side=LEFT, fill=BOTH, expand=1, padx=0, pady=2, in_=self.bodyframe)
        self.ltopframe = Frame()
        self.ltopframe.pack(fill=X, padx=0, pady=2, in_=self.leftframe)
        self.otentry = Entry(self.ltopframe, justify=LEFT)
        self.otentry.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        Button(self.ltopframe, text='  增    加  ', command=self.onAddFuncDef).pack(side=LEFT, padx=2, pady=2)
        self.lmidframe = Frame()
        self.lmidframe.pack(fill=BOTH, expand=1, padx=0, pady=2, in_=self.leftframe)
        self.optpframe = LabelFrame(self.lmidframe, text='操作类型')
        self.optpframe.pack(fill=BOTH, expand=1, padx=2, pady=2)
        self.optplist = MyScrolledList(self.optpframe)
        self.optplist.pack(fill=BOTH, expand=1, padx=2, pady=2)
        self.optplist.listbox.config(selectmode=SINGLE)
        self.optplist.listbox.bind('<Button-1>', self.onSelectOpItem)
        self.optplist.listbox.bind('<Double-1>', self.onDeleteOpItem)
        self.lbotframe = Frame()
        self.lbotframe.pack(fill=X, padx=0, pady=2, in_=self.leftframe)
        Button(self.lbotframe, text='  头 文 件  ', command=self.onGenHFiles).pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        Button(self.lbotframe, text=' SQC 文 件 ', command=self.onGenSqcFiles).pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        Button(self.lbotframe, text='  全    部  ', command=self.onGenAllFiles).pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        Separator(orient=VERTICAL).pack(side=LEFT, fill=Y, padx=10, pady=2, in_=self.bodyframe)
        self.destframe = Frame()
        self.destframe.pack(side=LEFT, fill=BOTH, expand=1, padx=2, pady=2, in_=self.bodyframe)
        self.targframe = LabelFrame(self.destframe, text='目标字段')
        self.targframe.pack(fill=X, padx=2, pady=2)
        self.targlist = MyScrolledList(self.targframe)
        self.targlist.pack(fill=BOTH, expand=1, padx=2, pady=2)
        self.targlist.listbox.bind('<Double-1>', self.onDeleteTargItem)
        Separator(orient=HORIZONTAL).pack(fill=X, expand=1, padx=2, pady=10, in_=self.destframe)
        self.condframe = LabelFrame(self.destframe, text='条件字段')
        self.condframe.pack(fill=X, padx=2, pady=2)
        self.condlist = MyScrolledList(self.condframe)
        self.condlist.pack(fill=BOTH, expand=1, padx=2, pady=2)
        self.condlist.listbox.bind('<Double-1>', self.onDeleteCondItem)
        self.bttnframe = Frame()
        self.bttnframe.pack(side=LEFT, padx=2, pady=2, in_=self.bodyframe)
        Button(self.bttnframe, text='  < < <  ', command=self.onInsertToTargList).pack(padx=2, pady=20)
        Button(self.bttnframe, text='  > > >  ', command=self.onDeleteFromTargList).pack(padx=2, pady=20)
        Separator(orient=HORIZONTAL).pack(fill=X, expand=1, padx=2, pady=40, in_=self.bttnframe)
        Button(self.bttnframe, text='  < < <  ', command=self.onInsertToCondList).pack(padx=2, pady=20)
        Button(self.bttnframe, text='  > > >  ', command=self.onDeleteFromCondList).pack(padx=2, pady=20)
        self.colsframe = LabelFrame(self.bodyframe, text='字段集合')
        self.colsframe.pack(side=LEFT, fill=BOTH, expand=1, padx=2, pady=2, in_=self.bodyframe)
        tablehead = ('序    号', '名    称', '类    型', '长    度')
        self.tableview = MyTableView(self.colsframe, tablehead, [])
        
        #self.codeframe = LabelFrame(self.viewframe, text='代码预览')
        #self.codeframe.pack(side=LEFT, fill=BOTH, expand=1, padx=2, pady=2)
        #self.codetext = MyScrolledText(self.codeframe)
        #self.codetext.pack(side=LEFT, fill=BOTH, expand=1, padx=2, pady=2)
        self.ilogframe = LabelFrame(self.viewframe, text='运行日志')
        self.ilogframe.pack(side=LEFT, fill=BOTH, expand=1, padx=2, pady=2)
        self.ilogtext = MyScrolledText(self.ilogframe)
        self.ilogtext.pack(side=LEFT, fill=BOTH, expand=1, padx=2, pady=2)
    
    def onSelectFile(self):
        ddlfilename = askopenfilename(defaultextension='.sql',
                                      filetypes=[('sql files', '*.sql'), ('txt files', '*.txt'), ('all files', '*')],
                                      initialdir='input',
                                      initialfile='test.sql',
                                      parent=self,
                                      title='选择您要打开的文件')
        if not ddlfilename:
            return
        
        if 'Windows' == platform.system():
            ddlfilename = ddlfilename.replace('/', '\\')
        
        if not self._testFileIsOK(ddlfilename):
            logger.error('打开DDL文件[%s]错误!' % ddlfilename)
            return
        
        tmpmd5 = self._getFileMd5(ddlfilename)
        if not tmpmd5:
            logger.error('获取DDL文件[%s]MD5值错误!' % ddlfilename)
            return
        
        if not self.filemd5:    # 首次运行
            pass
        elif tmpmd5 == self.filemd5:    # 同一文件或不同文件但内容相同
            self.fnentry.delete(0, END)
            self.fnentry.insert(END, ddlfilename)
            return
        else:    # 不同文件或同一文件但内容不同
            self.saveScene2His(self.tblidx)
            self.tables = []
            self.tblidx = -1
            self.funidx = -1
            self.errmsg = ''
            self.cnter = dict(zip(OPERATIONS, (0, 0, 0, 0, 0, 0, 0, 0)))
            self.updateUI(clearui=True)
        
        self.filemd5 = tmpmd5
        self.fnentry.delete(0, END)
        self.fnentry.insert(END, ddlfilename)
        
        ddla = DDLAnalyzer()
        (self.tables, self.errmsg) = ddla.analyze(ddlfilename)
        if 0 == len(self.tables):
            logger.error('解析DDL文件[%s]错误! 错误原因: %s' % (ddlfilename, self.errmsg))
            return
        
        tabnames = [table.name for table in self.tables]
        self.tblcombox.destroy()
        self.tblcombox = Combobox(self.rplcframe, values=tabnames, state='readonly', height=5)
        self.tblcombox.pack(side=LEFT, fill=X, expand=1, padx=2, pady=2)
        self.tblcombox.bind('<<ComboboxSelected>>', self.onSwitchTable)
    
    def _testFileIsOK(self, filename):
        fp = None
        bRet = False
        try:
            fp = open(filename, 'r')
            bRet = True
        except:
            logger.error('无法打开文件[%s]!' % filename)
            logger.error(sys.exc_info()[1])
            bRet = False
        finally:
            if fp:
                fp.close()
        
        return bRet
    
    def _getFileMd5(self, filename):
        fp = None
        rdstr = ''
        md5str = ''
        md5 = hashlib.md5()
        try:
            fp = open(filename, 'rb')
            while True:
                rdstr = fp.read(8096)
                if not rdstr:
                    break
                md5.update(rdstr)
            md5str = md5.hexdigest()
        except:
            logger.error('计算文件[%s]的MD5值错误!' % filename)
            logger.error(sys.exc_info()[1])
            md5str = ''
        finally:
            if fp:
                fp.close()
        
        return md5str
    
    def onSwitchTable(self, event):
        tmpidx = event.widget.current()
        if -1 == self.tblidx:    # 首次运行
            self.tblidx = tmpidx
            self.loadFromHis()
            self.updateUI(clearui=False)
        elif tmpidx == self.tblidx:    # 表未切换
            pass
        else:    # 表已切换
            self.saveScene2His(self.tblidx)
            self.tblidx = tmpidx
            self.loadFromHis()
            self.updateUI(clearui=True)
    
    def updateUI(self, clearui=True):
        if clearui:
            self.otentry.delete(0, END)
            self.optplist.clear()
            self.targlist.clear()
            self.condlist.clear()
            self.tableview.clearTable()
        
        self.funidx = -1
        self.errmsg = ''
        self.cnter = dict(zip(OPERATIONS, (0, 0, 0, 0, 0, 0, 0, 0)))
        
        try:
            _items = []
            _items = [(i, column.name, column.type, column.size)
                      for i, column in enumerate(self.tables[self.tblidx].columns, start=1)]
            self.tableview.clearTable()
            self.tableview.fillTable(_items)
        except:
            logger.error('填充字段集合表格错误! 当前表索引为[%d]!' % self.tblidx)
            logger.error(sys.exc_info()[1])
        
        try:
            funccnt = 0
            for _func in self.tables[self.tblidx].funcs:
                _text = ''
                if _func.macro.comstr:
                    _text = _func.macro.name + '  ' + _func.macro.comstr
                else:
                    _text = _func.macro.name
                self.optplist.append(_text)
                self.cnter[_func.type] += 1
                funccnt += 1
        except:
            logger.error('填充操作类型表格错误! 当前表索引为[%d]!' % self.tblidx)
            logger.error(sys.exc_info()[1])
        finally:
            if funccnt != 0:
                self.funidx = 0
                self.optplist.listbox.selection_clear(0, END)
                self.optplist.listbox.selection_set(self.funidx)
                self.otentry.delete(0, END)
                self.otentry.insert(END, self.optplist.listbox.get(self.funidx))
                self.targlist.clear()
                self.condlist.clear()
                _targs = self.tables[self.tblidx].funcs[self.funidx].targs
                for _targ in _targs:
                    self.targlist.append(_targ[1])
                _conds = self.tables[self.tblidx].funcs[self.funidx].conds
                for _cond in _conds:
                    self.condlist.append(_cond[1])
    
    def onAddFuncDef(self):
        if -1 == self.tblidx:
            logger.error('尚未选择表!')
            return
        
        rawtext = self.otentry.get().strip()
        if not rawtext:
            return
        
        operation = rawtext.upper().split('_')[0]
        if operation in OPERATIONS[0:4]:
            self._addFuncDef(rawtext)
        elif operation == OPERATIONS[4]:    # 游标声明
            cur_operations = list(OPERATIONS[4:])
            cur_operations.reverse()
            for cur_op in cur_operations:
                rawtext = cur_op + rawtext[len(cur_op):]
                self._addFuncDef(rawtext)
        elif operation in OPERATIONS[5:]:
            pass
        else:
            logger.error('[%s] is not a valid operation!' % operation)
            return
    
    def _addFuncDef(self, rawtext):
        _name = ''
        _value = 0
        _comstr = ''
        _text = ''
        
        # _comstr取值
        comlidx = rawtext.find('/*')
        comridx = rawtext.find('*/')
        if -1 == comlidx and -1 == comridx:
            _comstr = ''
        elif ((-1 == comlidx and comridx >= 0) or (comlidx >= 0 and -1 == comridx) or (comridx - comlidx < 2)):
            logger.error('注释标识符不匹配!')
            return
        else:
            tmpstr = rawtext[comlidx+2:comridx].strip()
            if not tmpstr:
                _comstr = ''
            else:
                _comstr = '/* ' + tmpstr + ' */'
        
        # _name取值
        if -1 == comlidx:
            tmpkey = rawtext.strip()
        else:
            tmpkey = rawtext[:comlidx].strip()
        if not tmpkey:
            return
        _name = tmpkey.upper()
        operation = _name.split('_')[0]
        if operation in OPERATIONS[5:]:
            _comstr = ''
        
        # _text取值
        if _comstr:
            _text = _name + '  ' + _comstr
        else:
            _text = _name
        
        # 判断_name是否已存在。若存在，只更新列表和当前func的macro
        i = 0
        idx = -1
        _items = self.optplist.listbox.get(0, END)
        for i, _item in enumerate(_items):
            if _item.split()[0] == _name:
                idx = i
                break
        if -1 != idx:    # _name已存在
            self.funidx = idx
            self.optplist.delete(idx)
            self.optplist.insert(idx, _text)
            self.optplist.listbox.selection_clear(0, END)
            self.optplist.listbox.selection_set(self.funidx)
            self.tables[self.tblidx].funcs[self.funidx].macro.comstr = _comstr
            return
        
        # _value取值
        i = 0
        idx = 0
        for i, _operation in enumerate(OPERATIONS):
            idx += self.cnter[_operation]
            if _operation == operation:
                break
        _value = (i+1)*100 + (self.cnter[operation] + 1)
        self.funidx = idx
        
        macro = Macro(_name, _value, _comstr)
        func = Func(operation, macro, '', [], [])
        self.tables[self.tblidx].funcs.insert(self.funidx, func)
        self.optplist.insert(self.funidx, _text)
        self.optplist.listbox.selection_clear(0, END)
        self.optplist.listbox.selection_set(self.funidx)
        self.cnter[operation] += 1
        self.targlist.clear()
        self.condlist.clear()
    
    def onSelectOpItem(self, event):
        if -1 == self.tblidx or -1 == self.funidx:
            return
        self.funidx = self.optplist.listbox.nearest(event.y)
        self.otentry.delete(0, END)
        self.otentry.insert(END, self.optplist.listbox.get(self.funidx))
        self.targlist.clear()
        self.condlist.clear()
        _targs = self.tables[self.tblidx].funcs[self.funidx].targs
        for _targ in _targs:
            self.targlist.append(_targ[1])
        _conds = self.tables[self.tblidx].funcs[self.funidx].conds
        for _cond in _conds:
            self.condlist.append(_cond[1])
    
    def onDeleteOpItem(self, event):
        if -1 == self.tblidx or -1 == self.funidx:
            return
        tmpidx = self.optplist.listbox.nearest(event.y)
        idxes = []
        _text = self.optplist.listbox.get(tmpidx)
        operation = _text.split('_')[0]
        if operation in OPERATIONS[0:4]:
            idxes = [tmpidx]
        elif operation in OPERATIONS[4:]:    # 游标声明
            idx = OPERATIONS.index(operation)
            rngs = len(OPERATIONS) - 1 - idx 
            idxes = [tmpidx+i*self.cnter[operation] for i in list(range(rngs, rngs-4, -1))]
        else:
            idxes = []
        self._deleteOpItem(idxes)
        
    def _deleteOpItem(self, idxes):
        for tmpidx in idxes:
            self.cnter[self.tables[self.tblidx].funcs[tmpidx].type] -= 1
            self.tables[self.tblidx].funcs.pop(tmpidx)
            self.optplist.delete(tmpidx)
            self.optplist.listbox.selection_clear(0, END)
            self.targlist.clear()
            self.condlist.clear()
            funcnum = len(self.tables[self.tblidx].funcs)
            if funcnum == 0:
                self.funidx = -1
            elif tmpidx >= funcnum:
                self.funidx = tmpidx - 1
    
    def onInsertToTargList(self):
        if -1 == self.tblidx or -1 == self.funidx:
            return
        _targitems = []
        _seleitems = self.tableview.table.selection()
        _targitems = [self.tableview.table.item(_seleitem, values=None)[0:2]
                     for _seleitem in _seleitems]
        for _targitem in _targitems:
            appendflag = 1
            _targs = self.tables[self.tblidx].funcs[self.funidx].targs
            for i, _targ in enumerate(_targs):
                if int(_targ[0]) == int(_targitem[0]):    # 已存在
                    appendflag = 0
                    break
                elif int(_targ[0]) > int(_targitem[0]):    # 插入当前位置
                    self.tables[self.tblidx].funcs[self.funidx].targs.insert(i, _targitem)
                    self.targlist.insert(i, _targitem[1])
                    appendflag = 0
                    break
            if appendflag:
                self.tables[self.tblidx].funcs[self.funidx].targs.append(_targitem)
                self.targlist.append(_targitem[1])
    
    def onDeleteFromTargList(self):
        if -1 == self.tblidx or -1 == self.funidx:
            return
        idxes = [int(idx) for idx in self.targlist.listbox.curselection()]
        idxes.reverse()
        for idx in idxes:
            self.tables[self.tblidx].funcs[self.funidx].targs.pop(idx)
            self.targlist.delete(idx)
    
    def onDeleteTargItem(self, event):
        if -1 == self.tblidx or -1 == self.funidx:
            return
        if 0 == self.targlist.count():
            return
        tmpidx = self.targlist.listbox.nearest(event.y)
        self.tables[self.tblidx].funcs[self.funidx].targs.pop(tmpidx)
        self.targlist.delete(tmpidx)
    
    def onInsertToCondList(self):
        if -1 == self.tblidx or -1 == self.funidx:
            return
        _conditems = []
        _seleitems = self.tableview.table.selection()
        _conditems = [self.tableview.table.item(_seleitem, values=None)[0:2]
                     for _seleitem in _seleitems]
        for _conditem in _conditems:
            appendflag = 1
            _conds = self.tables[self.tblidx].funcs[self.funidx].conds
            for i, _cond in enumerate(_conds):
                if int(_cond[0]) == int(_conditem[0]):    # 已存在
                    appendflag = 0
                    break
                elif int(_cond[0]) > int(_conditem[0]):    # 插入当前位置
                    self.tables[self.tblidx].funcs[self.funidx].conds.insert(i, _conditem)
                    self.condlist.insert(i, _conditem[1])
                    appendflag = 0
                    break
            if appendflag:
                self.tables[self.tblidx].funcs[self.funidx].conds.append(_conditem)
                self.condlist.append(_conditem[1])
    
    def onDeleteFromCondList(self):
        if -1 == self.tblidx or -1 == self.funidx:
            return
        idxes = [int(idx) for idx in self.condlist.listbox.curselection()]
        idxes.reverse()
        for idx in idxes:
            self.tables[self.tblidx].funcs[self.funidx].conds.pop(idx)
            self.condlist.delete(idx)
    
    def onDeleteCondItem(self, event):
        if -1 == self.tblidx or -1 == self.funidx:
            return
        if 0 == self.condlist.count():
            return
        tmpidx = self.condlist.listbox.nearest(event.y)
        self.tables[self.tblidx].funcs[self.funidx].conds.pop(tmpidx)
        self.condlist.delete(tmpidx)
    
    def onGenHFiles(self):
        curdir = self._getCurDir()
        env = Environment(loader=FileSystemLoader('templates', encoding='ascii'), trim_blocks=True)
        htmplt = env.get_template('tblnm.h')
        h_tmplt = env.get_template('tbl_nm.h')
        dt = datetime.datetime.now()
        year = dt.strftime('%Y')
        nowdt = dt.strftime('%Y/%m/%d')
        
        table = self.tables[self.tblidx]
        if len(table.funcs) == 0:
            boolvar = askokcancel(title='数据检查',
                                  message='函数列表为空，头文件中将不包含任何数据库表操作宏定义。\n\n确定继续吗？')
            if not boolvar:
                return
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
        self.ilogtext.addText('头文件已生成，请点击下面链接查看：\n')
        self.ilogtext.addText(os.path.join(curdir, headfile), 'link')
        self.ilogtext.addText('')
        
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
        self.ilogtext.addText('头文件已生成，请点击下面链接查看：\n')
        self.ilogtext.addText(os.path.join(curdir, head_file), 'link')
        self.ilogtext.addText('')
        
        self.saveScene2His(self.tblidx)
    
    def onGenSqcFiles(self):
        curdir = self._getCurDir()
        env = Environment(loader=FileSystemLoader('templates', encoding='ascii'), trim_blocks=True)
        ctmplt = env.get_template('tbl_nm.c')
        sqctmplt = env.get_template('md5_tbl_nm.sqc')
        dt = datetime.datetime.now()
        year = dt.strftime('%Y')
        nowdt = dt.strftime('%Y/%m/%d')
        
        table = self.tables[self.tblidx]
        for func in table.funcs:
            if len(func.targs) == 0 \
               and (func.type == OPERATIONS[0]       # SEL
                    or func.type == OPERATIONS[1]    # INS
                    or func.type == OPERATIONS[2]    # UPD
                    or func.type == OPERATIONS[4]    # DCL
                    or func.type == OPERATIONS[6]    # FEC
                   ):
                boolvar = askokcancel(title='数据检查',
                                      message='函数 [ %s ] 目标字段列表为空，不符合代码规范。\n\n确定继续吗？' % func.macro.name)
                if not boolvar:
                    return
            if len(func.conds) == 0 \
               and (func.type == OPERATIONS[2]       # UPD
                    or func.type == OPERATIONS[3]    # DEL
                   ):
                boolvar = askokcancel(title='数据检查',
                                      message='函数 [ %s ] 条件字段列表为空，不符合代码规范。\n\n确定继续吗？' % func.macro.name)
                if not boolvar:
                    return
        tblname = table.name.split('.')[1]
        tblschema = table.name.split('.')[0]
        
        if table.flag == 1:    # 单表只需生成一个.sqc文件
            tblnm = tblname.replace('_', '')
            funcs = [Func(OPDICT[func.type], func.macro, func.name, func.targs, func.conds)
                     for func in table.funcs]
            curprefix = ''
            for tmpstr in tblname.split('_')[2:]:
                curprefix += tmpstr[0]
            md5 = hashlib.md5()
            md5.update(tblname.encode('ascii'))
            md5str = md5.hexdigest()
            prefix = SYSID + md5str[0:4] + '_'
            rndred_sqctmplt = sqctmplt.render(cr_year=year,
                                              crt_time=nowdt,
                                              tbl_name=tblname,
                                              tblnm=tblnm,
                                              oprs=OPRS,
                                              flag='',
                                              funcs=funcs,
                                              tbl_schema=tblschema,
                                              cur_prefix=curprefix)
            sqcfile = os.path.join('output', 'src', (prefix + tblname + '.sqc'))
            with open(sqcfile, 'wb') as fp:
                if sys.version_info[0] < 3:
                    fp.write(rndred_sqctmplt)
                else:
                    fp.write(bytes(rndred_sqctmplt, 'gbk'))
            self.ilogtext.addText('SQC文件已生成，请点击下面链接查看：\n')
            self.ilogtext.addText(os.path.join(curdir, sqcfile), 'link')
            self.ilogtext.addText('')
        else:    # 多表需要生成.c和多个.sqc文件
            lflgs = list(range(1, table.flag+1))
            
            rndred_ctmplt = ctmplt.render(cr_year=year,
                                          crt_time=nowdt,
                                          tbl_name=tblname,
                                          oprs=OPRS,
                                          flags=lflgs)
            cfile = os.path.join('output', 'src', (tblname + '.c'))
            with open(cfile, 'wb') as fp:
                if sys.version_info[0] < 3:
                    fp.write(rndred_ctmplt)
                else:
                    fp.write(bytes(rndred_ctmplt, 'gbk'))
            self.ilogtext.addText('C文件已生成，请点击下面链接查看：\n')
            self.ilogtext.addText(os.path.join(curdir, cfile), 'link')
            self.ilogtext.addText('')
            
            tblnm = tblname.replace('_', '')
            funcs = [Func(OPDICT[func.type], func.macro, func.name, func.targs, func.conds)
                     for func in table.funcs]
            curprefix = ''
            for tmpstr in tblname.split('_')[2:]:
                curprefix += tmpstr[0]
            for flag in lflgs:
                tblnmflg = tblname + str(flag)
                md5 = hashlib.md5()
                md5.update(tblnmflg.encode('ascii'))
                md5str = md5.hexdigest()
                prefix = SYSID + md5str[0:4] + '_'
                rndred_sqctmplt = sqctmplt.render(cr_year=year,
                                                  crt_time=nowdt,
                                                  tbl_name=tblname,
                                                  tblnm=tblnm,
                                                  oprs=OPRS,
                                                  flag=str(flag),
                                                  funcs=funcs,
                                                  tbl_schema=tblschema,
                                                  cur_prefix=curprefix)
                sqcfile = os.path.join('output', 'src', (prefix + tblnmflg + '.sqc'))
                with open(sqcfile, 'wb') as fp:
                    if sys.version_info[0] < 3:
                        fp.write(rndred_sqctmplt)
                    else:
                        fp.write(bytes(rndred_sqctmplt, 'gbk'))
                self.ilogtext.addText('SQC文件已生成，请点击下面链接查看：\n')
                self.ilogtext.addText(os.path.join(curdir, sqcfile), 'link')
                self.ilogtext.addText('')
        
        self.saveScene2His(self.tblidx)
    
    def onGenAllFiles(self):
        self.onGenHFiles()
        self.onGenSqcFiles()
    
    def _getCurDir(self):
        path = sys.path[0]
        if os.path.isdir(path):
            return path
        elif os.path.isfile(path):
            return os.path.dirname(path)
    
    def onCloseApp(self):
        self.saveScene2His(self.tblidx)
        self.quit()
    
    def saveScene2His(self, tblidx):
        if tblidx not in range(len(self.tables)):
            return
        table = self.tables[tblidx]
        dmpfile = os.path.join('history', (table.name + '.dat'))
        with open(dmpfile, 'wb') as fp:
            pickle.dump(table, fp, pickle.HIGHEST_PROTOCOL)
    
    def loadFromHis(self):
        table = self.tables[self.tblidx]
        dmpfile = os.path.join('history', (table.name + '.dat'))
        if os.path.isfile(dmpfile):
            boolvar = askyesno(title='请选择是否载入历史数据',
                               message='表 [ %s ] 存在历史数据，是否载入？' % table.name)
            if not boolvar:
                return
            with open(dmpfile, 'rb') as fp:
                self.tables[self.tblidx] = pickle.load(fp)


def main():
    root = Tk()
    app = App(root)
    root.geometry('1198x768+40+40')
    root.minsize(1198, 768)
    root.maxsize(1198, 768)
    root.mainloop()


if __name__ == '__main__':
    main()
