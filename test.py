# -*- coding: utf-8 -*-
from parser import *

def debug(expr, on=True, name=""):
    if name=="" :
        expr.setName(expr.resultsName)
    else:
        expr.setName(name)
    expr.setDebug(on)

# debug(module_arg_type,True,"module_arg_type")
# debug(module_arg_list,True,"list")

#print(module_arg_type.parseString("BusCh.slave bus"))
print(module_arg_list.parseString("BusCh.slave bus, input clk"))
print(var_decl.parseString("logic [11:0] count;"))
print(expression.parseString("A || B"))
print(expression.parseString("1 + 2 || B"))
print(event_stmt.parseString("event(s) {}"))
print(event_stmt.parseString("event(s) {hoge();}"))
print(module_item.parseString("logic a;"))
print(module_item.parseString("/*hoge*/logic a;"))

pprint.pprint(module_decl.parseString("""
module Bridge(input clk,  // a
              input rst,
              BusCh.slave bus,  // channel are flatten in Verilog
              MemIfCh.master mem)
{
    logic [11:0] count;
    state s(clk.posedge || rst);
/* xxx */ logic xxx; // xxx 

/*
  logic yyy;
*/
logic a;
}
""").asList())


pprint.pprint(module_decl.parseString("""
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


