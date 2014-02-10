# Written by Niels Zeilemaker
# see LICENSE.txt for license information


import sys
from time import time
import logging
from time import sleep
logger = logging.getLogger(__name__)

try:
    import wxversion
    wxversion.select('2.8')
except:
    pass
import wx

ALLOW_MULTIPLE = False

from Tribler.Core.API import *
from Tribler.dispersy.decorator import attach_profiler
from Tribler.SocialMain.vwxGUI.MainFrame import MainFrame
from Tribler.Main.Utility.utility import Utility
from Tribler.Main.vwxGUI.GuiUtility import GUIUtility

class ABCApp():

    def __init__(self, params, single_instance_checker, installdir):
        self._logger = logging.getLogger(self.__class__.__name__)

        self.params = params
        self.single_instance_checker = single_instance_checker
        self.installdir = installdir

        s = self.startAPI()

        self.utility = Utility(self.installdir, s.get_state_dir())
        self.utility.app = self
        self.utility.session = s
        self.guiUtility = GUIUtility.getInstance(self.utility, self.params, self)

        self.frame = MainFrame(s)
        self.frame.SetIcon(wx.Icon(os.path.join(self.installdir, 'Tribler', 'Main', 'vwxGUI', 'images', 'tribler.ico'), wx.BITMAP_TYPE_ICO))
        self.frame.Show(True)
        self.frame.Layout()

    def startAPI(self):
        # Start Tribler Session
        defaultConfig = SessionStartupConfig()
        state_dir = defaultConfig.get_state_dir()
        if not state_dir:
            state_dir = Session.get_default_state_dir()
        cfgfilename = Session.get_default_config_filename(state_dir)

        try:
            self.sconfig = SessionStartupConfig.load(cfgfilename)
        except:
            self.sconfig = SessionStartupConfig()
            self.sconfig.set_state_dir(state_dir)

        self.sconfig.set_install_dir(self.installdir)

        s = Session(self.sconfig)
        s.start()

        def define_communities():
            from Tribler.community.privatesocial.community import SocialCommunity
            # must be called on the Dispersy thread
            dispersy.define_auto_load(SocialCommunity, (s.dispersy_member,), load=True)

        dispersy = s.get_dispersy_instance()
        dispersy.callback.call(define_communities)
        return s

    @staticmethod
    def determine_install_dir():
        # Niels, 2011-03-03: Working dir sometimes set to a browsers working dir
        # only seen on windows

        # apply trick to obtain the executable location
        # see http://www.py2exe.org/index.cgi/WhereAmI
        # Niels, 2012-01-31: py2exe should only apply to windows
        if sys.platform == 'win32':
            def we_are_frozen():
                """Returns whether we are frozen via py2exe.
                This will affect how we find out where we are located."""
                return hasattr(sys, "frozen")

            def module_path():
                """ This will get us the program's directory,
                even if we are frozen using py2exe"""
                if we_are_frozen():
                    return os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))

                filedir = os.path.dirname(unicode(__file__, sys.getfilesystemencoding()))
                return os.path.abspath(os.path.join(filedir, '..', '..'))

            return module_path()
        return os.getcwdu()

    def OnExit(self):
        self._logger.info("main: ONEXIT")
        self.ready = False
        self.done = True

        if self.frame:
            self.frame.Destroy()
            del self.frame

            # Arno, 2012-07-12: Shutdown should be quick
            # Niels, 2013-03-21: However, setting it too low will prevent checkpoints from being written to disk
            waittime = 60
            while not self.utility.session.has_shutdown():
                diff = time() - session_shutdown_start
                if diff > waittime:
                    self._logger.info("main: ONEXIT NOT Waiting for Session to shutdown, took too long")
                    break

                self._logger.info("main: ONEXIT Waiting for Session to shutdown, will wait for an additional %d seconds", waittime - diff)
                sleep(3)
            self._logger.info("main: ONEXIT Session is shutdown")

        Session.del_instance()

        if not ALLOW_MULTIPLE:
            del self.single_instance_checker
        return 0

#
#
# Main Program Start Here
#
#
@attach_profiler
def run(params=None):
    if params is None:
        params = [""]

    if len(sys.argv) > 1:
        params = sys.argv[1:]
    try:
        # Create single instance semaphore
        # Arno: On Linux and wxPython-2.8.1.1 the SingleInstanceChecker appears
        # to mess up stderr, i.e., I get IOErrors when writing to it via print_exc()
        #
        if sys.platform != 'linux2':
            single_instance_checker = wx.SingleInstanceChecker("tribler-" + wx.GetUserId())
        else:
            single_instance_checker = LinuxSingleInstanceChecker("tribler")

        installdir = ABCApp.determine_install_dir()

        if not ALLOW_MULTIPLE and single_instance_checker.IsAnotherRunning():
            statedir = SessionStartupConfig().get_state_dir() or Session.get_default_state_dir()

            # Send  torrent info to abc single instance
            if params[0] != "":
                torrentfilename = params[0]
                i2ic = Instance2InstanceClient(Utility(installdir, statedir).read_config('i2ilistenport'), 'START', torrentfilename)

            logger.info("Client shutting down. Detected another instance.")

        else:
            # Launch first abc single instance
            app = wx.GetApp()
            if not app:
                app = wx.PySimpleApp(redirect=False)

            abc = ABCApp(params, single_instance_checker, installdir)
            if abc.frame:
                app.SetTopWindow(abc.frame)
                abc.frame.set_wxapp(app)
                app.MainLoop()

            # since ABCApp is not a wx.App anymore, we need to call OnExit explicitly.
            abc.OnExit()

            # Niels: No code should be present here, only executed after gui closes

        logger.info("Client shutting down. Sleeping for a few seconds to allow other threads to finish")
        sleep(5)

    except:
        print_exc()

if __name__ == '__main__':
    run()
