import traceback
import sys

def python():
        import code

        # Set up a dictionary to serve as the environment for the shell.
        imported_objects = {}

        
        for pythonrc in OrderedSet([os.environ.get("PYTHONSTARTUP"), os.path.expanduser('~/.pythonrc.py')]):
            if not pythonrc:
                continue
            if not os.path.isfile(pythonrc):
                continue
            with open(pythonrc) as handle:
                pythonrc_code = handle.read()
            # Match the behavior of the cpython shell where an error in
            # PYTHONSTARTUP prints an exception and continues.
            try:
                exec(compile(pythonrc_code, pythonrc, 'exec'), imported_objects)
            except Exception:
                traceback.print_exc()

        # By default, this will set up readline to do tab completion and to read and
        # write history to the .python_history file, but this can be overridden by
        # $PYTHONSTARTUP or ~/.pythonrc.py.
        try:
            hook = sys.__interactivehook__
        except AttributeError:
            # Match the behavior of the cpython shell where a missing
            # sys.__interactivehook__ is ignored.
            pass
        else:
            try:
                hook()
            except Exception:
                # Match the behavior of the cpython shell where an error in
                # sys.__interactivehook__ prints a warning and the exception
                # and continues.
                print('Failed calling sys.__interactivehook__')
                traceback.print_exc()

        # Set up tab completion for objects imported by $PYTHONSTARTUP or
        # ~/.pythonrc.py.
        try:
            # 记录之前写过的代码，提升用户体验
            import readline
            import rlcompleter
            readline.set_completer(rlcompleter.Completer(imported_objects).complete)
        except ImportError:
            pass
        
        # imported_objects.update(test="你好")  这样进入的交互式界面，可以直接输入:test,输出:你好
        # Start the interactive interpreter.
        # 进入交互模式
        code.interact(local=imported_objects)


python()        