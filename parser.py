# -*- coding: utf-8 -*-
from pyparsing import (Word, nums, 
                       Keyword, Literal, Regex, Regex, MatchFirst, NotAny, CharsNotIn, Suppress, 
                       Forward, Group, Optional, ZeroOrMore, OneOrMore, 
                       delimitedList, operatorPrecedence, opAssoc, oneOf,
                       ParseException, ParseSyntaxException,
                       ParseResults,
                       cStyleComment, cppStyleComment)
from os import path
import sys
import pprint

this_mod = sys.modules[__name__]


_keywords_file             = path.join(path.dirname(this_mod.__file__), "keywords.txt")
_non_terminal_symbols_file = path.join(path.dirname(this_mod.__file__), "non_terminal_symbols.txt")

with open(_keywords_file,"r") as f:
    _keywords = [line.strip() for line in f]

ID = ~MatchFirst([Keyword(w) for w in _keywords]) + Regex(r"[a-zA-Z_][a-zA-Z0-9_$]*")("id")
LP,RP,LB,RB,LC,RC,COLON,SEMICOLON,CAMMA,PERIOD,SHARP,EQUAL,AT,ASTA,Q,PLUS,MINUS,USC,APS = map(Suppress,("()[]{}:;,.#=@*?+-_'"))

DSLASH = Suppress(Literal("//"))

for k in _keywords:
    setattr(this_mod, k.swapcase(), Keyword(k)("keyword"))
    #setattr(sys.modules[__name__],k,Literal(k))

with open(_non_terminal_symbols_file,"r") as f:
    for name in (line.strip() for line in f):
        sym = Forward()(name)
        sym.enablePackrat()
        sym.ignore(cStyleComment)
        #print("sym={0}".format(name))
        setattr(this_mod, name, sym)


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

def delimWithDsComment(expr,delimiter=','):
    d = Suppress(delimiter)
    return (Group(expr + d + Optional(comment)) + 
            ZeroOrMore(Group(expr + d + Optional(comment))) +
            Group(expr + Optional(comment))
            |
            Group(expr + Optional(comment)) 
            )

def delim(expr, delimiter=','):
    return _group( delimitedList(expr, delimiter).ignore(cStyleComment) - NotAny(delimiter) ,
                   errmsg = "invalid ','" )

def zeroOrMore(expr):
    return ZeroOrMore(expr).ignore(cStyleComment)

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


val    << Word(nums)
_range << val + COLON + val

identifier << ID + zeroOrMore( PERIOD + ID )

_type << identifier + Optional(Group( LB + _range + RB ))

term << ( val | identifier )

expression << operatorPrecedence( term, [
        (oneOf("* /"), 2, opAssoc.LEFT),
        (oneOf("+ -"), 2, opAssoc.LEFT),
        (oneOf("|| &&"), 2, opAssoc.LEFT),
        ] )

var_decl     << Group( _type + ID + SEMICOLON + Optional(comment))
typedef_decl << Group( TYPEDEF + _type + ID + SEMICOLON )

signal             << Group( ID + PERIOD + ID )
sig_direction_decl << Group( ( OUTPUT | INPUT ) + Optional(signal) + ID + SEMICOLON )


port_item << (sig_direction_decl | function_decl)
port_decl << Group( Group(PORT + ID) + LC + zeroOrMore( port_item ) + RC )

channel_item << (typedef_decl | var_decl | port_decl)
channel_decl << Group( Group(CHANNEL + ID) + LC +
                      zeroOrMore( channel_item ) + 
                      RC )

instantiation << Group( identifier + identifier + LP + Optional(delim(expression)) + RP )


function_arg_list << Optional( delim( Group(_type + ID ) ) )

function_decl << Group( Group(FUNCTION + _type + ID + LP + function_arg_list + RP) + 
                        LC + zeroOrMore( statement ) + RC )

assign_op << ( EQUAL | oneOf("+= -=") )

assignment << Group( ID + assign_op + expression + SEMICOLON )

func_call_expr << Group( ID + LP + Optional(identifier) + RP )

statement << (var_decl                   |
              instantiation + SEMICOLON  |
              assignment                 |
              func_call_expr + SEMICOLON )

event_stmt << Group( Group(EVENT + LP + Optional(identifier) + RP) + 
                    LC + zeroOrMore( statement ) + RC )

module_decl << Group( Group( MODULE + ID + LP + module_arg_list + RP ) +
                      LC + zeroOrMore( module_item ) + RC )

module_arg_type << ( INPUT | OUTPUT | _type ) 
module_arg_list << Optional( delimWithDsComment( Group(module_arg_type + ID) ) )

module_item << (var_decl                  |
                instantiation + SEMICOLON |
                function_decl             |
                event_stmt                |
                comment                   )

comment << Regex(r"\/\/(\\\n|.)*").setName("// comment")


