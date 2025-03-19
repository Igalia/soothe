# Soothe - testing framework for encoders quality
# Copyright (C) 2020, Fluendo, S.A.
#  Author: Pablo Marcos Oltra <pmarcos@fluendo.com>, Fluendo, S.A.
# Copyright (C) 2025, Igalia, S.L.
#  Author: Victor Jaquez <vjaquez@igalia.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library. If not, see <https://www.gnu.org/licenses/>.

"""CLI handler for Soothe"""

import argparse
import multiprocessing
import os
import sys

from typing import Any
from tempfile import gettempdir

from soothe.soothe import RunParams, Soothe

APPNAME = "soothe"
ASSETS_DIR = "assets"
RESOURCES_DIR = "resources"
OUTPUT_DIR = "soothe_output"
ENCODERS_DIR = "encoders"

def soothe_main() -> None:
    """Entry point for the application"""
    main = Main()
    main.run()

class Main: # pylint: disable=too-few-public-methods
    """Main class for Soothe"""

    def __init__(self) -> None:
        self.assets_dir = os.path.join(os.path.dirname(__file__), '..', ASSETS_DIR)
        self.resources_dir = os.path.join(os.path.dirname(__file__), '..', RESOURCES_DIR)
        self.output_dir = os.path.join(gettempdir(), OUTPUT_DIR)

        self.args = self._create_argument_parser()

    def run(self) -> None:
        """Run Soothe"""
        args = self.args.parse_args()

        if hasattr(args, 'func'):
            soothe = Soothe(
                assets_dir=args.assets_dir,
                resources_dir=args.resources_dir,
                output_dir=args.output_dir,
            )
            args.func(args, soothe)
        else:
            self.args.print_help()


    def _create_argument_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-r',
            '--resources-dir',
            help='set the directory where resources are taken from',
            default=self.resources_dir,
        )
        parser.add_argument(
            '-a',
            '--assets-dir',
            help=(
                'set directory where assets will be read from, '
                f"multiple directories are supported with OS path separator ({os.pathsep})"
            ),
            default=self.assets_dir,
        )
        parser.add_argument(
            '-o',
            '--output-dir',
            help='set the directory where encoders outputs will be stored',
            default=self.output_dir,
        )
        subparser = parser.add_subparsers(title='subcommands')
        self._add_list_cmd(subparser)
        self._add_run_cmd(subparser)
        self._add_download_cmd(subparser)
        return parser

    def _add_list_cmd(self, subparsers: Any) -> None:
        subparser = subparsers.add_parser(
            'list',
            aliases=['l'],
            help='show list of available test suites and decoders',
        )
        subparser.add_argument(
            '-al',
            '--asset-lists',
            help='show only the test suites given',
            nargs='+',
        )
        subparser.add_argument(
            '-a',
            '--assets',
            help='show assets of asset lists',
            action='store_true',
        )
        subparser.add_argument(
            '-c',
            '--check',
            help='check which encoders can be run successfully',
            action='store_true',
        )
        subparser.add_argument(
            '-v',
            '--verbose',
            help='show stdout and stderr of executed commands',
            action='store_true',
        )
        subparser.add_argument(
            '-e',
            '--encoders',
            help='show list of available encoders',
            action='store_true'
        )
        subparser.set_defaults(func=self._list_cmd)

    def _add_run_cmd(self, subparsers: Any) -> None:
        subparser = subparsers.add_parser(
            'run',
            aliases=['r'],
            help='run tests for encoders'
        )
        subparser.add_argument(
            '-j',
            '--jobs',
            help='number of parallel jobs to use. 1x logical cores by default.'
            '0 means all logical cores',
            type=int,
            default=multiprocessing.cpu_count(),
        )
        subparser.add_argument(
            '-t',
            '--timeout',
            help='timeout in secs for each encoding. Default to 350 secs',
            type=int,
            default=350,
        )
        subparser.add_argument(
            '-ff',
            '--fail-fast',
            help='stop after the first fail',
            action='store_true',
        )
        subparser.add_argument(
            '-q',
            '--quiet',
            help="don't show every test run",
            action='store_true',
        )
        subparser.add_argument(
            '-al',
            '--asset-lists',
            help='run only the specific asset lists',
            nargs='+'
        )
        subparser.add_argument(
            '-a',
            '--assets',
            help='run only the specific assets',
            nargs='+',
        )
        subparser.add_argument(
            '-sa',
            '--skip-assets',
            help='skip the specific assets',
            nargs='+',
        )
        subparser.add_argument(
            '-e',
            '--encoders',
            help='run only the specific encoders',
            nargs='+',
        )
        # subparser.add_argument(
        #     '-s',
        #     '--summary',
        #     help='generate a summary in Markdown format for each asset list'
        #     action='store_true',
        # )
        # subparser.add_argument(
        #     '-so',
        #     '--summary-output',
        #     help='dump summary output to a file',
        # )
        # subparser.add_argument(
        #     '-f',
        #     '--format',
        #     help='specify the format of the summary file',
        #     choices=[x.value in SummaryFormat],
        #     default=SummaryFormat.MARKDOWN.value,
        # )
        subparser.add_argument(
            '-k',
            '--keep',
            help='keep output files generated during test',
            action='store_true',
        )
        subparser.add_argument(
            '-th',
            '--threshold',
            help='set exit code to 2 if threshold tests are not success. Otherwise, exit code is 0',
            type=int,
        )
        subparser.add_argument(
            '-tth',
            '--time-threshold',
            help='set exit code to 3 if asset lists takes longer than threshold seconds. '\
            'Otherwise, exit code is 0',
            type=float,
        )
        subparser.add_argument(
            '-v',
            '--verbose',
            help='show stdout and stderr of executed commands',
            action='store_true',
        )
        subparser.set_defaults(func=self._run_cmd)

    def _add_download_cmd(self, subparsers: Any) -> None:
        subparser = subparsers.add_parser(
            'download',
            aliases=['d'],
            help='download assets resources')
        subparser.add_argument(
            '-j',
            '--jobs',
            help='number of parallel jobs to use. 2x logical cores by default'
            '0 means all logical cores',
            type=int,
            default=2 * multiprocessing.cpu_count(),
        )
        subparser.add_argument(
            '-r',
            '--retries',
            help='number of retries before failing',
            type=int,
            default=1,
        )
        subparser.add_argument('--asset-lists', help='asset lists to download', nargs='*')
        subparser.set_defaults(func=self._download_cmd)

    @staticmethod
    def _list_cmd(args: Any, soothe: Soothe) -> None:
        soothe.list_asset_lists(
            show_assets=args.assets,
            asset_lists=args.asset_lists,
        )
        soothe.list_encoders(
            check=args.check,
            verbose=args.verbose,
        )

    @staticmethod
    def _run_cmd(args: Any, soothe: Soothe) -> None:
        args.jobs = args.jobs if args.jobs > 0 else multiprocessing.cpu_count()
        params = RunParams(
            jobs=args.jobs,
            asset_lists_names=args.asset_lists,
            timeout=args.timeout,
            encoders_names=args.encoders,
            assets_names=args.assets,
            skip_assets_names=args.skip_assets,
            fail_fast=args.fail_fast,
            quiet=args.quiet,
            keep_files=args.keep,
            threshold=args.threshold,
            time_threshold=args.time_threshold,
            verbose=args.verbose,
            # summary=args.summary or args.summary_output,
            # summary_output=args.summary_output,
            # summary_format=args.format,
        )
        try:
            soothe.run_test_suites(params)
        except SystemExit as ex:
            sys.exit(ex.code)

    @staticmethod
    def _download_cmd(args: Any, soothe: Soothe) -> None:
        args.jobs = args.jobs if args.jobs > 0 else multiprocessing.cpu_count()
        soothe.download_assets(
            asset_lists=args.asset_lists,
            jobs=args.jobs,
            retries=args.retries,
        )
