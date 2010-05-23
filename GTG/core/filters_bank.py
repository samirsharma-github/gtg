# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Gettings Things Gnome! - a personal organizer for the GNOME desktop
# Copyright (c) 2008-2009 - Lionel Dricot & Bertrand Rousseau
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
# 

"""
filters_bank stores all of GTG's filters in centralized place
"""

from GTG.core.task import Task


class Filter:
    def __init__(self,func,req,negate=False):
        self.func = func
        self.dic = {}
        self.req = req
        self.negate = negate

    def set_parameters(self,dic):
        self.dic = dic
    
    def is_displayed(self,tid):
        task = self.req.get_task(tid)
        value = True
        if not task:
            value = False
        elif self.dic:
            value = self.func(task,parameters=self.dic)
        else:
            value = self.func(task)
        if self.negate:
            value = not value
        return value

    #return True is the filter is a flat list only
    def is_flat(self):
        if self.dic.has_key('flat'):
            return self.dic['flat']
        else:
            return False
            
class SimpleTagFilter:
    def __init__(self,tagname,req,negate=False):
        self.req = req
        self.tname = tagname
        self.negate = negate
        
    def is_displayed(self,tid):
        task = self.req.get_task(tid)
        value = True
        if not task:
            value = False
        else:
            tags = [self.tname]
            tags += self.req.get_tag(self.tname).get_children()
            value = task.has_tags(tags)
        if self.negate:
            value = not value
        return value
            
    def is_flat(self):
        return False
    
class FiltersBank:
    """
    Stores filter objects in a centralized place.
    """

    def __init__(self,req,tree=None):
        """
        Create several stock filters:

        workview - Tasks that are active, workable, and started
        active - Tasks of status Active
        closed - Tasks of status closed or dismissed
        notag - Tasks with no tags
        """
        self.tree = tree
        self.req = req
        self.available_filters = {}
        self.custom_filters = {}
        #Workview
        filt_obj = Filter(self.workview,self.req)
        self.available_filters['workview'] = filt_obj
        #Active
        filt_obj = Filter(self.active,self.req)
        self.available_filters['active'] = filt_obj
        #closed
        filt_obj = Filter(self.closed,self.req)
        param = {}
        param['flat'] = True
        filt_obj.set_parameters(param)
        self.available_filters['closed'] = filt_obj
        #notag
        filt_obj = Filter(self.notag,self.req)
        self.available_filters['notag'] = filt_obj
        #workdue
        filt_obj = Filter(self.workdue,self.req)
        self.available_filters['workdue'] = filt_obj
        #workstarted
        filt_obj = Filter(self.workstarted,self.req)
        self.available_filters['workstarted'] = filt_obj
        #worktostart
        filt_obj = Filter(self.worktostart,self.req)
        self.available_filters['worktostart'] = filt_obj
        #worklate
        filt_obj = Filter(self.worklate,self.req)
        self.available_filters['worklate'] = filt_obj

    ######### hardcoded filters #############
    def notag(self,task,parameters=None):
        """ Filter of tasks without tags """
        return task.has_tags(notag_only=True)
        
    def is_leaf(self,task,parameters=None):
        """ Filter of tasks which have no children """
        return not task.has_child()
    
    def is_workable(self,task,parameters=None):
        """ Filter of tasks that can be worked """
        return task.is_workable()
            
    def workview(self,task,parameters=None):
        wv = self.active(task) and\
             task.is_started() and\
             self.is_workable(task)
        return wv
        
    def workdue(self,task):
        ''' Filter for tasks due within the next day '''
        wv = self.workview(task) and \
             task.get_due_date() != no_date and \
             task.get_days_left() < 2
        return wv

    def worklate(self,task):
        ''' Filter for tasks due within the next day '''
        wv = self.workview(task) and \
             task.get_due_date() != no_date and \
             task.get_days_late() > 0
        return wv

    def workstarted(self,task):
        ''' Filter for workable tasks with a start date specified '''
        wv = self.workview(task) and \
             task.start_date
        return wv
        
    def worktostart(self,task):
        ''' Filter for workable tasks without a start date specified '''
        wv = self.workview(task) and \
             not task.start_date
        return wv
        
    def active(self,task,parameters=None):
        """ Filter of tasks which are active """
        #FIXME: we should also handle unactive tags
        return task.get_status() == Task.STA_ACTIVE
        
    def closed(self,task,parameters=None):
        """ Filter of tasks which are closed """
        ret = task.get_status() in [Task.STA_DISMISSED, Task.STA_DONE]
        return ret
        
    ##########################################
        
    def get_filter(self,filter_name):
        """ Get the filter object for a given name """
        if self.available_filters.has_key(filter_name):
            return self.available_filters[filter_name]
        elif self.custom_filters.has_key(filter_name):
            return self.custom_filters[filter_name]
        else:
            return None
    
    def list_filters(self):
        """ List, by name, all available filters """
        liste = self.available_filters.keys()
        liste += self.custom_filters.keys()
        return liste
    
    def add_filter(self,filter_name,filter_func):
        """
        Adds a filter to the filter bank 
        Return True if the filter was added
        Return False if the filter_name was already in the bank
        """
        if filter_name not in self.list_filters():
            negate = False
            if filter_name.startswith('!'):
                negate = True
                filter_name = filter_name[1:]
            if filter_name.startswith('@'):
                filter_obj = SimpleTagFilter(filter_name,self.req,negate=negate)
            else:
                filter_obj = Filter(filter_func,self.req,negate=negate)
            self.custom_filters[filter_name] = filter_obj
            return True
        else:
            return False
        
    def remove_filter(self,filter_name):
        """
        Remove a filter from the bank.
        Only custom filters that were added here can be removed
        Return False if the filter was not removed
        """
        if not self.available_filters.has_key(filter_name):
            if self.custom_filters.has_key(filter_name):
                self.unapply_filter(filter_name)
                self.custom_filters.pop(filter_name)
                return True
            else:
                return False
        else:
            return False
