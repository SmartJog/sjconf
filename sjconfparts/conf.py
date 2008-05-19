from sjconfparts.type import *
from sjconfparts.exceptions import *
import os, re, ConfigParser, errno

class Conf:

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

    class UnauthorizedSectionError(Error):
        def __init__(self, section, conf_file):
            self.msg = 'Unauthorized section "%s": all sections should be either "%s" or "%s:<subsection>"' % (section, conf_file, conf_file)

    class SafeConfigParser(ConfigParser.SafeConfigParser):
        def optionxform(self, optionstr):
            return optionstr

    class ConfSection:
        def __init__(self, dictionary = {}):
            self.dict = dict(dictionary)
            self.types = {}
            self.type_values = {}
            if hasattr(dictionary, 'get_types'):
                for (key, type) in dictionary.get_types().iteritems():
                    self.set_type(key, type)

        def __delitem__(self, key):
            del self.dict[key]
            if key in self.type_values:
                del self.type_values[key]

        def _find_type_of(self, key):
            type = None
            search_result = re.compile('(.*)_([^_]+)$').search(key)
            if search_result:
                key_tmp = search_result.group(1)
                type = search_result.group(2)
                if self._find_type_for(key_tmp) == type:
                    key = key_tmp
                else:
                    type = None
            return key, type

        def _find_type_for(self, key):
            type = None
            if key in self.types:
                type = self.types[key]
            else:
                for type_to_test in self.types:
                    if hasattr(type_to_test, 'search') and type_to_test.search(key):
                        type = self.types[type_to_test]
                        break
            return type

        def __getitem__(self, key):
            key, type = self._find_type_of(key)
            if type:
                value = self.type_values[key]
            else:
                type = self._find_type_for(key)
                if type:
                    Type.convert(type, 'str', self.type_values, self.dict, key)
                    value = self.dict[key]
                else:
                    value = self.dict[key]
            return value

        def __setitem__(self, key, value):
            key, type = self._find_type_of(key)
            if type:
                self.type_values[key] = value
                Type.convert(type, 'str', self.type_values, self.dict, key)
            else:
                self.dict[key] = value
                type = self._find_type_for(key)
                if type:
                    Type.convert('str', type, self.dict, self.type_values, key)

        def set_type(self, key, type):
            self.types[Type.convert_key(key, type)] = type
            keys = [key_matched for key_matched in self.dict if self._find_type_for(key_matched) == type]
            for key in keys:
                Type.convert('str', type, self.dict, self.type_values, key)

        def get_type(self, key):
            # Raise KeyError in key not defined
            self.dict[key]
            return self._find_type_for(key)

        def del_type(self, key):
            del self.types[key]

        def get_types(self):
            return self.types

        def __getattr__(self, *args, **kw):
            return getattr(self.dict, *args, **kw)

    def __init__(self, dictionary = {}, file_path = None, conf_section_class = ConfSection):
        self.conf_section_class = conf_section_class
        self.dict = dict({})
        self.file_path = file_path
        self.comments = None
        self.types = {}
        if self.file_path:
            self.load()
        elif dictionary:
            self.load_from_dict(dictionary)

    def __setitem__(self, key, value):
        if value.__class__ != self.conf_section_class:
            value = self.conf_section_class(value)
        self.dict[key] = value
        for (section, values) in self.types.iteritems():
            if section == key or (hasattr(section, 'search') and section.search(key)):
                for value in values:
                    self.dict[key].set_type(*value)

    def update(self, other_dict):
        for section in other_dict:
            if section in self:
                self.dict[section].update(other_dict[section])
            else:
                if other_dict[section].__class__ != self.conf_section_class:
                    value = self.conf_section_class(other_dict[section])
                else:
                    value = other_dict[section]
                self.dict[section] = value
        if hasattr(other_dict, 'get_types'):
            for (key, type) in other_dict.get_types().iteritems():
                self.set_type(self, key, type)

    def load_from_dict(self, dictionary):
        for section in dictionary:
            self.dict[section] = self.conf_section_class(dictionary[section])
        if hasattr(dictionary, 'get_types'):
            for (key, type) in dictionary.get_types().iteritems():
                self.set_type(self, key, type)

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
            cp = Conf.SafeConfigParser()
            cp.read(file_path)
            for section in cp.sections():
                self.dict[section] = self.conf_section_class(cp.items(section))

    def save(self, output_file = None):
        if not output_file:
            output_file = self.file_path
        if not hasattr(output_file, 'write'):
            output_file = open(output_file, "w")
        if self.comments != None and len(self.comments) > 0:
            for comment in self.comments.split('\n'):
               output_file.write('# ' + comment + '\n')
            output_file.write('\n')
        cp = Conf.SafeConfigParser()
        for section in self.dict:
            cp.add_section(section)
            for (key, value) in self.dict[section].iteritems():
                cp.set(section, key, value)
        cp.write(output_file)

    def set_type(self, section, key, type):
        self.types.setdefault(section, []).append((key, type))
        if hasattr(section, 'search'):
            sections = [section_matched for section_matched in self.dict if section.search(section_matched)]
        elif section in self.dict:
            sections = (section,)
        else:
            sections = ()
        for section in sections:
            self.dict[section].set_type(key, type)

    def get_type(self, section, key):
        return self.dict[section].get_type(key)

    def __getattr__(self, *args, **kw):
        return getattr(self.dict, *args, **kw)
