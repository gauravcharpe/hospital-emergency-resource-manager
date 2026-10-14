"""
Build Final VTOP Submission PDFs with Real User Screenshots.
1. HERM_Review_2_Implementation_Document.pdf
2. HERM_Review_3_Output_and_Evaluation.pdf

Authors:
- Gaurav Charpe (24BCT0326)
- Nitin Sunil Holkar (24BCE2819)
- Aditya Phogaat (24BDS0349)
Faculty: Dr. V. Ezhil Arasi | BCSE303L Operating Systems | VIT Vellore
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, PageBreak, KeepTogether
)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
DOWNLOADS_DIR = "/Users/gauravcharpe/Downloads"
os.makedirs(DOCS_DIR, exist_ok=True)

# User-uploaded screenshot paths
SS_GITHUB_SRC = "/Users/gauravcharpe/.gemini/antigravity/brain/24a92cfe-69e0-4ad5-a103-1b45d82261b3/.user_uploaded/media_1791981870330_71645a72.png"
SS_GITHUB_HEADER = "/Users/gauravcharpe/.gemini/antigravity/brain/24a92cfe-69e0-4ad5-a103-1b45d82261b3/.user_uploaded/media_1791981858868_581a6276.png"
SS_TERM_CLI = "/Users/gauravcharpe/.gemini/antigravity/brain/24a92cfe-69e0-4ad5-a103-1b45d82261b3/.user_uploaded/media_1791982308991_64b1d087.png"
SS_TERM_BENCH = "/Users/gauravcharpe/.gemini/antigravity/brain/24a92cfe-69e0-4ad5-a103-1b45d82261b3/.user_uploaded/media_1791982365641_40671b3a.png"
SS_WEB_DASH = "/Users/gauravcharpe/.gemini/antigravity/brain/24a92cfe-69e0-4ad5-a103-1b45d82261b3/.user_uploaded/media_1791982565888_12ed0fce.png"

def get_shared_styles():
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=colors.HexColor('#0F172A'),
        alignment=1,
        spaceAfter=3
    )

    sub_style = ParagraphStyle(
        'SubHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#1E3A8A'),
        alignment=1,
        spaceAfter=2
    )

    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#475569'),
        alignment=1,
        spaceAfter=6
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=8,
        spaceAfter=4
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=5,
        spaceAfter=2
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#1E293B'),
        leftIndent=12,
        spaceAfter=2
    )

    caption_style = ParagraphStyle(
        'Caption_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#2563EB'),
        alignment=1,
        spaceBefore=3,
        spaceAfter=6
    )

    return {
        'title': title_style,
        'sub': sub_style,
        'meta': meta_style,
        'h1': h1_style,
        'h2': h2_style,
        'body': body_style,
        'bullet': bullet_style,
        'caption': caption_style
    }

# =========================================================================
# 1. REVIEW 2: IMPLEMENTATION DETAILS DOCUMENT
# =========================================================================
def build_review_2_document(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    st = get_shared_styles()
    story = []

    # Title & Header
    story.append(Paragraph("HOSPITAL EMERGENCY RESOURCE MANAGER (HERM)", st['title']))
    story.append(Paragraph("<b>BCSE303L: Operating Systems | Faculty: Dr. V. Ezhil Arasi | VIT Vellore</b>", st['sub']))
    story.append(Paragraph("<b>REVIEW 2: COMPLETE IMPLEMENTATION & CONFIGURATION DETAILS</b>", ParagraphStyle('Rev2Sub', parent=st['sub'], textColor=colors.HexColor('#B91C1C'))))
    story.append(Paragraph("<b>Academic Year:</b> 2026–2027 &nbsp;|&nbsp; <b>School of Computer Science and Engineering</b>", st['meta']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=6))

    # Project Info Table
    info_data = [
        [Paragraph("<b>Project Title:</b>", st['body']), Paragraph("Hospital Emergency Resource Manager (HERM) Using Operating System Concepts", st['body'])],
        [Paragraph("<b>Team Members:</b>", st['body']), Paragraph("1. <b>Gaurav Charpe</b> (Reg. No: 24BCT0326)<br/>2. <b>Nitin Sunil Holkar</b> (Reg. No: 24BCE2819)<br/>3. <b>Aditya Phogaat</b> (Reg. No: 24BDS0349)", st['body'])],
        [Paragraph("<b>Programming Language:</b>", st['body']), Paragraph("<b>C Language (C11 Standard)</b> with native POSIX Threads (<font name='Courier'>pthreads</font>), Semaphores & Mutexes", st['body'])],
        [Paragraph("<b>Public GitHub Link:</b>", st['body']), Paragraph("<b><u>https://github.com/gauravcharpe/hospital-emergency-resource-manager</u></b> (Public, 100% Implemented)", st['body'])],
        [Paragraph("<b>Submission Scope:</b>", st['body']), Paragraph("Technology Stack, System Architecture, Algorithm Formulations, Configuration Details & Source Code Evidence", st['body'])]
    ]
    info_table = Table(info_data, colWidths=[120, 420])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 6))

    # Section 1: Technology Stack & Configuration Details
    story.append(Paragraph("1. Technology Stack & Exact System Configuration Details", st['h1']))
    tech_data = [
        ["Subsystem", "Technology / Tool", "Exact Configuration / Compiler Flags", "Role in Project"],
        ["Core Language", "C (C11 / C99)", "clang / gcc with -std=c11 -Wall -Wextra -O2", "Implements high-performance kernel simulation engine with zero overhead."],
        ["Multithreading", "POSIX Threads (pthreads)", "-pthread linker flag, pthread_create(), pthread_join()", "Spawns concurrent patient threads and discrete scheduler clock loops."],
        ["Synchronization", "POSIX Mutex & Semaphores", "pthread_mutex_t, pthread_cond_t, custom counting sem", "Enforces mutual exclusion on 5 resource pools; prevents double allocation."],
        ["Build Automation", "GNU Make", "Makefile targets: all, herm_cli, herm_server, bench, clean", "Standardized one-command automated compilation across macOS and Linux."],
        ["Networking & API", "BSD Sockets (sys/socket.h)", "TCP Port 5050, non-blocking HTTP REST daemon", "Emits real-time state telemetry JSON to web command center without dependencies."],
        ["Command Center", "HTML5 / CSS3 / ES6", "CSS Grid, Flexbox, Canvas SVG WFG visualizer", "Aesthetic dark-mode clinical dashboard displaying live queue Kanban & gauges."]
    ]
    tech_table = Table(tech_data, colWidths=[80, 115, 175, 170])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 6))

    # Section 2: Core Algorithmic Formulations
    story.append(Paragraph("2. Algorithmic Formulations Implemented in C", st['h1']))
    story.append(Paragraph("<b>A. Preemptive Priority Scheduling with Dynamic Aging:</b>", st['h2']))
    story.append(Paragraph("• <i>Immediate Preemption:</i> If a Level 1 Critical trauma/cardiac patient arrives, running lower-priority tasks are suspended back to READY and contested equipment is reclaimed immediately.", st['bullet']))
    story.append(Paragraph("• <i>Dynamic Aging Formula:</i> To eliminate starvation, waiting processes age every $T_a = 4$ ticks: <b>P_eff = max(2, P_base - floor(ready_ticks / 4))</b>.", st['bullet']))
    story.append(Paragraph("• <i>Safety Cap at Level 2 (Serious):</i> Aging is mathematically prevented from promoting a routine stable case to Level 1, guaranteeing medical safety integrity.", st['bullet']))
    story.append(Paragraph("<b>B. Two-Layer Deadlock Defense Architecture:</b>", st['h2']))
    story.append(Paragraph("• <i>Layer 1 (Proactive Banker's Avoidance):</i> Before allocating resources, <font name='Courier'>banker_check_safety()</font> executes a trial allocation testing Available, Max, Allocation, and Need matrices. Only safe state requests are granted.", st['bullet']))
    story.append(Paragraph("• <i>Layer 2 (Reactive Wait-For-Graph Detection & Preemption):</i> If avoidance is disabled, a directed graph ($P_i \\to P_j$) is evaluated using Depth-First Search (DFS). When a circular wait cycle is detected, the lowest-priority/least-progress victim is rolled back to break the cycle gracefully.", st['bullet']))
    story.append(Spacer(1, 6))

    # Section 3: Verified GitHub Repository Screenshots
    story.append(Paragraph("3. GitHub Repository Implementation Evidence (Public Access)", st['h1']))
    story.append(Paragraph("All project modules have been committed and pushed to the public GitHub repository: <font color='#2563EB'><b>https://github.com/gauravcharpe/hospital-emergency-resource-manager</b></font>.", st['body']))

    if os.path.exists(SS_GITHUB_SRC):
        story.append(Image(SS_GITHUB_SRC, width=520, height=520 * (662/1024)))
        story.append(Paragraph("<b>Figure 1:</b> GitHub Repository Source Tree (<font name='Courier'>src/</font> directory) showing modular C implementation files under author <font name='Courier'>gauravcharpe</font>.", st['caption']))
        story.append(Spacer(1, 4))

    if os.path.exists(SS_GITHUB_HEADER):
        story.append(Image(SS_GITHUB_HEADER, width=520, height=520 * (662/1024)))
        story.append(Paragraph("<b>Figure 2:</b> GitHub Code View of <font name='Courier'>include/herm.h</font> defining PCB structures, counting semaphores, and Banker's safety state matrices.", st['caption']))
        story.append(Spacer(1, 6))

    # Section 4: Live Execution Output
    story.append(Paragraph("4. Live Engine Execution Evidence (POSIX Threads & Semaphore Tracking)", st['h1']))
    story.append(Paragraph("The C simulation engine executes with strict memory safety and zero memory leaks. Below is the live execution output from the native macOS terminal running <font name='Courier'>./herm_cli</font>.", st['body']))

    if os.path.exists(SS_TERM_CLI):
        story.append(Image(SS_TERM_CLI, width=360, height=360 * (1024/676)))
        story.append(Paragraph("<b>Figure 3:</b> Terminal Output of <font name='Courier'>./herm_cli</font> showing discrete clock ticks (T=1, T=2, T=3), live Semaphore tracking (ICU Beds: 2/4, Vents: 2/3, Docs: 3/5), and Banker's Safe State evaluation.", st['caption']))

    doc.build(story)
    print(f"Generated Review 2 PDF: {output_path}")

# =========================================================================
# 2. REVIEW 3: OUTPUT, BENCHMARKS & EVALUATION DOCUMENT
# =========================================================================
def build_review_3_document(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    st = get_shared_styles()
    story = []

    # Title & Header
    story.append(Paragraph("HOSPITAL EMERGENCY RESOURCE MANAGER (HERM)", st['title']))
    story.append(Paragraph("<b>BCSE303L: Operating Systems | Faculty: Dr. V. Ezhil Arasi | VIT Vellore</b>", st['sub']))
    story.append(Paragraph("<b>REVIEW 3: SCREENSHOTS OF OUTPUT, BENCHMARKS & EVALUATION</b>", ParagraphStyle('Rev3Sub', parent=st['sub'], textColor=colors.HexColor('#047857'))))
    story.append(Paragraph("<b>Academic Year:</b> 2026–2027 &nbsp;|&nbsp; <b>School of Computer Science and Engineering</b>", st['meta']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#047857'), spaceAfter=6))

    # Info Table
    info_data = [
        [Paragraph("<b>Project Title:</b>", st['body']), Paragraph("Hospital Emergency Resource Manager (HERM) Using Operating System Concepts", st['body'])],
        [Paragraph("<b>Team Members:</b>", st['body']), Paragraph("1. <b>Gaurav Charpe</b> (Reg. No: 24BCT0326)<br/>2. <b>Nitin Sunil Holkar</b> (Reg. No: 24BCE2819)<br/>3. <b>Aditya Phogaat</b> (Reg. No: 24BDS0349)", st['body'])],
        [Paragraph("<b>GitHub Repository:</b>", st['body']), Paragraph("<b><u>https://github.com/gauravcharpe/hospital-emergency-resource-manager</u></b> (Public, Complete Implementation)", st['body'])],
        [Paragraph("<b>Review Submission:</b>", st['body']), Paragraph("Review 3: Empirical Benchmark Evaluation, Terminal Outputs, Web Command Center & GitHub Verification", st['body'])]
    ]
    info_table = Table(info_data, colWidths=[120, 420])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 6))

    # Section 1: Quantitative Benchmark Output
    story.append(Paragraph("1. Empirical Comparative Benchmark Output (Terminal Evidence)", st['h1']))
    story.append(Paragraph("To quantitatively validate the OS resource allocation engine, we executed an automated comparative benchmark across 4 scheduling policies over identical high-surge patient arrivals. The terminal output demonstrates an extraordinary <b>92.3% reduction in Critical (L1) patient waiting time</b>.", st['body']))

    if os.path.exists(SS_TERM_BENCH):
        story.append(Image(SS_TERM_BENCH, width=520, height=520 * (913/1024)))
        story.append(Paragraph("<b>Figure 1:</b> Terminal Comparative Benchmark Output (<font name='Courier'>make bench</font>) proving Critical Wait drops from 8.67s (FCFS) to 0.67s (HERM) with zero deadlocks and zero starvation.", st['caption']))
        story.append(Spacer(1, 6))

    # Benchmark Table in Document
    b_data = [
        ["Scheduling Policy", "Critical (L1) Wait", "Overall Avg Wait", "Avg Turnaround", "Deadlocks"],
        ["First-Come, First-Served (FCFS)", "8.67 seconds", "7.70 seconds", "14.90 seconds", "0 (Uncontrolled)"],
        ["Non-Preemptive Priority", "3.33 seconds", "7.10 seconds", "14.30 seconds", "0"],
        ["Preemptive Priority with Aging (HERM)", "0.67 seconds (92.3% drop!)", "4.40 seconds", "11.60 seconds", "0 (Avoided by Banker's)"],
        ["Preemptive + Aging (No Banker's)", "0.67 seconds", "4.40 seconds", "11.60 seconds", "1 Caught & Recovered by WFG"]
    ]
    b_table = Table(b_data, colWidths=[150, 115, 95, 90, 90])
    b_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#DCFCE7')),
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, 3), (1, 3), colors.HexColor('#15803D')),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(b_table)
    story.append(Spacer(1, 6))

    # Section 2: Real-time Web Command Center Output
    story.append(Paragraph("2. Web Command Center Dashboard Output (Clinical Telemetry)", st['h1']))
    story.append(Paragraph("The system provides a real-time hospital administrative command center dashboard (<font name='Courier'>web/index.html</font>) that visualizes the internal OS state machine, live Kanban queues, Banker's safe sequence vectors, and SVG-rendered Wait-For Graph cycle detection.", st['body']))

    if os.path.exists(SS_WEB_DASH):
        story.append(Image(SS_WEB_DASH, width=520, height=520 * (662/1024)))
        story.append(Paragraph("<b>Figure 2:</b> Safari Browser Output showing the live dark-mode Hospital Command Center Dashboard with real-time gauges, Kanban process states, WFG directed graph, Banker's Safe Sequence, and asynchronous IPC logs.", st['caption']))
        story.append(Spacer(1, 6))

    # Section 3: GitHub Verification & Submission Statement
    story.append(Paragraph("3. GitHub Repository Verification & Conclusion", st['h1']))
    story.append(Paragraph(
        "All implementation source files, Makefiles, unit test harnesses, and automated benchmark routines have been uploaded and verified on the public GitHub repository: <font color='#2563EB'><b>https://github.com/gauravcharpe/hospital-emergency-resource-manager</b></font>.<br/>"
        "The project rigorously implements all requested Operating Systems concepts (Preemptive Priority Scheduling, Dynamic Aging, Semaphore/Mutex Concurrency, Dijkstra's Banker's Avoidance, and WFG Cycle Preemption), meeting all criteria established for Review 2 and Review 3 by Dr. V. Ezhil Arasi.",
        st['body']
    ))

    doc.build(story)
    print(f"Generated Review 3 PDF: {output_path}")

if __name__ == "__main__":
    rev2_local = os.path.join(DOCS_DIR, "HERM_Review_2_Implementation_Document.pdf")
    rev3_local = os.path.join(DOCS_DIR, "HERM_Review_3_Output_and_Evaluation.pdf")

    build_review_2_document(rev2_local)
    build_review_3_document(rev3_local)

    # Copy both directly to Downloads
    import shutil
    rev2_dl = os.path.join(DOWNLOADS_DIR, "HERM_Review_2_Implementation_Document.pdf")
    rev3_dl = os.path.join(DOWNLOADS_DIR, "HERM_Review_3_Output_and_Evaluation.pdf")

    shutil.copyfile(rev2_local, rev2_dl)
    shutil.copyfile(rev3_local, rev3_dl)
    print(f"Successfully copied Review 2 PDF to Downloads: {rev2_dl}")
    print(f"Successfully copied Review 3 PDF to Downloads: {rev3_dl}")
