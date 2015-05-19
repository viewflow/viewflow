# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DynamicSplitProcess'
        db.create_table('customnode_dynamicsplitprocess', (
            ('process_ptr', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, primary_key=True, to=orm['viewflow.Process'])),
            ('question', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('split_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('customnode', ['DynamicSplitProcess'])

        # Adding model 'Decision'
        db.create_table('customnode_decision', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('process', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['customnode.DynamicSplitProcess'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, null=True, to=orm['auth.User'])),
            ('decision', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('customnode', ['Decision'])


    def backwards(self, orm):
        # Deleting model 'DynamicSplitProcess'
        db.delete_table('customnode_dynamicsplitprocess')

        # Deleting model 'Decision'
        db.delete_table('customnode_decision')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'blank': 'True', 'to': "orm['auth.Permission']"})
        },
        'auth.permission': {
            'Meta': {'object_name': 'Permission', 'unique_together': "(('content_type', 'codename'),)", 'ordering': "('content_type__app_label', 'content_type__model', 'codename')"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'blank': 'True', 'related_name': "'user_set'", 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'blank': 'True', 'related_name': "'user_set'", 'to': "orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'object_name': 'ContentType', 'unique_together': "(('app_label', 'model'),)", 'ordering': "('name',)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'customnode.decision': {
            'Meta': {'object_name': 'Decision'},
            'decision': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'process': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['customnode.DynamicSplitProcess']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'to': "orm['auth.User']"})
        },
        'customnode.dynamicsplitprocess': {
            'Meta': {'object_name': 'DynamicSplitProcess', '_ormbases': ['viewflow.Process']},
            'process_ptr': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'primary_key': 'True', 'to': "orm['viewflow.Process']"}),
            'question': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'split_count': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'viewflow.process': {
            'Meta': {'object_name': 'Process'},
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'auto_now_add': 'True'}),
            'finished': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'null': 'True'}),
            'flow_cls': ('viewflow.fields.FlowReferenceField', [], {'max_length': '250'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django_fsm.FSMField', [], {'max_length': '3', 'default': "'NEW'"})
        }
    }

    complete_apps = ['customnode']
