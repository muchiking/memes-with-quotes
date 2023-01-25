from contextlib import contextmanager

from darr import asarray, create_array, Array, \
    delete_array

from .ramsnd import BaseSnd

__all__ = ['asdarrsnd', 'create_darrsnd', 'delete_darrsnd', 'DarrSnd']

# scalingfactor
# append?
class DarrSnd(BaseSnd):

    _classid = "DiskSnd"

    def __init__(self, path, accessmode='r'):
        self._diskarray = a = Array(path=path, accessmode=accessmode)
        self.metadata = metadata = a.metadata
        nframes = a.shape[0]
        nchannels = a.shape[1]
        fs = metadata['fs']
        startdatetime = metadata['startdatetime']
        BaseSnd.__init__(self, nframes=nframes, nchannels=nchannels, fs=fs,
                         dtype=a.dtype, startdatetime=startdatetime)

    @contextmanager
    def view_frames(self, startframe=0, endframe=None,
                    channelindex=slice(None)):
        """Returns a memmap view of samples

        """
        with self._diskarray.open() as ar:
            yield ar[startframe:endframe, channelindex]

    def read_frames(self, startframe=0, endframe=None,
                    channelindex=slice(None)):
        """Returns a copy of samples

        """
        return self._diskarray[startframe:endframe, channelindex]

    def set_startdatetime(self, startdatetime):
        self._diskarray.metadata.update(startdatetime=startdatetime)


    def copy(self, path, dtype=None, accessmode='r', chunksize=44100,
             overwrite=False):
        return self._diskarray.copy(path=path, dtype=dtype, chunklen=chunksize,
                                    accessmode=accessmode, overwrite=overwrite)

# fixme adapt audio import to this


def asdarrsnd(path, array, fs, scalingfactor=None, startdatetime='NaT',
              dtype=None, metadata=None, accessmode='r', overwrite=False):
    da  = asarray(path=path, array=array, dtype=dtype, metadata=metadata,
                      accessmode=accessmode, overwrite=overwrite)
    da.accessmode = 'r+'
    sndmetadata = {'fs': fs,
                   'scalingfactor': scalingfactor,
                   'startdatetime': str(startdatetime)}
    da.metadata.update(sndmetadata)
    da.accessmode = accessmode
    return DarrSnd(path=path, accessmode=accessmode)

def create_darrsnd(path, nframes, nchannels, fs, startdatetime='NaT',
                   dtype='float32', fill=None, fillfunc=None, accessmode='r+',
                   chunksize=1024 * 1024, metadata=None, scalingfactor=None,
                   overwrite=False):
    shape = (nframes, nchannels)
    da = create_array(path=path, shape=shape,
                   dtype=dtype, fill=fill, fillfunc=fillfunc, accessmode=accessmode,
                   chunklen=chunksize, metadata=metadata, overwrite=overwrite)

    sndmetadata = {'fs': fs,
                   'scalingfactor': scalingfactor,
                   'startdatetime': startdatetime}
    da.metadata.update(sndmetadata)
    return DarrSnd(path=path, accessmode=accessmode)


def delete_darrsnd(ds):
    """
    Delete DiskSnd data from disk.

    Parameters
    ----------
    path: path to data directory

    """
    delete_array(ds._diskarray)