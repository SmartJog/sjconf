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
        if str_object in ("yes", "on", "true", "enabled", "enable"):
            return True
        elif str_object in ("no", "off", "false", "disabled", "disable"):
            return False
        else:
            raise TypeError

    @classmethod
    def bool_to_str(xcls, bool_object):
        if bool_object:
            return "yes"
        else:
            return "no"
