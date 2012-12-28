# -*- coding: utf-8 -*-
from pyparsing import *
from from_pyv import alias,_group,delim,unalias,ungroup,Action,Grammar
import sys
import pprint

_keywords = ["channel","typedef","port","output","input",
"function","wait","module","event","if","else"]

ID = ~MatchFirst([Keyword(w) for w in _keywords]) + Regex(r"[a-zA-Z_][a-zA-Z0-9_$]*")("id")
LP,RP,LB,RB,LC,RC,COLON,SEMICOLON,CAMMA,PERIOD,SHARP,EQUAL,AT,ASTA,Q,PLUS,MINUS,USC,APS = map(Suppress,("()[]{}:;,.#=@*?+-_'"))

for k in _keywords:
    setattr(sys.modules[__name__],k,Literal(k))


val = Word(nums)
identifier = ID | ID + ZeroOrMore( PERIOD + ID )
_type = identifier

term = ( ID | val | identifier )

var_decl = Group( _type + ID + SEMICOLON )
typedef_decl = Group( typedef + _type + ID + SEMICOLON )

signal = Group( ID + PERIOD + ID )
sig_direction_decl = Group( ( output | input ) + Optional(signal) + ID + SEMICOLON )

function_decl = Forward()

port_item = sig_direction_decl | function_decl
port_decl = Group( port + ID + LC + ZeroOrMore( port_item ) + RC )

channel_item = (typedef_decl | var_decl | port_decl)
channel_decl = Group( Group(channel + ID) + LC +
                      ZeroOrMore( channel_item ) + 
                      RC )

instantiation = identifier + identifier + LP + Optional(delim(term)) + RP + SEMICOLON

statement = Forward()

function_arg_list = Optional( delim( Group(_type + ID ) ) )

function_decl << Group( Group(function + _type + ID + LP +
                       function_arg_list +
                       RP) + LC +
                       ZeroOrMore( statement ) +
                       RC )

assignment = Group(ID + EQUAL + term + SEMICOLON)

wait_stmt = Group( wait + LP + RP + SEMICOLON )

statement << (var_decl |
              instantiation |
              assignment  |
              wait_stmt )

pprint.pprint(function_decl.parseString("""
        function void write(address_t addr, data_t data ) 
        {
            en      = 1;
            write   = 1;
            Addr    = addr;
            OutData = data;
            wait();
            en      = 0;
        }
""").asList())

pprint.pprint(channel_decl.parseString("""
channel BusCh {
    address_t  Addr;
    data_t OutData;
    data_t InData;
    logic req;
    logic wen;
    logic ack;

    port master{ 
        output Addr;
        output OutData;
        input  InData;
        output req;
        output wen;
        input  ack;
    }

    port slave{
        input master.OutData  InData;
        output master.InData  OutData;
        output ack;
    }

    port monitor{
    }
}
""").asList(),indent=2)


pprint.pprint(channel_decl.parseString("""
channel MemIfCh {

    logic en;
    logic write;
    logic ack;
    address_t Addr;
    data_t OutData;
    data_t InData;

    port master{ 
        output en;
        output write;
        input ack;
        output  Addr;
        output  OutData;
        input InData;
        
        function void write(address_t addr, data_t data ) 
        {
            en      = 1;
            write   = 1;
            Addr    = addr;
            OutData = data;
            wait();
            en      = 0;
        }
        function void read(address_t addr)
        {
            en = 1;
            write = 0;
            Addr = addr;
            wait();
        }
        function data_t read(address_t addr)
        {
            en = 1;
            write = 0;
            Addr = addr;
            wait();
            return InData;
        }
    }

    port slave{
        input master.OutData InData;
        output master.InData OutData;
        output ack;
    }
    
    port monitor{}

}
""").asList(),indent=2,width=100)


pprint.pprint(port_decl.parseString("""
    port master{ 
        output Addr;
        output OutData;
        input  InData;
        output req;
        output wen;
        input  ack;
    }
""").asList())
print(signal.parseString("master.OutData"))
print(sig_direction_decl.parseString("input  ack;"))

pprint.pprint(port_decl.parseString("""
    port slave {
        input master.OutData  InData;
        output master.InData  OutData;
        output ack;
    }
""").asList())

# print(var_decl.parseString("adddress_t Addr;"))
# print(typedef_decl.parseString("typedef logic hoge_t;"))

# print(val.parseString("1"))
# print(val.parseString("123"))
# print(identifier.parseString("abc.def"))
# print(identifier.parseString("a"))
# print(instantiation.parseString("state s();"))
# print(instantiation.parseString("state s(1,2);"))


