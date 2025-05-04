#!/bin/bash -ex

VMAF_VERSION="v3.0.0"
VMAF_URL="https://github.com/Netflix/vmaf/releases/download/${VMAF_VERSION}/vmaf"

BASE_DIR=$(dirname "$0")
VMAF_DIR="${BASE_DIR}/../resources"

[[ -f $VMAF_DIR/vmaf && -x $VMAF_DIR/vmaf ]] && exit 0

WGET=$(which wget | head)
[[ -f ${WGET} && -x ${WGET} ]] || (>&2 echo "This script needs `wget` command"; exit 255)

[[ -e "$VMAF_DIR" ]] || mkdir -p "$VMAF_DIR"

cd ${VMAF_DIR}
if ${WGET} --no-config ${VMAF_URL}; then
    chmod +x ./vmaf
fi
cd -
