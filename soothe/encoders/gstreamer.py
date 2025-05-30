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

"""Module for GStreamer-based encoders"""

import shlex
import subprocess

from functools import lru_cache

from ..codec import Codec
from ..encoder import Encoder, register_encoder
from ..utils import normalize_binary_cmd, run_command

PIPELINE_TPL = "{} --eos-on-shutdown --no-fault filesrc location={} ! "\
    "y4mdec ! videoconvert dither=none ! "\
    "{} ! decodebin ! "\
    "videoconvert dither=none ! y4menc ! filesink location={}"


class GStreamer(Encoder):
    """Base class for GStreamer encoders"""

    cmd: str
    encoder_bin: str
    api: str
    provider = 'GStreamer'
    variant: str

    def __init__(self) -> None:
        super().__init__()
        self.encoder_name = f'{self.provider}-{self.codec.value}-'\
            f'{self.variant}-{self.api}-Gst1.0'
        self.description = f'{self.provider} {self.codec.value} '\
            f'{self.variant} {self.api} encoder for GStreamer 1.0'
        self.cmd = normalize_binary_cmd('gst-launch-1.0')

    def _construct_pipeline(
            self,
            input_file: str,
            output_file: str,
    ) -> str:
        """Generate the GStreamer pipeline used to encode the asset"""
        return PIPELINE_TPL.format(
            self.cmd,
            input_file,
            self.encoder_bin,
            output_file
        )

    @lru_cache(maxsize=128)
    def check(self, verbose: bool) -> bool:
        """Check if GStreamer decoder is valid (better than gst-inspect)"""
        try:
            binary = normalize_binary_cmd('gst-launch-1.0')
            pipeline = f"{binary} --no-fault "\
                f"appsrc num-buffers=0 ! {self.encoder_bin} ! fakesink"
            run_command(shlex.split(pipeline), verbose=verbose)
        except FileNotFoundError as e:
            print("Executable not found:", e)
            return False
        except subprocess.CalledProcessError as e:
            print("Process failed:", e)
            return False
        return True

    def encode(
            self,
            input_file: str,
            output_file: str,
            timeout: int,
            verbose: bool,
    ):
        """Encodes input_file in output_file"""

        pipeline = self._construct_pipeline(input_file, output_file)
        run_command(shlex.split(pipeline), timeout=timeout, verbose=verbose)


@register_encoder
class GStreamerVaH264MainEncoder(GStreamer):
    """GStreamer H.264 Main VA encoder"""
    codec = Codec.H264
    encoder_bin = " vah264enc ! video/x-h264, profile=main "
    variant = "main"
    api = "VA"


@register_encoder
class GStreamerVaH264HighEncoder(GStreamer):
    """GStreamer H.264 High VA encoder"""
    codec = Codec.H264
    encoder_bin = " vah264enc ! video/x-h264, profile=high "
    variant = "high"
    api = "VA"


@register_encoder
class GStreamerVaH264ConstrainedEncoder(GStreamer):
    """GStreamer H.264 Constrained baseline VA encoder"""
    codec = Codec.H264
    encoder_bin = " vah264enc ! video/x-h264, profile=constrained-baseline "
    variant = "constrained-baseline"
    api = "VA"


@register_encoder
class GStreamerVaH264LpMainEncoder(GStreamer):
    """GStreamer H.264 low power Main VA encoder"""
    codec = Codec.H264
    encoder_bin = " vah264lpenc ! video/x-h264, profile=main "
    variant = "lp-main"
    api = "VA"


@register_encoder
class GStreamerVaH264LpHighEncoder(GStreamer):
    """GStreamer H.264 low power High VA encoder"""
    codec = Codec.H264
    encoder_bin = " vah264lpenc ! video/x-h264, profile=high "
    variant = "lp-high"
    api = "VA"


@register_encoder
class GStreamerVaH264LpConstrainedEncoder(GStreamer):
    """GStreamer H.264 low power Constrained baseline VA encoder"""
    codec = Codec.H264
    encoder_bin = " vah264lpenc ! video/x-h264, profile=constrained-baseline "
    variant = "lp-constrained-baseline"
    api = "VA"


@register_encoder
class GStreamerVaH265MainEncoder(GStreamer):
    """GStreamer H.265 Main VA encoder"""
    codec = Codec.H265
    encoder_bin = " vah265enc ! video/x-h265, profile=main "
    variant = "main"
    api = "VA"


@register_encoder
class GStreamerVaH265LpMainEncoder(GStreamer):
    """GStreamer H.265 low power Main VA encoder"""
    codec = Codec.H265
    encoder_bin = " vah265lpenc ! video/x-h265, profile=main "
    variant = "lp-main"
    api = "VA"


@register_encoder
class GStreamerVaVp9LpEncoder(GStreamer):
    """GStreamer VP9 low power VA encoder"""
    codec = Codec.VP9
    encoder_bin = " vavp9lpenc ! video/x-vp9 "
    variant = "lp"
    api = "VA"
