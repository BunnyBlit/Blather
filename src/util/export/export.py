from pathlib import Path
import inspect
from .export_class import ExportClass
from .export_function import ExportFunction
from .export_named_tuple import ExportNamedTuple

def blog_export(code_object, export_dir=Path("tmp")):
    """ Top level of exporting a code object along with all its dependencies
        Works recursively-- we export the code object, keeping track of all the dependencies,
        and then export all of those files to the export directory
        this leaves us with a flat structure, which is helpful because we pre-generate import statements for code we haven't exported yet
    """
    print(f"Exporting: {code_object}")
    exported = None
    if inspect.isclass(code_object):
        # check inheritance, its how we figure out if a class is a NamedTuple or not
        # FIXME: someday I want to treat NamedTuples how they should be treated (with ExportClass)
        #           but I can't figure it out
        mro = inspect.getmro(code_object)
        # TODO: if I ever dip into multiple inheritance, I'll need to be more complicated here, but roughly, I only care about the first two elements
        if mro[0] != code_object: raise Exception(f"Unexpected MRO for {code_object}:\n{mro}") 
        superclass = mro[1] if mro[1] != object else None
        # if we have tuple as our first class in our chain, we're a named tuple and need 
        # to do custom things
        if superclass == tuple:
            exported = ExportNamedTuple.export(code_object, export_dir)
        else:
            exported = ExportClass.export(code_object, export_dir)
        
    elif inspect.isfunction(code_object):
        exported = ExportFunction.export(code_object, export_dir)

    else:
        print(f"function: {inspect.isfunction(code_object)}")
        print(f"class: {inspect.isclass(code_object)}")
        print(f"module: {inspect.ismodule(code_object)}")
        raise RuntimeError(f"Couldn't export {code_object}")
    
    if exported:
         for differed_export in exported.differed:
            blog_export(differed_export, export_dir)
