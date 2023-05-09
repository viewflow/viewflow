from .celery import app as celery_app

__all__ = ("celery_app",)


def print_urls():
    """For debug purpose"""

    def list_urls(urls, parent_pattern=""):
        for entry in urls:
            full_pattern = parent_pattern + entry.pattern.regex.pattern
            if hasattr(entry, "url_patterns"):
                list_urls(entry.url_patterns, full_pattern)
            else:
                print(f"{entry.name or '<unnamed>'}: {full_pattern}")

    from django.conf import settings

    urlconf = __import__(settings.ROOT_URLCONF, {}, {}, [""])
    list_urls(urlconf.urlpatterns)
