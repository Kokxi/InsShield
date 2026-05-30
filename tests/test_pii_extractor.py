"""测试PII提取器"""
import pytest
from app.pii_extractor import extract_pii_from_text, extract_persons, group_pii_to_persons, PIIItem, Person


class TestExtractPIIFromText:
    """结构化PII提取测试"""

    def test_extract_id_number(self):
        """提取身份证号"""
        text = "投保人：张三\n身份证号：110101199001011234"
        items = extract_pii_from_text(text)
        assert len(items) == 1
        assert items[0].type == "id_number"
        assert items[0].value == "110101199001011234"

    def test_extract_phone(self):
        """提取手机号"""
        text = "联系电话：13812345678"
        items = extract_pii_from_text(text)
        assert len(items) == 1
        assert items[0].type == "phone"
        assert items[0].value == "13812345678"

    def test_extract_bank_account(self):
        """提取银行卡号"""
        text = "银行账号：6222021234567890123"
        items = extract_pii_from_text(text)
        assert len(items) == 1
        assert items[0].type == "bank_account"

    def test_extract_email(self):
        """提取邮箱"""
        text = "邮箱：zhangsan@example.com"
        items = extract_pii_from_text(text)
        assert len(items) == 1
        assert items[0].type == "email"

    def test_extract_multiple(self):
        """提取多个PII"""
        text = "身份证号：110101199001011234\n手机：13812345678"
        items = extract_pii_from_text(text)
        assert len(items) == 2

    def test_no_pii(self):
        """无PII内容"""
        text = "这是一段普通文本"
        items = extract_pii_from_text(text)
        assert len(items) == 0


class TestExtractPersons:
    """人员提取测试"""

    def test_extract_applicant(self):
        """提取投保人"""
        text = "投保人：张三"
        persons = extract_persons(text)
        assert len(persons) == 1
        assert persons[0].name == "张三"
        assert persons[0].role == "applicant"

    def test_extract_insured(self):
        """提取被保人"""
        text = "被保人：李四"
        persons = extract_persons(text)
        assert len(persons) == 1
        assert persons[0].name == "李四"
        assert persons[0].role == "insured"

    def test_extract_beneficiary(self):
        """提取受益人"""
        text = "受益人：王五"
        persons = extract_persons(text)
        assert len(persons) == 1
        assert persons[0].name == "王五"
        assert persons[0].role == "beneficiary"

    def test_extract_multiple_persons(self):
        """提取多个人员"""
        text = "投保人：张三\n被保人：李四\n受益人：王五"
        persons = extract_persons(text)
        assert len(persons) == 3

    def test_no_persons(self):
        """无人员信息"""
        text = "这是一段普通文本"
        persons = extract_persons(text)
        assert len(persons) == 0


class TestGroupPIIToPersons:
    """PII归属测试"""

    def test_group_to_nearest_person(self):
        """PII归属到最近的人员"""
        text = "投保人：张三\n身份证号：110101199001011234\n被保人：李四"
        persons = extract_persons(text)
        pii_items = extract_pii_from_text(text)
        grouped = group_pii_to_persons(persons, pii_items, text)

        # 身份证号应该归属到张三（投保人）
        zhangsan = [p for p in grouped if p.name == "张三"][0]
        assert len(zhangsan.details) == 1
        assert zhangsan.details[0].type == "id_number"

    def test_anonymous_person(self):
        """无人员时创建匿名人员"""
        text = "身份证号：110101199001011234"
        persons = extract_persons(text)
        pii_items = extract_pii_from_text(text)
        grouped = group_pii_to_persons(persons, pii_items, text)

        assert len(grouped) == 1
        assert grouped[0].name == ""
        assert grouped[0].role == "anonymous"
        assert len(grouped[0].details) == 1

    def test_extract_address(self):
        """提取地址"""
        text = "投保人：张三\n联系地址：北京市朝阳区"
        persons = extract_persons(text)
        pii_items = extract_pii_from_text(text)
        grouped = group_pii_to_persons(persons, pii_items, text)

        zhangsan = [p for p in grouped if p.name == "张三"][0]
        assert len(zhangsan.details) == 1
        assert zhangsan.details[0].type == "address"

    def test_extract_health_info(self):
        """提取健康信息"""
        text = "被保人：李四\n健康状况：良好"
        persons = extract_persons(text)
        pii_items = extract_pii_from_text(text)
        grouped = group_pii_to_persons(persons, pii_items, text)

        lisi = [p for p in grouped if p.name == "李四"][0]
        assert len(lisi.details) == 1
        assert lisi.details[0].type == "health"

    def test_extract_birth_date(self):
        """提取出生日期"""
        text = "投保人：张三\n出生日期：1990年1月1日"
        persons = extract_persons(text)
        pii_items = extract_pii_from_text(text)
        grouped = group_pii_to_persons(persons, pii_items, text)

        zhangsan = [p for p in grouped if p.name == "张三"][0]
        assert len(zhangsan.details) == 1
        assert zhangsan.details[0].type == "birth_date"
