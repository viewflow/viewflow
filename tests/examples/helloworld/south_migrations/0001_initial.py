# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'HelloWorldProcess'
        db.create_table('helloworld_helloworldprocess', (
            ('process_ptr', self.gf('django.db.models.fields.related.OneToOneField')(primary_key=True, unique=True, to=orm['viewflow.Process'])),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('approved', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('helloworld', ['HelloWorldProcess'])


    def backwards(self, orm):
        # Deleting model 'HelloWorldProcess'
        db.delete_table('helloworld_helloworldprocess')


    models = {
        'helloworld.helloworldprocess': {
            'Meta': {'object_name': 'HelloWorldProcess', '_ormbases': ['viewflow.Process']},
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'process_ptr': ('django.db.models.fields.related.OneToOneField', [], {'primary_key': 'True', 'unique': 'True', 'to': "orm['viewflow.Process']"}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'viewflow.process': {
            'Meta': {'object_name': 'Process'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'finished': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'null': 'True'}),
            'flow_cls': ('viewflow.fields.FlowReferenceField', [], {'max_length': '250'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django_fsm.FSMField', [], {'default': "'NEW'", 'max_length': '3'})
        }
    }

    complete_apps = ['helloworld']