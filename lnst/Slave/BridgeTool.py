"""
This module defines a class useful to work with "bridge" tool.

Copyright 2015 Mellanox Technologies. All rights reserved.
Licensed under the GNU General Public License, version 2 as
published by the Free Software Foundation; see COPYING for details.
"""

__author__ = """
jiri@mellanox.com (Jiri Pirko)
"""

from lnst.Common.ExecCmd import exec_cmd

class BridgeTool:
    def __init__(self, dev_name):
        self._dev_name = dev_name

    def _add_del_vlan(self, op, br_vlan_info):
        cmd = "bridge vlan %s dev %s vid %d" % (op, self._dev_name,
                                                br_vlan_info["vlan_id"])
        if br_vlan_info["pvid"]:
            cmd += " pvid"
        if br_vlan_info["untagged"]:
            cmd += " untagged"
        if br_vlan_info["self"]:
            cmd += " self"
        if br_vlan_info["master"]:
            cmd += " master"
        exec_cmd(cmd)

    def add_vlan(self, br_vlan_info):
        return self._add_del_vlan("add", br_vlan_info)

    def del_vlan(self, br_vlan_info):
        return self._add_del_vlan("del", br_vlan_info)

    def _add_del_fdb(self, op, br_fdb_info):
        cmd = "bridge fdb %s %s dev %s" % (op, br_fdb_info["hwaddr"],
                                           self._dev_name)
        if br_fdb_info["self"]:
            cmd += " self"
        if br_fdb_info["master"]:
            cmd += " master"
        if br_fdb_info["vlan_id"]:
            cmd += " vlan %s" % br_fdb_info["vlan_id"]
        exec_cmd(cmd)

    def add_fdb(self, br_fdb_info):
        return self._add_del_fdb("add", br_fdb_info)

    def del_fdb(self, br_fdb_info):
        return self._add_del_fdb("del", br_fdb_info)