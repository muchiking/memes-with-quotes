import os
import numpy as np
from soundfile import SoundFile
from .darrsnd import asdarrsnd
from .audiofile import AudioFile

# FIXME os to pathlib

__all__ = ['audiofile_to_disksnd', 'audiofiles_to_disksnd',
           'audiodir_to_disksnd']


def _list_audiofiles(audiodir, extensions=('.wav', '.WAV'), filenames=None):
    if not filenames is None:
        # FIXME there could be some checks here
        paths = filenames
    else:
        audiofiles = [f for f in os.listdir(audiodir)
                      if (os.path.isfile(os.path.join(audiodir, f))
                          and os.path.splitext(f)[1] in extensions)]
        paths = sorted(audiofiles)
    fullpaths = [os.path.join(audiodir, f) for f in paths]
    if len(fullpaths) == 0:
        raise IOError(
            "there are no ({}) files in {}".format(extensions, audiodir))
    nchannelss = []
    fss = []
    sizes = []
    for path in fullpaths:
        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(
            path)
        with SoundFile(path, 'r') as f:
            nchannelss.append(f.channels)
            fss.append(f.samplerate)
            sizes.append(size)
    return fullpaths, paths, fss, nchannelss, sizes

# FIXME non-numpy way
def _allfilessamenchannels(nchannelss):
    nchannels = nchannelss[0]
    if not (np.array(nchannelss) == nchannels).all():
        raise ValueError(
            'not all audio files have the same number of channels')
    return nchannels

# FIXME non-numpy way
def _allfilessamefs(fss):
    fs = fss[0]
    if not (np.array(fss) == fs).all():
        raise ValueError('not all audio files have the same sampling rate')
    return fs


# fixme
def audiodir_to_disksnd(importdir, sndpath,
                        extensions=('.wav', '.WAV'),
                        dtype='float32', scalingfactor=None,
                        startdatetime='NaT', metadata=None, framesize=44100,
                        overwrite=False):
    # fixme not necessary
    fullpaths, filenames, fss, nchannelss, sizes = _list_audiofiles(
        audiodir=importdir,
        extensions=extensions)
    nchannels = _allfilessamenchannels(nchannelss)
    fs = _allfilessamefs(fss)
    return audiofiles_to_disksnd(audiofilepaths=fullpaths, sndpath=sndpath,
                                 dtype=dtype, scalingfactor=scalingfactor,
                                 startdatetime=startdatetime, metadata=metadata,
                                 framesize=framesize, overwrite=overwrite)


def audiofiles_to_disksnd(audiofilepaths, sndpath, dtype='float32',
                          scalingfactor=None, startdatetime='NaT',
                          metadata=None, framesize=44100, mode='r',
                          overwrite=False):
    snd = audiofile_to_disksnd(audiofilepath=audiofilepaths[0], sndpath=sndpath,
                               dtype=dtype,
                               scalingfactor=scalingfactor,
                               startdatetime=startdatetime, metadata=metadata,
                               framesize=framesize, mode='r+',
                               overwrite=overwrite)
    for afp in audiofilepaths[1:]:
        af = AudioFile(filepath=afp, readdtype=dtype, mode='r')
        assert af.nchannels == snd.nchannels
        assert af.fs == snd.fs
        snd._diskarray.iterappend(af.iterread_frames(blocklen=framesize))
    return snd


def audiofile_to_disksnd(audiofilepath, sndpath, dtype='float32',
                         startframe=None, endframe=None,
                         scalingfactor=None, startdatetime='NaT',
                         metadata=None, framesize=44100, mode='r',
                         overwrite=False):
    af = AudioFile(filepath=audiofilepath, mode='r')
    gen = af.iterread_frames(blocklen=framesize, stepsize=None,
                             include_remainder=True, startframe=startframe,
                             endframe=endframe)
    snd = asdarrsnd(path=sndpath, array=gen, fs=af.fs, dtype=dtype,
                    startdatetime=startdatetime, metadata=metadata,
                    accessmode=mode, overwrite=overwrite)
    return snd

