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
    def list_to_str(xcls, list):
        return ', '.join(list)
