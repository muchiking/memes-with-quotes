import os
from contextlib import contextmanager
import numpy as np
import soundfile as sf
from .snd import Snd
from .utils import duration_string, check_episode, iter_timewindowindices

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
        rs = Snd(samples=frames, fs=self.fs,
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
            yield Snd(samples=window, fs=self.fs,
                         startdatetime=startdatetime, starttime=elapsedsec,
                         startframe=nread, nwindow=nwindow)
            nread += window.shape[0]
            nwindow += 1

    # fixme make this separate function
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


