# -*- coding: utf-8 -*-
import collections
import ast

class Arg(collections.Mapping):
    def __init__(self, parentNode, level=None):
        assert(isinstance(parentNode, ast.AstNode) or parentNode is None)
        self._dict = {}
        self._add('parentNode',parentNode)
        self._add('level',level)
        self._add('childNodes',[])

    def __len__(self):
        return len(self._dict)

    def __getitem__(self,key):
        return self._dict[key]

    def __iter__(self):
        for k in self._dict.keys():
            yield k

    def _add(self, key, value):
        if key in self._dict:
            raise Exception("already has key '{0}' in self._dict".format(key))
        self._dict[ key ] = value
        #setattr(self, key, value)
        #setattr(self.__class__, key, property(lambda self: self.__getitem__(key)))

    def nextArg(self, parentNode, **kws):
        arg = Arg(parentNode, self.level + 1)
        for key, value in kws.items():
            arg._add(key,value)
        return arg

class Visitor(object):
    def visit(self, node, arg):
        handler = getattr(self, "_visit" + type(node).__name__)
        if handler:
            handler(node,arg)

class TraverseTraceVisitor(Visitor):
    def visit(self,node,arg):
        print("{spc}{node}(arg={arg})".format(
                spc  = " "*arg.level*2 ,
                node = repr(node),
                arg  = arg.items()))

class StatementPrettyPrinterVisitor(Visitor):
    def __init__(self, out_stream, indent=2):
        self._out_stream = out_stream
        self._indent     = indent

    def _write(self, level, string):
        for s in string.split("\n"):
            self._out_stream.write(" " * (self._indent * level) + s + "\n")

    def _visitAny(self,node,arg):
        self._write(arg.level, str(node))

    def _visitConditionalStatement(self,node,arg):
        first = True
        for cond, stmt in node.eachCondAndStatements():
            if cond:
                self._write(arg.level,
                            "{key} {cond} then:".format(key  = "if" if first else "else if",
                                                        cond = str(cond)))
                first = False
            else:
                self._write(arg.level, "else:")
            self.visit(stmt,arg.createChild(node))

    def _visitBlock(self,block,arg):
        self._write(arg.level, "{key}".format(key="begin" if block.isSequencial else "fork"))
        newarg = arg.createChild(block)
        for s in block.eachStatements():
            self.visit(s,newarg)
        self._write(arg.level, "{key}".format(key="end" if block.isSequencial else "join"))

    def _visitConstructStatementItem(self,node,arg):
        self._write(arg.level,node.type)
        self.visit(node.statement,arg.createChild(node))

    def _visitContinuousAssignmentItems(self,node,arg):
        self._write(arg.level,node.type)
        for s in node.eachStatements():
            self.visit(s,arg.createChild(node))

    def _visitNodeList(self,nlist,arg):
        for n in nlist: 
            self.visit(n,arg)

    def _visitCaseStatement(self,node,arg):
        self._write(arg.level, "{key}:".format(key = str(node)))
        new_arg = arg.createChild(node)
        for item in node.eachItems():
            self.visit(item, new_arg)
