"""Pydantic 数据模型"""
from pydantic import BaseModel, Field
from typing import Optional


class PolicyFields(BaseModel):
    """单个保单的提取字段"""
    insurance_company: Optional[str] = Field(None, description="保险公司")
    policy_type: Optional[str] = Field(None, description="险种")
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


class SensitiveStats(BaseModel):
    """敏感信息统计"""
    total_unique_insured: int = Field(description="去重后的被保人数量")
    insured_list: list[str] = Field(description="被保人姓名列表（去重后）")
    details: list[PolicyResult] = Field(description="所有识别结果明细")


class UploadResponse(BaseModel):
    """上传响应"""
    results: list[PolicyResult] = Field(description="识别结果列表")
    stats: SensitiveStats = Field(description="敏感信息统计")
