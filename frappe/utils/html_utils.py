import json
import re

from bleach_allowlist import bleach_allowlist

import frappe


def clean_html(html):
	import bleach

	if not isinstance(html, str):
		return html

	return bleach.clean(clean_script_and_style(html),
		tags=['div', 'p', 'br', 'ul', 'ol', 'li', 'strong', 'b', 'em', 'i', 'u',
			'table', 'thead', 'tbody', 'td', 'tr'],
		attributes=[],
		styles=['color', 'border', 'border-color'],
		strip=True, strip_comments=True)

def clean_email_html(html):
	import bleach

	if not isinstance(html, str):
		return html

	return bleach.clean(clean_script_and_style(html),
		tags=['div', 'p', 'br', 'ul', 'ol', 'li', 'strong', 'b', 'em', 'i', 'u', 'a',
			'table', 'thead', 'tbody', 'td', 'tr', 'th', 'pre', 'code',
			'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'button', 'img'],
		attributes=['border', 'colspan', 'rowspan',
			'src', 'href', 'style', 'id'],
		styles=['color', 'border-color', 'width', 'height', 'max-width',
			'background-color', 'border-collapse', 'border-radius',
			'border', 'border-top', 'border-bottom', 'border-left', 'border-right',
			'margin', 'margin-top', 'margin-bottom', 'margin-left', 'margin-right',
			'padding', 'padding-top', 'padding-bottom', 'padding-left', 'padding-right',
			'font-size', 'font-weight', 'font-family', 'text-decoration',
			'line-height', 'text-align', 'vertical-align', 'display'
		],
		protocols=['cid', 'http', 'https', 'mailto', 'data'],
		strip=True, strip_comments=True)

def clean_script_and_style(html):
	# remove script and style
	from bs4 import BeautifulSoup

	soup = BeautifulSoup(html, 'html5lib')
	for s in soup(['script', 'style']):
		s.decompose()
	return frappe.as_unicode(soup)

def sanitize_html(html, linkify=False):
	"""
	Sanitize HTML tags, attributes and style to prevent XSS attacks
	Based on bleach clean, bleach whitelist and html5lib's Sanitizer defaults

	Does not sanitize JSON, as it could lead to future problems
	"""
	import bleach
	from bs4 import BeautifulSoup
	import re

	if not isinstance(html, str):
		return html

	elif is_json(html):
		return html

	# regex for finding unicode characters like %3E, %3c
	regex = re.compile(r"%[0-9]?[a-zA-Z]?")
	char_list = regex.findall(html)

	if not bool(BeautifulSoup(html, 'html.parser').find()) \
		and not bool(char_list) and (u"<" not in html and u">" not in html):
		return html

	html = strip_encoded_chars(html, char_list) if bool(char_list) else html

	tags = (acceptable_elements + svg_elements + mathml_elements
		+ ["html", "head", "meta", "link", "body", "style", "o:p"])
	attributes = {"*": acceptable_attributes, 'svg': svg_attributes}
	styles = bleach_allowlist.all_styles
	strip_comments = False

	# returns html with escaped tags, escaped orphan >, <, etc.
	escaped_html = bleach.clean(html, tags=tags, attributes=attributes, styles=styles,
		strip_comments=strip_comments, strip=True, protocols=['cid', 'http', 'https', 'mailto'])

	return escaped_html

def is_json(text):
	try:
		json.loads(text)
	except ValueError:
		return False
	else:
		return True

def get_icon_html(icon, small=False):
	from frappe.utils import is_image

	emoji_pattern = re.compile(
		u"(\ud83d[\ude00-\ude4f])|"
		u"(\ud83c[\udf00-\uffff])|"
		u"(\ud83d[\u0000-\uddff])|"
		u"(\ud83d[\ude80-\udeff])|"
		u"(\ud83c[\udde0-\uddff])"
		"+", flags=re.UNICODE)

	icon = icon or ""
	if icon and emoji_pattern.match(icon):
		return '<span class="text-muted">' + icon + '</span>'

	if is_image(icon):
		return \
			'<img style="width: 16px; height: 16px;" src="{icon}">'.format(icon=icon) \
				if small else \
			'<img src="{icon}">'.format(icon=icon)
	else:
		return "<i class='{icon}'></i>".format(icon=icon)

def unescape_html(value):
	from html import unescape
	return unescape(value)

def strip_encoded_chars(html, char_list):
	for d in char_list:
		html = html.replace(d, '')
	return html

# adapted from https://raw.githubusercontent.com/html5lib/html5lib-python/4aa79f113e7486c7ec5d15a6e1777bfe546d3259/html5lib/sanitizer.py
acceptable_elements = [
	'a', 'abbr', 'acronym', 'address', 'area',
	'article', 'aside', 'audio', 'b', 'big', 'blockquote', 'br', 'button',
	'canvas', 'caption', 'center', 'cite', 'code', 'col', 'colgroup',
	'command', 'datagrid', 'datalist', 'dd', 'del', 'details', 'dfn',
	'dialog', 'dir', 'div', 'dl', 'dt', 'em', 'event-source', 'fieldset',
	'figcaption', 'figure', 'footer', 'font', 'form', 'header', 'h1',
	'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'input', 'ins',
	'keygen', 'kbd', 'label', 'legend', 'li', 'm', 'map', 'menu', 'meter',
	'multicol', 'nav', 'nextid', 'ol', 'output', 'optgroup', 'option',
	'p', 'pre', 'progress', 'q', 's', 'samp', 'section', 'select',
	'small', 'sound', 'source', 'spacer', 'span', 'strike', 'strong',
	'sub', 'sup', 'table', 'tbody', 'td', 'textarea', 'time', 'tfoot',
	'th', 'thead', 'tr', 'tt', 'u', 'ul', 'var', 'video'
]

mathml_elements = [
	'maction', 'math', 'merror', 'mfrac', 'mi',
	'mmultiscripts', 'mn', 'mo', 'mover', 'mpadded', 'mphantom',
	'mprescripts', 'mroot', 'mrow', 'mspace', 'msqrt', 'mstyle', 'msub',
	'msubsup', 'msup', 'mtable', 'mtd', 'mtext', 'mtr', 'munder',
	'munderover', 'none'
]

svg_elements = [
	'a', 'animate', 'animateColor', 'animateMotion',
	'animateTransform', 'clipPath', 'circle', 'defs', 'desc', 'ellipse',
	'font-face', 'font-face-name', 'font-face-src', 'g', 'glyph', 'hkern',
	'linearGradient', 'line', 'marker', 'metadata', 'missing-glyph',
	'mpath', 'path', 'polygon', 'polyline', 'radialGradient', 'rect',
	'set', 'stop', 'svg', 'switch', 'text', 'title', 'tspan', 'use'
]

acceptable_attributes = [
	'abbr', 'accept', 'accept-charset', 'accesskey',
	'action', 'align', 'alt', 'autocomplete', 'autofocus', 'axis',
	'background', 'balance', 'bgcolor', 'bgproperties', 'border',
	'bordercolor', 'bordercolordark', 'bordercolorlight', 'bottompadding',
	'cellpadding', 'cellspacing', 'ch', 'challenge', 'char', 'charoff',
	'choff', 'charset', 'checked', 'cite', 'class', 'clear', 'color',
	'cols', 'colspan', 'compact', 'contenteditable', 'controls', 'coords',
	'data', 'datafld', 'datapagesize', 'datasrc', 'datetime', 'default',
	'delay', 'dir', 'disabled', 'draggable', 'dynsrc', 'enctype', 'end',
	'face', 'for', 'form', 'frame', 'galleryimg', 'gutter', 'headers',
	'height', 'hidefocus', 'hidden', 'high', 'href', 'hreflang', 'hspace',
	'icon', 'id', 'inputmode', 'ismap', 'keytype', 'label', 'leftspacing',
	'lang', 'list', 'longdesc', 'loop', 'loopcount', 'loopend',
	'loopstart', 'low', 'lowsrc', 'max', 'maxlength', 'media', 'method',
	'min', 'multiple', 'name', 'nohref', 'noshade', 'nowrap', 'open',
	'optimum', 'pattern', 'ping', 'point-size', 'poster', 'pqg', 'preload',
	'prompt', 'radiogroup', 'readonly', 'rel', 'repeat-max', 'repeat-min',
	'replace', 'required', 'rev', 'rightspacing', 'rows', 'rowspan',
	'rules', 'scope', 'selected', 'shape', 'size', 'span', 'src', 'start',
	'step', 'style', 'summary', 'suppress', 'tabindex', 'target',
	'template', 'title', 'toppadding', 'type', 'unselectable', 'usemap',
	'urn', 'valign', 'value', 'variable', 'volume', 'vspace', 'vrml',
	'width', 'wrap', 'xml:lang', 'data-row', 'data-list', 'data-language',
	'data-value', 'role', 'frameborder', 'allowfullscreen', 'spellcheck',
	'data-mode', 'data-gramm', 'data-placeholder', 'data-comment',
	'data-id', 'data-denotation-char', 'itemprop', 'itemscope',
	'itemtype', 'itemid', 'itemref', 'datetime', 'data-is-group'
]

mathml_attributes = [
	'actiontype', 'align', 'columnalign', 'columnalign',
	'columnalign', 'columnlines', 'columnspacing', 'columnspan', 'depth',
	'display', 'displaystyle', 'equalcolumns', 'equalrows', 'fence',
	'fontstyle', 'fontweight', 'frame', 'height', 'linethickness', 'lspace',
	'mathbackground', 'mathcolor', 'mathvariant', 'mathvariant', 'maxsize',
	'minsize', 'other', 'rowalign', 'rowalign', 'rowalign', 'rowlines',
	'rowspacing', 'rowspan', 'rspace', 'scriptlevel', 'selection',
	'separator', 'stretchy', 'width', 'width', 'xlink:href', 'xlink:show',
	'xlink:type', 'xmlns', 'xmlns:xlink'
]

svg_attributes = [
	'accent-height', 'accumulate', 'additive', 'alphabetic',
	'arabic-form', 'ascent', 'attributeName', 'attributeType',
	'baseProfile', 'bbox', 'begin', 'by', 'calcMode', 'cap-height',
	'class', 'clip-path', 'color', 'color-rendering', 'content', 'cx',
	'cy', 'd', 'dx', 'dy', 'descent', 'display', 'dur', 'end', 'fill',
	'fill-opacity', 'fill-rule', 'font-family', 'font-size',
	'font-stretch', 'font-style', 'font-variant', 'font-weight', 'from',
	'fx', 'fy', 'g1', 'g2', 'glyph-name', 'gradientUnits', 'hanging',
	'height', 'horiz-adv-x', 'horiz-origin-x', 'id', 'ideographic', 'k',
	'keyPoints', 'keySplines', 'keyTimes', 'lang', 'marker-end',
	'marker-mid', 'marker-start', 'markerHeight', 'markerUnits',
	'markerWidth', 'mathematical', 'max', 'min', 'name', 'offset',
	'opacity', 'orient', 'origin', 'overline-position',
	'overline-thickness', 'panose-1', 'path', 'pathLength', 'points',
	'preserveAspectRatio', 'r', 'refX', 'refY', 'repeatCount',
	'repeatDur', 'requiredExtensions', 'requiredFeatures', 'restart',
	'rotate', 'rx', 'ry', 'slope', 'stemh', 'stemv', 'stop-color',
	'stop-opacity', 'strikethrough-position', 'strikethrough-thickness',
	'stroke', 'stroke-dasharray', 'stroke-dashoffset', 'stroke-linecap',
	'stroke-linejoin', 'stroke-miterlimit', 'stroke-opacity',
	'stroke-width', 'systemLanguage', 'target', 'text-anchor', 'to',
	'transform', 'type', 'u1', 'u2', 'underline-position',
	'underline-thickness', 'unicode', 'unicode-range', 'units-per-em',
	'values', 'version', 'viewBox', 'visibility', 'width', 'widths', 'x',
	'x-height', 'x1', 'x2', 'xlink:actuate', 'xlink:arcrole',
	'xlink:href', 'xlink:role', 'xlink:show', 'xlink:title', 'xlink:type',
	'xml:base', 'xml:lang', 'xml:space', 'xmlns', 'xmlns:xlink', 'y',
	'y1', 'y2', 'zoomAndPan'
]
