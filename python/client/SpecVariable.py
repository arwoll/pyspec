#  %W%  %G% CSS
#  "pyspec" Release %R%
#
#$Id: SpecVariable.py,v 1.4 2005/03/17 12:43:46 guijarro Exp $

"""SpecVariable module

This module defines the class for Spec variable objects
"""
from SpecConnection import SpecConnection

import SpecEventsDispatcher as SpecEventsDispatcher
import SpecWaitObject as SpecWaitObject

from SpecEventsDispatcher import UPDATEVALUE, FIREEVENT

class SpecVariable(object):
    """SpecVariable class

    Thin wrapper around SpecChannel objects, to make
    variables watching, setting and getting values easier.
    """
    def __init__(self, varname, specapp):
        """Constructor

        Keyword arguments:
        varname -- the variable name in Spec
        specapp -- 'host:port' string representing a Spec server to connect to (defaults to None)
        timeout -- optional timeout (defaults to None)
        """
        self._conn = None

        if varname is not None and specapp is not None:
            self.connectToSpec(varname, specapp)
        else:
            self.chan_name = None

    def connectToSpec(self, varname, specapp):
        """Connect to a remote Spec

        Connect to Spec

        Arguments:
        varname -- the variable name in Spec
        specapp -- 'host:port' string representing a Spec server to connect to
        timeout -- optional timeout (defaults to None)
        """
        if "/" in varname: 
            self.chan_name = str(varname)
        else:
            self.chan_name = 'var/' + str(varname)

        if isinstance(specapp, str):
            self._conn = SpecConnection(specapp)
        else:
            self._conn = specapp

        self._conn.wait_connected()

    def is_connected(self):
        """Return whether the remote Spec version is connected or not."""
        return self._conn is not None and self._conn.is_connected()

    def getValue(self):
        """Return the watched variable current value."""
        if self.is_connected():
            return self._conn.get(self.chan_name)
        return None

    def setValue(self, value):
        """Set the watched variable value

        Arguments:
        value -- the new variable value
        """
        if self.is_connected():
            return self._conn.set(self.chan_name, value)

    def waitUpdate(self, waitValue = None, timeout = None):
        """Wait for the watched variable value to change

        Keyword arguments:
        waitValue -- wait for a specific variable value
        timeout -- optional timeout
        """
        if self.is_connected():
            w = SpecWaitObject.SpecWaitObject(self._conn)
            w.waitChannelUpdate(self.chan_name, waitValue = waitValue, timeout = timeout)
            return w.value

class SpecVariableA(SpecVariable):
    """SpecVariableA class - asynchronous version of SpecVariable

    Thin wrapper around SpecChannel objects, to make
    variables watching, setting and getting values easier.
    """
    def __init__(self, varname = None, specapp = None, dispatchMode = UPDATEVALUE, callbacks={}):
        """Constructor

        Keyword arguments:
        varname -- name of the variable to monitor (defaults to None)
        specapp -- 'host:port' string representing a Spec server to connect to (defaults to None)
        """
        self.__callbacks = {
          'connected': None,
          'disconnected': None,
          'update': None,
        }

        for cb_name in iter(self.__callbacks.keys()):
            if callable(callbacks.get(cb_name)):
               self.__callbacks[cb_name] = SpecEventsDispatcher.callableObjectRef(callbacks[cb_name])

        super(SpecVariableA,self).__init__(varname, specapp)

        self._conn.connect_event('connected', self._connected)
        self._conn.connect_event('disconnected', self._disconnected)

        self.dispatchMode = dispatchMode

        if self._conn.is_connected():
            self._connected()

    def refresh(self):
        self._conn.update()

    def _connected(self):
        #
        # register channel
        #
        self._conn.registerChannel(self.chan_name, self._update, dispatchMode = self.dispatchMode)

        try:
            if self.__callbacks.get("connected"):
                cb = self.__callbacks["connected"]()
                if cb is not None:
                    cb()
        finally:
            self.connected()

    def connected(self):
        """Callback triggered by a 'connected' event from Spec

        To be extended by derivated classes.
        """
        pass

    def _disconnected(self):
        try:
            if self.__callbacks.get("disconnected"):
                cb = self.__callbacks["disconnected"]()
                if cb is not None:
                    cb()
        finally:
            self.disconnected()

    def disconnected(self):
        """Callback triggered by a 'disconnected' event from Spec

        To be extended by derivated classes.
        """
        pass

    def _update(self, value):
        try:
            if self.__callbacks.get("update"):
                cb = self.__callbacks["update"]()
                if cb is not None:
                    cb(value)
        finally:
            self.update(value)

    def update(self, value):
        """Callback triggered by a variable update

        Extend it to do something useful.
        """
        pass

