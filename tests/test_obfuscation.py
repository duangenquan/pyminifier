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
        cls.options = _Options(obfuscate=True, obf_builtins=True,
                               replacement_length=10, obf_variables=True,
                               custom_ignores="exec_output")

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


if __name__ == '__main__':
    unittest.main()
