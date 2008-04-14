from sjconfparts.type import *
import os, re, ConfigParser, errno

class Conf(dict):
    class ConfSection(dict):
        def __init__(self, dictionnary):
            dict.__init__(self, dictionnary)
            self.types = {}
            if 'get_type' in dir(dictionnary):
                for key in dictionnary:
                    type = dictionnary.get_type(key)
                    if type != None:
                        self.set_type(self, key, dictionnary.get_type(key))

        def __delitem__(self, key):
            dict.__delitem__(self, key)
            if key in self.types:
                del self.types[key]

        def __find_type(self, key):
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
            key, type = self.__find_type(key)
            value = dict.__getitem__(self, key)
            if type:
                value = self.types[key][1]
            elif key in self.types:
                value = apply(getattr(Type, self.types[key][0] + '_to_str'), [self.types[key][1]])
                dict.__setitem__(self, key, value)
            return value

        def __setitem__(self, key, value):
            key, type = self.__find_type(key)
            if type:
                self.types[key][1] = value
                value = apply(getattr(Type, self.types[key][0] + '_to_str'), [value])
            elif key in self.types:
                self.types[key][1] = apply(getattr(Type, 'str_to_' + self.types[key][0]), [value])
            dict.__setitem__(self, key, value)

        def set_type(self, key, type):
            self.types[key] = [type, apply(getattr(Type, 'str_to_' + type), [self[key]])]

        def get_type(self, key):
            # Raise KeyError in key not defined
            self[key]
            if key in self.types:
                type = self.types[key][0]
            else:
                type = None
            return type

    def __init__(self, dictionnary = {}, file_path = None, conf_section_class = ConfSection):
        self.conf_section_class = conf_section_class
        dict.__init__({})
        self.file_path = file_path
        self.comments = None
        if self.file_path:
            self.load()
        elif dictionnary:
            self.load_from_dict(dictionnary)

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

    def load_from_dict(self, dictionnary):
        for section in dictionnary:
            self[section] = self.conf_section_class(dictionnary[section])

    def load(self, file_path = None):
        if not file_path:
            file_path = self.file_path
        # Configuration file loader
        if not os.path.exists(file_path):
            raise IOError(errno.ENOENT, "%s: %s" % (self.file_path, os.strerror(errno.ENOENT)))
        elif os.path.isdir(file_path):
            raise IOError(errno.EISDIR, "%s: %s" % (self.file_path, os.strerror(errno.EISDIR)))
        cp = ConfigParser.ConfigParser()
        cp.read(file_path)
        for section in cp.sections():
            self[section] = self.conf_section_class(cp.items(section))

    def save(self, file_path = None):
        if not file_path:
            file_path = self.file_path
        output_file = open(file_path, "w")
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
