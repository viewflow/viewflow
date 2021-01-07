import django

from django.db import models
from django.urls import include, re_path
from django.contrib import admin
from django.contrib.auth.models import User
from django.test import TestCase

from viewflow.templatetags import base


class Test(TestCase):
    def setUp(self):
        self.related = TemplateTagProcessRelated.objects.create(related_content='related')
        self.child_process = ChildTemplateTagProcess.objects.create(
            content='child_process', child_content='child process content', related=self.related)
        self.entity1 = TemplateTagProcessEntity.objects.create(process=self.child_process, content='entity1')
        self.entity2 = TemplateTagProcessEntity.objects.create(
            process=self.child_process, content='entity2', circled_link=self.entity1)

    def test_get_model_display_data_for_superuser(self):
        self.superuser = User.objects.create(username='superuser', is_superuser=True)
        data = base.get_model_display_data(self.child_process, self.superuser)

        if django.VERSION >= (1, 9):
            self.assertEqual(data, [
                ('Child Template Tag Process', [
                    ('Content', 'child_process'),
                    ('Child Content', 'child process content')],
                 '/admin/tests/childtemplatetagprocess/1/change/'),
                ('Related', [
                    ('Related Content', 'related')],
                 '/admin/tests/templatetagprocessrelated/1/change/'),
                ('Template Tag Process Entity', [
                    ('Content', 'entity1')],
                 '/admin/tests/templatetagprocessentity/1/change/'),
                ('Template Tag Process Entity',
                 [('Content', 'entity2')],
                 '/admin/tests/templatetagprocessentity/2/change/'),
                ('Template Tag Process',
                 [('Content', 'child_process')],
                 None)])
        else:
            # older django has different andmin change page urls
            self.assertEqual(data, [
                ('Child Template Tag Process', [
                    ('Content', 'child_process'),
                    ('Child Content', 'child process content')],
                 '/admin/tests/childtemplatetagprocess/1/'),
                ('Related', [
                    ('Related Content', 'related')],
                 '/admin/tests/templatetagprocessrelated/1/'),
                ('Template Tag Process Entity', [
                    ('Content', 'entity1')],
                 '/admin/tests/templatetagprocessentity/1/'),
                ('Template Tag Process Entity',
                 [('Content', 'entity2')],
                 '/admin/tests/templatetagprocessentity/2/'),
                ('Template Tag Process',
                 [('Content', 'child_process')],
                 None)])

    def test_get_model_display_data_for_unpriviledged_ser(self):
        self.user = User.objects.create(username='ruser', is_superuser=False)
        data = base.get_model_display_data(self.child_process, self.user)

        self.assertEqual(data, [
            ('Child Template Tag Process', [
                ('Content', 'child_process'),
                ('Child Content', 'child process content')],
             None),
            ('Related', [
                ('Related Content', 'related')],
             None),
            ('Template Tag Process Entity', [
                ('Content', 'entity1')],
             None),
            ('Template Tag Process Entity',
             [('Content', 'entity2')],
             None),
            ('Template Tag Process',
             [('Content', 'child_process')],
             None)])


class TemplateTagProcessRelated(models.Model):
    related_content = models.CharField(max_length=50)


class TemplateTagProcess(models.Model):
    content = models.CharField(max_length=50)
    related = models.ForeignKey(TemplateTagProcessRelated, on_delete=models.CASCADE)


class ChildTemplateTagProcess(TemplateTagProcess):
    child_content = models.CharField(max_length=50)


class TemplateTagProcessEntity(models.Model):
    content = models.CharField(max_length=50)
    process = models.ForeignKey(TemplateTagProcess, on_delete=models.CASCADE)
    circled_link = models.ForeignKey(
        'TemplateTagProcessEntity', null=True, on_delete=models.CASCADE)


admin.site.register(TemplateTagProcessRelated)
admin.site.register(ChildTemplateTagProcess)
admin.site.register(TemplateTagProcessEntity)


urlpatterns = [
    re_path(r'^admin/', admin.site.urls)
]

try:
    from django.test import override_settings
    Test = override_settings(ROOT_URLCONF=__name__)(Test)
except ImportError:
    """
    django 1.6
    """
    Test.urls = __name__
