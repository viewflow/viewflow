# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Carrier'
        db.create_table('shipment_carrier', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=15)),
        ))
        db.send_create_signal('shipment', ['Carrier'])

        # Adding model 'Insurance'
        db.create_table('shipment_insurance', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('company_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('cost', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('shipment', ['Insurance'])

        # Adding model 'Shipment'
        db.create_table('shipment_shipment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('shipment_no', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('carrier', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['shipment.Carrier'])),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('zipcode', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('need_insurance', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('insurance', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['shipment.Insurance'])),
            ('carrier_quote', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('post_label', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('package_tag', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('shipment', ['Shipment'])

        # Adding model 'ShipmentItem'
        db.create_table('shipment_shipmentitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('shipment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shipment.Shipment'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('quantity', self.gf('django.db.models.fields.IntegerField')(default=1)),
        ))
        db.send_create_signal('shipment', ['ShipmentItem'])

        # Adding model 'ShipmentProcess'
        db.create_table('shipment_shipmentprocess', (
            ('process_ptr', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, to=orm['viewflow.Process'], primary_key=True)),
            ('shipment', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['shipment.Shipment'], blank=True)),
        ))
        db.send_create_signal('shipment', ['ShipmentProcess'])


    def backwards(self, orm):
        # Deleting model 'Carrier'
        db.delete_table('shipment_carrier')

        # Deleting model 'Insurance'
        db.delete_table('shipment_insurance')

        # Deleting model 'Shipment'
        db.delete_table('shipment_shipment')

        # Deleting model 'ShipmentItem'
        db.delete_table('shipment_shipmentitem')

        # Deleting model 'ShipmentProcess'
        db.delete_table('shipment_shipmentprocess')


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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_set'", 'blank': 'True', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_set'", 'blank': 'True', 'to': "orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'db_table': "'django_content_type'", 'object_name': 'ContentType', 'unique_together': "(('app_label', 'model'),)", 'ordering': "('name',)"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'shipment.carrier': {
            'Meta': {'object_name': 'Carrier'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        'shipment.insurance': {
            'Meta': {'object_name': 'Insurance'},
            'company_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'cost': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'shipment.shipment': {
            'Meta': {'object_name': 'Shipment'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'carrier': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['shipment.Carrier']"}),
            'carrier_quote': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'insurance': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['shipment.Insurance']"}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'need_insurance': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'package_tag': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'post_label': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'shipment_no': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'zipcode': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'shipment.shipmentitem': {
            'Meta': {'object_name': 'ShipmentItem'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'quantity': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'shipment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shipment.Shipment']"})
        },
        'shipment.shipmentprocess': {
            'Meta': {'object_name': 'ShipmentProcess', '_ormbases': ['viewflow.Process']},
            'process_ptr': ('django.db.models.fields.related.OneToOneField', [], {'unique': 'True', 'to': "orm['viewflow.Process']", 'primary_key': 'True'}),
            'shipment': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['shipment.Shipment']", 'blank': 'True'})
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

    complete_apps = ['shipment']
