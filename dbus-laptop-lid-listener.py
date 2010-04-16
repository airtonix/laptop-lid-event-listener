#!/usr/bin/env python
############################################
## DBUS Laptop Lid Event Listener v0.03
## Zenobius JiriceK, airtonix > ubuntuforums.org
## 
##  A userland dbus event watcher that runs a script when the laptop lid opens and one when it closes.
##  opening and closing scripts are run as the user not root.
## 
## Dependancies : 
##   pynotify, notify-osd, notifcation-daemon
##      sudo apt-get install python-notify notify-osd notification-daemon
##
## Install/Setup : 
##  1) Put this script somewhere sane in your home folder (ie : ~/bin)
##  2) Add it to your session startup application list or script with the following command :
##           ~/bin/dbus-laptop-lid-listener.py listen
##  3) Create a script to run when laptop lid OPENS : 
##       1) gedit ~/bin/laptop-lid-opened.sh
##       2) paste in the following  : 
##           #!/bin/sh
##           notify-osd "lid open"
##       3) make it executable : 
##           chmod +x ~/bin/laptop-lid-opened.sh
##  4) Create a script to run when laptop lid CLOSES : 
##       1) gedit ~/bin/laptop-lid-closed.sh
##       2) paste in the following  : 
##           #!/bin/sh
##           # do stuff.
##       3) make it executable : 
##           chmod +x ~/bin/laptop-lid-closed.sh

import pygtk
pygtk.require('2.0')
import pynotify
import os
import sys
import gtk
import dbus
import gobject
from dbus.mainloop.glib import DBusGMainLoop

class LaptopLid:


	def __init__(self):
		self.notifications = True
		self.name = "DBUS Laptop Lid Event Listener"
		self.dbusObject = {
					"interface" : "org.freedesktop.Hal.Device",
					"path" : ""
				}

		self.acpiLIDstatePath = "/proc/acpi/button/lid/LID0/state"							#this may vary dending on your system
		self.eventScriptsOpen={
			"exists": 0,
			"path": sys.path[0] + "/laptop-lid-opened.sh"
		}
		
		self.eventScriptsClose={
			"exists": 0,
			"path": sys.path[0] + "/laptop-lid-closed.sh"
		}		
		self.strings={
			"NoOpenScript" : {
				"title" : "No Open Script", 
				"body" : "laptop lid opened, you need to specify/create an opening script. See the help text. [dbus-laptop-lid-listener.py help]"
			},
			"NoCloseScript" : {
				"title" : "No Close Script", 
				"body" : "laptop lid closeed, you need to specify/create an closing script. See the help text. [dbus-laptop-lid-listener.py help]"
			},
			"HalObjectFound" : {
				"title" : "Laptop Lid Hal Address",
				"body" : "found laptop switch : "
			},
			"HalObjectNotFound" : {
				"title" : "No laptop lid HAL entry",
				"body" : "Could not find the hal-dbus address of your laptop lid switch."
			}
		}
		self.state=""

		dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
		self.bus = dbus.SystemBus()

		if len(sys.argv) > 1:
			if sys.argv[1] == "test":
				if len(sys.argv)>2 : 
					value = sys.argv[2]
				else:
					value = "Lid Switch"

				print self.findLidSwitchHALaddress(value)

			elif sys.argv[1] == "listen":
				if len(sys.argv)==2:
					if os.path.isfile(self.eventScriptsOpen["path"]) : 
						self.eventScriptsOpen["exists"] = 1
						print "%s : Open Script Found" % self.name

					if os.path.isfile(self.eventScriptsClose["path"]) :
						self.eventScriptsClose["exists"] = 1					
						print "%s : Close Script Found" % self.name
					
				if len(sys.argv)>2 and os.path.isfile(sys.argv[2]):
					self.eventScriptsOpen["path"] = sys.argv[2]

				if len(sys.argv)>3 and os.path.isfile(sys.argv[3]):
					self.eventScriptsClose = sys.argv[3]
						
				self.dbusObject["path"] = self.findLidSwitchHALaddress("Lid Switch")
				self.sniff_start()

			else :
				self.help()

		else :
			self.help()
		
	def sniff_start(self) :
		self.message(gtk.STOCK_DIALOG_INFO,"Listening","waiting for laptop lid events...")
		self.bus.add_signal_receiver(self.cb_func,
																dbus_interface=self.dbusObject['interface'],
																path=self.dbusObject['path'])
		self.loop = gobject.MainLoop()
		try:
		    self.loop.run()

		except KeyboardInterrupt:
			print "%s : usb-device-tracker: keyboad interrupt received, shutting down" % self.name
			self.sniff_stop()
			
	def sniff_stop(self):
		self.loop.quit()
		self.quit()
		
	def cb_func(self, message, sender=None):
		lidStateFile = open(self.acpiLIDstatePath, 'r').read()
		if lidStateFile.count("open") > 0 and (not self.state=="opened") :
			self.state = "opened"
			if self.eventScriptsOpen['exists'] > 0:
				os.system('sh '+self.eventScriptsOpen["path"])
			else:
				self.message(gtk.STOCK_DIALOG_ERROR, self.strings["NoOpenScript"]["title"], self.strings["NoOpenScript"]["body"])

		elif lidStateFile.count("closed") > 0 and (not self.state=="closed") :
			self.state = "closed"
			if self.eventScriptsClose['exists'] > 0:
				os.system('sh '+self.eventScriptsClose["path"])
			else:
				self.message(gtk.STOCK_DIALOG_ERROR, self.strings["NoCloseScript"]["title"], self.strings["NoCloseScript"]["body"] )
	
	def findLidSwitchHALaddress(self,value):
		obj = self.bus.get_object("org.freedesktop.Hal", "/org/freedesktop/Hal/Manager")
		iface = dbus.Interface(obj, "org.freedesktop.Hal.Manager")
		output= iface.FindDeviceStringMatch("info.product", value)
		if len(output) > 0:
			self.message(gtk.STOCK_DIALOG_INFO, self.strings["HalObjectFound"]["title"], self.strings["HalObjectFound"]["body"] +output[0]) 
			return output[0]

		else :
			self.message(gtk.STOCK_DIALOG_ERROR, self.strings["HalObjectNotFound"]["title"], self.strings["HalObjectNotFound"]["body"])
			self.quit()
			
			
	def help(self,keyword=None):
		print self.name 
		print """
Usage: dbus-laptop-lid-listener.py [MODE] [OPENSCRIPT, CLOSESCRIPT]

Runs scripts in response to dbus signals from the laptop lid switch.

Mandatory MODE must be one of :  
 listen\t : what you'd be interested in... sits in memory listening for dbus signals and runs your openScript when the 
\t   acpi laptop lid state changes to "open" and your close script when it changes to "closed"

 test\t : prints out the hal address of your laptop lid switch.

 help\t : This text.
 
 
Optional references to files [OPENSCRIPT, CLOSESCRIPT]
     Any script, terminal commands, etc that can be executed under your users account.
     
     Omitting references to these files will cause the script to look for them in the same directory that the script is located : 
     # <script-location>/laptop-lid-opened.sh
     # <script-location>/laptop-lid-closed.sh
      
"""
		self.quit()

	def message(self, icon, title, message):
		if self.notifications == True and pynotify.init("Images Test") :
			helper = gtk.Button()
			icon = helper.render_icon(icon, gtk.ICON_SIZE_DIALOG)
			bubble = pynotify.Notification(title,message)
			bubble.set_icon_from_pixbuf(icon)
		else:
			self.notifications = False

		if not bubble.show():
			print "%s : Failed to send notification" % self.name

		print "%s : %s << %s >>"  % (self.name, title, message)

	def quit(self):
		sys.exit(0)


###########################
l = LaptopLid()

