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

"""Module to handle an asset list"""

import json
import os
import sys
import urllib.error

from dataclasses import dataclass
from multiprocessing import Pool
from typing import Any, Dict, List, Type

from .utils import NamedClass, file_checksum, download
from .asset import Asset


@dataclass
class DownloadWork:
    """Context to pass to each download worker"""
    out_dir: str
    verify: bool
    asset_list_name: str
    retries: int
    asset: Asset


@dataclass
class Content:
    """Class for keeping track of an asset list"""
    name: str
    description: str
    assets: Dict[str, Asset]


class AssetList(NamedClass):
    """Asset list class"""

    def __init__(
            self,
            filename: str,
            resources_dir: str,
            content: Content,
    ):
        self.filename = filename
        self.resources_dir = resources_dir
        self.content = content
        self.time_taken = 0.0

    @classmethod
    def from_json_file(
            cls: Type["AssetList"],
            filename: str,
            resources_dir: str
    ) -> "AssetList":
        """Create an AssetList instance from a file"""
        with open(filename, encoding="utf-8") as json_file:
            data = json.load(json_file)
            data["assets"] = dict(map(Asset.from_json, data["assets"]))
            return cls(filename, resources_dir, Content(**data))

    @staticmethod
    def _download_worker(ctx: DownloadWork) -> None:
        """Download and extract an asset"""
        asset = ctx.asset
        dest_dir = os.path.join(ctx.out_dir, ctx.asset_list_name)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, os.path.basename(asset.source))
        if ctx.verify and os.path.exists(dest_path):
            checksum = file_checksum(dest_path)
            if checksum == asset.checksum:
                return
        print(f'\tDownloading asset {asset.name} to {dest_dir}')
        # Catch the exception that download may throw to make sure pickle can
        # serialize it properly
        # This avoids:
        # Error sending result: '<multiprocessing.pool.ExceptionWithTraceback>'
        # Reason: 'TypeError("cannot pickle '_io.BufferedReader' object")'
        for i in range(ctx.retries):
            try:
                exception_str = ""
                download(asset.source, dest_dir)
            except urllib.error.URLError as ex:
                exception_str = f'Unable to download {asset.source} to '\
                    f'{dest_dir}: {str(ex)} (retry count={i + 1})'
                continue
            except OSError as ex:
                raise RuntimeError(f'Unable to store {asset.source} to '
                                   f'{dest_dir}: {str(ex)}') from ex
            break

        if exception_str:
            raise RuntimeError(exception_str)

        if asset.checksum != "__skip__":
            checksum = file_checksum(dest_path)
            if asset.checksum != checksum:
                raise RuntimeError(
                    f"Checksum error for test vector '{asset.name}': "
                    f"'{checksum}' instead of '{asset.checksum}'")

    def assets(self) -> List[Asset]:
        """Return the list of assets contained"""
        return list(self.content.assets.values())

    def name(self) -> str:
        """Return asset list name"""
        return self.content.name

    def download(
            self,
            jobs: int,
            out_dir: str,
            verify: bool,
            retries: int = 1,
    ) -> None:
        """Download the asset list"""
        os.makedirs(os.path.join(out_dir, self.content.name), exist_ok=True)

        with Pool(jobs) as pool:

            def _callback_error(err: Any) -> None:
                print(f'Error downloading: {err}')

            downloads = []

            print(f'Downloading test suite {self.content.name} use {jobs} '
                  f'parallel jobs')
            for asset in self.assets():
                dwork = DownloadWork(
                    out_dir,
                    verify,
                    self.content.name,
                    retries,
                    asset
                )
                downloads.append(
                    pool.apply_async(
                        self._download_worker,
                        args=(dwork,),
                        error_callback=_callback_error,
                    )
                )
            pool.close()
            pool.join()

        for job in downloads:
            if not job.successful():
                sys.exit("Some download failed")

        print('All downloads finished')

    def __str__(self) -> str:
        return (
            f'{self.content.name}: {self.content.description} — '
            f'{len(self.content.assets)} assets'
        )
