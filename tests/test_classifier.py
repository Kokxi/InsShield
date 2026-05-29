"""测试险种分类器"""
import pytest
from app.classifier import classify_insurance, get_category_display_name


class TestClassifyInsurance:
    """险种分类器正向测试"""

    def test_classify_life(self):
        """人寿险：年金"""
        assert classify_insurance("国寿鑫享至尊年金保险") == "life"

    def test_classify_life_shou(self):
        """人寿险：寿险"""
        assert classify_insurance("定期寿险") == "life"

    def test_classify_life_renshen(self):
        """人寿险：人寿"""
        assert classify_insurance("中国人寿") == "life"

    def test_classify_health_yiliao(self):
        """健康险：医疗"""
        assert classify_insurance("百万医疗险") == "health"

    def test_classify_health_zhongji(self):
        """健康险：重疾"""
        assert classify_insurance("重大疾病保险") == "health"

    def test_classify_accident(self):
        """意外险"""
        assert classify_insurance("综合意外险") == "accident"

    def test_classify_jiayi(self):
        """驾意归意外险，不归车险"""
        assert classify_insurance("驾意险") == "accident"

    def test_classify_car(self):
        """车险"""
        assert classify_insurance("交强险") == "car"

    def test_classify_property(self):
        """财产险"""
        assert classify_insurance("企业财产保险") == "property"

    def test_classify_property_zheren(self):
        """责任险"""
        assert classify_insurance("公众责任险") == "property"

    def test_classify_unknown(self):
        """无法识别"""
        assert classify_insurance("某自定义产品") == "unknown"

    def test_classify_empty(self):
        """空输入"""
        assert classify_insurance(None) == "unknown"
        assert classify_insurance("") == "unknown"

    def test_classify_priority_life_first(self):
        """人寿险优先于财产险（人寿在上）"""
        assert classify_insurance("人寿险") == "life"

    def test_classify_priority_health_before_car(self):
        """健康险优先于车险"""
        assert classify_insurance("健康险") == "health"


class TestGetCategoryDisplayName:
    """分类显示名测试"""

    def test_life_name(self):
        assert get_category_display_name("life") == "人寿险"

    def test_unknown_name(self):
        assert get_category_display_name("unknown") == "未知"

    def test_nonexistent(self):
        assert get_category_display_name("bogus") == "未知"
