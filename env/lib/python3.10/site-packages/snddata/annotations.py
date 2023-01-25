from .utils import read_json, write_json

__all__ =['create_sndannotations','SndAnnotations']


class SndAnnotations(object):

    def __init__(self, filepath):

        self.filepath = filepath
        self._annotations = self._read(filepath)

    def __getitem__(self, item):
        return self._annotations[item]

    def __len__(self):
        return len(self._annotations)

    def __str__(self):
        s =  'sequence no, annotation, start time, end time\n'
        s += '---------------------------------------------\n'
        for i, (anno, starttime, endtime) in enumerate(self._annotations):
            s += f'{i}, "{anno}", {starttime}, {endtime}\n'
        return s

    def _read(self, path):
        annodict = read_json(path)
        if not annodict.get('sndlabclass', None) == self.__class__.__name__:
            raise TypeError(f"'{path}' does not contain SndAnnotations "
                            f"data")
        return annodict['annotations']

    def _write(self, path=None, overwrite=False):
        if path is None:
            path = self.filepath
        datadict = {'sndlabclass': SndAnnotations.__name__,
                'annotations': self._annotations}
        write_json(datadict=datadict, path=path, overwrite=overwrite,
                   indent=1)

    def sort_starttime(self):
        self._annotations.sort(key=lambda item: item[1])
        self._write(overwrite=True)

    def sort_endtime(self):
        self._annotations.sort(key=lambda item: item[2])
        self._write(overwrite=True)

    def sort_annotation(self):
        self._annotations.sort(key=lambda item: item[0])
        self._write(overwrite=True)

    def append(self, annotation, starttime=None, endtime=None):
        if not isinstance(annotation, basestring):
            raise TypeError("'annotation' should be text")
        self._annotations.append((annotation, starttime, endtime))
        self._write(overwrite=True)

    def save_as(self, filepath, overwite=False):
        self._write(filepath, overwrite=overwite)


def create_sndannotations(path, overwrite=False):

    datadict = {'sndlabclass': SndAnnotations.__name__,
                'annotations': []}
    write_json(datadict, path=path, overwrite=overwrite)
    return SndAnnotations(path)




