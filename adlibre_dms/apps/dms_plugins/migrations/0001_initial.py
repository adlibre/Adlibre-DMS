# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DoccodePluginMapping'
        db.create_table('dms_plugins_doccodepluginmapping', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('doccode', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['core.DocumentTypeRule'], unique=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('dms_plugins', ['DoccodePluginMapping'])

        # Adding M2M table for field before_storage_plugins on 'DoccodePluginMapping'
        m2m_table_name = db.shorten_name('dms_plugins_doccodepluginmapping_before_storage_plugins')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('doccodepluginmapping', models.ForeignKey(orm['dms_plugins.doccodepluginmapping'], null=False)),
            ('plugin', models.ForeignKey(orm['djangoplugins.plugin'], null=False))
        ))
        db.create_unique(m2m_table_name, ['doccodepluginmapping_id', 'plugin_id'])

        # Adding M2M table for field database_storage_plugins on 'DoccodePluginMapping'
        m2m_table_name = db.shorten_name('dms_plugins_doccodepluginmapping_database_storage_plugins')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('doccodepluginmapping', models.ForeignKey(orm['dms_plugins.doccodepluginmapping'], null=False)),
            ('plugin', models.ForeignKey(orm['djangoplugins.plugin'], null=False))
        ))
        db.create_unique(m2m_table_name, ['doccodepluginmapping_id', 'plugin_id'])

        # Adding M2M table for field storage_plugins on 'DoccodePluginMapping'
        m2m_table_name = db.shorten_name('dms_plugins_doccodepluginmapping_storage_plugins')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('doccodepluginmapping', models.ForeignKey(orm['dms_plugins.doccodepluginmapping'], null=False)),
            ('plugin', models.ForeignKey(orm['djangoplugins.plugin'], null=False))
        ))
        db.create_unique(m2m_table_name, ['doccodepluginmapping_id', 'plugin_id'])

        # Adding M2M table for field before_retrieval_plugins on 'DoccodePluginMapping'
        m2m_table_name = db.shorten_name('dms_plugins_doccodepluginmapping_before_retrieval_plugins')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('doccodepluginmapping', models.ForeignKey(orm['dms_plugins.doccodepluginmapping'], null=False)),
            ('plugin', models.ForeignKey(orm['djangoplugins.plugin'], null=False))
        ))
        db.create_unique(m2m_table_name, ['doccodepluginmapping_id', 'plugin_id'])

        # Adding M2M table for field before_removal_plugins on 'DoccodePluginMapping'
        m2m_table_name = db.shorten_name('dms_plugins_doccodepluginmapping_before_removal_plugins')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('doccodepluginmapping', models.ForeignKey(orm['dms_plugins.doccodepluginmapping'], null=False)),
            ('plugin', models.ForeignKey(orm['djangoplugins.plugin'], null=False))
        ))
        db.create_unique(m2m_table_name, ['doccodepluginmapping_id', 'plugin_id'])

        # Adding M2M table for field before_update_plugins on 'DoccodePluginMapping'
        m2m_table_name = db.shorten_name('dms_plugins_doccodepluginmapping_before_update_plugins')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('doccodepluginmapping', models.ForeignKey(orm['dms_plugins.doccodepluginmapping'], null=False)),
            ('plugin', models.ForeignKey(orm['djangoplugins.plugin'], null=False))
        ))
        db.create_unique(m2m_table_name, ['doccodepluginmapping_id', 'plugin_id'])

        # Adding M2M table for field update_plugins on 'DoccodePluginMapping'
        m2m_table_name = db.shorten_name('dms_plugins_doccodepluginmapping_update_plugins')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('doccodepluginmapping', models.ForeignKey(orm['dms_plugins.doccodepluginmapping'], null=False)),
            ('plugin', models.ForeignKey(orm['djangoplugins.plugin'], null=False))
        ))
        db.create_unique(m2m_table_name, ['doccodepluginmapping_id', 'plugin_id'])

        # Adding M2M table for field database_update_plugins on 'DoccodePluginMapping'
        m2m_table_name = db.shorten_name('dms_plugins_doccodepluginmapping_database_update_plugins')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('doccodepluginmapping', models.ForeignKey(orm['dms_plugins.doccodepluginmapping'], null=False)),
            ('plugin', models.ForeignKey(orm['djangoplugins.plugin'], null=False))
        ))
        db.create_unique(m2m_table_name, ['doccodepluginmapping_id', 'plugin_id'])

        # Adding model 'PluginOption'
        db.create_table('dms_plugins_pluginoption', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pluginmapping', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['dms_plugins.DoccodePluginMapping'])),
            ('plugin', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['djangoplugins.Plugin'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('value', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
        ))
        db.send_create_signal('dms_plugins', ['PluginOption'])


    def backwards(self, orm):
        # Deleting model 'DoccodePluginMapping'
        db.delete_table('dms_plugins_doccodepluginmapping')

        # Removing M2M table for field before_storage_plugins on 'DoccodePluginMapping'
        db.delete_table(db.shorten_name('dms_plugins_doccodepluginmapping_before_storage_plugins'))

        # Removing M2M table for field database_storage_plugins on 'DoccodePluginMapping'
        db.delete_table(db.shorten_name('dms_plugins_doccodepluginmapping_database_storage_plugins'))

        # Removing M2M table for field storage_plugins on 'DoccodePluginMapping'
        db.delete_table(db.shorten_name('dms_plugins_doccodepluginmapping_storage_plugins'))

        # Removing M2M table for field before_retrieval_plugins on 'DoccodePluginMapping'
        db.delete_table(db.shorten_name('dms_plugins_doccodepluginmapping_before_retrieval_plugins'))

        # Removing M2M table for field before_removal_plugins on 'DoccodePluginMapping'
        db.delete_table(db.shorten_name('dms_plugins_doccodepluginmapping_before_removal_plugins'))

        # Removing M2M table for field before_update_plugins on 'DoccodePluginMapping'
        db.delete_table(db.shorten_name('dms_plugins_doccodepluginmapping_before_update_plugins'))

        # Removing M2M table for field update_plugins on 'DoccodePluginMapping'
        db.delete_table(db.shorten_name('dms_plugins_doccodepluginmapping_update_plugins'))

        # Removing M2M table for field database_update_plugins on 'DoccodePluginMapping'
        db.delete_table(db.shorten_name('dms_plugins_doccodepluginmapping_database_update_plugins'))

        # Deleting model 'PluginOption'
        db.delete_table('dms_plugins_pluginoption')


    models = {
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
        'djangoplugins.plugin': {
            'Meta': {'ordering': "('_order',)", 'unique_together': "(('point', 'name'),)", 'object_name': 'Plugin'},
            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['djangoplugins.PluginPoint']"}),
            'pythonpath': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'})
        },
        'djangoplugins.pluginpoint': {
            'Meta': {'object_name': 'PluginPoint'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pythonpath': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'dms_plugins.doccodepluginmapping': {
            'Meta': {'object_name': 'DoccodePluginMapping'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'before_removal_plugins': ('djangoplugins.fields.ManyPluginField', [], {'symmetrical': 'False', 'related_name': "'settings_before_removal'", 'blank': 'True', 'point': "orm['djangoplugins.Plugin']"}),
            'before_retrieval_plugins': ('djangoplugins.fields.ManyPluginField', [], {'symmetrical': 'False', 'related_name': "'settings_before_retrieval'", 'blank': 'True', 'point': "orm['djangoplugins.Plugin']"}),
            'before_storage_plugins': ('djangoplugins.fields.ManyPluginField', [], {'symmetrical': 'False', 'related_name': "'settings_before_storage'", 'blank': 'True', 'point': "orm['djangoplugins.Plugin']"}),
            'before_update_plugins': ('djangoplugins.fields.ManyPluginField', [], {'symmetrical': 'False', 'related_name': "'settings_before_update'", 'blank': 'True', 'point': "orm['djangoplugins.Plugin']"}),
            'database_storage_plugins': ('djangoplugins.fields.ManyPluginField', [], {'symmetrical': 'False', 'related_name': "'settings_database_storage'", 'blank': 'True', 'point': "orm['djangoplugins.Plugin']"}),
            'database_update_plugins': ('djangoplugins.fields.ManyPluginField', [], {'symmetrical': 'False', 'related_name': "'settings_database_update'", 'blank': 'True', 'point': "orm['djangoplugins.Plugin']"}),
            'doccode': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['core.DocumentTypeRule']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'storage_plugins': ('djangoplugins.fields.ManyPluginField', [], {'symmetrical': 'False', 'related_name': "'settings_storage'", 'blank': 'True', 'point': "orm['djangoplugins.Plugin']"}),
            'update_plugins': ('djangoplugins.fields.ManyPluginField', [], {'symmetrical': 'False', 'related_name': "'settings_update'", 'blank': 'True', 'point': "orm['djangoplugins.Plugin']"})
        },
        'dms_plugins.pluginoption': {
            'Meta': {'object_name': 'PluginOption'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'plugin': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['djangoplugins.Plugin']"}),
            'pluginmapping': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dms_plugins.DoccodePluginMapping']"}),
            'value': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        }
    }

    complete_apps = ['dms_plugins']