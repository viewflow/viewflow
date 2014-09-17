# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'FlowReferencedModel'
        db.create_table('unit_flowreferencedmodel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('flow_cls', self.gf('viewflow.fields.FlowReferenceField')(max_length=250)),
            ('task', self.gf('viewflow.fields.TaskReferenceField')(max_length=150)),
        ))
        db.send_create_signal('unit', ['FlowReferencedModel'])

        # Adding model 'TokenModel'
        db.create_table('unit_tokenmodel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('token', self.gf('viewflow.fields.TokenField')(default='start', max_length=150)),
        ))
        db.send_create_signal('unit', ['TokenModel'])

        # Adding model 'TestProcess'
        db.create_table('unit_testprocess', (
            ('process_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['viewflow.Process'], primary_key=True, unique=True)),
        ))
        db.send_create_signal('unit', ['TestProcess'])


    def backwards(self, orm):
        # Deleting model 'FlowReferencedModel'
        db.delete_table('unit_flowreferencedmodel')

        # Deleting model 'TokenModel'
        db.delete_table('unit_tokenmodel')

        # Deleting model 'TestProcess'
        db.delete_table('unit_testprocess')


    models = {
        'unit.flowreferencedmodel': {
            'Meta': {'object_name': 'FlowReferencedModel'},
            'flow_cls': ('viewflow.fields.FlowReferenceField', [], {'max_length': '250'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'task': ('viewflow.fields.TaskReferenceField', [], {'max_length': '150'})
        },
        'unit.testprocess': {
            'Meta': {'_ormbases': ['viewflow.Process'], 'object_name': 'TestProcess'},
            'process_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['viewflow.Process']", 'primary_key': 'True', 'unique': 'True'})
        },
        'unit.tokenmodel': {
            'Meta': {'object_name': 'TokenModel'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'token': ('viewflow.fields.TokenField', [], {'default': "'start'", 'max_length': '150'})
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

    complete_apps = ['unit']