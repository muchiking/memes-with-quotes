from contextlib import contextmanager
import numpy as np

from .utils import duration_string, check_episode, iter_timewindowindices

__all__ = ['RamSnd']


# FIXME all output becomes a generator?

class BaseSnd(object):
    _timeaxis = 0
    _channelaxis = 1

    """Subclasses have to implement 'open', 'view_frames', and 
    'read_frames' methods."""

    def __init__(self, nframes, nchannels, fs, dtype, startdatetime='NaT'):

        self.nframes = nframes
        self.nchannels = nchannels
        self.fs = fs
        self.dt = 1 / float(fs)
        self.dtype = dtype
        self.startdatetime = np.datetime64(startdatetime)

    @property
    def duration(self):
        return self.nframes * self.dt

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
        if self.nchannels == 1:
            chstr = "channel"
        else:
            chstr = "channels"
        return f'{self._classid} <{totdur}, {self.fs} Hz, {self.nchannels} {chstr}>'

    __repr__ = __str__

    def _check_episode(self, startframe=None, endframe=None, starttime=None,
                       endtime=None, startdatetime=None, enddatetime=None):
        return check_episode(startframe=startframe, endframe=endframe,
                             starttime=starttime, endtime=endtime,
                             startdatetime=startdatetime,
                             enddatetime=enddatetime,
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
            raise ValueError(f"'where' argument should be either 'start', "
                             f"'center', or 'end', not '{where}'")

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
            time = np.round(np.asanyarray(time) * 1e9).astype(
                'timedelta64[ns]')
            return self.startdatetime + time

    @contextmanager
    def open(self):
        yield None

    def view_frames(self, startframe=0, endframe=None,
                    channelindex=slice(None)):
        raise NotImplementedError('This method should be implemented in a '
                                  'subclass and not used directly on a '
                                  'BaseSound')

    def read_frames(self, startframe=0, endframe=None,
                    channelindex=slice(None)):
        raise NotImplementedError('This method should be implemented in a '
                                  'subclass and not used directly on a '
                                  'BaseSound')

    def iterview_frames(self, blocklen=44100, stepsize=None,
                        include_remainder=True, startframe=None, endframe=None,
                        channelindex=slice(None)):
        startframe, endframe = self._check_episode(startframe=startframe,
                                                   endframe=endframe)
        with self.open():
            for windowstart, windowend in iter_timewindowindices(
                    ntimeframes=self.nframes,
                    framesize=blocklen,
                    stepsize=stepsize,
                    include_remainder=include_remainder,
                    startindex=startframe,
                    endindex=endframe):
                with self.view_frames(startframe=windowstart,
                                      endframe=windowend,
                                      channelindex=channelindex) as ar:
                    yield ar

    def iterread_frames(self, blocklen=44100, stepsize=None,
                        include_remainder=True, startframe=None, endframe=None,
                        channelindex=slice(None), dtype=None):
        i = 0
        for ar in self.iterview_frames(blocklen=blocklen, stepsize=stepsize,
                                       include_remainder=include_remainder,
                                       startframe=startframe,
                                       endframe=endframe,
                                       channelindex=channelindex):
            yield np.array(ar, copy=True, dtype=dtype)

    @contextmanager
    def view(self, startframe=None, endframe=None, starttime=None,
             endtime=None, startdatetime=None, enddatetime=None,
             channelindex=slice(None)):
        startframe, endframe = self._check_episode(startframe=startframe,
                                                   endframe=endframe,
                                                   starttime=starttime,
                                                   endtime=endtime,
                                                   startdatetime=startdatetime,
                                                   enddatetime=enddatetime)
        with self.view_frames(startframe=startframe, endframe=endframe,
                              channelindex=channelindex) as frames:
            startdatetime = self.frameindex_to_datetime(startframe,
                                                        where='start')
            metadata = getattr(self, 'metadata', {})
            s = RamSnd(samples=frames, fs=self.fs,
                       timeaxis=self._timeaxis,
                       nchannels=self.nchannels,
                       startdatetime=startdatetime,
                       metadata=metadata)
            s.starttime = startframe / float(self.fs)
            yield s

    def read(self, startframe=None, endframe=None, starttime=None,
             endtime=None, startdatetime=None, enddatetime=None,
             channelindex=slice(None), dtype=None):
        with self.view(startframe=startframe, endframe=endframe,
                       starttime=starttime, endtime=endtime,
                       startdatetime=startdatetime,
                       enddatetime=enddatetime,
                       channelindex=channelindex) as s:
            if (dtype is not None) and np.issubdtype(dtype, s._array.dtype):
                s._array = s._array.astype(dtype)
            if s._array.base is not None:
                s._array = s._array.copy()
        return s

    def iterread(self, blocklen=44100, stepsize=None, include_remainder=True,
                 startframe=None, endframe=None, starttime=None, endtime=None,
                 startdatetime=None, enddatetime=None,
                 channelindex=slice(None),
                 copy=False):
        startframe, endframe = self._check_episode(startframe=startframe,
                                                   endframe=endframe,
                                                   starttime=starttime,
                                                   endtime=endtime,
                                                   startdatetime=startdatetime,
                                                   enddatetime=enddatetime)
        nread = 0
        nwindow = 0
        metadata = getattr(self, 'metadata', {})
        for window in self.iterread_frames(blocklen=blocklen,
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
                                np.timedelta64(int(elapsedsec * 1e9), 'ns')
            yield RamSnd(samples=window, fs=self.fs,
                         startdatetime=startdatetime, starttime=elapsedsec,
                         startframe=nread, nwindow=nwindow,
                         metadata=metadata)
            nread += window.shape[0]
            nwindow += 1


class RamSnd(BaseSnd):
    _classid = 'Snd'
    _classdescr = 'RAM-based (i.e. non-disk) sound'
    _version = '0.1'

    def __init__(self, samples, fs, startdatetime='NaT', **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)
        self.extraattrs = sorted(kwargs.keys())
        self._array = samples
        nframes, nchannels = samples.shape[0], samples.shape[1]
        #self.dtype = samples.dtype
        BaseSnd.__init__(self, nframes=nframes, nchannels=nchannels, fs=fs,
                         dtype=samples.dtype, startdatetime=startdatetime)

    @property
    def samplingtimes(self):
        return ((np.arange(self.nframes, dtype=np.float64) + 0.5) * self.dt)

    @contextmanager
    def open(self):
        yield None

    #do we really need this?
    @contextmanager
    def view_frames(self, startframe=0, endframe=None,
                    channelindex=slice(None)):
        yield self._array[slice(startframe, endframe), channelindex]

    def read_frames(self, startframe=0, endframe=None,
                    channelindex=slice(None), dtype=None, order='K', ndmin=0):
        frames = self._array[slice(startframe, endframe), channelindex]
        return np.array(frames, copy=True, dtype=dtype, order=order,
                        ndmin=ndmin)
# 
# class SecMemSnd(BaseSnd):
#     raise NotImplementedError()
# 
# 
# class SndView(BaseSnd):
#     raise NotImplementedError()
# 
