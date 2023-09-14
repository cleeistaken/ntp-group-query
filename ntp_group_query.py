import logging
import ntplib

from argparse import ArgumentParser, Namespace
from datetime import datetime
from prettytable import PrettyTable
from threading import Thread
from typing import List

NIST_NTP = ['time-a-g.nist.gov',
            'time-b-g.nist.gov',
            'time-c-g.nist.gov',
            'time-d-g.nist.gov',
            'time-e-g.nist.gov',
            'time-a-wwv.nist.gov',
            'time-b-wwv.nist.gov',
            'time-c-wwv.nist.gov',
            'time-d-wwv.nist.gov',
            'time-e-wwv.nist.gov',
            'time-a-b.nist.gov',
            'time-b-b.nist.gov',
            'time-c-b.nist.gov',
            'time-d-b.nist.gov',
            'time-e-b.nist.gov',
            'utcnist.colorado.edu',
            'utcnist2.colorado.edu',
            'utcnist3.colorado.edu']


class NtpQueryThread(Thread):
    def __init__(self, server: str):
        logging.debug('creating thread for server %s', server)
        super().__init__()
        self.server = server
        self.stats = None

    def run(self):
        logging.debug('running thread to %s', self.server)
        c = ntplib.NTPClient()
        self.stats = c.request(host=self.server, version=3)

    def join(self, timeout=3.0):
        logging.debug('joining thread to %s with timeout %.1f seconds', self.server, timeout)
        Thread.join(self)


class NtqQueryThreadStat(object):
    def __init__(self, server: str, stats: ntplib.NTPStats):
        self.server = server
        self.stats = stats


class NtqQueryThreadResults(object):
    def __init__(self, threads: List[NtpQueryThread]):
        self.results = [NtqQueryThreadStat(server=thread.server, stats=thread.stats) for thread in threads]

    def get_results_table(self) -> PrettyTable:
        table = PrettyTable()
        table.field_names = ['Remote', 'Refid', 'Stratum', 'Delay', 'Offset', 'TX Time', 'Adjusted Time']
        table.align['Remote'] = 'l'
        table.align['Delay'] = 'l'
        table.align['Offset'] = 'l'
        table.align['TX Time'] = 'l'
        table.align['Adjusted Time'] = 'l'
        for result in self.results:
            table.add_row([result.server,
                           result.stats.ref_id,
                           result.stats.stratum,
                           result.stats.delay,
                           result.stats.offset,
                           datetime.fromtimestamp(result.stats.tx_time),
                           datetime.fromtimestamp(result.stats.orig_time + result.stats.offset)])
        return table


def get_args() -> Namespace:
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-s', '--server-list', nargs='+', default=[])
    group.add_argument('-n', '--nist', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    return parser.parse_args()


def main():
    args = get_args()

    # Set logging
    level = logging.DEBUG if args.verbose else logging.ERROR
    logging.basicConfig(level=level, format='(%(threadName)-9s) %(message)s', )

    # Set servers
    servers = NIST_NTP if args.nist else args.server_list

    threads = [NtpQueryThread(server=server) for server in servers]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    results = NtqQueryThreadResults(threads=threads)
    print(results.get_results_table())


if __name__ == "__main__":
    main()
