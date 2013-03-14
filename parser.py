# -*- coding: utf-8 -*-
from pyparsing import (Word, nums, 
                       Keyword, Literal, Regex, Regex, MatchFirst, NotAny, CharsNotIn, Suppress, 
                       Forward, Group, Optional, ZeroOrMore, OneOrMore, 
                       delimitedList, operatorPrecedence, opAssoc, oneOf,
                       ParseException, ParseSyntaxException,
                       ParseResults,
                       cStyleComment, cppStyleComment,
                       lineno, col)

from os import path
import sys
import pprint
import logging

import ast

this_mod = sys.modules[__name__]

parentLogger = logging.getLogger("parser")
_lhandler = logging.StreamHandler()
_lhandler.setFormatter(logging.Formatter("%(name)s:%(levelname)s # %(message)s"))
parentLogger.addHandler(_lhandler)

_parserLoggers = {}
def getLogger(name):
    logger = _parserLoggers.get(name,None)
    if not logger:
        logger = logging.getLogger("parser." + name)
        _parserLoggers[name] = logger
    return logger

def enableLog(name=None, level=logging.DEBUG):
    l = parentLogger if not name else getLogger(name)
    l.setLevel(level)

def disableLog(name=None, level=logging.WARN):
    l = parentLogger if not name else getLogger(name)
    l.setLevel(level)

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

def ZeroOrMoreIgnoreComment(expr):
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
    #grammar_def = grammar_def_func()[0]
    def _error():
        raise Exception("Not Implemented: " + grammar_def_func.__name__)
    symbol = getattr(this_mod, grammar_def_func.__name__)
    #symbol << grammar_def
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

def nodeInfo(node):
    if isinstance(node,str):
        return "str: {0}".format(node)
    if isinstance(node,ParseResults):
        return "pr: {0}".format([prop for prop in dir(node) if not prop.startswith("__")])
    if isinstance(node,ast.AstNode):
        return "ast: {0}".format(repr(node))
    return type(node)

@Grammar
def val(_ = Word(nums)): 
    return (_,lambda t: int(t[0]))

@Grammar
def _range(_ = val + COLON + val): 
    return (_,lambda t: ast.Range(t[0], t[1]))

@Grammar
def identifier(_ = alias(ID,"head") + ZeroOrMore( PERIOD + ID )("tails") ):
    def action(token):
        return ast.Id(unalias(token.head), [tail for tail in token.tails])
    return (_,action)

@Grammar
def var_type(_ = identifier + Optional(LB + _range + RB)):
    return (_, lambda t: ast.Type(t.identifier, t._range))

@Grammar
def term(_ = val | identifier ):
    return (_, lambda t: ast.Term(t[0]))

@Grammar
def expression():
    action=None
    _ = operatorPrecedence( term, [
            (oneOf("* /")  , 2, opAssoc.LEFT, action),
            (oneOf("+ -")  , 2, opAssoc.LEFT, action),
            (oneOf("|| &&"), 2, opAssoc.LEFT, action),
            ] )

    @Action(ungroup=True)
    def action(token):
        #print("exp={0}".format(token))
        if isinstance(token,ast.BinExp) or isinstance(token,ast.Term):
            return token
        else:
            return ast.BinExp(token[1], token[0], token[2])
    return (_,action)


@Grammar
def var_decl(_ = var_type + ID + SEMICOLON):
    return (_, lambda t: ast.VarDecl(t.var_type, t.id))

@Grammar
def typedef_decl(_ = TYPEDEF + var_type + ID):
    return (_, lambda t: ast.TypedefDecl(t.var_type, t.id))

@Grammar
def port_signal():
    _ = (( OUTPUT | INPUT ) + Optional(identifier)("renamed") + ID + SEMICOLON |
         ( OUTPUT | INPUT )                                   + ID + SEMICOLON )
    def action(token):
        return ast.PortSignal( token.keyword, token.id, token.renamed )
    return (_,action)

@Grammar
def port_decl():
    _ = (PORT + ID + 
         LC + ZeroOrMoreIgnoreComment( port_signal | func_decl )("port_items") + RC )
    def action(token):
        return ast.Port( token.id,
                         [item for item in token.port_items] if token.port_items else [] )
    return (_,action)


@Grammar
def func_decl():
    func_arg = var_type + ID
    func_arg.setParseAction(lambda t: ast.Argument('input', t.var_type, t.id))

    _ = (FUNC + ID + LP + Optional(delim( func_arg )("func_args")) + RP + 
         LC + ZeroOrMoreIgnoreComment( statement )("statements") + RC )
    def action(token):
        # if token.func_args:
        #     print(token.func_args)
        #     for index,arg in enumerate(token.func_args):
        #         print("[{0}] = {1}".format(index, arg))
        return ast.Function(token.id,
                            [arg for arg in token.func_args] if token.func_args else [],
                            [stm for stm in token.statements] if token.statements else [])
    return (_,action)


@Grammar
def channel_decl():
    _  = (CHANNEL + ID + 
          LC + ZeroOrMoreIgnoreComment( typedef_decl | var_decl | port_decl )("channel_items") +  RC)
    # return (_,lambda token: ast.Channel( token.id, 
    #                                      [item for item in token.items] if not token.items else [] ))
    def action(token):
        #print("chitems={0}".format(token.channel_items))
        return ast.Channel( token.id, 
                            [item for item in token.channel_items] if token.channel_items else [] )
    return (_,action)


@Grammar
def func_call():
    _ = ( alias(identifier,"func_id") + 
          LP + Optional( delim(expression)("param_exprs") ) + RP )
    def action(token):
        return ast.FuncCall( unalias(token.func_id), 
                             [expr for expr in token.param_exprs] if token.param_exprs else [] )
    return (_,action)

@Grammar
def instantiation():
    _ = ( alias(identifier,"type_id") + alias(ID,"inst_id") + 
          LP + Optional( delim(expression)("param_exprs") ) + RP )
    def action(token):
        # print(token)
        # print(nodeInfo(token))
        return ast.Inst(unalias(token.type_id), 
                        unalias(token.inst_id),
                        [expr for expr in token.param_exprs] if token.param_exprs else [])
    return (_,action)

@Grammar
def assignment():
    return (ID + oneOf("= += -=")("op") + expression + SEMICOLON,
            lambda token: ast.Assign( token.op, token.id, token.expression ))

@GrammarNotImplementedYet
def wait_statement():
    _ = ( WAIT + Optional( LP + Optional( expression("cond_expr") ) + RP ) |
          Literal("@") + LP + expression + RP )

@GrammarNotImplementedYet
def if_statement():
    pass

@GrammarNotImplementedYet
def for_statement():
    pass

@Grammar
def statement():
    return ((var_decl                  |
             instantiation + SEMICOLON |
             assignment                |
             wait_statement            |
             if_statement              |
             for_statement             |
             func_call     + SEMICOLON |
             comment                   ),
            lambda token: token[0])

@Grammar
def event_struct():
    _ = ( EVENT + ID + LP + Optional( expression("cond_expr") ) + RP + 
          LC + ZeroOrMoreIgnoreComment( statement )("stmts") + RC )
    def action(token):
        return ast.Event(token.id, 
                         token.cond_expr if token.cond_expr else None,
                         [s for s in token.stmts] if token.stmts else [])
    return (_,action)

@Grammar
def module_arg():
    _ = ( (INPUT | OUTPUT)("dir_type") + var_type + ID |
          (INPUT | OUTPUT)("dir_type")            + ID |
                                         var_type + ID )
    def action(token):
        #print("token={0}".format(nodeInfo(token)))
        return ast.Argument( "input" if not token.dir_type else token.dir_type,
                             token.var_type if token.var_type else None,
                             token.id )
    return (_,action)

@Grammar
def module_decl():
    logger = getLogger("module_decl")
    module_item = (var_decl                  |
                   instantiation + SEMICOLON |
                   func_decl                 |
                   event_struct              |
                   comment                   )
                   
    module_item.setParseAction(lambda token: token[0])
    module_item.setName("module_item")
    #module_item.setDebug(True)

    _ = ( MODULE + ID + LP + delimWithDsComment( module_arg )("args") + RP + 
          LC + ZeroOrMoreIgnoreComment( module_item )("module_items") + RC )
    def action(token):
        logger.info("ID={0}, args={1}, items={2}".format(token.id, token.args, token.module_items))
        for item in token.module_items:
            logger.debug(item)
        return ast.Module(token.id, 
                          [ arg for arg in token.args ] if token.args else [],
                          [ item for item in token.module_items ] if token.module_items else [])
    return (_,action)


@Grammar
def comment():
    _ = Regex(r"\/\/((\\\n|.)*)")
    logger = getLogger("comment")
    def action(s, loc, token):
        _lineno = lineno(loc,s)
        _colno  = col(loc,s)-1
        logger.info("log={0} (lineno={1}, col={2})".format(loc, _lineno, _colno))
        logger.debug("comment: {0}".format(token[0]))
        logger.debug("comment: {0}".format(nodeInfo(token)))
        _comment = ast.Comment(token[0][2:])
        _comment.loc_info = (_lineno, _colno)
        return _comment
    return (_, action)


