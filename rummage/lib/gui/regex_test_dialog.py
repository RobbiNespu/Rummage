"""
Regex Test dialog.

Licensed under MIT
Copyright (c) 2013 - 2015 Isaac Muse <isaacmuse@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions
of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
"""
from __future__ import unicode_literals
import re
import traceback
import wx
import os
import functools
import codecs
import time
from backrefs import bre, bregex
from . import gui
from .controls.pick_button import PickButton, pick_extend
from .settings import Settings
from . import data
from .localization import _
from .. import rumcore
from .. import util


class RegexTestDialog(gui.RegexTestDialog):
    """Regex test dialog."""

    def __init__(self, parent):
        """Init Regex Test Dialog object."""

        super(RegexTestDialog, self).__init__(None)
        if util.platform() == "windows":
            self.SetDoubleBuffered(True)
        self.localize()

        self.SetIcon(
            data.get_image('rummage_large.png').GetIcon()
        )
        self.parent = parent
        self.regex_mode = Settings.get_regex_mode()
        self.regex_version = Settings.get_regex_version()
        self.imported_plugin = {}

        # Ensure OS selectall shortcut works in text inputs
        self.set_keybindings(
            [
                (wx.ACCEL_CMD if util.platform() == "osx" else wx.ACCEL_CTRL, ord('A'), self.on_textctrl_selectall)
            ]
        )

        pick_extend(self.m_replace_plugin_dir_picker, PickButton)
        self.m_replace_plugin_dir_picker.pick_init(
            PickButton.FILE_TYPE,
            self.SELECT_SCRIPT,
            default_path=os.path.join(Settings.get_config_folder(), 'plugins'),
            pick_change_evt=self.on_replace_plugin_dir_changed
        )

        self.m_regex_search_checkbox.SetValue(parent.m_regex_search_checkbox.GetValue())
        self.m_case_checkbox.SetValue(parent.m_case_checkbox.GetValue())
        self.m_dotmatch_checkbox.SetValue(parent.m_dotmatch_checkbox.GetValue())
        self.m_unicode_checkbox.SetValue(parent.m_unicode_checkbox.GetValue())
        self.m_replace_plugin_checkbox.SetValue(parent.m_replace_plugin_checkbox.GetValue())
        if self.regex_mode in rumcore.REGEX_MODES:
            self.m_bestmatch_checkbox.SetValue(parent.m_bestmatch_checkbox.GetValue())
            self.m_enhancematch_checkbox.SetValue(parent.m_enhancematch_checkbox.GetValue())
            self.m_word_checkbox.SetValue(parent.m_word_checkbox.GetValue())
            self.m_reverse_checkbox.SetValue(parent.m_reverse_checkbox.GetValue())
            self.m_posix_checkbox.SetValue(parent.m_posix_checkbox.GetValue())
            self.m_format_replace_checkbox.SetValue(parent.m_format_replace_checkbox.GetValue())
            if self.regex_version == 0:
                self.m_fullcase_checkbox.SetValue(parent.m_fullcase_checkbox.GetValue())
            else:
                self.m_fullcase_checkbox.Hide()
        else:
            self.m_bestmatch_checkbox.Hide()
            self.m_enhancematch_checkbox.Hide()
            self.m_word_checkbox.Hide()
            self.m_reverse_checkbox.Hide()
            self.m_posix_checkbox.Hide()
            self.m_format_replace_checkbox.Hide()
            self.m_fullcase_checkbox.Hide()

        if not self.parent.m_replace_plugin_checkbox.GetValue():
            self.m_replace_plugin_dir_picker.Hide()

        self.regex_event_code = -1
        self.testing = False
        self.init_regex_timer()
        self.start_regex_timer()

        self.m_regex_text.SetValue(
            parent.m_searchfor_textbox.GetValue() if not parent.m_chains_checkbox.GetValue() else ""
        )
        self.m_replace_text.SetValue(
            parent.m_replace_textbox.GetValue() if not parent.m_chains_checkbox.GetValue() else ""
        )

        self.refresh_localization()

        # Ensure good sizing of frame
        self.m_test_text.SetMinSize(wx.Size(-1, 60))
        self.m_test_replace_text.SetMinSize(wx.Size(-1, 60))
        self.m_tester_panel.Fit()
        self.Fit()
        self.SetMinSize(self.GetSize())

    def localize(self):
        """Translate strings."""

        self.TITLE = _("Regex Tester")
        self.OKAY = _("Use")
        self.CLOSE = _("Close")
        self.SELECT_SCRIPT = _("Select replace script")
        self.REGEX = _("Regex search")
        self.CASE = _("Search case-sensitive")
        self.DOT = _("Dot matches newline")
        self.UNICODE = _("Use Unicode properties")
        self.BEST_MATCH = _("Best fuzzy match")
        self.FUZZY_FIT = _("Improve fuzzy fit")
        self.WORD = _("Unicode word break")
        self.REVERSE = _("Reverse match")
        self.POSIX = _("Use POSIX matching")
        self.FORMAT = _("Format style replacements")
        self.FULLCASE = _("Full case-folding")
        self.TEXT = _("Text")
        self.RESULT = _("Result")
        self.REGEX_INPUT = _("Regex Input")
        self.FIND = _("Find")
        self.USE_REPLACE_PLUGIN = _("Use replace plugin")
        self.REPLACE_PLUGIN = _("Replace plugin")
        self.REPLACE = _("Replace")

    def refresh_localization(self):
        """Localize dialog."""

        self.SetTitle(self.TITLE)
        self.m_use_regex_button.SetLabel(self.OKAY)
        self.m_close_button.SetLabel(self.CLOSE)
        self.m_regex_search_checkbox.SetLabel(self.REGEX)
        self.m_case_checkbox.SetLabel(self.CASE)
        self.m_dotmatch_checkbox.SetLabel(self.DOT)
        self.m_unicode_checkbox.SetLabel(self.UNICODE)
        self.m_bestmatch_checkbox.SetLabel(self.BEST_MATCH)
        self.m_enhancematch_checkbox.SetLabel(self.FUZZY_FIT)
        self.m_word_checkbox.SetLabel(self.WORD)
        self.m_reverse_checkbox.SetLabel(self.REVERSE)
        self.m_posix_checkbox.SetLabel(self.POSIX)
        self.m_format_replace_checkbox.SetLabel(self.FORMAT)
        self.m_fullcase_checkbox.SetLabel(self.FULLCASE)
        self.m_test_text.GetContainingSizer().GetStaticBox().SetLabel(self.TEXT)
        self.m_test_replace_text.GetContainingSizer().GetStaticBox().SetLabel(self.RESULT)
        main_sizer = self.m_tester_panel.GetSizer()
        main_sizer.GetItem(2).GetSizer().GetStaticBox().SetLabel(self.REGEX_INPUT)
        self.m_find_label.SetLabel(self.FIND)
        self.m_replace_plugin_checkbox.SetLabel(self.USE_REPLACE_PLUGIN)
        if self.parent.m_replace_plugin_checkbox.GetValue():
            self.m_replace_label.SetLabel(self.REPLACE_PLUGIN)
        else:
            self.m_replace_label.SetLabel(self.REPLACE)
        self.Fit()

    def init_regex_timer(self):
        """Init the update Timer object]."""

        self.regex_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.regex_event, self.regex_timer)

    def regex_expand(self, m, replace):
        """Regex module expand."""

        return m.expandf(replace) if self.m_format_replace_checkbox.GetValue() else m.expand(replace)

    def start_regex_timer(self):
        """Start update timer."""

        if not self.regex_timer.IsRunning():
            self.regex_timer.Start(500)

    def stop_regex_timer(self):
        """Stop update timer."""

        if self.regex_timer.IsRunning():
            self.regex_timer.Stop()

    def regex_event(self, event):
        """Event for regex."""

        if self.regex_event_code == 0:
            if not self.testing:
                self.test_regex()
                self.regex_event_code -= 1
            else:
                event.Skip()
        else:
            if self.regex_event_code > 0:
                self.regex_event_code = 0
            event.Skip()

    def set_keybindings(self, keybindings):
        """Set keybindings for frame."""

        tbl = []
        for binding in keybindings:
            keyid = wx.NewId()
            self.Bind(wx.EVT_MENU, binding[2], id=keyid)
            tbl.append((binding[0], binding[1], keyid))

        if len(keybindings):
            self.SetAcceleratorTable(wx.AcceleratorTable(tbl))

    def reset_highlights(self):
        """Reset highlights."""

        # Reset Colors
        self.m_test_text.SetStyle(
            0,
            self.m_test_text.GetLastPosition(),
            wx.TextAttr(wx.Colour(0, 0, 0), colBack=wx.Colour(255, 255, 255))
        )

    def import_plugin(self, script):
        """Import replace plugin."""

        import imp

        if script not in self.imported_plugin:
            self.imported_plugin = {}
            module = imp.new_module(script)
            with open(script, 'rb') as f:
                encoding = rumcore.text_decode._special_encode_check(f.read(256), '.py')
            with codecs.open(script, 'r', encoding=encoding.encode) as f:
                exec(
                    compile(
                        f.read(),
                        script,
                        'exec'
                    ),
                    module.__dict__
                )

            # Don't let the module get garbage collected
            # We will remove references when we are done with it.
            self.imported_plugin[script] = module

        return self.imported_plugin[script].get_replace()

    def test_regex(self):
        """Test and highlight search results in content buffer."""

        # Replace functions
        def replace_literal(m, replace=None):
            """Replace literal."""
            return replace

        def replace_bregex_format(m, replace=None):
            """Replace for bregex format."""
            return m.expandf(replace)

        def replace_regex(m, replace=None):
            """Replace for regex."""
            return self.regex_expand(m, replace)

        def replace_re(m, replace=None):
            """Replace for re."""
            return m.expand(replace)

        if not self.testing:
            self.testing = True
            if self.m_regex_text.GetValue() == "":
                self.m_test_text.SetStyle(
                    0,
                    self.m_test_text.GetLastPosition(),
                    wx.TextAttr(wx.Colour(0, 0, 0), colBack=wx.Colour(255, 255, 255))
                )
                self.testing = False
                return

            is_regex = self.m_regex_search_checkbox.GetValue()

            if self.regex_mode in rumcore.REGEX_MODES:
                import regex

                engine = bregex if self.regex_mode == rumcore.BREGEX_MODE else regex
                rum_flags = rumcore.MULTILINE
                flags = engine.MULTILINE
                if self.regex_version == 1:
                    flags |= engine.VERSION1
                    rum_flags |= rumcore.VERSION1
                else:
                    flags |= engine.VERSION0
                    rum_flags |= rumcore.VERSION0
                if not self.m_case_checkbox.GetValue():
                    flags |= engine.IGNORECASE
                    rum_flags |= rumcore.IGNORECASE
                if self.m_unicode_checkbox.GetValue():
                    flags |= engine.UNICODE
                    rum_flags |= rumcore.UNICODE
                else:
                    flags |= engine.ASCII
                    rum_flags |= rumcore.ASCII
                if flags & engine.VERSION0 and self.m_fullcase_checkbox.GetValue():
                    flags |= engine.FULLCASE
                    rum_flags |= rumcore.FULLCASE
                if is_regex:
                    if self.m_dotmatch_checkbox.GetValue():
                        flags |= engine.DOTALL
                        rum_flags |= rumcore.DOTALL
                    if self.m_bestmatch_checkbox.GetValue():
                        flags |= engine.BESTMATCH
                        rum_flags |= rumcore.BESTMATCH
                    if self.m_enhancematch_checkbox.GetValue():
                        flags |= engine.ENHANCEMATCH
                        rum_flags |= rumcore.ENHANCEMATCH
                    if self.m_word_checkbox.GetValue():
                        flags |= engine.WORD
                        rum_flags |= rumcore.WORD
                    if self.m_reverse_checkbox.GetValue():
                        flags |= engine.REVERSE
                        rum_flags |= rumcore.REVERSE
                    if self.m_posix_checkbox.GetValue():
                        flags |= engine.POSIX
                        rum_flags |= rumcore.POSIX
                    search_text = self.m_regex_text.GetValue()
                else:
                    search_text = engine.escape(self.m_regex_text.GetValue())
            else:
                engine = bre if self.regex_mode == rumcore.BRE_MODE else re

                flags = engine.MULTILINE
                rum_flags = rumcore.MULTILINE
                if not self.m_case_checkbox.GetValue():
                    flags |= engine.IGNORECASE
                    rum_flags |= rumcore.IGNORECASE
                if self.m_unicode_checkbox.GetValue():
                    flags |= engine.UNICODE
                    rum_flags |= rumcore.UNICODE
                else:
                    if util.PY3:
                        flags |= engine.ASCII
                    rum_flags |= rumcore.ASCII
                if is_regex:
                    if self.m_dotmatch_checkbox.GetValue():
                        flags |= engine.DOTALL
                        rum_flags |= rumcore.DOTALL
                    search_text = self.m_regex_text.GetValue()
                else:
                    search_text = engine.escape(self.m_regex_text.GetValue())

            try:
                if self.regex_mode == rumcore.BREGEX_MODE:
                    test = bregex.compile_search(search_text, flags)
                elif self.regex_mode == rumcore.REGEX_MODE:
                    test = regex.compile(search_text, flags)
                elif self.regex_mode == rumcore.BRE_MODE:
                    test = bre.compile_search(search_text, flags)
                else:
                    test = re.compile(search_text, flags)
            except Exception:
                self.reset_highlights()
                self.m_test_replace_text.SetValue(
                    self.m_test_text.GetValue() if self.m_replace_text.GetValue() else ''
                )
                self.testing = False
                return

            text = self.m_test_text.GetValue()

            replace_test = None
            try:
                rpattern = self.m_replace_text.GetValue()
                if rpattern and self.m_replace_plugin_checkbox.GetValue():
                    assert os.path.exists(rpattern), TypeError
                    assert os.path.isfile(rpattern), TypeError
                    file_info = rumcore.FileInfoRecord(
                        0,
                        "TestBuffer.txt",
                        len(text),
                        time.ctime(),
                        time.ctime(),
                        rumcore.text_decode.Encoding('unicode', None)
                    )
                    replace_test = self.import_plugin(rpattern)(file_info, rum_flags).replace
                elif rpattern:
                    if not is_regex:
                        replace_test = functools.partial(replace_literal, replace=rpattern)
                    elif self.regex_mode == rumcore.BREGEX_MODE:
                        if self.m_format_replace_checkbox.GetValue():
                            replace_test = functools.partial(replace_bregex_format, replace=rpattern)
                        else:
                            replace_test = bregex.compile_replace(test, self.m_replace_text.GetValue())
                    elif self.regex_mode == rumcore.REGEX_MODE:
                        replace_test = functools.partial(replace_regex, replace=rpattern)
                    elif self.regex_mode == rumcore.BRE_MODE:
                        replace_test = bre.compile_replace(test, self.m_replace_text.GetValue())
                    else:
                        replace_test = functools.partial(replace_re, replace=rpattern)
            except Exception as e:
                print(e)
                pass

            try:
                # Reset Colors
                self.reset_highlights()

                new_text = []
                offset = 0
                for m in test.finditer(text):
                    try:
                        if replace_test:
                            new_text.append(text[offset:m.start(0)])
                            new_text.append(replace_test(m))
                            offset = m.end(0)
                    except Exception as e:
                        print(e)
                        replace_test = None
                    self.m_test_text.SetStyle(
                        m.start(0),
                        m.end(0),
                        wx.TextAttr(wx.Colour(0, 0, 0), colBack=wx.Colour(0xFF, 0xCC, 0x00))
                    )
                if replace_test:
                    new_text.append(text[offset:])
                self.m_test_replace_text.SetValue(''.join(new_text))

            except Exception:
                print(str(traceback.format_exc()))
            self.testing = False

    def regex_start_event(self, event):
        """Regex start event."""

        self.regex_event_code += 1
        event.Skip()

    def on_textctrl_selectall(self, event):
        """Selectall content of textctrl."""

        text = self.FindFocus()
        if isinstance(text, wx.TextCtrl):
            text.SelectAll()
        event.Skip()

    def on_close(self, event):
        """Enable parent Rummage Dialog "Test Regex" button on close."""

        self.stop_regex_timer()
        event.Skip()

    def on_use(self, event):
        """Copy regex to parent Rummage Dialog search input."""

        # Disable chain mode if enabled
        if self.parent.m_chains_checkbox.GetValue():
            self.parent.m_chains_checkbox.SetValue(False)
            self.parent.on_chain_toggle(None)

        # Turn off replace plugin if enabled
        if self.parent.m_replace_plugin_checkbox.GetValue() != self.m_replace_plugin_checkbox.GetValue():
            self.parent.m_replace_plugin_checkbox.SetValue(self.m_replace_plugin_checkbox.GetValue())
            self.parent.on_plugin_function_toggle(None)

        # Set "regex search" true if not already
        if self.parent.m_regex_search_checkbox.GetValue() != self.m_regex_search_checkbox.GetValue():
            self.parent.m_regex_search_checkbox.SetValue(self.m_regex_search_checkbox.GetValue())
            self.parent.on_regex_search_toggle(None)

        self.parent.m_searchfor_textbox.SetValue(self.m_regex_text.GetValue())
        self.parent.m_replace_textbox.SetValue(self.m_replace_text.GetValue())
        self.parent.m_unicode_checkbox.SetValue(self.m_unicode_checkbox.GetValue())
        self.parent.m_case_checkbox.SetValue(self.m_case_checkbox.GetValue())
        self.parent.m_dotmatch_checkbox.SetValue(self.m_dotmatch_checkbox.GetValue())
        if self.regex_mode in rumcore.REGEX_MODES:
            self.parent.m_bestmatch_checkbox.SetValue(self.m_bestmatch_checkbox.GetValue())
            self.parent.m_enhancematch_checkbox.SetValue(self.m_enhancematch_checkbox.GetValue())
            self.parent.m_word_checkbox.SetValue(self.m_word_checkbox.GetValue())
            self.parent.m_reverse_checkbox.SetValue(self.m_reverse_checkbox.GetValue())
            self.parent.m_posix_checkbox.SetValue(self.m_posix_checkbox.GetValue())
            self.parent.m_format_replace_checkbox.SetValue(self.m_format_replace_checkbox.GetValue())
            if self.regex_version == 0:
                self.parent.m_fullcase_checkbox.SetValue(self.m_fullcase_checkbox.GetValue())
        self.Close()

    def on_cancel(self, event):
        """Close dialog."""

        self.Close()

    def on_test_changed(self, event):
        """On test change event."""

        if not self.testing:
            self.regex_start_event(event)
        else:
            event.Skip()

    def on_replace_plugin_dir_changed(self, event):
        """Handle replace plugin dir change."""

        pth = event.target
        if pth is not None and os.path.exists(pth):
            self.m_replace_text.SetValue(pth)

    def on_replace_plugin_toggle(self, event):
        """Handle plugin function toggle."""

        if self.m_replace_plugin_checkbox.GetValue():
            self.m_replace_label.SetLabel(self.REPLACE_PLUGIN)
            self.m_replace_plugin_dir_picker.Show()
        else:
            self.m_replace_label.SetLabel(self.REPLACE)
            self.m_replace_plugin_dir_picker.Hide()
        self.m_tester_panel.GetSizer().Layout()

        self.regex_start_event(event)

    def on_replace_changed(self, event):
        """On replace pattern change."""

        if self.m_replace_plugin_checkbox.GetValue():
            pth = self.m_replace_text.GetValue()
            if os.path.exists(pth) and os.path.isfile(pth):
                self.regex_start_event(event)
        else:
            self.regex_start_event(event)

    on_regex_changed = regex_start_event

    on_regex_toggle = regex_start_event

    on_case_toggle = regex_start_event

    on_dot_toggle = regex_start_event

    on_unicode_toggle = regex_start_event

    on_bestmatch_toggle = regex_start_event

    on_enhancematch_toggle = regex_start_event

    on_word_toggle = regex_start_event

    on_reverse_toggle = regex_start_event

    on_posix_toggle = regex_start_event

    on_format_replace_toggle = regex_start_event

    on_fullcase_toggle = regex_start_event
