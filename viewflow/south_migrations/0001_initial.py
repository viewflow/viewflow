# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Process'
        db.create_table('viewflow_process', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('flow_cls', self.gf('viewflow.fields.FlowReferenceField')(max_length=250)),
            ('status', self.gf('django_fsm.FSMField')(max_length=3, default='NEW')),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('finished', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('viewflow', ['Process'])

        # Adding model 'Task'
        db.create_table('viewflow_task', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('flow_task', self.gf('viewflow.fields.TaskReferenceField')(max_length=150)),
            ('flow_task_type', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('status', self.gf('django_fsm.FSMField')(max_length=3, default='NEW', db_index=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('started', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('finished', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('token', self.gf('viewflow.fields.TokenField')(max_length=150, default='start')),
            ('process', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['viewflow.Process'])),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['auth.User'], blank=True)),
            ('external_task_id', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True, db_index=True)),
            ('owner_permission', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
        ))
        db.send_create_signal('viewflow', ['Task'])

        # Adding M2M table for field previous on 'Task'
        m2m_table_name = db.shorten_name('viewflow_task_previous')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_task', models.ForeignKey(orm['viewflow.task'], null=False)),
            ('to_task', models.ForeignKey(orm['viewflow.task'], null=False))
        ))
        db.create_unique(m2m_table_name, ['from_task_id', 'to_task_id'])


    def backwards(self, orm):
        # Deleting model 'Process'
        db.delete_table('viewflow_process')

        # Deleting model 'Task'
        db.delete_table('viewflow_task')

        # Removing M2M table for field previous on 'Task'
        db.delete_table(db.shorten_name('viewflow_task_previous'))


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_set'", 'blank': 'True', 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'user_set'", 'blank': 'True', 'symmetrical': 'False', 'to': "orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'db_table': "'django_content_type'", 'object_name': 'ContentType', 'unique_together': "(('app_label', 'model'),)", 'ordering': "('name',)"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'viewflow.process': {
            'Meta': {'object_name': 'Process'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'finished': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'flow_cls': ('viewflow.fields.FlowReferenceField', [], {'max_length': '250'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django_fsm.FSMField', [], {'max_length': '3', 'default': "'NEW'"})
        },
        'viewflow.task': {
            'Meta': {'object_name': 'Task'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'external_task_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True', 'db_index': 'True'}),
            'finished': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'flow_task': ('viewflow.fields.TaskReferenceField', [], {'max_length': '150'}),
            'flow_task_type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['auth.User']", 'blank': 'True'}),
            'owner_permission': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'previous': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'previous_rel_+'", 'to': "orm['viewflow.Task']"}),
            'process': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['viewflow.Process']"}),
            'started': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django_fsm.FSMField', [], {'max_length': '3', 'default': "'NEW'", 'db_index': 'True'}),
            'token': ('viewflow.fields.TokenField', [], {'max_length': '150', 'default': "'start'"})
        }
    }

    complete_apps = ['viewflow']