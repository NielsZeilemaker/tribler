# Written by Arno Bakker and Bram Cohen
# Updated by George Milescu
# Updated by Egbert Bouman, added subsection names + using OrderedDict + cleanup 
# see LICENSE.txt for license information

""" Default values for all configurarable parameters of the Core"""
#
# For an explanation of each parameter, see SessionConfig/DownloadConfig.py
#
# defaults with comments behind them are not user-setable via the
# *ConfigInterface classes, because they are not currently implemented (IPv6)
# or we only use them internally.
#
# WARNING:
#    As we have release Tribler 4.5.0 you must now take into account that
#    people have stored versions of these params on their disk. Make sure
#    you change the version number of the structure and provide upgrade code
#    such that your code won't barf because we loaded an older version from
#    disk that does not have your new fields.
#

import sys

from collections import OrderedDict

from Tribler.Core.simpledefs import DISKALLOC_NORMAL, DISKALLOC_SPARSE

DEFAULTPORT = 7760

#
# Session opts
#
# History:
#  Version 2: as released in Tribler 4.5.0
#

SESSDEFAULTS_VERSION = 2
sessdefaults = OrderedDict()

# General Tribler settings
sessdefaults['general'] = OrderedDict()
sessdefaults['general']['version'] = SESSDEFAULTS_VERSION
sessdefaults['general']['state_dir'] = None
sessdefaults['general']['install_dir'] = u'.'
sessdefaults['general']['ip'] = ''
sessdefaults['general']['minport'] = DEFAULTPORT
sessdefaults['general']['maxport'] = DEFAULTPORT
sessdefaults['general']['bind'] = []
sessdefaults['general']['ipv6_enabled'] = 0  # allow the client to connect to peers via IPv6 (currently not supported)
sessdefaults['general']['ipv6_binds_v4'] = None  # set if an IPv6 server socket won't also field IPv4 connections (default = set automatically)
sessdefaults['general']['timeout'] = 300.0
sessdefaults['general']['timeout_check_interval'] = 60.0
sessdefaults['general']['eckeypairfilename'] = None
sessdefaults['general']['megacache'] = True
sessdefaults['general']['nickname'] = '__default_name__'  # is replaced with hostname in LaunchManyCore.py
sessdefaults['general']['mugshot'] = None
sessdefaults['general']['videoanalyserpath'] = None
sessdefaults['general']['peer_icon_path'] = None
sessdefaults['general']['live_aux_seeders'] = []

# Mainline DHT settings
sessdefaults['mainline_dht'] = OrderedDict()
sessdefaults['mainline_dht']['enabled'] = True
sessdefaults['mainline_dht']['mainline_dht_port'] = DEFAULTPORT - 3

# Torrent checking settings
sessdefaults['torrent_checking'] = OrderedDict()
sessdefaults['torrent_checking']['enabled'] = 1
sessdefaults['torrent_checking']['torrent_checking_period'] = 31  # will be changed to min(max(86400/ntorrents, 15), 300) at runtime

# Torrent collecting settings
sessdefaults['torrent_collecting'] = OrderedDict()
sessdefaults['torrent_collecting']['enabled'] = True
sessdefaults['torrent_collecting']['dht_torrent_collecting'] = True
sessdefaults['torrent_collecting']['torrent_collecting_max_torrents'] = 50000
sessdefaults['torrent_collecting']['torrent_collecting_dir'] = None
sessdefaults['torrent_collecting']['stop_collecting_threshold'] = 200

# Libtorrent settings
sessdefaults['libtorrent'] = OrderedDict()
sessdefaults['libtorrent']['enabled'] = True
sessdefaults['libtorrent']['lt_proxytype'] = 0  # no proxy server is used by default
sessdefaults['libtorrent']['lt_proxyserver'] = None
sessdefaults['libtorrent']['lt_proxyauth'] = None
sessdefaults['libtorrent']['utp'] = True

# SWIFTPROC config
sessdefaults['swift'] = OrderedDict()
sessdefaults['swift']['enabled'] = True
sessdefaults['swift']['swiftpath'] = None
sessdefaults['swift']['swiftworkingdir'] = '.'
sessdefaults['swift']['swiftcmdlistenport'] = DEFAULTPORT + 481
sessdefaults['swift']['swiftdlsperproc'] = 1000
sessdefaults['swift']['swiftmetadir'] = None
# Config for tunneling via swift, e.g. dispersy
sessdefaults['swift']['swifttunnellistenport'] = DEFAULTPORT - 2
sessdefaults['swift']['swifttunnelhttpgwlistenport'] = sessdefaults['swift']['swifttunnellistenport'] + 10000
sessdefaults['swift']['swifttunnelcmdgwlistenport'] = sessdefaults['swift']['swifttunnellistenport'] + 20000
sessdefaults['swift']['swiftdhtport'] = 9999

# Dispersy config
sessdefaults['dispersy'] = OrderedDict()
sessdefaults['dispersy']['enabled'] = True
sessdefaults['dispersy']['dispersy-tunnel-over-swift'] = False
sessdefaults['dispersy']['dispersy_port'] = DEFAULTPORT - 1

#
# BT per download opts
#
# History:
#  Version 2: as released in Tribler 4.5.0
#  Version 3:
#  Version 4: allow users to specify a download directory every time
#  Version 6: allow users to overwrite the multifile destination
#  Version 7: swift params
#  Version 8: deleted many of the old params that were not used anymore (due to the switch to libtorrent)

DLDEFAULTS_VERSION = 8
dldefaults = OrderedDict()

# General download settings
dldefaults['general'] = OrderedDict()
dldefaults['general']['version'] = DLDEFAULTS_VERSION
dldefaults['general']['saveas'] = None  # Set to get_default_destdir()
dldefaults['general']['showsaveas'] = True  # Allow users to choose directory for every new download
dldefaults['general']['max_upload_rate'] = 0
dldefaults['general']['max_download_rate'] = 0
dldefaults['general']['alloc_type'] = DISKALLOC_NORMAL if sys.platform == 'win32' else DISKALLOC_SPARSE
dldefaults['general']['super_seeder'] = 0
dldefaults['general']['mode'] = 0
dldefaults['general']['selected_files'] = []
dldefaults['general']['correctedfilename'] = None

# VOD config
dldefaults['vod'] = OrderedDict()
dldefaults['vod']['vod_usercallback'] = None
dldefaults['vod']['vod_userevents'] = []
dldefaults['vod']['video_source'] = None
dldefaults['vod']['video_ratelimit'] = 0
dldefaults['vod']['video_source_authconfig'] = None

# Swift config
dldefaults['swift'] = OrderedDict()
dldefaults['swift']['swiftlistenport'] = None
dldefaults['swift']['swiftcmdgwlistenport'] = None
dldefaults['swift']['swifthttpgwlistenport'] = None
dldefaults['swift']['swiftmetadir'] = None
dldefaults['swift']['name'] = None

tdefdictdefaults = {}
tdefdictdefaults['comment'] = None
tdefdictdefaults['created by'] = None
tdefdictdefaults['announce'] = None
tdefdictdefaults['announce-list'] = None
tdefdictdefaults['nodes'] = None  # mainline DHT
tdefdictdefaults['httpseeds'] = None
tdefdictdefaults['url-list'] = None
tdefdictdefaults['encoding'] = None

tdefmetadefaults = {}
tdefmetadefaults['version'] = 1
tdefmetadefaults['piece length'] = 0
tdefmetadefaults['makehash_md5'] = 0
tdefmetadefaults['makehash_crc32'] = 0
tdefmetadefaults['makehash_sha1'] = 0
tdefmetadefaults['createmerkletorrent'] = 0
tdefmetadefaults['torrentsigkeypairfilename'] = None
tdefmetadefaults['thumb'] = None  # JPEG data

tdefdefaults = {}
tdefdefaults.update(tdefdictdefaults)
tdefdefaults.update(tdefmetadefaults)
