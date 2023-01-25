import numpy as np
import soundfile as sf
from pathlib import Path

from .disksnd import asdisksnd
from .audiofile import AudioFile
#from .utils import isgenerator

__all__ = ["available_formats", "available_subtypes",
           "toaudiofile", "todisksnd", 'tosnd']

defaultaudioformat = 'WAV'
defaultaudiosubtype = {'AIFF': 'FLOAT',
                       'AU': 'FLOAT',
                       'AVR': 'PCM_16',
                       'CAF': 'FLOAT',
                       'FLAC': 'PCM_24',
                       'HTK': 'PCM_16',
                       'IRCAM': 'FLOAT',
                       'MAT4': 'FLOAT',
                       'MAT5': 'FLOAT',
                       'MPC2K': 'PCM_16',
                       'NIST': 'PCM_32',
                       'OGG': 'VORBIS',
                       'PAF': 'PCM_24',
                       'PVF': 'PCM_32',
                       'RAW': 'FLOAT',
                       'RF64': 'FLOAT',
                       'SD2': 'PCM_24',
                       'SDS': 'PCM_24',
                       'SVX': 'PCM_16',
                       'VOC': 'PCM_16',
                       'W64': 'FLOAT',
                       'WAV': 'FLOAT',
                       'WAVEX': 'FLOAT',
                       'WVE': 'ALAW',
                       'XI': 'DPCM_16'}

available_formats = sf.available_formats
available_subtypes = sf.available_subtypes


#FIXME all funcs should accept generators

def toaudiofile(path, s, format=None, subtype=None, endian=None,
                startframe=None, endframe=None,
                starttime=None, endtime=None,
                startdatetime=None, enddatetime=None,
                overwrite=False, channelindex=slice(None)):
    """
    Save sound object to an audio file.

    Parameters
    ----------
    s: Snd, DiskSnd, or AudioFile
    path
    format
    subtype
    endian
    startframe: {int, None}
        The index of the frame at which the exported sound should start.
        Defaults to None, which means the start of the sound (index 0).
    endframe: {int, None}
        The index of the frame at which the exported sound should start.
        Defaults to None, which means the start of the sound (index 0).
    starttime
    endtime
    startdatetime
    enddatetime
    overwrite
    channelindex

    Returns
    -------
    AudioFile object

    """
    if format is None:
        if isinstance(s, AudioFile):
            format = s.fileformat
        else:
            format = defaultaudioformat
            subtype = defaultaudiosubtype[defaultaudioformat]
    if subtype is None:
        if isinstance(s, AudioFile):
            if s.fileformatsubtype in sf.available_subtypes(format):
                subtype = s.fileformatsubtype
        else:
            subtype = defaultaudiosubtype[format]

    # if subtype is None:
    #     subtype = defaultsubtype
    samplerate = round(s.fs)
    path = Path(path)
    if path.exists() and not overwrite:
        raise IOError(
            "File '{}' already exists; use 'overwrite'".format(path))
    startframe, endframe = s._check_episode(startframe=startframe,
                                            endframe=endframe,
                                            starttime=starttime,
                                            endtime=endtime,
                                            startdatetime=startdatetime,
                                            enddatetime=enddatetime)
    nchannels = len(np.ones([1, s.nchannels])[0, channelindex])
    with sf.SoundFile(file=path, mode='w', samplerate=samplerate,
                      channels=nchannels, subtype=subtype, endian=endian,
                      format=format) as f:
        for window in s.iterread_frames(blocklen=samplerate,
                                        startframe=startframe,
                                        endframe=endframe,
                                        channelindex=channelindex):
            f.write(window)

    return AudioFile(path)


def todisksnd(path, s, dtype=None, metadata=None, mode='r',
              startframe=None, endframe=None,
              starttime=None, endtime=None,
              startdatetime=None, enddatetime=None,
              overwrite=False):
    startframe, endframe = s._check_episode(startframe=startframe,
                                            endframe=endframe,
                                            starttime=starttime,
                                            endtime=endtime,
                                            startdatetime=startdatetime,
                                            enddatetime=enddatetime)
    arraygen = s.iterread_frames(startframe=startframe, endframe=endframe)
    if dtype is None:
        dtype = s.dtype
    if hasattr(s, 'scalingfactor'):
        scalingfactor = s.scalingfactor
    else:
        scalingfactor = None
    if metadata is None and hasattr(s, 'metadata'):
        metadata = s.metadata
    startdatetime = s.frameindex_to_datetime(startframe)
    return asdisksnd(path=path, array=arraygen, fs=s.fs,
                     scalingfactor=scalingfactor,
                     startdatetime=startdatetime, dtype=dtype,
                     metadata=metadata,
                     accessmode=mode, overwrite=overwrite)


def tosnd(s, startframe=None, endframe=None, starttime=None, endtime=None,
          startdatetime=None, enddatetime=None, channelindex=slice(None),
          dtype=None):
    s.read(startframe=startframe, endframe=endframe, starttime=starttime,
           endtime=endtime, startdatetime=startdatetime,
           enddatetime=enddatetime, channelindex=channelindex, dtype=dtype)
