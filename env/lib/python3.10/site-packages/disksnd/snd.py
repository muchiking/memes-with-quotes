import os
from contextlib import contextmanager
import numpy as np
import soundfile as sf
from .utils import duration_string, check_episode, iter_timewindowindices
from .annotations import SndAnnotations, create_sndannotations

__all__ = ['AudioFile', 'MemSnd']


class BaseSnd(object):

    _timeaxis = 0
    _channelaxis = 1

    """Subclasses have to implement a 'read_frames' method and can implement
    an 'open' method."""

    def __init__(self, nframes, nchannels, fs, dtype, startdatetime='NaT'):

        self.nframes = nframes
        self.nchannels = nchannels
        self.fs = fs
        self.dt = 1 / float(fs)
        self.dtype = dtype
        self.startdatetime = np.datetime64(startdatetime)

    @property
    def duration(self):
        return self.nframes *self.dt

    @property
    def enddatetime(self):
        return self.frameindex_to_datetime(self.nframes, where='end')

    @property
    def startepochtime(self):
        if str(self.startdatetime) == "NaT":
            return None
        else:
            return (np.datetime64(self.startdatetime) -
                    np.datetime64('1970-01-01T00:00:00')) / \
                   np.timedelta64(1, 's')

    @property
    def endepochtime(self):
        if str(self.startdatetime) == "NaT":
            return None
        else:
            return self.startepochtime + self.duration

    def __str__(self):
        totdur = duration_string(self.nframes * self.dt)
        return '{} <{}, {} Hz, {} channels>'.format(self._classid,
                                                    totdur, self.fs,
                                                    self.nchannels)

    __repr__ = __str__

    def _check_episode(self, startframe=None, endframe=None, starttime=None,
                       endtime=None, startdatetime=None, enddatetime=None):
        return check_episode(startframe=startframe, endframe=endframe,
                             starttime=starttime, endtime=endtime,
                             startdatetime=startdatetime, enddatetime=enddatetime,
                             fs=self.fs, nframes=self.nframes,
                             originstartdatetime=self.startdatetime)

    def frameindex_to_sndtime(self, frameindex, where='start'):
        frameindex = np.asanyarray(frameindex)
        if where == 'start':
            return frameindex * self.dt
        elif where == 'center':
            return (0.5 + frameindex) * self.dt
        elif where == 'end':
            return (1 + frameindex) * self.dt
        else:
            raise ValueError("'where' argument should be either 'start', "
                             "'center', or 'end', not '{}'".format(where))

    def frameindex_to_epochtime(self, frameindex, where='start'):
        epochtime = self.startepochtime
        if epochtime is not None:
            return self.frameindex_to_sndtime(frameindex, where=where) + \
                   epochtime
        else:
            return None


    def frameindex_to_datetime(self, frameindex, where='start'):
        sndtime = self.frameindex_to_sndtime(frameindex=frameindex,
                                             where=where)
        if str(self.startdatetime) == "NaT":
            return np.datetime64('NaT')
        else:
            return self.startdatetime + \
                   np.round(sndtime * 1e9).astype('timedelta64[ns]')

    def sndtime_to_datetime(self, time):
        if str(self.startdatetime) == "NaT":
            return None
        else:
            time = np.round(np.asanyarray(time)*1e9).astype('timedelta64[ns]')
            return self.startdatetime + time

    @contextmanager
    def open(self):
        yield None

    def read_frames(self, startframe=0, endframe=None,
                    channelindex=slice(None)):
        raise NotImplementedError('This method should be implemented in a '
                                  'subclass and not used directly on a '
                                  'BaseSound')

    def iterread_frames(self, framesize=44100, stepsize=None,
                        include_remainder=True, startframe=None, endframe=None,
                        channelindex=slice(None)):
        startframe, endframe = self._check_episode(startframe=startframe,
                                                   endframe=endframe)
        with self.open():
            for windowstart, windowend in iter_timewindowindices(
                    ntimeframes=self.nframes,
                    framesize=framesize,
                    stepsize=stepsize,
                    include_remainder=include_remainder,
                    startindex=startframe,
                    endindex=endframe):
                yield self.read_frames(startframe=windowstart,
                                       endframe=windowend,
                                       channelindex=channelindex)

    def read(self, startframe=None, endframe=None, starttime=None,
             endtime=None, startdatetime=None, enddatetime=None,
             channelindex=slice(None), dtype=None, copy=False):
        startframe, endframe = self._check_episode(startframe=startframe,
                                                   endframe=endframe,
                                                   starttime=starttime,
                                                   endtime=endtime,
                                                   startdatetime=startdatetime,
                                                   enddatetime=enddatetime)
        frames = self.read_frames(startframe=startframe, endframe=endframe,
                                  channelindex=channelindex)
        if (dtype is not None) and (dtype is not frames.dtype):
            frames = frames.astype(dtype)
        elif copy:
            frames = frames.copy()
        startdatetime = self.frameindex_to_datetime(startframe, where='start')
        rs = MemSnd(samples=frames, fs=self.fs,
                    timeaxis=self._timeaxis,
                    nchannels=self.nchannels,
                    startdatetime=startdatetime)
        rs.starttime = startframe / float(self.fs)
        return rs

    def iterread(self, framesize=44100, stepsize=None, include_remainder=True,
                 startframe=None, endframe=None, starttime=None, endtime=None,
                 startdatetime=None, enddatetime=None, channelindex=slice(None),
                 copy=False):
        startframe, endframe = self._check_episode(startframe=startframe,
                                                   endframe=endframe,
                                                   starttime=starttime,
                                                   endtime=endtime,
                                                   startdatetime=startdatetime,
                                                   enddatetime=enddatetime)
        nread = 0
        nwindow = 0
        for window in self.iterread_frames(framesize=framesize,
                                           stepsize=stepsize,
                                           include_remainder=include_remainder,
                                           startframe=startframe,
                                           endframe=endframe,
                                           channelindex=channelindex):
            if copy:
                window = window.copy()
            elapsedsec = (nread + startframe) * self.dt
            if str(self.startdatetime) == 'NaT':
                startdatetime = 'NaT'
            else:
                startdatetime = self.startdatetime + \
                                np.timedelta64(int(elapsedsec*1e9), 'ns')
            yield MemSnd(samples=window, fs=self.fs,
                         startdatetime=startdatetime, starttime=elapsedsec,
                         startframe=nread, nwindow=nwindow)
            nread += window.shape[0]
            nwindow += 1

    def export_audio(self, filepath, subtype=None, endian=None, format=None,
                     startframe=None, endframe=None,
                     starttime=None, endtime=None,
                     startdatetime=None, enddatetime=None,
                     overwrite=False, channelindex=slice(None)):
        """
        This class method is based on the PySoundFile library. See its
        documentation for details (http://pysoundfile.readthedocs.org/) on the
        'subtype', 'endian', and 'format' arguments.

        Parameters
        ----------
        filepath
        subtype
        endian
        format
        startframe: {int, None}
            The index of the frame at which the exported sound should start.
            Defaults to None, which means the start of the sound (index 0).
        endframe: {int, None}
            The index of the frame at which the exported sound should start.
            Defaults to None, which means the start of the sound (index 0).
        starttime
        endtime
        overwrite
        channelindex

        Returns
        -------
        None

        """
        # if format is None:
        #     format = DEFAULTAUDIOFORMAT
        # if subtype is None:
        #     subtype = DEFAULTSUBTYPE
        samplerate = int(round(self.fs))
        if os.path.exists(filepath) and not overwrite:
            raise IOError("File '{}' already exists; use 'overwrite'".format(filepath))
        startframe, endframe = self._check_episode(startframe=startframe,
                                                   endframe=endframe,
                                                   starttime=starttime,
                                                   endtime=endtime,
                                                   startdatetime=startdatetime,
                                                   enddatetime=enddatetime)
        nchannels = len(np.ones([1,self.nchannels])[0,channelindex])
        with sf.SoundFile(file=filepath, mode='w', samplerate=samplerate,
                          channels=nchannels, subtype=subtype, endian=endian,
                          format=format) as f:
            for window in self.iterread_frames(framesize=samplerate,
                                               startframe=startframe,
                                               endframe=endframe,
                                               channelindex=channelindex):
                f.write(window)
        return AudioFile(filepath)



class MemSnd(BaseSnd):

    _classid = 'MemSnd'
    _classdescr = 'RAM-based (i.e. non-disk) sound'
    _version = '0.1'

    def __init__(self, samples, fs, startdatetime='NaT', **kwargs):
        self._array = samples
        nframes, nchannels = samples.shape[0], samples.shape[1]
        self.dtype = samples.dtype
        for name, value in kwargs.items():
            setattr(self, name, value)
        self.extraattrs = sorted(kwargs.keys())
        BaseSnd.__init__(self, nframes=nframes, nchannels=nchannels, fs=fs,
                         dtype=samples.dtype, startdatetime=startdatetime)

    @property
    def samplingtimes(self):
        return ((np.arange(self.nframes, dtype=np.float64) + 0.5) * self.dt)

    def read_frames(self, startframe=0, endframe=None,
                    channelindex=slice(None)):
        return self._array[slice(startframe, endframe), channelindex]


class AudioFile(BaseSnd):

    def __init__(self, filepath, dtype='float64', startdatetime='NaT',
                 mode='r'):

        self.filepath = filepath
        self.mode = mode
        with sf.SoundFile(filepath) as f:
            nframes = f.seek(0, sf.SEEK_END)
            nchannels = f.channels
            fs = f.samplerate
        super(self.__class__, self).__init__(nframes=nframes,
                                             nchannels=nchannels, fs=fs,
                                             dtype=dtype,
                                             startdatetime=startdatetime)
        self._fileobj = None
        self.isopen = False

    @contextmanager
    def open(self, mode=None):
        if mode is None:
            mode = self.mode
        if self.isopen:
            yield self._fileobj
        else:
            with sf.SoundFile(self.filepath, mode=mode) as fileobj:
                yield fileobj

    def read_frames(self, startframe=0, endframe=None,
                    channelindex=slice(None)):
        startframe, endframe = self._check_episode(startframe=startframe,
                                                   endframe=endframe,
                                                   starttime=None,
                                                   endtime=None)
        with self.open() as f:
            f.seek(startframe)
            return f.read(endframe-startframe, dtype=self.dtype,
                          always_2d=True)

    # fixme implement
    def to_disksnd(self):
        pass