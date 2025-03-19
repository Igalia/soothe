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

"""Main soothe module"""

import os

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from shutil import which
from typing import Iterator, List, Optional, Tuple

from soothe.asset import Asset
from soothe.asset_list import AssetList
from soothe.encoder import ENCODERS
from soothe.test_suite import TestSuite, Params as TestSuiteParams
from soothe.utils import get_matches_from_list

# Import decoders that will auto-register
from soothe.encoders import * # noqa: F403 pylint: disable=wildcard-import disable=unused-wildcard-import

@dataclass
class RunParams: # pylint: disable=too-many-instance-attributes
    """Context for run command"""
    jobs: int
    asset_lists_names: List[str]
    timeout: int
    encoders_names: List[str]
    assets_names: List[str]
    skip_assets_names: List[str]
    fail_fast: bool = False
    quiet: bool = False
    keep_files: bool = False
    threshold: Optional[int] = None
    time_threshold: Optional[int] = None
    verbose: bool = False
    #summary: bool = False
    #summary_output: str
    #summary_formart: str

    def as_test_suite_params(
            self,
            name: str,
            assets: List[Tuple[str, Asset]],
            vmaf_binary: Path,
            resources_dir: str,
            output_dir: str,
    ) -> TestSuiteParams:
        """Convert RunParams TestSuiteParams"""

        return TestSuiteParams(
            name = name,
            jobs = self.jobs,
            assets = assets,
            timeout = self.timeout,
            fail_fast = self.fail_fast,
            quiet = self.quiet,
            vmaf_binary = vmaf_binary,
            resources_dir = resources_dir,
            output_dir = output_dir,
            keep_files = self.keep_files,
            verbose = self.verbose,
        )

class Soothe:
    """Main class for soothe"""

    def __init__(
            self,
            assets_dir: str,
            resources_dir: str,
            output_dir: str,
            verbose: bool = False,
    ):
        self.assets_dir = assets_dir
        self.resources_dir = resources_dir
        self.output_dir = output_dir
        self.asset_lists: List[AssetList] = []
        self.verbose = verbose
        self.vmaf_binary: Optional[Path] = None
        if self.verbose:
            print(
                f"NOTE: Internal dirs used:\n"
                f" * assets_dir: {self.assets_dir}\n"
                f" * resources_dir: {self.resources_dir}"
            )

    def _check_vmaf(self) -> bool:
        """Check whether vmaf can be ran"""
        if self.vmaf_binary:
            return True

        for path in [None, self.resources_dir]:
            vmaf_path = which('vmaf', path=path)
            if vmaf_path:
                self.vmaf_binary = Path(vmaf_path)
                return True

        return False

    def _walk_assets_dir(self) -> Iterator[Tuple[str, List[str], List[str]]]:
        for asset_dir in self.assets_dir.split(os.pathsep):
            for root, dirnames, files in os.walk(asset_dir):
                yield (root, dirnames, files)

    @lru_cache(maxsize=128)
    def _load_asset_lists(self) -> None:
        for root, _, files in self._walk_assets_dir():
            for f in files:
                if os.path.splitext(f)[1] == '.json':
                    try:
                        asset_list = AssetList.from_json_file(
                            os.path.join(root, f),
                            self.resources_dir)
                        if asset_list.content.name in [ a.content.name for a in self.asset_lists ]:
                            raise RuntimeError(f'Repeated asset list with '\
                                               f'"{asset_list.content.name}"')
                        self.asset_lists.append(asset_list)
                    except (OSError, ValueError, LookupError) as ex:
                        print(f'Error loading asset list from {f}: {ex}')
        if len(self.asset_lists) == 0:
            raise RuntimeError(f'No assets found in "{self.assets_dir}"')

    def download_assets(self, asset_lists: List[str], jobs: int, retries: int) -> None:
        """Download a group of assets"""
        self._load_asset_lists()
        download_asset_lists = get_matches_from_list(
            asset_lists,
            self.asset_lists,
            "Asset Lists",
        )

        for asset_list in download_asset_lists:
            asset_list.download(
                jobs,
                self.resources_dir,
                verify=True,
                retries=retries)

    def _generate_assets(self, params: RunParams) -> Tuple[str, List[Tuple[str, Asset]]]:
        """
        Generate the list of assets given a set of asset lists, filtering
        the explicit assets and removing the skipped assets.
        """
        self._load_asset_lists()

        asset_lists = get_matches_from_list(
            params.asset_lists_names,
            self.asset_lists,
            "asset lists",
        )

        assets = [ (asset_list.name(), asset) for asset_list in asset_lists
                   for asset in asset_list.assets() ]
        if params.assets_names:
            assets = [asset for asset in assets if asset[1].name in params.assets_names ]
        if params.skip_assets_names:
            assets = [ asset for asset in assets if asset[1].name not in params.skip_assets_names ]
        if len(assets) == 0:
            raise RuntimeError('No defined assets to tests')

        test_suite_name = '-'.join([ asset_list.name() for asset_list in asset_lists ])

        return (test_suite_name, assets)

    def run_test_suites(self, params: RunParams) -> None:
        """
        Run all the test suites for each encoder
        (test suite == asset list per encoder)
        """
        self._check_vmaf()
        if not self.vmaf_binary:
            raise RuntimeError('No VMAF binary')

        encoders = get_matches_from_list(
            params.encoders_names,
            ENCODERS,
            "encoders",
        )
        if len(encoders) == 0:
            raise RuntimeError('No encoders to test')


        (test_suite_name, assets) = self._generate_assets(params)
        test_suite = TestSuite(
            params.as_test_suite_params(
                test_suite_name,
                assets,
                self.vmaf_binary,
                self.resources_dir,
                self.output_dir
            )
        )
        for encoder in encoders:
            test_suite.run(encoder)

    def list_asset_lists(
            self,
            show_assets: bool = False,
            asset_lists: Optional[List[str]] = None,
    ) -> None:
        """List all asset lists"""
        self._load_asset_lists()
        print('\nList of available asset lists:')
        if asset_lists:
            asset_lists = [ x.lower() for x in asset_lists ]

        for asset_list in self.asset_lists:
            if asset_lists and asset_list.name().lower() not in asset_lists:
                continue
            print(f'\t{asset_list}')
            if show_assets:
                for asset in asset_list.assets():
                    print(f'\t\t{asset}')
        if len(self.asset_lists) == 0:
            print(f"\tNo asset lists found in '{self.assets_dir}'")

    def list_encoders(
            self,
            check: bool,
            verbose: bool,
    ) -> None:
        """List all the available encoders"""
        print('\nList of available encoders:')
        for encoder in ENCODERS:
            string = f'{encoder}'
            if check:
                string += ' … ' + (
                    '✓' if encoder.check(verbose) else '𐄂'
                )
            print(f'\t{string}')
