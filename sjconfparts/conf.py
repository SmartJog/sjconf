from sjconfparts.type import *
from sjconfparts.exceptions import *
import os, re, ConfigParser, errno

class Conf(dict):

    class Error(Error):
        pass

    class ListError(Error):
        pass

    class ListValueAlreadyExistError(ListError):
        def __init__(self, section, key, value):
            self.msg = "The value \"%s\" is already in key %s of section %s" % (value, section, key)

    class ListExistInParentError(ListError):
        def __init__(self, section, key, conf_parent):
            self.msg = 'The key "%s" in section "%s" does not exist in local configuration, but exist in %s configuration. To force, first set the value to "" before adding to the list' % (key, section, conf_parent)

    class UnauthorizedSection(Error):
        def __init__(self, section, conf_file):
            self.msg = 'Unauthorized section "%s": all sections should be either "%s" or "%s:<subsection>"' % (section, conf_file, conf_file)

    class ConfSection(dict):
        def __init__(self, dictionary = {}):
            dict.__init__(self, dictionary)
            self.types = {}
            if 'get_type' in dir(dictionary):
                for key in dictionary:
                    type = dictionary.get_type(key)
                    if type != None:
                        self.set_type(self, key, dictionary.get_type(key))

        def __delitem__(self, key):
            dict.__delitem__(self, key)
            if key in self.types:
                del self.types[key]

        def _find_type(self, key):
            type = None
            search_result = re.compile('(.*)_([^_]+)$').search(key)
            if search_result:
                key_tmp = search_result.group(1)
                type = search_result.group(2)
                if key_tmp in self.types and type == self.types[key_tmp][0]:
                    key = key_tmp
                else:
                    type = None
            return key, type

        def __getitem__(self, key):
            key, type = self._find_type(key)
            value = dict.__getitem__(self, key)
            if type:
                value = self.types[key][1]
            elif key in self.types:
                value = Type.convert(self.types[key][0], 'str', self.types[key][1])
                dict.__setitem__(self, key, value)
            return value

        def __setitem__(self, key, value):
            key, type = self._find_type(key)
            if type:
                self.types[key][1] = value
                value = Type.convert(self.types[key][0], 'str', value)
            elif key in self.types:
                self.types[key][1] = Type.convert('str', self.types[key][0], value)
            dict.__setitem__(self, key, value)

        def set_type(self, key, type):
            self.types[key] = (type, Type.convert('str', type, self[key]))

        def get_type(self, key):
            # Raise KeyError in key not defined
            self[key]
            if key in self.types:
                type = self.types[key][0]
            else:
                type = None
            return type

    def __init__(self, dictionary = {}, file_path = None, conf_section_class = ConfSection):
        self.conf_section_class = conf_section_class
        dict.__init__({})
        self.file_path = file_path
        self.comments = None
        if self.file_path:
            self.load()
        elif dictionary:
            self.load_from_dict(dictionary)

    def __setitem__(self, key, value):
        if value.__class__ != self.conf_section_class:
            value = self.conf_section_class(value)
        dict.__setitem__(self, key, self.conf_section_class(value))

    def update(self, other_dict):
        for section in other_dict:
            if section in self:
                self[section].update(other_dict[section])
            else:
                if other_dict[section].__class__ != self.conf_section_class:
                    value = self.conf_section_class(other_dict[section])
                else:
                    value = other_dict[section]
                self[section] = value

    def load_from_dict(self, dictionary):
        for section in dictionary:
            self[section] = self.conf_section_class(dictionary[section])

    def load(self, file_path = None):
        if not file_path:
            file_path = self.file_path
        # Configuration file loader
        if os.path.isdir(file_path) and file_path.endswith('.conf'):
            raise IOError(errno.EISDIR, "%s: %s" % (self.file_path, os.strerror(errno.EISDIR)))
        if not os.path.isdir(file_path) and not file_path.endswith('.conf'):
            raise IOError(errno.ENOTDIR, "%s: %s" % (self.file_path, os.strerror(errno.ENOTDIR)))
        if os.path.isdir(file_path):
            files_path = map(lambda file_name: file_path + '/' + file_name, os.listdir(file_path))
        else:
            files_path = (file_path,)
        for file_path in files_path:
            if not file_path.endswith('.conf'):
                continue
            if not os.path.exists(file_path):
                raise IOError(errno.ENOENT, "%s: %s" % (self.file_path, os.strerror(errno.ENOENT)))
            elif os.path.isdir(file_path):
                raise IOError(errno.EISDIR, "%s: %s" % (self.file_path, os.strerror(errno.EISDIR)))
            cp = ConfigParser.ConfigParser()
            cp.read(file_path)
            for section in cp.sections():
                self[section] = self.conf_section_class(cp.items(section))

    def save(self, output_file = None):
        if not output_file:
            output_file = self.file_path
        if not hasattr(output_file, 'write'):
            output_file = open(output_file, "w")
        if self.comments != None and len(self.comments) > 0:
            for comment in self.comments.split('\n'):
                output_file.write('# ' + comment + '\n')
            output_file.write('\n')
        cp = ConfigParser.ConfigParser()
        for section in self:
            cp.add_section(section)
            for key in self[section]:
                cp.set(section, key, self[section][key])
        cp.write(output_file)

    def set_type(self, section, key, type):
        self[section].set_type(key, type)

    def get_type(self, section, key):
        return self[section].get_type(key)
