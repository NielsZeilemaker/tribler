import logging
import sys

from threading import enumerate
from Tribler.Main.vwxGUI.TopSearchPanel import TopSearchPanelStub
from Tribler.Main.vwxGUI.list_header import TitleHeader
from Tribler.Main.vwxGUI.SRstatusbar import SRstatusbar
try:
    import wxversion
    wxversion.select('2.8')

except:
    pass
import wx

from Tribler.SocialMain.vwxGUI.list import FriendList, WallList
from Tribler.Main.vwxGUI.GuiUtility import GUIUtility
from Tribler.Main.vwxGUI import DEFAULT_BACKGROUND, forceWxThread, \
    SEPARATOR_GREY

class MainFrame(wx.Frame):

    def __init__(self, session):
        self._logger = logging.getLogger(self.__class__.__name__)

        print >> sys.stderr, 'GUI started'

        self.ready = False
        self.quitting = False
        self.wxapp = None

        self.guiUtility = GUIUtility.getInstance()
        self.guiUtility.frame = self

        # Get window size and (sash) position from config file
        primarydisplay = wx.Display(0)
        dsize = primarydisplay.GetClientArea()
        position = dsize.GetTopLeft()
        size = wx.Size(1024, 670)
        style = wx.DEFAULT_DIALOG_STYLE | wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX | wx.RESIZE_BORDER | wx.NO_FULL_REPAINT_ON_RESIZE | wx.CLIP_CHILDREN
        wx.Frame.__init__(self, None, wx.ID_ANY, 'OnePage', position, size, style)

        if sys.platform == 'linux2':
            font = self.GetFont()
            if font.GetPointSize() > 9:
                font.SetPointSize(9)
                self.SetFont(font)

        self.Freeze()
        self.SetDoubleBuffered(True)
        self.SetBackgroundColour(DEFAULT_BACKGROUND)

        themeColour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
        r, g, b = themeColour.Get(False)
        if r > 190 or g > 190 or b > 190:  # Grey == 190,190,190
            self.SetForegroundColour(wx.BLACK)

        # Create all components
        friendtitle = TitleHeader(self, None, [], 0, radius=0, spacers=[10, 10])
        friendtitle.SetTitle('Your Friends')
        friendtitle.SetBackgroundColour(DEFAULT_BACKGROUND)

        walltitle = TitleHeader(self, None, [], 0, radius=0, spacers=[10, 10])
        walltitle.SetTitle('Recent activity from your friends')
        walltitle.SetBackgroundColour(DEFAULT_BACKGROUND)

        self.friendlist = FriendList(self)
        self.actlist = WallList(self, None)
        self.top_bg = TopSearchPanelStub()

        self.friendlist.SetMinSize((200, -1))

        sizer = wx.FlexGridSizer(3, 3, 0, 0)
        sizer.SetFlexibleDirection(wx.BOTH)
        sizer.AddGrowableRow(2)
        sizer.AddGrowableCol(2)
        sizer.Add(friendtitle)
        separator = wx.Panel(self, size=(1, -1))
        separator.SetBackgroundColour(SEPARATOR_GREY)
        sizer.Add(separator)
        sizer.Add(walltitle)

        separator = wx.Panel(self, size=(-1, 1))
        separator.SetBackgroundColour(SEPARATOR_GREY)
        sizer.Add(separator, 0, wx.EXPAND)
        separator = wx.Panel(self, size=(1, 1))
        separator.SetBackgroundColour(SEPARATOR_GREY)
        sizer.Add(separator)
        separator = wx.Panel(self, size=(-1, 1))
        separator.SetBackgroundColour(SEPARATOR_GREY)
        sizer.Add(separator, 0, wx.EXPAND)

        sizer.Add(self.friendlist)
        separator = wx.Panel(self, size=(1, -1))
        separator.SetBackgroundColour(SEPARATOR_GREY)
        sizer.Add(separator, 0, wx.EXPAND)
        sizer.Add(self.actlist, 1, wx.EXPAND)
        self.SetSizer(sizer)

        manager = self.actlist.GetManager()
        manager.refresh()

        self.SRstatusbar = SRstatusbar(self, show_ff=False)
        self.SRstatusbar.SetConnections(1.0, 20, 20)
        self.SRstatusbar.onReachable()
        self.SetStatusBar(self.SRstatusbar)

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.Bind(wx.EVT_QUERY_END_SESSION, self.OnCloseWindow)
        self.Bind(wx.EVT_END_SESSION, self.OnCloseWindow)

        print >> sys.stderr, 'GUI ready'
        self.Thaw()
        self.ready = True

    def set_wxapp(self, wxapp):
        self.wxapp = wxapp

    def OnCloseWindow(self, event=None, force=False):
        if event != None:
            nr = event.GetEventType()
            lookup = {wx.EVT_CLOSE.evtType[0]: "EVT_CLOSE", wx.EVT_QUERY_END_SESSION.evtType[0]: "EVT_QUERY_END_SESSION", wx.EVT_END_SESSION.evtType[0]: "EVT_END_SESSION"}
            if nr in lookup:
                nr = lookup[nr]
            self._logger.info("mainframe: Closing due to event %s %s", nr, repr(event))
        else:
            self._logger.info("mainframe: Closing untriggered by event")

        if not self.quitting:
            self.quitting = True
            print >> sys.stderr, 'GUI closing'
            self.GUIupdate = False

            self._logger.info("mainframe: Calling quit")
            self.quit(event != None or force)

            self._logger.debug("mainframe: OnCloseWindow END")
            ts = enumerate()
            for t in ts:
                self._logger.info("mainframe: Thread still running %s daemon %s", t.getName(), t.isDaemon())

            print >> sys.stderr, 'GUI closed'

    @forceWxThread
    def quit(self, force=True):
        self._logger.info("mainframe: in quit")
        if self.wxapp is not None:
            self._logger.info("mainframe: using self.wxapp")
            app = self.wxapp
        else:
            self._logger.info("mainframe: got app from wx")
            app = wx.GetApp()

        self._logger.info("mainframe: looping through toplevelwindows")
        for item in wx.GetTopLevelWindows():
            if item != self:
                if isinstance(item, wx.Dialog):
                    self._logger.info("mainframe: destroying %s", item)
                    item.Destroy()
                item.Close()
        self._logger.info("mainframe: destroying %s", self)
        self.Destroy()

        if app:
            def doexit():
                app.ExitMainLoop()
                wx.WakeUpMainThread()

            wx.CallLater(1000, doexit)
            if force:
                wx.CallLater(2500, app.Exit)
