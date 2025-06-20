# Soothe - testing framework for encoders quality
# Copyright (C) 2020, Fluendo, S.A.
#  Author: Pablo Marcos Oltra <pmarcos@fluendo.com>, Fluendo, S.A.
#  Author: Andoni Morales Alastruey <amorales@fluendo.com>, Fluendo, S.A.
# Copyright (C) 2025, Igalia, S.L.
#  Author: Victor Jaquez <vjaquez@igalia.com>
#  Author: Stephane Cerveau <scerveau@igalia.com>
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

"""Module for Vulkan Video Samples based encoders"""

import shlex
import subprocess

from functools import lru_cache

from ..codec import Codec
from ..encoder import Encoder, register_encoder
from ..utils import normalize_binary_cmd, run_command

VKVS_ENC_TPL = "{} -c {} -i {} -o {} --profile {}"
VKVS_DEC_TPL = "{} -i {} -o {} --y4m --noPresent --enablePostProcessFilter 0"


class VKVS(Encoder):
    """Base class for Vulkan Video Samples encoders"""

    enc_cmd: str
    dec_cmd: str
    provider = 'VKVS'
    variant: str

    def __init__(self) -> None:
        super().__init__()
        self.encoder_name = f'{self.provider}-{self.codec.value}-'\
            f'{self.variant}'
        self.description = f'{self.provider} {self.codec.value}'\
            f' {self.variant} encoder'
        self.enc_cmd = normalize_binary_cmd('vk-video-enc-test')
        self.dec_cmd = normalize_binary_cmd('vk-video-dec-test')

    def codec_name(self, codec: Codec) -> str:
        """Generate the codec name"""
        if codec == Codec.H264:
            return 'h264'
        if codec == Codec.H265:
            return 'h265'
        if codec == Codec.AV1:
            return 'av1'
        return 'unknown'

    def _construct_enc_cmd(
            self,
            input_file: str,
            output_file: str,
    ) -> str:
        """Generate the VKVS command used to encode the asset"""
        return VKVS_ENC_TPL.format(
            self.enc_cmd,
            self.codec_name(self.codec),
            input_file,
            output_file,
            self.variant
        )

    def _construct_dec_cmd(
            self,
            input_file: str,
            output_file: str,
    ) -> str:
        """Generate the VKVS command used to decode the asset"""
        return VKVS_DEC_TPL.format(
            self.dec_cmd,
            input_file,
            output_file
        )

    @lru_cache(maxsize=128)
    def check(self, verbose: bool) -> bool:
        """Check if VKVS decoder is valid"""
        try:
            enc_cmd = f"{self.enc_cmd} --help"
            run_command(shlex.split(enc_cmd), verbose=verbose)
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
        encoded_file = f"{output_file}.enc"
        enc_cmd = self._construct_enc_cmd(input_file, encoded_file)
        run_command(shlex.split(enc_cmd), timeout=timeout, verbose=verbose)
        dec_cmd = self._construct_dec_cmd(encoded_file, output_file)
        run_command(shlex.split(dec_cmd), timeout=timeout, verbose=verbose)


@register_encoder
class VKVSH264MainEncoder(VKVS):
    """Vulkan Video samples H.264 Main encoder"""
    codec = Codec.H264
    variant = "main"


@register_encoder
class VKVSH265MainEncoder(VKVS):
    """VKVS H.265 Main encoder"""
    codec = Codec.H265
    variant = "main"


@register_encoder
class VKVSAV1MainEncoder(VKVS):
    """VKVS AV1 Main encoder"""
    codec = Codec.AV1
    variant = "main"
