from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import re

import manimpango
import pygments
import pygments.formatters
import pygments.lexers

from manimlib.constants import DEFAULT_PIXEL_WIDTH, FRAME_WIDTH
from manimlib.constants import NORMAL
from manimlib.logger import log
from manimlib.mobject.svg.labelled_string import LabelledString
from manimlib.utils.config_ops import digest_config
from manimlib.utils.customization import get_customization
from manimlib.utils.directories import get_downloads_dir
from manimlib.utils.directories import get_text_dir
from manimlib.utils.tex_file_writing import tex_hash

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from colour import Color
    from typing import Iterable, Union

    from manimlib.mobject.types.vectorized_mobject import VGroup

    ManimColor = Union[str, Color]
    Span = tuple[int, int]
    Selector = Union[
        str,
        re.Pattern,
        tuple[Union[int, None], Union[int, None]],
        Iterable[Union[
            str,
            re.Pattern,
            tuple[Union[int, None], Union[int, None]]
        ]]
    ]


TEXT_MOB_SCALE_FACTOR = 0.0076
DEFAULT_LINE_SPACING_SCALE = 0.6
# Ensure the canvas is large enough to hold all glyphs.
DEFAULT_CANVAS_WIDTH = 16384
DEFAULT_CANVAS_HEIGHT = 16384


# See https://docs.gtk.org/Pango/pango_markup.html
MARKUP_COLOR_KEYS = (
    "foreground", "fgcolor", "color",
    "background", "bgcolor",
    "underline_color",
    "overline_color",
    "strikethrough_color"
)
MARKUP_TAG_CONVERSION_DICT = {
    "b": {"font_weight": "bold"},
    "big": {"font_size": "larger"},
    "i": {"font_style": "italic"},
    "s": {"strikethrough": "true"},
    "sub": {"baseline_shift": "subscript", "font_scale": "subscript"},
    "sup": {"baseline_shift": "superscript", "font_scale": "superscript"},
    "small": {"font_size": "smaller"},
    "tt": {"font_family": "monospace"},
    "u": {"underline": "single"}
}


# Temporary handler
class _Alignment:
    VAL_DICT = {
        "LEFT": 0,
        "CENTER": 1,
        "RIGHT": 2
    }

    def __init__(self, s: str):
        self.value = _Alignment.VAL_DICT[s.upper()]


class MarkupText(LabelledString):
    CONFIG = {
        "is_markup": True,
        "font_size": 48,
        "lsh": None,
        "justify": False,
        "indent": 0,
        "alignment": "LEFT",
        "line_width": None,
        "font": "",
        "slant": NORMAL,
        "weight": NORMAL,
        "gradient": None,
        "t2c": {},
        "t2f": {},
        "t2g": {},
        "t2s": {},
        "t2w": {},
        "global_config": {},
        "local_configs": {},
    }

    def __init__(self, text: str, **kwargs):
        self.full2short(kwargs)
        digest_config(self, kwargs)

        if not self.font:
            self.font = get_customization()["style"]["font"]
        if self.is_markup:
            self.validate_markup_string(text)

        self.text = text
        super().__init__(text, **kwargs)

        if self.t2g:
            log.warning(
                "Manim currently cannot parse gradient from svg. "
                "Please set gradient via `set_color_by_gradient`.",
            )
        if self.gradient:
            self.set_color_by_gradient(*self.gradient)
        if self.height is None:
            self.scale(TEXT_MOB_SCALE_FACTOR)

    @property
    def hash_seed(self) -> tuple:
        return (
            self.__class__.__name__,
            self.svg_default,
            self.path_string_config,
            self.base_color,
            self.isolate,
            self.text,
            self.is_markup,
            self.font_size,
            self.lsh,
            self.justify,
            self.indent,
            self.alignment,
            self.line_width,
            self.font,
            self.slant,
            self.weight,
            self.t2c,
            self.t2f,
            self.t2s,
            self.t2w,
            self.global_config,
            self.local_configs
        )

    def full2short(self, config: dict) -> None:
        conversion_dict = {
            "line_spacing_height": "lsh",
            "text2color": "t2c",
            "text2font": "t2f",
            "text2gradient": "t2g",
            "text2slant": "t2s",
            "text2weight": "t2w"
        }
        for kwargs in [config, self.CONFIG]:
            for long_name, short_name in conversion_dict.items():
                if long_name in kwargs:
                    kwargs[short_name] = kwargs.pop(long_name)

    def get_file_path_by_content(self, content: str) -> str:
        hash_content = str((
            content,
            self.justify,
            self.indent,
            self.alignment,
            self.line_width
        ))
        svg_file = os.path.join(
            get_text_dir(), tex_hash(hash_content) + ".svg"
        )
        if not os.path.exists(svg_file):
            self.markup_to_svg(content, svg_file)
        return svg_file

    def markup_to_svg(self, markup_str: str, file_name: str) -> str:
        self.validate_markup_string(markup_str)

        # `manimpango` is under construction,
        # so the following code is intended to suit its interface
        alignment = _Alignment(self.alignment)
        if self.line_width is None:
            pango_width = -1
        else:
            pango_width = self.line_width / FRAME_WIDTH * DEFAULT_PIXEL_WIDTH

        return manimpango.MarkupUtils.text2svg(
            text=markup_str,
            font="",                     # Already handled
            slant="NORMAL",              # Already handled
            weight="NORMAL",             # Already handled
            size=1,                      # Already handled
            _=0,                         # Empty parameter
            disable_liga=False,
            file_name=file_name,
            START_X=0,
            START_Y=0,
            width=DEFAULT_CANVAS_WIDTH,
            height=DEFAULT_CANVAS_HEIGHT,
            justify=self.justify,
            indent=self.indent,
            line_spacing=None,           # Already handled
            alignment=alignment,
            pango_width=pango_width
        )

    @staticmethod
    def validate_markup_string(markup_str: str) -> None:
        validate_error = manimpango.MarkupUtils.validate(markup_str)
        if not validate_error:
            return
        raise ValueError(
            f"Invalid markup string \"{markup_str}\"\n"
            f"{validate_error}"
        )

    def parse(self) -> None:
        self.global_attr_dict = self.get_global_attr_dict()
        self.tag_pairs_from_markup = self.get_tag_pairs_from_markup()
        self.tag_spans = self.get_tag_spans()
        self.items_from_markup = self.get_items_from_markup()
        self.specified_items = self.get_specified_items()
        super().parse()

    # Toolkits

    @staticmethod
    def get_attr_dict_str(attr_dict: dict[str, str]) -> str:
        return " ".join([
            f"{key}='{val}'"
            for key, val in attr_dict.items()
        ])

    # Parsing

    def get_global_attr_dict(self) -> dict[str, str]:
        result = {
            "foreground": self.int_to_hex(self.base_color_int),
            "font_family": self.font,
            "font_style": self.slant,
            "font_weight": self.weight,
            "font_size": str(self.font_size * 1024),
        }
        # `line_height` attribute is supported since Pango 1.50.
        pango_version = manimpango.pango_version()
        if tuple(map(int, pango_version.split("."))) < (1, 50):
            if self.lsh is not None:
                log.warning(
                    f"Pango version {pango_version} found (< 1.50), "
                    "unable to set `line_height` attribute"
                )
        else:
            line_spacing_scale = self.lsh or DEFAULT_LINE_SPACING_SCALE
            result["line_height"] = str(((line_spacing_scale) + 1) * 0.6)
        return result

    def get_tag_pairs_from_markup(
        self
    ) -> list[tuple[Span, Span, dict[str, str]]]:
        if not self.is_markup:
            return []

        tag_pattern = r"""<(/?)(\w+)\s*((\w+\s*\=\s*(['"])[\s\S]*?\5\s*)*)>"""
        attr_pattern = r"""(\w+)\s*\=\s*(['"])([\s\S]*?)\2"""
        begin_match_obj_stack = []
        match_obj_pairs = []
        for match_obj in re.finditer(tag_pattern, self.string):
            if not match_obj.group(1):
                begin_match_obj_stack.append(match_obj)
            else:
                match_obj_pairs.append(
                    (begin_match_obj_stack.pop(), match_obj)
                )

        result = []
        for begin_match_obj, end_match_obj in match_obj_pairs:
            tag_name = begin_match_obj.group(2)
            if tag_name == "span":
                attr_dict = {
                    match.group(1): match.group(3)
                    for match in re.finditer(
                        attr_pattern, begin_match_obj.group(3)
                    )
                }
            else:
                attr_dict = MARKUP_TAG_CONVERSION_DICT.get(tag_name, {})

            result.append(
                (begin_match_obj.span(), end_match_obj.span(), attr_dict)
            )
        return result

    def get_tag_spans(self) -> list[Span]:
        return self.chain(
            (begin_tag_span, end_tag_span)
            for begin_tag_span, end_tag_span, _ in self.tag_pairs_from_markup
        )

    def get_items_from_markup(self) -> list[tuple[Span, dict[str, str]]]:
        return [
            ((span_begin, span_end), attr_dict)
            for (_, span_begin), (span_end, _), attr_dict
            in self.tag_pairs_from_markup
            if span_begin < span_end
        ]

    def get_specified_items(self) -> list[tuple[Span, dict[str, str]]]:
        result = self.chain(
            self.items_from_markup,
            [
                (span, {key: val})
                for t2x_dict, key in (
                    (self.t2c, "foreground"),
                    (self.t2f, "font_family"),
                    (self.t2s, "font_style"),
                    (self.t2w, "font_weight")
                )
                for selector, val in t2x_dict.items()
                for span in self.find_spans_by_selector(selector)
            ],
            [
                (span, local_config)
                for selector, local_config in self.local_configs.items()
                for span in self.find_spans_by_selector(selector)
            ],
            [
                (span, {})
                for span in self.find_spans_by_selector(self.isolate)
            ]
        )
        entity_spans = self.tag_spans.copy()
        if self.is_markup:
            entity_spans.extend(self.find_spans(r"&[\s\S]*?;"))
        return [
            (span, attr_dict)
            for span, attr_dict in result
            if not any([
                entity_begin < index < entity_end
                for index in span
                for entity_begin, entity_end in entity_spans
            ])
        ]

    def get_command_repl_items(self) -> list[tuple[Span, str]]:
        result = [
            (tag_span, "") for tag_span in self.tag_spans
        ]
        if not self.is_markup:
            result.extend([
                (span, escaped)
                for char, escaped in (
                    ("&", "&amp;"),
                    (">", "&gt;"),
                    ("<", "&lt;")
                )
                for span in self.find_spans(re.escape(char))
            ])
        return result

    def get_specified_spans(self) -> list[Span]:
        return self.remove_redundancies([
            span for span, _ in self.specified_items
        ])

    def get_label_span_list(self) -> list[Span]:
        interval_spans = sorted(self.chain(
            self.tag_spans,
            [
                (index, index)
                for span in self.specified_spans
                for index in span
            ]
        ))
        text_spans = self.get_complement_spans(interval_spans, self.full_span)
        if self.is_markup:
            pattern = r"[0-9a-zA-Z]+|(?:&[\s\S]*?;|[^0-9a-zA-Z\s])+"
        else:
            pattern = r"[0-9a-zA-Z]+|[^0-9a-zA-Z\s]+"
        return self.chain(*[
            self.find_spans(pattern, pos=span_begin, endpos=span_end)
            for span_begin, span_end in text_spans
        ])

    def get_content(self, is_labelled: bool) -> str:
        predefined_items = [
            (self.full_span, self.global_attr_dict),
            (self.full_span, self.global_config),
            *self.specified_items
        ]
        if is_labelled:
            attr_dict_items = self.chain(
                [
                    (span, {
                        key:
                        "black" if key.lower() in MARKUP_COLOR_KEYS else val
                        for key, val in attr_dict.items()
                    })
                    for span, attr_dict in predefined_items
                ],
                [
                    (span, {"foreground": self.int_to_hex(label + 1)})
                    for label, span in enumerate(self.label_span_list)
                ]
            )
        else:
            attr_dict_items = self.chain(
                predefined_items,
                [
                    (span, {})
                    for span in self.label_span_list
                ]
            )
        inserted_string_pairs = [
            (span, (
                f"<span {self.get_attr_dict_str(attr_dict)}>",
                "</span>"
            ))
            for span, attr_dict in attr_dict_items if attr_dict
        ]
        return self.get_replaced_string(
            inserted_string_pairs, self.command_repl_items
        )

    # Selector

    def get_cleaned_substr(self, span: Span) -> str:
        repl_items = list(filter(
            lambda repl_item: self.span_contains(span, repl_item[0]),
            self.command_repl_items
        ))
        return self.get_replaced_substr(span, repl_items).strip()

    # Method alias

    def get_parts_by_text(self, selector: Selector) -> VGroup:
        return self.select_parts(selector)

    def get_part_by_text(self, selector: Selector) -> VGroup:
        return self.select_part(selector)

    def set_color_by_text(self, selector: Selector, color: ManimColor):
        return self.set_parts_color(selector, color)

    def set_color_by_text_to_color_map(
        self, color_map: dict[Selector, ManimColor]
    ):
        return self.set_parts_color_by_dict(color_map)

    def get_text(self) -> str:
        return self.get_string()


class Text(MarkupText):
    CONFIG = {
        "is_markup": False,
    }


class Code(MarkupText):
    CONFIG = {
        "font": "Consolas",
        "font_size": 24,
        "lsh": 1.0,
        "language": "python",
        # Visit https://pygments.org/demo/ to have a preview of more styles.
        "code_style": "monokai",
    }

    def __init__(self, code: str, **kwargs):
        digest_config(self, kwargs)
        self.code = code
        lexer = pygments.lexers.get_lexer_by_name(self.language)
        formatter = pygments.formatters.PangoMarkupFormatter(
            style=self.code_style
        )
        markup = pygments.highlight(code, lexer, formatter)
        markup = re.sub(r"</?tt>", "", markup)
        super().__init__(markup, **kwargs)


@contextmanager
def register_font(font_file: str | Path):
    """Temporarily add a font file to Pango's search path.
    This searches for the font_file at various places. The order it searches it described below.
    1. Absolute path.
    2. Downloads dir.

    Parameters
    ----------
    font_file :
        The font file to add.
    Examples
    --------
    Use ``with register_font(...)`` to add a font file to search
    path.
    .. code-block:: python
        with register_font("path/to/font_file.ttf"):
           a = Text("Hello", font="Custom Font Name")
    Raises
    ------
    FileNotFoundError:
        If the font doesn't exists.
    AttributeError:
        If this method is used on macOS.
    Notes
    -----
    This method of adding font files also works with :class:`CairoText`.
    .. important ::
        This method is available for macOS for ``ManimPango>=v0.2.3``. Using this
        method with previous releases will raise an :class:`AttributeError` on macOS.
    """

    input_folder = Path(get_downloads_dir()).parent.resolve()
    possible_paths = [
        Path(font_file),
        input_folder / font_file,
    ]
    for path in possible_paths:
        path = path.resolve()
        if path.exists():
            file_path = path
            break
    else:
        error = f"Can't find {font_file}." f"Tried these : {possible_paths}"
        raise FileNotFoundError(error)

    try:
        assert manimpango.register_font(str(file_path))
        yield
    finally:
        manimpango.unregister_font(str(file_path))
