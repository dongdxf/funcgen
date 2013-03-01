#!/usr/bin/env python
# -*- Encoding: UTF-8 -*-
# -*- Filename: uiutil.py -*-
# -*- Datetime: 2011-10-03 20:20:20 -*-


import os
import subprocess

from tkinter import *
from tkinter.ttk import *
from tkinter.font import *


class callit:
    '''
    This little class helps me to call a callback with command option
    passing parameters to it
    The trick is in the definition of __call__, so that an instance of
    this class can replace a function
    '''
    def __init__(self, func, *args):
        self.func = func
        self.args = args
    
    def __call__(self, *ignored):
        self.func(*self.args)


class MyTableView(Frame):
    
    def __init__(self, master, header, items):
        Frame.__init__(self, master)
        self.header = header
        self.items = items
        
        self.pack(fill=BOTH, expand=1)
        
        self.table = Treeview(columns=self.header, show='headings')
        self.table.grid(column=0, row=0, sticky='nsew', in_=self)
        vsb = Scrollbar(orient='vertical', command=self.table.yview)
        vsb.grid(column=1, row=0, sticky='ns', in_=self)
        hsb = Scrollbar(orient='horizontal', command=self.table.xview)
        hsb.grid(column=0, row=1, sticky='ew', in_=self)
        self.table.config(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._initTable()
    
    def _initTable(self):
        self._setHeader()
        
        for item in self.items:
            self.table.insert('', 'end', values=item)
            # adjust columns widths if necessary
            for idx, val in enumerate(item):
                ilen = Font().measure(val)
                if self.table.column(self.header[idx], width=None) < ilen:
                    self.table.column(self.header[idx], width=ilen)
    
    def _setHeader(self):
        for col in self.header:
            self.table.heading(col, text=col)
            self.table.column(col, width=Font().measure(col))
    
    def fillTable(self, newitems):
        for item in newitems:
            self.table.insert('', 'end', values=item)
            # adjust columns widths if necessary
            for idx, val in enumerate(item):
                ilen = Font().measure(val)
                if self.table.column(self.header[idx], width=None) < ilen:
                    self.table.column(self.header[idx], width=ilen)
    
    def clearTable(self):
        children = self.table.get_children()
        for child in children:
            self.table.delete(child)
        
        self._setHeader()


class MyScrolledList(Frame):
    '''
    A compound widget containing a listbox and a vertical scrollbar.
    
    State/invariants:
        .listbox:     [ The Listbox widget       ]
        .vScrollbar:  [ The vertical scrollbar   ]
        .callback:    [ as passed to constructor ]
    '''
    def __init__(self, master=None, callback=None):
        '''
        Constructor for ScrolledList.
        '''
        Frame.__init__(self, master)
        self.callback = callback
        self.__createWidgets()
    
    def __createWidgets(self):
        '''
        Lay out internal widgets.
        '''
        self.listbox = Listbox(self, selectmode=EXTENDED)
        self.listbox.pack(side=LEFT, fill=BOTH, expand=1)
        self.vScrollbar = Scrollbar(self, orient='vertical', command=self.listbox.yview)
        self.vScrollbar.pack(side=LEFT, fill=Y)
        self.listbox.config(yscrollcommand=self.vScrollbar.set)
    
    def __clickHandler(self, event):
        '''
        Called when the user clicks on a line in the listbox.
        '''
        if not self.callback:
            return
        
        idx = self.listbox.nearest(event.y)
        self.callback(idx)
        self.listbox.focus_set()
    
    def count(self):
        '''
        Return the number of lines in use in the listbox.
        '''
        return self.listbox.size()
    
    def __getitem__(self, idx):
        '''
        Get the (idx)th line from the listbox.
        '''
        if (0 <= idx < self.count()):
            return self.listbox.get(idx)
        else:
            raise IndexError('ScrolledList[%d] out of range [0 ~ %d]!' % (idx, self.count()-1))
    
    def append(self, text):
        '''
        Append a line to the listbox.
        '''
        self.listbox.insert(END, text)
    
    def insert(self, idx, text):
        '''
        Insert a line between two existing lines.
        '''
        if (0 <= idx < self.count()):
            _idx = idx
        else:
            _idx = END
        
        self.listbox.insert(_idx, text)
    
    def delete(self, idx):
        '''
        Delete a line from the listbox.
        '''
        if (0 <= idx < self.count()):
            self.listbox.delete(idx)
    
    def clear(self):
        '''
        Remove all lines.
        '''
        self.listbox.delete(0, END)


class MyScrolledText(Frame):
    '''
    This class combines a Text and a Scrollbar
    to obtain a vertical scrollable text.
    '''
    def __init__(self, master):
        Frame.__init__(self, master)
        
        self.stext = Text(self, relief=SUNKEN, wrap='word')
        self.stext.pack(side=LEFT, fill=BOTH, expand=1)
        self.vsb = Scrollbar(self, orient='vertical', command=self.stext.yview)
        self.vsb.pack(side=LEFT, fill=Y)
        self.stext.config(yscrollcommand=self.vsb.set)
        self.stext.config(state=DISABLED)
        self.stext['font'] = Entry()['font']
        self.stext.tag_configure('Errors', foreground='red')
        self.stext.tag_configure('Links', foreground='blue', underline=1)
        self.cnt = 0
    
    def setText(self, contents, type=''):
        self.stext.config(state=NORMAL)
        self.stext.delete(1.0, END)
        if type == 'error':
            self.stext.insert(END, contents+'\n', 'Errors')
        elif type == 'link':
            self.stext.insert(END, contents+'\n', ('Links', self.cnt))
            self.stext.tag_bind(self.cnt, '<Any-Enter>', callit(self.linkenter_callback, self.cnt))
            self.stext.tag_bind(self.cnt, '<Any-Leave>', callit(self.linkleave_callback, self.cnt))
            self.stext.tag_bind(self.cnt, '<1>', callit(self.linkclick_callback, self.cnt, contents))
            self.cnt += 1
        else:
            self.stext.insert(END, contents+'\n')
        self.stext.config(state=DISABLED)
        self.stext.see(END)
    
    def addText(self, contents, type=''):
        self.stext.config(state=NORMAL)
        if type == 'error':
            self.stext.insert(END, contents+'\n', 'Errors')
        elif type == 'link':
            self.stext.insert(END, contents+'\n', ('Links', self.cnt))
            self.stext.tag_bind(self.cnt, '<Any-Enter>', callit(self.linkenter_callback, self.cnt))
            self.stext.tag_bind(self.cnt, '<Any-Leave>', callit(self.linkleave_callback, self.cnt))
            self.stext.tag_bind(self.cnt, '<1>', callit(self.linkclick_callback, self.cnt, contents))
            self.cnt += 1
        else:
            self.stext.insert(END, contents+'\n')
        self.stext.config(state=DISABLED)
        self.stext.see(END)
    
    def linkenter_callback(self, tag):
        self.stext.tag_configure(tag, foreground='red')
        self.stext.configure( cursor='hand2')
    
    def linkleave_callback(self, tag):
        self.stext.tag_configure(tag, foreground='blue')
        self.stext.configure( cursor='xterm')
    
    def linkclick_callback(self, tag, url):
        path = str(url)
        if os.path.isfile(path):
            path = os.path.dirname(path)
        elif os.path.isdir(path):
            pass
        else:
            return
        cmd = 'explorer ' + '"' + path + '"'
        subprocess.Popen(cmd, shell=False)
