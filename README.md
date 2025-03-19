# Soothe

Soothe is a testing framework written in Python for encoder quality. It's a
command line interface application that runs a number of test suites with the
supported encoders. Its purpose is to compare different encoder implementations
and configurations. It uses [VMAF](https://github.com/Netflix/vmaf) binary to
measure the transcoded videos.

## How to use it

### Clone the repository

```sh
git clone XXX
cd soothe
```

### Install vmaf

With Fedora you can install it via `dnf`:

```
sudo dnf install vmaf vmaf-models
```

Otherwise, you can download the binary via a script:

```
scritps/download_vmaf.sh
```

### Download assets

Assets are videos grouped in sets of common videos known as assets lists.

```
./soothe.py download
```

### Run tests

Right now there are two encoders available: dummy and GStreamer VA. Dummy just
copy the input video.

```
./soothe.py run
```

### List available assets lists and encoders

```
./soothe.py list
```
