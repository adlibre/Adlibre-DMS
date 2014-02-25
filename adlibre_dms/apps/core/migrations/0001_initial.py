# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DocumentTypeRule'
        db.create_table('core_documenttyperule', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('doccode_type', self.gf('django.db.models.fields.CharField')(default='1', max_length=64)),
            ('sequence_last', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=60)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('regex', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('split_string', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('barcode_format', self.gf('django.db.models.fields.CharField')(default='%s', max_length=100)),
            ('barcode_zfill', self.gf('django.db.models.fields.IntegerField')(default=0, max_length=2, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('core', ['DocumentTypeRule'])

        # Adding model 'DocumentTypeRulePermission'
        db.create_table('core_documenttyperulepermission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('core', ['DocumentTypeRulePermission'])

        # Adding model 'CoreConfiguration'
        db.create_table('core_coreconfiguration', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uncategorized', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.DocumentTypeRule'])),
            ('aui_url', self.gf('django.db.models.fields.CharField')(max_length=150, blank=True)),
        ))
        db.send_create_signal('core', ['CoreConfiguration'])

        # Adding unique constraint on 'CoreConfiguration', fields ['uncategorized', 'aui_url']
        db.create_unique('core_coreconfiguration', ['uncategorized_id', 'aui_url'])

        # Adding model 'DocTags'
        db.create_table('core_doctags', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('doccode', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.DocumentTypeRule'])),
        ))
        db.send_create_signal('core', ['DocTags'])


    def backwards(self, orm):
        # Removing unique constraint on 'CoreConfiguration', fields ['uncategorized', 'aui_url']
        db.delete_unique('core_coreconfiguration', ['uncategorized_id', 'aui_url'])

        # Deleting model 'DocumentTypeRule'
        db.delete_table('core_documenttyperule')

        # Deleting model 'DocumentTypeRulePermission'
        db.delete_table('core_documenttyperulepermission')

        # Deleting model 'CoreConfiguration'
        db.delete_table('core_coreconfiguration')

        # Deleting model 'DocTags'
        db.delete_table('core_doctags')


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'core.coreconfiguration': {
            'Meta': {'unique_together': "(('uncategorized', 'aui_url'),)", 'object_name': 'CoreConfiguration'},
            'aui_url': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'uncategorized': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.DocumentTypeRule']"})
        },
        'core.doctags': {
            'Meta': {'object_name': 'DocTags'},
            'doccode': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.DocumentTypeRule']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'core.documenttyperule': {
            'Meta': {'object_name': 'DocumentTypeRule'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'barcode_format': ('django.db.models.fields.CharField', [], {'default': "'%s'", 'max_length': '100'}),
            'barcode_zfill': ('django.db.models.fields.IntegerField', [], {'default': '0', 'max_length': '2', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'doccode_type': ('django.db.models.fields.CharField', [], {'default': "'1'", 'max_length': '64'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'regex': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'sequence_last': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'split_string': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '60'})
        },
        'core.documenttyperulepermission': {
            'Meta': {'object_name': 'DocumentTypeRulePermission'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_tagged_items'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_items'", 'to': "orm['taggit.Tag']"})
        }
    }

    complete_apps = ['core']