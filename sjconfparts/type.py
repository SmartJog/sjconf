from sjconfparts.exceptions import *
import re

class TypePythonIsCrappy:

    class Error(Error):
        pass

    class ConversionError(Error):
        pass

class ConversionList:

    def __init__(self, conversion_method, list_object = None):
        self.conversion_method = conversion_method
        if list_object == None:
            list_object = []
        self.list = list_object

    def __getattr__(self, name):
        list_method = getattr(self.list, name)
        def method(*args, **kw):
            result =  list_method(*args, **kw)
            if name in ('__setslice__', '__delslice__', '__setitem__', '__delitem__', '__add__', '__radd__', '__iadd__', '__mul__', '__rmul__', '__imul__', 'append', 'extend', 'insert', 'pop', 'remove', 'reverse', 'sort'):
                self.conversion_method()
            return result
        return method

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

    @classmethod
    def convert_key(xcls, key, type):
        return xcls._convert_method('key', key, type)

    @classmethod
    def convert_value(xcls, value, type, dict_str, dict_type, key):
        return xcls._convert_method('value', value, type, dict_str, dict_type, key)

    @classmethod
    def convert_key_for_search(xcls, key, type):
        return xcls._convert_method('key_for_search', key, type)

    @classmethod
    def _convert_method(xcls, method, value, type, *args):
        type_class = getattr(xcls, type.capitalize())
        if not hasattr(type_class, method):
            converted_value = value
        else:
            converted_value = getattr(type_class, method)(value, *args)
        return converted_value

    class List:

        @classmethod
        def value(xcls, value, dict_str, dict_type, key):
            def conversion_method():
                Type.List.list_to_str(dict_type, dict_str, key)
            return ConversionList(conversion_method, value)

        @classmethod
        def str_to_list(xcls, dict_source, dict_dest, key):
            def conversion_method():
                Type.List.list_to_str(dict_dest, dict_source, key)
            str_object = dict_source[key]
            list = map(str.strip, str_object.split(','))
            try:
                list.remove('')
            except ValueError:
                pass
            dict_dest[key] = ConversionList(conversion_method, list)
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
        def key(xcls, key):
            match_results = re.compile('^(.*)-\d+$').match(key)
            if match_results:
                key = match_results.group(1)
            return key

        @classmethod
        def key_for_search(xcls, key):
            if not hasattr(key, 'search'):
                key = xcls.key(key)
                key = re.compile('^%s(-\d+)?$' % (key))
            return key

        @classmethod
        def value(xcls, value, dict_str, dict_type, key):
            def conversion_method():
                Type.Sequence.sequence_to_str(dict_type, dict_str, key)
            return ConversionList(conversion_method, value)

        @classmethod
        def key_to_index(xcls, key, key_to_convert):
            index = key_to_convert[len(key) + 1:]
            if index == '':
                index = -1
            else:
                index = int(index)
            return index

        @classmethod
        def str_to_sequence(xcls, dict_source, dict_dest, key):
            def conversion_method():
                Type.Sequence.sequence_to_str(dict_dest, dict_source, key)
            str_object = []
            key = xcls.key(key)
            regexp = re.compile('^%s-\d+$' % (key))
            for (key_to_test, value) in dict_source.iteritems():
                if key_to_test == key or regexp.match(key_to_test):
                    str_object.append((key_to_test, value))
            str_object.sort(key = lambda str_object: xcls.key_to_index(key, str_object[0]))
            sequence_object = ConversionList(conversion_method, [value for (str_key, value) in str_object])
            dict_dest[key] = sequence_object
            return dict_dest

        @classmethod
        def assign_elts(xcls, elts, assignments_old, indices_unassigned):

            def _assign_unassigned(indices, elts_unassigned, indices_unassigned, index_prev, index):
                indices_available = [index_unassigned for index_unassigned in indices_unassigned if index_unassigned > index_prev and (index_unassigned < index or index < -1)]
                for index_available in indices_available:
                    indices_unassigned.remove(index_available)
                while len(indices_available) > len(elts_unassigned) - (index >= -1 and 1 or 0):
                    indices_available.pop()
                indices_available.append(index)
                indices_to_assign = []
                for index_available in indices_available:
                    while len(indices_to_assign) < len(elts_unassigned) - (index_available >= -1 and 1 or 0):
                        if index_prev < index_available - 1 or index_available < -1:
                            index_prev += 1
                            indices_to_assign.append(index_prev)
                    if index_available >= -1:
                        indices_to_assign.append(index_available)
                        index_prev = index_available
                while len(elts_unassigned) > 0:
                    elts_unassigned.pop(0)
                    index_prev = indices_to_assign.pop(0)
                    indices.append(index_prev)
                return index_prev

            elts_unassigned = []
            indices = []
            index_prev = 0
            for elt in elts:
                elts_unassigned.append(elt)
                if elt in assignments_old:
                    index = assignments_old[elt]
                    if index > index_prev and (len(elts_unassigned) == 1 or len(elts_unassigned) <= index - index_prev):
                        index_prev = _assign_unassigned(indices, elts_unassigned, indices_unassigned, index_prev, index)
            index_prev = _assign_unassigned(indices, elts_unassigned, indices_unassigned, index_prev, -2)
            return indices

        @classmethod
        def sequence_to_str(xcls, dict_source, dict_dest, key):
            key = xcls.key(key)
            sequence_object = [elt for elt in list(dict_source[key]) if elt != '']
            regexp = re.compile('^%s-\d+$' % (key))
            str_keys = [key_to_test for key_to_test in dict_dest if regexp.match(key_to_test)]
            keys_unassigned = [str_key for str_key in str_keys if dict_dest[str_key] == '']
            str_keys = [str_key for str_key in str_keys if str_key not in keys_unassigned]
            assignments_old = dict([(dict_dest[str_key], xcls.key_to_index(key, str_key)) for str_key in sorted(str_keys, key = lambda key_to_convert: xcls.key_to_index(key, key_to_convert))])
            indices = xcls.assign_elts(sequence_object, assignments_old, [xcls.key_to_index(key, key_to_convert) for key_to_convert in keys_unassigned])
            for str_key in str_keys:
                del dict_dest[str_key]
            while len(sequence_object) > 0:
                elt = sequence_object.pop(0)
                index = indices.pop(0)
                dict_dest[key + '-' + str(index)] = elt
            return dict_dest
