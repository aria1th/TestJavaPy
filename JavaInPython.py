# Java pipeline called from python
import subprocess

JAVA_VERSION = "1.8"
AUTO_INSTALL = True
try:
    import jpype
    import jpype.imports
except (ModuleNotFoundError, ImportError):
    print("JPype not installed, please install JPype to use this feature.")
    if AUTO_INSTALL:
        import pip

        pip.main(['install', 'JPype1'])
        import jpype
        import jpype.imports
    else:
        raise ImportError("JPype not installed, please install JPype to use this feature.")


def precompile(filename, codeblock):
    # Write your Java code to a file
    with open(filename, 'w') as f:
        f.write(codeblock)
    if not jpype.isJVMStarted():
        jpype.startJVM(jpype.getDefaultJVMPath())
    # Compile your Java code using javac
    subprocess.check_call(['javac', '-source', JAVA_VERSION, '-target', JAVA_VERSION, filename])
    # Load your compiled Java class using JPype
    MyClass = jpype.JClass(filename[:-5])
    # We defined public class, so class defined inside codeblock must match with filename.
    return MyClass


def generateCodeBlock(function_name: str = "exampleFunction", args: dict = None, return_type: str = "void",
                      code: str = None, public_clsname: str = "Test", imports: list = None):
    """
    Generate code block for precompile function.
    """
    if args is None:
        args = {}
    code_block = f"""
    {" ".join([f"import {import_};" for import_ in imports])}
    
    public class {public_clsname} {{
        public static {return_type} {function_name}({", ".join([f"{argType} {argName}" for argName, argType in args.items()])}) {{
            {code}
        }}
    }}
    """
    return code_block


# TODO : decorator -> Java code block generator
if __name__ == "__main__":
    example_code = """
    public class Test {
        public static String substring(String targetString, int start) {
            return targetString.substring(start);
        }
    }
    """
    testClass = precompile('Test.java', example_code)
    print(testClass.substring("Hello World", 6))
    # prints World

    generatedCode = generateCodeBlock(function_name="substring", args={"targetString": "String", "start": "int"},
                                      return_type="String", code="return targetString.substring(start);",
                                      public_clsname="Test", imports=["java.lang.String"])
    testClass = precompile('Test.java', generatedCode)
    print(testClass.substring("Hello World", 6))
    # prints World
