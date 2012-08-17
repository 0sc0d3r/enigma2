
from enigma import eListboxPythonMultiContent, gFont, eEnv

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Network import iNetwork
from Components.NimManager import nimmanager

from Screens.Screen import Screen
from Screens.NetworkSetup import *
from Screens.About import SystemInfo
from Screens.PluginBrowser import PluginDownloadBrowser, PluginFilter, PluginBrowser
from Screens.LanguageSelection import LanguageSelection
from Screens.Satconfig import NimSelection
from Screens.ScanSetup import ScanSimple, ScanSetup
from Screens.Setup import Setup, getSetupTitle
from Screens.HarddiskSetup import HarddiskSelection, HarddiskFsckSelection, HarddiskConvertExt4Selection

from Plugins.Plugin import PluginDescriptor
from Plugins.SystemPlugins.PositionerSetup.plugin import PositionerSetup, RotorNimSelection
from Plugins.SystemPlugins.Satfinder.plugin import Satfinder, SatNimSelection
from Plugins.SystemPlugins.NetworkBrowser.MountManager import AutoMountManager
from Plugins.SystemPlugins.NetworkBrowser.NetworkBrowser import NetworkBrowser
from Plugins.SystemPlugins.NetworkWizard.NetworkWizard import NetworkWizard
from Plugins.SystemPlugins.Videomode.plugin import VideoSetup
from Plugins.SystemPlugins.Videomode.VideoHardware import video_hw
from Plugins.SystemPlugins.VideoEnhancement.plugin import VideoEnhancementSetup
from Plugins.Extensions.Aafpanel.RestartNetwork import RestartNetwork
from Plugins.Extensions.Aafpanel.MountManager import HddMount
from Plugins.Extensions.Aafpanel.SoftcamPanel import *
from Plugins.SystemPlugins.SoftwareManager.ImageBackup import ImageBackup
from Plugins.SystemPlugins.SoftwareManager.plugin import UpdatePlugin
from Plugins.SystemPlugins.SoftwareManager.BackupRestore import BackupScreen, RestoreScreen, BackupSelection, getBackupPath, getBackupFilename

from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE, SCOPE_SKIN
from Tools.LoadPixmap import LoadPixmap

from os import path
from time import sleep
from re import search
import NavigationInstance

plugin_path_networkbrowser = eEnv.resolve("${libdir}/enigma2/python/Plugins/SystemPlugins/NetworkBrowser")

if path.exists("/usr/lib/enigma2/python/Plugins/Extensions/AudioSync"):
	from Plugins.Extensions.AudioSync.AC3setup import AC3LipSyncSetup
	plugin_path_audiosync = eEnv.resolve("${libdir}/enigma2/python/Plugins/Extensions/AudioSync")
	AUDIOSYNC = True
else:
	AUDIOSYNC = False

def isFileSystemSupported(filesystem):
	try:
		for fs in open('/proc/filesystems', 'r'):
			if fs.strip().endswith(filesystem):
				return True
		return False
	except Exception, ex:
		print "[Harddisk] Failed to read /proc/filesystems:", ex

class QuickMenu(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		Screen.setTitle(self, _("Quick Launch Menu"))

		self["key_red"] = Label(_("Exit"))
		self["key_green"] = Label(_("System Info"))
		self["key_yellow"] = Label(_("Devices"))
		self["key_blue"] = Label()
		self["description"] = Label()

		self.menu = 0
		self.list = []
		self["list"] = QuickMenuList(self.list)
		self.sublist = []
		self["sublist"] = QuickMenuSubList(self.sublist)
		self.selectedList = []
		self.onChangedEntry = []
		self["list"].onSelectionChanged.append(self.selectionChanged)
		self["sublist"].onSelectionChanged.append(self.selectionSubChanged)

		self["actions"] = ActionMap(["SetupActions","WizardActions","MenuActions","MoviePlayerActions"],
		{
			"ok": self.ok,
			"back": self.keyred,
			"cancel": self.keyred,
			"left": self.goLeft,
			"right": self.goRight,
			"up": self.goUp,
			"down": self.goDown,
		}, -1)


		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
			{
			"red": self.keyred,
			"green": self.keygreen,
			"yellow": self.keyyellow,
			})

		self.MainQmenu()
		self.selectedList = self["list"]
		self.selectionChanged()
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self["sublist"].selectionEnabled(0)

	def selectionChanged(self):
		if self.selectedList == self["list"]:
			item = self["list"].getCurrent()
			if item:
				self["description"].setText(_(item[4]))
				self.okList()

	def selectionSubChanged(self):
		if self.selectedList == self["sublist"]:
			item = self["sublist"].getCurrent()
			if item:
				self["description"].setText(_(item[3]))

	def goLeft(self):
		if self.menu <> 0:
			self.menu = 0
			self.selectedList = self["list"]
			self["list"].selectionEnabled(1)
			self["sublist"].selectionEnabled(0)
			self.selectionChanged()

	def goRight(self):
		if self.menu == 0:
			self.menu = 1
			self.selectedList = self["sublist"]
			self["sublist"].moveToIndex(0)
			self["sublist"].selectionEnabled(1)
			self.selectionSubChanged()

	def goUp(self):
		self.selectedList.up()
		
	def goDown(self):
		self.selectedList.down()
		
	def keyred(self):
		self.close()

	def keygreen(self):
		self.session.open(SystemInfo)

	def keyyellow(self):
		self.session.open(QuickMenuDevices)

######## Main Menu ##############################
	def MainQmenu(self):
		self.menu = 0
		self.list = []
		self.oldlist = []
		self.list.append(QuickMenuEntryComponent("Network","Setup your local network","Setup your local network. For Wlan you need to boot with a USB-Wlan stick"))
		self.list.append(QuickMenuEntryComponent("Mounts","Mount Setup","Setup your mounts for network"))
		self.list.append(QuickMenuEntryComponent("AV Setup","Setup Videomode","Setup your Video Mode, Video Output and other Video Settings"))
		self.list.append(QuickMenuEntryComponent("Tuner Setup","Setup Tuner","Setup your Tuner and search for channels"))
		self.list.append(QuickMenuEntryComponent("Softcam","Start/stop/select cam","Start/stop/select your cam, You need to install first a softcam"))
		self.list.append(QuickMenuEntryComponent("Software Manager","Update/Backup/Restore your box","Update/Backup your firmware, Backup/Restore settings"))
		self.list.append(QuickMenuEntryComponent("Plugins","Download plugins","Shows available pluigns. Here you can download and install them"))
		self.list.append(QuickMenuEntryComponent("Harddisk","Harddisk Setup","Setup your Harddisk"))
		self["list"].l.setList(self.list)

######## Network Menu ##############################
	def Qnetwork(self):
		self.sublist = []
		self.sublist.append(QuickSubMenuEntryComponent("Network Wizard","Configure your Network","Use the Networkwizard to configure your Network. The wizard will help you to setup your network"))
		if len(self.adapters) > 1: # show only adapter selection if more as 1 adapter is installed
			self.sublist.append(QuickSubMenuEntryComponent("Network Adapter Selection","Select Lan/Wlan","Setup your network interface. If no Wlan stick is used, you only can select Lan"))
		if not self.activeInterface == None: # show only if there is already a adapter up
			self.sublist.append(QuickSubMenuEntryComponent("Network Interface","Setup interface","Setup network. Here you can setup DHCP, IP, DNS"))
		self.sublist.append(QuickSubMenuEntryComponent("Network Restart","Restart network to with current setup","Restart network and remount connections"))
		self.sublist.append(QuickSubMenuEntryComponent("Network Services","Setup Network Services","Setup Network Services (Samba, Ftp, NFS, ...)"))
		self["sublist"].l.setList(self.sublist)

#### Network Services Menu ##############################
	def Qnetworkservices(self):
		self.sublist = []
		self.sublist.append(QuickSubMenuEntryComponent("Samba","Setup Samba","Setup Samba"))
		self.sublist.append(QuickSubMenuEntryComponent("NFS","Setup NFS","Setup NFS"))
		self.sublist.append(QuickSubMenuEntryComponent("FTP","Setup FTP","Setup FTP"))
		self.sublist.append(QuickSubMenuEntryComponent("AFP","Setup AFP","Setup AFP"))
		self.sublist.append(QuickSubMenuEntryComponent("OpenVPN","Setup OpenVPN","Setup OpenVPN"))
		self.sublist.append(QuickSubMenuEntryComponent("MiniDLNA","Setup MiniDLNA","Setup MiniDLNA"))
		self.sublist.append(QuickSubMenuEntryComponent("Inadyn","Setup Inadyn","Setup Inadyn"))
		self.sublist.append(QuickSubMenuEntryComponent("SABnzbd","Setup SABnzbd","Setup SABnzbd"))
		self.sublist.append(QuickSubMenuEntryComponent("uShare","Setup uShare","Setup uShare"))
		self.sublist.append(QuickSubMenuEntryComponent("Telnet","Setup Telnet","Setup Telnet"))
		self["sublist"].l.setList(self.sublist)

######## Mount Settings Menu ##############################
	def Qmount(self):
		self.sublist = []
		self.sublist.append(QuickSubMenuEntryComponent("Mount Manager","Manage network mounts","Setup your network mounts"))
		self.sublist.append(QuickSubMenuEntryComponent("Network Browser","Search for network shares","Search for network shares"))
		self.sublist.append(QuickSubMenuEntryComponent("Device Manager","Mounts Devices","Setup your Device mounts (USB, HDD, others...)"))
		self["sublist"].l.setList(self.sublist)

######## Softcam Menu ##############################
	def Qsoftcam(self):
		self.sublist = []
		if Check_Softcam(): # show only when there is a softcam installed
			self.sublist.append(QuickSubMenuEntryComponent("Softcam Panel","Control your Softcams","Use the Softcam Panel to control your Cam. This let you start/stop/select a cam"))
		self.sublist.append(QuickSubMenuEntryComponent("Download Softcams","Download and install cam","Shows available softcams. Here you can download and install them"))
		self["sublist"].l.setList(self.sublist)

######## A/V Settings Menu ##############################
	def Qavsetup(self):
		self.sublist = []
		self.sublist.append(QuickSubMenuEntryComponent("AV Settings","Setup Videomode","Setup your Video Mode, Video Output and other Video Settings"))
		if AUDIOSYNC == True:
			self.sublist.append(QuickSubMenuEntryComponent("Audio Sync","Setup Audio Sync","Setup Audio Sync settings"))
		self.sublist.append(QuickSubMenuEntryComponent("Auto Language","Auto Language Selection","Select your Language for Audio/Subtitles"))
		self.sublist.append(QuickSubMenuEntryComponent("VideoEnhancement","VideoEnhancement Setup","VideoEnhancement Setup"))
		self["sublist"].l.setList(self.sublist)

######## Tuner Menu ##############################
	def Qtuner(self):
		self.sublist = []
		self.sublist.append(QuickSubMenuEntryComponent("Tuner Configuration","Setup tuner(s)","Setup each tuner for your satellite system"))
		self.sublist.append(QuickSubMenuEntryComponent("Positioner Setup","Setup rotor","Setup your positioner for your satellite system"))
		self.sublist.append(QuickSubMenuEntryComponent("Automatic Scan","Service Searching","Automatic scan for services"))
		self.sublist.append(QuickSubMenuEntryComponent("Manual Scan","Service Searching","Manual scan for services"))
		self.sublist.append(QuickSubMenuEntryComponent("Sat Finder","Search Sats","Search Sats, check signal and lock"))
		self["sublist"].l.setList(self.sublist)

######## Software Manager Menu ##############################
	def Qsoftware(self):
		self.sublist = []
		self.sublist.append(QuickSubMenuEntryComponent("Software Update","Online software update","Check/Install online updates (you must have a working internet connection)"))
		self.sublist.append(QuickSubMenuEntryComponent("Complete Backup","Backup your current image","Backup your current image to HDD or USB. This will make a 1:1 copy of your box"))
		self.sublist.append(QuickSubMenuEntryComponent("Backup Settings","Backup your current settings","Backup your current settings. This includes E2-setup, channels, network and all selected files"))
		self.sublist.append(QuickSubMenuEntryComponent("Restore Settings","Restore settings from a backup","Restore your settings back from a backup. After restore the box will restart to activated the new settings"))
		self.sublist.append(QuickSubMenuEntryComponent("Select Backup files","Choose the files to backup","Here you can select which files should be added to backupfile. (default: E2-setup, channels, network"))
		self["sublist"].l.setList(self.sublist)

######## Plugins Menu ##############################
	def Qplugin(self):
		self.sublist = []
		self.sublist.append(QuickSubMenuEntryComponent("Plugin Browser","Open the Plugin Browser","Shows Plugins Browser. Here you can setup installed Plugin"))
		self.sublist.append(QuickSubMenuEntryComponent("Download Plugins","Download and install Plugins","Shows available plugins. Here you can download and install them"))
		self.sublist.append(QuickSubMenuEntryComponent("Remove Plugins","Delete Plugins","Delete and unstall Plugins. This will remove the Plugin from your box"))
		self.sublist.append(QuickSubMenuEntryComponent("Plugin Filter","Setup Plugin filter","Setup Plugin filter. Here you can select which Plugins are showed in the PluginBrowser"))
		self.sublist.append(QuickSubMenuEntryComponent("IPK Installer","Install local extension","Scan for local extensions and install them"))
		self["sublist"].l.setList(self.sublist)

######## Harddisk Menu ##############################
	def Qharddisk(self):
		self.sublist = []
		self.sublist.append(QuickSubMenuEntryComponent("Harddisk Setup","Harddisk Setup","Setup your Harddisk"))
		self.sublist.append(QuickSubMenuEntryComponent("Initialization","Format HDD","Format your Harddisk"))
		self.sublist.append(QuickSubMenuEntryComponent("Filesystem Check","Check HDD","Filesystem check your Harddisk"))
		if isFileSystemSupported("ext4"):
			self.sublist.append(QuickSubMenuEntryComponent("Convert ext3 to ext4","Convert filesystem ext3 to ext4","Convert filesystem ext3 to ext4"))
		self["sublist"].l.setList(self.sublist)

	def ok(self):
		if self.menu > 0:
			self.okSubList()
		else:
			self.okList()


#####################################################################
######## Make Selection MAIN MENU LIST ##############################
#####################################################################
			
	def okList(self):
		item = self["list"].getCurrent()

######## Select Network Menu ##############################
		if item[0] == _("Network"):
			self.GetNetworkInterfaces()
			self.Qnetwork()
######## Select Mount Menu ##############################
		elif item[0] == _("Mounts"):
			self.Qmount()
######## Select Softcam Menu ##############################
		elif item[0] == _("Softcam"):
			self.Qsoftcam()
######## Select AV Setup Menu ##############################
		elif item[0] == _("AV Setup"):
			self.Qavsetup()
######## Select Tuner Setup Menu ##############################
		elif item[0] == _("Tuner Setup"):
			self.Qtuner()
######## Select Software Manager Menu ##############################
		elif item[0] == _("Software Manager"):
			self.Qsoftware()
######## Select PluginDownloadBrowser Menu ##############################
		elif item[0] == _("Plugins"):
			self.Qplugin()
######## Select Tuner Setup Menu ##############################
		elif item[0] == _("Harddisk"):
			self.Qharddisk()

		self["sublist"].selectionEnabled(0)

#####################################################################
######## Make Selection SUB MENU LIST ##############################
#####################################################################
			
	def okSubList(self):
		item = self["sublist"].getCurrent()

######## Select Network Menu ##############################
		if item[0] == _("Network Wizard"):
			self.session.open(NetworkWizard)
		elif item[0] == _("Network Adapter Selection"):
			self.session.open(NetworkAdapterSelection)
		elif item[0] == _("Network Interface"):
			self.session.open(AdapterSetup,self.activeInterface)
		elif item[0] == _("Network Restart"):
			self.session.open(RestartNetwork)
		elif item[0] == _("Network Services"):
			self.Qnetworkservices()
			self["sublist"].moveToIndex(0)
		elif item[0] == _("Samba"):
			self.session.open(NetworkSamba)
		elif item[0] == _("NFS"):
			self.session.open(NetworkNfs)
		elif item[0] == _("FTP"):
			self.session.open(NetworkFtp)
		elif item[0] == _("AFP"):
			self.session.open(NetworkAfp)
		elif item[0] == _("OpenVPN"):
			self.session.open(NetworkOpenvpn)
		elif item[0] == _("MiniDLNA"):
			self.session.open(NetworkMiniDLNA)
		elif item[0] == _("Inadyn"):
			self.session.open(NetworkInadyn)
		elif item[0] == _("SABnzbd"):
			self.session.open(NetworkSABnzbd)
		elif item[0] == _("uShare"):
			self.session.open(NetworkuShare)
		elif item[0] == _("Telnet"):
			self.session.open(NetworkTelnet)
######## Select Mounts Menu ##############################
		elif item[0] == _("Mount Manager"):
			self.session.open(AutoMountManager, None, plugin_path_networkbrowser)
		elif item[0] == _("Network Browser"):
			self.session.open(NetworkBrowser, None, plugin_path_networkbrowser)
		elif item[0] == _("Device Manager"):
			self.session.open(HddMount)
######## Select Softcam Menu ##############################
		elif item[0] == _("Softcam Panel"):
			self.session.open(SoftcamPanel)
		elif item[0] == _("Download Softcams"):
			self.session.open(ShowSoftcamPackages)
######## Select AV Setup Menu ##############################
		elif item[0] == _("AV Settings"):
			self.session.open(VideoSetup, video_hw)
		elif item[0] == _("Auto Language"):
			self.openSetup("autolanguagesetup")
		elif item[0] == _("Audio Sync"):
			self.session.open(AC3LipSyncSetup, plugin_path_audiosync)
		elif item[0] == _("VideoEnhancement"):
			self.session.open(VideoEnhancementSetup)
######## Select TUNER Setup Menu ##############################
		elif item[0] == _("Tuner Configuration"):
			self.session.open(NimSelection)
		elif item[0] == _("Positioner Setup"):
			self.PositionerMain()
		elif item[0] == _("Automatic Scan"):
			self.session.open(ScanSimple)
		elif item[0] == _("Manual Scan"):
			self.session.open(ScanSetup)
		elif item[0] == _("Sat Finder"):
			self.SatfinderMain()
######## Select Software Manager Menu ##############################
		elif item[0] == _("Software Update"):
			self.session.open(UpdatePlugin)
		elif item[0] == _("Complete Backup"):
			self.session.open(ImageBackup)
		elif item[0] == _("Backup Settings"):
			self.session.openWithCallback(self.backupDone,BackupScreen, runBackup = True)
		elif item[0] == _("Restore Settings"):
			self.backuppath = getBackupPath()
			self.backupfile = getBackupFilename()
			self.fullbackupfilename = self.backuppath + "/" + self.backupfile
			if os_path.exists(self.fullbackupfilename):
				self.session.openWithCallback(self.startRestore, MessageBox, _("Are you sure you want to restore your STB_BOX backup?\nSTB will restart after the restore"))
			else:
				self.session.open(MessageBox, _("Sorry no backups found!"), MessageBox.TYPE_INFO, timeout = 10)
		elif item[0] == _("Select Backup files"):
			self.session.openWithCallback(self.backupfiles_choosen,BackupSelection)
######## Select PluginDownloadBrowser Menu ##############################
		elif item[0] == _("Plugin Browser"):
			self.session.open(PluginBrowser)
		elif item[0] == _("Download Plugins"):
			self.session.open(PluginDownloadBrowser, 0)
		elif item[0] == _("Remove Plugins"):
			self.session.open(PluginDownloadBrowser, 1)
		elif item[0] == _("Plugin Filter"):
			self.session.open(PluginFilter)
		elif item[0] == _("IPK Installer"):
			try:
				from Plugins.Extensions.MediaScanner.plugin import main
				main(self.session)
			except:
				self.session.open(MessageBox, _("Sorry MediaScanner is not installed!"), MessageBox.TYPE_INFO, timeout = 10)
######## Select Harddisk Menu ############################################
		elif item[0] == _("Harddisk Setup"):
			self.openSetup("harddisk")
		elif item[0] == _("Initialization"):
			self.session.open(HarddiskSelection)
		elif item[0] == _("Filesystem Check"):
			self.session.open(HarddiskFsckSelection)
		elif item[0] == _("Convert ext3 to ext4"):
			self.session.open(HarddiskConvertExt4Selection)

######## OPEN SETUP MENUS ####################
	def openSetup(self, dialog):
		self.session.openWithCallback(self.menuClosed, Setup, dialog)

	def menuClosed(self, *res):
		pass

######## NETWORK TOOLS #######################
	def GetNetworkInterfaces(self):
		self.adapters = [(iNetwork.getFriendlyAdapterName(x),x) for x in iNetwork.getAdapterList()]

		if not self.adapters:
			self.adapters = [(iNetwork.getFriendlyAdapterName(x),x) for x in iNetwork.getConfiguredAdapters()]

		if len(self.adapters) == 0:
			self.adapters = [(iNetwork.getFriendlyAdapterName(x),x) for x in iNetwork.getInstalledAdapters()]

		self.activeInterface = None
	
		for x in self.adapters:
			if iNetwork.getAdapterAttribute(x[1], 'up') is True:
				self.activeInterface = x[1]
				return

######## TUNER TOOLS #######################
	def PositionerMain(self):
		nimList = nimmanager.getNimListOfType("DVB-S")
		if len(nimList) == 0:
			self.session.open(MessageBox, _("No positioner capable frontend found."), MessageBox.TYPE_ERROR)
		else:
			if len(NavigationInstance.instance.getRecordings()) > 0:
				self.session.open(MessageBox, _("A recording is currently running. Please stop the recording before trying to configure the positioner."), MessageBox.TYPE_ERROR)
			else:
				usableNims = []
				for x in nimList:
					configured_rotor_sats = nimmanager.getRotorSatListForNim(x)
					if len(configured_rotor_sats) != 0:
						usableNims.append(x)
				if len(usableNims) == 1:
					self.session.open(PositionerSetup, usableNims[0])
				elif len(usableNims) > 1:
					self.session.open(RotorNimSelection)
				else:
					self.session.open(MessageBox, _("No tuner is configured for use with a diseqc positioner!"), MessageBox.TYPE_ERROR)

	def SatfinderMain(self):
		nims = nimmanager.getNimListOfType("DVB-S")

		nimList = []
		for x in nims:
			if not nimmanager.getNimConfig(x).configMode.value in ("loopthrough", "satposdepends", "nothing"):
				nimList.append(x)

		if len(nimList) == 0:
			self.session.open(MessageBox, _("No satellite frontend found!!"), MessageBox.TYPE_ERROR)
		else:
			if len(NavigationInstance.instance.getRecordings()) > 0:
				self.session.open(MessageBox, _("A recording is currently running. Please stop the recording before trying to start the satfinder."), MessageBox.TYPE_ERROR)
			else:
				if len(nimList) == 1:
					self.session.open(Satfinder, nimList[0])
				else:
					self.session.open(SatNimSelection)

		
######## SOFTWARE MANAGER TOOLS #######################
	def backupfiles_choosen(self, ret):
		config.plugins.configurationbackup.backupdirs.save()
		config.plugins.configurationbackup.save()
		config.save()

	def backupDone(self,retval = None):
		if retval is True:
			self.session.open(MessageBox, _("Backup done."), MessageBox.TYPE_INFO, timeout = 10)
		else:
			self.session.open(MessageBox, _("Backup failed."), MessageBox.TYPE_INFO, timeout = 10)

	def startRestore(self, ret = False):
		if (ret == True):
			self.exe = True
			self.session.open(RestoreScreen, runRestore = True)


######## Create MENULIST format #######################
def QuickMenuEntryComponent(name, description, long_description = None, width=540):
	pngname = name.replace(" ","_") 
	png = LoadPixmap("/usr/lib/enigma2/python/Plugins/Extensions/Aafpanel/icons/" + pngname + ".png")
	if png is None:
		png = LoadPixmap("/usr/lib/enigma2/python/Plugins/Extensions/Aafpanel/icons/default.png")

	return [
		_(name),
		MultiContentEntryText(pos=(120, 5), size=(width-120, 25), font=0, text = _(name)),
		MultiContentEntryText(pos=(120, 26), size=(width-120, 17), font=1, text = _(description)),
		MultiContentEntryPixmapAlphaTest(pos=(10, 5), size=(100, 40), png = png),
		_(long_description),
	]

def QuickSubMenuEntryComponent(name, description, long_description = None, width=540):
	return [
		_(name),
		MultiContentEntryText(pos=(10, 5), size=(width-10, 25), font=0, text = _(name)),
		MultiContentEntryText(pos=(10, 26), size=(width-10, 17), font=1, text = _(description)),
		_(long_description),
	]

class QuickMenuList(MenuList):
	def __init__(self, list, enableWrapAround=True):
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setFont(1, gFont("Regular", 14))
		self.l.setItemHeight(50)

class QuickMenuSubList(MenuList):
	def __init__(self, sublist, enableWrapAround=True):
		MenuList.__init__(self, sublist, enableWrapAround, eListboxPythonMultiContent)
		self.l.setFont(0, gFont("Regular", 20))
		self.l.setFont(1, gFont("Regular", 14))
		self.l.setItemHeight(50)

class QuickMenuDevices(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		Screen.setTitle(self, _("Devices"))
		self['lab1'] = Label()
		self.devicelist = []
		self['devicelist'] = List(self.devicelist)

		self['actions'] = ActionMap(['WizardActions'], 
		{
			'back': self.close,
		})
		self.activityTimer = eTimer()
		self.activityTimer.timeout.get().append(self.updateList2)
		self.updateList()

	def updateList(self, result = None, retval = None, extra_args = None):
		scanning = _("Wait please while scanning for devices...")
		self['lab1'].setText(scanning)
		self.activityTimer.start(10)

	def updateList2(self):
		self.activityTimer.stop()
		self.devicelist = []
		list2 = []
		f = open('/proc/partitions', 'r')
		for line in f.readlines():
			parts = line.strip().split()
			if not parts:
				continue
			device = parts[3]
			if not search('sd[a-z][1-9]',device):
				continue
			if device in list2:
				continue
			self.buildMy_rec(device)
			list2.append(device)

		f.close()
		self['devicelist'].list = self.devicelist
		if len(self.devicelist) == 0:
			self['lab1'].setText(_("No Devices Found !!"))
		else:
			self['lab1'].hide()

	def buildMy_rec(self, device):
		try:
			if device.find('1') > 0:
				device2 = device.replace('1', '')
		except:
			device2 = ''
		try:
			if device.find('2') > 0:
				device2 = device.replace('2', '')
		except:
			device2 = ''
		try:
			if device.find('3') > 0:
				device2 = device.replace('3', '')
		except:
			device2 = ''
		try:
			if device.find('4') > 0:
				device2 = device.replace('4', '')
		except:
			device2 = ''
		devicetype = path.realpath('/sys/block/' + device2 + '/device')
		d2 = device
		name = 'USB: '
		mypixmap = '/usr/lib/enigma2/python/Plugins/Extensions/Aafpanel/icons/dev_usbstick.png'
		model = file('/sys/block/' + device2 + '/device/model').read()
		model = str(model).replace('\n', '')
		des = ''
		if devicetype.find('/devices/pci') != -1:
			name = _("HARD DISK: ")
			mypixmap = '/usr/lib/enigma2/python/Plugins/Extensions/Aafpanel/icons/dev_hdd.png'
		name = name + model

		from Components.Console import Console
		self.Console = Console()
		self.Console.ePopen("sfdisk -l /dev/sd? | grep swap | awk '{print $(NF-9)}' >/tmp/devices.tmp")
		sleep(0.5)
		f = open('/tmp/devices.tmp', 'r')
		swapdevices = f.read()
		f.close()
		swapdevices = swapdevices.replace('\n','')
		swapdevices = swapdevices.split('/')
		f = open('/proc/mounts', 'r')
		for line in f.readlines():
			if line.find(device) != -1:
				parts = line.strip().split()
				d1 = parts[1]
				dtype = parts[2]
				rw = parts[3]
				break
				continue
			else:
				if device in swapdevices:
					parts = line.strip().split()
					d1 = _("None")
					dtype = 'swap'
					rw = _("None")
					break
					continue
				else:
					d1 = _("None")
					dtype = _("unavailable")
					rw = _("None")
		f.close()
		f = open('/proc/partitions', 'r')
		for line in f.readlines():
			if line.find(device) != -1:
				parts = line.strip().split()
				size = int(parts[2])
				if ((size / 1024) / 1024) > 1:
					des = _("Size: ") + str((size / 1024) / 1024) + _("GB")
				else:
					des = _("Size: ") + str(size / 1024) + _("MB")
			else:
				try:
					size = file('/sys/block/' + device2 + '/' + device + '/size').read()
					size = str(size).replace('\n', '')
					size = int(size)
				except:
					size = 0
				if (((size / 2) / 1024) / 1024) > 1:
					des = _("Size: ") + str(((size / 2) / 1024) / 1024) + _("GB")
				else:
					des = _("Size: ") + str((size / 2) / 1024) + _("MB")
		f.close()
		if des != '':
			if rw.startswith('rw'):
				rw = ' R/W'
			elif rw.startswith('ro'):
				rw = ' R/O'
			else:
				rw = ""
			des += '\t' + _("Mount: ") + d1 + '\n' + _("Device: ") + ' /dev/' + device + '\t' + _("Type: ") + dtype + rw
			png = LoadPixmap(mypixmap)
			res = (name, des, png)
			self.devicelist.append(res)

