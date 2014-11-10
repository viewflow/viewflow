# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TestCeleryProcess'
        db.create_table('integration_testceleryprocess', (
            ('process_ptr', self.gf('django.db.models.fields.related.OneToOneField')(primary_key=True, unique=True, to=orm['viewflow.Process'])),
            ('throw_error', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('integration', ['TestCeleryProcess'])


    def backwards(self, orm):
        # Deleting model 'TestCeleryProcess'
        db.delete_table('integration_testceleryprocess')


    models = {
        'integration.testceleryprocess': {
            'Meta': {'_ormbases': ['viewflow.Process'], 'object_name': 'TestCeleryProcess'},
            'process_ptr': ('django.db.models.fields.related.OneToOneField', [], {'primary_key': 'True', 'unique': 'True', 'to': "orm['viewflow.Process']"}),
            'throw_error': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'viewflow.process': {
            'Meta': {'object_name': 'Process'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'finished': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'flow_cls': ('viewflow.fields.FlowReferenceField', [], {'max_length': '250'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django_fsm.FSMField', [], {'max_length': '3', 'default': "'NEW'"})
        }
    }

    complete_apps = ['integration']