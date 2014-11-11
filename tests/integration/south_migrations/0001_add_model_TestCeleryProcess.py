# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TestCeleryProcess'
        db.create_table('integration_testceleryprocess', (
            ('process_ptr', self.gf('django.db.models.fields.related.OneToOneField')
             (primary_key=True, unique=True, to=orm['viewflow.Process'])),
            ('throw_error', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('integration', ['TestCeleryProcess'])

        db.create_table('integration_brokengateprocess', (
            ('process_ptr', self.gf('django.db.models.fields.related.OneToOneField')
             (primary_key=True, unique=True, to=orm['viewflow.Process'])),
            ('throw_error', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('integration', ['BrokenGateProcess'])

    def backwards(self, orm):
        db.delete_table('integration_testceleryprocess')
        db.delete_table('integration_brokengateprocess')

    models = {
        'integration.testceleryprocess': {
            'Meta': {'_ormbases': ['viewflow.Process'], 'object_name': 'TestCeleryProcess'},
            'process_ptr': ('django.db.models.fields.related.OneToOneField', [],
                            {'primary_key': 'True', 'unique': 'True', 'to': "orm['viewflow.Process']"}),
            'throw_error': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'integration.brokengateprocess': {
            'Meta': {'_ormbases': ['viewflow.Process'], 'object_name': 'TestCeleryProcess'},
            'process_ptr': ('django.db.models.fields.related.OneToOneField', [],
                            {'primary_key': 'True', 'unique': 'True', 'to': "orm['viewflow.Process']"}),
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
