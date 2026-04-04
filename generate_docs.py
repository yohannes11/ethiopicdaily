"""
Ethiopian Daily — Developer Documentation Generator
Produces a structured PDF using reportlab.
Run with:  python generate_docs.py
"""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, Image, NextPageTemplate,
    PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether,
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.colors import HexColor

# ── Palette ───────────────────────────────────────────────────────────────────
NAVY      = HexColor('#0f4c81')
NAVY_DARK = HexColor('#0b3a63')
GOLD      = HexColor('#d8a038')
SLATE     = HexColor('#334155')
LIGHT     = HexColor('#f1f5f9')
MID_GRAY  = HexColor('#94a3b8')
CODE_BG   = HexColor('#f8fafc')
CODE_FG   = HexColor('#1e3a5f')
WHITE     = colors.white
BLACK     = colors.black
GREEN     = HexColor('#059669')
AMBER     = HexColor('#d97706')
RED       = HexColor('#dc2626')

W, H = A4   # 595 x 842 pt

# ── Style sheet ───────────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()

    def add(name, **kw):
        base.add(ParagraphStyle(name=name, **kw))

    add('CoverTitle',
        fontName='Helvetica-Bold', fontSize=32, leading=40,
        textColor=WHITE, alignment=TA_CENTER, spaceAfter=8)
    add('CoverSub',
        fontName='Helvetica', fontSize=14, leading=20,
        textColor=HexColor('#bfdbfe'), alignment=TA_CENTER, spaceAfter=4)
    add('CoverMeta',
        fontName='Helvetica', fontSize=10, leading=14,
        textColor=HexColor('#93c5fd'), alignment=TA_CENTER)

    add('H1',
        fontName='Helvetica-Bold', fontSize=20, leading=26,
        textColor=NAVY, spaceBefore=18, spaceAfter=8,
        borderPadding=(0, 0, 4, 0))
    add('H2',
        fontName='Helvetica-Bold', fontSize=14, leading=20,
        textColor=NAVY_DARK, spaceBefore=14, spaceAfter=6)
    add('H3',
        fontName='Helvetica-Bold', fontSize=11, leading=16,
        textColor=SLATE, spaceBefore=10, spaceAfter=4)

    add('Body',
        fontName='Helvetica', fontSize=10, leading=15,
        textColor=SLATE, spaceAfter=6, alignment=TA_JUSTIFY)
    add('BodyBold',
        fontName='Helvetica-Bold', fontSize=10, leading=15,
        textColor=SLATE, spaceAfter=6)
    add('MyBullet',
        fontName='Helvetica', fontSize=10, leading=14,
        textColor=SLATE, leftIndent=14, bulletIndent=4,
        spaceAfter=3, bulletFontName='Helvetica', bulletFontSize=10)
    add('SubBullet',
        fontName='Helvetica', fontSize=9.5, leading=13,
        textColor=MID_GRAY, leftIndent=28, bulletIndent=18,
        spaceAfter=2)

    add('MyCode',
        fontName='Courier', fontSize=8.5, leading=13,
        textColor=CODE_FG, backColor=CODE_BG,
        leftIndent=10, rightIndent=10,
        borderPadding=(6, 8, 6, 8),
        spaceAfter=8, spaceBefore=4)
    add('InlineCode',
        fontName='Courier', fontSize=9,
        textColor=CODE_FG)

    add('TableHeader',
        fontName='Helvetica-Bold', fontSize=9,
        textColor=WHITE, alignment=TA_CENTER)
    add('TableCell',
        fontName='Helvetica', fontSize=9, leading=13,
        textColor=SLATE)
    add('TableCellCode',
        fontName='Courier', fontSize=8.5,
        textColor=CODE_FG)
    add('Caption',
        fontName='Helvetica-Oblique', fontSize=8.5, leading=12,
        textColor=MID_GRAY, alignment=TA_CENTER, spaceAfter=10)

    add('TOCEntry1',
        fontName='Helvetica-Bold', fontSize=11, leading=16,
        textColor=NAVY, leftIndent=0, spaceAfter=4)
    add('TOCEntry2',
        fontName='Helvetica', fontSize=10, leading=14,
        textColor=SLATE, leftIndent=16, spaceAfter=2)

    add('Note',
        fontName='Helvetica-Oblique', fontSize=9.5, leading=14,
        textColor=HexColor('#0369a1'), backColor=HexColor('#e0f2fe'),
        leftIndent=10, rightIndent=10, borderPadding=(6, 8, 6, 8),
        spaceAfter=8, spaceBefore=4)

    return base


# ── Page templates ─────────────────────────────────────────────────────────────
MARGIN = 18 * mm

def cover_page(canvas, doc):
    canvas.saveState()
    # Full-bleed navy gradient rectangle
    canvas.setFillColor(NAVY_DARK)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    # Accent bar
    canvas.setFillColor(GOLD)
    canvas.rect(0, H - 6, W, 6, fill=1, stroke=0)
    # Bottom stripe
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, W, 60, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(HexColor('#93c5fd'))
    canvas.drawCentredString(W / 2, 22, 'Ethiopian Daily Newsroom Platform — Developer Reference')
    canvas.restoreState()


def normal_page(canvas, doc):
    canvas.saveState()
    # Top rule
    canvas.setStrokeColor(NAVY)
    canvas.setLineWidth(2)
    canvas.line(MARGIN, H - 14 * mm, W - MARGIN, H - 14 * mm)
    # Header text
    canvas.setFont('Helvetica-Bold', 8)
    canvas.setFillColor(NAVY)
    canvas.drawString(MARGIN, H - 11 * mm, 'Ethiopian Daily — Developer Documentation')
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(MID_GRAY)
    canvas.drawRightString(W - MARGIN, H - 11 * mm, f'Page {doc.page}')
    # Bottom rule
    canvas.setStrokeColor(LIGHT)
    canvas.setLineWidth(1)
    canvas.line(MARGIN, 12 * mm, W - MARGIN, 12 * mm)
    canvas.setFont('Helvetica', 7.5)
    canvas.setFillColor(MID_GRAY)
    canvas.drawCentredString(W / 2, 8 * mm, '© Ethiopian Daily · Confidential')
    canvas.restoreState()


# ── Helper builders ────────────────────────────────────────────────────────────
def S(style_name, styles):
    return styles[style_name]

def h1(text, styles): return Paragraph(text, styles['H1'])
def h2(text, styles): return Paragraph(text, styles['H2'])
def h3(text, styles): return Paragraph(text, styles['H3'])
def body(text, styles): return Paragraph(text, styles['Body'])
def bold(text, styles): return Paragraph(text, styles['BodyBold'])
def note(text, styles): return Paragraph(f'<b>Note:</b> {text}', styles['Note'])
def sp(n=6): return Spacer(1, n)
def rule(color=LIGHT, thickness=1):
    return HRFlowable(width='100%', thickness=thickness, color=color, spaceAfter=8, spaceBefore=4)

def code_block(text, styles):
    escaped = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return Paragraph(escaped, styles['MyCode'])

def bullet(text, styles, level=1):
    style = 'MyBullet' if level == 1 else 'SubBullet'
    marker = '•' if level == 1 else '–'
    return Paragraph(f'{marker}  {text}', styles[style])

def field_table(rows, styles, col_widths=None):
    """Render a two-column [Field, Description] table."""
    if col_widths is None:
        col_widths = [55 * mm, 110 * mm]
    header = [
        Paragraph('Field / Item', styles['TableHeader']),
        Paragraph('Description', styles['TableHeader']),
    ]
    data = [header] + [
        [Paragraph(str(r[0]), styles['TableCellCode']),
         Paragraph(str(r[1]), styles['TableCell'])]
        for r in rows
    ]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.4, HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, 0), 1, GOLD),
    ]))
    return t

def url_table(rows, styles):
    """Render a three-column [Method, URL, View] table."""
    col_widths = [18 * mm, 72 * mm, 75 * mm]
    header = [
        Paragraph('Method', styles['TableHeader']),
        Paragraph('URL Pattern', styles['TableHeader']),
        Paragraph('View / Purpose', styles['TableHeader']),
    ]
    data = [header] + [
        [Paragraph(str(r[0]), styles['TableCellCode']),
         Paragraph(str(r[1]), styles['TableCellCode']),
         Paragraph(str(r[2]), styles['TableCell'])]
        for r in rows
    ]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.4, HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, 0), 1, GOLD),
    ]))
    return t


# ── Section badge ──────────────────────────────────────────────────────────────
def section_badge(number, title, styles):
    data = [[
        Paragraph(f'<font color="white"><b>{number}</b></font>', ParagraphStyle('bn', fontName='Helvetica-Bold', fontSize=13, textColor=WHITE, alignment=TA_CENTER)),
        Paragraph(f'<font color="white"><b>{title}</b></font>', ParagraphStyle('bt', fontName='Helvetica-Bold', fontSize=16, textColor=WHITE, leading=22)),
    ]]
    t = Table(data, colWidths=[12 * mm, W - 2 * MARGIN - 12 * mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (0, 0), 10),
        ('LEFTPADDING', (1, 0), (1, 0), 10),
        ('LINEBELOW', (0, 0), (-1, 0), 3, GOLD),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return t


# ── Document content ───────────────────────────────────────────────────────────
def build_content(styles):
    story = []

    # ─────────────────────────────────────────────────────────────────────────
    # COVER (rendered on its own PageTemplate, no header/footer)
    # ─────────────────────────────────────────────────────────────────────────
    story.append(NextPageTemplate('cover'))
    story.append(PageBreak())

    story.append(Spacer(1, 60 * mm))
    story.append(Paragraph('Ethiopian Daily', styles['CoverTitle']))
    story.append(Spacer(1, 4))
    story.append(Paragraph('Developer Documentation', styles['CoverSub']))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width=80 * mm, thickness=2, color=GOLD,
                             spaceAfter=10, spaceBefore=2))
    story.append(Paragraph('Newsroom CMS · Public Site · Telegram Integration · Analytics',
                            styles['CoverMeta']))
    story.append(Spacer(1, 6))
    story.append(Paragraph('Version 1.0 · April 2026', styles['CoverMeta']))

    # ─────────────────────────────────────────────────────────────────────────
    # TABLE OF CONTENTS
    # ─────────────────────────────────────────────────────────────────────────
    story.append(NextPageTemplate('normal'))
    story.append(PageBreak())

    story.append(h1('Table of Contents', styles))
    toc_items = [
        ('1', 'Project Overview'),
        ('2', 'Technology Stack'),
        ('3', 'Project Structure'),
        ('4', 'App Architecture'),
        ('5', 'Data Models'),
        ('  5.1', 'Article & Category'),
        ('  5.2', 'ReviewNote'),
        ('  5.3', 'Reaction'),
        ('  5.4', 'TelegramChannel & TelegramImport'),
        ('  5.5', 'Advertisement'),
        ('  5.6', 'PageView (Analytics)'),
        ('  5.7', 'User & PasswordSetupToken'),
        ('6', 'URL Reference'),
        ('7', 'Views Reference'),
        ('  7.1', 'Public Views'),
        ('  7.2', 'Editorial Views'),
        ('  7.3', 'Review Views'),
        ('  7.4', 'Telegram Views'),
        ('  7.5', 'Ads Views'),
        ('  7.6', 'Stats View'),
        ('8', 'Permission System'),
        ('9', 'Forms'),
        ('10', 'Template System'),
        ('11', 'Context Processors'),
        ('12', 'Middleware'),
        ('13', 'Telegram Integration'),
        ('14', 'Background Scheduler'),
        ('15', 'Advertisement System'),
        ('16', 'Analytics & Statistics'),
        ('17', 'Admin Interface'),
        ('18', 'Development Workflow'),
        ('19', 'Environment & Settings'),
    ]
    toc_data = [[
        Paragraph(f'<b>{num}</b>', styles['TableCell']),
        Paragraph(title, styles['TableCell']),
    ] for num, title in toc_items]
    toc_table = Table(toc_data, colWidths=[22 * mm, 145 * mm])
    toc_table.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [WHITE, LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.3, HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(toc_table)

    # ─────────────────────────────────────────────────────────────────────────
    # 1. PROJECT OVERVIEW
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_badge('1', 'Project Overview', styles))
    story.append(sp(10))

    story.append(body(
        '<b>Ethiopian Daily</b> is a full-stack Django news platform designed for Ethiopian journalism. '
        'It combines a public-facing news site with a complete Newsroom CMS — allowing writers, '
        'reviewers, and administrators to collaborate on content, import news from Telegram channels, '
        'manage advertisements, and monitor site usage through a built-in analytics dashboard.',
        styles))

    story.append(h2('What the platform does', styles))
    for item in [
        '<b>Public site</b> — Homepage with featured/trending/category sections, article detail pages, emoji reactions, and full-text search.',
        '<b>Newsroom CMS</b> — Role-based editorial dashboard where writers draft articles, submit them for review, and track status.',
        '<b>Review workflow</b> — Reviewers pick up submitted articles, move them to "In Review", then approve or reject with written feedback.',
        '<b>Telegram integration</b> — Admins register public Telegram channels; the platform auto-scrapes messages on a configurable interval and lets admins publish them as articles with one click.',
        '<b>Advertisement management</b> — Four placement slots (homepage banner, homepage sidebar, article top, article bottom). Supports Google AdSense HTML code <i>and</i> personal image ads (image URL + click destination).',
        '<b>Analytics dashboard</b> — Tracks page views via middleware, shows daily traffic charts, top articles, writer activity, and article status breakdowns.',
        '<b>User management</b> — Admins create accounts with roles (Writer, Reviewer, Admin). New users receive a password-setup email link.',
    ]:
        story.append(bullet(item, styles))

    story.append(h2('User Roles', styles))
    role_data = [
        ('Writer', 'Create, edit, and submit articles for review. Can only access their own articles.'),
        ('Reviewer', 'Access the review queue, move articles through the workflow, approve or reject with notes.'),
        ('Admin', 'Full access to everything: all articles, user management, Telegram channels, advertisements, and analytics. Can also approve Telegram imports directly.'),
    ]
    story.append(field_table(role_data, styles, col_widths=[35 * mm, 130 * mm]))

    # ─────────────────────────────────────────────────────────────────────────
    # 2. TECHNOLOGY STACK
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_badge('2', 'Technology Stack', styles))
    story.append(sp(10))

    stack_data = [
        ('Django 5.2', 'Web framework — models, views, templates, ORM, admin.'),
        ('Python 3.10+', 'Runtime language.'),
        ('SQLite 3', 'Default development database (single file db.sqlite3). Swap for PostgreSQL in production.'),
        ('Tailwind CSS (CDN)', 'Utility-first CSS loaded from cdn.tailwindcss.com. Config injected via inline &lt;script&gt; per template.'),
        ('APScheduler', 'Background scheduler that auto-fetches Telegram channels every minute.'),
        ('BeautifulSoup4 + requests', 'HTML scraping of Telegram public web preview pages.'),
        ('reportlab', 'PDF generation (this document).'),
        ('whitenoise', 'Static file serving in production.'),
        ('Google Fonts', 'Playfair Display, Lora, Plus Jakarta Sans, Noto Ethiopic — loaded via CDN link.'),
    ]
    story.append(field_table(stack_data, styles, col_widths=[55 * mm, 110 * mm]))

    story.append(sp(8))
    story.append(note(
        'No JavaScript framework is used. All interactivity (reactions, sidebar, data-saver toggle) '
        'is vanilla JS embedded directly in the templates.', styles))

    # ─────────────────────────────────────────────────────────────────────────
    # 3. PROJECT STRUCTURE
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_badge('3', 'Project Structure', styles))
    story.append(sp(10))

    story.append(body('The repository root contains two Django apps (<b>core</b>, <b>users</b>) '
                      'plus the project configuration package:', styles))

    story.append(code_block(
        'ethiopicdaily/           ← repository root\n'
        '├── ethiopicdaily/       ← Django project package\n'
        '│   ├── settings.py      ← all configuration\n'
        '│   ├── urls.py          ← root URL dispatcher\n'
        '│   ├── wsgi.py\n'
        '│   └── asgi.py\n'
        '├── core/                ← main application\n'
        '│   ├── models/\n'
        '│   │   ├── article.py   (Article, Category, ReviewNote)\n'
        '│   │   ├── reaction.py  (Reaction)\n'
        '│   │   ├── telegram.py  (TelegramChannel, TelegramImport)\n'
        '│   │   ├── advertisement.py (Advertisement)\n'
        '│   │   └── analytics.py (PageView)\n'
        '│   ├── views/\n'
        '│   │   ├── public.py    (homepage, article_detail, search, reactions)\n'
        '│   │   ├── editorial.py (writer CRUD)\n'
        '│   │   ├── review.py    (reviewer workflow)\n'
        '│   │   ├── telegram.py  (import management)\n'
        '│   │   ├── ads.py       (advertisement CRUD)\n'
        '│   │   └── stats.py     (analytics dashboard)\n'
        '│   ├── templates/core/  ← all HTML templates\n'
        '│   ├── forms.py\n'
        '│   ├── admin.py\n'
        '│   ├── decorators.py    ← permission decorators\n'
        '│   ├── context_processors.py\n'
        '│   ├── middleware.py    ← PageViewMiddleware\n'
        '│   ├── services.py      ← Telegram scraper\n'
        '│   ├── scheduler.py     ← APScheduler setup\n'
        '│   ├── apps.py          ← CoreConfig (starts scheduler)\n'
        '│   └── urls.py\n'
        '├── users/               ← auth & user management app\n'
        '│   ├── models.py        (User, PasswordSetupToken)\n'
        '│   ├── views.py\n'
        '│   ├── forms.py\n'
        '│   ├── services.py      ← password setup email\n'
        '│   ├── templates/users/\n'
        '│   └── urls.py\n'
        '├── manage.py\n'
        '└── db.sqlite3', styles))

    # ─────────────────────────────────────────────────────────────────────────
    # 4. APP ARCHITECTURE
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_badge('4', 'App Architecture', styles))
    story.append(sp(10))

    story.append(body(
        'The project uses two Django apps. The <b>core</b> app is a monolith containing '
        'all content-related logic. The <b>users</b> app handles authentication and user '
        'management. Both are registered in INSTALLED_APPS and share the same SQLite database.', styles))

    story.append(h2('Request Lifecycle', styles))
    story.append(body(
        'Every HTTP request passes through Django\'s middleware stack before reaching a view:', styles))
    for step in [
        '<b>SecurityMiddleware</b> — HTTPS redirect, HSTS headers.',
        '<b>WhiteNoiseMiddleware</b> — serves compressed static files in production.',
        '<b>SessionMiddleware</b> — loads the session for each request.',
        '<b>PageViewMiddleware</b> (custom) — logs GET 200 responses as PageView records; skips admin, static, AJAX, and known bots.',
        '<b>CommonMiddleware</b> — URL normalisation.',
        '<b>CsrfViewMiddleware</b> — validates CSRF tokens on POST requests.',
        '<b>AuthenticationMiddleware</b> — attaches request.user.',
        '<b>MessageMiddleware</b> — flash messages (Django messages framework).',
        '<b>XFrameOptionsMiddleware</b> — prevents clickjacking.',
    ]:
        story.append(bullet(step, styles))

    story.append(h2('URL Routing', styles))
    story.append(body(
        'The root URLconf (<b>ethiopicdaily/urls.py</b>) mounts two app URL files:', styles))
    story.append(code_block(
        'urlpatterns = [\n'
        '    path("admin/", admin.site.urls),\n'
        '    path("",       include("core.urls")),   # namespace: core\n'
        '    path("users/", include("users.urls")),  # namespace: users\n'
        ']', styles))

    story.append(h2('Context Processors', styles))
    story.append(body('Three custom context processors run on every template render:', styles))
    ctx_data = [
        ('telegram_channels', 'Injects active TelegramChannel objects into every template. Used by the CMS sidebar to list channels.'),
        ('global_context', 'Injects categories (for public header nav) and the current breaking article (for the ticker banner).'),
        ('active_ads', 'Injects active advertisements keyed by placement slug. Usage: {{ ads.homepage_banner.rendered_html|safe }}'),
    ]
    story.append(field_table(ctx_data, styles, col_widths=[55 * mm, 110 * mm]))

    # ─────────────────────────────────────────────────────────────────────────
    # 5. DATA MODELS
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_badge('5', 'Data Models', styles))
    story.append(sp(10))

    story.append(body(
        'All models live in <b>core/models/</b> (a Python package) and are re-exported '
        'from <b>core/models/__init__.py</b>. The User model lives in <b>users/models.py</b>.', styles))

    # 5.1 Article
    story.append(h2('5.1  Article & Category', styles))
    story.append(body('<b>File:</b> core/models/article.py', styles))

    story.append(h3('Category', styles))
    story.append(field_table([
        ('name',  'CharField(100) — unique category name e.g. "Politics"'),
        ('slug',  'SlugField — auto-generated from name, used in URLs'),
        ('color', 'CharField(30) — Tailwind color class for the badge (e.g. "red", "blue")'),
    ], styles))

    story.append(h3('Article', styles))
    story.append(field_table([
        ('title',        'CharField(255)'),
        ('slug',         'SlugField(255) — unique, auto-generated'),
        ('summary',      'TextField(500) — shown as standfirst / excerpt'),
        ('content',      'TextField — full article body'),
        ('image_url',    'URLField — hero image'),
        ('video_url',    'URLField — YouTube, Vimeo, or .mp4 link; embed parsed in template'),
        ('category',     'FK → Category (nullable, SET_NULL)'),
        ('author',       'FK → User (nullable, SET_NULL, related_name="articles")'),
        ('reviewed_by',  'FK → User (nullable, related_name="reviewed_articles")'),
        ('status',       'CharField — choices: draft · submitted · in_review · published · rejected'),
        ('is_featured',  'BooleanField — pinned as the hero article on the homepage'),
        ('is_breaking',  'BooleanField — shown in the live ticker banner'),
        ('views_count',  'PositiveIntegerField — incremented once per visitor (cookie-gated)'),
        ('published_at', 'DateTimeField(null=True) — set when approved'),
        ('submitted_at', 'DateTimeField(null=True) — set when submitted for review'),
        ('reviewed_at',  'DateTimeField(null=True) — set when review action taken'),
        ('created_at',   'DateTimeField(auto_now_add=True)'),
        ('updated_at',   'DateTimeField(auto_now=True)'),
    ], styles))

    story.append(h3('Article — Status Transitions', styles))
    story.append(code_block(
        'DRAFT  ──[submit]──▶  SUBMITTED  ──[reviewer picks up]──▶  IN_REVIEW\n'
        '                                                            │        │\n'
        '                          DRAFT  ◀──[withdraw]──           │        │\n'
        '                                                     [approve]  [reject]\n'
        '                                                         │          │\n'
        '                                                     PUBLISHED   REJECTED', styles))

    story.append(h3('Article — Key Methods', styles))
    story.append(field_table([
        ('can_edit(user)',     'True if article is DRAFT or REJECTED and user is the author or admin.'),
        ('can_submit(user)',   'True if DRAFT and user is author or admin.'),
        ('can_withdraw(user)', 'True if SUBMITTED and user is author or admin.'),
        ('reading_time()',     'Estimated minutes to read (word count ÷ 200, min 1).'),
        ('embed_video_url',    'Property — converts YouTube/Vimeo share URL to embed URL for iframe.'),
    ], styles))

    story.append(h3('ReviewNote', styles))
    story.append(body('Append-only audit log for every action taken on an article.', styles))
    story.append(field_table([
        ('article',    'FK → Article (related_name="review_notes")'),
        ('actor',      'FK → User (the person who took the action)'),
        ('action',     'choices: submitted · withdrawn · in_review · approved · rejected · comment'),
        ('note',       'TextField — free-text feedback (required when rejecting)'),
        ('created_at', 'DateTimeField(auto_now_add=True)'),
    ], styles))

    # 5.2 Reaction
    story.append(h2('5.2  Reaction', styles))
    story.append(body('<b>File:</b> core/models/reaction.py', styles))
    story.append(field_table([
        ('article',       'FK → Article (related_name="reactions")'),
        ('user',          'FK → User'),
        ('reaction_type', 'choices: like · love · wow · sad · angry'),
        ('created_at',    'DateTimeField(auto_now_add=True)'),
        ('Meta',          'unique_together: (article, user) — one reaction per user per article. Toggling the same type removes it; changing type updates it.'),
    ], styles))

    # 5.3 Telegram
    story.append(h2('5.3  TelegramChannel & TelegramImport', styles))
    story.append(body('<b>File:</b> core/models/telegram.py', styles))

    story.append(h3('TelegramChannel', styles))
    story.append(field_table([
        ('slug',           'SlugField — Telegram @username (unique)'),
        ('display_name',   'CharField(100) — human-readable name'),
        ('is_active',      'BooleanField — only active channels are fetched'),
        ('fetch_interval', 'PositiveIntegerField — minutes between auto-fetches (min 1)'),
        ('last_fetched_at','DateTimeField(null=True) — last successful fetch'),
        ('created_at',     'DateTimeField(auto_now_add=True)'),
        ('is_due()',        'Method — True if now - last_fetched_at ≥ fetch_interval minutes.'),
    ], styles))

    story.append(h3('TelegramImport', styles))
    story.append(field_table([
        ('message_id',  'CharField — unique ID from Telegram (format: "channel/1234")'),
        ('channel',     'CharField — slug of the source channel'),
        ('source_url',  'URLField — link to original Telegram post'),
        ('raw_text',    'TextField — cleaned message text (emojis stripped)'),
        ('image_urls',  'JSONField — list of image URLs found in the message'),
        ('date',        'DateTimeField — original post date from Telegram'),
        ('fetched_at',  'DateTimeField(auto_now_add=True)'),
        ('status',      'choices: pending · approved · rejected'),
        ('article',     'OneToOneField → Article (null, set when approved)'),
        ('suggested_title/summary', 'Properties — first line / next 2 lines of raw_text.'),
    ], styles))

    # 5.4 Advertisement
    story.append(h2('5.4  Advertisement', styles))
    story.append(body('<b>File:</b> core/models/advertisement.py', styles))
    story.append(field_table([
        ('name',         'CharField(100) — internal label, not shown to readers'),
        ('client_name',  'CharField(150, blank) — advertiser name for personal connection ads'),
        ('placement',    'choices: homepage_banner · homepage_sidebar · article_top · article_bottom'),
        ('image_url',    'URLField(blank) — for image-based personal ads'),
        ('link_url',     'URLField(blank) — click destination for image ads'),
        ('ad_code',      'TextField(blank) — raw HTML for Google AdSense or custom code'),
        ('is_active',    'BooleanField(default=True)'),
        ('rendered_html','Property — returns ad_code if set; otherwise builds &lt;a&gt;&lt;img&gt;&lt;/a&gt; from image_url + link_url.'),
    ], styles))

    story.append(sp(6))
    story.append(note(
        'Only one ad per placement slot is served (the most recently updated active one). '
        'The context processor picks the first match.', styles))

    # 5.5 PageView
    story.append(h2('5.5  PageView (Analytics)', styles))
    story.append(body('<b>File:</b> core/models/analytics.py', styles))
    story.append(field_table([
        ('path',        'CharField(500) — request path e.g. "/article/my-story/"'),
        ('user',        'FK → User (null for anonymous visitors)'),
        ('session_key', 'CharField(100) — Django session key; used to count unique visitors'),
        ('date',        'DateField(auto_now_add=True) — for daily aggregation'),
        ('created_at',  'DateTimeField(auto_now_add=True) — exact timestamp'),
    ], styles))

    # 5.6 User
    story.append(h2('5.6  User & PasswordSetupToken', styles))
    story.append(body('<b>File:</b> users/models.py  —  AUTH_USER_MODEL = "users.User"', styles))

    story.append(h3('User  (extends AbstractUser)', styles))
    story.append(field_table([
        ('email',                'EmailField — unique, used as login identifier'),
        ('username',             'Derived from email automatically (before @)'),
        ('role',                 'choices: writer · reviewer · admin'),
        ('must_change_password', 'BooleanField(default=True) — new users must set password on first login'),
        ('is_writer()',          'Method — role == WRITER'),
        ('is_reviewer()',        'Method — role == REVIEWER'),
        ('is_admin()',           'Method — role == ADMIN'),
    ], styles))

    story.append(h3('PasswordSetupToken', styles))
    story.append(field_table([
        ('user',       'OneToOneField → User'),
        ('token',      'CharField — unique UUID used in the setup link'),
        ('created_at', 'DateTimeField(auto_now_add=True)'),
        ('is_used',    'BooleanField(default=False)'),
        ('is_expired()','Method — True if created_at > 24 hours ago.'),
    ], styles))

    # ─────────────────────────────────────────────────────────────────────────
    # 6. URL REFERENCE
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_badge('6', 'URL Reference', styles))
    story.append(sp(10))

    story.append(h2('Public URLs  (no login required)', styles))
    story.append(url_table([
        ('GET', '/', 'homepage — featured, trending, latest, category sections'),
        ('GET', '/search/', 'Full-text search across published articles'),
        ('GET', '/article/&lt;slug&gt;/', 'Article detail page; increments views_count once per visitor'),
        ('POST', '/article/&lt;slug&gt;/react/', 'Toggle emoji reaction (JSON response)'),
    ], styles))

    story.append(h2('Editorial URLs  (writer or admin)', styles))
    story.append(url_table([
        ('GET', '/editorial/', 'Dashboard — article list with search/filter'),
        ('GET/POST', '/editorial/new/', 'Create a new article draft'),
        ('GET/POST', '/editorial/&lt;slug&gt;/edit/', 'Edit an article'),
        ('GET', '/editorial/&lt;slug&gt;/preview/', 'Preview an article before publishing'),
        ('POST', '/editorial/&lt;slug&gt;/submit/', 'Submit article for review'),
        ('POST', '/editorial/&lt;slug&gt;/withdraw/', 'Pull article back to draft'),
        ('POST', '/editorial/&lt;slug&gt;/delete/', 'Delete draft article'),
        ('POST', '/editorial/wipe-all/', 'Admin only — delete all articles'),
    ], styles))

    story.append(h2('Review URLs  (reviewer or admin)', styles))
    story.append(url_table([
        ('GET', '/review/', 'Review queue — articles awaiting review'),
        ('GET', '/review/&lt;slug&gt;/', 'View article; auto-transitions to IN_REVIEW'),
        ('POST', '/review/&lt;slug&gt;/action/', 'Submit review decision: approve · reject · comment'),
    ], styles))

    story.append(h2('Telegram URLs  (admin only)', styles))
    story.append(url_table([
        ('GET', '/telegram/', 'List of imports with status/channel filters'),
        ('POST', '/telegram/fetch/', 'Manually fetch latest messages from one or all channels'),
        ('GET/POST', '/telegram/&lt;pk&gt;/approve/', 'Approve import — form to create article'),
        ('POST', '/telegram/&lt;pk&gt;/reject/', 'Reject import'),
        ('GET', '/channels/', 'List all registered channels'),
        ('GET/POST', '/channels/add/', 'Add a new channel'),
        ('POST', '/channels/&lt;pk&gt;/toggle/', 'Activate or pause a channel'),
        ('POST', '/channels/&lt;pk&gt;/delete/', 'Delete a channel'),
    ], styles))

    story.append(h2('Ad Management URLs  (admin only)', styles))
    story.append(url_table([
        ('GET', '/ads/', 'Ad list grouped by placement slot'),
        ('GET/POST', '/ads/new/', 'Create a new ad'),
        ('GET/POST', '/ads/&lt;pk&gt;/edit/', 'Edit an ad'),
        ('POST', '/ads/&lt;pk&gt;/toggle/', 'Activate or pause an ad'),
        ('POST', '/ads/&lt;pk&gt;/delete/', 'Delete an ad'),
    ], styles))

    story.append(h2('Analytics URL  (admin only)', styles))
    story.append(url_table([
        ('GET', '/stats/', 'Statistics dashboard'),
    ], styles))

    story.append(h2('User Management URLs  (/users/ prefix)', styles))
    story.append(url_table([
        ('GET/POST', '/users/login/', 'Login page'),
        ('POST', '/users/logout/', 'Logout'),
        ('GET', '/users/', 'User list (admin only)'),
        ('GET/POST', '/users/new/', 'Create a new user (admin only)'),
        ('GET', '/users/&lt;pk&gt;/', 'User detail'),
        ('POST', '/users/&lt;pk&gt;/edit/', 'Update user role'),
        ('POST', '/users/&lt;pk&gt;/delete/', 'Delete user'),
        ('GET/POST', '/users/setup-password/&lt;token&gt;/', 'Password setup for new users (public link)'),
    ], styles))

    # ─────────────────────────────────────────────────────────────────────────
    # 7. VIEWS REFERENCE
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_badge('7', 'Views Reference', styles))
    story.append(sp(10))

    story.append(h2('7.1  Public Views  (core/views/public.py)', styles))
    story.append(field_table([
        ('homepage(request)',
         'Builds the homepage context: featured article, 3 sub-hero articles, 8 latest, '
         '6 trending (by views_count), 5 most-read, and up to 4 category sections (4 articles each).'),
        ('search(request)',
         'Accepts GET param q. Filters published articles by title/summary/content (case-insensitive). '
         'Returns core/search_results.html.'),
        ('article_detail(request, slug)',
         'Fetches article by slug. Non-published articles visible only to author/reviewer/admin. '
         'Increments views_count once per visitor using cookie va_{pk} (30-day expiry). '
         'Loads reaction counts and the current user\'s reaction. '
         'Returns core/article_detail.html.'),
        ('react_to_article(request, slug)',
         'POST only. Requires login. Toggles the reaction (same type = remove; different type = update). '
         'Returns JSON: { counts: {...}, user_reaction: "like"|null }.'),
    ], styles))

    story.append(h2('7.2  Editorial Views  (core/views/editorial.py)', styles))
    story.append(field_table([
        ('editorial_dashboard(request)',
         'Lists articles (all for admin, own for writer). Supports advanced search via ArticleSearchForm '
         '(q, status, category, author_email, date range, featured/breaking toggles). '
         'Shows status count cards. Admins see extra stats (total users, recent published, pending Telegram imports).'),
        ('article_create(request)',
         'GET: blank ArticleForm. POST: creates Article with status=DRAFT, '
         'creates ReviewNote (action=COMMENT "Article created as draft"), '
         'redirects to edit view.'),
        ('article_edit(request, slug)',
         'GET: pre-filled ArticleForm. POST: saves updates. '
         'If save_and_submit param present, also submits for review in the same request.'),
        ('article_submit/withdraw/delete/wipe_all',
         'POST-only actions that transition article status. All validate permissions before acting. '
         'wipe_all requires the text "I AGREE" in a confirmation field.'),
        ('article_preview(request, slug)',
         'Renders core/article_preview.html (standalone page mimicking the public article layout). '
         'Only accessible by article author or admin.'),
    ], styles))

    story.append(h2('7.3  Review Views  (core/views/review.py)', styles))
    story.append(field_table([
        ('review_queue(request)',
         'Lists SUBMITTED and IN_REVIEW articles ordered by submitted_at. '
         'Filterable by status. Shows pending/in-review counts.'),
        ('review_article(request, slug)',
         'Displays article content + sidebar with article info, review form, and history timeline. '
         'Auto-transitions SUBMITTED → IN_REVIEW on first view (creates ReviewNote).'),
        ('review_action(request, slug)',
         'POST only. Actions: approve (→ PUBLISHED, sets published_at), '
         'reject (→ REJECTED, note required), comment (adds ReviewNote without status change).'),
    ], styles))

    story.append(h2('7.4  Telegram Views  (core/views/telegram.py)', styles))
    story.append(field_table([
        ('fetch_telegram(request)',
         'POST only. Calls services.fetch_telegram_messages() for one channel or '
         'services.fetch_all_channels() for all. Saves new messages via TelegramImport.get_or_create(). '
         'Updates last_fetched_at.'),
        ('telegram_import_list(request)',
         'Lists imports with status filter (default: pending) and channel filter. '
         'Shows per-status counts. Paginated (25 per page).'),
        ('approve_import(request, pk)',
         'GET: form pre-filled with suggested_title/summary from raw_text. '
         'POST: creates Article (status=PUBLISHED), links to import, sets import.status=approved.'),
        ('reject_import(request, pk)',
         'POST: sets import.status=rejected.'),
        ('channel_list / channel_create / channel_toggle / channel_delete',
         'Standard CRUD for TelegramChannel. channel_create uses ChannelForm with '
         'duplicate-slug validation.'),
    ], styles))

    story.append(h2('7.5  Ads Views  (core/views/ads.py)', styles))
    story.append(field_table([
        ('ad_list(request)',
         'Groups all ads by placement. Counts total / active. '
         'Passes by_placement dict (each entry has label + list of ads).'),
        ('ad_create / ad_edit(request)',
         'Standard ModelForm create/edit using AdvertisementForm. '
         'On save, shows success flash message.'),
        ('ad_toggle(request, pk)',
         'Flips is_active. Updates only that field (update_fields).'),
        ('ad_delete(request, pk)',
         'Deletes the ad. Triggered via JS modal to avoid accidental deletion.'),
    ], styles))

    story.append(h2('7.6  Stats View  (core/views/stats.py)', styles))
    story.append(field_table([
        ('stats_dashboard(request)',
         'Computes: views today/yesterday/7-day/30-day, unique sessions today, '
         '14-day daily chart data, top 10 pages by views, top 10 articles by views_count, '
         'article status breakdown with percentages, writer activity (article count per user).'),
    ], styles))

    # ─────────────────────────────────────────────────────────────────────────
    # 8. PERMISSION SYSTEM
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_badge('8', 'Permission System', styles))
    story.append(sp(10))

    story.append(body(
        'Permissions are enforced using function-based decorators defined in '
        '<b>core/decorators.py</b>. Each decorator checks the user\'s role and '
        'redirects unauthenticated users to the login page (with a next= parameter).', styles))

    story.append(field_table([
        ('@writer_required', 'Allows writers and admins. Used on all editorial views.'),
        ('@reviewer_required', 'Allows reviewers and admins. Used on all review views.'),
        ('@cms_required', 'Allows any CMS user (writer, reviewer, or admin). Available for shared views.'),
        ('@admin_required', 'Admins only. Used on Telegram, ads, stats, and user management views.'),
    ], styles))

    story.append(sp(6))
    story.append(h3('How a decorator works', styles))
    story.append(code_block(
        'def writer_required(view_func):\n'
        '    @wraps(view_func)\n'
        '    def wrapper(request, *args, **kwargs):\n'
        '        if not request.user.is_authenticated:\n'
        '            return redirect(f"/users/login/?next={request.path}")\n'
        '        if not (request.user.is_writer() or request.user.is_admin()):\n'
        '            messages.error(request, "You need a writer account.")\n'
        '            return redirect("core:homepage")\n'
        '        return view_func(request, *args, **kwargs)\n'
        '    return wrapper', styles))

    story.append(sp(6))
    story.append(h3('Additional object-level checks', styles))
    story.append(body('Beyond decorator-level access, views enforce object-level rules:', styles))
    for item in [
        'Writers can only edit <i>their own</i> articles in DRAFT or REJECTED status.',
        'Writers can only delete <i>their own DRAFT</i> articles.',
        'Admins can edit and delete <i>any</i> article.',
        'The article preview page is restricted to the article\'s author and admins.',
        'Non-published articles are hidden from the public (404 for unauthorised users).',
    ]:
        story.append(bullet(item, styles))

    # ─────────────────────────────────────────────────────────────────────────
    # 9. FORMS
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_badge('9', 'Forms', styles))
    story.append(sp(10))

    story.append(body('All core forms live in <b>core/forms.py</b>. User forms are in <b>users/forms.py</b>.', styles))

    story.append(h2('ArticleForm  (ModelForm → Article)', styles))
    story.append(field_table([
        ('Fields', 'title, summary, content, image_url, video_url, category, is_featured, is_breaking'),
        ('__init__(user=...)', 'Removes is_featured and is_breaking from non-admin users.'),
        ('Validation', 'clean_title / clean_summary / clean_content — strip whitespace, require non-empty.'),
    ], styles))

    story.append(h2('ChannelForm  (ModelForm → TelegramChannel)', styles))
    story.append(field_table([
        ('Fields', 'slug, display_name, fetch_interval'),
        ('clean_slug', 'Strips, lowercases. Validates uniqueness (excluding self on edit).'),
        ('clean_fetch_interval', 'Enforces minimum of 1 minute.'),
    ], styles))

    story.append(h2('AdvertisementForm  (ModelForm → Advertisement)', styles))
    story.append(field_table([
        ('Fields', 'name, client_name, placement, image_url, link_url, ad_code, is_active'),
        ('clean()', 'Cross-field validation: at least one of image_url or ad_code must be provided.'),
        ('Widgets', 'All fields use Tailwind-styled widgets. ad_code uses an 8-row monospace textarea.'),
    ], styles))

    story.append(h2('ArticleSearchForm  (non-Model Form)', styles))
    story.append(body('Powers the editorial dashboard search bar. Fields:', styles))
    for f in ['q (text search)', 'status (choice)', 'category (ModelChoice)',
              'author_email (text, admin-only)', 'date_from / date_to (DateField)',
              'is_featured (choice: any/yes/no)', 'is_breaking (choice: any/yes/no)']:
        story.append(bullet(f, styles))

    # ─────────────────────────────────────────────────────────────────────────
    # 10. TEMPLATE SYSTEM
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_badge('10', 'Template System', styles))
    story.append(sp(10))

    story.append(body('All templates are in <b>core/templates/core/</b> and <b>users/templates/users/</b>. '
                      'No global templates/ directory is used.', styles))

    story.append(h2('Base Templates', styles))
    story.append(field_table([
        ('core/cms_base.html',
         'CMS layout: collapsible sidebar (navigation links depend on role), '
         'sticky top bar with page title/subtitle/actions blocks, flash messages, '
         'main content area. Tailwind config with brand colours defined here.'),
        ('core/public_base.html',
         'Public site layout: breaking news ticker, sticky header with logo/search/auth links, '
         'category nav bar, footer with social links/sections/legal. Data Saver toggle JS.'),
        ('users/base.html',
         'Standalone layout for auth pages: decorative gradient header, top nav bar with logo.'),
    ], styles))

    story.append(h2('Template Inheritance Tree', styles))
    story.append(code_block(
        'cms_base.html\n'
        '  ├── editorial_dashboard.html\n'
        '  ├── article_form.html\n'
        '  ├── review_queue.html\n'
        '  ├── review_article.html\n'
        '  ├── telegram_imports.html\n'
        '  ├── approve_import.html\n'
        '  ├── channel_list.html\n'
        '  ├── channel_form.html\n'
        '  ├── ad_list.html\n'
        '  ├── ad_form.html\n'
        '  └── stats_dashboard.html\n'
        '\n'
        'public_base.html\n'
        '  ├── home.html\n'
        '  ├── article_detail.html\n'
        '  └── search_results.html\n'
        '\n'
        'users/base.html\n'
        '  ├── login.html\n'
        '  ├── user_list.html\n'
        '  ├── user_detail.html\n'
        '  ├── create_user.html\n'
        '  └── setup_password.html\n'
        '\n'
        'Standalone (no base):\n'
        '  └── article_preview.html   (full HTML, mimics public article page)', styles))

    story.append(h2('Tailwind Configuration', styles))
    story.append(body(
        'Tailwind is loaded from CDN and configured inline in each base template\'s '
        '&lt;script&gt; block. The brand colour palette is:', styles))
    story.append(field_table([
        ('brand.DEFAULT', '#0f4c81  — navy blue (sidebar, headers, primary buttons)'),
        ('brand.dark',    '#0b3a63  — darker navy for gradients'),
        ('brand.light',   '#e8f4ff  — pale blue background tint'),
        ('brand.accent',  '#d8a038  — golden amber (Ethiopian cultural colour, badges, CTAs)'),
    ], styles))

    # ─────────────────────────────────────────────────────────────────────────
    # 11. CONTEXT PROCESSORS
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_badge('11', 'Context Processors', styles))
    story.append(sp(10))

    story.append(body('Defined in <b>core/context_processors.py</b>. All three run on every request.', styles))

    story.append(h2('telegram_channels', styles))
    story.append(body('Injects <b>telegram_channels</b> (QuerySet of active channels). '
                      'Used by cms_base.html to render the dynamic channel list in the sidebar under "Telegram".', styles))

    story.append(h2('global_context', styles))
    story.append(body('Injects <b>categories</b> (all Category objects) and <b>breaking</b> '
                      '(first published article with is_breaking=True, or None). '
                      'Categories power the public header nav. Breaking powers the ticker banner.', styles))

    story.append(h2('active_ads', styles))
    story.append(body('Injects <b>ads</b> — a dict keyed by placement slug containing the first '
                      'active Advertisement for each slot.', styles))
    story.append(code_block(
        '# In templates:\n'
        '{% if ads.homepage_banner %}\n'
        '  {{ ads.homepage_banner.rendered_html|safe }}\n'
        '{% endif %}', styles))
    story.append(body('The rendered_html property returns ad_code if set, otherwise builds '
                      '&lt;a href="link_url"&gt;&lt;img src="image_url"&gt;&lt;/a&gt; for image ads.', styles))

    # ─────────────────────────────────────────────────────────────────────────
    # 12. MIDDLEWARE
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_badge('12', 'Middleware', styles))
    story.append(sp(10))

    story.append(h2('PageViewMiddleware  (core/middleware.py)', styles))
    story.append(body('Automatically records a PageView row for every real page visit.', styles))

    story.append(h3('What it logs', styles))
    for item in [
        'GET requests that return HTTP 200.',
        'Records: path, user (if authenticated), session_key, date.',
    ]:
        story.append(bullet(item, styles))

    story.append(h3('What it skips', styles))
    for item in [
        'Non-GET methods (POST, PUT, DELETE, etc.).',
        'Non-200 responses (404s, redirects, etc.).',
        'Paths starting with /admin/, /static/, /media/, /favicon.',
        'AJAX requests (X-Requested-With: XMLHttpRequest header).',
        'Known bots (user-agent containing: bot, crawler, spider, slurp, wget, curl, python-requests).',
    ]:
        story.append(bullet(item, styles))

    story.append(h3('Position in middleware stack', styles))
    story.append(body('Placed after SessionMiddleware (so session_key is available) but '
                      'before CommonMiddleware. This ensures the session exists before the view logs it.', styles))

    # ─────────────────────────────────────────────────────────────────────────
    # 13. TELEGRAM INTEGRATION
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_badge('13', 'Telegram Integration', styles))
    story.append(sp(10))

    story.append(body('The Telegram integration scrapes public channel preview pages — '
                      '<b>no API key or bot token required</b>. It uses the public '
                      'web preview at https://t.me/s/{channel}.', styles))

    story.append(h2('How it works', styles))
    for step in [
        '<b>Admin registers a channel</b> by its @username (slug) and sets a fetch interval.',
        '<b>Fetch is triggered</b> either manually (via the Fetch button in the CMS) or '
        'automatically by the background scheduler.',
        '<b>services.fetch_telegram_messages()</b> sends a GET request to t.me/s/{channel}, '
        'parses the HTML with BeautifulSoup, extracts message text, dates, and image URLs.',
        '<b>Text is cleaned</b> by clean_text() — removes emojis, symbols, zero-width characters, '
        'and control characters while preserving all Unicode scripts (Amharic, Arabic, Latin, etc.).',
        '<b>New messages are saved</b> as TelegramImport records (status=pending). '
        'Duplicates are silently ignored via get_or_create on message_id.',
        '<b>Admin reviews imports</b> at /telegram/. Pending imports show the raw text, images, '
        'and suggested title/summary.',
        '<b>Approve</b>: Admin fills the article form (pre-populated from the import), '
        'clicks Approve — an Article is created (status=PUBLISHED), import is linked.',
        '<b>Reject</b>: Import is marked rejected (hidden from queue).',
    ]:
        story.append(bullet(step, styles))

    story.append(h2('services.py — Key Functions', styles))
    story.append(field_table([
        ('clean_text(text)',
         'Strips emoji/symbols from scraped text using Unicode category analysis. '
         'Preserves Amharic and all other alphabetic scripts.'),
        ('get_active_channels()',
         'Returns {slug: display_name} dict for all active TelegramChannel records.'),
        ('fetch_telegram_messages(channel, count=5)',
         'Scrapes t.me/s/{channel}, returns up to count message dicts. '
         'Raises ValueError for unknown channels, requests.RequestException on network errors.'),
        ('fetch_all_channels(count_per_channel=5)',
         'Calls fetch_telegram_messages() for every active channel. '
         'Returns {slug: [messages] | Exception} — errors per channel don\'t stop others.'),
    ], styles))

    # ─────────────────────────────────────────────────────────────────────────
    # 14. BACKGROUND SCHEDULER
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_badge('14', 'Background Scheduler', styles))
    story.append(sp(10))

    story.append(body('The scheduler lives in <b>core/scheduler.py</b> and is started in '
                      '<b>CoreConfig.ready()</b> (apps.py). It uses APScheduler\'s '
                      'BackgroundScheduler with a 1-minute IntervalTrigger.', styles))

    story.append(h2('The _auto_fetch() job', styles))
    for step in [
        'Runs every 1 minute.',
        'Loads all active TelegramChannel records.',
        'For each channel, calls ch.is_due() (compares last_fetched_at + fetch_interval to now).',
        'If due: calls fetch_telegram_messages(), saves new TelegramImport records.',
        'Updates ch.last_fetched_at after each successful fetch.',
        'Errors per channel are logged as warnings — other channels still run.',
    ]:
        story.append(bullet(step, styles))

    story.append(h2('Lifecycle', styles))
    story.append(code_block(
        '# apps.py\n'
        'class CoreConfig(AppConfig):\n'
        '    def ready(self):\n'
        '        from . import scheduler\n'
        '        scheduler.start()   # starts on Django launch\n'
        '\n'
        '# scheduler.py\n'
        'def start():    # idempotent — won\'t double-start\n'
        'def stop():     # called on shutdown (optional)', styles))

    story.append(sp(6))
    story.append(note(
        'APScheduler runs in a daemon thread inside the Django process. '
        'In production with multiple workers (gunicorn), each worker starts its own scheduler. '
        'To avoid duplicate fetches, consider moving to Celery Beat or a single-worker process.', styles))

    # ─────────────────────────────────────────────────────────────────────────
    # 15. ADVERTISEMENT SYSTEM
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_badge('15', 'Advertisement System', styles))
    story.append(sp(10))

    story.append(body('The ad system supports two types of ads and four placement slots. '
                      'It is fully managed through the CMS — no code changes are needed to add or swap ads.', styles))

    story.append(h2('Ad Types', styles))
    story.append(field_table([
        ('Google AdSense / Custom HTML',
         'Paste the full &lt;ins class="adsbygoogle"&gt; block (plus the &lt;script&gt; tag) '
         'into the "Ad Code" field. The HTML is injected verbatim via |safe in the template.'),
        ('Personal / Image Ad',
         'Provide an Image URL and a Destination Link. The system auto-generates: '
         '&lt;a href="link_url" target="_blank"&gt;&lt;img src="image_url"&gt;&lt;/a&gt;. '
         'Optionally add a Client Name for your own reference.'),
    ], styles))

    story.append(h2('Placement Slots', styles))
    story.append(field_table([
        ('homepage_banner',  'Top of the homepage, above the article grid. 728×90 (leaderboard). High visibility.'),
        ('homepage_sidebar', 'Right sidebar on the homepage between "Most Read" and "Topics". 300×250 (medium rectangle).'),
        ('article_top',      'Below the article\'s hero image, before the body text. Responsive width.'),
        ('article_bottom',   'After the article body, above "Related Stories". 728×90.'),
    ], styles))

    story.append(h2('How ads are served', styles))
    for step in [
        'The active_ads context processor runs on every request.',
        'It queries Advertisement.objects.filter(is_active=True).',
        'For each active ad, it adds it to ads_map[placement] — first active ad per slot wins.',
        'Templates check {% if ads.homepage_banner %} and render {{ ads.homepage_banner.rendered_html|safe }}.',
        'Only one ad is served per slot at a time. To swap ads, pause the old one and activate the new one.',
    ]:
        story.append(bullet(step, styles))

    # ─────────────────────────────────────────────────────────────────────────
    # 16. ANALYTICS & STATISTICS
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_badge('16', 'Analytics & Statistics', styles))
    story.append(sp(10))

    story.append(body('Usage tracking is built directly into the Django app — no third-party '
                      'analytics service is required. Data is stored in the PageView table.', styles))

    story.append(h2('What is tracked', styles))
    story.append(field_table([
        ('Page views', 'Every real GET 200 response: path, user, session key, date, timestamp.'),
        ('Article views', 'views_count on Article is incremented once per visitor per article (cookie-gated, 30-day cookie).'),
        ('Reactions', 'Per-user emoji reactions stored in the Reaction table.'),
    ], styles))

    story.append(h2('Statistics Dashboard (/stats/)', styles))
    story.append(field_table([
        ('Today\'s views', 'PageView count for today, with comparison to yesterday (up/down indicator).'),
        ('Unique visitors today', 'Distinct session_keys from today\'s PageView records.'),
        ('7-day / 30-day totals', 'Aggregate PageView counts for recent periods.'),
        ('14-day bar chart', 'Daily view counts rendered as CSS height-percentage bars, with hover tooltips.'),
        ('Article status breakdown', 'Count and percentage bar for each Article.Status value.'),
        ('Top 10 pages', 'Most-visited URL paths in the last 30 days (by PageView count).'),
        ('Top 10 articles', 'Published articles sorted by views_count (all-time).'),
        ('Writer activity', 'Users ordered by total article count.'),
    ], styles))

    # ─────────────────────────────────────────────────────────────────────────
    # 17. ADMIN INTERFACE
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_badge('17', 'Admin Interface', styles))
    story.append(sp(10))

    story.append(body('The Django admin is enhanced with a <b>Global Search</b> view '
                      '(admin/search/) and custom ModelAdmin configurations.', styles))

    story.append(h2('Global Search', styles))
    story.append(body('Accessible at /admin/search/. Searches across Articles, Categories, '
                      'Users, Telegram Channels, and Telegram Imports simultaneously. '
                      'Supports date range filters and type checkboxes.', styles))

    story.append(h2('Registered Model Admins', styles))
    story.append(field_table([
        ('CategoryAdmin',      'list_display: name, slug, color. prepopulated_fields: slug from name.'),
        ('ArticleAdmin',       'list_editable: status, is_featured, is_breaking. date_hierarchy on published_at. Full search across title/summary/content.'),
        ('ReviewNoteAdmin',    'Read-friendly list with article, actor, action, date.'),
        ('TelegramChannelAdmin','list_editable: is_active, fetch_interval. Shows last_fetched_at.'),
        ('TelegramImportAdmin','All fields read-only (prevents accidental editing of scraped data). Filterable by status and channel.'),
    ], styles))

    # ─────────────────────────────────────────────────────────────────────────
    # 18. DEVELOPMENT WORKFLOW
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_badge('18', 'Development Workflow', styles))
    story.append(sp(10))

    story.append(h2('Setup', styles))
    story.append(code_block(
        '# 1. Clone and enter the project\n'
        'git clone <repo-url>\n'
        'cd ethiopicdaily\n'
        '\n'
        '# 2. Create and activate a virtual environment\n'
        'python -m venv .venv\n'
        'source .venv/bin/activate      # macOS/Linux\n'
        '.venv\\Scripts\\activate         # Windows\n'
        '\n'
        '# 3. Install dependencies\n'
        'pip install django apscheduler beautifulsoup4 requests whitenoise reportlab\n'
        '\n'
        '# 4. Apply migrations\n'
        'python manage.py migrate\n'
        '\n'
        '# 5. (Optional) Seed sample articles\n'
        'python manage.py seed_articles\n'
        '\n'
        '# 6. Create a superuser\n'
        'python manage.py createsuperuser\n'
        '\n'
        '# 7. Run the dev server\n'
        'python manage.py runserver', styles))

    story.append(h2('Creating your first admin user via the CMS', styles))
    for step in [
        'Log in with the superuser you created.',
        'Go to /users/ → "New User" to create writer/reviewer accounts.',
        'New users receive a password setup email link (check the console in dev mode).',
        'They visit the link at /users/setup-password/&lt;token&gt;/ and set their password.',
    ]:
        story.append(bullet(step, styles))

    story.append(h2('Making model changes', styles))
    story.append(code_block(
        '# After editing any model in core/models/\n'
        'python manage.py makemigrations core\n'
        'python manage.py migrate\n'
        '\n'
        '# After editing users/models.py\n'
        'python manage.py makemigrations users\n'
        'python manage.py migrate', styles))

    story.append(h2('Seeding test data', styles))
    story.append(body('The management command <b>seed_articles</b> '
                      '(core/management/commands/seed_articles.py) '
                      'creates sample categories, articles in various states, '
                      'and assigns them to an existing user. Run it after migrations.', styles))

    # ─────────────────────────────────────────────────────────────────────────
    # 19. ENVIRONMENT & SETTINGS
    # ─────────────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_badge('19', 'Environment & Settings', styles))
    story.append(sp(10))

    story.append(body('Key settings in <b>ethiopicdaily/settings.py</b>:', styles))

    story.append(h2('Environment Variables', styles))
    story.append(field_table([
        ('DJANGO_SECRET_KEY', 'Override the default insecure key in production. Set as env var.'),
        ('DJANGO_DEBUG', 'Set to "False" in production. Defaults to "True".'),
    ], styles))

    story.append(h2('INSTALLED_APPS', styles))
    story.append(code_block(
        "INSTALLED_APPS = [\n"
        "    'django.contrib.admin',\n"
        "    'django.contrib.auth',\n"
        "    'django.contrib.contenttypes',\n"
        "    'django.contrib.sessions',\n"
        "    'django.contrib.messages',\n"
        "    'django.contrib.staticfiles',\n"
        "    'users',\n"
        "    'core.apps.CoreConfig',   # CoreConfig.ready() starts the scheduler\n"
        "]", styles))

    story.append(h2('Middleware Order', styles))
    story.append(code_block(
        "MIDDLEWARE = [\n"
        "    'django.middleware.security.SecurityMiddleware',\n"
        "    'whitenoise.middleware.WhiteNoiseMiddleware',\n"
        "    'django.contrib.sessions.middleware.SessionMiddleware',\n"
        "    'core.middleware.PageViewMiddleware',   # ← custom, after Session\n"
        "    'django.middleware.common.CommonMiddleware',\n"
        "    'django.middleware.csrf.CsrfViewMiddleware',\n"
        "    'django.contrib.auth.middleware.AuthenticationMiddleware',\n"
        "    'django.contrib.messages.middleware.MessageMiddleware',\n"
        "    'django.middleware.clickjacking.XFrameOptionsMiddleware',\n"
        "]", styles))

    story.append(h2('AUTH_USER_MODEL', styles))
    story.append(code_block("AUTH_USER_MODEL = 'users.User'", styles))
    story.append(body('This tells Django to use the custom User model in the users app '
                      'instead of the built-in auth.User. All FK references use '
                      "settings.AUTH_USER_MODEL or 'users.User'.", styles))

    story.append(h2('ALLOWED_HOSTS', styles))
    story.append(code_block(
        "ALLOWED_HOSTS = ['ethiopicdailydevelop.onrender.com', 'localhost', '127.0.0.1']", styles))

    story.append(sp(8))
    story.append(rule(GOLD, 2))
    story.append(sp(4))
    story.append(Paragraph(
        'End of Documentation  ·  Ethiopian Daily Newsroom Platform  ·  Version 1.0',
        ParagraphStyle('End', fontName='Helvetica-Oblique', fontSize=9,
                       textColor=MID_GRAY, alignment=TA_CENTER)))

    return story


# ── Build document ─────────────────────────────────────────────────────────────
def build_pdf(output_path='EthiopicDaily_Django_Documentation.pdf'):
    styles = build_styles()

    doc = BaseDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title='Ethiopian Daily — Developer Documentation',
        author='Ethiopian Daily Engineering',
        subject='Django CMS Reference',
    )

    cover_frame = Frame(0, 0, W, H, leftPadding=MARGIN, rightPadding=MARGIN,
                        topPadding=0, bottomPadding=0)
    normal_frame = Frame(MARGIN, 20 * mm, W - 2 * MARGIN, H - 36 * mm,
                         leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    doc.addPageTemplates([
        PageTemplate(id='cover', frames=[cover_frame], onPage=cover_page),
        PageTemplate(id='normal', frames=[normal_frame], onPage=normal_page),
    ])

    story = build_content(styles)
    doc.build(story)
    print(f'PDF generated: {output_path}')


if __name__ == '__main__':
    build_pdf()
