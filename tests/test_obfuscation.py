import dataclasses
import textwrap
import unittest
from typing import Optional

from pyminifier import obfuscate, obfuscate_file_text


@dataclasses.dataclass
class _Options:
    outfile: Optional[str] = None
    destdir: str = './minified'
    nominify: bool = False
    tabs: bool = False
    bzip2: bool = False
    gzip: bool = False
    lzma: bool = False
    pyz: bool = False
    obfuscate: bool = False
    obf_classes: bool = False
    obf_functions: bool = False
    obf_variables: bool = False
    obf_import_methods: bool = False
    obf_builtins: bool = False
    replacement_length: int = 1
    nonlatin: bool = False
    prepend: Optional[str] = None
    custom_ignores: str = ""


class ObfuscationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.options = _Options(
            obfuscate=False,
            obf_builtins=True,
            replacement_length=10,
            obf_variables=True,
            custom_ignores="exec_output",
        )

    def test_leave_class_attributes(self):
        source = textwrap.dedent(
            """\
            # This is a test to see if bar and baz get obfuscated 
            import unittest 
            
            class Foo:
                bar = True
                
                def get_true(self):
                    this_should_be_obfuscated = True
                    if self.bar and self.baz and this_should_be_obfuscated:
                        return True
                        
                    return False

                baz = True
            
            exec_output = Foo()
            """
        )
        name_generator = obfuscate.obfuscation_machine(
            identifier_length=int(self.options.replacement_length))
        module = 'test_module'

        obfuscated_text = obfuscate_file_text(source, module, name_generator,
                                              self.options)
        self.assertIn('bar', obfuscated_text)
        self.assertIn('baz', obfuscated_text)
        self.assertNotIn('this_should_be_obfuscated', obfuscated_text)

        # If the class variables were obfuscated this raises an AttributeError
        # This creates an exec_output variable of class Foo that we can test.
        exec(obfuscated_text, globals())

        # noinspection PyUnresolvedReferences
        self.assertTrue(exec_output.baz)
        # noinspection PyUnresolvedReferences
        self.assertTrue(exec_output.bar)

    def test_leave_class_attributes_with_kwargs(self):
        self.options.custom_ignores = (
            'output_foo,sum_foo,output_bar,sum_bar,output_testing')
        source = textwrap.dedent(
            """\
            # For some reason there has to be at least one import.
            import unittest
                         
            class Bar:
                def __init__(self, bar_arg, bar_kwarg=None):
                    self._bar_arg = bar_arg
                    self.bar_kwarg = bar_kwarg
                    
                def sum(self):
                    return self._bar_arg + self.bar_kwarg

            class Foo:
                def __init__(self, foo_arg, foo_other_kwarg=None):
                    tmp = 'some_random_assignment'
                    self._foo_arg = foo_arg
                    self.foo_kwarg = foo_other_kwarg
                    
                    
                @property
                def sum(self):
                    return self._foo_arg + self.foo_kwarg
            
            def test_function(testing_input, fn_kwarg=10):
                a = testing_input
                b = a + testing_input + fn_kwarg
                return b
            
            output_foo = Foo(10, foo_other_kwarg=12)
            output_bar = Bar(bar_arg=11, bar_kwarg=13)
            output_testing = test_function(output_foo.foo_kwarg, 
                                           output_bar.bar_kwarg)
            sum_foo = output_foo.sum
            sum_bar = output_bar.sum()
            """
        )
        name_generator = obfuscate.obfuscation_machine(
            identifier_length=int(self.options.replacement_length))
        module = 'test_module'

        obfuscated_text = obfuscate_file_text(source, module, name_generator,
                                              self.options, ignore_length=0)
        self.assertIn('bar_kwarg', obfuscated_text,
                      msg="kwargs do not get obfuscated.")
        self.assertIn('foo_kwarg', obfuscated_text,
                      msg="kwargs do not get obfuscated.")
        # TODO: Enable private attributes to be obfuscated.
        # self.assertNotIn('_bar_arg', obfuscated_text,
        #                  msg="This is private and should get obfuscated.")
        # self.assertNotIn('_foo_arg', obfuscated_text,
        #                  msg="This is private and should get obfuscated.")

        # If the class variables were obfuscated this raises an AttributeError
        # This creates an exec_output variable of class Foo that we can test.
        exec(obfuscated_text, globals())

        # noinspection PyUnresolvedReferences
        self.assertEqual(output_foo.foo_kwarg, 12)
        # noinspection PyUnresolvedReferences
        self.assertEqual(sum_foo, 22)
        # noinspection PyUnresolvedReferences
        self.assertTrue(output_bar.bar_kwarg, 13)
        # noinspection PyUnresolvedReferences
        self.assertEqual(sum_bar, 24)
        # noinspection PyUnresolvedReferences
        self.assertEqual(output_testing, 12 + 12 + 13)

    def test_handles_function_references_from_classes(self):
        source = textwrap.dedent(
            """\
            # This is a test that no references to the function should get
            # obfuscated. 
            import unittest 
            
            def _private_module_function(testing):
                return 10 + testing
            
            class Foo:
                def plus_ten(self, input):
                    inner_variable = [
                        _private_module_function(i) for i in input]
                    return inner_variable
                    
            exec_output = Foo()
            """
        )
        name_generator = obfuscate.obfuscation_machine(
            identifier_length=int(self.options.replacement_length))
        module = 'test_module'

        obfuscated_text = obfuscate_file_text(source, module, name_generator,
                                              self.options)
        self.assertIn('_private_module_function', obfuscated_text)
        self.assertNotIn('inner_variable', obfuscated_text)

        # If the class variables were obfuscated this raises an AttributeError
        # This creates an exec_output variable of class Foo that we can test.
        exec(obfuscated_text, globals())

        # noinspection PyUnresolvedReferences
        self.assertEqual(exec_output.plus_ten([1, 2]), [11, 12])


if __name__ == '__main__':
    unittest.main()
