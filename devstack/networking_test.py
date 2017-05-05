#!/usr/bin/env python
# Copyright 2016 Hewlett Packard Enterprise Development Company LP
#
# Author: Federico Ceratto <federico.ceratto@hpe.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
    Network simulator
    ~~~~~~~~~~~~~~~~~
    Perform end-to-end stress tests on Designate on a simulated network
    that displays high latency and packet loss (almost like real ones)

    WARNING: this script is to be run on a disposable devstack VM
    It requires sudo and it will configure /sbin/tc

    Usage:
    cd <designate_repo>/contrib/vagrant
    ./setup_ubuntu_devstack
    vagrant ssh ubuntu
    source ~/devstack/openrc
    /opt/stack/designate/devstack/networking_test.py
    Monitor the logfiles
"""

from argparse import ArgumentParser
from collections import OrderedDict
from itertools import product
from subprocess import check_output
from subprocess import CalledProcessError
from tempfile import NamedTemporaryFile
from threading import Thread
import json
import logging
import os
import random
import string
import time
import sys

import dns
import dns.resolver

log = logging.getLogger()

tc_path = '/sbin/tc'
sudo_path = '/usr/bin/sudo'
iptables_restore_path = '/sbin/iptables-restore'
designate_cli_path = '/usr/local/bin/designate'
openstack_cli = 'openstack'


def gen_random_name(l):
    return "".join(
        random.choice(string.ascii_lowercase + string.digits)
        for n in range(l)
    )


def parse_args():
    ap = ArgumentParser()
    ap.add_argument('-d', '--debug', action='store_true')
    return ap.parse_args()


def run_shell(cmd, env=None):
    log.debug("  running %s" % cmd)
    out = check_output(cmd, env=env, shell=True, executable='/bin/bash')
    return [line.rstrip() for line in out.splitlines()]


class DesignateCLI(object):
    """Designate CLI runner
    """

    def __init__(self):
        """Setup CLI handler"""
        self._cli_env = {}
        for k, v in sorted(os.environ.items()):
            if k.startswith('OS_'):
                log.debug("%s: %s", k, v)
                self._cli_env[k] = v

    def setup_quota(self, quota):
        """Setup quota
        """
        user_id = self.run_json("token issue")["user_id"]

        cmd = """quota-update
        --domains %(quota)d
        --domain-recordsets %(quota)d
        --recordset-records %(quota)d
        --domain-records %(quota)d
        %(user_id)s """
        cmd = ' '.join(cmd.split())
        quotas = self.run_designate_cli_table(cmd % dict(quota=quota,
                                                         user_id=user_id))
        assert quotas['domain_records'] == str(quota)

    def run(self, cmd):
        """Run a openstack client command
        """
        return run_shell("%s %s" % (openstack_cli, cmd),
                         env=self._cli_env)

    def run_json(self, cmd):
        """Run a openstack client command using JSON output

        :returns: dict
        :raises CalledProcessError:
        """
        cmd = "%s %s -f json" % (openstack_cli, cmd)
        log.debug("  running %s" % cmd)
        out = check_output(cmd, env=self._cli_env, shell=True,
                           executable='/bin/bash')
        return json.loads(out)

    def runcsv(self, cmd):
        """Run a command using the -f csv flag, parse the output
        and return a list of dicts
        """
        cmdout = self.run(cmd + " -f csv")
        header = [item.strip('"') for item in cmdout[0].split(',')]
        output_rows = []
        for line in cmdout[1:]:
            rawvalues = line.split(',')
            d = OrderedDict()
            for k, v in zip(header, rawvalues):
                if v.startswith('"') or v.endswith('"'):
                    v = v.strip('"')
                else:
                    try:
                        v = int(v)
                    except ValueError:
                        v = float(v)

                d[k] = v

            output_rows.append(d)

        return output_rows

    def run_designate_cli_table(self, cmd):
        """Run a command in the designate cli expecting a table to be
        returned and parse it into a dict
        """
        cmdout = run_shell("%s %s" % (designate_cli_path, cmd),
                           env=self._cli_env)
        out = {}
        try:
            for line in cmdout:
                if not line.startswith('| '):
                    continue
                if not line.endswith(' |'):
                    continue
                k = line.split('|')[1].strip()
                v = line.split('|')[2].strip()
                out[k] = v
        except Exception:
            log.error("Unable to parse output into a dict:")
            for line in out:
                log.error(line)
            log.error("-----------------------------------")
            raise

        return out


class TrafficControl(object):
    """Configure Linux Traffic Control to simulate a real network
    """

    protocol_marks = dict(
        mysql=1,
        dns_udp=2,
        dns_tcp=3,
    )

    def run_tc(self, cmd):
        return run_shell("%s %s %s" % (sudo_path, tc_path, cmd))

    def _apply_iptables_conf(self, ipt_conf):
        tf = NamedTemporaryFile()
        tf.file.write(ipt_conf)
        tf.file.flush()
        run_shell("%s %s %s" % (sudo_path, iptables_restore_path, tf.name))
        tf.file.close()

    def cleanup_iptables_marking(self):
        # Currently unneeded
        ipt_conf = """
*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
COMMIT
*mangle
:PREROUTING ACCEPT [0:0]
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]
COMMIT
"""
        self._apply_iptables_conf(ipt_conf)

    def setup_iptables_marking(self):
        # Currently unneeded
        ipt_conf = """
*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
COMMIT
*mangle
:PREROUTING ACCEPT [0:0]
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]
-A PREROUTING -i lo -p tcp -m tcp --dport 3306 -j MARK --set-xmark %(mysql)s
-A PREROUTING -i lo -p tcp -m tcp --sport 3306 -j MARK --set-xmark %(mysql)s
-A PREROUTING -i lo -p tcp -m tcp --dport 53 -j MARK --set-xmark %(dns_tcp)s
-A PREROUTING -i lo -p tcp -m tcp --sport 53 -j MARK --set-xmark %(dns_tcp)s
-A PREROUTING -i lo -p udp -m udp --dport 53 -j MARK --set-xmark %(dns_udp)s
-A PREROUTING -i lo -p udp -m udp --sport 53 -j MARK --set-xmark %(dns_udp)s
COMMIT
"""
        marks = dict((k, "0x%d/0xffffffff" % v)
                     for k, v in self.protocol_marks.items())
        ipt_conf = ipt_conf % marks
        self._apply_iptables_conf(ipt_conf)

    def cleanup_tc(self):
        """Clean up tc conf
        """
        out = self.run_tc('qdisc show dev lo')
        if out:
            log.debug("Cleaning up tc conf")
            self.run_tc('qdisc del dev lo root')
        else:
            log.debug("No tc conf to be cleaned up")

    def setup_tc(self, dns_latency_ms=0, dns_packet_loss_perc=0,
                 db_latency_ms=1, db_packet_loss_perc=1):
        """Setup traffic control
        """
        self.cleanup_tc()

        # Create HTB at the root
        self.run_tc("qdisc add dev lo handle 1: root htb")

        self.run_tc("class add dev lo parent 1: classid 1:5 htb rate 1000Mbps")
        self.run_tc("class add dev lo parent 1: classid 1:7 htb rate 1000Mbps")

        # TCP DNS
        self._setup_tc_block('1:8', 'tcp', 53, dns_latency_ms,
                             dns_packet_loss_perc)
        # UDP DNS
        self._setup_tc_block('1:9', 'udp', 53, dns_latency_ms,
                             dns_packet_loss_perc)
        # TCP mDNS
        self._setup_tc_block('1:10', 'tcp', 5354, dns_latency_ms,
                             dns_packet_loss_perc)
        # UDP mDNS
        self._setup_tc_block('1:11', 'udp', 5354, dns_latency_ms,
                             dns_packet_loss_perc)
        # MySQL
        self._setup_tc_block('1:12', 'tcp', 3306, 1, 1)

        # RabbitMQ port: 5672
        self._setup_tc_block('1:13', 'tcp', 5672, 1, 1)

        # MemcacheD
        self._setup_tc_block('1:14', 'tcp', 11211, 1, 1)

    def _setup_tc_block(self, class_id, proto, port, latency_ms,
                        packet_loss_perc):
        """Setup tc htb entry, netem and filter"""
        assert proto in ('tcp', 'udp')
        cmd = "class add dev lo parent 1: classid %s htb rate 1000Mbps" % \
            class_id
        self.run_tc(cmd)
        self._setup_netem(class_id, latency_ms, latency_ms, packet_loss_perc)
        self._setup_filter(proto, 'sport %d' % port, class_id)
        self._setup_filter(proto, 'dport %d' % port, class_id)

    def _setup_netem(self, classid, latency1, latency2, loss_perc):
        """Setup tc netem
        """
        # This could be done with the FireQOS tool instead:
        # https://firehol.org/tutorial/fireqos-new-user/
        cmd = ("qdisc add dev lo parent {cid} netem"
               " corrupt 0.1%"
               " delay {lat1}ms {lat2}ms distribution normal"
               " duplicate 0.1%"
               " loss {packet_loss_perc}%"
               " reorder 25% 50%")
        cmd = cmd.format(cid=classid, lat1=latency1, lat2=latency2,
                         packet_loss_perc=loss_perc)
        self.run_tc(cmd)

    def _setup_filter(self, protocol, filter, flowid):
        """Setup tc filter
        """
        protocol_nums = dict(tcp=6, udp=17)
        pnum = protocol_nums[protocol]
        cmd = "filter add dev lo protocol ip prio 1 u32 match ip protocol " \
            "%(pnum)d 0xff match ip %(filter)s 0xffff flowid %(flowid)s"

        self.run_tc(cmd % dict(pnum=pnum, filter=filter, flowid=flowid))


class Digger(object):
    def __init__(self):
        self.ns_ipaddr = self.get_nameserver_ipaddr()
        self._setup_resolver()
        self.max_probes_per_second = 30
        self.reset_goals()

    @property
    def prober_is_running(self):
        try:
            return self._prober_thread.is_alive()
        except AttributeError:
            return False

    def _setup_resolver(self, timeout=1):
        resolver = dns.resolver.Resolver(configure=False)
        resolver.timeout = timeout
        resolver.lifetime = timeout
        resolver.nameservers = [self.ns_ipaddr]
        self.resolver = resolver

    def get_nameserver_ipaddr(self):
        # FIXME: find a better way to do this
        out = run_shell('sudo netstat -nlpt | grep pdns_server')
        ipaddr = out[0].split()[3]
        ipaddr = ipaddr.split(':', 1)[0]
        log.debug("Resolver ipaddr: %s" % ipaddr)
        return ipaddr

    def query_a_record(self, record_name, timeout=3):
        try:
            answer = self.resolver.query(record_name, 'A')
            if answer.rrset:
                return answer.rrset[0].address
        except Exception:
            return None

    def query_soa(self, zone_name, timeout=3):
        try:
            soa_answer = self.resolver.query(zone_name, 'SOA')
            soa_serial = soa_answer[0].serial
            return soa_serial
        except Exception:
            return None

    def reset_goals(self):
        assert not self.prober_is_running
        self.goals = set()
        self.summary = dict(
            success_cnt=0,
            total_time_to_success=0,
        )

    def add_goal(self, goal):
        self.goals.add(goal + (time.time(), ))

    def _print_summary(self, final=True):
        """Log out a summary of the current run
        """
        remaining = len(self.goals)
        success_cnt = self.summary['success_cnt']
        try:
            avg_t = (self.summary['total_time_to_success'] / success_cnt)
            avg_t = ", avg time to success: %2.3fs" % avg_t
        except ZeroDivisionError:
            avg_t = ''

        logf = log.info if final else log.debug
        logf("  test summary: success %3d, remaining %3d %s" % (
            success_cnt, remaining, avg_t))

    def _probe_resolver(self):
        """Probe the local resolver, report achieved goals
        """
        log.debug("Starting prober")
        assert self.prober_is_running is True
        self._progress_report_time = 0
        now = time.time()
        while (self.goals or not self.prober_can_stop) and \
                now < self.prober_timeout_time:

            for goal in tuple(self.goals):
                goal_type = goal[0]
                if goal_type == 'zone_serial_ge':
                    goal_type, zone_name, serial, t0 = goal
                    actual_serial = self.query_soa(zone_name)
                    if actual_serial and actual_serial >= serial:
                        deltat = time.time() - t0
                        log.debug("  reached %s in %.3fs" % (repr(goal),
                                                             deltat))
                        self.goals.discard(goal)
                        self.summary['success_cnt'] += 1
                        self.summary['total_time_to_success'] += deltat

                elif goal_type == 'record_a':
                    goal_type, record_name, ipaddr, t0 = goal
                    actual_ipaddr = self.query_a_record(record_name)
                    if actual_ipaddr == ipaddr:
                        deltat = time.time() - t0
                        log.debug("  reached %s in %.3fs" % (repr(goal),
                                                             deltat))
                        self.goals.discard(goal)
                        self.summary['success_cnt'] += 1
                        self.summary['total_time_to_success'] += deltat

                else:
                    log.error("Unknown goal %r" % goal)

                if time.time() < self.prober_timeout_time:
                    time.sleep(1.0 / self.max_probes_per_second)
                else:
                    break

                if time.time() > self._progress_report_time:
                    self._print_summary(final=False)
                    self._progress_report_time = time.time() + 10

            time.sleep(1.0 / self.max_probes_per_second)
            now = time.time()

        if now > self.prober_timeout_time:
            log.info("prober timed out after %d s" % (
                now - self.prober_start_time))

        self._print_summary()

    def probe_resolver(self, timeout=600):
        """Probe the local resolver in a dedicated thread until all
        goals have been achieved or timeout occours
        """
        assert not self.prober_is_running
        self.prober_can_stop = False
        self.prober_start_time = time.time()
        self.prober_timeout_time = self.prober_start_time + timeout
        self._prober_thread = Thread(target=self._probe_resolver)
        self._prober_thread.daemon = True
        self._prober_thread.start()

    def stop_prober(self):
        self.prober_can_stop = True
        self.prober_timeout_time = 0

    def wait_on_prober(self):
        self.prober_can_stop = True
        self._prober_thread.join()
        assert self.prober_is_running is False


def list_zones(cli):
    zones = [z["name"] for z in cli.run_json('zone list')]
    log.debug("Found zones: %r", zones)
    return zones


def delete_zone_by_name(cli, zn, ignore_missing=False):
    if ignore_missing:
        # Return if the zone is not present
        zones = list_zones(cli)
        if zn not in zones:
            return

    cli.run('zone delete %s' % zn)


def create_and_probe_a_record(cli, digger, zone_id, record_name, ipaddr):
    cli.run_json('recordset create %s %s --type A --records %s' %
                 (zone_id, record_name, ipaddr))
    digger.add_goal(('record_a', record_name, ipaddr))


def delete_all_zones(cli):
    zones = list_zones(cli)
    log.info("%d zones to be deleted" % len(zones))
    for zone in zones:
        log.info("Deleting %s", zone)
        delete_zone_by_name(cli, zone)


def create_zone_with_retry_on_duplicate(cli, digger, zn, timeout=300,
                                        dig=False):
    """Create a zone, retry when a duplicate is found,
    optionally monitor for propagation

    :returns: dict
    """
    t0 = time.time()
    timeout_time = timeout + t0
    created = False
    while time.time() < timeout_time:
        try:
            output = cli.run_json(
                "zone create %s --email devstack@example.org" % zn)
            created = True
            log.debug("  zone created after %f" % (time.time() - t0))
            break

        except CalledProcessError as e:
            if e.output == 'Duplicate Zone':
                # dup zone, sleep and retry
                time.sleep(1)
                pass

            elif e.output == 'over_quota':
                raise RuntimeError('over_quota')

            else:
                raise

    assert output['serial']

    if not created:
        raise RuntimeError('timeout')

    if dig:
        digger.reset_goals()
        digger.add_goal(('zone_serial_ge', zn, int(output['serial'])))
        digger.probe_resolver(timeout=timeout)
        digger.wait_on_prober()

    return output


def test_create_list_delete_loop(cli, digger, cycles_num, zn='cld.org.'):
    """Create, list, delete a zone in a loop
    Monitor for propagation time
    """
    log.info("Test zone creation, list, deletion")
    delete_zone_by_name(cli, zn, ignore_missing=True)

    for cycle_cnt in range(cycles_num):
        zone = create_zone_with_retry_on_duplicate(cli, digger, zn, dig=True)

        zones = cli.runcsv('domain-list')
        assert any(z['name'] == zn for z in zones), zones

        cli.run('domain-delete %s' % zone['id'])

        zones = cli.runcsv('domain-list')
        assert not any(z['name'] == zn for z in zones), zones

    log.info("done")


def test_one_big_zone(cli, digger, zone_size):
    """Create a zone with many records,
    perform CRUD on records and monitor for propagation time
    """
    t0 = time.time()
    zn = 'bigzone-%s.org.' % gen_random_name(12)
    delete_zone_by_name(cli, zn, ignore_missing=True)
    zone = create_zone_with_retry_on_duplicate(cli, digger, zn, dig=True)
    assert 'serial' in zone, zone
    assert 'id' in zone, zone
    try:
        digger.reset_goals()
        digger.add_goal(('zone_serial_ge', zn, int(zone['serial'])))
        digger.probe_resolver(timeout=60)

        record_creation_threads = []
        for record_num in range(zone_size):
            record_name = "rec%d" % record_num
            ipaddr = "127.%d.%d.%d" % (
                (record_num >> 16) % 256,
                (record_num >> 8) % 256,
                record_num % 256,
            )
            t = Thread(target=create_and_probe_a_record,
                       args=(cli, digger, zone['id'], record_name, ipaddr))
            t.start()
            record_creation_threads.append(t)
            time.sleep(.5)

        digger.wait_on_prober()

    except KeyboardInterrupt:
        log.info("Exiting on keyboard")
        raise

    finally:
        digger.stop_prober()
        delete_zone_by_name(cli, zone['name'])
        log.info("Done in %ds" % (time.time() - t0))


def test_servers_are_configured(cli):
    servers = cli.runcsv('server-list')
    assert servers[0]['name'] == 'ns1.devstack.org.'
    log.info("done")


def test_big_zone(args, cli, digger, tc):
    log.info("Test creating many records in one big zone")

    dns_latencies_ms = (1, 100)
    dns_packet_losses = (1, 15)
    zone_size = 20

    for dns_latency_ms, dns_packet_loss_perc in product(dns_latencies_ms,
                                                        dns_packet_losses):
        tc.cleanup_tc()
        tc.setup_tc(dns_latency_ms=dns_latency_ms,
                    dns_packet_loss_perc=dns_packet_loss_perc)
        log.info("Running test with DNS latency %dms packet loss %d%%" % (
                    dns_latency_ms, dns_packet_loss_perc))
        test_one_big_zone(cli, digger, zone_size)


def run_tests(args, cli, digger, tc):
    """Run all integration tests
    """
    # test_servers_are_configured(cli)
    # test_create_list_delete_loop(cli, digger, 10)
    test_big_zone(args, cli, digger, tc)


def main():
    args = parse_args()
    loglevel = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=loglevel,
        format='%(relativeCreated)8d %(levelname)s %(funcName)20s %(message)s',
    )

    cli = DesignateCLI()
    cli.setup_quota(10000)

    digger = Digger()

    delete_all_zones(cli)

    tc = TrafficControl()
    tc.cleanup_tc()

    try:
        run_tests(args, cli, digger, tc)
    finally:
        tc.cleanup_tc()


if __name__ == '__main__':
    sys.exit(main())
