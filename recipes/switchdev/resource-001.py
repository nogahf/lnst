"""
Copyright 2017 Mellanox Technologies. All rights reserved.
Licensed under the GNU General Public License, version 2 as
published by the Free Software Foundation; see COPYING for details.
"""

__author__ = """
arkadis@mellanox.com (Arkadi Sharshevsky)
"""

from lnst.Controller.Task import ctl
from TestLib import TestLib
from time import sleep
import os

def create_batch_file(tl, iface, route_count):
    machine = iface.get_machine()
    m = iface.get_host()
    routes = 0

    if (route_count > 100000):
        raise Exception("Route count cannot be larger than 100,000")

    f = open("routes_{}".format(route_count), "a")
    f.write("address add 20.0.0.2/24 dev {}\n".format(iface.get_devname()))
    for i in range(1, 101):
        for j in range(1, 101):
            for k in range(0, 10):
                if (routes < (route_count * 1000)):
                    f.write("route add {}.{}.{}.0/24 dev {}\n".format(i, j, k, iface.get_devname()))
                routes += 1
    f.close()
    machine.copy_file_to_machine("routes_{}".format(route_count), "/tmp/routes_{}".format(route_count))

def create_batch_files(tl, iface):
    create_batch_file(tl, iface, 50)
    create_batch_file(tl, iface, 100)

def destroy_batch_file(tl, iface, route_count):
    machine = iface.get_machine()
    host = iface.get_host()

    if os.path.isfile("routes_{}".format(route_count)):
        os.remove("routes_{}".format(route_count))

    cmd = "rm -f /tmp/routes_{}".format(route_count)
    host.run(cmd)

def destroy_batch_files(tl, iface):
    destroy_batch_file(tl, iface, 50)
    destroy_batch_file(tl, iface, 100)

def get_offload_route_count(host):
    cmd = "ip route | grep -o 'offload' | wc -l"
    cmd = host.run(cmd)
    return cmd.out()

def set_default_profile(tl, iface):
    tl.devlink_resource_set(iface, "/kvd/hash_double", 60416)
    tl.devlink_resource_set(iface, "/kvd/hash_single", 87040)
    tl.devlink_reload(iface)

def add_routes(host, rout_count):
    cmd = "ip -force -b /tmp/routes_{}".format(rout_count)
    host.run(cmd, timeout=250)
    sleep(15)

def do_task(ctl, hosts, ifaces, aliases):
    m1, sw = hosts
    m1_if1, sw_if1 = ifaces

    tl = TestLib(ctl, aliases)
    destroy_batch_files(tl, sw_if1)
    create_batch_files(tl, sw_if1)

    sw_if1.set_link_down()
    sw_if1.set_link_up()
    sleep(15)

    # Add 50K routes, shouldn't fail
    add_routes(sw_if1.get_host(), 50)
    num = get_offload_route_count(sw_if1.get_host())
    if int(num) != 50001:
        tl.custom(sw_if1.get_host(), "resource test", "should have been 50001, currently {}".format(num))

    tl.devlink_reload(sw_if1)
    sw_if1.set_link_up()
    sleep(15)

    # Add 100K routes, should fail
    add_routes(sw_if1.get_host(), 100)
    num = get_offload_route_count(sw_if1.get_host())
    if int(num) != 0:
        tl.custom(sw_if1.get_host(), "resource test", "should abort, kvd linear to small")

    # Enlarge the hash single partiton
    tl.devlink_resource_set(sw_if1, "/kvd/hash_double", 32768)
    tl.devlink_resource_set(sw_if1, "/kvd/hash_single", 114688)
    tl.devlink_reload(sw_if1)
    sw_if1.set_link_up()
    sleep(15)

    # Add 100K routes, should succeed
    add_routes(sw_if1.get_host(), 100)
    num = get_offload_route_count(sw_if1.get_host())
    if int(num) != 100001:
        tl.custom(sw_if1.get_host(), "resource test", "should be able to offload")

    destroy_batch_files(tl, sw_if1)
    set_default_profile(tl, sw_if1)

do_task(ctl, [ctl.get_host("machine1"),
              ctl.get_host("switch")],
        [ctl.get_host("machine1").get_interface("if1"),
         ctl.get_host("switch").get_interface("if1")],
        ctl.get_aliases())
