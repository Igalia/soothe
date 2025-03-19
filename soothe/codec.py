# Soothe - testing framework for encoders quality
# Copyright (C) 2020, Fluendo, S.A.
#  Author: Pablo Marcos Oltra <pmarcos@fluendo.com>, Fluendo, S.A.
# Copyright (C) 2025, Igalia, S.A.
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

"""Codec module"""

from enum import Enum

class Codec(Enum):
    """Codec type"""

    NONE = "None"
    DUMMY = "Dummy"
    H264 = "H.264"
    H265 = "H.265"
    H266 = "H.266"
    VP8 = "VP8"
    VP9 = "VP9"
    AV1 = "AV1"
    MPEG2_VIDEO = "MPEG2_VIDEO"

    def __str__(self) -> str:
        return self.value
