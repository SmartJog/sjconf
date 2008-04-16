from sjconfparts.exceptions import *

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
            raise ConversionBadTypeError(type_source, type_dest)
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
                self.msg = 'Bad value "%s" for str to bool conversion, expected a value in %s' % (str_object, str(TRUE_VALUES + FALSE_VALUES))

        class BoolToStrError(TypePythonIsCrappy.ConversionError):
            def __init__(self, bool_object):
                self.msg = 'Bad value "%s" for bool to str conversion, expected True or False' % (str_object)

        @classmethod
        def str_to_bool(xcls, str_object):
            if str_object in Type.Bool.TRUE_VALUES:
                return True
            elif str_object in Type.Bool.FALSE_VALUES:
                return False
            else:
                raise StrToBoolError(str_object)

        @classmethod
        def bool_to_str(xcls, bool_object):
            if bool_object == True:
                return "yes"
            elif bool_object == False:
                return "no"
            else:
                raise BoolToStrError(bool_object)
