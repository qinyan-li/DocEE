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
	NAME = '破产清算'
	FIELDS   = ['公司行业','裁定时间','受理法院','公告时间','公司名称']
	TRIGGERS = {1: ['公司行业'], 2: ['公司行业', '裁定时间'], 3: ['公司行业', '裁定时间', '受理法院'], 4: ['公司行业', '裁定时间', '受理法院', '公告时间'], 5: ['公司行业', '裁定时间', '受理法院', '公告时间', '公司名称']} 
	TRIGGERS['all'] = ['公司行业','裁定时间','受理法院','公告时间','公司名称']
	def __init__(self, recguid=None):
		super().__init__(
		self.FIELDS, event_name=self.NAME, recguid=recguid
		 )
		self.set_key_fields(self.TRIGGERS)



class event_1(BaseEvent):
	NAME = '重大安全事故'
	FIELDS   = ['其他影响','伤亡人数','损失金额','公告时间','公司名称']
	TRIGGERS = {1: ['其他影响'], 2: ['其他影响', '伤亡人数'], 3: ['其他影响', '伤亡人数', '损失金额'], 4: ['其他影响', '伤亡人数', '损失金额', '公告时间'], 5: ['其他影响', '伤亡人数', '损失金额', '公告时间', '公司名称']} 
	TRIGGERS['all'] = ['其他影响','伤亡人数','损失金额','公告时间','公司名称']
	def __init__(self, recguid=None):
		super().__init__(
		self.FIELDS, event_name=self.NAME, recguid=recguid
		 )
		self.set_key_fields(self.TRIGGERS)



class event_2(BaseEvent):
	NAME = '股东减持'
	FIELDS   = ['减持的股东','减持金额','减持开始日期']
	TRIGGERS = {1: ['减持的股东'], 2: ['减持的股东', '减持金额'], 3: ['减持的股东', '减持金额', '减持开始日期']} 
	TRIGGERS['all'] = ['减持的股东','减持金额','减持开始日期']
	def __init__(self, recguid=None):
		super().__init__(
		self.FIELDS, event_name=self.NAME, recguid=recguid
		 )
		self.set_key_fields(self.TRIGGERS)



class event_3(BaseEvent):
	NAME = '股权质押'
	FIELDS   = ['质押方','质押结束日期','接收方','质押开始日期','质押金额']
	TRIGGERS = {1: ['质押方'], 2: ['质押方', '质押结束日期'], 3: ['质押方', '质押结束日期', '接收方'], 4: ['质押方', '质押结束日期', '接收方', '质押开始日期'], 5: ['质押方', '质押结束日期', '接收方', '质押开始日期', '质押金额']} 
	TRIGGERS['all'] = ['质押方','质押结束日期','接收方','质押开始日期','质押金额']
	def __init__(self, recguid=None):
		super().__init__(
		self.FIELDS, event_name=self.NAME, recguid=recguid
		 )
		self.set_key_fields(self.TRIGGERS)



class event_4(BaseEvent):
	NAME = '股东增持'
	FIELDS   = ['增持金额','增持开始日期','增持的股东']
	TRIGGERS = {1: ['增持金额'], 2: ['增持金额', '增持开始日期'], 3: ['增持金额', '增持开始日期', '增持的股东']} 
	TRIGGERS['all'] = ['增持金额','增持开始日期','增持的股东']
	def __init__(self, recguid=None):
		super().__init__(
		self.FIELDS, event_name=self.NAME, recguid=recguid
		 )
		self.set_key_fields(self.TRIGGERS)



class event_5(BaseEvent):
	NAME = '股权冻结'
	FIELDS   = ['冻结结束日期','被冻结股东','冻结金额','冻结开始日期']
	TRIGGERS = {1: ['冻结结束日期'], 2: ['冻结结束日期', '被冻结股东'], 3: ['冻结结束日期', '被冻结股东', '冻结金额'], 4: ['冻结结束日期', '被冻结股东', '冻结金额', '冻结开始日期']} 
	TRIGGERS['all'] = ['冻结结束日期','被冻结股东','冻结金额','冻结开始日期']
	def __init__(self, recguid=None):
		super().__init__(
		self.FIELDS, event_name=self.NAME, recguid=recguid
		 )
		self.set_key_fields(self.TRIGGERS)



class event_6(BaseEvent):
	NAME = '高层死亡'
	FIELDS   = ['死亡年龄','死亡/失联时间','高层职务','高层人员','公司名称']
	TRIGGERS = {1: ['死亡年龄'], 2: ['死亡年龄', '死亡/失联时间'], 3: ['死亡年龄', '死亡/失联时间', '高层职务'], 4: ['死亡年龄', '死亡/失联时间', '高层职务', '高层人员'], 5: ['死亡年龄', '死亡/失联时间', '高层职务', '高层人员', '公司名称']} 
	TRIGGERS['all'] = ['死亡年龄','死亡/失联时间','高层职务','高层人员','公司名称']
	def __init__(self, recguid=None):
		super().__init__(
		self.FIELDS, event_name=self.NAME, recguid=recguid
		 )
		self.set_key_fields(self.TRIGGERS)



class event_7(BaseEvent):
	NAME = '重大资产损失'
	FIELDS   = ['其他损失','损失金额','公告时间','公司名称']
	TRIGGERS = {1: ['其他损失'], 2: ['其他损失', '损失金额'], 3: ['其他损失', '损失金额', '公告时间'], 4: ['其他损失', '损失金额', '公告时间', '公司名称']} 
	TRIGGERS['all'] = ['其他损失','损失金额','公告时间','公司名称']
	def __init__(self, recguid=None):
		super().__init__(
		self.FIELDS, event_name=self.NAME, recguid=recguid
		 )
		self.set_key_fields(self.TRIGGERS)



class event_8(BaseEvent):
	NAME = '重大对外赔付'
	FIELDS   = ['赔付金额','赔付对象','公告时间','公司名称']
	TRIGGERS = {1: ['赔付金额'], 2: ['赔付金额', '赔付对象'], 3: ['赔付金额', '赔付对象', '公告时间'], 4: ['赔付金额', '赔付对象', '公告时间', '公司名称']} 
	TRIGGERS['all'] = ['赔付金额','赔付对象','公告时间','公司名称']
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
event_5.NAME: event_5,
event_6.NAME: event_6,
event_7.NAME: event_7,
event_8.NAME: event_8,}
event_type_fields_list = [(event_0.NAME,event_0.FIELDS,event_0.TRIGGERS,2),
(event_1.NAME,event_1.FIELDS,event_1.TRIGGERS,2),
(event_2.NAME,event_2.FIELDS,event_2.TRIGGERS,2),
(event_3.NAME,event_3.FIELDS,event_3.TRIGGERS,2),
(event_4.NAME,event_4.FIELDS,event_4.TRIGGERS,2),
(event_5.NAME,event_5.FIELDS,event_5.TRIGGERS,2),
(event_6.NAME,event_6.FIELDS,event_6.TRIGGERS,2),
(event_7.NAME,event_7.FIELDS,event_7.TRIGGERS,2),
(event_8.NAME,event_8.FIELDS,event_8.TRIGGERS,2),]
