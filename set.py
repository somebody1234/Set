#!/usr/bin/env python3

from enum import Enum
from sys import stdin, stdout, stderr
import argparse
import os


class Eof(object):
    def __str__(self):
        return "EOF"

    def __repr__(self):
        return "EOF"

EOF = Eof()
_chr = chr

def chr(value):
    return _chr(value) if value >= 0 else ""


class Set(object):
    __slots__ = (
        "variables", "program", "index", "input", "input_index",
        "debug"
    )

    def __init__(self, debug=False):
        self.variables = {"?": 0}
        self.program = []
        self.index = 0
        self.input = ""
        self.input_index = -1
        self.debug = debug
        for lowercase in "abcdefghijklmnopqrstuvwxyz":
            self.variables[lowercase] = 0
        for uppercase in "ABCDEFGHIJKLMNOPQRSTUVWZYZ":
            self.variables[uppercase] = ord(uppercase)

    def add(self, code):
        index = debug_index = 0

        def get(item):
            if isinstance(item, int):

                def getter():
                    return item
                return getter
            elif item == "?":

                def getter():
                    return self.index
                return getter
            elif item == "!":

                def getter():
                    self.input_index += 1
                    return (
                        self.input[self.input_index]
                        if self.input_index < len(self.input) else
                        ""
                    )
                return getter

            def getter():
                return self.variables[item]
            return getter

        def set(item, value):
            if isinstance(item, int):
                raise TypeError("Cannot assign to a number")
            elif item == "?":

                def setter():
                    self.index = value() - 1
                return setter
            elif item == "!":

                def setter():
                    stdout.write(chr(value()))
                    self.index += 1
                return setter

            def setter():
                self.variables[item] = value()
                self.index += 1
            return setter

        def add(a, b):
            def adder():
                return a() + b()
            return adder

        def subtract(a, b):
            def subtractor():
                return a() - b()
            return subtractor

        def equal(a, b):
            def equalize(line):
                def equalizer():
                    if a() == b():
                        line()
                    else:
                        self.index += 1
                return equalizer
            return equalize

        def unequal(a, b):
            def unequalize(line):
                def unequalizer():
                    if a() != b():
                        line()
                    else:
                        self.index += 1
                return unequalizer
            return unequalize

        def ws():
            nonlocal index
            while index < len(code) and code[index] in " \t":
                index += 1

        def tok():
            nonlocal index
            ws()
            if index == len(code):
                return EOF
            result = code[index]
            if result >= "0" and result <= "9":
                original = index
                index += 1
                while (
                    index < len(code) and
                    code[index] >= "0" and
                    code[index] <= "9"
                ):
                    index += 1
                return code[original:index]
            index += 1
            return result

        def var():
            name = tok()
            return (
                int(name)
                if name[0] >= "0" and name[0] <= "9" else
                name
            )

        def sdvar():
            nonlocal index
            ws()
            result = code[index]
            index += 1
            return (
                int(result)
                if result >= "0" and result <= "9" else
                result
            )

        def com_or_var():
            nonlocal index
            ws()
            result = code[index]
            if code[index] != "(":
                return get(var())
            tok()  # (
            first, type, second = sdvar(), tok(), sdvar()
            if type not in "+-":
                raise SyntaxError(
                    "%s is not a valid combiner type" % repr(type)
                )
            closing = tok()
            if closing != ")":
                raise SyntaxError(
                    "Unexpected %s, expected ')'" % repr(closing)
                )
            return (
                add(get(first), get(second))
                if type == "+" else
                subtract(get(first), get(second))
            )

        while index < len(code) and code[index] in " \t\f\v\r\n>":
            if code[index] == ">":
                while index < len(code) and code[index - 1] != "\n":
                    index += 1
            while index < len(code) and code[index] in " \t\f\v\r\n":
                index += 1
        while index < len(code):
            try:
                debug_index += 1
                # skip whitespace and comments
                # ok now check for a conditional
                conditional = None
                if code[index] == "[":
                    index += 1
                    first, type, second = sdvar(), tok(), sdvar()
                    if type not in "=/":
                        raise SyntaxError(
                            "%s is not a valid conditional type" % repr(type)
                        )
                    closing = tok()
                    if closing != "]":
                        raise SyntaxError(
                            "Unexpected %s, expected ']'" % repr(closing)
                        )
                    conditional = (
                        equal(get(first), get(second))
                        if type == "=" else
                        unequal(get(first), get(second))
                    )
                ws()
                if code[index:index + 3] != "set":
                    raise SyntaxError(
                        "Unexpected %s, expected 'set'" % repr(code[index])
                    )
                index += 3
                first, second = var(), com_or_var()
                line = set(first, second)
                self.program += [
                    conditional(line) if conditional is not None else line
                ]
                while index < len(code) and code[index] in " \t\f\v\r\n>":
                    if code[index] == ">":
                        index += 1
                        while index < len(code) and code[index - 1] != "\n":
                            index += 1
                    while index < len(code) and code[index] in " \t\f\v\r\n":
                        index += 1
            except Exception as e:
                if self.debug:
                    stderr.write("%s on line %s\n" % (str(e), debug_index))
                while index < len(code) and code[index - 1] != "\n":
                    index += 1
                while index < len(code) and code[index] in " \t\f\v\r\n>":
                    if code[index] == ">":
                        index += 1
                        while index < len(code) and code[index - 1] != "\n":
                            index += 1
                    while index < len(code) and code[index] in " \t\f\v\r\n":
                        index += 1
                pass  # invalid line, just skip it
        return self  # yay fluent

    def run(self, input=""):
        global lines
        self.input = input
        while self.index < len(self.program):
            self.program[self.index]()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Interpret the Set language."
    )
    parser.add_argument(
        "file", metavar="FILE", type=str, nargs="?", default="",
        help="File path of the program."
    )
    parser.add_argument(
        "-c", "--code", type=str, nargs="?", default="",
        help="Code."
    )
    parser.add_argument(
        "-i", "--input", type=str, nargs="?", default=None,
        help="Input."
    )
    parser.add_argument(
        "-d", "--debug", action="store_true",
        help="If enabled, shows parse errors."
    )
    parser.add_argument(
        "-od", "--onlydebug", action="store_true",
        help="If enabled, shows parse errors and exits."
    )
    argv = parser.parse_args()
    code = input = ""
    if argv.code:
        code = argv.code
    elif argv.file:
        if os.path.isfile(argv.file):
            with open(argv.file) as file:
                code = file.read()
        elif os.path.isfile(argv.file + ".set"):
            with open(argv.file + ".cl") as file:
                code = file.read()
        else:
            print(
                "FileNotFoundError: The specified Set file was not found."
            )
            sys.exit(1)
    if argv.input is not None:
        input = argv.input
    else:
        input = stdin.read()
    if not argv.onlydebug:
        Set(debug=argv.debug).add(code).run(input)
    else:
        Set(debug=argv.debug).add(code)
