# -*- coding: utf-8 -*-
import sys
from os import path

from pyparsing import (Keyword, Literal, Regex, Regex, MatchFirst, NotAny, CharsNotIn, Suppress, 
                       Forward, Group, Optional, ZeroOrMore, OneOrMore, 
                       delimitedList, operatorPrecedence, opAssoc, oneOf,
                       ParseException, ParseSyntaxException,
                       ParseResults)

import ast

this_mod = sys.modules[__name__]

_keywords_file = path.join(path.dirname(this_mod.__file__), "keywords.txt")
_non_terminal_symbols_file = path.join(path.dirname(this_mod.__file__), "non_terminal_symbols.txt")

# with open(_keywords_file,"r") as f:
#     _keywords = [line.strip() for line in f]

# ID = ~MatchFirst([Keyword(w) for w in _keywords]) + Regex(r"[a-zA-Z_][a-zA-Z0-9_$]*")("id")
# LP,RP,LB,RB,LC,RC,COLON,SEMICOLON,CAMMA,PERIOD,SHARP,EQUAL,AT,ASTA,Q,PLUS,MINUS,USC,APS = map(Suppress,("()[]{}:;,.#=@*?+-_'"))

# NB = Suppress(Literal("<="))
# TRIG = Suppress(Literal("->"))

#LP/RP : left/right paren          ()
#LB/RB : left/right bracket        []
#LC/RC : left/right curly bracket  {}

# setup keywords
# for kw in _keywords:
#     setattr(this_mod, kw.swapcase(), Keyword(kw)("keyword"))

# setup non-terminal-symbols
# with open(_non_terminal_symbols_file,"r") as f:
#     for name in (line.strip() for line in f):
#         sym = Forward()(name)
#         sym.enablePackrat()
#         setattr(this_mod, name, sym)


def alias(grammar, name):
    if name: 
        return Group(grammar)(name)
    else:
        return Group(grammar)

class ErrorReportException(ParseException):
    pass

def _group(expr, errmsg=None):
    class WrapGroup(Group):
        def __init__(self, expr):
            super(WrapGroup,self).__init__(expr)
        def parseImpl(self, *args):
            target = None
            try:
                if len(args)>=2:
                    target = "\'{0}\'".format(args[0][args[1]:])
                return super(WrapGroup,self).parseImpl(*args)
            except ParseException as e:
                if errmsg:
                    raise ErrorReportException("Syntax Error: " + errmsg)
                elif not isinstance(e, ErrorReportException):
                    raise ErrorReportException("Syntax Error: " + target)
                else:
                    raise
            except ParseSyntaxException as e:
                if errmsg: 
                    e.msg = "Syntax Error: " + errmsg
                    raise e
                else:
                    raise
    return WrapGroup(expr)

def delim(expr, delimiter=','):
    return _group( delimitedList(expr,delimiter) - NotAny(delimiter) ,
                   errmsg = "invalid ','" )

def unalias(token): return token[0]
def ungroup(token): return token[0]

def Action(*argv,**kw):
    def deco_func(action):
        if kw.get('ungroup',False):
            new_func = lambda t: action(ungroup(t))
        else:
            new_func = action
        for grammar in argv:
            grammar.setParseAction(new_func)
        return new_func
    return deco_func

def Grammar(grammar_def_func):
    grammar_def, action = grammar_def_func()
    symbol = getattr(this_mod, grammar_def_func.__name__)
    symbol << grammar_def
    if action:
        symbol.setParseAction(action)
    return symbol

def GrammarNotImplementedYet(grammar_def_func):
    grammar_def = grammar_def_func()[0]
    def _error():
        raise Exception("Not Implemented: " + grammar_def_func.__name__)
    symbol = getattr(this_mod, grammar_def_func.__name__)
    symbol << grammar_def
    symbol.setParseAction(_error)
    return symbol

class NotImplementedCompletelyAction(Exception):
    def __init__(self, token=None):
        import inspect
        frame = inspect.currentframe(1)
        msg = "Error at {0}:{1}".format(
            frame.f_code.co_filename,
            frame.f_lineno)
        if token:
            msg += "\n    token={0}".format(ast.nodeInfo(token))
        super(Exception,self).__init__(msg)

