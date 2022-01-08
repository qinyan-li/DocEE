class BaseEvent(object):
    def __init__(self, fields, event_name='Event', key_fields=(), recguid=None):
        self.recguid = recguid
        self.name = event_name
        self.fields = list(fields)
        self.field2content = {f: None for f in fields}
        self.nonempty_count = 0
        self.nonempty_ratio = self.nonempty_count / len(self.fields)

        self.key_fields = set(key_fields)
        for key_field in self.key_fields:
            assert key_field in self.field2content

    def __repr__(self):
        event_str = "\n{}[\n".format(self.name)
        event_str += "  {}={}\n".format("recguid", self.recguid)
        event_str += "  {}={}\n".format("nonempty_count", self.nonempty_count)
        event_str += "  {}={:.3f}\n".format("nonempty_ratio", self.nonempty_ratio)
        event_str += "] (\n"
        for field in self.fields:
            if field in self.key_fields:
                key_str = " (key)"
            else:
                key_str = ""
            event_str += "  " + field + "=" + str(self.field2content[field]) + ", {}\n".format(key_str)
        event_str += ")\n"
        return event_str

    def update_by_dict(self, field2text, recguid=None):
        self.nonempty_count = 0
        self.recguid = recguid

        for field in self.fields:
            if field in field2text and field2text[field] is not None:
                self.nonempty_count += 1
                self.field2content[field] = field2text[field]
            else:
                self.field2content[field] = None

        self.nonempty_ratio = self.nonempty_count / len(self.fields)

    def field_to_dict(self):
        return dict(self.field2content)

    def set_key_fields(self, key_fields):
        self.key_fields = set(key_fields)

    def is_key_complete(self):
        for key_field in self.key_fields:
            if self.field2content[key_field] is None:
                return False

        return True

    def get_argument_tuple(self):
        args_tuple = tuple(self.field2content[field] for field in self.fields)
        return args_tuple

    def is_good_candidate(self, min_match_count=2):
        key_flag = self.is_key_complete()
        if key_flag:
            if self.nonempty_count >= min_match_count:
                return True
        return False

class event_0(BaseEvent):
	NAME = 'test'
	FIELDS   = ['time','object','loc','subject']
	TRIGGERS = {1: ['subject'],
   2: ['object','time'],
   3: ['object','time','subject'],
   4: ['object','loc','time','subject']}

	TRIGGERS['all'] = ['time','object','loc','subject']
	def __init__(self, recguid=None):
		super().__init__(
		self.FIELDS, event_name=self.NAME, recguid=recguid
		 )
		self.set_key_fields(self.TRIGGERS)

common_fields = []
event_type2event_class = { event_0.NAME: event_0,}
event_type_fields_list = [(event_0.NAME,event_0.FIELDS,event_0.TRIGGERS,2),]
