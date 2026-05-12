"""
Enhanced DOCX to Markdown converter with LaTeX equation support and image extraction.

This module extends docling's capabilities by:
1. Converting Office Math Markup Language (OMML) equations to LaTeX format
2. Extracting embedded images and linking them in the markdown output

Use this when docling's default DOCX conversion fails on documents with complex
mathematical equations, or when you need images properly extracted and referenced.

Usage:
    from docling_skill.scripts.docx_latex_converter import convert_docx_to_markdown
    
    # Basic conversion
    markdown = convert_docx_to_markdown("document.docx", "output.md")
    
    # With custom image directory
    markdown = convert_docx_to_markdown("document.docx", "output.md", "assets/images")
"""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import re
import os

# XML namespaces used in DOCX
NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
    'v': 'urn:schemas-microsoft-com:vml',
    'o': 'urn:schemas-microsoft-com:office:office',
    'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
}


class OmmlToLatex:
    """Convert Office Math Markup Language (OMML) to LaTeX.
    
    Handles most common OMML elements including:
    - Fractions, radicals (square roots)
    - Superscripts, subscripts
    - Summations, products, integrals (n-ary operators)
    - Matrices and equation arrays
    - Delimiters (parentheses, brackets, braces)
    - Accents (hat, bar, vec, etc.)
    - Greek letters and mathematical symbols
    """
    
    def __init__(self):
        self.handlers = {
            'm:r': self._handle_run,
            'm:t': self._handle_text,
            'm:f': self._handle_fraction,
            'm:rad': self._handle_radical,
            'm:sSup': self._handle_superscript,
            'm:sSub': self._handle_subscript,
            'm:sSubSup': self._handle_subsup,
            'm:nary': self._handle_nary,
            'm:d': self._handle_delimiter,
            'm:func': self._handle_func,
            'm:acc': self._handle_accent,
            'm:bar': self._handle_bar,
            'm:eqArr': self._handle_eqarray,
            'm:m': self._handle_matrix,
            'm:limLow': self._handle_limlow,
            'm:limUpp': self._handle_limupp,
            'm:groupChr': self._handle_groupchr,
            'm:box': self._handle_box,
            'm:borderBox': self._handle_borderbox,
        }
        
        # Greek letters and symbol mappings
        self.greek = {
            'α': r'\alpha', 'β': r'\beta', 'γ': r'\gamma', 'δ': r'\delta',
            'ε': r'\epsilon', 'ζ': r'\zeta', 'η': r'\eta', 'θ': r'\theta',
            'ι': r'\iota', 'κ': r'\kappa', 'λ': r'\lambda', 'μ': r'\mu',
            'ν': r'\nu', 'ξ': r'\xi', 'ο': r'o', 'π': r'\pi',
            'ρ': r'\rho', 'σ': r'\sigma', 'τ': r'\tau', 'υ': r'\upsilon',
            'φ': r'\phi', 'χ': r'\chi', 'ψ': r'\psi', 'ω': r'\omega',
            'Α': r'A', 'Β': r'B', 'Γ': r'\Gamma', 'Δ': r'\Delta',
            'Ε': r'E', 'Ζ': r'Z', 'Η': r'H', 'Θ': r'\Theta',
            'Ι': r'I', 'Κ': r'K', 'Λ': r'\Lambda', 'Μ': r'M',
            'Ν': r'N', 'Ξ': r'\Xi', 'Ο': r'O', 'Π': r'\Pi',
            'Ρ': r'P', 'Σ': r'\Sigma', 'Τ': r'T', 'Υ': r'\Upsilon',
            'Φ': r'\Phi', 'Χ': r'X', 'Ψ': r'\Psi', 'Ω': r'\Omega',
            '∞': r'\infty', '∂': r'\partial', '∇': r'\nabla',
            '∑': r'\sum', '∏': r'\prod', '∫': r'\int',
            '≤': r'\leq', '≥': r'\geq', '≠': r'\neq', '≈': r'\approx',
            '±': r'\pm', '×': r'\times', '÷': r'\div', '·': r'\cdot',
            '→': r'\rightarrow', '←': r'\leftarrow', '↔': r'\leftrightarrow',
            '⇒': r'\Rightarrow', '⇐': r'\Leftarrow', '⇔': r'\Leftrightarrow',
            '∈': r'\in', '∉': r'\notin', '⊂': r'\subset', '⊃': r'\supset',
            '∪': r'\cup', '∩': r'\cap', '∅': r'\emptyset',
            '∀': r'\forall', '∃': r'\exists', '¬': r'\neg',
            '∧': r'\land', '∨': r'\lor',
        }
        
        # Accent mappings
        self.accents = {
            'ˆ': 'hat', '^': 'hat', '~': 'tilde', '˜': 'tilde',
            '¯': 'bar', '-': 'bar', '̅': 'bar',
            '→': 'vec', '⃗': 'vec', '.': 'dot', '..': 'ddot',
            '˙': 'dot', '¨': 'ddot', '˘': 'breve', 'ˇ': 'check',
            '́': 'acute', '̀': 'grave',
        }
    
    def convert(self, elem):
        """Convert an OMML element to LaTeX string.
        
        Args:
            elem: An XML element containing OMML math markup
            
        Returns:
            LaTeX string representation of the math content
        """
        try:
            return self._process_element(elem).strip()
        except Exception as e:
            # Fallback: extract plain text if conversion fails
            return self._extract_text(elem)
    
    def _extract_text(self, elem):
        """Extract plain text from element as fallback."""
        texts = []
        for t in elem.iter('{http://schemas.openxmlformats.org/officeDocument/2006/math}t'):
            if t.text:
                texts.append(t.text)
        return ''.join(texts)
    
    def _process_element(self, elem):
        """Process a single element."""
        tag = elem.tag.replace('{http://schemas.openxmlformats.org/officeDocument/2006/math}', 'm:')
        
        if tag in self.handlers:
            return self.handlers[tag](elem)
        
        return self._process_children(elem)
    
    def _process_children(self, elem):
        """Process all children of an element."""
        result = []
        for child in elem:
            result.append(self._process_element(child))
        return ''.join(result)
    
    def _get_child(self, elem, tag):
        """Get first child with given tag."""
        full_tag = '{http://schemas.openxmlformats.org/officeDocument/2006/math}' + tag
        return elem.find(full_tag)
    
    def _get_children(self, elem, tag):
        """Get all children with given tag."""
        full_tag = '{http://schemas.openxmlformats.org/officeDocument/2006/math}' + tag
        return elem.findall(full_tag)
    
    def _handle_run(self, elem):
        return self._process_children(elem)
    
    def _handle_text(self, elem):
        text = elem.text or ''
        result = []
        for char in text:
            if char in self.greek:
                result.append(self.greek[char] + ' ')
            else:
                result.append(char)
        return ''.join(result)
    
    def _handle_fraction(self, elem):
        num = self._get_child(elem, 'num')
        den = self._get_child(elem, 'den')
        num_latex = self._process_children(num) if num is not None else ''
        den_latex = self._process_children(den) if den is not None else ''
        return r'\frac{' + num_latex + '}{' + den_latex + '}'
    
    def _handle_radical(self, elem):
        deg = self._get_child(elem, 'deg')
        e = self._get_child(elem, 'e')
        e_latex = self._process_children(e) if e is not None else ''
        
        if deg is not None:
            deg_latex = self._process_children(deg).strip()
            if deg_latex and deg_latex != '2':
                return r'\sqrt[' + deg_latex + ']{' + e_latex + '}'
        return r'\sqrt{' + e_latex + '}'
    
    def _handle_superscript(self, elem):
        e = self._get_child(elem, 'e')
        sup = self._get_child(elem, 'sup')
        e_latex = self._process_children(e) if e is not None else ''
        sup_latex = self._process_children(sup) if sup is not None else ''
        
        if len(sup_latex) == 1:
            return e_latex + '^' + sup_latex
        return e_latex + '^{' + sup_latex + '}'
    
    def _handle_subscript(self, elem):
        e = self._get_child(elem, 'e')
        sub = self._get_child(elem, 'sub')
        e_latex = self._process_children(e) if e is not None else ''
        sub_latex = self._process_children(sub) if sub is not None else ''
        
        if len(sub_latex) == 1:
            return e_latex + '_' + sub_latex
        return e_latex + '_{' + sub_latex + '}'
    
    def _handle_subsup(self, elem):
        e = self._get_child(elem, 'e')
        sub = self._get_child(elem, 'sub')
        sup = self._get_child(elem, 'sup')
        e_latex = self._process_children(e) if e is not None else ''
        sub_latex = self._process_children(sub) if sub is not None else ''
        sup_latex = self._process_children(sup) if sup is not None else ''
        return e_latex + '_{' + sub_latex + '}^{' + sup_latex + '}'
    
    def _handle_nary(self, elem):
        """Handle n-ary operators: sum, product, integral."""
        naryPr = self._get_child(elem, 'naryPr')
        sub = self._get_child(elem, 'sub')
        sup = self._get_child(elem, 'sup')
        e = self._get_child(elem, 'e')
        
        op = r'\int'
        if naryPr is not None:
            chr_elem = naryPr.find('{http://schemas.openxmlformats.org/officeDocument/2006/math}chr')
            if chr_elem is not None:
                val = chr_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val', '')
                if val in ('∑', 'Σ'):
                    op = r'\sum'
                elif val in ('∏', 'Π'):
                    op = r'\prod'
                elif val == '∫':
                    op = r'\int'
                elif val == '∬':
                    op = r'\iint'
                elif val == '∮':
                    op = r'\oint'
        
        sub_latex = self._process_children(sub) if sub is not None else ''
        sup_latex = self._process_children(sup) if sup is not None else ''
        e_latex = self._process_children(e) if e is not None else ''
        
        result = op
        if sub_latex:
            result += '_{' + sub_latex + '}'
        if sup_latex:
            result += '^{' + sup_latex + '}'
        result += ' ' + e_latex
        
        return result
    
    def _handle_delimiter(self, elem):
        """Handle delimiters: parentheses, brackets, braces."""
        dPr = self._get_child(elem, 'dPr')
        
        beg_chr, end_chr = '(', ')'
        
        if dPr is not None:
            beg = dPr.find('{http://schemas.openxmlformats.org/officeDocument/2006/math}begChr')
            end = dPr.find('{http://schemas.openxmlformats.org/officeDocument/2006/math}endChr')
            if beg is not None:
                beg_chr = beg.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val', '(')
            if end is not None:
                end_chr = end.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val', ')')
        
        delim_map = {
            '(': '(', ')': ')', '[': '[', ']': ']',
            '{': r'\{', '}': r'\}', '|': '|', '‖': r'\|',
            '⌈': r'\lceil', '⌉': r'\rceil',
            '⌊': r'\lfloor', '⌋': r'\rfloor',
            '〈': r'\langle', '〉': r'\rangle',
            '': '.', ' ': '.',
        }
        
        beg_latex = delim_map.get(beg_chr, beg_chr)
        end_latex = delim_map.get(end_chr, end_chr)
        
        e_elems = self._get_children(elem, 'e')
        contents = [self._process_children(e) for e in e_elems]
        content = ', '.join(contents) if len(contents) > 1 else (contents[0] if contents else '')
        
        return r'\left' + beg_latex + ' ' + content + r' \right' + end_latex
    
    def _handle_func(self, elem):
        """Handle functions: sin, cos, log, etc."""
        fName = self._get_child(elem, 'fName')
        e = self._get_child(elem, 'e')
        
        func_name = self._process_children(fName) if fName is not None else ''
        e_latex = self._process_children(e) if e is not None else ''
        
        func_map = {
            'sin': r'\sin', 'cos': r'\cos', 'tan': r'\tan',
            'sec': r'\sec', 'csc': r'\csc', 'cot': r'\cot',
            'sinh': r'\sinh', 'cosh': r'\cosh', 'tanh': r'\tanh',
            'log': r'\log', 'ln': r'\ln', 'lg': r'\lg',
            'exp': r'\exp', 'lim': r'\lim', 'max': r'\max', 'min': r'\min',
            'arg': r'\arg', 'det': r'\det', 'dim': r'\dim',
            'gcd': r'\gcd', 'hom': r'\hom', 'inf': r'\inf', 'sup': r'\sup',
            'ker': r'\ker', 'deg': r'\deg', 'Pr': r'\Pr',
        }
        
        func_name_clean = func_name.strip()
        latex_func = func_map.get(func_name_clean, r'\mathrm{' + func_name_clean + '}')
        
        return latex_func + ' ' + e_latex
    
    def _handle_accent(self, elem):
        accPr = self._get_child(elem, 'accPr')
        e = self._get_child(elem, 'e')
        e_latex = self._process_children(e) if e is not None else ''
        
        accent = 'hat'
        if accPr is not None:
            chr_elem = accPr.find('{http://schemas.openxmlformats.org/officeDocument/2006/math}chr')
            if chr_elem is not None:
                val = chr_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val', '^')
                accent = self.accents.get(val, 'hat')
        
        return '\\' + accent + '{' + e_latex + '}'
    
    def _handle_bar(self, elem):
        e = self._get_child(elem, 'e')
        e_latex = self._process_children(e) if e is not None else ''
        return r'\overline{' + e_latex + '}'
    
    def _handle_eqarray(self, elem):
        rows = self._get_children(elem, 'e')
        row_latex = [self._process_children(row) for row in rows]
        return r'\begin{aligned} ' + r' \\ '.join(row_latex) + r' \end{aligned}'
    
    def _handle_matrix(self, elem):
        rows = self._get_children(elem, 'mr')
        row_latex = []
        for row in rows:
            cells = self._get_children(row, 'e')
            cell_latex = [self._process_children(c) for c in cells]
            row_latex.append(' & '.join(cell_latex))
        return r'\begin{matrix} ' + r' \\ '.join(row_latex) + r' \end{matrix}'
    
    def _handle_limlow(self, elem):
        e = self._get_child(elem, 'e')
        lim = self._get_child(elem, 'lim')
        e_latex = self._process_children(e) if e is not None else ''
        lim_latex = self._process_children(lim) if lim is not None else ''
        return e_latex + '_{' + lim_latex + '}'
    
    def _handle_limupp(self, elem):
        e = self._get_child(elem, 'e')
        lim = self._get_child(elem, 'lim')
        e_latex = self._process_children(e) if e is not None else ''
        lim_latex = self._process_children(lim) if lim is not None else ''
        return e_latex + '^{' + lim_latex + '}'
    
    def _handle_groupchr(self, elem):
        """Handle underbrace/overbrace."""
        groupChrPr = self._get_child(elem, 'groupChrPr')
        e = self._get_child(elem, 'e')
        e_latex = self._process_children(e) if e is not None else ''
        
        chr_val = '⏟'
        pos = 'bot'
        if groupChrPr is not None:
            chr_elem = groupChrPr.find('{http://schemas.openxmlformats.org/officeDocument/2006/math}chr')
            pos_elem = groupChrPr.find('{http://schemas.openxmlformats.org/officeDocument/2006/math}pos')
            if chr_elem is not None:
                chr_val = chr_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val', '⏟')
            if pos_elem is not None:
                pos = pos_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val', 'bot')
        
        if chr_val in ('⏟', '︸') or pos == 'bot':
            return r'\underbrace{' + e_latex + '}'
        return r'\overbrace{' + e_latex + '}'
    
    def _handle_box(self, elem):
        e = self._get_child(elem, 'e')
        return self._process_children(e) if e is not None else ''
    
    def _handle_borderbox(self, elem):
        e = self._get_child(elem, 'e')
        e_latex = self._process_children(e) if e is not None else ''
        return r'\boxed{' + e_latex + '}'


class DocxToMarkdown:
    """Convert DOCX to Markdown with LaTeX equation support and image extraction.
    
    This class provides enhanced DOCX conversion that:
    1. Converts OMML equations to LaTeX (inline $...$ and display $$...$$)
    2. Extracts embedded images to a specified directory
    3. Preserves document structure (headings, tables, paragraphs)
    
    Args:
        docx_path: Path to the input DOCX file
        image_dir: Directory to extract images to (default: 'images' in same dir as output)
    """
    
    def __init__(self, docx_path, image_dir=None):
        self.docx_path = Path(docx_path)
        self.omml_converter = OmmlToLatex()
        self.image_dir = Path(image_dir) if image_dir else self.docx_path.parent / 'images'
        self.relationships = {}
        self.image_counter = 0
        self.extracted_images = {}
        
    def convert(self):
        """Convert DOCX to Markdown string.
        
        Returns:
            Markdown content as string with LaTeX equations and image references
        """
        with zipfile.ZipFile(self.docx_path, 'r') as zf:
            self._load_relationships(zf)
            self._extract_images(zf)
            doc_xml = zf.read('word/document.xml')
        
        root = ET.fromstring(doc_xml)
        body = root.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body')
        
        if body is None:
            return ''
        
        md_parts = []
        
        for elem in body:
            tag = elem.tag.split('}')[-1]
            
            if tag == 'p':
                para_md = self._process_paragraph(elem)
                md_parts.append(para_md)
            elif tag == 'tbl':
                table_md = self._process_table(elem)
                md_parts.append('')
                md_parts.append(table_md)
                md_parts.append('')
            elif tag == 'sectPr':
                pass
            else:
                text = self._extract_text(elem)
                if text.strip():
                    md_parts.append(text)
        
        return '\n'.join(md_parts)
    
    def _load_relationships(self, zf):
        """Load document relationships to map rId to file paths."""
        try:
            rels_xml = zf.read('word/_rels/document.xml.rels')
            root = ET.fromstring(rels_xml)
            
            for rel in root:
                rel_id = rel.get('Id', '')
                target = rel.get('Target', '')
                rel_type = rel.get('Type', '')
                
                if 'image' in rel_type.lower() or target.startswith('media/'):
                    self.relationships[rel_id] = target
        except KeyError:
            pass
    
    def _extract_images(self, zf):
        """Extract all images from the DOCX to the image directory."""
        self.image_dir.mkdir(parents=True, exist_ok=True)
        
        for name in zf.namelist():
            if name.startswith('word/media/'):
                orig_name = Path(name).name
                target_path = self.image_dir / orig_name
                
                with zf.open(name) as src:
                    with open(target_path, 'wb') as dst:
                        dst.write(src.read())
                
                media_path = name.replace('word/', '')
                self.extracted_images[media_path] = f'images/{orig_name}'
        
        for rel_id, target in self.relationships.items():
            if target in self.extracted_images:
                self.extracted_images[rel_id] = self.extracted_images[target]
            elif target.startswith('media/'):
                orig_name = Path(target).name
                self.extracted_images[rel_id] = f'images/{orig_name}'
    
    def _process_paragraph(self, para_elem):
        """Process a paragraph element."""
        pPr = para_elem.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pPr')
        heading_level = 0
        
        if pPr is not None:
            pStyle = pPr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pStyle')
            if pStyle is not None:
                style_val = pStyle.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '')
                if style_val.startswith('Heading'):
                    try:
                        heading_level = int(style_val.replace('Heading', ''))
                    except ValueError:
                        pass
        
        content_parts = []
        for child in para_elem:
            tag = child.tag.split('}')[-1]
            
            if tag == 'r':
                run_text = self._process_run(child)
                content_parts.append(run_text)
            elif tag == 'oMathPara' or tag == 'oMath':
                latex = self.omml_converter.convert(child)
                if latex.strip():
                    if tag == 'oMathPara':
                        content_parts.append('\n$$\n' + latex + '\n$$\n')
                    else:
                        content_parts.append('$' + latex + '$')
            elif tag == 'hyperlink':
                link_text = self._extract_text(child)
                content_parts.append(link_text)
            elif tag not in ('bookmarkStart', 'bookmarkEnd', 'pPr'):
                text = self._extract_text(child)
                content_parts.append(text)
        
        content = ''.join(content_parts).strip()
        
        if heading_level > 0 and content:
            content = '#' * heading_level + ' ' + content
        
        return content
    
    def _process_run(self, run_elem):
        """Process a run element."""
        parts = []
        
        for child in run_elem:
            tag = child.tag.split('}')[-1]
            
            if tag == 't':
                parts.append(child.text or '')
            elif tag == 'tab':
                parts.append('\t')
            elif tag == 'br':
                parts.append('\n')
            elif tag == 'rPr':
                pass
            elif tag == 'drawing':
                img_md = self._process_drawing(child)
                parts.append(img_md)
            elif tag in ('pict', 'object'):
                img_md = self._process_vml_picture(child)
                parts.append(img_md)
            elif 'oMath' in child.tag:
                latex = self.omml_converter.convert(child)
                if latex.strip():
                    parts.append('$' + latex + '$')
        
        return ''.join(parts)
    
    def _process_drawing(self, drawing_elem):
        """Process a drawing element to extract image reference."""
        blip = None
        for blip_elem in drawing_elem.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}blip'):
            blip = blip_elem
            break
        
        if blip is None:
            for blip_elem in drawing_elem.iter('{http://purl.oclc.org/ooxml/drawingml/main}blip'):
                blip = blip_elem
                break
        
        if blip is not None:
            embed_id = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed', '')
            if not embed_id:
                embed_id = blip.get('{http://purl.oclc.org/ooxml/officeDocument/relationships}embed', '')
            
            if embed_id and embed_id in self.extracted_images:
                img_path = self.extracted_images[embed_id]
                self.image_counter += 1
                desc = self._get_image_description(drawing_elem)
                if desc:
                    return f'\n\n![{desc}]({img_path})\n\n'
                return f'\n\n![Image {self.image_counter}]({img_path})\n\n'
        
        self.image_counter += 1
        return f'[Image {self.image_counter}]'
    
    def _process_vml_picture(self, pict_elem):
        """Process VML picture element (legacy format)."""
        for imagedata in pict_elem.iter('{urn:schemas-microsoft-com:vml}imagedata'):
            rel_id = imagedata.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id', '')
            if not rel_id:
                rel_id = imagedata.get('{urn:schemas-microsoft-com:office:office}relid', '')
            
            if rel_id and rel_id in self.extracted_images:
                img_path = self.extracted_images[rel_id]
                self.image_counter += 1
                return f'\n\n![Image {self.image_counter}]({img_path})\n\n'
        
        for shape in pict_elem.iter('{urn:schemas-microsoft-com:vml}shape'):
            for imagedata in shape.iter('{urn:schemas-microsoft-com:vml}imagedata'):
                rel_id = imagedata.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id', '')
                if rel_id and rel_id in self.extracted_images:
                    img_path = self.extracted_images[rel_id]
                    self.image_counter += 1
                    return f'\n\n![Image {self.image_counter}]({img_path})\n\n'
        
        for ole in pict_elem.iter('{urn:schemas-microsoft-com:office:office}OLEObject'):
            rel_id = ole.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id', '')
            if rel_id and rel_id in self.extracted_images:
                img_path = self.extracted_images[rel_id]
                self.image_counter += 1
                return f'\n\n![Image {self.image_counter}]({img_path})\n\n'
        
        self.image_counter += 1
        return f'[Image {self.image_counter}]'
    
    def _get_image_description(self, drawing_elem):
        """Try to extract image description/alt text."""
        for docPr in drawing_elem.iter('{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr'):
            desc = docPr.get('descr', '')
            if desc:
                return desc
            name = docPr.get('name', '')
            if name:
                return name
        return ''
    
    def _process_table(self, table_elem):
        """Process a table element."""
        rows = table_elem.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr')
        
        if not rows:
            return ''
        
        md_rows = []
        
        for i, row in enumerate(rows):
            cells = row.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc')
            cell_texts = []
            
            for cell in cells:
                cell_content = []
                for para in cell.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                    para_text = self._process_paragraph(para)
                    cell_content.append(para_text)
                cell_text = ' '.join(cell_content).replace('\n', ' ').strip()
                cell_texts.append(cell_text)
            
            md_rows.append('| ' + ' | '.join(cell_texts) + ' |')
            
            if i == 0:
                md_rows.append('|' + '|'.join(['---' for _ in cell_texts]) + '|')
        
        return '\n'.join(md_rows)
    
    def _extract_text(self, elem):
        """Extract all text from an element."""
        texts = []
        for t in elem.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
            if t.text:
                texts.append(t.text)
        return ''.join(texts)


def convert_docx_to_markdown(input_path, output_path=None, image_dir=None):
    """Convert a DOCX file to Markdown with LaTeX equations and images.
    
    This function provides an enhanced alternative to docling's default DOCX
    conversion, specifically handling:
    - OMML equations converted to LaTeX format
    - Embedded images extracted and properly referenced
    
    Args:
        input_path: Path to the input DOCX file
        output_path: Path for the output markdown file (optional)
        image_dir: Directory to extract images to (optional)
    
    Returns:
        The markdown content as a string
        
    Example:
        >>> markdown = convert_docx_to_markdown("report.docx", "report.md")
        >>> # Images will be in ./images/ directory
        >>> # Equations will be in LaTeX format: $inline$ or $$display$$
    """
    input_path = Path(input_path)
    
    if output_path:
        output_path = Path(output_path)
        if image_dir is None:
            image_dir = output_path.parent / 'images'
    else:
        if image_dir is None:
            image_dir = input_path.parent / 'images'
    
    converter = DocxToMarkdown(input_path, image_dir)
    markdown = converter.convert()
    
    if output_path:
        Path(output_path).write_text(markdown, encoding='utf-8')
        print(f"Converted: {input_path} -> {output_path}")
        print(f"Output size: {len(markdown)} characters")
        print(f"Images extracted to: {image_dir}")
        print(f"Total images: {converter.image_counter}")
    
    return markdown


# Convenience function for quick conversion
def convert_with_latex(source, output_format="markdown"):
    """Quick conversion wrapper compatible with docling's API style.
    
    Args:
        source: Path to DOCX file
        output_format: Output format (only "markdown" supported currently)
    
    Returns:
        Markdown string with LaTeX equations
    """
    if output_format != "markdown":
        raise ValueError("Only 'markdown' output format is supported")
    
    return convert_docx_to_markdown(source)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python docx_latex_converter.py <input.docx> [output.md] [image_dir]")
        print("\nConverts DOCX to Markdown with LaTeX equations and image extraction.")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.docx', '.md')
    image_dir = sys.argv[3] if len(sys.argv) > 3 else None
    
    convert_docx_to_markdown(input_file, output_file, image_dir)
