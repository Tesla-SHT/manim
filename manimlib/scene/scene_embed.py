import inspect
import pyperclip
import re

from IPython.terminal import pt_inputhooks
from IPython.terminal.embed import InteractiveShellEmbed

from manimlib.animation.fading import VFadeInThenOut
from manimlib.constants import RED
from manimlib.mobject.mobject import Mobject
from manimlib.mobject.frame import FullScreenRectangle
from manimlib.module_loader import ModuleLoader


def interactive_scene_embed(scene):
    scene.stop_skipping()
    scene.update_frame(force_draw=True)

    shell = get_ipython_shell_for_embedded_scene(scene)
    enable_gui(shell, scene)
    ensure_frame_update_post_cell(shell, scene)
    ensure_flash_on_error(shell, scene)

    # Launch shell
    shell()


def get_ipython_shell_for_embedded_scene(scene):
    """
    Create embedded IPython terminal configured to have access to
    the local namespace of the caller
    """
    # Triple back should take us to the context in a user's scene definition
    # which is calling "self.embed"
    caller_frame = inspect.currentframe().f_back.f_back.f_back

    # Update the module's namespace to include local variables
    module = ModuleLoader.get_module(caller_frame.f_globals["__file__"])
    module.__dict__.update(caller_frame.f_locals)
    module.__dict__.update(get_shortcuts(scene))

    return InteractiveShellEmbed(
        user_module=module,
        display_banner=False,
        xmode=scene.embed_exception_mode
    )


def get_shortcuts(scene):
    """
    A few custom shortcuts useful to have in the interactive shell namespace
    """
    return dict(
        play=scene.play,
        wait=scene.wait,
        add=scene.add,
        remove=scene.remove,
        clear=scene.clear,
        focus=scene.focus,
        save_state=scene.save_state,
        reload=scene.reload,
        undo=scene.undo,
        redo=scene.redo,
        i2g=scene.i2g,
        i2m=scene.i2m,
        checkpoint_paste=scene.checkpoint_paste,
    )


def enable_gui(shell, scene):
    """Enables gui interactions during the embed"""
    def inputhook(context):
        while not context.input_is_ready():
            if not scene.is_window_closing():
                scene.update_frame(dt=0)
        if scene.is_window_closing():
            shell.ask_exit()

    pt_inputhooks.register("manim", inputhook)
    shell.enable_gui("manim")


def ensure_frame_update_post_cell(shell, scene):
    """Ensure the scene updates its frame after each ipython cell"""
    def post_cell_func(*args, **kwargs):
        if not scene.is_window_closing():
            scene.update_frame(dt=0, force_draw=True)

    shell.events.register("post_run_cell", post_cell_func)


def ensure_flash_on_error(shell, scene):
    """Flash border, and potentially play sound, on exceptions"""
    def custom_exc(shell, etype, evalue, tb, tb_offset=None):
        # Show the error don't just swallow it
        shell.showtraceback((etype, evalue, tb), tb_offset=tb_offset)
        if scene.embed_error_sound:
            os.system("printf '\a'")
        rect = FullScreenRectangle().set_stroke(RED, 30).set_fill(opacity=0)
        rect.fix_in_frame()
        scene.play(VFadeInThenOut(rect, run_time=0.5))

    shell.set_custom_exc((Exception,), custom_exc)


class CheckpointManager:
    checkpoint_states: dict[str, list[tuple[Mobject, Mobject]]] = dict()

    def checkpoint_paste(self, scene):
        """
        Used during interactive development to run (or re-run)
        a block of scene code.

        If the copied selection starts with a comment, this will
        revert to the state of the scene the first time this function
        was called on a block of code starting with that comment.
        """
        shell = get_ipython()
        if shell is None:
            return

        code_string = pyperclip.paste()

        checkpoint_key = self.get_leading_comment(code_string)
        self.handle_checkpoint_key(scene, checkpoint_key)
        shell.run_cell(code_string)

    @staticmethod
    def get_leading_comment(code_string: str):
        leading_line = code_string.partition("\n")[0].lstrip()
        if leading_line.startswith("#"):
            return leading_line
        return None

    def handle_checkpoint_key(self, scene, key: str):
        if key is None:
            return
        elif key in self.checkpoint_states:
            # Revert to checkpoint
            scene.restore_state(self.checkpoint_states[key])

            # Clear out any saved states that show up later
            all_keys = list(self.checkpoint_states.keys())
            index = all_keys.index(key)
            for later_key in all_keys[index + 1:]:
                self.checkpoint_states.pop(later_key)
        else:
            self.checkpoint_states[key] = scene.get_state()

    def clear_checkpoints(self):
        self.checkpoint_states = dict()
