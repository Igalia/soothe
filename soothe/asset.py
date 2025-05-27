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

"""Module that holds an asset"""

from typing import Any, Type


class Asset:
    """Asset class"""

    def __init__(
            self,
            name: str,
            source: str,
            checksum: str,
            filename: str,
    ):
        # JSON members
        self.name = name
        self.source = source
        self.checksum = checksum
        self.filename = filename

        # Not in JSON
        self.test_time = 0.0

    @classmethod
    def from_json(cls: Type["Asset"], data: Any) -> Any:
        """Deserialize an instance of Asset from json file"""
        return (data["name"], cls(**data))

    def __str__(self) -> str:
        return self.filename
