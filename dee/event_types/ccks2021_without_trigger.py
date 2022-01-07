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
	NAME = '欺诈风险'
	FIELDS   = ['订单号','身份证号','手机号','受害人身份','涉案平台','案发时间','案发城市','嫌疑人','受害人','支付渠道','资损金额']
	TRIGGERS = {1: ['资损金额'],
   2: ['资损金额','涉案平台'],
   3: ['资损金额','涉案平台','身份证号'],
   4: ['资损金额','支付渠道','涉案平台','身份证号'],
   5: ['涉案平台','手机号','支付渠道','资损金额','身份证号'],
   6: ['手机号','支付渠道','受害人身份','资损金额','涉案平台','身份证号'],
   7: ['手机号','支付渠道','受害人身份','案发时间','资损金额','涉案平台','身份证号'],
   8: ['手机号','支付渠道','受害人身份','案发时间','订单号','资损金额','涉案平台','身份证号'],
   9: ['手机号','支付渠道','受害人身份','案发时间','订单号','资损金额','受害人','涉案平台','身份证号'],
   10: ['手机号','支付渠道','受害人身份','案发时间','订单号','资损金额','受害人','案发城市','涉案平台','身份证号'],
   11: ['嫌疑人','手机号','支付渠道','受害人身份','案发时间','订单号','资损金额','受害人','案发城市','涉案平台','身份证号']}
	TRIGGERS['all'] = ['订单号','身份证号','手机号','受害人身份','涉案平台','案发时间','案发城市','嫌疑人','受害人','支付渠道','资损金额']
	def __init__(self, recguid=None):
		super().__init__(
		self.FIELDS, event_name=self.NAME, recguid=recguid
		 )
		self.set_key_fields(self.TRIGGERS)



class event_1(BaseEvent):
	NAME = '盗用风险'
	FIELDS   = ['交易号','银行卡号','手机号','受害人身份','涉案平台','案发时间','案发城市','嫌疑人','受害人','支付渠道','资损金额']
	TRIGGERS = {1: ['资损金额'],
   2: ['支付渠道','涉案平台'],
   3: ['资损金额','支付渠道','涉案平台'],
   4: ['资损金额','手机号','支付渠道','涉案平台'],
   5: ['涉案平台','手机号','支付渠道','受害人身份','资损金额'],
   6: ['手机号','支付渠道','受害人身份','案发时间','资损金额','涉案平台'],
   7: ['手机号','支付渠道','受害人身份','案发时间','资损金额','银行卡号','涉案平台'],
   8: ['手机号','支付渠道','受害人身份','案发时间','资损金额','银行卡号','交易号','涉案平台'],
   9: ['手机号','支付渠道','受害人身份','案发时间','资损金额','银行卡号','交易号','受害人','涉案平台'],
   10: ['手机号','支付渠道','受害人身份','案发时间','资损金额','银行卡号','交易号','受害人','案发城市','涉案平台'],
   11: ['手机号','支付渠道','受害人身份','案发时间','资损金额','银行卡号','交易号','受害人','案发城市','涉案平台','嫌疑人']}
	TRIGGERS['all'] = ['交易号','银行卡号','手机号','受害人身份','涉案平台','案发时间','案发城市','嫌疑人','受害人','支付渠道','资损金额']
	def __init__(self, recguid=None):
		super().__init__(
		self.FIELDS, event_name=self.NAME, recguid=recguid
		 )
		self.set_key_fields(self.TRIGGERS)



class event_2(BaseEvent):
	NAME = '无效内容'
	FIELDS   = ['涉案平台','案发时间','案发城市','嫌疑人','支付渠道','资损金额']
	TRIGGERS = {1: ['资损金额'],
   2: ['案发城市','支付渠道'],
   3: ['案发城市','支付渠道','案发时间'],
   4: ['支付渠道','资损金额','案发时间','嫌疑人'],
   5: ['支付渠道','案发时间','案发城市','资损金额','嫌疑人'],
   6: ['支付渠道','案发时间','资损金额','案发城市','涉案平台','嫌疑人']}
	TRIGGERS['all'] = ['涉案平台','案发时间','案发城市','嫌疑人','支付渠道','资损金额']
	def __init__(self, recguid=None):
		super().__init__(
		self.FIELDS, event_name=self.NAME, recguid=recguid
		 )
		self.set_key_fields(self.TRIGGERS)



class event_3(BaseEvent):
	NAME = '微信社交负面'
	FIELDS   = ['支付渠道']
	TRIGGERS = {1: ['支付渠道']} 
	TRIGGERS['all'] = ['支付渠道']
	def __init__(self, recguid=None):
		super().__init__(
		self.FIELDS, event_name=self.NAME, recguid=recguid
		 )
		self.set_key_fields(self.TRIGGERS)



class event_4(BaseEvent):
	NAME = '商户风险'
	FIELDS   = ['涉案平台','资损金额']
	TRIGGERS = {1: ['涉案平台'], 2: ['涉案平台', '资损金额']} 
	TRIGGERS['all'] = ['涉案平台','资损金额']
	def __init__(self, recguid=None):
		super().__init__(
		self.FIELDS, event_name=self.NAME, recguid=recguid
		 )
		self.set_key_fields(self.TRIGGERS)



class event_5(BaseEvent):
	NAME = '其他'
	FIELDS   = ['受害人身份','涉案平台','支付渠道','资损金额']
	TRIGGERS = {1: ['支付渠道'],
   2: ['支付渠道','资损金额'],
   3: ['支付渠道','资损金额','受害人身份'],
   4: ['涉案平台','支付渠道','资损金额','受害人身份']}
	TRIGGERS['all'] = ['受害人身份','涉案平台','支付渠道','资损金额']
	def __init__(self, recguid=None):
		super().__init__(
		self.FIELDS, event_name=self.NAME, recguid=recguid
		 )
		self.set_key_fields(self.TRIGGERS)

common_fields = []
event_type2event_class = { event_0.NAME: event_0,
event_1.NAME: event_1,
event_2.NAME: event_2,
event_3.NAME: event_3,
event_4.NAME: event_4,
event_5.NAME: event_5,}
event_type_fields_list = [(event_0.NAME,event_0.FIELDS,event_0.TRIGGERS,2),
(event_1.NAME,event_1.FIELDS,event_1.TRIGGERS,2),
(event_2.NAME,event_2.FIELDS,event_2.TRIGGERS,2),
(event_3.NAME,event_3.FIELDS,event_3.TRIGGERS,2),
(event_4.NAME,event_4.FIELDS,event_4.TRIGGERS,2),
(event_5.NAME,event_5.FIELDS,event_5.TRIGGERS,2),]
