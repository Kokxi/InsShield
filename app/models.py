"""Pydantic 数据模型：以人为单位的涉敏统计"""
from pydantic import BaseModel, Field
from typing import Optional, List


class PIIItemModel(BaseModel):
    """单条个人信息"""
    type: str = Field(description="PII 类型: id_number/phone/bank_account/address/health/email/birth_date")
    value: str = Field(description="PII 值")
    raw_label: str = Field(default="", description="原文标签")


class PersonModel(BaseModel):
    """一个涉敏个体"""
    name: str = Field(default="", description="姓名，无姓名时为空")
    role: str = Field(default="", description="角色: applicant/insured/beneficiary/reporter/anonymous")
    role_display: str = Field(default="", description="角色中文名")
    details: List[PIIItemModel] = Field(default_factory=list, description="关联的 PII 列表")


# === 向后兼容：旧模型别名，供 field_extractor 和测试引用 ===
class PolicyFields(BaseModel):
    """保单字段（旧版模型，保持向后兼容）"""
    policy_type: str = ""
    policy_number: str = ""
    applicant: str = ""
    insured: Optional[str] = None
    beneficiary: str = ""
    premium: str = ""
    payment_method: str = ""
    effective_date: str = ""
    insurance_period: str = ""
    sales_manager: str = ""
    insurance_company: str = ""
    insurance_category: str = ""


class FileResult(BaseModel):
    """单份文件的识别结果"""
    filename: str = Field(description="文件名")
    is_insurance_related: bool = Field(default=False, description="是否保险相关文档")
    document_type: str = Field(default="unknown", description="文档类型")
    document_type_display: str = Field(default="未知", description="文档类型中文名")
    insurance_category: str = Field(default="unknown", description="险种类别: life/health/accident/car/property/unknown")
    insurance_category_display: str = Field(default="未知", description="险种中文名")
    insurance_branch: str = Field(default="unknown", description="保险大类分支: life/property/social/unknown")
    insurance_branch_display: str = Field(default="未知", description="保险大类分支中文名")
    anomaly: str = Field(default="", description="异常标记: ''/'财产险多人'等")
    insurance_company: str = Field(default="", description="保险公司")
    policy_number: str = Field(default="", description="保单号（如有）")
    persons: List[PersonModel] = Field(default_factory=list, description="涉敏人员列表")
    sensitive_count: int = Field(default=0, description="本文件涉敏人数")
    status: str = Field(default="ok", description="状态: ok/not_insurance/no_pii/error")
    error_message: Optional[str] = Field(None, description="错误信息")
    raw_text: str = Field(default="", description="OCR/提取原始全文")


class GlobalStats(BaseModel):
    """全局统计"""
    total_files: int = Field(default=0, description="总文件数")
    sensitive_files: int = Field(default=0, description="涉敏文件数")
    global_unique_persons: int = Field(default=0, description="全局去重涉敏人数（按姓名）")
    non_sensitive_files: int = Field(default=0, description="非涉敏文件数")
    life_sensitive_files: int = Field(default=0, description="人身险涉敏文件数")
    life_unique_persons: int = Field(default=0, description="人身险涉敏人数（去重）")
    property_files: int = Field(default=0, description="财产险文件数")
    property_sensitive_persons: int = Field(default=0, description="财产险涉敏人数")
    anomaly_files: int = Field(default=0, description="异常文件数")


class UploadResponse(BaseModel):
    """上传响应"""
    results: List[FileResult] = Field(description="文件识别结果")
    stats: GlobalStats = Field(description="全局统计")
