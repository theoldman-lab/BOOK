#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LaTeX 数学公式转纯文本工具
用于将 Markdown 文档中的 LaTeX 数学公式（$和$$包裹）转换为纯文本形式
"""

import re
import sys
from typing import Dict, Callable


class LaTeXToTextConverter:
    """LaTeX 公式到纯文本的转换器"""
    
    # 上标字符映射
    SUPERSCRIPT_MAP = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
        'a': 'ᵃ', 'b': 'ᵇ', 'c': 'ᶜ', 'd': 'ᵈ', 'e': 'ᵉ',
        'f': 'ᶠ', 'g': 'ᵍ', 'h': 'ʰ', 'i': 'ⁱ', 'j': 'ʲ',
        'k': 'ᵏ', 'l': 'ˡ', 'm': 'ᵐ', 'n': 'ⁿ', 'o': 'ᵒ',
        'p': 'ᵖ', 'q': 'q', 'r': 'ʳ', 's': 'ˢ', 't': 'ᵗ',
        'u': 'ᵘ', 'v': 'ᵛ', 'w': 'ʷ', 'x': 'ˣ', 'y': 'ʸ', 'z': 'ᶻ',
        '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾',
    }
    
    # 下标字符映射
    SUBSCRIPT_MAP = {
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
        '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
        'a': 'ₐ', 'b': 'բ', 'c': '꜀', 'd': 'ᑯ', 'e': 'ₑ',
        'f': 'ᶟ', 'g': 'g', 'h': 'ₕ', 'i': 'ᵢ', 'j': 'ⱼ',
        'k': 'ₖ', 'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ', 'o': 'ₒ',
        'p': 'ₚ', 'q': 'q', 'r': 'ᵣ', 's': 'ₛ', 't': 'ₜ',
        'u': 'ᵤ', 'v': 'ᵥ', 'w': 'w', 'x': 'ₓ', 'y': 'y', 'z': 'z',
        '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎',
    }
    
    # 希腊字母映射
    GREEK_LETTERS = {
        r'\alpha': 'α', r'\beta': 'β', r'\gamma': 'γ', r'\delta': 'δ',
        r'\epsilon': 'ε', r'\zeta': 'ζ', r'\eta': 'η', r'\theta': 'θ',
        r'\iota': 'ι', r'\kappa': 'κ', r'\lambda': 'λ', r'\mu': 'μ',
        r'\nu': 'ν', r'\xi': 'ξ', r'\pi': 'π', r'\rho': 'ρ',
        r'\sigma': 'σ', r'\tau': 'τ', r'\upsilon': 'υ', r'\phi': 'φ',
        r'\chi': 'χ', r'\psi': 'ψ', r'\omega': 'ω',
        r'\Gamma': 'Γ', r'\Delta': 'Δ', r'\Theta': 'Θ', r'\Lambda': 'Λ',
        r'\Xi': 'Ξ', r'\Pi': 'Π', r'\Sigma': 'Σ', r'\Phi': 'Φ',
        r'\Psi': 'Ψ', r'\Omega': 'Ω',
    }
    
    # 数学函数映射
    MATH_FUNCTIONS = [
        r'\sin', r'\cos', r'\tan', r'\cot', r'\sec', r'\csc',
        r'\arcsin', r'\arccos', r'\arctan',
        r'\sinh', r'\cosh', r'\tanh',
        r'\log', r'\ln', r'\lg', r'\lb',
        r'\exp', r'\lim', r'\sup', r'\inf',
        r'\max', r'\min', r'\dim', r'\ker',
        r'\det', r'\hom', r'\arg', r'\Re', r'\Im',
    ]
    
    FUNCTION_NAMES = {
        r'\sin': 'sin', r'\cos': 'cos', r'\tan': 'tan',
        r'\cot': 'cot', r'\sec': 'sec', r'\csc': 'csc',
        r'\arcsin': 'arcsin', r'\arccos': 'arccos', r'\arctan': 'arctan',
        r'\sinh': 'sinh', r'\cosh': 'cosh', r'\tanh': 'tanh',
        r'\log': 'log', r'\ln': 'ln', r'\lg': 'lg', r'\lb': 'lb',
        r'\exp': 'exp', r'\lim': 'lim', r'\sup': 'sup', r'\inf': 'inf',
        r'\max': 'max', r'\min': 'min', r'\dim': 'dim', r'\ker': 'ker',
        r'\det': 'det', r'\hom': 'hom', r'\arg': 'arg', r'\Re': 'Re', r'\Im': 'Im',
    }
    
    def __init__(self):
        self.replacements = []
        self._setup_replacements()
    
    def _setup_replacements(self):
        """设置替换规则"""
        # 按照处理顺序添加替换规则
        # 1. 首先处理复杂结构
        self.replacements.append((self._convert_frac, "分数转换"))
        self.replacements.append((self._convert_sqrt, "根式转换"))
        self.replacements.append((self._convert_superscript, "上标转换"))
        self.replacements.append((self._convert_subscript, "下标转换"))
        
        # 2. 然后处理特殊符号（必须在希腊字母之前，避免 \in 被误处理）
        self.replacements.append((self._convert_special_symbols, "特殊符号转换"))
        
        # 3. 然后处理希腊字母和函数
        self.replacements.append((self._convert_greek, "希腊字母转换"))
        self.replacements.append((self._convert_functions, "数学函数转换"))
        
        # 4. 最后清理
        self.replacements.append((self._cleanup, "清理"))
    
    def _convert_frac(self, text: str) -> str:
        """转换分数 \\frac{a}{b} 为 a/b 形式"""
        # 处理嵌套的 frac
        prev_text = None
        while prev_text != text:
            prev_text = text
            # 匹配 \frac{...}{...}
            text = re.sub(
                r'\\frac\{([^{}]*)\}\{([^{}]*)\}',
                lambda m: f"{self._convert_formula(m.group(1))}/{self._convert_formula(m.group(2))}",
                text
            )
        return text
    
    def _convert_sqrt(self, text: str) -> str:
        """转换根式 \\sqrt[n]{x} 为 ⁿ√x 或 √x 形式"""
        prev_text = None
        while prev_text != text:
            prev_text = text
            # 处理 \sqrt[n]{x}
            text = re.sub(
                r'\\sqrt\[([^\]]+)\]\{([^{}]*)\}',
                lambda m: f"{self._to_superscript(m.group(1))}√({self._convert_formula(m.group(2))})",
                text
            )
            # 处理 \sqrt{x}
            text = re.sub(
                r'\\sqrt\{([^{}]*)\}',
                lambda m: f"√({self._convert_formula(m.group(1))})",
                text
            )
        return text
    
    def _convert_superscript(self, text: str) -> str:
        """转换上标 x^{n} 或 x^n 为 xⁿ 形式"""
        prev_text = None
        while prev_text != text:
            prev_text = text
            # 处理 x^{...} 形式
            text = re.sub(
                r'\^\{([^{}]+)\}',
                lambda m: self._to_superscript(m.group(1)),
                text
            )
            # 处理 x^n 形式（单个字符或数字）
            text = re.sub(
                r'\^([0-9a-zA-Z])',
                lambda m: self._to_superscript(m.group(1)),
                text
            )
        return text
    
    def _convert_subscript(self, text: str) -> str:
        """转换下标 x_{n} 或 x_n 为 xₙ 形式"""
        prev_text = None
        while prev_text != text:
            prev_text = text
            # 处理 x_{...} 形式
            text = re.sub(
                r'_\{([^{}]+)\}',
                lambda m: self._to_subscript(m.group(1)),
                text
            )
            # 处理 x_n 形式（单个字符或数字）
            text = re.sub(
                r'_([0-9a-zA-Z])',
                lambda m: self._to_subscript(m.group(1)),
                text
            )
        return text
    
    def _to_superscript(self, text: str) -> str:
        """将文本转换为上标形式"""
        result = []
        for char in text.strip():
            result.append(self.SUPERSCRIPT_MAP.get(char, char))
        return ''.join(result)
    
    def _to_subscript(self, text: str) -> str:
        """将文本转换为下标形式"""
        result = []
        for char in text.strip():
            result.append(self.SUBSCRIPT_MAP.get(char, char))
        return ''.join(result)
    
    def _convert_greek(self, text: str) -> str:
        """转换希腊字母"""
        for latex, unicode_char in self.GREEK_LETTERS.items():
            text = text.replace(latex, unicode_char)
        return text
    
    def _convert_functions(self, text: str) -> str:
        """转换数学函数"""
        for latex_func in self.MATH_FUNCTIONS:
            func_name = self.FUNCTION_NAMES[latex_func]
            # 使用 re.escape 来安全地转义 LaTeX 命令
            pattern = re.escape(latex_func) + r'(?![a-zA-Z])'
            text = re.sub(pattern, func_name, text)
        return text
    
    def _convert_special_symbols(self, text: str) -> str:
        """转换特殊符号"""
        # 按顺序替换特殊符号，更长的匹配先执行
        replacements = [
            # 标签和标记
            (r'\tag{', '('), (r'\tag', ''),
            (r'\text{', ''), (r'\text', ''),
            (r'\dot', '·'), (r'\ddot', '"'),
            (r'\hat', '^'), (r'\bar', '-'), (r'\vec', '→'),
            (r'\Delta', 'Δ'), (r'\triangle', '△'),
            # 无穷大和积分
            (r'\infty', '∞'), (r'\integral', '∫'), (r'\int', '∫'),
            # 运算符
            (r'\times', '×'), (r'\cdot', '·'), (r'\div', '÷'), (r'\pm', '±'), (r'\mp', '∓'),
            (r'\leq', '≤'), (r'\geq', '≥'), (r'\neq', '≠'), (r'\approx', '≈'),
            (r'\equiv', '≡'), (r'\sim', '∼'), (r'\simeq', '≃'), (r'\cong', '≅'),
            # 集合论
            (r'\subset', '⊂'), (r'\supset', '⊃'),
            (r'\subseteq', '⊆'), (r'\supseteq', '⊇'), (r'\cup', '∪'), (r'\cap', '∩'),
            (r'\emptyset', '∅'), (r'\varnothing', '∅'),
            # 微积分符号
            (r'\partial', '∂'), (r'\nabla', '∇'),
            (r'\oint', '∮'), (r'\iint', '∬'), (r'\iiint', '∭'),
            # 逻辑符号
            (r'\forall', '∀'), (r'\exists', '∃'), (r'\nexists', '∄'),
            (r'\neg', '¬'), (r'\wedge', '∧'), (r'\vee', '∨'),
            # 其他数学符号
            (r'\oplus', '⊕'), (r'\otimes', '⊗'), (r'\odot', '⊙'),
            (r'\langle', '⟨'), (r'\rangle', '⟩'), (r'\lfloor', '⌊'), (r'\rfloor', '⌋'),
            (r'\lceil', '⌈'), (r'\rceil', '⌉'),
            (r'\sum', '∑'), (r'\prod', '∏'), (r'\coprod', '∐'),
            (r'\degree', '°'), (r'\circ', '°'),
            (r'\left', ''), (r'\right', ''),
            (r'\dots', '…'), (r'\cdots', '…'), (r'\vdots', '⋮'), (r'\ddots', '⋱'),
            (r'\rightarrow', '→'), (r'\leftarrow', '←'), (r'\leftrightarrow', '↔'),
            (r'\Rightarrow', '⇒'), (r'\Leftarrow', '⇐'), (r'\Leftrightarrow', '⇔'),
            (r'\mapsto', '↦'), (r'\hookrightarrow', '↪'),
            (r'\prime', "'"), (r'\backslash', '\\'), (r'\%', '%'), (r'\#', '#'),
            (r'\&', '&'), (r'\in', '∈'), (r'\ni', '∋'),
            # 希腊字母（作为符号时）
            (r'\omega', 'ω'), (r'\Omega', 'Ω'),
        ]
        
        for latex, symbol in replacements:
            text = text.replace(latex, symbol)
        
        # 特殊处理需要转义的
        text = text.replace(r'\_', '_')
        text = text.replace(r'\{', '{')
        text = text.replace(r'\}', '}')
        
        return text
    
    def _convert_formula(self, formula: str) -> str:
        """转换单个公式内容"""
        for func, name in self.replacements:
            formula = func(formula)
        return formula.strip()
    
    def _cleanup(self, text: str) -> str:
        """清理多余的空白和括号"""
        # 移除多余空格
        text = re.sub(r' +', ' ', text)
        # 移除开头和结尾的空格
        text = text.strip()
        return text
    
    def convert_inline(self, match: re.Match) -> str:
        """转换行内公式 $...$"""
        formula = match.group(1)
        converted = self._convert_formula(formula)
        return converted
    
    def convert_display(self, match: re.Match) -> str:
        """转换独立公式 $$...$$"""
        formula = match.group(1).strip()
        converted = self._convert_formula(formula)
        # 独立公式转换为单独一行
        return converted
    
    def convert_text(self, text: str) -> str:
        """转换整个文本"""
        # 先处理独立公式 $$...$$
        text = re.sub(r'\$\$(.+?)\$\$', self.convert_display, text, flags=re.DOTALL)
        # 再处理行内公式 $...$（但要排除 $$）
        text = re.sub(r'\$([^\$]+?)\$', self.convert_inline, text)
        # 最后处理独立的 LaTeX 命令（不在 $ 中的）
        text = self._convert_standalone_commands(text)
        return text
    
    def _convert_standalone_commands(self, text: str) -> str:
        """转换独立的 LaTeX 命令（不在 $ 公式环境中的）"""
        # 处理 \tag{数字} -> (数字)
        text = re.sub(r'\\tag\{(\d+)\}', r'(\1)', text)
        text = re.sub(r'\\tag', '', text)
        
        # 处理 \dot{x} -> ẋ
        def replace_dot(match):
            content = match.group(1)
            # 为字母加上点标记
            dot_map = {
                'd': 'ḋ', 'x': 'ẋ', 'y': 'ẏ', 'z': 'ż',
                'a': 'ȧ', 'b': 'ḃ', 'c': 'ċ', 'e': 'ė',
                'f': 'ḟ', 'g': 'ġ', 'h': 'ḣ', 'i': 'i̇',
                'l': 'ḷ', 'm': 'ṁ', 'n': 'ṅ', 'o': 'ȯ',
                'p': 'ṗ', 'r': 'ṙ', 's': 'ṡ', 't': 'ṫ',
                'v': 'v̇', 'w': 'ẇ', 'D': 'Ḋ', 'X': 'Ẋ', 'Y': 'Ẏ',
            }
            return dot_map.get(content, f'·{content}')
        
        text = re.sub(r'\\dot\{([a-zA-Z])\}', replace_dot, text)
        text = re.sub(r'\\dot', '·', text)
        
        # 处理 \text{...} -> ...
        text = re.sub(r'\\text\{([^}]*)\}', r'\1', text)
        
        # 处理集合论和逻辑符号
        replacements = {
            # 集合论符号
            r'\aleph': 'ℵ', r'\aleph_0': 'ℵ₀', r'\aleph_1': 'ℵ₁', r'\aleph_2': 'ℵ₂', r'\aleph_3': 'ℵ₃',
            r'\mathfrak{c}': 'c', r'\mathfrak': '',
            # 逻辑符号
            r'\lor': '∨', r'\land': '∧', r'\neg': '¬',
            r'\notin': '∉', r'\ni': '∋', r'\in': '∈',
            r'\subset': '⊂', r'\supset': '⊃', r'\subseteq': '⊆', r'\supseteq': '⊇',
            r'\cup': '∪', r'\cap': '∩',
            r'\emptyset': '∅', r'\varnothing': '∅',
            # 箭头符号
            r'\rightarrow': '→', r'\leftarrow': '←', r'\leftrightarrow': '↔',
            r'\Rightarrow': '⇒', r'\Leftarrow': '⇐', r'\Leftrightarrow': '⇔',
            r'\mapsto': '↦', r'\hookrightarrow': '↪', r'\iff': '⇔', r'\vdash': '⊢',
            # 几何符号
            r'\angle': '∠', r'\triangle': '△',
            # 其他符号
            r'\Delta': 'Δ',
            r'\omega': 'ω', r'\Omega': 'Ω',
            r'\left': '', r'\right': '',
            r'\ ': ' ', r'\,': ' ',
            r'\cdot': '·', r'\times': '×',
            r'\mid': '|', r'\parallel': '∥',
            r'\approx': '≈', r'\equiv': '≡', r'\sim': '∼',
            r'\leq': '≤', r'\geq': '≥', r'\neq': '≠',
            r'\infty': '∞', r'\partial': '∂', r'\nabla': '∇',
            r'\sum': '∑', r'\prod': '∏', r'\int': '∫',
        }
        
        # 先处理长的匹配
        for latex, replacement in replacements.items():
            text = text.replace(latex, replacement)
        
        # 处理 \aleph₀ 等下标
        text = re.sub(r'ℵ_(\d)', lambda m: f'ℵ{self.SUBSCRIPT_MAP.get(m.group(1), m.group(1))}', text)
        
        return text


def process_file(input_path: str, output_path: str = None, dry_run: bool = False):
    """处理文件"""
    converter = LaTeXToTextConverter()
    
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 统计公式数量
    inline_count = len(re.findall(r'\$[^\$]+?\$', content))
    display_count = len(re.findall(r'\$\$.+?\$\$', content, re.DOTALL))
    
    print(f"处理文件：{input_path}")
    print(f"  发现行内公式 (${{...}}$): {inline_count} 个")
    print(f"  发现独立公式 ($${{...}}$$): {display_count} 个")
    
    converted = converter.convert_text(content)
    
    # 检查是否还有未处理的公式
    remaining_inline = len(re.findall(r'\$[^\$]+?\$', converted))
    remaining_display = len(re.findall(r'\$\$.+?\$\$', converted, re.DOTALL))
    
    if remaining_inline > 0 or remaining_display > 0:
        print(f"  ⚠️  警告：仍有 {remaining_inline} 个行内公式和 {remaining_display} 个独立公式未处理")
    
    if dry_run:
        print("\n--- 转换预览（前 500 字符）---")
        print(converted[:500])
        print("...\n")
    else:
        if output_path is None:
            output_path = input_path
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(converted)
        
        print(f"  ✓ 已保存到：{output_path}")
    
    return converted


def run_tests():
    """运行测试"""
    print("运行测试...\n")
    
    converter = LaTeXToTextConverter()
    
    tests = [
        (r'$x^2$', 'x²'),
        (r'$x^n$', 'xⁿ'),
        (r'$\frac{a}{b}$', 'a/b'),
        (r'$\sqrt{x}$', '√'),
        (r'$\sqrt[3]{x}$', '³√'),
        (r'$\pi$', 'π'),
        (r'$\sin x$', 'sin'),
        (r'$\log x$', 'log'),
        (r'$\alpha + \beta$', 'α'),
        (r'$\times$', '×'),
        (r'$\cdot$', '·'),
        (r'$\infty$', '∞'),
        (r'$\int_0^1$', '∫'),
        (r'$$\frac{2}{\pi}$$', '2/π'),
        (r'$a_1 + a_2$', 'a₁'),
        (r'$(-1) \times (-1)$', '×'),
        (r'$\sqrt{-1}$', '√(-1)'),
        (r'$x^2 + y^2 = z^2$', 'x²'),
        (r'$3\frac{10}{71}$', '10/71'),
        (r'$h = 100t - 16t^2$', 't²'),
    ]
    
    passed = 0
    failed = 0
    
    for input_text, expected in tests:
        result = converter.convert_text(input_text)
        if expected in result:
            print(f"✓ {input_text} → {result}")
            passed += 1
        else:
            print(f"✗ {input_text} → {result} (期望包含：{expected})")
            failed += 1
    
    print(f"\n测试结果：{passed} 通过，{failed} 失败")
    return failed == 0


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LaTeX 数学公式转纯文本工具')
    parser.add_argument('input', nargs='?', help='输入文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径（默认覆盖原文件）')
    parser.add_argument('-n', '--dry-run', action='store_true', help='仅预览，不写入文件')
    parser.add_argument('-t', '--test', action='store_true', help='运行测试')
    
    args = parser.parse_args()
    
    if args.test or args.input is None:
        run_tests()
        return
    
    process_file(args.input, args.output, args.dry_run)


if __name__ == '__main__':
    main()
