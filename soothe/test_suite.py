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

"""Test Suite - a set of tests"""

import os

from dataclasses import dataclass
from multiprocessing import Pool
from pathlib import Path
from shutil import rmtree
from time import perf_counter
from typing import List, Tuple

from soothe.asset import Asset
from soothe.encoder import Encoder
from soothe.test import Test, Params as TestParams, Result as TestResult

@dataclass
class Params: # pylint: disable=too-many-instance-attributes
    """Params for a test suite"""
    name: str
    jobs: int
    assets: List[Tuple[str, Asset]]
    timeout: int
    fail_fast: bool
    quiet: bool
    vmaf_binary: Path
    resources_dir: str
    output_dir: str
    keep_files: bool = False
    verbose: bool = False

class TestSuite: # pylint: disable=too-few-public-methods
    """
    Test suite class.
    A test suite is one encoder encoding multiple assets
    """

    def __init__(self, params: Params):
        self.params = params
        self.output_dir = os.path.join(params.output_dir, params.name)
        self.time = 0.0
        self.num_results = 0

    def _generate_tests(self, encoder: Encoder) -> List[Test]:
        tests = []
        for asset in self.params.assets:
            tests.append(
                Test(TestParams(
                    encoder = encoder,
                    asset = asset,
                    vmaf_binary = self.params.vmaf_binary,
                    resources_dir = self.params.resources_dir,
                    output_dir = self.params.output_dir,
                    timeout = self.params.timeout,
                    keep_files = self.params.keep_files,
                    verbose = self.params.verbose,
                ))
            )

        return tests

    def _run_worker(self, test: Test) -> TestResult:
        """Run one test"""
        test_result = TestResult()
        test.run(test_result)
        return test_result

    def _run_test_suite_in_parallel (self, tests: List[Test]) -> None:
        """Run the tests suite in parallel"""

        test_results: List[TestResult] = []
        with Pool(self.params.jobs) as pool:

            def _callback(test_result: TestResult) -> None:
                print(test_result, flush=True)
                if self.params.fail_fast:
                    pool.terminate()
                test_results.append(test_result)

            start = perf_counter()
            for test in tests:
                pool.apply_async(self._run_worker, (test,), callback=_callback)

            pool.close()
            pool.join()

        self.time = perf_counter() - start
        self.num_results = len(test_results)

    def run(self, encoder: Encoder) -> None:
        """
        Run the test suite.
        Returns a new copy of the test suite with results of the test
        """

        if not encoder.check(self.params.verbose):
            print(f'Skipping encoder {encoder.name} because it cannot run')
            return

        self.params.output_dir = os.path.join(self.params.output_dir, self.params.name)
        if os.path.exists(self.params.output_dir):
            rmtree(self.params.output_dir)
        os.makedirs(self.params.output_dir)

        tests = self._generate_tests(encoder)

        print(f'Running {self.params.name} [{len(tests)} tests] for encoder {encoder.name()}')
        self._run_test_suite_in_parallel(tests)
        print(f'Ran {self.num_results} tests in {self.time:.3f} secs\n')
