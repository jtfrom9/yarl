# -*- coding: utf-8 -*-

class AstNode(object):
    def __str__(self):
        return self.__class__.__name__
    def __repr__(self):
        return self.__str__();
    def has_comment(self):
        return True if getattr(self,"comment",False) != "" else False

    @property
    def has_loc_info(self):
        return True if getattr(self,"_loc_info",False) != "" else False
    @property
    def loc_info(self):
        return self._loc_info
    @loc_info.setter
    def loc_info(self,info):
        if not isinstance(info,tuple) or len(info)!=2:
            raise Exception("fail to set loc_info")
        self._loc_info = info
    @property
    def lineno(self):
        return self.loc_info[0]
    @property
    def colno(self):
        return self.loc_info[1]

    def traverse(self,visitor,arg):
        visitor.visit(self, arg)

class Id(AstNode):
    def __init__(self, head, tails):
        self._ids = tuple([head] + tails)
    def __str__(self):
        return ".".join(i for i in self._ids)

class Range(AstNode):
    def __init__(self,lsb,msb):
        self._lsb = lsb
        self._msb = msb
    def __str__(self):
        return "({0}:{1})".format(self._lsb, self._msb)

class Type(AstNode):
    def __init__(self, typename, typerange):
        """typename  : ast.Id
           typerange : ast.Range """
        self._typename = typename
        self._range    = typerange
    def __str__(self):
        return "(t:{0}{1})".format(self._typename,
                                   "" if not self._range else self._range)

class VarDecl(AstNode):
    def __init__(self, var_type, var_id):
        self._var_type = var_type
        self._var_id   = var_id
    def __str__(self):
        return "(var:{0}<{1}>)".format(self._var_id, self._var_type)

class TypedefDecl(AstNode):
    def __init__(self, typedef_type, typedef_id):
        self._typedef_type = typedef_type
        self._typedef_id   = typedef_id
    def __str__(self):
        return "(typedef:{0}<{1}>)".format(self._typedef_id, self._typedef_type)

class PortSignal(AstNode):
    def __init__(self, signal_dir, signal_id, orig_signal):
        #print("dir={0}, id={1}, orig={2}".format(signal_dir,signal_id, orig_signal))
        self._signal_dir = signal_dir
        self._signal_id  = signal_id
        self._orig_signal = orig_signal
    def __str__(self):
        return "(sig:{dir}:{name}{alias})".format(
            dir = self._signal_dir,
            name = self._signal_id,
            alias = "" if self._orig_signal else str(self._orig_signal))
        
class Inst(AstNode):
    def __init__(self, inst_type_id, inst_id, param_exprs):
        self._inst_type_id = inst_type_id
        self._inst_id      = inst_id
        self._param_exprs  = param_exprs
    def __str__(self):
        return "(inst:{name}<{type}>)".format(
            name = self._inst_id, 
            type = self._inst_type_id)

class Argument(AstNode):
    def __init__(self, arg_dir, arg_type, arg_id):
        """
        arg_dir: 'input' or 'output'
        """
        self._arg_dir  = arg_dir
        self._arg_type = arg_type
        self._arg_id   = arg_id
    def __str__(self):
        return "(a:{dir}/{vtype} {var})".format(
            dir   = self._arg_dir,
            vtype = self._arg_type, 
            var   = self._arg_id)

class Comment(AstNode):
    def __init__(self, comment_str):
        self._comment_str = comment_str
    def __str__(self):
        return "\"{comment}\"({lineno},{colno})".format(comment = self._comment_str,
                                                    lineno = self.lineno,
                                                    colno  = self.colno)

#
# Expression
#
class Expression(AstNode):
    pass

class Term(Expression):
    def __init__(self,data):
        self._data = data
    def __str__(self):
        return str(self._data)

class BinExp(Expression):
    def __init__(self,op,lhs,rhs):
        self._lhs = lhs
        self._rhs = rhs
        self._op  = op
    def __str__(self):
        return "(expr:{0}{1}{2})".format(self._lhs,self._op,self._rhs)

class FuncCall(Expression):
    def __init__(self, func_id, param_exprs):
        self._func_id     = func_id
        self._param_exprs = param_exprs
    def __str__(self):
        return "(fcall:{name}(...))".format(name = self._func_id)



#
# Statement
#
class Statement(AstNode):
    pass

class Assign(Statement):
    def __init__(self, op, lsh, rsh):
        self._op  = op
        self._lsh = lsh
        self._rsh = rsh
    def __str__(self):
        return "({lsh}{op}{rsh})".format(op=self._op, lsh=self._lsh, rsh=self._rsh)

#
# StatementBlock
#
class StatementBlock(AstNode):
    pass

class Function(StatementBlock):
    def __init__(self, func_id, func_args, func_stmts):
        self._func_id    = func_id
        self._func_args  = func_args
        self._func_stmts = func_stmts
    def __str__(self):
        return "(func:{name}({args}){{...{num} statements...}})".format(
            name = self._func_id,
            args = ",".join(str(arg) for arg in self._func_args),
            num  = len(self._func_stmts))

class Event(StatementBlock):
    def __init__(self, event_id, cond_expr, stmts):
        self._event_id  = event_id
        self._cond_expr = cond_expr
        self._stmts     = stmts
    def __str__(self):
        return "(event:{name}({cond}){{...{num} statements...}})".format(
            name = self._event_id,
            cond = str(self._cond_expr),
            num  = len(self._stmts))
        
#
# Structure
#
class Structure(AstNode):
    pass

class Port(Structure):
    def __init__(self, port_id, port_items):
        self._port_id    = port_id
        self._port_items = port_items
    def __str__(self):
        return "(port:{name}(...{num} items...))".format(
            name = self._port_id,
            num  = len(self._port_items))

class Channel(Structure):
    def __init__(self, channel_id, channel_items):
        self._channel_id    = channel_id
        self._channel_items = channel_items
        #print("chitems={0}".format(channel_items))
    def __str__(self):
        return "(ch:{name}{{...{num} items...}})".format(
            name=self._channel_id, 
            num =len(self._channel_items))
    
class Module(Structure):
    def __init__(self, name, args, items):
        self._name = name
        self._args = args
        self._items = items
    
