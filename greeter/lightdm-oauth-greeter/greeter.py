#!/usr/bin/env python
#
# Author: Joshua Higgins
# Copyright (C) 2015 Joshua Higgins
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.
#
# This code is based on the LightDM Python Greeter which was written by:
# Matt Fischer <matthew.fischer@canonical.com>

# required packages:
# liblightdm-gobject-1-0
# gir1.2-lightdm-1
# python-gobject
# gir1.2-glib-2.0
# python-dbus

import subprocess
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GObject, GLib, LightDM
import sys

class NwGreeterService(dbus.service.Object):

    def __init__(self, loop, greeter):
        self.loop = loop
        self.greeter = greeter
        # state
        self.current_token = ""
        self.current_session = ""
        # set up dbus
        bus_name = dbus.service.BusName('org.kxes.NwGreeter', bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, '/org/kxes/NwGreeter')
        # start up
        self._start_wm()
        self._start_helper()
        # connect signals
        self.greeter.connect("authentication-complete", self._greeter_authentication_complete_cb)
        self.greeter.connect("show-message", self._greeter_show_message_cb)
        self.greeter.connect("show-prompt", self._greeter_show_prompt_cb)
        # connect greeter
        self.greeter.connect_sync()

    @dbus.service.method('org.kxes.NwGreeter')
    def version(self):
        return "NwGreeterService version 0.1"

    @dbus.service.method('org.kxes.NwGreeter')
    def getSessions(self):
        pass

    @dbus.service.method('org.kxes.NwGreeter')
    def doLogin(self, username, token, session):
        self.current_token = token
        self.current_session = session
        # 1. start the authentication
        self.greeter.authenticate(username)
        return self.greeter.get_in_authentication()

    def _start_helper(self):
        self._helper_process = subprocess.Popen(["/opt/lightdm-oauth-greeter/nwjs/nw"])

    def _start_wm(self):
        self._wm_process = subprocess.Popen(['xfwm4'])

    def _greeter_show_prompt_cb(self, greeter, text, promptType):
        # 2. this callback prompts for the password, continue
        self.greeter.respond(self.current_token)

    def _greeter_show_message_cb(self, text, message_type):
        pass

    def _greeter_authentication_complete_cb(self, greeter):
        # 3. this callback is after we send password, check status
        if self.greeter.get_is_authenticated():
            self._helper_process.kill()
            self._wm_process.kill()
            self.greeter.start_session_sync("xfce")

if __name__ == '__main__':
    DBusGMainLoop(set_as_default=True)
    loop = GLib.MainLoop()
    greeter = LightDM.Greeter()
    service = NwGreeterService(loop, greeter)
    loop.run()
