# Soothe - testing framework for encoders quality
# Copyright (C) 2020, Fluendo, S.A.
#  Author: Pablo Marcos Oltra <pmarcos@fluendo.com>, Fluendo, S.A.
#  Author: Andoni Morales Alastruey <amorales@fluendo.com>, Fluendo, S.A.
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

"""Utilities module"""

import hashlib
import os
import platform
import random
import shutil
import subprocess
import time
import urllib.request
import sys

from abc import abstractmethod, ABC
from pty import openpty
from threading import Lock
from typing import Any, List, Optional, Sequence

download_lock = Lock()

def download(url: str, dest_dir: str, max_retries: int = 5) -> None:
    """Downloads a file to a directory with a mutex lock to avoid conflicts and
    retries with exponential backoff"""
    for attempt in range(max_retries):
        done = False
        try:
            with download_lock:
                with urllib.request.urlopen(url) as response:
                    dest_path = os.path.join(dest_dir, url.split('/')[-1])
                    with open(dest_path, 'wb') as dest:
                        shutil.copyfileobj(response, dest)
            done = True
        except urllib.error.URLError as ex:
            if attempt < max_retries - 1:
                wait_time = random.uniform(1, 2**attempt)
                time.sleep(wait_time)
            else:
                raise urllib.error.URLError(reason=ex.reason) from ex
        if done:
            break

def file_checksum(path: str) -> str:
    """Calculates checksum of a file reading chunks of 64K"""
    md5 = hashlib.md5()
    with open(path, 'rb') as f:
        chunk = f.read(65536)
        while chunk:
            md5.update(chunk)
            chunk = f.read(65536)
    return md5.hexdigest()

def run_command(
        command: List[str],
        verbose: bool = False,
        check: bool = True,
        timeout: Optional[int] = None,
) -> None:
    """Runs a command"""
    out = subprocess.DEVNULL if not verbose else None
    err = subprocess.DEVNULL if not verbose else None

    if verbose:
        print(f'Running command "{" ".join(command)}"')

    try:
        subprocess.run(
            command,
            stdout=out,
            stderr=err,
            check=check,
            timeout=timeout)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as ex:
        # Developer experience improvement (facilitates copy/paste)
        ex.cmd = " ".join(ex.cmd)
        raise ex

def run_command_with_output(
        command: List[str],
        verbose: bool = False,
        check: bool = True,
        timeout: Optional[int] = None,
) -> str:
    """Runs a command and returns std output trace"""
    if verbose:
        print(f'Runnig command "{" ".join(command)}"')

    m_fd, s_fd = openpty()
    try:
        with subprocess.Popen(
            command,
            stderr=s_fd,
            stdout=s_fd,
        ) as proc:
            proc.communicate(timeout=timeout)

        out = os.read(m_fd, 1024).decode('utf-8').strip()
        os.close(m_fd)
        os.close(s_fd)

        if verbose and out:
            print(out)

        return out or ""
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as ex:
        if verbose and ex.output:
            # Workaround inconsistent Python implementation
            if isinstance(ex, subprocess.TimeoutExpired):
                print(ex.output)
            else:
                print(ex.output)

        if isinstance(ex, subprocess.CalledProcessError) and not check:
            return ex.output or ""

        # Developer experience improvement (facilitates copy/paste)
        ex.cmd = " ".join(ex.cmd)
        raise ex

def normalize_binary_cmd(cmd: str) -> str:
    """Return the OS-form binary"""
    if platform.system() == "Windows":
        return cmd if cmd.endswith(".exe") else cmd + ".exe"
    if cmd.endswith(".exe"):
        return cmd.replace(".exe", "")
    return cmd

def normalize_path(path: str) -> str:
    """Normalize the path to make it Unix-like"""
    if platform.system() == "Windows":
        return path.replace("\\", "/")
    return path

class NamedClass(ABC): # pylint: disable=too-few-public-methods
    """Abstract class for classes with name"""
    @abstractmethod
    def name(self) -> str:
        """Name of the class"""
        raise NotImplementedError

def get_matches_from_list(
        in_list: Optional[List[str]],
        check_list: Sequence[NamedClass],
        name: str
) -> Sequence[Any]:
    """Function that gets a list of objects with the name specified by in_list from check_list"""
    if in_list:
        in_list_names = { x.lower() for x in in_list }
        check_list_names = { x.name().lower() for x in check_list }
        matches = in_list_names & check_list_names
        if len(matches) != len(in_list):
            sys.exit(f"No {name} found for: {', '.join(in_list_names - check_list_names)}")

        return [ x for x in check_list if x.name().lower() in matches ]
    return check_list
