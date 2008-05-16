from sjconfparts.exceptions import *
import re

class TypePythonIsCrappy:

    class Error(Error):
        pass

    class ConversionError(Error):
        pass

class Type(TypePythonIsCrappy):

    class ConversionBadTypeError(TypePythonIsCrappy.ConversionError):
        def __init__(self, type_source, type_dest):
            self.msg = 'Invalid conversion from type %s to type %s, can only convert from str or to str'

    @classmethod
    def convert(xcls, type_source, type_dest, dict_source, dict_dest, key):
        if type_source == 'str':
            type_class_name = type_dest.capitalize()
        elif type_dest == 'str':
            type_class_name = type_source.capitalize()
        else:
            raise Type.ConversionBadTypeError(type_source, type_dest)
        type_class = getattr(xcls, type_class_name)
        return getattr(type_class, type_source + '_to_' + type_dest)(dict_source, dict_dest, key)

    class List:

        @classmethod
        def str_to_list(xcls, dict_source, dict_dest, key):
            str_object = dict_source[key]
            list = map(str.strip, str_object.split(','))
            try:
                list.remove('')
            except ValueError:
                pass
            dict_dest[key] = list
            return dict_dest

        @classmethod
        def list_to_str(xcls, dict_source, dict_dest, key):
            list_object = dict_source[key]
            str_object = ', '.join(list_object)
            dict_dest[key] = str_object
            return dict_dest

    class Bool:

        TRUE_VALUES = ("yes", "on", "true", "enabled", "enable")

        FALSE_VALUES = ("no", "off", "false", "disabled", "disable")

        class StrToBoolError(TypePythonIsCrappy.ConversionError):
            def __init__(self, str_object):
                self.msg = 'Bad value "%s" for str to bool conversion, expected a value in %s' % (str_object, str(Type.Bool.TRUE_VALUES + Type.Bool.FALSE_VALUES))

        class BoolToStrError(TypePythonIsCrappy.ConversionError):
            def __init__(self, bool_object):
                self.msg = 'Bad value "%s" for bool to str conversion, expected a boolean' % (bool_object)

        @classmethod
        def str_to_bool(xcls, dict_source, dict_dest, key):
            str_object = dict_source[key]
            if str_object.lower() in Type.Bool.TRUE_VALUES:
                bool_object = True
            elif str_object.lower() in Type.Bool.FALSE_VALUES:
                bool_object = False
            else:
                raise Type.Bool.StrToBoolError(str_object)
            dict_dest[key] = bool_object
            return dict_dest

        @classmethod
        def bool_to_str(xcls, dict_source, dict_dest, key):
            bool_object = dict_source[key]
            if bool_object == True:
                str_object = "yes"
            elif bool_object == False:
                str_object = "no"
            else:
                raise Type.Bool.BoolToStrError(bool_object)
            dict_dest[key] = str_object
            return dict_dest

    class Size:

        class StrToSizeError(TypePythonIsCrappy.ConversionError):
            def __init__(self, str_object):
                self.msg = 'Bad value "%s" for str to size conversion, expected a value like, e.g. 10M' % (str_object)

        class SizeToStrError(TypePythonIsCrappy.ConversionError):
            def __init__(self, size_object):
                self.msg = 'Bad value "%s" for size to str conversion, expected an integer' % (size_object)

        @classmethod
        def str_to_size(xcls, dict_source, dict_dest, key):
            str_object = dict_source[key]
            suffixes = ['T', 'G', 'M', 'k']
            match_result = re.compile("^(\d+)([%s])?$" % (''.join(suffixes))).match(str_object)
            if match_result == None:
                raise Type.Size.StrToSizeError(str_object)
            size, suffix = match_result.groups('')
            size_object = int(size)
            while len(suffixes) > 0:
                if suffix in suffixes:
                    size_object *= 1024
                suffixes.pop()
            dict_dest[key] = size_object
            return dict_dest

        @classmethod
        def size_to_str(xcls, dict_source, dict_dest, key):
            try:
                size_object = int(size_object)
            except ValueError:
                raise SizeToStrError(size_object)
            for suffix_to_test in ('k', 'M', 'G', 'T'):
                if size > 1024:
                    suffix = suffix_to_test
                    size /= 1024
            str_object = str(size) + suffix
            dict_dest[key] = str_object
            return dict_dest

    class Sequence:

        @classmethod
        def str_to_sequence(xcls, dict_source, dict_dest, key):
            sequence_object = []
            str_object = []
            match_results = re.compile('^(.*)-\d+$').match(key)
            if match_results:
                key = match_results.group(1)
            regexp = re.compile('^%s-\d+$' % (key))
            for (key_to_test, value) in dict_source.iteritems():
                if key_to_test == key or regexp.match(key_to_test):
                    str_object.append((key_to_test, value))
            str_object.sort()
            sequence_object = [value for (str_key, value) in str_object]
            dict_dest[key] = sequence_object
            return dict_dest

        @classmethod
        def sequence_to_str(xcls, dict_source, dict_dest, key):
            match_results = re.compile('^(.*)-\d+$').match(key)
            if match_results:
                key = match_results.group(1)
            sequence_object = list(dict_source[key])
            str_keys = []
            regexp = re.compile('^%s-\d+$' % (key))
            for key_to_test in dict_dest:
                if key_to_test == key or regexp.match(key_to_test):
                    str_keys.append(key_to_test)
            str_keys.sort()
            index = str_keys[-1].replace(key + '-', '')
            while len(str_keys) > 0 and len(sequence_object) > 0:
                dict_dest[str_keys.pop(0)] = sequence_object.pop(0)
            for str_key in str_keys:
                del dict_dest[str_key]
            for elt in sequence_object:
                index += 1
                dict_dest[key + '-' + index] = elt
            return dict_dest
