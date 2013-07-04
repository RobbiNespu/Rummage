"""
Simple Log
Licensed under MIT
Copyright (c) 2013 Isaac Muse <isaacmuse@gmail.com>
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import codecs

ALL = 0
DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40
CRITICAL = 50

class Log(object):
    def __init__(self, filename=None, format="%(message)s", level=ERROR, filemode="w"):
        if filemode == "w":
            with codecs.open(filename, "w", "utf-8") as f:
                pass
        self.filename = filename
        self.level = level
        self.format = format
        self.save_to_file = self.filename is not None
        self.echo = not self.save_to_file

    def set_echo(self, enable):
        if self.save_to_file:
            self.echo = bool(enable)

    def set_level(self, level):
        self.level = int(level)

    def get_level(self):
        return self.level

    def formater(self, lvl, format, msg, fmt=None):
        return format % {
            "loglevel": lvl,
            "message": str(msg if fmt is None else fmt(msg))
        }

    def debug(self, msg, format="%(loglevel)s: %(message)s\n", echo=True, fmt=None):
        if self.level <= DEBUG:
            self._log(self.formater("DEBUG", format, msg, fmt), echo)

    def info(self, msg, format="%(loglevel)s: %(message)s\n", echo=True, fmt=None):
        if self.level <= INFO:
            self._log(self.formater("INFO", format, msg, fmt), echo)

    def warning(self, msg, format="%(loglevel)s: %(message)s\n", echo=True, fmt=None):
        if self.level <= WARNING:
            self._log(self.formater("WARNING", format, msg, fmt), echo)

    def error(self, msg, format="%(loglevel)s: %(message)s\n", echo=True, fmt=None):
        if self.level <= ERROR:
            self._log(self.formater("ERROR", format, msg, fmt), echo)

    def critical(self, msg, format="%(loglevel)s: %(message)s\n", echo=True, fmt=None):
        if self.level <= CRITICAL:
            self._log(self.formater("CRITICAL", format, msg, fmt), echo)

    def _log(self, msg, echo=True):
        if not (echo and self.echo) and self.save_to_file:
            with codecs.open(self.filename, "a", "utf-8") as f:
                f.write(self.format % {"message": msg})
        if echo and self.echo:
            print(self.format % {"message": msg})

    def read(self):
        txt = ""
        try:
            with codecs.open(self.filename, "r", "utf-8") as f:
                txt = f.read()
        except:
            pass
        return txt


def init_global_log(file_name, level=ERROR):
    global global_log
    global_log = Log(file_name, level=level)


def get_global_log():
    return global_log