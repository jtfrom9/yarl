# -*- coding: utf-8 -*-
import sys
import pprint
import unittest
import logging 

from test_common import testOf, run_tests, debug, _id_print

import parser

def debug(expr, on=True, name=""):
    if name=="" :
        expr.setName(expr.resultsName)
    else:
        expr.setName(name)
    expr.setDebug(on)

@testOf(parser.var_decl)
def test_var_decl(self):
    print(self.check_pass("logic [11:0] count;"))
    print(self.check_pass("int [11:0] count;"))
    print(self.check_pass("char x;"))
    print(self.check_pass("int x;"))

@testOf(parser._range)
def test_range(self):
    print(self.check_pass("1:0"))

@testOf(parser.val)
def test_val(self):
    print(self.check_pass("1"))

@testOf(parser.ID)
def test_ID(self):
    print(self.check_pass("a"))
    
@testOf(parser.identifier)
def test_identifier(self):
    print(self.check_pass("a"))
    #debug(identifier)
    print(self.check_pass("a.b"))
    print(self.check_pass("hoge.foo.bar"))

@testOf(parser.expression)
def test3(self):
    self.check_pass("A || B")
    self.check_pass("A + B")
    self.check_pass("A * B")
    self.check_pass("A + B * C")
    self.check_pass("A * B + C")

@testOf(parser.port_signal)
def test_psig(self):
    #debug(port_signal)
    print(self.check_pass("output Addr;"))
    print(self.check_pass("input  ack;"))
    print(self.check_pass("input master.OutData  InData;  // alias"))

@testOf(parser.port_decl)
def test_port_decl(self):
    print(self.check_pass("""
port hoge{}
"""))
    print(self.check_pass("""
port hoge{
 output Addr;
 input DataIn;
}
"""))
    
@testOf(parser.channel_decl)
def test_channel_decl(self):
    print(self.check_pass("""
channel ch {}
"""))
    print(self.check_pass("""
channel ch {
typedef logic[1:0] hoge;
}
"""))
    print(self.check_pass("""
channel ch {
typedef logic[1:0] hoge;
    address_t  Addr;
}
"""))

@testOf(parser.func_decl)
def test_func_decl(self):
    print(self.check_pass("""
func write() {}
"""))
    print(self.check_pass("""
func write(data_t data) {}
"""))

    #debug(parser._type)
    print(self.check_pass("""
func write(address_t addr, 
           data_t data) {}
"""))

@testOf(parser.expression)
def test_exp(self):
    print(self.check_pass("1 + 2 || B"))
    print(self.check_pass("1"))

@testOf(parser.instantiation)
def test_inst(self):
    print(self.check_pass("hoge H()"))
    print(self.check_pass("hoge H(1)"))
    print(self.check_pass("hoge H(1,2)"))
    print(self.check_pass("hoge H(1,2,A,X+1)"))

@testOf(parser.assignment)
def test_assign(self):
    print(self.check_pass("A=1;"))
    print(self.check_pass("A=1+2;"))
    print(self.check_pass("A+=1+2;"))
    print(self.check_pass("A-=1+2;"))

@testOf(parser.func_call)
def test_fcall(self):
    print(self.check_pass("foo()"))
    print(self.check_pass("foo(1, 2, X+Y)"))

@testOf(parser.statement)
def test_stmt(self):
    print(self.check_pass("logic [11:0] count;"))
    print(self.check_pass("int [11:0] count;"))
    print(self.check_pass("char x;"))
    print(self.check_pass("int x;"))
    print(self.check_pass("hoge H();"))
    print(self.check_pass("hoge H(1);"))
    print(self.check_pass("hoge H(1,2);"))
    print(self.check_pass("hoge H(1,2,A,X+1);"))
    print(self.check_pass("foo();"))
    print(self.check_pass("foo(1, 2, X+Y);"))
    print(self.check_pass("A=1;"))
    print(self.check_pass("A=1+2;"))
    print(self.check_pass("A+=1+2;"))
    print(self.check_pass("A-=1+2;"))

@testOf(parser.event_struct)
def test_estruct(self):
    print(self.check_pass("event x(s) {}"))
    print(self.check_pass("event x(s) {hoge();}"))
    print(self.check_pass("""
   event proc(clk.posedge || rst) {
        logic [11:0] count; // writable in this event
   }
"""))


@testOf(parser.module_arg)
def test_module_arg(self):
    print(self.check_pass("input clk"))
    print(self.check_pass("input wire[1:0] A"))
    print(self.check_pass("logic A"))

@testOf(parser.comment)
def test_comment(self):
    print(self.check_pass("// hoge"))
    print(self.check_pass("   //ABC"))
    print(self.check_pass("""

   
   //  foo

"""))

@testOf(parser.module_decl)
def test_module_decl(self):
    # debug(val)
    # debug(parser._range)
    # debug(parser.term)
    # debug(parser.expression)
    # debug(comment)
    parser.enableLog("module_decl")
    parser.enableLog("comment")
    pprint.pprint(self.check_pass("""
module Bridge(input clk,  // a
              input rst,
              BusCh.slave bus,  // channel are flatten in Verilog
              MemIfCh.master mem)
{
    logic [11:0] count;
    state s(clk.posedge || rst);
/* xxx */ logic xxx;  // xxx
/*
  logic yyy;
*/
logic a;
}
""").asList())

@testOf(parser.module_decl)
def test_module_decl2(self):
    pprint.pprint(self.check_pass("""
module Bridge(input clk, 
              input rst,
              BusCh.slave bus,  // channel are flatten in Verilog
              MemIfCh.master mem)
{
    logic [11:0] count; // a

    state s(clk.posedge || rst);
    //always and, always_comb are instantiated 

/*
  event(s) { }
    event(s) {
      //hoge();
    }
    event(s) {
        if(~rst) {
            reset();
            count = 0;
        } else {
            main();
            count += 1;
        }
    }*/

//* hogehoge */
logic a;
}
""").asList(),indent=2,width=100)

@testOf(parser.channel_decl)
def test_channel_decl2(self):
    pprint.pprint(self.check_pass("""
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
            wait(ack);   /* wait */
            en      = 0;
        }

        /* synch */
        function void read(address_t addr)
        {
            en = 1;
            write = 0;
            Addr = addr;
            wait(ack);
        }

        /* async */
        function data_t read(address_t addr)
        {
            en = 1;
            write = 0;
            Addr = addr;
            wait(ack);
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

@testOf(parser.port_decl)
def test_port_decl2(self):
    pprint.pprint(self.check_pass("""
    port master{ 
        output Addr;
        output OutData;
        input  InData;
        output req;
        output wen;
        input  ack;
    }
""").asList())

    pprint.pprint(self.check_pass("""
    port slave {
        input master.OutData  InData;
        output master.InData  OutData;
        output ack;
    }
""").asList())

if __name__=='__main__':
    run_tests()
