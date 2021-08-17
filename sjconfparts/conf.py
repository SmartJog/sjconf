from sjconfparts.type import *
from sjconfparts.exceptions import *
import os, re, configparser, errno


class Conf:
    class Error(Error):
        pass

    class ListError(Error):
        pass

    class ListValueAlreadyExistError(ListError):
        def __init__(self, section, key, value):
            self.msg = 'The value "%s" is already in key %s of section %s' % (
                value,
                section,
                key,
            )

    class UnauthorizedSectionError(Error):
        def __init__(self, section, conf_file):
            self.msg = (
                'Unauthorized section "%s": all sections should be either "%s" or "%s:<subsection>"'
                % (section, conf_file, conf_file)
            )

    class ProfileConflictError(Error):
        def __init__(self, conf_name1, conf_name2, section, key):
            self.msg = (
                'The profiles "%s" and "%s" are enabled on the same level, but have a conflicting value for key "%s" in section "%s", please set it to the appropriate value in local.conf or disable one of the profiles'
                % (conf_name1, conf_name2, key, section)
            )

    class RawConfigParser(configparser.RawConfigParser):
        """RawConfigParser subclass, with an ordered write() method."""

        def write(self, fp):
            """Write an .ini-format representation of the configuration
            state. Sections are written sorted."""
            if self._defaults:
                fp.write("[%s]\n" % configparser.DEFAULTSECT)
                for (key, value) in list(self._defaults.items()):
                    fp.write("%s = %s\n" % (key, str(value).replace("\n", "\n\t")))
                fp.write("\n")
            tmp_sections = list(self._sections.keys())
            tmp_sections.sort()
            for section in tmp_sections:
                fp.write("[%s]\n" % section)
                tmp_keys = list(self._sections[section].keys())
                tmp_keys.sort()
                for key in tmp_keys:
                    if key != "__name__":
                        fp.write(
                            "%s = %s\n"
                            % (
                                key,
                                str(self._sections[section][key]).replace("\n", "\n\t"),
                            )
                        )
                fp.write("\n")

        def optionxform(self, optionstr):
            return optionstr

    class SafeConfigParser(configparser.SafeConfigParser, RawConfigParser):
        """A SafeConfigParser subclass, with an ordered write() method."""

        def optionxform(self, optionstr):
            return optionstr

        def write(self, fp):
            Conf.RawConfigParser.write(self, fp)

    class ConfSection:
        def __init__(self, dictionary={}):
            self.dict = dict(dictionary)
            self.types = {}
            self.type_values = {}
            if hasattr(dictionary, "get_types"):
                for (key, type) in dictionary.get_types().items():
                    self.set_type(key, type)

        def __delitem__(self, key):
            del self.dict[key]
            if key in self.type_values:
                del self.type_values[key]

        def _find_type_of(self, key):
            type = None
            search_result = re.compile(r"(.*)_([^_]+)$").search(key)
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
                    if hasattr(type_to_test, "search") and type_to_test.search(key):
                        type = self.types[type_to_test]
                        break
            return type

        def __getitem__(self, key):
            key, type = self._find_type_of(key)
            if type:
                value = self.type_values[key]
            else:
                value = self.dict[key]
            return value

        def __setitem__(self, key, value):
            key, type = self._find_type_of(key)
            if type:
                self.type_values[key] = Type.convert_value(
                    value, type, self.dict, self.type_values, key
                )
                Type.convert(type, "str", self.type_values, self.dict, key)
            else:
                self.dict[key] = value
                type = self._find_type_for(key)
                if type:
                    Type.convert("str", type, self.dict, self.type_values, key)

        def update(self, other_dict):
            for (key, value) in other_dict.items():
                if hasattr(other_dict, "get_type"):
                    type = other_dict._find_type_for(key)
                    if type:
                        self.set_type(key, type)
                self[key] = value

        def set_type(self, key, type):
            self.types[Type.convert_key_for_search(key, type)] = type
            keys = [
                key_matched
                for key_matched in self.dict
                if self._find_type_for(key_matched) == type
            ]
            for key in keys:
                Type.convert("str", type, self.dict, self.type_values, key)

        def get_type(self, key):
            # Raise KeyError in key not defined
            self.dict[key]
            return self._find_type_for(key)

        def del_type(self, key, type=None):
            if not key in self.types and type is not None:
                key = Type.convert_key_for_search(key, type)
            del self.types[key]

        def get_types(self):
            return self.types

        def __iter__(self):
            return self.dict.__iter__()

        def __getattr__(self, *args, **kw):
            return getattr(self.dict, *args, **kw)

    def __init__(
        self,
        dictionary={},
        file_path=None,
        conf_section_class=ConfSection,
        parser_type="magic",
    ):
        self.conf_section_class = conf_section_class
        self.dict = dict({})
        self.file_path = file_path
        self.comments = None
        self.types = {}
        if parser_type == "raw":
            self.config_parser_class = Conf.RawConfigParser
        else:
            self.config_parser_class = Conf.SafeConfigParser
        if self.file_path:
            self.load()
        elif dictionary:
            self.load_from_dict(dictionary)

    def __setitem__(self, key, value):
        self.dict[key] = self._value_to_section(key, value)

    def __getitem__(self, key):
        return self.dict[key]

    def __contains__(self, key):
        return self.dict.__contains__(key)

    def __iter__(self):
        return self.dict.__iter__()

    def setdefault(self, key, value=None):
        return self.dict.setdefault(key, self._value_to_section(key, value))

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
        if hasattr(other_dict, "get_types"):
            for (key, type) in other_dict.get_types().items():
                self.set_type(self, key, type)

    def update_verify_conflict(self, other_dict):
        conflicting_values = []
        for (section_name, section) in self.dict.items():
            for key, value in section.items():
                if (
                    section_name in other_dict
                    and key in other_dict[section_name]
                    and value != other_dict[section_name][key]
                ):
                    conflicting_values.append((section_name, key))
        return conflicting_values

    def load_from_dict(self, dictionary):
        for section in dictionary:
            self.dict[section] = self.conf_section_class(dictionary[section])
        if hasattr(dictionary, "get_types"):
            for (key, type) in dictionary.get_types().items():
                self.set_type(self, key, type)

    def load(self, file_path=None):
        if not file_path:
            file_path = self.file_path
        # Configuration file loader
        if os.path.isdir(file_path) and file_path.endswith(".conf"):
            raise IOError(
                errno.EISDIR, "%s: %s" % (self.file_path, os.strerror(errno.EISDIR))
            )
        if not os.path.isdir(file_path) and not file_path.endswith(".conf"):
            raise IOError(
                errno.ENOTDIR, "%s: %s" % (self.file_path, os.strerror(errno.ENOTDIR))
            )
        if os.path.isdir(file_path):
            files_path = [
                file_path + "/" + file_name for file_name in os.listdir(file_path)
            ]
        else:
            files_path = (file_path,)
        for file_path in files_path:
            if not file_path.endswith(".conf"):
                continue
            if not os.path.exists(file_path):
                raise IOError(
                    errno.ENOENT, "%s: %s" % (self.file_path, os.strerror(errno.ENOENT))
                )
            elif os.path.isdir(file_path):
                raise IOError(
                    errno.EISDIR, "%s: %s" % (self.file_path, os.strerror(errno.EISDIR))
                )
            cp = self.config_parser_class()
            cp.read(file_path)
            for section in cp.sections():
                self.dict[section] = self.conf_section_class(cp.items(section))

    def save(self, output_file=None):
        opened = False
        if not output_file:
            output_file = self.file_path
        if not hasattr(output_file, "write"):
            output_file = open(output_file, "w")
            opened = True
        if self.comments != None and len(self.comments) > 0:
            for comment in self.comments.split("\n"):
                output_file.write("# " + comment + "\n")
            output_file.write("\n")
        cp = self.config_parser_class()
        sections = list(self.dict.keys())
        sections.sort(reverse=True)
        for section in sections:
            cp.add_section(section)
            keys = list(self.dict[section].keys())
            keys.sort(reverse=True)
            for key in keys:
                cp.set(section, key, self.dict[section][key])
        cp.write(output_file)
        if opened:
            output_file.close()

    def set_type(self, section, key, type):
        self.types.setdefault(section, []).append((key, type))
        if hasattr(section, "search"):
            sections = [
                section_matched
                for section_matched in self.dict
                if section.search(section_matched)
            ]
        elif section in self.dict:
            sections = (section,)
        else:
            sections = ()
        for section in sections:
            self.dict[section].set_type(key, type)

    def get_type(self, section, key):
        return self.dict[section].get_type(key)

    def del_type(self, section, key, type=None):
        if hasattr(section, "search"):
            sections = [
                section_matched
                for section_matched in self.dict
                if section.search(section_matched)
            ]
        else:
            sections = (section,)
        for section in sections:
            self.dict[section].del_type(key, type)

    def __getattr__(self, *args, **kw):
        return getattr(self.dict, *args, **kw)

    def _value_to_section(self, key, value):
        if value.__class__ != self.conf_section_class:
            value = self.conf_section_class(value)
        for (section, types) in self.types.items():
            if section == key or (hasattr(section, "search") and section.search(key)):
                for type in types:
                    value.set_type(*type)
        return value
