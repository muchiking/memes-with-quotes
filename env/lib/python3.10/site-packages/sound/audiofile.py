from contextlib import contextmanager
import soundfile as sf
from .ramsnd import BaseSnd

__all__ = ["AudioFile"]

#FIXME we want to consolidate disksnd and audiofile in one class




# FIXME append?
# FIXME SoundFile can view things?
class AudioFile(BaseSnd):

    _classid = 'AudioFile'
    _classdescr = 'Disk-based (i.e. non-disk) sound in audio format'
    _version = '0.1'

    """
    readdtype must be one of ['float32', 'float64', 'int16', 'int32']
    
    """

    def __init__(self, filepath, readdtype='float64', startdatetime='NaT',
                 mode='r'):

        self.filepath = filepath
        self._mode = mode
        self._readdtype = readdtype
        with sf.SoundFile(filepath) as f:
            #nframes = f.seek(0, sf.SEEK_END)
            nframes = len(f)
            nchannels = f.channels
            fs = f.samplerate
            self.fileformat = f.format
            self.fileformatsubtype = f.subtype
        super(self.__class__, self).__init__(nframes=nframes,
                                             nchannels=nchannels, fs=fs,
                                             startdatetime=startdatetime,
                                             dtype=readdtype)
        self._fileobj = None

    @property
    def mode(self):
        return self._mode

    @property
    def readdtype(self):
        return self._readdtype

    @contextmanager
    def _openfile(self, mode=None):
        if mode is None:
            mode = self._mode
        if self._fileobj is not None:
            yield self._fileobj
        else:
            try:
                with sf.SoundFile(self.filepath, mode=mode) as fileobj:
                    self._fileobj = fileobj
                    yield fileobj
            except:
                raise
            finally:
                self._fileobj = None


    @contextmanager
    def open(self):
        with self._openfile():
            yield None

    def set_readdtype(self, dtype):
        self._readdtype = dtype

    def set_mode(self, mode):
        if not mode in {'r', 'r+'}:
            raise ValueError(f"'mode' must be 'r' or 'r+', not '{mode}'")
        self._mode = mode

    @contextmanager
    def view_frames(self, startframe=0, endframe=None,
                    channelindex=slice(None)):
        yield self.read_frames(startframe=startframe, endframe=endframe,
                                channelindex=channelindex)

    def read_frames(self, startframe=0, endframe=None,
                    channelindex=slice(None), dtype=None):
        if dtype is None:
            dtype=self.readdtype
        startframe, endframe = self._check_episode(startframe=startframe,
                                                   endframe=endframe,
                                                   starttime=None,
                                                   endtime=None)
        with self._openfile() as f:
            f.seek(startframe)
            return f.read(endframe-startframe, dtype=dtype,
                          always_2d=True)[:,channelindex]
