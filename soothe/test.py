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

"""Test module"""

import os

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from subprocess import TimeoutExpired
from time import perf_counter
from typing import Optional, Tuple

from soothe.asset import Asset
from soothe.encoder import Encoder
from soothe.utils import normalize_path, run_command_with_output

@dataclass
class Params:
    """Params for a test"""
    encoder: Encoder
    asset: Tuple[str, Asset]
    vmaf_binary: Path
    resources_dir: str
    output_dir: str
    timeout: int
    keep_files: bool = False
    verbose: bool = False

class EncodeTestResult(Enum):
    """Encode test result"""

    NOT_RUN = "Not Run"
    SUCCESS = "Success"
    FAIL = "Fail"
    TIMEOUT = "Timeout"
    ERROR = "Error"

@dataclass
class Result:
    """Test result class"""

    asset_fname: Optional[str] = None
    encoder_name: Optional[str] = None
    encode_time: float = 0.0
    encode_result: EncodeTestResult = EncodeTestResult.NOT_RUN
    vmaf_result: EncodeTestResult = EncodeTestResult.NOT_RUN
    vmaf_score: float = 0.0
    vmaf_time: float = 0.0

    def __str__(self):
        s = f'{self.encoder_name} — {self.asset_fname} '
        if self.encode_result is not EncodeTestResult.SUCCESS:
            return  f'{s} → Encode {self.encode_result.value}'
        if self.vmaf_result is not EncodeTestResult.SUCCESS:
            return f'{s} → VMAF {self.vmaf_result.value}'
        time = self.encode_time + self.vmaf_time
        return f'{s} [{time:.3f}s] → {self.vmaf_score:.5f}'

class Test: # pylint: disable=too-few-public-methods
    """Test class"""

    def __init__(self, params: Params):
        self.params = params

    def run(self, result: Result) -> None:
        """Run the test"""

        output_filepath = os.path.join(
            self.params.output_dir,
            self.params.asset[1].name + ".y4m"
        )
        input_filepath = os.path.join(
            self.params.resources_dir,
            self.params.asset[0],
            self.params.asset[1].filename,
        )
        output_filepath = normalize_path(output_filepath)
        input_filepath = normalize_path(input_filepath)

        result.asset_fname = self.params.asset[1].filename
        result.encoder_name = self.params.encoder.name()

        try:
            start = perf_counter()
            self.params.encoder.encode(
                input_filepath,
                output_filepath,
                self.params.timeout,
                self.params.verbose,
            )
            result.encode_time = perf_counter() - start
        except TimeoutExpired:
            result.encode_result = EncodeTestResult.TIMEOUT
            raise
        except:
            result.encode_result = EncodeTestResult.ERROR
            raise
        finally:
            result.encode_result = EncodeTestResult.SUCCESS

        if result.encode_result is EncodeTestResult.SUCCESS:
            cmd = [
                str(self.params.vmaf_binary),
                '--quiet',
                '--reference',
                input_filepath,
                '--distorted',
                output_filepath
            ]
            try:
                start = perf_counter()
                output = run_command_with_output(
                    command=cmd,
                    verbose=self.params.verbose,
                )
                result.vmaf_time = perf_counter() - start
            except:
                result.vmaf_result = EncodeTestResult.ERROR
                raise
            finally:
                try:
                    result.vmaf_score = float(output.split(':')[1])
                    result.vmaf_result = EncodeTestResult.SUCCESS
                except (IndexError, ValueError):
                    result.vmaf_result = EncodeTestResult.FAIL

        if not self.params.keep_files \
           and os.path.exists(output_filepath) \
           and os.path.isfile(output_filepath):
            os.remove(output_filepath)
