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

"""Module with the encoder abstract class and the list of available encoders"""

from abc import abstractmethod
from functools import lru_cache
from shutil import which
from typing import List, Type

from .codec import Codec
from .utils import NamedClass, normalize_binary_cmd


class Encoder(NamedClass):
    """Abstract base class for encoders"""

    encoder_name: str = ""
    codec: Codec = Codec.NONE
    hw_acceleration: bool = False
    description: str = ""
    binary: str = ""

    def __init__(self) -> None:
        if self.binary:
            self.binary = normalize_binary_cmd(self.binary)

    @abstractmethod
    def encode(
            self,
            input_file: str,
            output_file: str,
            timeout: int,
            verbose: bool,
    ):
        """Encodes input_file in output_file"""
        raise NotImplementedError

    @lru_cache(maxsize=128)
    def check(self, verbose: bool) -> bool:
        """Checks whether the encoder can be ran"""
        if hasattr(self, "binary") and self.binary:
            path = which(self.binary)
            if verbose and not path:
                print(f'{self.binary} cannot be found in path')
            return path is not None
        return True

    def name(self) -> str:
        """Encoder's name"""
        return self.encoder_name

    def __str__(self) -> str:
        return f'{self.encoder_name}: {self.description}'


ENCODERS: List[Encoder] = []


def register_encoder(cls: Type[Encoder]) -> Type[Encoder]:
    """Register a new decoder implementation"""
    ENCODERS.append(cls())
    ENCODERS.sort(key=lambda enc: enc.encoder_name)
    return cls
