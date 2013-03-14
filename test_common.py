# -*- coding: utf-8 -*-
import sys, os, traceback
import unittest
from pyparsing import stringEnd, ParseBaseException, ParseResults

sys.path.append(os.path.join(os.path.dirname(__file__),os.pardir))
#from src import grammar, ast, visitor


def format_traceback_last_of(tb, count):
    def tail(iterator, count):
        import collections, itertools
        num_of_elem = len(iterator) if isinstance(iterator, collections.Sized) else len(list(iterator))
        for x in itertools.islice(iterator, 
                                  (num_of_elem - count if num_of_elem >= count else 0),
                                  None):
            yield x

    return "".join(f for f in traceback.format_list(tail(traceback.extract_tb(tb),count))).strip()
    

def format_error_detail(e):
    msg  = e.msg + "\n"
    msg += e.line + "\n"
    msg += " " * (e.col -1) + "^"
    return msg

class GrammarTestCase(unittest.TestCase):
    def grammar(self):
        pass

    def do_parse(self, text):
        return (self.grammar() + stringEnd).parseString(text)

    def onException(self):
        ex, v, tb = sys.exc_info()
        tb_num = 5
        print("Exception: {cls}: {reason}\n".format(cls=type(v), reason=str(v)))
        print("[Traceback last of {num}]:".format(num=tb_num))
        print(format_traceback_last_of(sys.exc_info()[2], tb_num))

    def check_pass(self, text, expect=None, msg=None):
        print("\ncheck_pass: \"{0}\"".format(text))
        try:
            result = self.do_parse(text)
        except ParseBaseException as e:
            self.setFail()
            print("Error: " + format_error_detail(e))
            return None
        except Exception as e:
            self.setFail()
            self.onException()
            return None
        else:
            print("OK.")
            if expect:
                errmsg = "input = \"{0}\", expect = {1}, result = {2}".format(text, expect, result)
                if msg: 
                    errmsg += "\n   " + msg
                self.assertEqual(result, expect, errmsg)
            else:
                self.assertTrue(result)
        return result

    def check_fail(self, text):
        print("\ncheck_fail: \"{0}\"".format(text))
        try:
            result = self.do_parse(text)
        except ParseBaseException as e:
            print("OK. Error expected: " + format_error_detail(e))
            return None
        except Exception as e:
            self.setFail()
            print("Error. type of exception is NOT expected.")
            self.onException()
            return None
        else:
            self.setFail()
            print("Error. This must be fail...")
            return result

def testOf(grammar):
    def _decolator(test_func):
        class _TestCase(GrammarTestCase):
            def setUp(self):
                print("\n{0}: Test({1}) Start:".format(grammar.resultsName, test_func.__name__))
                self._result = True
            def tearDown(self):
                print("\n{0}: Test({1}) End".format(grammar.resultsName,test_func.__name__))
            def grammar(self):
                return grammar
            def setFail(self):
                self._result = False
            def runTest(self):
                test_func(self)
                if not self._result:
                    self.fail("fail on some test")

        _TestCase.__name__   = test_func.__name__
        _TestCase.__module__ = test_func.__module__
        return _TestCase
    return _decolator

def run_tests(tests=[]):
    import sys
    if len(sys.argv)>1:
        for arg in sys.argv[1:]: tests.append(arg)
    if len(tests)==0:
        unittest.main()
    else:
        import inspect
        modname = inspect.currentframe(1).f_globals["__name__"]
        suite = unittest.defaultTestLoader.loadTestsFromNames([modname + "." + test for test in tests])
        unittest.TextTestRunner().run(suite)

def _print(result):
    if result is None:
        return
    if isinstance(result,ParseResults):
        print(result.asXML())
    print(ast.nodeInfo(result))

def _id_print(result):
    print(result.asXML())
    idAst = result[0]
    if idAst.hasIndex(): print("Index={0}".format(idAst.getIndex()))
    if idAst.hasRange(): print("Range={0}".format(idAst.getRange()))
    if idAst.isHierachical():
        for index,id in enumerate(idAst.each_id()):
            print("  name[{0}] str={1}, repr={2}".format(index,str(id),repr(id)))

def ___stmt_print(obj, level=0, indent=3, out=sys.stdout, debug=False):
    if debug:
        print("_stmt_print: level={0}, obj={1} ({2})".format(level, ast.nodeInfo(obj), type(obj)))
    if isinstance(obj, ParseResults):
        out.write("{spc}{data}:\n".format(spc=" "*indent*level,
                                          data = obj.keys()[0]))
        #out.write(obj.resultsName +':\n')
        for x in obj:
            _stmt_print(x, level+1, indent, debug = debug)
    elif isinstance(obj, ast.IterableAstNode):
        #_stmt_pprint(obj.asList(), level, indent, out)
        import pprint
        out.write("{spc}{data}\n".format(spc=" "*indent*level,
                                       data=pprint.pformat(obj.asList(),indent=indent, width=10)))
    elif obj is not None:
        out.write(str(obj)+'\n')
    else:
        pass # if None


def _stmt_print(result, out=sys.stdout, debug=False):
    if not result:
        return

    if debug:
        print("_stmt_print: level={0}, obj={1} ({2})".format(level, ast.nodeInfo(obj), type(obj)))

    out.write("{0}:\n".format(result.keys()[0]))
    node = result[0]
    node.traverse(visitor.StatementPrettyPrinterVisitor(out),visitor.Arg(None,1))
    #node.traverse(visitor.TraverseTraceVisitor(),visitor.Arg(None,1))


# def _defaultStartDebugAction( instring, loc, expr ):
#     print ("Match " + _ustr(expr) + " at loc " + _ustr(loc) + "(%d,%d)" % ( lineno(loc,instring), col(loc,instring) ))
# def _defaultSuccessDebugAction( instring, startloc, endloc, expr, toks ):
#     print ("Matched " + _ustr(expr) + " -> " + str(toks.asList()))
# def _defaultExceptionDebugAction( instring, loc, expr, exc ):
#     print ("Exception raised:" + _ustr(exc))


def debug(expr, on=True):
    expr.setName(expr.resultsName)
    expr.setDebug(on)
    # def start(*argv):
    #     print("start {0}".format(argv))
    # def success(*argv):
    #     print("success {0}".format(argv))
    # def excep(*argv):
    #     print("excep {0}".format(argv))
    # expr.setDebugActions(start,success,excep)

def fail(expr, action):
    expr.setName(expr.resultsName)
    expr.setFailAction(action)
    
