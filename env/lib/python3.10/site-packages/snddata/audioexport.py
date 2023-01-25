import os
import numpy as np
import soundfile as sf
from .disksnd import asdisksnd
from .audiofile import AudioFile

__all__ = ["available_formats", "available_subtypes",
           "saveasaudiofile", "saveasdisksnd"]

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
                       'MPC2K':'PCM_16',
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

def saveasaudiofile(filepath, s, format=None, subtype=None, endian=None,
                    startframe=None, endframe=None,
                    starttime=None, endtime=None,
                    startdatetime=None, enddatetime=None,
                    overwrite=False, channelindex=slice(None)):
    """
    Save sound object to an audio file.

    Parameters
    ----------
    s: Snd, DiskSnd, or AudioFile
    filepath
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
            subtype = defaultaudioformat
    if subtype is None:
        if isinstance(s, AudioFile):
            if s.fileformatsubtype in sf.available_subtypes(format):
                subtype = s.fileformatsubtype
        else:
             subtype = defaultaudiosubtype[format]

    # if subtype is None:
    #     subtype = defaultsubtype
    samplerate = int(round(s.fs))
    if os.path.exists(filepath) and not overwrite:
        raise IOError("File '{}' already exists; use 'overwrite'".format(filepath))
    startframe, endframe = s._check_episode(startframe=startframe,
                                            endframe=endframe,
                                            starttime=starttime,
                                            endtime=endtime,
                                            startdatetime=startdatetime,
                                            enddatetime=enddatetime)
    nchannels = len(np.ones([1, s.nchannels])[0, channelindex])
    with sf.SoundFile(file=filepath, mode='w', samplerate=samplerate,
                      channels=nchannels, subtype=subtype, endian=endian,
                      format=format) as f:
        for window in s.iterread_frames(framesize=samplerate,
                                        startframe=startframe,
                                        endframe=endframe,
                                        channelindex=channelindex):
            f.write(window)

    return AudioFile(filepath)


def saveasdisksnd(path, snd, dtype=None, metadata=None, mode='r',
                  startframe=None, endframe=None,
                  starttime=None, endtime=None,
                  startdatetime=None, enddatetime=None,
                  overwrite=False):
    startframe, endframe = snd._check_episode(startframe=startframe,
                                              endframe=endframe,
                                              starttime=starttime,
                                              endtime=endtime,
                                              startdatetime=startdatetime,
                                              enddatetime=enddatetime)
    arraygen = snd.iterread_frames(startframe=startframe, endframe=endframe)
    if dtype is None:
        dtype=snd.dtype
    if hasattr(snd, 'scalingfactor'):
        scalingfactor = snd.scalingfactor
    else:
        scalingfactor = None
    if metadata is None and hasattr(snd, 'metadata'):
        metadata = snd.metadata
    startdatetime = snd.frameindex_to_datetime(startframe)
    return asdisksnd(path=path, array=arraygen, fs=snd.fs, scalingfactor=scalingfactor,
                     startdatetime=startdatetime, dtype=dtype, metadata=metadata,
                     mode=mode, overwrite=overwrite)