class Type:

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

    @classmethod
    def str_to_bool(xcls, str_object):
        if str_object == "yes" or str_object == "on" or str_object == "true":
            return True
        elif str_object == "no" or str_object == "off" or str_object == "false":
            return False
        else:
            raise TypeError

    @classmethod
    def bool_to_str(xcls, bool_object):
        if bool_object:
            return "yes"
        else:
            return "no"
