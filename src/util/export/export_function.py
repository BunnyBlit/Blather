from dataclasses import dataclass
from pathlib import Path
from typing import get_origin, get_args
import inspect
from util.export.export_code import ExportCode

class ExportFunction(ExportCode):
    """ Class to hold onto all the data I need to generate a function. This also
        traces through the code object, identifying dependencies and marking those
        for generation and importing
    Attributes:
        source: the actual code source string, clearing out leading spaces
    """
    source: str

    def __init__(self, code_object):
        super().__init__(code_object)
        # this is gonna kinda suck-- split into lines to identify the smallest amount of leading space
        # then left-justify everything by that much whitespace
        source_lines = [line for line in inspect.getsource(code_object).split("\n")]
        min_leading = min([len(line) - len(line.lstrip()) for line in source_lines if line and not line.isspace()])
        stripped_lines = [line[min_leading:] if len(line) > min_leading else "\n" for line in source_lines]
        self.source = "\n".join(stripped_lines)

    def handle_annotations(self):
        """ Handle the function annotations! Since they're present in the function's source,
            we don't need to generate anything, we just need to make sure we import all the correct
            symbols from the typing module
        """
        annotations = self.src_code.__annotations__
        for name, typing_type in annotations.items():
            _ = self.unpack_nested_annotation(typing_type)

        return self

    def handle_references(self):
        """ Identify references to other, non-local symbols in the function's source code, and mark them
            for importing. Also, generate import statements for them
        """
        # TODO: maybe also check unbound?
        _nonlocals, _globals, _builtins, _unbound = inspect.getclosurevars(self.src_code)
        # at this point, we've already gotten source code and checked for potential unbound references
        # inside the block, so we can just get movin' and groovin'
        for global_name, global_ref in _globals.items():
            self.handle_import(global_name, global_ref)
    
        return self

    def generate_module(self, export_dir:Path):
        """ Actually generate the code at path to write a bare function in its own module
        Params:
            export_dir: the file system directory we want to create a new python file under
        """
        # create required directories
        export_dir.mkdir(parents=True, exist_ok=True)
        # trim a leading dot from the export_module if we need to
        if self.export_module.startswith("."):
            file_name = self.export_module[1:] + ".py"
        else:
            file_name = self.export_module + ".py"
        path = export_dir / file_name #pathin'

        with open(path.resolve(), "w") as f:
            # import statements
            for module, symbols in self.imports.items():
                if module != "__main__" and module != "":
                    # everything ends up in the same directory so we don't need to think to hard
                    # about execution location for imports
                    f.write(f"from {module} import {', '.join(symbols)}\n")
                else:
                    for symbol in symbols:
                        f.write(f"import {symbol}\n")

            f.write("\n")
            f.write(self.source)
            f.write("\n")
    
    @classmethod
    def export(cls, code_object, path:Path):
        """ Export this function to a file located under path
        Params:
            code_object: the function we're trying to export
            path: the location to where we eventually want to write a python file
        """       
        return ExportFunction(code_object)\
            .handle_references()\
            .handle_annotations()\
            .generate_module(path)
