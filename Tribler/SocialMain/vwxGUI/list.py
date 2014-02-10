import wx
from time import time

from Tribler.Main.vwxGUI.list import ActivitiesList
from Tribler.Main.vwxGUI.list_item import ActivityListItem, CommentActivityItem, \
    AvantarItem
from Tribler.Main.vwxGUI.channel import ActivityList, ActivityManager
from Tribler.Main.vwxGUI import forceWxThread, format_time, DEFAULT_BACKGROUND, \
    LIST_EXPANDED, LIST_SELECTED
from collections import namedtuple
from Tribler.Main.vwxGUI.IconsManager import IconsManager, SMALL_ICON_MAX_DIM
from Tribler.Main.vwxGUI.list_body import ListItem

class Comment(namedtuple('Comment', ('id', 'inserted', 'time_stamp', 'name', 'comment', 'torrent', 'channel'))):
    def isMyComment(self):
        return False

Like = namedtuple('Like', ('id', 'inserted', 'time_stamp', 'name'))
Thumb = namedtuple('Thumb', ('id', 'inserted', 'time_stamp', 'name', 'message', 'path'))

class FriendListItem(ListItem):

    def __init__(self, *args, **kwargs):
        ListItem.__init__(self, *args, **kwargs)

    def AddComponents(self, leftSpacer, rightSpacer):
        ListItem.AddComponents(self, leftSpacer, rightSpacer)

        im = IconsManager.getInstance()
        icon = wx.StaticBitmap(self, bitmap=im.get_default('ONLINE' if self.data[0] in ['Niels', 'Johan'] else 'OFFLINE', SMALL_ICON_MAX_DIM))
        self.hSizer.Prepend(icon, 0, wx.CENTER | wx.RIGHT | wx.LEFT, 5)
        self.hSizer.Layout()

class LikeActivityItem(AvantarItem):

    def __init__(self, parent, parent_list, columns, data, original_data, leftSpacer=0, rightSpacer=0, showChange=False, list_selected=LIST_SELECTED, list_expanded=LIST_EXPANDED):
        AvantarItem.__init__(self, parent, parent_list, columns, data, original_data, 45, rightSpacer, showChange, list_selected, list_expanded)

    def AddComponents(self, leftSpacer, rightSpacer):
        like = self.original_data

        self.header = "New like received, posted %s by %s" % (format_time(like.time_stamp).lower(), like.name)

        im = IconsManager.getInstance()
        self.avantar = im.get_default('THUMB_UP', SMALL_ICON_MAX_DIM)
        AvantarItem.AddComponents(self, leftSpacer, rightSpacer)

class ThumbActivityItem(AvantarItem):

    def AddComponents(self, leftSpacer, rightSpacer):
        like = self.original_data

        self.header = "New image received, posted %s by %s" % (format_time(like.time_stamp).lower(), like.name)
        self.body = [wx.Bitmap(like.path)]

        im = IconsManager.getInstance()
        self.avantar = im.get_default('THUMBNAIL', SMALL_ICON_MAX_DIM)
        AvantarItem.AddComponents(self, leftSpacer, rightSpacer)

class WallManager(ActivityManager):

    def refresh(self):
        now = time()
        DAY = 86400

        comments = [Comment(1, now - 2 * DAY, now - 2 * DAY, 'Niels', 'Hello World', None, None),
                    Comment(2, now - 1 * DAY, now - 1 * DAY, 'Niels', 'OnePage is working', None, None)]
        likes = [Like(1, now - 1, now - 1, 'Johan')]
        thumbnails = [Thumb(1, now - 1 * DAY, now - 1 * DAY, 'Niels', 'MSG', r'c:\thumb.png')]
        self.list.SetData(comments, likes, thumbnails)

class WallList(ActivityList):

    def GetManager(self):
        if getattr(self, 'manager', None) == None:
            self.manager = WallManager(self)
        return self.manager

    def CreateHeader(self, parent):
        return None

    @forceWxThread
    def SetData(self, comments, likes, thumbnails):

        # first element must be timestamp, allows for easy sorting
        data = [(comment.inserted, ("COMMENT_%d" % comment.id, (), (0, comment), CommentActivityItem)) for comment in comments]
        data += [(like.inserted, ("LIKE_%d" % like.id, (), like, LikeActivityItem)) for like in likes]
        data += [(thumb.inserted, ("THUMB_%d" % thumb.id, (), thumb, ThumbActivityItem)) for thumb in thumbnails]
        data.sort(reverse=False)

        # removing timestamp
        data = [item for _, item in data]
        if len(data) > 0:
            self.list.SetData(data)
        else:
            self.list.ShowMessage('No recent activity is found.')

    def ShowPreview(self):
        pass

class FriendList(ActivitiesList):

    def _SetData(self):
        self.list.SetData([(1, ['Niels'], None, FriendListItem), (2, ['Johan'], None, FriendListItem), (3, ['Lipu'], None, FriendListItem)])
        self.ResizeListItems()

    def OnExpand(self, item):
        return True

