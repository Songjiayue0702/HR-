"""
PDF 导出工具

用于导出简历分析报告：
- 应聘岗位
- 基本信息
- 教育信息
- 工作经历
- 简历匹配度分析
"""

import os
from datetime import datetime
from typing import Dict, Any, List

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from config import Config

# 全局中文字体名称
CH_FONT_NAME = "SimSun"


def _register_chinese_font() -> str:
    """
    注册中文字体，返回可用的字体名称。
    优先使用常见的 Windows 中文字体（宋体 / 黑体 / 微软雅黑）。
    """
    global CH_FONT_NAME

    # 已注册则直接返回
    try:
        pdfmetrics.getFont(CH_FONT_NAME)
        return CH_FONT_NAME
    except KeyError:
        pass

    font_candidates = [
        ("SimSun", r"C:\Windows\Fonts\simsun.ttc"),
        ("SimSun", r"C:\Windows\Fonts\simsun.ttf"),
        ("SimHei", r"C:\Windows\Fonts\simhei.ttf"),
        ("MSYH", r"C:\Windows\Fonts\msyh.ttc"),
        ("MSYH", r"C:\Windows\Fonts\msyh.ttf"),
    ]

    for name, path in font_candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                CH_FONT_NAME = name
                return CH_FONT_NAME
            except Exception:
                continue

    # 如果找不到中文字体，只能退回默认 Helvetica（中文会显示为方块）
    CH_FONT_NAME = "Helvetica"
    return CH_FONT_NAME


def _ensure_export_folder() -> str:
    """确保导出目录存在并返回路径"""
    export_folder = getattr(Config, "EXPORT_FOLDER", "exports")
    if not os.path.exists(export_folder):
        os.makedirs(export_folder, exist_ok=True)
    return export_folder


def _draw_wrapped_text(
    c: canvas.Canvas,
    text: str,
    x: int,
    y: int,
    max_width: int,
    leading: int = 16,
    min_y: int = 80,
    page_height: int = None,
) -> int:
    """
    在 PDF 上绘制自动换行的文本，并返回新的 y 坐标
    如果内容超过一页，会自动分页
    """
    if not text:
        return y

    font_name = CH_FONT_NAME
    if page_height is None:
        from reportlab.lib.pagesizes import A4
        _, page_height = A4

    current_line = ""
    for ch in text:
        if ch == "\n":
            # 检查是否需要换页
            if y < min_y:
                c.showPage()
                c.setFont(CH_FONT_NAME, 11)
                y = page_height - 60
            c.drawString(x, y, current_line)
            y -= leading
            current_line = ""
            continue

        if pdfmetrics.stringWidth(current_line + ch, font_name, 11) > max_width:
            # 检查是否需要换页
            if y < min_y:
                c.showPage()
                c.setFont(CH_FONT_NAME, 11)
                y = page_height - 60
            c.drawString(x, y, current_line)
            y -= leading
            current_line = ch
        else:
            current_line += ch

    if current_line:
        # 检查是否需要换页
        if y < min_y:
            c.showPage()
            c.setFont(CH_FONT_NAME, 11)
            y = page_height - 60
        c.drawString(x, y, current_line)
        y -= leading

    return y


def export_resume_analysis_to_pdf(resume, analysis: Dict[str, Any] | None) -> str:
    """
    导出简历分析报告为 PDF

    Args:
        resume: Resume 模型实例
        analysis: 匹配分析结果字典（可为空）

    Returns:
        生成的 PDF 文件路径
    """
    export_folder = _ensure_export_folder()
    _register_chinese_font()

    filename = f"resume_analysis_{resume.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(export_folder, filename)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    margin_left = 50
    margin_right = 50
    max_text_width = width - margin_left - margin_right

    y = height - 60

    # 标题
    c.setFont(CH_FONT_NAME, 16)
    c.drawString(margin_left, y, "简历分析报告")
    y -= 30

    c.setFont(CH_FONT_NAME, 11)

    def check_page_break(min_y: int = 80):
        """检查是否需要换页，如果需要则换页"""
        nonlocal y
        if y < min_y:
            c.showPage()
            c.setFont(CH_FONT_NAME, 11)
            y = height - 60
    
    def draw_section(title: str):
        nonlocal y
        check_page_break()
        c.setFont(CH_FONT_NAME, 12)
        c.drawString(margin_left, y, title)
        y -= 18
        c.setFont(CH_FONT_NAME, 11)

    # 一、应聘岗位
    draw_section("一、应聘岗位")
    applied_position = getattr(resume, "applied_position", "") or "-"
    y = _draw_wrapped_text(c, f"应聘岗位：{applied_position}", margin_left, y, max_text_width)
    y -= 10

    # 二、基本信息
    draw_section("二、基本信息")
    basic_lines = [
        f"姓名：{getattr(resume, 'name', '') or '-'}",
        f"性别：{getattr(resume, 'gender', '') or '-'}",
        f"出生年份：{getattr(resume, 'birth_year', '') or '-'}",
        f"年龄：{getattr(resume, 'age', '') or '-'}",
        f"手机号：{getattr(resume, 'phone', '') or '-'}",
        f"邮箱：{getattr(resume, 'email', '') or '-'}",
    ]
    for line in basic_lines:
        y = _draw_wrapped_text(c, line, margin_left, y, max_text_width)
    y -= 10

    # 三、教育信息
    draw_section("三、教育信息")
    edu_lines = [
        f"最高学历：{getattr(resume, 'highest_education', '') or '-'}",
        f"毕业学校：{getattr(resume, 'school', '') or '-'}",
        f"专业：{getattr(resume, 'major', '') or '-'}",
    ]
    for line in edu_lines:
        y = _draw_wrapped_text(c, line, margin_left, y, max_text_width)
    y -= 10

    # 四、工作经历
    draw_section("四、工作经历")
    work_exps: List[Dict[str, Any]] = getattr(resume, "work_experience", None) or []
    if not work_exps:
        check_page_break()
        y = _draw_wrapped_text(c, "暂无工作经历", margin_left, y, max_text_width)
    else:
        for idx, exp in enumerate(work_exps, start=1):
            check_page_break()
            company = exp.get("company") or "-"
            position = exp.get("position") or "-"
            start_year = exp.get("start_year")
            end_year = exp.get("end_year")

            if start_year and end_year:
                time_range = f"{start_year} - {end_year}"
            elif start_year and not end_year:
                time_range = f"{start_year} - 至今"
            elif not start_year and end_year:
                time_range = f"至 {end_year}"
            else:
                time_range = "-"

            line = f"{idx}. {company} | {position} | {time_range}"
            y = _draw_wrapped_text(c, line, margin_left, y, max_text_width)
    y -= 10

    # 五、简历匹配度分析
    draw_section("五、简历匹配度分析")
    if analysis:
        match_score = analysis.get("match_score", None)
        match_level = analysis.get("match_level", "")
        detailed = analysis.get("detailed_analysis", "") or ""
        strengths = analysis.get("strengths") or []
        weaknesses = analysis.get("weaknesses") or []
        suggestions = analysis.get("suggestions") or []

        if match_score is not None:
            y = _draw_wrapped_text(c, f"匹配度分数：{match_score}", margin_left, y, max_text_width)
        if match_level:
            y = _draw_wrapped_text(c, f"匹配等级：{match_level}", margin_left, y, max_text_width)
        y -= 5

        if detailed:
            check_page_break()
            y = _draw_wrapped_text(c, "详细分析：", margin_left, y, max_text_width)
            check_page_break()
            y = _draw_wrapped_text(c, detailed, margin_left + 20, y, max_text_width - 20)
            y -= 5

        if strengths:
            check_page_break()
            y = _draw_wrapped_text(c, "优势：", margin_left, y, max_text_width)
            for s in strengths:
                check_page_break()
                y = _draw_wrapped_text(c, f"• {s}", margin_left + 20, y, max_text_width - 20)
            y -= 5

        if weaknesses:
            check_page_break()
            y = _draw_wrapped_text(c, "不足：", margin_left, y, max_text_width)
            for w in weaknesses:
                check_page_break()
                y = _draw_wrapped_text(c, f"• {w}", margin_left + 20, y, max_text_width - 20)
            y -= 5

        if suggestions:
            check_page_break()
            y = _draw_wrapped_text(c, "面试重点考核项及对应面试问题：", margin_left, y, max_text_width)
            import re
            for s in suggestions:
                check_page_break()
                # 解析格式化的字符串：【考核重点】xxx - 【面试问题】xxx
                match = re.match(r'【考核重点】(.*?)\s*-\s*【面试问题】(.*)', s)
                if match:
                    focus = match.group(1).strip()
                    question = match.group(2).strip()
                    y = _draw_wrapped_text(c, f"• 【考核重点】{focus}", margin_left + 20, y, max_text_width - 20)
                    check_page_break()
                    y = _draw_wrapped_text(c, f"  【面试问题】{question}", margin_left + 40, y, max_text_width - 40)
                else:
                    # 如果没有匹配到格式，直接显示原内容
                    y = _draw_wrapped_text(c, f"• {s}", margin_left + 20, y, max_text_width - 20)
    else:
        y = _draw_wrapped_text(c, "暂无匹配度分析结果。请在系统中先执行一次匹配分析。", margin_left, y, max_text_width)

    c.showPage()
    c.save()

    return file_path


def export_interview_round_analysis_to_pdf(interview, round_name: str, analysis_text: str) -> str:
    """
    导出单轮面试反馈报告为 PDF

    内容顺序：
    1. 候选人信息
    2. 本轮面试详情（面试官、时间、是否通过、面试评价）
    3. AI 分析结果

    Args:
        interview: Interview 模型实例
        round_name: '一面'/'二面'/'三面'
        analysis_text: 已生成的 AI 分析文本
    """
    export_folder = _ensure_export_folder()
    _register_chinese_font()

    filename = f"interview_{interview.id}_{round_name}_面试反馈报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(export_folder, filename)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    margin_left = 50
    margin_right = 50
    max_text_width = width - margin_left - margin_right

    y = height - 60

    c.setFont(CH_FONT_NAME, 16)
    c.drawString(margin_left, y, f"{round_name}面试反馈报告")
    y -= 30

    c.setFont(CH_FONT_NAME, 11)

    # 一、候选人信息
    c.setFont(CH_FONT_NAME, 12)
    c.drawString(margin_left, y, "一、候选人信息")
    y -= 18
    c.setFont(CH_FONT_NAME, 11)

    basic_lines = [
        f"姓名：{getattr(interview, 'name', '') or '-'}",
        f"应聘岗位：{getattr(interview, 'applied_position', '') or '-'}",
        f"当前流程状态：{getattr(interview, 'status', '') or '-'}",
        f"简历匹配度：{getattr(interview, 'match_score', '') if getattr(interview, 'match_score', None) is not None else '-'}",
    ]
    for line in basic_lines:
        y = _draw_wrapped_text(c, line, margin_left, y, max_text_width)
    y -= 12

    # 二、本轮面试详情
    c.setFont(CH_FONT_NAME, 12)
    c.drawString(margin_left, y, "二、本轮面试详情")
    y -= 18
    c.setFont(CH_FONT_NAME, 11)

    # 按轮次取字段
    interviewer = "-"
    time_str = "-"
    result = "-"
    comment = ""

    if round_name == "一面":
        interviewer = getattr(interview, "round1_interviewer", "") or "-"
        time_val = getattr(interview, "round1_time", None)
        time_str = (str(time_val)[:10] if time_val else "-")
        result = getattr(interview, "round1_result", "") or "未填写"
        comment = getattr(interview, "round1_comment", "") or ""
    elif round_name == "二面":
        interviewer = getattr(interview, "round2_interviewer", "") or "-"
        time_val = getattr(interview, "round2_time", None)
        time_str = (str(time_val)[:10] if time_val else "-")
        result = getattr(interview, "round2_result", "") or "未填写"
        comment = getattr(interview, "round2_comment", "") or ""
    else:  # 三面
        interviewer = getattr(interview, "round3_interviewer", "") or "-"
        time_val = getattr(interview, "round3_time", None)
        time_str = (str(time_val)[:10] if time_val else "-")
        result = getattr(interview, "round3_result", "") or "未填写"
        comment = getattr(interview, "round3_comment", "") or ""

    detail_lines = [
        f"面试轮次：{round_name}",
        f"面试官：{interviewer}",
        f"面试时间：{time_str}",
        f"面试结果：{result}",
    ]
    for line in detail_lines:
        y = _draw_wrapped_text(c, line, margin_left, y, max_text_width)

    if comment:
        y = _draw_wrapped_text(c, "面试评价：", margin_left, y, max_text_width)
        y = _draw_wrapped_text(c, comment, margin_left + 20, y, max_text_width - 20)
    else:
        y = _draw_wrapped_text(c, "面试评价：暂无填写", margin_left, y, max_text_width)
    y -= 12

    # 三、AI 分析结果
    c.setFont(CH_FONT_NAME, 12)
    c.drawString(margin_left, y, "三、AI 分析结果")
    y -= 18
    c.setFont(CH_FONT_NAME, 11)

    if analysis_text:
        y = _draw_wrapped_text(c, analysis_text, margin_left, y, max_text_width)
    else:
        y = _draw_wrapped_text(
            c,
            "暂无AI分析结果，请先在系统中执行该轮面试的AI分析。",
            margin_left,
            y,
            max_text_width,
        )

    c.showPage()
    c.save()

    return file_path

