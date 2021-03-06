"""
sentry.templatetags.sentry_plugins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2014 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from django import template

from sentry.plugins import plugins
from sentry.utils.safe import safe_execute

register = template.Library()


@register.filter
def get_actions(group, request):
    project = group.project

    action_list = []
    for plugin in plugins.for_project(project):
        results = safe_execute(plugin.actions, request, group, action_list)

        if not results:
            continue

        action_list = results

    return [(a[0], a[1], request.path == a[1]) for a in action_list]


@register.filter
def get_panels(group, request):
    project = group.project

    panel_list = []
    for plugin in plugins.for_project(project):
        results = safe_execute(plugin.panels, request, group, panel_list)

        if not results:
            continue

        panel_list = results

    return [(p[0], p[1], request.path == p[1]) for p in panel_list]


@register.filter
def get_widgets(group, request):
    project = group.project

    for plugin in plugins.for_project(project):
        resp = safe_execute(plugin.widget, request, group)

        if resp:
            yield resp.render(request)


@register.filter
def get_tags(group, request=None):
    project = group.project

    tag_list = []
    for plugin in plugins.for_project(project):
        results = safe_execute(plugin.tags, request, group, tag_list)

        if not results:
            continue

        tag_list = results

    for tag in tag_list:
        yield tag


@register.simple_tag
def handle_before_events(request, event_list):
    if not event_list:
        return ''

    if not hasattr(event_list, '__iter__'):
        project = event_list.project
        event_list = [event_list]
    else:
        projects = set(e.project for e in event_list)
        if len(projects) == 1:
            project = projects.pop()
        else:
            project = None

    for plugin in plugins.for_project(project):
        safe_execute(plugin.before_events, request, event_list)

    return ''


@register.filter
def get_plugins(project):
    results = []
    for plugin in plugins.for_project(project):
        if plugin.has_project_conf():
            results.append(plugin)
    return results


@register.filter
def get_plugins_with_status(project):
    return [
        (plugin, safe_execute(plugin.is_enabled, project))
        for plugin in plugins.all()
        if plugin.can_enable_for_projects()
    ]
