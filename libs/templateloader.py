from django.conf import settings
from django.template import TemplateDoesNotExist
from django.template.loader import BaseLoader
from django.utils._os import safe_join
import os

class MvcTemplateLoader(BaseLoader):
    "A custom template loader for the MVCEngine framework."

    is_usable = True

    __view_paths = None

    def __init__(self, views_path):
        self.views_path = views_path
        # We only need to instantiate the view_paths class variable once.
        if MvcTemplateLoader.__view_paths is None:
            temp_paths = []
            for each_path in os.listdir(views_path):
                # We want to skip hidden directories, so avoid anything that starts with .
                # This works on both Windows and *NIX, but could it fail for other OS's?
                if not each_path.startswith('.'):
                    full_path = os.path.join(views_path, each_path)
                    if each_path == "shared":
                        # The shared directory is special. Since templates in many other directories will be
                        # inheriting from or including templates there, it should come second, right after the
                        # root views directory. For now, it will be first.
                        temp_paths.insert(0, full_path)
                    else:
                        temp_paths.append(full_path)
            # The root views_path itself will always be first in order to give resolution precendence to templates
            # that are specified with a parent directory. In other words, home/index.html will be immediately
            # resolved with no ambiguity; whereas, index.html could resolve as bar/index.html rather than
            # foo/index.html.
            #temp_paths.insert(0, views_path)
            temp_paths.append(views_path)
            MvcTemplateLoader.__view_paths = temp_paths


    def get_template_sources(self, template_name):
        for template_dir in MvcTemplateLoader.__view_paths:
            try:
                yield safe_join(template_dir, template_name)
            except UnicodeDecodeError:
                # The template dir name was a bytestring that wasn't valid UTF-8.
                raise
            except ValueError:
                # The joined path was located outside of this particular
                # template_dir (it might be inside another one, so this isn't
                # fatal).
                pass

    def load_template_source(self, template_name, template_dirs=None):
        tried = []
        for filepath in self.get_template_sources(template_name):
            try:
                file = open(filepath)
                try:
                    return (file.read().decode(settings.FILE_CHARSET), filepath)
                finally:
                    file.close()
            except IOError:
                tried.append(filepath)

        error_msg = "Could not find %s in any of the views subdirectories." % template_name
        raise TemplateDoesNotExist(error_msg)
    load_template_source.is_usable = True

_loader = MvcTemplateLoader

