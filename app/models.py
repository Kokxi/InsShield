"""Pydantic 数据模型"""
from pydantic import BaseModel, Field
from typing import Optional


class PolicyFields(BaseModel):
    """单个保单的提取字段"""
    insurance_company: Optional[str] = Field(None, description="保险公司")
    policy_type: Optional[str] = Field(None, description="险种")
    insurance_category: Optional[str] = Field(None, description="险种分类: life/health/accident/car/property/unknown")
    policy_number: Optional[str] = Field(None, description="保单号")
    applicant: Optional[str] = Field(None, description="投保人")
    insured: Optional[str] = Field(None, description="被保人")
    beneficiary: Optional[str] = Field(None, description="受益人")
    premium: Optional[str] = Field(None, description="保费")
    payment_method: Optional[str] = Field(None, description="交费方式")
    effective_date: Optional[str] = Field(None, description="生效日期")
    insurance_period: Optional[str] = Field(None, description="保险期间")
    sales_manager: Optional[str] = Field(None, description="销售经理")


class PolicyResult(BaseModel):
    """单个保单的识别结果"""
    filename: str = Field(description="原始文件名")
    is_policy: bool = Field(description="是否为保单首页")
    fields: PolicyFields = Field(default_factory=PolicyFields, description="提取字段")
    status: str = Field(default="ok", description="状态: ok / low_confidence / not_policy / error")
    error_message: Optional[str] = Field(None, description="错误信息")
    raw_text: str = Field(default="", description="OCR 原始全文（所有文字块按阅读顺序拼接）")


class SensitiveStats(BaseModel):
    """敏感信息统计（按险种类型区分）"""
    # 人身险统计
    life_insured_count: int = Field(0, description="人身险被保人去重数")
    life_insured_list: list[str] = Field(default_factory=list, description="人身险被保人姓名列表")

    # 财产险统计
    property_count: int = Field(0, description="财产险保单数")
    property_applicant_list: list[str] = Field(default_factory=list, description="财产险投保人列表")

    # 未知分类
    unknown_count: int = Field(0, description="未分类保单数")

    # 总览
    total_applicant_count: int = Field(0, description="所有保单去重投保人数")
    total_insured_count: int = Field(0, description="仅人身险被保人去重数")
    sensitive_info_count: int = Field(0, description="涉敏信息条数（人身险被保人去重数 + 财产险保单数）")


class UploadResponse(BaseModel):
    """上传响应"""
    results: list[PolicyResult] = Field(description="识别结果列表")
    stats: SensitiveStats = Field(description="敏感信息统计")
