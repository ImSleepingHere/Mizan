"""Al Yamamah schedule exchange: read an Edugate "student schedule" PDF or a phone-app screenshot, and print a
timetable back in the Edugate layout. Reading uses the Windows OCR engine on this PC (Arabic + English); nothing
leaves the machine. Reading never writes anything: the user reviews and corrects the rows before import."""
import asyncio
import io
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from statistics import median

# Course-code prefixes as printed by Edugate (Arabic) and by the phone app (English), with known course names.
PREFIXES = {"عرب": "ARB", "مال": "FIN", "نما": "MIS", "تسق": "MKT", "ادا": "MGT"}
PREFIX_AR = {v: k for k, v in PREFIXES.items()}
DEPARTMENTS = {"ARB": "Arabic", "FIN": "Finance", "MIS": "Information Systems", "MKT": "Marketing", "MGT": "Management"}
CATALOG = {
    "ARB 202": ("Arabic Writing Skills", "مهارات الكتابة باللغة العربية"),
    "FIN 202": ("Introduction to Finance", "مقدمة في المالية"),
    "MIS 201": ("Introduction to Management Information Systems", "مقدمة في نظم المعلومات الإدارية"),
    "MKT 201": ("Introduction to Marketing", "مقدمة في التسويق"),
    "MGT 220": ("Organizational Behavior", "السلوك التنظيمي"),
    "MGT 210": ("Business Communication", "Business Communication"),
}
DAYS_AR = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس"]
DAYS_EN = ["sun", "mon", "tue", "wed", "thu"]
ACTIVITIES = {"نظري": "Lecture", "عملي": "Lab", "مختبر": "Lab", "تمارين": "Tutorial"}
TIME = re.compile(r"(\d{1,2})\s*[:.]\s*(\d{2})")


class ReadError(ValueError):
    """The document could not be read; the message is shown to the user (en, ar)."""
    def __init__(self, en, ar):
        super().__init__(en)
        self.en, self.ar = en, ar


@dataclass
class Line:
    text: str
    x: float
    y: float
    w: float
    h: float

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def cy(self):
        return self.y + self.h / 2


# ---------------------------------------------------------------- OCR (Windows.Media.Ocr, local)

def _ocr(image, lang):
    """Lines of text with pixel boxes. `image` is a PIL image."""
    try:
        from winrt.windows.media.ocr import OcrEngine
        from winrt.windows.globalization import Language
        from winrt.windows.graphics.imaging import SoftwareBitmap, BitmapPixelFormat, BitmapAlphaMode
        from winrt.windows.storage.streams import DataWriter
    except ImportError as e:
        raise ReadError("Text recognition is not available on this computer (Windows OCR).",
                        "التعرف على النص غير متاح على هذا الجهاز (Windows OCR).") from e
    engine = OcrEngine.try_create_from_language(Language(lang))
    if engine is None:
        raise ReadError(f"The Windows OCR language {lang} is not installed.", f"لغة التعرف {lang} غير مثبتة في Windows.")
    limit = OcrEngine.max_image_dimension
    scale = min(1.0, limit / max(image.size))
    if scale < 1:
        image = image.resize((int(image.width * scale), int(image.height * scale)))
    rgba = image.convert("RGBA")
    writer = DataWriter()
    writer.write_bytes(rgba.tobytes())
    bitmap = SoftwareBitmap(BitmapPixelFormat.RGBA8, rgba.width, rgba.height, BitmapAlphaMode.PREMULTIPLIED)
    bitmap.copy_from_buffer(writer.detach_buffer())

    async def run():
        return await engine.recognize_async(bitmap)
    result = asyncio.run(run())
    lines = []
    for line in result.lines:
        boxes = [w.bounding_rect for w in line.words]
        x0, y0 = min(b.x for b in boxes), min(b.y for b in boxes)
        x1, y1 = max(b.x + b.width for b in boxes), max(b.y + b.height for b in boxes)
        lines.append(Line(line.text, x0 / scale, y0 / scale, (x1 - x0) / scale, (y1 - y0) / scale))
    return lines


# ---------------------------------------------------------------- normalisation helpers

def _norm_ar(s):
    s = re.sub(r"[إأآا]", "ا", s)
    return s.replace("ى", "ي").replace("ة", "ه").replace("ـ", "")


# OCR mostly confuses Arabic letters that share a shape and differ only in dots (ت/ن/ب/ي, ف/ق, ...).
SKELETON = str.maketrans("تثنبيئفقجخذزشضظغة", "ببببببففححدرسصطعه")


def _skeleton(s):
    return _norm_ar(s).translate(SKELETON)


def _similar(a, b):
    return SequenceMatcher(None, _norm_ar(a), _norm_ar(b)).ratio()


def match_day(word):
    """Fuzzy Arabic/English weekday name -> 0..4 (Sunday-based), or None."""
    w = word.strip().lower()
    for i, d in enumerate(DAYS_EN):
        if w.startswith(d):
            return i
    if not re.search(r"[؀-ۿ]", w) or len(w) < 4:
        return None
    best = max(range(5), key=lambda i: _similar(w, DAYS_AR[i]))
    return best if _similar(w, DAYS_AR[best]) >= 0.6 else None


def clean_room(text):
    """'A-OI' -> 'A-01', '04-A' (read right-to-left) -> 'A-04', 'COED-II' -> 'COED-11'."""
    t = text.strip().upper().replace(" ", "")
    m = re.fullmatch(r"([0-9OIL]{1,3})-([A-Z]{1,5})", t)
    if m:
        t = f"{m.group(2)}-{m.group(1)}"
    m = re.fullmatch(r"([A-Z]{1,5})-?([0-9OIL|]{1,3})", t)
    if not m:
        return None
    digits = m.group(2).translate(str.maketrans("OIL|", "0111"))
    return f"{m.group(1)}-{digits.zfill(2)}"


def code_parts(text):
    """('MKT', '201') from 'MKT 201', '202 عرب' or 'نسق 201' (a misread of تسق); None if not a course code."""
    m = re.search(r"\b([A-Z]{2,4})\s?(\d{3})\b", text.upper())
    if m:
        return m.group(1), m.group(2)
    digits = re.search(r"\d{3}", text)
    letters = re.sub(r"[^؀-ۿ]", "", text)
    if not digits or not 2 <= len(letters) <= 4:
        return None
    exact = [k for k in PREFIXES if _skeleton(k) == _skeleton(letters)]
    best = exact[0] if len(exact) == 1 else max(PREFIXES, key=lambda k: _similar(letters, k))
    prefix = PREFIXES[best] if exact or _similar(letters, best) >= 0.6 else letters
    return prefix, digits.group(0)


def to_minutes(hour, minute, marker=None):
    """12-hour clock -> minutes after midnight. Without AM/PM, hours before 8 are taken as afternoon."""
    hour, minute = int(hour), int(minute)
    pm = marker in ("PM", "P", "م") or (marker is None and 1 <= hour < 8)
    if pm and hour < 12:
        hour += 12
    if marker in ("AM", "A", "ص") and hour == 12:
        hour = 0
    return hour * 60 + minute


def _row(code, start=None, end=None, days=(), room="", section="", activity="", credits=None, name="", warnings=()):
    english = CATALOG.get(code)
    prefix = code.split(" ")[0]
    return dict(code=code, code_ar=f"{PREFIX_AR[prefix]} {code.split(' ')[1]}" if prefix in PREFIX_AR else None,
                name=english[0] if english else name, name_ar=english[1] if english else name,
                section=section, activity=activity, credits=credits, days=sorted(set(days)), start=start, end=end,
                room=room or "", warnings=list(warnings))


WARN = {
    "start": ("Start time not readable — please enter it", "وقت البداية غير مقروء — يرجى إدخاله"),
    "end": ("End time not visible — please enter it", "وقت النهاية غير ظاهر — يرجى إدخاله"),
    "days": ("Days not readable — please choose them", "الأيام غير مقروءة — يرجى اختيارها"),
    "room": ("Room not readable", "القاعة غير مقروءة"),
    "name": ("Course name read by OCR — please check", "اسم المقرر مقروء آلياً — يرجى التحقق"),
    "inferred": ("Time estimated from the block's position — please check", "الوقت مقدّر من موضع المربع — يرجى التحقق"),
    "copied": ("Time copied from the same course on another day", "الوقت منقول من نفس المقرر في يوم آخر"),
}


def warning(key):
    en, ar = WARN[key]
    return dict(key=key, en=en, ar=ar)


# ---------------------------------------------------------------- Edugate PDF ("جدول الطالب")

def _render_pdf(raw):
    import pymupdf
    from PIL import Image
    try:
        doc = pymupdf.open(stream=raw, filetype="pdf")
    except Exception as e:
        raise ReadError("This file is not a readable PDF.", "هذا الملف ليس ملف PDF صالحاً.") from e
    pages = []
    for page in list(doc)[:3]:
        text = page.get_text().strip()
        pix = page.get_pixmap(matrix=pymupdf.Matrix(3, 3))
        pages.append((Image.frombytes("RGB", (pix.width, pix.height), pix.samples), text))
    return pages


def _upright(image):
    """Edugate prints the table sideways; keep the rotation where the most clock times are readable."""
    best, score = image, -1
    for angle in (0, 90, 270):
        candidate = image.rotate(angle, expand=True) if angle else image
        small = candidate.resize((candidate.width // 2, candidate.height // 2))
        found = sum(len(TIME.findall(l.text)) for l in _ocr(small, "en-US"))
        if found > score:
            best, score = candidate, found
    return best


def parse_edugate_pdf(raw):
    rows, meta = [], {"student_id": None, "term": None}
    for image, _ in _render_pdf(raw):
        image = _upright(image)
        arabic, latin = _ocr(image, "ar-SA"), _ocr(image, "en-US")
        page_rows, page_meta = _edugate_rows(arabic, latin)
        rows += page_rows
        meta.update({k: v for k, v in page_meta.items() if v})
    if not rows:
        raise ReadError("No schedule rows were found. Upload the Edugate “Student schedule” PDF or the app screenshot.",
                        "لم يُعثر على صفوف جدول. ارفع ملف «جدول الطالب» من البوابة أو لقطة شاشة التطبيق.")
    return dict(format="edugate_pdf", rows=rows, **meta)


def _edugate_rows(arabic, latin):
    anchors = sorted((l for l in arabic + latin if len(TIME.findall(l.text)) >= 2), key=lambda l: l.cy)
    merged = []
    for a in anchors:  # the Arabic and the English pass both see each time cell; keep one per row
        if not merged or abs(a.cy - merged[-1].cy) > a.h:
            merged.append(a)
        elif "ص" in a.text or "م" in a.text:
            merged[-1] = a
    if not merged:
        return [], {}
    gaps = [b.cy - a.cy for a, b in zip(merged, merged[1:])]
    half = (median(gaps) if gaps else merged[0].h * 4) / 2
    time_cx = median(a.cx for a in merged)
    singles = [l for l in arabic if re.fullmatch(r"\d", l.text.strip())]
    credits_cx = median(l.cx for l in singles) if singles else None
    rows = []
    for anchor in merged:
        def near(lines):
            return [l for l in lines if abs(l.cy - anchor.cy) < half]
        pairs = re.findall(r"([صم]|AM|PM|[ap])?\s*(\d{1,2})\s*[:.]\s*(\d{2})\s*([صم]|AM|PM)?", anchor.text)
        times = sorted(to_minutes(h, m, (pre or post or None) and (pre or post).replace("p", "PM").replace("a", "AM"))
                       for pre, h, m, post in pairs)
        row_ar, row_en = near(arabic), near(latin)
        room = next((r for r in (clean_room(l.text) for l in sorted(row_en + row_ar, key=lambda l: l.cx) if l.cx < time_cx) if r), "")
        day_lines = [l for l in row_ar if l.cx > anchor.x + anchor.w and (credits_cx is None or l.cx < credits_cx)]
        days = [d for l in day_lines for d in (match_day(w) for w in l.text.split()) if d is not None]
        numbers = sorted((l for l in row_ar if re.fullmatch(r"\d{1,4}", l.text.strip()) and l.cx > time_cx), key=lambda l: l.cx)
        credits = int(numbers[0].text) if numbers and len(numbers[0].text.strip()) == 1 else None
        section = numbers[1].text.strip() if len(numbers) > 1 else (numbers[0].text.strip() if numbers and credits is None else "")
        code_line = max((l for l in row_ar if code_parts(l.text) and not re.fullmatch(r"[\d\s]+", l.text)), key=lambda l: l.cx, default=None)
        if not code_line:
            continue
        prefix, digits = code_parts(code_line.text)
        activity = next((a for l in row_ar for a in ACTIVITIES if _similar(l.text.strip(), a) >= 0.75), "")
        lower = max(numbers[-1].cx if numbers else time_cx, time_cx)
        name_lines = sorted((l for l in row_ar + row_en if lower + 1 < l.cx < code_line.x and _similar(l.text.strip(), activity or "-") < 0.75
                             and not re.fullmatch(r"[\d\s]+", l.text)), key=lambda l: l.cy)
        seen, words = [], []
        for l in name_lines:  # the two OCR passes overlap; keep one reading per box, Arabic word order fixed
            if any(abs(l.cy - s.cy) < l.h / 2 and abs(l.cx - s.cx) < l.w / 2 for s in seen):
                continue
            seen.append(l)
            words.append(" ".join(reversed(l.text.split())) if re.search(r"[؀-ۿ]", l.text) else l.text)
        name = " ".join(words)
        if prefix not in PREFIX_AR:  # unknown prefix: a catalogue course with these digits and a matching name
            twin = max((c for c in CATALOG if c.endswith(digits)), key=lambda c: _similar(name, CATALOG[c][1]), default=None)
            if twin and _similar(name, CATALOG[twin][1]) >= 0.6:
                prefix = twin.split(" ")[0]
        warnings = []
        if len(times) < 2:
            warnings.append(warning("start" if not times else "end"))
        if not days:
            warnings.append(warning("days"))
        if not room:
            warnings.append(warning("room"))
        code = f"{prefix} {digits}"
        if code not in CATALOG:
            warnings.append(warning("name"))
        rows.append(_row(code, times[0] if times else None, times[-1] if len(times) > 1 else None, days, room, section,
                         activity, credits, name, warnings))
    every = " ".join(l.text for l in arabic + latin)
    student = re.search(r"\b(20\d{7})\b", every)
    term = re.search(r"(20\d{2})\s*/\s*(20\d{2})", every)
    return rows, dict(student_id=student.group(1) if student else None, term=f"{term.group(1)}/{term.group(2)}" if term else None)


# ---------------------------------------------------------------- phone app screenshot ("My Courses" week grid)

def parse_app_screenshot(raw):
    from PIL import Image, ImageOps, UnidentifiedImageError
    try:
        image = Image.open(io.BytesIO(raw))
        image.load()
    except (UnidentifiedImageError, OSError) as e:
        raise ReadError("This image could not be opened.", "تعذّر فتح هذه الصورة.") from e
    gray = ImageOps.autocontrast(ImageOps.invert(ImageOps.grayscale(image.convert("RGB"))))
    headers = {}
    for lang, factor in (("en-US", 2), ("ar-SA", 2)):
        if len(headers) >= 2:
            break
        for l in _ocr(gray.resize((gray.width * factor, gray.height * factor)), lang):
            d = match_day(l.text) if len(l.text.split()) == 1 else None
            if d is not None:
                headers.setdefault(d, (l.cx / factor, l.cy / factor))
    if len(headers) < 2:
        raise ReadError("The weekday header (Sun … Thu) was not found in the image.", "لم يُعثر على صف أيام الأسبوع في الصورة.")
    # Column centres follow a straight line across the week; fill in days whose header was unreadable.
    ks = sorted(headers)
    step = (headers[ks[-1]][0] - headers[ks[0]][0]) / (ks[-1] - ks[0])
    centres = [headers[ks[0]][0] + (d - ks[0]) * step for d in range(5)]
    top = int(max(y for _, y in headers.values()) + abs(step) * 0.15)
    blocks, scale = [], 2
    for day, cx in enumerate(centres):
        x0, x1 = int(max(0, cx - abs(step) / 2)), int(min(gray.width, cx + abs(step) / 2))
        crop = gray.crop((x0, top, x1, gray.height))
        crop = crop.resize((crop.width * scale, crop.height * scale))
        lines = sorted(_ocr(crop, "en-US"), key=lambda l: l.cy)
        blocks += _column_blocks(day, lines, crop.height)
    return dict(format="app_screenshot", rows=_screenshot_rows(blocks), student_id=None, term=None)


def _column_blocks(day, lines, height):
    tokens = []
    for l in lines:
        m = re.search(r"(\d{1,2})\s*:\s*(\d{2})\s*([AP])?", l.text.upper())
        if m:
            tokens.append(("time", l.cy, to_minutes(m.group(1), m.group(2), m.group(3) and m.group(3) + "M")))
            continue
        parts = code_parts(l.text)
        if parts and re.search("[A-Za-z]", l.text):
            tokens.append(("code", l.cy, f"{parts[0]} {parts[1]}"))
            continue
        room = clean_room(l.text)
        if room:
            tokens.append(("room", l.cy, room))
    codes = [t for t in tokens if t[0] == "code"]
    blocks = [dict(day=day, code=c[2], y=c[1], start=None, end=None, room="", height=height) for c in codes]
    for kind, y, value in tokens:
        if kind == "room":
            above = [b for b in blocks if b["y"] < y]
            if above and not above[-1]["room"]:
                above[-1]["room"] = value
        if kind != "time":
            continue
        prev = max((b for b in blocks if b["y"] < y), key=lambda b: b["y"], default=None)
        nxt = min((b for b in blocks if b["y"] > y), key=lambda b: b["y"], default=None)
        # A label belongs to the block whose code it sits closer to: below a code = its end, above = its start.
        if prev and (not nxt or y - prev["y"] <= nxt["y"] - y) and prev["end"] is None:
            prev["end"], prev["end_y"] = value, y
        elif nxt and nxt["start"] is None:
            nxt["start"], nxt["start_y"] = value, y
    return blocks


def _screenshot_rows(blocks):
    # Pixel geometry of this screenshot: minutes per pixel and the label offsets above/below a block's code line.
    starts = [(b["start_y"], b["start"]) for b in blocks if b.get("start_y") is not None]
    up = median(b["y"] - b["start_y"] for b in blocks if b.get("start_y") is not None) if starts else None
    slope = None
    if len({m for _, m in starts}) >= 2:
        (y0, m0), (y1, m1) = min(starts), max(starts)
        slope = (m1 - m0) / (y1 - y0) if y1 != y0 else None
    for b in blocks:
        b["warnings"] = []
    # 1) the same course meets at the same time on its other days
    for b in blocks:
        twin = next((o for o in blocks if o is not b and o["code"] == b["code"] and o["start"] is not None and o["end"] is not None), None)
        if twin and (b["start"] is None or b["end"] is None):
            b["start"] = b["start"] if b["start"] is not None else twin["start"]
            b["end"] = b["end"] if b["end"] is not None else twin["end"]
            b["warnings"].append(warning("copied"))
    # 2) a missing start = end minus the usual class length. A missing end is never guessed: a block can run
    #    past the bottom of the screenshot, so the user enters it.
    lengths = [b["end"] - b["start"] for b in blocks if b["start"] is not None and b["end"] is not None]
    usual = median(lengths) if lengths else None
    for b in blocks:
        if b["start"] is None and b["end"] is not None and usual:
            b["start"] = int(b["end"] - usual)
            b["warnings"].append(warning("inferred"))
        elif b["start"] is None and b["end"] is None and slope and up is not None:
            y0, m0 = min(starts)
            b["start"] = round((m0 + (b["y"] - up - y0) * slope) / 5) * 5
            b["warnings"].append(warning("inferred"))
    groups = {}
    for b in blocks:
        groups.setdefault((b["code"], b["start"], b["end"], b["room"]), []).append(b)
    rows = []
    for (code, start, end, room), members in groups.items():
        warns = {w["key"]: w for b in members for w in b["warnings"]}
        if start is None:
            warns["start"] = warning("start")
        if end is None:
            warns["end"] = warning("end")
        if not room:
            warns["room"] = warning("room")
        rows.append(_row(code, start, end, [b["day"] for b in members], room, warnings=list(warns.values())))
    return sorted(rows, key=lambda r: (r["days"][0] if r["days"] else 9, r["start"] or 0))


def read_schedule(raw, filename=""):
    if len(raw) > 15 * 1024 * 1024:
        raise ReadError("The file is larger than 15 MB.", "حجم الملف أكبر من ١٥ ميغابايت.")
    if raw[:5] == b"%PDF-":
        return parse_edugate_pdf(raw)
    return parse_app_screenshot(raw)


# ---------------------------------------------------------------- export in the Edugate "جدول الطالب" layout

def _clock(minutes):
    """Edugate time, e.g. '04:30 م' for 16:30 (ص = morning, م = afternoon)."""
    h, m = divmod(minutes, 60)
    return f"{(h - 1) % 12 + 1:02d}:{m:02d} {'ص' if h < 12 else 'م'}"


def schedule_rows(data, student_id, original=None):
    """Printable rows for one student: one row per section and meeting time, marked when it differs from `original`."""
    student = next((s for s in data.students if s.id == student_id), None)
    if student is None:
        raise KeyError(student_id)
    courses, sections = {c.id: c for c in data.courses}, {s.id: s for s in data.sections}
    before = {s.id: s for s in original.sections} if original else {}
    rows = []
    for sid in student.sections:
        section, course = sections[sid], courses[sections[sid].course_id]
        old = before.get(sid)
        changed = bool(original) and (old is None or old.room_id != section.room_id
                                      or sorted((m.day, m.start, m.end) for m in old.meetings) != sorted((m.day, m.start, m.end) for m in section.meetings))
        groups = {}
        for m in sorted(section.meetings, key=lambda m: m.day):
            groups.setdefault((m.start, m.end), []).append(m.day)
        for (start, end), days in groups.items():
            rows.append(dict(code=course.code_ar or course.code or course.id, name=course.name_ar, activity=section.activity or "—",
                             section=section.label or section.id, credits="—" if course.credits is None else str(course.credits),
                             days=[DAYS_AR[d] for d in days], time=f"{_clock(start)} - {_clock(end)}", room=section.room_id, changed=changed))
    return student, rows


def render_schedule_pdf(data, student_id, original=None, status_ar="", status_en="", source="", generated=None):
    import html
    import pymupdf
    from datetime import datetime
    student, rows = schedule_rows(data, student_id, original)
    generated = generated or datetime.now()
    doc = pymupdf.open()
    page = doc.new_page(width=792, height=612)  # US Letter, landscape, as Edugate prints it
    ink, grey, rule = (0, 0, 0), (0.6, 0.6, 0.6), (0.78, 0.78, 0.78)

    def text(rect, value, size=9.5, bold=False, align="center", color="#000", rtl=True):
        style = f"font-family:sans-serif;font-size:{size}px;color:{color};text-align:{align};font-weight:{'bold' if bold else 'normal'};line-height:1.25"
        page.insert_htmlbox(pymupdf.Rect(*rect), f'<div dir="{"rtl" if rtl else "ltr"}" style="{style}">{value}</div>')

    esc = html.escape
    date, clock = generated.strftime("%d/%m/%Y"), generated.strftime("%H:%M")
    # Header: English block left, Arabic block right, each underlined with a heavy rule.
    text((40, 34, 300, 110), "Al Yamamah University<br/>Mizan · Timetable assistant<br/>"
         f"Date : {date}<br/>Time : {clock}", 10.5, True, "left", rtl=False)
    text((492, 34, 752, 110), "جامعة اليمامة<br/>ميزان · مساعد الجداول<br/>"
         f"التاريخ : {date}<br/>الوقت : {clock}", 10.5, True, "right")
    page.draw_line((40, 116), (300, 116), color=ink, width=2.4)
    page.draw_line((492, 116), (752, 116), color=ink, width=2.4)
    text((320, 40, 472, 70), "ميزان &nbsp;|&nbsp; MIZAN", 13, True)
    text((300, 128, 492, 150), "جدول الطالب", 13, True)
    # Student details (right) and document status (left), label : value.
    info_right = [("اسم الطالب", student.name), ("رقم الطالب", student.id), ("فصل التسجيل", data.term or "—")]
    info_left = [("الحالة", status_ar), ("المصدر", source), ("التغييرات", str(sum(r["changed"] for r in rows)) if original else "—")]
    for i, ((la, va), (lb, vb)) in enumerate(zip(info_right, info_left)):
        y = 160 + i * 20
        text((620, y, 752, y + 18), f"{esc(la)}&nbsp;:", 10, True, "right")
        text((420, y, 618, y + 18), esc(va), 10, True, "right")
        text((290, y, 400, y + 18), f"{esc(lb)}&nbsp;:", 10, True, "right")
        text((40, y, 288, y + 18), esc(vb), 10, True, "right")
    text((200, 226, 592, 246), f"الفصل الدراسي {esc(data.term)}" if data.term else esc(data.name), 10.5, True)
    # Table, right-to-left: code, name, activity, section, credits, days, time, room.
    columns = [("رمز المقرر", 72, "code"), ("اسم المقرر", 170, "name"), ("النشاط", 56, "activity"), ("الشعبة", 56, "section"),
               ("س", 30, "credits"), ("اليوم", 76, "days"), ("الوقت", 140, "time"), ("القاعة", 112, "room")]
    top, head_h = 252, 24
    row_h = [max(30, 14 * len(r["days"]) + 8, 14 * (len(r["name"]) // 26 + 1) + 8) for r in rows]
    bottom = top + head_h + sum(row_h)
    x = 752
    page.draw_rect(pymupdf.Rect(40, top, 752, top + head_h), color=None, fill=(0.95, 0.95, 0.95))
    y = top + head_h
    for r, h in zip(rows, row_h):
        if r["changed"]:
            page.draw_rect(pymupdf.Rect(40, y, 752, y + h), color=None, fill=(1, 0.95, 0.8))
        y += h
    for label, width, key in columns:
        page.draw_rect(pymupdf.Rect(x - width, top, x, bottom), color=rule, width=0.7)
        text((x - width + 3, top + 6, x - 3, top + head_h), esc(label), 9.5, False, color="#999")
        y = top + head_h
        for r, h in zip(rows, row_h):
            value = "<br/>".join(esc(d) for d in r["days"]) if key == "days" else esc(r[key])
            if key in ("room", "section", "credits"):
                value = f"<bdi>{value}</bdi>"
            text((x - width + 3, y + 6, x - 3, y + h), value, 9.5)
            y += h
        x -= width
    y = top + head_h
    for h in row_h:
        page.draw_line((40, y), (752, y), color=rule, width=0.7)
        y += h
    page.draw_rect(pymupdf.Rect(40, top, 752, bottom), color=grey, width=1)
    # Footer: what this document is (and is not).
    note_y = max(bottom + 14, 520)
    if original and any(r["changed"] for r in rows):
        text((40, note_y, 752, note_y + 16), "الصفوف المظللة تغيّرت عن الجدول المستورد &nbsp;·&nbsp; Shaded rows differ from the imported schedule", 8.5, color="#7a5b00")
    text((40, note_y + 18, 752, note_y + 46), "أُنشئ بواسطة ميزان على هذا الجهاز. جدول للمراجعة يتطلب اعتماد الجهة المختصة، وليس وثيقة تسجيل رسمية من البوابة الإلكترونية."
         "<br/>Generated locally by Mizan for review. Changes require approval; this is not an official Edugate registration record.", 8, color="#666")
    text((700, 18, 752, 30), "1/1", 8, rtl=False, align="right", color="#666")
    doc.subset_fonts()
    out = doc.tobytes(garbage=4, deflate=True)
    doc.close()
    return out
