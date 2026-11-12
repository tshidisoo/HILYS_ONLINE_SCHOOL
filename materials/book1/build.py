"""Build HILYS Book 1 slide decks (.pptx) from lessons.py.

Usage:  python build.py            -> writes decks/ and LESSON-MAP.md / WORDS-TO-CHECK.md
"""
import os, re, sys
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lessons import LESSONS, GREETING  # noqa: E402

# ── Brand ────────────────────────────────────────────────────────────────
def rgb(h): return RGBColor.from_string(h)
NAVY, NAVY2, BG, WHITE, GREY, MUTED = "151A2E", "2A3150", "F6F7FB", "FFFFFF", "A8AECB", "5B6285"
YEL, ORA, COR, TEAL, BLUE = "F7BD45", "F5824F", "F06A70", "3CC4C0", "8FA2FF"
PALETTE = [YEL, TEAL, COR, BLUE, ORA]
VOWEL = {"a": "1FA39F", "e": "E5672F", "i": "5468E0", "o": "D9485A", "u": "B98612"}
HEAD, BODY = "Bricolage Grotesque", "Andika"
W, H = Inches(13.333), Inches(7.5)

# Minutes per slide type; the total is scaled so every lesson is exactly 40 minutes.
MINUTES = dict(title=0.5, greeting=2.5, goals=1, review=4, letter=2.5, tip=2, syllables=4, words=4, read=3,
               sentences=3, story=5, talk=5, game=4, qedisa=2, answers=1, culture=3, chant=2, writing=3,
               home=1.5, goodbye=1, vowels=6, rows=4, capitals=3, counting=4, plurals=4, past=4,
               letters=4, certificate=2)


class Deck:
    def __init__(self, L):
        self.L = L
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = W, H
        self.blank = self.prs.slide_layouts[6]
        self.slides = []  # (slide, kind, notes)

    # ── primitives ──
    def new(self, kind, notes, dark=False, tag=None, tag_color=TEAL):
        s = self.prs.slides.add_slide(self.blank)
        fill = s.background.fill
        fill.solid(); fill.fore_color.rgb = rgb(NAVY if dark else BG)
        self.band(s)
        self.footer(s, dark)
        if tag:
            self.pill(s, tag, Inches(0.6), Inches(0.62), tag_color)
        self.slides.append([s, kind, notes])
        return s

    def band(self, s):
        n, w = 20, W / 20
        for i in range(n):
            r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, int(i * w), 0, int(w) + 1, Inches(0.32))
            r.fill.solid(); r.fill.fore_color.rgb = rgb(PALETTE[i % 5])
            r.line.color.rgb = rgb(NAVY); r.line.width = Pt(1.5)
            d = s.shapes.add_shape(MSO_SHAPE.DIAMOND, int(i * w + w / 2 - Inches(0.11)), Inches(0.05), Inches(0.22), Inches(0.22))
            d.fill.solid(); d.fill.fore_color.rgb = rgb(WHITE); d.line.color.rgb = rgb(NAVY); d.line.width = Pt(1)

    def footer(self, s, dark):
        L = self.L
        c = GREY if dark else MUTED
        self.text(s, f"HILYS  ·  Book 1  ·  Isifundo {L['n']}", Inches(0.6), Inches(7.0), Inches(7), Inches(0.35), 12, c, font=BODY)
        self.text(s, f"Sekuthe Dlwe 1a  ·  pages {L['pages']}", Inches(6.7), Inches(7.0), Inches(6.05), Inches(0.35), 12, c,
                  align=PP_ALIGN.RIGHT, font=BODY)

    def text(self, s, t, x, y, w, h, size, color=NAVY, bold=False, align=PP_ALIGN.LEFT, font=BODY,
             anchor=MSO_ANCHOR.TOP, lines=None, spacing=None):
        tb = s.shapes.add_textbox(x, y, w, h)
        tf = tb.text_frame; tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(0.05); tf.margin_top = tf.margin_bottom = Inches(0.02)
        tf.vertical_anchor = anchor
        items = lines if lines is not None else [(t, size, color, bold)]
        for i, it in enumerate(items):
            tt, sz, col, b = (it + (None,) * 4)[:4] if isinstance(it, tuple) else (it, size, color, bold)
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            if spacing: p.space_after = Pt(spacing)
            r = p.add_run(); r.text = tt
            r.font.size = Pt(sz or size); r.font.bold = bold if b is None else b
            r.font.color.rgb = rgb(col or color); r.font.name = font
        return tb

    def box(self, s, x, y, w, h, fill=WHITE, line=None, radius=0.12, lw=2):
        b = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
        b.adjustments[0] = radius
        b.fill.solid(); b.fill.fore_color.rgb = rgb(fill)
        if line: b.line.color.rgb = rgb(line); b.line.width = Pt(lw)
        else: b.line.fill.background()
        b.shadow.inherit = False
        return b

    def pill(self, s, t, x, y, color):
        w = Inches(0.25 + 0.13 * len(t))
        b = self.box(s, x, y, w, Inches(0.42), fill=color, radius=0.5)
        tf = b.text_frame; tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = t; r.font.size = Pt(14); r.font.bold = True; r.font.name = HEAD; r.font.color.rgb = rgb(NAVY)

    def heading(self, s, nd, en, y=Inches(1.15), dark=False):
        self.text(s, None, Inches(0.6), y, Inches(12.1), Inches(1.2), 40, font=HEAD, lines=[
            (nd, 40, WHITE if dark else NAVY, True), (en, 20, GREY if dark else MUTED, False)])

    def card_text(self, shape, parts, anchor=MSO_ANCHOR.MIDDLE):
        tf = shape.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = Inches(0.08)
        for i, (t, sz, col, b, font) in enumerate(parts):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = PP_ALIGN.CENTER
            r = p.add_run(); r.text = t; r.font.size = Pt(sz); r.font.bold = b; r.font.color.rgb = rgb(col); r.font.name = font

    def grid(self, s, items, top=Inches(2.45), bottom=Inches(6.85), cols=None, emoji_size=54, word_size=28):
        """items: (emoji, word, english) cards."""
        n = len(items)
        cols = cols or (5 if n > 8 else 4 if n > 6 else 3 if n in (3, 5, 6) else max(n, 1) if n <= 4 else 4)
        rows = -(-n // cols)
        longest = max(len(w) for _, w, _ in items)
        limit = {3: 16, 4: 11, 5: 9}.get(cols, 7)
        if longest > limit: word_size = max(16, int(word_size * limit / longest))
        gap = Inches(0.25)
        cw = int((Inches(12.1) - gap * (cols - 1)) / cols)
        ch = int(min(Inches(2.1), (bottom - top - gap * (rows - 1)) / rows))
        for i, (em, word, en) in enumerate(items):
            r_, c_ = divmod(i, cols)
            x = Inches(0.6) + c_ * (cw + gap); y = top + r_ * (ch + gap)
            b = self.box(s, x, y, cw, ch, line=PALETTE[i % 5], lw=3)
            parts = []
            if em: parts.append((em, emoji_size if ch > Inches(1.5) else int(emoji_size * .75), NAVY, False, BODY))
            parts.append((word, word_size, NAVY, True, BODY))
            if en: parts.append((en.replace("*", ""), 14, MUTED, False, BODY))
            self.card_text(b, parts)

    def chips(self, s, items, top=Inches(3.4), size=26, cols=None):
        n = len(items)
        cols = cols or (5 if n > 12 else 4 if n > 6 else 3 if n > 4 else n)
        if max(len(x) for x in items) > 22: cols = min(cols, 2); size = min(size, 22)
        elif max(len(x) for x in items) > 14: cols = min(cols, 3)
        rows = -(-n // cols)
        gap = Inches(0.2)
        cw = int((Inches(12.1) - gap * (cols - 1)) / cols)
        ch = int(min(Inches(1.0), (Inches(6.8) - top - gap * (rows - 1)) / rows))
        if ch < Inches(0.55): size = min(size, 18)
        for i, t in enumerate(items):
            r_, c_ = divmod(i, cols)
            b = self.box(s, Inches(0.6) + c_ * (cw + gap), top + r_ * (ch + gap), cw, ch, fill=WHITE, line=PALETTE[i % 5], lw=3, radius=0.3)
            self.card_text(b, [(t.replace("*", ""), size, NAVY, True, BODY)])

    def syll_row(self, s, sylls, y, h, size):
        n = len(sylls); gap = Inches(0.25)
        cw = int((Inches(12.1) - gap * (n - 1)) / n)
        for i, sy in enumerate(sylls):
            col = VOWEL.get(sy[-1], NAVY)
            b = self.box(s, Inches(0.6) + i * (cw + gap), y, cw, h, fill=WHITE, line=col, lw=4)
            tf = b.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
            for part, c in ((sy[:-1], NAVY), (sy[-1], col)):
                if part:
                    r = p.add_run(); r.text = part; r.font.size = Pt(size); r.font.bold = True; r.font.name = BODY; r.font.color.rgb = rgb(c)

    # ── save with notes and timings ──
    def save(self, path):
        total = sum(MINUTES[k] for _, k, _ in self.slides)
        scale = 40 / total
        t = 0.0
        for s, kind, notes in self.slides:
            m = MINUTES[kind] * scale
            a, b = t, t + m
            stamp = f"⏱ {fmt(a)}–{fmt(b)}  ({m:.1f} min)"
            s.notes_slide.notes_text_frame.text = stamp + "\n\n" + notes.strip()
            t = b
        self.prs.save(path)


def fmt(m):
    sec = int(round(m * 60)); return f"{sec // 60}:{sec % 60:02d}"


def clean(t): return t.replace("*", "") if t else t


def syllables(letter):
    return [letter + v for v in "aeiou"]


# ── slide recipes ────────────────────────────────────────────────────────
def s_title(d):
    L = d.L
    s = d.new("title", f"""SCRIPT:
Salibonani! Welcome to HILYS, isiNdebele for children. This is Book 1, lesson {L['n']}: {L['title_nd']}, {L['title_en'].lower()}.
Get your book ready. We are on page{'s' if '–' in L['pages'] else ''} {L['pages']}. Let's begin!

FOR VIDEO: show this title card for about 5 seconds with music.""", dark=True)
    d.text(s, f"ISIFUNDO {L['n']}  ·  LESSON {L['n']}", Inches(0.8), Inches(1.3), Inches(8), Inches(0.5), 20, YEL, True, font=HEAD)
    d.text(s, None, Inches(0.8), Inches(1.95), Inches(8.2), Inches(3.2), 60, font=HEAD, anchor=MSO_ANCHOR.MIDDLE, lines=[
        (L["title_nd"], 60, WHITE, True), (L["title_en"], 28, TEAL, False)])
    d.text(s, f"Sekuthe Dlwe — Ugwalo Lokuqala 1a  ·  pages {L['pages']}", Inches(0.8), Inches(5.4), Inches(8), Inches(0.5), 16, GREY)
    em = (L.get("key") or ("📚",))[0] if L["kind"] == "phonics" else {"pre": "👨‍👩‍👧", "vowels": "🔤", "review": "⭐",
                                                                      "reading": "📖", "celebration": "🏆"}[L["kind"]]
    c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(9.3), Inches(1.6), Inches(3.4), Inches(3.4))
    c.fill.solid(); c.fill.fore_color.rgb = rgb(YEL); c.line.color.rgb = rgb(WHITE); c.line.width = Pt(6)
    big = L.get("letter")
    d.card_text(c, [((big + (L.get("letter2") or "")) if big else em, 110 if big else 96, NAVY, True, BODY)])


def s_greeting(d):
    s = d.new("greeting", """SCRIPT:
Let's say hello the isiNdebele way! I say "Salibonani!" and you say "Yebo, salibonani!"
Salibonani! … (pause for the child) … Yebo, salibonani!
Now I ask "Linjani?", which means "How are you all?" You answer "Siyaphila!", which means "We are well!"
Linjani? … (pause) … Siyaphila! Wonderful!

TEACHER: Wave with your whole hand. Do it twice: once softly, once LOUD. In the video, leave a 2-second pause after each question for the child to answer.""",
              tag="UKUBINGELELA · HELLO", tag_color=YEL)
    d.heading(s, "Salibonani!", "Let's greet each other")
    for i, (nd, en) in enumerate(GREETING):
        y = Inches(2.65) + (i // 2) * Inches(2.05)
        x = Inches(0.6) + (i % 2) * Inches(6.15)
        who = "Mina  🙋🏾 (teacher)" if i % 2 == 0 else "Wena  🧒🏾 (you)"
        b = d.box(s, x, y, Inches(5.95), Inches(1.8), line=PALETTE[i], lw=3)
        d.card_text(b, [(who, 14, MUTED, False, BODY), (nd, 34, NAVY, True, BODY), (en, 16, MUTED, False, BODY)])


def s_goals(d):
    L = d.L
    goals = L.get("goals") or default_goals(L)
    s = d.new("goals", "SCRIPT:\nToday we will learn three things:\n" + "\n".join(f"{i+1}. {g}" for i, g in enumerate(goals)) +
              "\nAre you ready? Say “Yebo!”", tag="LAMUHLA · TODAY", tag_color=TEAL)
    d.heading(s, "Lamuhla sizafunda…", "Today we will learn…")
    for i, g in enumerate(goals):
        b = d.box(s, Inches(0.6), Inches(2.6) + i * Inches(1.35), Inches(12.1), Inches(1.15), line=PALETTE[i], lw=3)
        tf = b.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE; tf.margin_left = Inches(0.4)
        p = tf.paragraphs[0]
        r = p.add_run(); r.text = f"{['①','②','③','④'][i]}  "; r.font.size = Pt(30); r.font.color.rgb = rgb(PALETTE[i] if PALETTE[i] != YEL else ORA); r.font.bold = True
        r = p.add_run(); r.text = g; r.font.size = Pt(26); r.font.name = BODY; r.font.color.rgb = rgb(NAVY)


def default_goals(L):
    k = L["kind"]
    if k == "phonics":
        lt = L["letter"] + (" and " + L["letter2"] if L.get("letter2") else "")
        g = [f"Say and read the sound {lt}" + (" (a click!)" if L.get("click") else ""),
             f"Read {L['letter']}a {L['letter']}e {L['letter']}i {L['letter']}o {L['letter']}u and new words",
             "Read sentences and write the letter"]
        return g
    if k == "review":
        return [f"Remember the sounds {' '.join(L['letters'])}", "Read words and sentences on our own", "Play a game and finish the words"]
    if k == "reading":
        return [f"Talk about pictures: {L['title_en'].lower()}", "Read a short story from the book", "Answer questions and finish the words"]
    return ["Show the family everything we can read", "Read a story out loud", "Get your Book 1 certificate!"]


def s_review(d, prev):
    if prev is None: return
    if prev["kind"] == "phonics":
        rows = [" ".join(syllables(prev["letter"]))] + ([" ".join(syllables(prev["letter2"]))] if prev.get("letter2") else [])
        kw = prev["key"]; extra = f"{kw[1]}  {kw[0]}" + (f"   {prev['key2'][1]}  {prev['key2'][0]}" if prev.get("key2") else "")
        lines = rows + [extra]
    elif prev["kind"] == "vowels":
        lines = ["a  e  i  o  u", "u  o  i  e  a", "umama  ubaba  ugogo"]
    elif prev.get("read"):
        lines = prev["read"][:4]
    elif prev.get("talk"):
        lines = ["  ".join(f"{e} {w}" for e, w, _ in prev["talk"]["items"][:4])]
    else:
        lines = ["a  e  i  o  u"]
    s = d.new("review", f"""SCRIPT:
Do you remember what we learned last time? Lesson {prev['n']}: {prev['title_nd']}, {prev['title_en'].lower()}.
Let's read it together. Read each line with me:
""" + "\n".join(lines) + """
Great remembering! (Sizwe!)

TEACHER: Point to each item. Let the child read first and only help if they get stuck. Note any sounds they forgot.""",
              tag="KHUMBULA · REMEMBER", tag_color=BLUE)
    d.heading(s, "Khumbula!", f"Remember lesson {prev['n']}: {prev['title_en']}")
    for i, ln in enumerate(lines[:4]):
        b = d.box(s, Inches(0.6), Inches(2.6) + i * Inches(1.08), Inches(12.1), Inches(0.92), line=PALETTE[(i + 3) % 5], lw=3)
        d.card_text(b, [(ln, 32 if len(ln) < 40 else 24, NAVY, True, BODY)])


def s_letter(d, letter, key):
    L = d.L
    word, em, en = key
    s = d.new("letter", f"""SCRIPT:
Here is our new sound: {letter}! Small {letter} and big {letter.upper()}.
Our picture word is "{word}"{f', which means {clean(en)}' if en else ''}. Listen: {word}. Say it with me: {word}!
Can you hear the {letter} sound in {word}?
{"TEACHER: *English meaning to be checked/added by Sija." if not en or '*' in (en or '') else ''}
TEACHER: Draw the letter in the air with your finger together.""", tag="UMSINDO OMUTSHA · NEW SOUND", tag_color=ORA)
    b = d.box(s, Inches(0.6), Inches(1.35), Inches(5.4), Inches(5.4), fill=YEL, line=NAVY, lw=4)
    d.card_text(b, [(f"{letter} {letter.upper()}", 150, NAVY, True, BODY)])
    c = d.box(s, Inches(6.4), Inches(1.35), Inches(6.3), Inches(5.4), line=TEAL, lw=4)
    d.card_text(c, [(em, 120, NAVY, False, BODY), (word, 54, NAVY, True, BODY)] + ([(clean(en), 22, MUTED, False, BODY)] if en else []))


def s_tip(d):
    L = d.L
    click = L.get("click")
    s = d.new("tip", f"""SCRIPT:
{"This is a special sound: a CLICK! isiNdebele has three clicks and this is one of them. " if click else ""}Let's learn how to make the sound.
{clean(L['tip'])}
Try it three times with me … 1, 2, 3!
{"Now try the click with each vowel: " + ", ".join(syllables(L['letter'])) + "." if click else ""}
TEACHER: Exaggerate your mouth on camera. For video, use a close-up of the mouth.""",
              tag="ICHOFO! · A CLICK!" if click else "YENZA UMSINDO · MAKE THE SOUND", tag_color=COR if click else TEAL)
    d.heading(s, "Ichofo!" if click else "Yenza umsindo", "A click sound: let's make it!" if click else "How to make the sound")
    b = d.box(s, Inches(0.6), Inches(2.6), Inches(2.6), Inches(4.0), fill=COR if click else TEAL)
    d.card_text(b, [("👅" if click else "👄", 90, NAVY, False, BODY)])
    t = d.box(s, Inches(3.5), Inches(2.6), Inches(9.2), Inches(4.0), line=COR if click else TEAL, lw=3)
    d.card_text(t, [(clean(L["tip"]), 26 if len(L["tip"]) < 150 else 22, NAVY, False, BODY)], anchor=MSO_ANCHOR.MIDDLE)


def s_syllables(d, letter):
    L = d.L
    sy = syllables(letter)
    mix = [sy[i] for i in (1, 4, 0, 3, 2)]
    s = d.new("syllables", f"""SCRIPT:
Now we join {letter} with each vowel. Watch the colours: each vowel has its own colour.
{letter} + a = {sy[0]}, {letter} + e = {sy[1]}, {letter} + i = {sy[2]}, {letter} + o = {sy[3]}, {letter} + u = {sy[4]}.
Read with me: {' – '.join(sy)}.
Now the mixed row. Can you read it on your own? {' – '.join(mix)}.
SING IT: sing {' '.join(sy)} to the tune of "Twinkle, Twinkle, Little Star", then faster!

TEACHER: Point at each card. Read the top row 3 times (slow, normal, fast), then the mixed row.""",
              tag="IZINKAMISA · SYLLABLES", tag_color=YEL)
    d.heading(s, f"{letter} + a e i o u", "Read the syllables")
    d.syll_row(s, sy, Inches(2.55), Inches(1.9), 80)
    d.syll_row(s, mix, Inches(4.75), Inches(1.5), 54)


def s_words(d, words, title=("Amabala", "Words"), tag="AMABALA · WORDS"):
    L = d.L
    lines = "\n".join(f"{e} {w}{' — ' + clean(en) if en else ''}" for w, e, en in words)
    missing = [w for w, e, en in words if not en]
    s = d.new("words", f"""SCRIPT:
Let's read some words. I'll read each word, then you say it after me.
{lines}
Now you read them on your own, from the first to the last!
{"TEACHER: Meanings still needed from Sija for: " + ", ".join(missing) + ". Explain them in your own words." if missing else ""}""",
              tag=tag, tag_color=TEAL)
    d.heading(s, title[0], title[1])
    d.grid(s, [(e, w, en) for w, e, en in words])


def s_read(d, rows, title=("Ake sibale", "Let's read (from the book)")):
    for part in range(0, len(rows), 5):
        chunk = rows[part:part + 5]
        s = d.new("read", f"""SCRIPT:
Open your book. Let's read these lines together, slowly, one at a time.
""" + "\n".join(chunk) + """
Now read them again, a little faster. Well done!

TEACHER: Child reads each line first. Track with your finger (or the cursor in the video).""",
                  tag="UKUBALA · READING", tag_color=BLUE)
        d.heading(s, title[0], title[1] + (" (continued)" if part else ""))
        h = Inches(0.84)
        for i, ln in enumerate(chunk):
            b = d.box(s, Inches(0.6), Inches(2.5) + i * (h + Inches(0.08)), Inches(12.1), h, line=PALETTE[i % 5], lw=3)
            d.card_text(b, [(ln, 30 if len(ln) < 44 else 24, NAVY, True, BODY)])
    # scale: count extra read slides as part of the reading time
    if len(rows) > 5:
        for sl in d.slides[-(-(-len(rows) // 5)):]:
            pass


def s_sentences(d, sents, title=("Imisho", "Sentences")):
    s = d.new("sentences", "SCRIPT:\nNow we read whole sentences! Listen first, then read with me.\n" +
              "\n".join(f"{nd} — {clean(en) if en else '(meaning: ask Sija)'}" for nd, en in sents) +
              "\nAct each sentence out with your body!\n\nTEACHER: Sentences marked * in the lesson file were added by HILYS; check them.",
              tag="IMISHO · SENTENCES", tag_color=COR)
    d.heading(s, title[0], title[1])
    n = len(sents); h = min(Inches(1.15), int((Inches(4.3) - Inches(0.12) * (n - 1)) / n))
    for i, (nd, en) in enumerate(sents):
        b = d.box(s, Inches(0.6), Inches(2.55) + i * (h + Inches(0.12)), Inches(12.1), h, line=PALETTE[(i + 2) % 5], lw=3)
        d.card_text(b, [(nd, 30 if h > Inches(0.95) else 24, NAVY, True, BODY)] + ([(clean(en), 15, MUTED, False, BODY)] if en else []))


def s_story(d, st):
    lines = st["lines"]
    for part in range(0, len(lines), 5):
        chunk = lines[part:part + 5]
        s = d.new("story", f"""SCRIPT:
Story time! This story is on page {st['page']} of your book. It is called "{st['title']}", which means "{st['en']}".
Listen while I read, then we read it together.
""" + "\n".join(f"{nd}  ({clean(en) if en else 'meaning: ask Sija'})" for nd, en in chunk) + """
Questions: Who is in the story? What happened? Point to the picture in your book.

TEACHER: Read 3 times: (1) teacher reads, (2) together, (3) child alone.""", tag="INDABA · STORY", tag_color=ORA)
        d.heading(s, st["title"], f"{st['en']}  ·  book page {st['page']}" + ("  (continued)" if part else ""))
        n = len(chunk); h = min(Inches(0.95), int((Inches(4.35) - Inches(0.08) * (n - 1)) / n))
        for i, (nd, en) in enumerate(chunk):
            b = d.box(s, Inches(0.6), Inches(2.5) + i * (h + Inches(0.08)), Inches(12.1), h, line=PALETTE[i % 5], lw=3)
            d.card_text(b, [(nd, 28, NAVY, True, BODY)] + ([(clean(en), 14, MUTED, False, BODY)] if en else []))


def s_talk(d, t):
    items = t["items"]
    qs = t.get("questions") or []
    s = d.new("talk", f"""SCRIPT:
Let's look at the pictures and talk. {t['en']}.
""" + "\n".join(f"{e} This is {w}{' — ' + clean(en) if en else ''}. Say it: {w}!" for e, w, en in items) +
              ("\n\nQuestions to ask:\n" + "\n".join(f"• {q}{' — ' + a if a else ''}" for q, a in qs) if qs else "") + """

TEACHER: Let the child point and name. Accept English first, then give the isiNdebele word and have them repeat it twice.
Items marked * were added by HILYS; please check the isiNdebele.""", tag="SIXOXA · LET'S TALK", tag_color=BLUE)
    d.heading(s, t["title"], t["en"])
    top = Inches(2.45)
    if qs and len(items) <= 8:
        q = qs[0]
        b = d.box(s, Inches(0.6), Inches(6.05), Inches(12.1), Inches(0.75), fill=YEL)
        d.card_text(b, [(f"💬  {q[0]}" + (f"   ·   {q[1]}" if q[1] else ""), 20, NAVY, True, BODY)])
        d.grid(s, items, top=top, bottom=Inches(5.85))
    else:
        d.grid(s, items, top=top)


def s_game(d, g):
    s = d.new("game", f"""SCRIPT:
Game time! This game is called "{g['title']}", which means "{g['en']}".
{clean(g['how'])}
Ready? Let's play!
Items: {' | '.join(clean(x) for x in g['items'])}

TEACHER: Keep it fast and fun. Cheer every try: “Sizwe!” (Well done!) For the video, show each item for 3–4 seconds with a pause for the child to answer.""",
              tag="UMDLALO · GAME", tag_color=COR)
    d.heading(s, f"🎲 {g['title']}", g["en"])
    d.text(s, clean(g["how"]), Inches(0.6), Inches(2.45), Inches(12.1), Inches(0.8), 20, NAVY2)
    d.chips(s, g["items"], top=Inches(3.35))


def s_qedisa(d, items):
    s = d.new("qedisa", "SCRIPT:\nQedisa! Finish the word. Which letters are missing? Look carefully and say the whole word.\n" +
              "\n".join(f"{q}  → missing: {a}" for q, a in items) +
              "\nTake your time; the answers are on the next slide.", tag="QEDISA · FINISH IT", tag_color=YEL)
    d.heading(s, "✏️ Qedisa!", "Fill in the missing letters")
    d.chips(s, [q for q, _ in items], top=Inches(2.6), size=34)
    s2 = d.new("answers", "SCRIPT:\nLet's check! " + " ".join(f"{fill(q, a)}." for q, a in items) + "\nHow many did you get right? Sizwe!",
               tag="IZIMPENDULO · ANSWERS", tag_color=TEAL)
    d.heading(s2, "✅ Izimpendulo", "Answers")
    d.chips(s2, [fill(q, a) for q, a in items], top=Inches(2.6), size=34)


def fill(q, a):
    """'___' (3+ underscores) is a missing word; a single '_' is a missing letter group inside one word."""
    q = re.sub(r"\s*\(.*?\)", "", q).strip()
    if re.search(r"_{3,}", q):
        return re.sub(r"\s+([.?!])", r"\1", re.sub(r"_{3,}", a, q))
    parts = a.split()
    word = q.replace(" ", "")
    for i in range(word.count("_")):
        word = word.replace("_", parts[i] if i < len(parts) else parts[-1], 1)
    return word


def s_culture(d, c):
    nd, en, body = c
    s = d.new("culture", f"""SCRIPT:
Ulwazi! Did you know? Today's topic: {nd}, {en.lower()}.
{clean(body)}
What do you think? Have you seen this? Ask your family about it tonight!

TEACHER: This is the "value" part of the lesson. Add a photo or a short clip here when editing the video. Facts marked * should be checked.""",
              tag="ULWAZI · DID YOU KNOW?", tag_color=ORA)
    d.heading(s, f"🌍 {nd}", en)
    b = d.box(s, Inches(0.6), Inches(2.6), Inches(12.1), Inches(4.1), line=ORA, lw=4)
    d.card_text(b, [(clean(body), 26 if len(body) < 230 else 23, NAVY, False, BODY)])


def s_chant(d, lines):
    s = d.new("chant", "SCRIPT:\nLet's chant together! Clap on every word.\n" + "\n".join(lines) +
              "\nAgain, louder! And once more, whispering!\n\nTEACHER: Original HILYS chant. Set it to any simple tune.",
              tag="SIHLABELELE · LET'S CHANT", tag_color=TEAL)
    d.heading(s, "🎵 Sihlabelele!", "Let's chant")
    b = d.box(s, Inches(0.6), Inches(2.6), Inches(12.1), Inches(4.1), fill=NAVY)
    d.card_text(b, [(ln, 34, WHITE if i < len(lines) - 1 or not ln.isascii() else YEL, True, BODY) for i, ln in enumerate(lines)])


def s_writing(d, w):
    L = d.L
    kind = w["kind"] if isinstance(w, dict) else "letters"
    txt = w["text"] if isinstance(w, dict) else w
    s = d.new("writing", f"""SCRIPT:
Get your pencil and paper. Let's write!
{"First trace it in the air with your finger, then on the table, then on paper. " if kind == 'letters' else ''}{txt if kind != 'letters' else 'Write: ' + txt}
Start at the top, go slowly, and keep your letters sitting on the line.
Write each one 5 times. Then show me!

TEACHER: Hold the paper up to the camera to check. Praise the best one.""", tag="AKE SIBHALE · LET'S WRITE", tag_color=BLUE)
    d.heading(s, "✏️ Ake sibhale", "Let's write")
    b = d.box(s, Inches(0.6), Inches(2.55), Inches(12.1), Inches(4.2), line=BLUE, lw=3)
    if kind == "letters":
        d.card_text(b, [(txt, 120 if len(txt) < 8 else 90, "D3D7E8", True, BODY)])
    else:
        d.card_text(b, [("— —   ⌒⌒   /\\/\\   ◯◯", 48, "C3C8DD", True, BODY), (txt, 22, NAVY, False, BODY)])
    for k in range(3):  # handwriting lines
        y = Inches(5.55) + k * Inches(0.32)
        ln = s.shapes.add_connector(1, Inches(1.0), y, Inches(12.3), y)
        ln.line.color.rgb = rgb("C9CEE3" if k != 1 else COR); ln.line.width = Pt(1.25)
        if k == 1: ln.line.dash_style = 4


def s_home(d):
    L = d.L
    s = d.new("home", f"""SCRIPT:
Here is your home task before next lesson: {clean(L['home'])}
Ask a grown-up to help you, and tell me all about it next time!""", tag="UMSEBENZI WASEKHAYA · HOME TASK", tag_color=YEL)
    d.heading(s, "🏠 Umsebenzi wasekhaya", "Home task")
    b = d.box(s, Inches(0.6), Inches(2.6), Inches(12.1), Inches(3.0), fill=YEL)
    d.card_text(b, [(clean(L["home"]), 30, NAVY, True, BODY)])
    d.text(s, "Parents: please help your child do this before the next lesson. Thank you! Ngiyabonga!", Inches(0.6), Inches(5.85),
           Inches(12.1), Inches(0.6), 16, MUTED, align=PP_ALIGN.CENTER)


def s_goodbye(d, nxt):
    s = d.new("goodbye", f"""SCRIPT:
You did so well today. Sizwe kakhulu!
{"Next time we will learn: " + nxt['title_nd'] + ", " + nxt['title_en'].lower() + "." if nxt else "You finished Book 1!"}
I say "Sala kuhle!" (stay well), and you say "Hamba kuhle!" (go well).
Sala kuhle! … Hamba kuhle! Bye-bye!

FOR VIDEO: end card with music, about 5 seconds.""", dark=True)
    d.text(s, "Sala kuhle! 👋🏾", Inches(0.6), Inches(1.4), Inches(12.1), Inches(1.6), 72, WHITE, True, align=PP_ALIGN.CENTER, font=HEAD)
    d.text(s, "Hamba kuhle!  ·  Goodbye, see you next time!", Inches(0.6), Inches(3.05), Inches(12.1), Inches(0.7), 26, TEAL,
           align=PP_ALIGN.CENTER, font=HEAD)
    b = d.box(s, Inches(2.6), Inches(4.3), Inches(8.1), Inches(1.9), fill=NAVY2, line=YEL, lw=3)
    if nxt:
        d.card_text(b, [("NEXT LESSON  ·  ISIFUNDO " + str(nxt["n"]), 16, YEL, True, HEAD), (nxt["title_nd"], 34, WHITE, True, BODY),
                        (nxt["title_en"], 18, GREY, False, BODY)])
    else:
        d.card_text(b, [("🎉 BOOK 1 COMPLETE", 30, YEL, True, HEAD), ("Next: Book 1b", 22, WHITE, False, BODY)])


# special recipes
def s_vowels(d):
    info = [("a", "like “a” in father", "amasi"), ("e", "like “e” in bed", "esikolo"), ("i", "like “ee” in see", "iluba"),
            ("o", "like “o” in more", "omama"), ("u", "like “oo” in moon", "umama")]
    s = d.new("vowels", "SCRIPT:\nMeet the five vowels (onkamisa). Every isiNdebele syllable has one!\n" +
              "\n".join(f"{v} — {h}. Example: {ex}." for v, h, ex in info) +
              "\nSay them with me: a – e – i – o – u! Now open your mouth wide for a, smile for e and i, make a circle for o and u.\n\n"
              "VIDEO: give each vowel its own colour; these colours stay the same in every lesson.", tag="ONKAMISA · VOWELS", tag_color=TEAL)
    d.heading(s, "a  e  i  o  u", "The 5 vowels: onkamisa")
    gap = Inches(0.25); cw = int((Inches(12.1) - gap * 4) / 5)
    for i, (v, h, ex) in enumerate(info):
        b = d.box(s, Inches(0.6) + i * (cw + gap), Inches(2.55), cw, Inches(4.2), line=VOWEL[v], lw=5)
        d.card_text(b, [(v, 110, VOWEL[v], True, BODY), (h, 15, MUTED, False, BODY), (ex, 22, NAVY, True, BODY)])


def s_rows(d, rows):
    s = d.new("rows", "SCRIPT:\nLet's read the vowels in different orders. Point and read each row, like book page 10.\n" +
              "\n".join(" – ".join(r) for r in rows) + "\nFaster now! Can you read a row in 3 seconds?", tag="UKUBALA · READING", tag_color=BLUE)
    d.heading(s, "Bala onkamisa", "Read the vowels")
    for i, r in enumerate(rows):
        d.syll_row(s, r, Inches(2.45) + i * Inches(1.08), Inches(0.95), 46)


def s_capitals(d, caps):
    s = d.new("capitals", "SCRIPT:\nEvery letter has a big brother: the capital letter! We use capitals at the start of names and sentences.\n" +
              "\n".join(f"Big {a}, small {b}." for a, b in caps) + "\nYour name starts with a capital letter too!",
              tag="AMABALA AMAKHULU · CAPITALS", tag_color=ORA)
    d.heading(s, "Aa  Bb  Cc", "Capital letters (book page 34)")
    d.chips(s, [f"{a}  {b}" for a, b in caps], top=Inches(2.7), size=60, cols=5)
    d.text(s, "Umama  ·  Ubaba  ·  UVusa  ·  Bona umuzi kaZulu.", Inches(0.6), Inches(5.0), Inches(12.1), Inches(1), 30, NAVY, True,
           align=PP_ALIGN.CENTER)


def s_counting(d, c):
    s = d.new("counting", "SCRIPT:\nLet's count to five in isiNdebele!\n" + "\n".join(f"{n} — {w}" for n, w, _ in c) +
              "\nCount on your fingers with me. Again, faster!", tag="AMANANI · NUMBERS", tag_color=YEL)
    d.heading(s, "Bala amanani", "Count 1 to 5")
    d.grid(s, [(e, f"{n}  {w}", None) for n, w, e in c], cols=5, emoji_size=26, word_size=26)


def s_plurals(d, pl):
    s = d.new("plurals", "SCRIPT:\nOne and many! In isiNdebele we change the START of the word to make many.\n" +
              "\n".join(f"One: {a}. Many: {b}." for a, b in pl) + "\nWhat changed? The beginning!", tag="KUNYE · KUNENGI", tag_color=TEAL)
    d.heading(s, "Kunye → kunengi", "One → many (book page 51)")
    for i, (a, b) in enumerate(pl):
        y = Inches(2.45) + i * Inches(0.86)
        x1 = d.box(s, Inches(0.6), y, Inches(5.3), Inches(0.74), line=BLUE, lw=3); d.card_text(x1, [(a, 28, NAVY, True, BODY)])
        d.text(s, "→", Inches(6.0), y, Inches(1.3), Inches(0.74), 34, ORA, True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        x2 = d.box(s, Inches(7.4), y, Inches(5.3), Inches(0.74), line=COR, lw=3); d.card_text(x2, [(b, 28, NAVY, True, BODY)])


def s_past(d, pt):
    s = d.new("past", "SCRIPT:\nNow or already done? “uyalima” means he is digging NOW. “ulimile” means he HAS dug.\n" +
              "\n".join(f"{a} → {b}" for a, b in pt) + "\nListen to the endings: -ile means it is already done!",
              tag="MANJE · SEKWENZIWE", tag_color=BLUE)
    d.heading(s, "Manje → sekwenziwe", "Now → already done (book page 60)")
    for i, (a, b) in enumerate(pt):
        y = Inches(2.45) + i * Inches(0.86)
        x1 = d.box(s, Inches(0.6), y, Inches(5.3), Inches(0.74), line=TEAL, lw=3); d.card_text(x1, [(a, 28, NAVY, True, BODY)])
        d.text(s, "→", Inches(6.0), y, Inches(1.3), Inches(0.74), 34, ORA, True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        x2 = d.box(s, Inches(7.4), y, Inches(5.3), Inches(0.74), line=ORA, lw=3); d.card_text(x2, [(b, 28, NAVY, True, BODY)])


def s_letters(d, letters, keys):
    s = d.new("letters", "SCRIPT:\nLet's remember our sounds and their picture words.\n" +
              "\n".join(f"{l} — {keys.get(l, ('', '', ''))[0]}" for l in letters) + "\nPoint to a letter and say its sound!",
              tag="IMISINDO · OUR SOUNDS", tag_color=YEL)
    d.heading(s, "Imisindo yethu", "Our sounds")
    d.grid(s, [(keys.get(l, ("", "🔤", ""))[1], l, keys.get(l, ("",))[0]) for l in letters], emoji_size=30, word_size=36,
           cols=5 if len(letters) <= 10 else 7, top=Inches(2.4))


def s_certificate(d):
    s = d.new("certificate", "SCRIPT:\nThis is for you! You finished Book 1 of HILYS. Sizwe kakhulu, well done!\n"
              "Write your name on the certificate and show your whole family.\n\nTEACHER: Type the child's name on this slide before the lesson.",
              dark=True)
    b = d.box(s, Inches(1.4), Inches(0.9), Inches(10.5), Inches(5.8), fill=WHITE, line=YEL, lw=8)
    d.card_text(b, [("🏆", 70, NAVY, False, BODY), ("Isitifiketi · Certificate", 20, MUTED, True, HEAD),
                    ("______________________", 34, NAVY, True, BODY),
                    ("has finished HILYS Book 1: Sekuthe Dlwe 1a", 22, NAVY, False, BODY),
                    ("Siyakubongela!  Congratulations!", 30, ORA, True, HEAD)])


# ── lesson assembly ──────────────────────────────────────────────────────
def build(L, prev, nxt, keys):
    d = Deck(L)
    s_title(d); s_greeting(d); s_goals(d); s_review(d, prev)
    k = L["kind"]
    if k == "phonics":
        s_letter(d, L["letter"], L["key"])
        if L.get("letter2"): s_letter(d, L["letter2"], L["key2"])
        s_tip(d); s_syllables(d, L["letter"])
        if L.get("letter2"): s_syllables(d, L["letter2"])
        s_words(d, L["words"])
        s_read(d, L["read"])
        if L.get("story"): s_story(d, L["story"])
        if L.get("sentences"): s_sentences(d, L["sentences"])
        if L.get("talk"): s_talk(d, L["talk"])
        s_game(d, L["game"])
        s_culture(d, L["culture"])
        s_qedisa(d, L["qedisa"])
        s_writing(d, " ".join(f"{x}  {x.upper()}" for x in [L["letter"]] + ([L["letter2"]] if L.get("letter2") else [])))
    elif k in ("pre", "vowels"):
        if L.get("vowels_intro"): s_vowels(d)
        if L.get("read_rows"): s_rows(d, L["read_rows"])
        if L.get("talk"): s_talk(d, L["talk"])
        s_game(d, L["game"])
        if L.get("game2"): s_game(d, L["game2"])
        if L.get("chant"): s_chant(d, L["chant"])
        s_culture(d, L["culture"])
        s_writing(d, L["writing"])
    elif k == "review":
        s_letters(d, L["letters"], keys)
        if L.get("capitals"): s_capitals(d, L["capitals"])
        s_read(d, L["read"])
        if L.get("sentences"): s_sentences(d, L["sentences"])
        if L.get("talk"): s_talk(d, L["talk"])
        s_game(d, L["game"]); s_culture(d, L["culture"]); s_qedisa(d, L["qedisa"])
        s_writing(d, "  ".join(L["letters"]))
    elif k == "reading":
        if L.get("talk"): s_talk(d, L["talk"])
        if L.get("story"): s_story(d, L["story"])
        if L.get("read"): s_read(d, L["read"])
        if L.get("counting"): s_counting(d, L["counting"])
        if L.get("plurals"): s_plurals(d, L["plurals"])
        if L.get("pasttense"): s_past(d, L["pasttense"])
        s_game(d, L["game"]); s_culture(d, L["culture"]); s_qedisa(d, L["qedisa"])
    elif k == "celebration":
        s_letters(d, L["letters"], keys); s_read(d, L["read"]); s_story(d, L["story"]); s_game(d, L["game"])
        s_culture(d, L["culture"]); s_certificate(d)
    s_home(d); s_goodbye(d, nxt)
    return d


def slug(L):
    t = re.sub(r"[^A-Za-z0-9]+", "-", L["title_en"]).strip("-").lower()
    return f"HILYS Book 1 - Lesson {L['n']:02d} - {L['title_nd']} ({L['title_en']})"


def main():
    out = os.path.join(HERE, "decks"); os.makedirs(out, exist_ok=True)
    keys = {}
    for L in LESSONS:
        if L["kind"] == "phonics":
            keys[L["letter"]] = L["key"]
            if L.get("letter2"): keys[L["letter2"]] = L["key2"]
    only = [int(a) for a in sys.argv[1:]]
    for i, L in enumerate(LESSONS):
        if only and L["n"] not in only: continue
        d = build(L, LESSONS[i - 1] if i else None, LESSONS[i + 1] if i + 1 < len(LESSONS) else None, keys)
        name = slug(L).replace(":", "") + ".pptx"
        d.save(os.path.join(out, name))
        print(f"{len(d.slides):3d} slides  {name}")
    if not only: write_docs()


def write_docs():
    kinds = {"pre": "Getting ready", "vowels": "Vowels", "phonics": "New sound", "review": "Review", "reading": "Reading", "celebration": "Show"}
    rows = ["| # | Lesson | Type | Book pages | Culture piece |", "|---|---|---|---|---|"]
    for L in LESSONS:
        rows.append(f"| {L['n']} | **{L['title_nd']}**: {L['title_en']} | {kinds[L['kind']]} | {L['pages']} | {L['culture'][1]} |")
    md = f"""# HILYS Book 1: lesson map

Source: *Sekuthe Dlwe — Ugwalo Lokuqala 1a* (CPS, 2017), 62 pages. 35 lessons of 40 minutes each.
The slides follow the book's order and words, using our own visuals (no scans from the book).

## Every lesson follows the same shape

| Part | What happens |
|---|---|
| Hello | *Salibonani! / Linjani?*, the same every time |
| Remember | quick review of last lesson |
| New sound | letter card, how to make the sound, syllables (ma me mi mo mu) |
| Words and reading | picture words, lines from the book, sentences or a story |
| Talk | picture talk about the book's theme pages |
| Game | a short game that uses the new sound |
| Did you know? | a culture piece: this is the added value |
| Finish it (*Qedisa*) | fill in the missing letters, then the answers |
| Write | trace and write the letter |
| Home task and goodbye | *Sala kuhle! / Hamba kuhle!* |

Each slide's speaker notes hold the timing (adds up to 40:00) and a full narration script for the videos.

## The 35 lessons

""" + "\n".join(rows) + """

At 2 lessons a week, Book 1 takes about 4½ months.

## Rebuilding the slides
Edit `lessons.py`, then run `python build.py`. The decks are written to `decks/`.
"""
    open(os.path.join(HERE, "LESSON-MAP.md"), "w", encoding="utf-8").write(md)

    chk = ["# Words for Sija to check", "",
           "These are glosses or phrases that HILYS added, or book words still missing an English meaning. "
           "Book words are copied from the book. Please correct anything wrong in `lessons.py` and rebuild, or fix it directly in the Google Slides.", ""]
    for L in LESSONS:
        items = []
        for key in ("words",):
            for w, e, en in L.get(key, []):
                if not en: items.append(f"- **{w}**: meaning missing")
                elif "*" in en: items.append(f"- **{w}** = {en.replace('*','')} (added gloss)")
        if L.get("talk"):
            for e, w, en in L["talk"]["items"]:
                if en and "*" in en: items.append(f"- **{w}** = {en.replace('*','')} (added word)")
        for k in ("sentences",):
            for nd, en in L.get(k, []):
                if not en: items.append(f"- **{nd}**: meaning missing")
                elif "*" in en: items.append(f"- **{nd}** = {en.replace('*','')} (added sentence)")
        if L.get("story"):
            for nd, en in L["story"]["lines"]:
                if not en: items.append(f"- **{nd}**: meaning missing")
                elif "*" in en: items.append(f"- **{nd}** = {en.replace('*','')} (translation to check)")
        if "*" in L["culture"][2]: items.append(f"- Culture note: {L['culture'][0]} (contains added isiNdebele)")
        if items:
            chk.append(f"## Lesson {L['n']}: {L['title_nd']}"); chk += items; chk.append("")
    open(os.path.join(HERE, "WORDS-TO-CHECK.md"), "w", encoding="utf-8").write("\n".join(chk))


if __name__ == "__main__":
    main()
