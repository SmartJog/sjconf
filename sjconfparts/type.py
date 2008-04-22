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
    def convert(xcls, type_source, type_dest, value):
        if type_source == 'str':
            type_class_name = type_dest.capitalize()
        elif type_dest == 'str':
            type_class_name = type_source.capitalize()
        else:
            raise Type.ConversionBadTypeError(type_source, type_dest)
        type_class = getattr(xcls, type_class_name)
        return getattr(type_class, type_source + '_to_' + type_dest)(value)

    class List:

        @classmethod
        def str_to_list(xcls, str_object):
            list = map(str.strip, str_object.split(','))
            try:
                list.remove('')
            except ValueError:
                pass
            return list

        @classmethod
        def list_to_str(xcls, list_object):
            return ', '.join(list_object)

    class Bool:

        TRUE_VALUES = ("yes", "on", "true", "enabled", "enable")

        FALSE_VALUES = ("no", "off", "false", "disabled", "disable")

        class StrToBoolError(TypePythonIsCrappy.ConversionError):
            def __init__(self, str_object):
                self.msg = 'Bad value "%s" for str to bool conversion, expected a value in %s' % (str_object, str(Type.Bool.TRUE_VALUES + Type.Bool.FALSE_VALUES))

        class BoolToStrError(TypePythonIsCrappy.ConversionError):
            def __init__(self, bool_object):
                self.msg = 'Bad value "%s" for bool to str conversion, expected a boolean' % (str_object)

        @classmethod
        def str_to_bool(xcls, str_object):
            if str_object in Type.Bool.TRUE_VALUES:
                return True
            elif str_object in Type.Bool.FALSE_VALUES:
                return False
            else:
                raise Type.Bool.StrToBoolError(str_object)

        @classmethod
        def bool_to_str(xcls, bool_object):
            if bool_object == True:
                return "yes"
            elif bool_object == False:
                return "no"
            else:
                raise Type.Bool.BoolToStrError(bool_object)

    class Size:

        class StrToSizeError(TypePythonIsCrappy.ConversionError):
            def __init__(self, str_object):
                self.msg = 'Bad value "%s" for str to size conversion, expected a value like, e.g. 10M' % (str_object)

        class SizeToStrError(TypePythonIsCrappy.ConversionError):
            def __init__(self, size_object):
                self.msg = 'Bad value "%s" for size to str conversion, expected an integer' % (size_object)

        @classmethod
        def str_to_size(xcls, str_object):
            suffixes = ['T', 'G', 'M', 'k']
            match_result = re.compile("^(\d+)([%s])?$" % (''.join(suffixes))).match(str_object)
            if match_result == None:
                raise Type.Size.StrToSizeError(str_object)
            size, suffix = match_result.groups('')
            size = int(size)
            while len(suffixes) > 0:
                if suffix in suffixes:
                    size *= 1024
                suffixes.pop()
            return size

        @classmethod
        def size_to_str(xcls, size_object):
            if not isinstance(size_object, int):
                raise SizeToStrError(size_object)
            for suffix_to_test in ('k', 'M', 'G', 'T'):
                if size > 1024:
                    suffix = suffix_to_test
                    size /= 1024
            return str(size) + suffix
