import numpy as np
import os.path

from diskarray.diskarray import asdiskarray, create_diskarray, DiskArray
from diskarray.diskarray import BaseDir, create_basedir

from .snd import BaseSnd

__all__ = ['asdisksnd', 'create_disksnd', 'DiskSnd']

# scalingfactor
class DiskSnd(BaseDir, BaseSnd):

    _sndarraydir = 'array'
    _sndmetadatafilename = 'sndmetadata.json'
    _sndmetadatakeys = ('fs', 'startdatetime', 'scalingfactor')
    _classid = 'DiskSnd'
    _classdescr = 'Disk-based (i.e. non-RAM) sound'
    _version = "0.1.0"

    def __init__(self, path, mode='r'):
        BaseDir.__init__(self, path=path)
        self._sndarraypath = os.path.join(path, self._sndarraydir)
        self._diskarray = da = DiskArray(path=self._sndarraypath, mode=mode)
        self._sndmetadatapath = os.path.join(path, self._sndmetadatafilename)
        self._sndmetadata = self._read_jsondict(self._sndmetadatafilename,
                                          requiredkeys=self._sndmetadatakeys)
        nframes = da.shape[0]
        nchannels = da.shape[1]
        fs = self._sndmetadata['fs']
        startdatetime = self._sndmetadata['startdatetime']
        BaseSnd.__init__(self, nframes=nframes, nchannels=nchannels, fs=fs,
                         dtype=da.dtype, startdatetime=startdatetime)

    def read_frames(self, startframe=0, endframe=None,
                    channelindex=slice(None)):
        return self._diskarray.values[startframe:endframe, channelindex]

    def set_startdatetime(self, startdatetime):
        md = self._sndmetadata.copy()
        md['startdatetime'] = str(np.datetime64(startdatetime))
        self._write_jsondict(filename=self._sndmetadatapath, d=md, overwrite=True)


    def copy(self, path, dtype=None, chunksize=None, mode='r', overwrite=False):
        if not os.path.exists(path):
            os.makedirs(path)
        else:
            raise IOError('{} already exist, remove first'.format(path))
        sndarraypath = os.path.join(path, self._sndarraydir)
        DiskArray.copy(path=sndarraypath, dtype=dtype, chunksize=chunksize,
                       mode=mode)
        mdp = os.path.join(path, self._sndmetadatafilename)
        self._write_jsondict(filename=mdp, d=self._sndmetadata)
        return DiskSnd(path=path)

    # fixme: minmax
    def toint8(self, path, chunksize=None, mode='r'):

        minval, maxval = self.minmax()
        absmax = max(abs(minval), abs(maxval))
        intlim = min(abs(np.iinfo(np.int8).min), np.iinfo(np.int8).max)
        mfactor = intlim/float(absmax)
        if chunksize is None:
            chunksize = 1024 * 100
        chunklen = max(chunksize // np.product(self.shape[1:]), 1)
        gen = ((c*mfactor).astype(np.int8)
               for c in self.iter_chunks(chunklen=chunklen))
        return asdisksnd(path=path, array=gen, fs=self.fs,
                         scalingfactor=1/mfactor, metadata=self.metadata,
                         dtype=np.int8, mode=mode)


# fixme adapt audio import to this
# fixme next two functions together?


def asdisksnd(path, array, fs, scalingfactor=None, startdatetime='NaT',
              dtype=None, metadata=None, mode='r'):
    bd = create_basedir(dirname=path, classname='DiskSnd',
                        classversion=DiskSnd._version,
                        readmetxt=None)
    sndarraypath = os.path.join(path, DiskSnd._sndarraydir)
    asdiskarray(path=sndarraypath, array=array, dtype=dtype,
                mode=mode)
    sndmetadata = {'fs': fs,
                   'scalingfactor': scalingfactor,
                   'startdatetime': startdatetime}
    bd._write_jsondict(DiskSnd._sndmetadatafilename, d=sndmetadata)
    return DiskSnd(path=path, mode=mode)




def create_disksnd(path, nframes, nchannels, fs, startdatetime='NaT',
                   dtype='float32', fill=None, fillfunc=None, mode='r+',
                   chunksize=1024 * 1024, metadata=None, scalingfactor=None):

    shape = (nframes, nchannels)
    sndmetadata = {'fs': fs,
                   'scalingfactor': scalingfactor,
                   'startdatetime': startdatetime}

    bd = create_basedir(dirname=path, classname='DiskSnd',
                        classversion=DiskSnd._version,
                        readmetxt=None)
    sndarraypath = os.path.join(path, DiskSnd._sndarraydir)
    dar = create_diskarray(path=sndarraypath, shape=shape, dtype=dtype,
                           fill=fill, fillfunc=fillfunc,  metadata=metadata,
                           mode=mode, chunksize=chunksize)
    bd._write_jsondict(name=DiskSnd._sndmetadatafilename, d=sndmetadata,
                        requiredkeys=DiskSnd._sndmetadatakeys)
    return DiskSnd(path=bd.path, mode=mode)
