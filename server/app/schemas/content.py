from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("*", mode="before")
    @classmethod
    def reject_markup(cls, value: object) -> object:
        if isinstance(value, str):
            lowered = value.lower()
            if "<script" in lowered or "javascript:" in lowered or "data:text/html" in lowered:
                raise ValueError("内容不允许包含脚本或可执行 HTML")
        return value


class SeoContent(StrictModel):
    title: str = Field(min_length=2, max_length=70)
    description: str = Field(min_length=10, max_length=180)
    keywords: list[str] = Field(default_factory=list, max_length=12)


class NavigationItem(StrictModel):
    label: str = Field(min_length=1, max_length=20)
    anchor: str = Field(pattern=r"^#[a-z0-9-]+$")


class HeroContent(StrictModel):
    eyebrow: str = Field(max_length=36)
    title: str = Field(min_length=8, max_length=42)
    description: str = Field(min_length=16, max_length=180)
    primary_label: str = Field(min_length=2, max_length=16)
    secondary_label: str = Field(min_length=2, max_length=16)
    image_alt: str = Field(min_length=6, max_length=160)
    image_asset_id: str | None = Field(default=None, max_length=36)


class CapabilityItem(StrictModel):
    key: str = Field(pattern=r"^[a-z0-9-]+$")
    title: str = Field(min_length=2, max_length=32)
    description: str = Field(min_length=8, max_length=120)


class WorkflowItem(StrictModel):
    step: str = Field(pattern=r"^[0-9]{2}$")
    title: str = Field(min_length=2, max_length=24)
    description: str = Field(min_length=6, max_length=100)


class TiciContent(StrictModel):
    eyebrow: str = Field(max_length=36)
    title: str = Field(min_length=4, max_length=48)
    description: str = Field(min_length=20, max_length=260)
    points: list[str] = Field(min_length=2, max_length=6)
    image_alt: str = Field(min_length=6, max_length=160)
    image_asset_id: str | None = Field(default=None, max_length=36)


class ProgressItem(StrictModel):
    status: Literal["implemented", "researching", "pending"]
    label: str = Field(min_length=2, max_length=12)
    title: str = Field(min_length=2, max_length=38)
    description: str = Field(min_length=8, max_length=140)


class SafetyContent(StrictModel):
    title: str = Field(min_length=4, max_length=40)
    statements: list[str] = Field(min_length=4, max_length=8)


class BackgroundContent(StrictModel):
    title: str = Field(min_length=2, max_length=40)
    description: str = Field(min_length=12, max_length=220)
    affiliation: str = Field(min_length=4, max_length=80)


class DownloadContent(StrictModel):
    eyebrow: str = Field(max_length=36)
    title: str = Field(min_length=4, max_length=42)
    description: str = Field(min_length=12, max_length=180)
    button_label: str = Field(min_length=2, max_length=20)
    fallback_note: str = Field(min_length=4, max_length=100)


class FooterContent(StrictModel):
    summary: str = Field(min_length=6, max_length=120)
    copyright: str = Field(min_length=4, max_length=100)
    icp_number: str = Field(default="辽ICP备2026005104号-2", max_length=50)


class SectionOrder(StrictModel):
    key: Literal[
        "capabilities", "workflow", "tici", "progress", "safety", "background", "download"
    ]
    visible: bool = True


class PublishedSiteContent(StrictModel):
    schema_version: Literal[1] = 1
    seo: SeoContent
    navigation: list[NavigationItem] = Field(min_length=3, max_length=8)
    hero: HeroContent
    capabilities_title: str = Field(min_length=4, max_length=48)
    capabilities_intro: str = Field(min_length=12, max_length=180)
    capabilities: list[CapabilityItem] = Field(min_length=3, max_length=8)
    workflow_title: str = Field(min_length=4, max_length=48)
    workflow: list[WorkflowItem] = Field(min_length=3, max_length=8)
    tici: TiciContent
    progress_title: str = Field(min_length=4, max_length=48)
    progress: list[ProgressItem] = Field(min_length=3, max_length=9)
    safety: SafetyContent
    background: BackgroundContent
    download: DownloadContent
    footer: FooterContent
    section_order: list[SectionOrder] = Field(min_length=7, max_length=7)

    @model_validator(mode="after")
    def validate_unique_keys(self) -> "PublishedSiteContent":
        keys = [item.key for item in self.capabilities]
        if len(keys) != len(set(keys)):
            raise ValueError("产品能力 key 不可重复")
        anchors = [item.anchor for item in self.navigation]
        if len(anchors) != len(set(anchors)):
            raise ValueError("导航锚点不可重复")
        section_keys = [item.key for item in self.section_order]
        if len(section_keys) != len(set(section_keys)):
            raise ValueError("栏目顺序不可重复")
        return self


def default_site_content() -> PublishedSiteContent:
    return PublishedSiteContent.model_validate(
        {
            "schema_version": 1,
            "seo": {
                "title": "朗泰 LungTic｜面向 4D 肺部影像的科研工作台",
                "description": "围绕呼吸运动影像核验、辅助勾画、IGTV 重建与运动分析打造的医学影像科研原型。",
                "keywords": ["LungTic", "4D CT", "呼吸运动", "医学影像科研"],
            },
            "navigation": [
                {"label": "产品能力", "anchor": "#capabilities"},
                {"label": "工作流", "anchor": "#workflow"},
                {"label": "TICI", "anchor": "#tici"},
                {"label": "项目进展", "anchor": "#progress"},
                {"label": "下载", "anchor": "#download"},
            ],
            "hero": {
                "eyebrow": "LUNGTIC · 4D 肺部影像科研工作台",
                "title": "让呼吸运动不再成为精准放疗的盲区",
                "description": "在同一条可复核的工作流中浏览多时相影像、叠加 Mask、重建 IGTV，并观察随呼吸变化的运动轨迹。",
                "primary_label": "下载体验版",
                "secondary_label": "了解工作流",
                "image_alt": "LungTic 工作台显示肺部 CT、时相列表、分割叠加和 TICI 曲线",
            },
            "capabilities_title": "把分散的影像步骤放回一条工作流",
            "capabilities_intro": "聚焦研究过程中最需要反复核验的环节，并保留每一步的人工复核入口。",
            "capabilities": [
                {"key": "phases", "title": "多时相浏览", "description": "按呼吸时相组织影像，在同一视图中快速切换与比对。"},
                {"key": "mask", "title": "Mask 叠加", "description": "以清晰边界叠加分割结果，辅助发现轮廓与影像间的不一致。"},
                {"key": "cine", "title": "Cine 播放", "description": "连续播放呼吸周期，直观观察目标区域的形态与位置变化。"},
                {"key": "igtv", "title": "IGTV 重建", "description": "汇总各时相信息，形成可继续复核的研究输出。"},
                {"key": "motion", "title": "运动分析", "description": "以时间连续视角组织位移变化，支持进一步研究分析。"},
                {"key": "review", "title": "结果复核", "description": "将关键结果与原始影像并置，保留人工确认和导出环节。"},
            ],
            "workflow_title": "从影像核验到结果导出",
            "workflow": [
                {"step": "01", "title": "影像核验", "description": "检查序列、时相与基础影像质量。"},
                {"step": "02", "title": "辅助勾画", "description": "查看并修订候选区域与轮廓。"},
                {"step": "03", "title": "IGTV", "description": "汇总多时相信息形成研究结果。"},
                {"step": "04", "title": "运动分析", "description": "观察连续变化与运动趋势。"},
                {"step": "05", "title": "复核与导出", "description": "回到原始证据完成确认与留存。"},
            ],
            "tici": {
                "eyebrow": "TIME-SERIES IMAGE CONTINUUM",
                "title": "把离散时相组织成可追溯的连续表达",
                "description": "TICI 是 Time-series Image Continuum 的缩写，用于封装时序影像、相关标注与分析结果，帮助研究者在连续变化和原始时相之间往返核验。它描述的是项目中的数据组织与呈现思路，不代表已验证的临床结论。",
                "points": ["保留原始时相索引", "关联影像、标注与分析结果", "支持连续观察与逐帧复核"],
                "image_alt": "合成 TICI 示例显示呼吸周期时间轴和肺部轮廓变化",
            },
            "progress_title": "研发状态，清楚标注",
            "progress": [
                {"status": "implemented", "label": "已实现", "title": "多时相影像浏览与基础复核", "description": "已在研究原型中提供基本浏览、叠加与交互能力。"},
                {"status": "researching", "label": "研究中", "title": "TICI 连续表达与运动分析", "description": "持续优化数据组织、可视化方式和研究流程。"},
                {"status": "pending", "label": "待验证", "title": "临床环境中的系统性验证", "description": "尚需在合规前提下完成更充分的测试与评估。"},
            ],
            "safety": {
                "title": "使用边界",
                "statements": ["当前为科研原型", "仅用于辅助研究与决策参考", "不替代医生的专业判断", "不得直接用于患者治疗决策"],
            },
            "background": {
                "title": "项目背景",
                "description": "朗泰 LungTic 源于跨专业学生团队对 4D 肺部影像研究流程的探索，聚焦影像查看、组织、分析与复核体验。",
                "affiliation": "大连交通大学创新训练项目",
            },
            "download": {
                "eyebrow": "TICI VIEWER",
                "title": "从独立查看器开始体验",
                "description": "公开下载仅包含可独立运行的 TICI Viewer；依赖医院中心服务的临床客户端不对外提供。",
                "button_label": "下载体验版",
                "fallback_note": "当前版本暂未发布，请稍后再来。",
            },
            "footer": {
                "summary": "面向 4D 肺部影像研究的可视化工作台。",
                "copyright": "© 2026 朗泰 LungTic",
                "icp_number": "辽ICP备2026005104号-2",
            },
            "section_order": [
                {"key": "capabilities", "visible": True},
                {"key": "workflow", "visible": True},
                {"key": "tici", "visible": True},
                {"key": "progress", "visible": True},
                {"key": "safety", "visible": True},
                {"key": "background", "visible": True},
                {"key": "download", "visible": True},
            ],
        }
    )
