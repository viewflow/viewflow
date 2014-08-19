import copy


class SideItem(object):
    def __init__(self, title, url, parent=None):
        self.title = title
        self.url = url
        self.parent = parent
        self.children = []
        self.is_expanded = False
        self.is_active = False

    def can_view(self, user):
        return True


class Sidebar(object):
    def __init__(self, viewsite=None):
        if viewsite is None:
            from . import viewsite
        self.viewsite = viewsite
        self._sideitems = []

    @property
    def sideitems(self):
        if not self._sideitems:
            for item in self.viewsite.sideitems():
                if item.parent is None:
                    self._sideitems.append(item)
                else:
                    item.parent.children.append(item)
        return self._sideitems

    def render(self, request):
        current_url = request.path
        items = [copy.deepcopy(item) for item in self.sideitems if item.can_view(request.user)]

        # lookup for expanded tree
        expanded_item = None
        expanded_candidates = []
        for item in items:
            if current_url.startswith(item.url):
                subpath = current_url[len(item.url):]
                expanded_candidates.append((item, subpath))

        if expanded_candidates:
            expanded_item = sorted(expanded_candidates, key=lambda data: len(data[1]))[0][0]
            expanded_item.is_expanded = True

        # lookup for active
        if expanded_item:
            active_item = None
            active_candidates = []

            active_candidates.append((expanded_item, current_url[len(expanded_item.url):]))
            for item in expanded_item.children:
                if current_url.startswith(item.url):
                    subpath = current_url[len(item.url):]
                    active_candidates.append((item, subpath))

            if active_candidates:
                active_item = sorted(active_candidates, key=lambda data: len(data[1]))[0][0]
                active_item.is_active = True

        return items
