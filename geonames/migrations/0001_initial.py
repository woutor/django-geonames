# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'GeonamesUpdate'
        db.create_table(u'geonames_geonamesupdate', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('update_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'geonames', ['GeonamesUpdate'])

        # Adding model 'Timezone'
        db.create_table(u'geonames_timezone', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['geonames.Country'])),
            ('gmt_offset', self.gf('django.db.models.fields.DecimalField')(max_digits=4, decimal_places=2)),
            ('dst_offset', self.gf('django.db.models.fields.DecimalField')(max_digits=4, decimal_places=2)),
        ))
        db.send_create_signal(u'geonames', ['Timezone'])

        # Adding unique constraint on 'Timezone', fields ['name', 'country', 'gmt_offset']
        db.create_unique(u'geonames_timezone', ['name', 'country_id', 'gmt_offset'])

        # Adding model 'Language'
        db.create_table(u'geonames_language', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('iso_639_1', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('iso_639_2', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('iso_639_3', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'geonames', ['Language'])

        # Adding model 'Currency'
        db.create_table(u'geonames_currency', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=3, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'geonames', ['Currency'])

        # Adding model 'Country'
        db.create_table(u'geonames_country', (
            ('iso', self.gf('django.db.models.fields.CharField')(max_length=2, primary_key=True, db_index=True)),
            ('iso3', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=3, null=True, blank=True)),
            ('iso_numeric', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('fips', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=2, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
            ('capital_name', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
            ('capital', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='countries', null=True, to=orm['geonames.Locality'])),
            ('area', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('population', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('continent', self.gf('django.db.models.fields.CharField')(max_length=2, null=True, blank=True)),
            ('tld', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('currency', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['geonames.Currency'], null=True, blank=True)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('postal_code_format', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
            ('postal_code_regex', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
            ('geonameid', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('equivalent_fips_code', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
        ))
        db.send_create_signal(u'geonames', ['Country'])

        # Adding M2M table for field languages on 'Country'
        m2m_table_name = db.shorten_name(u'geonames_country_languages')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('country', models.ForeignKey(orm[u'geonames.country'], null=False)),
            ('language', models.ForeignKey(orm[u'geonames.language'], null=False))
        ))
        db.create_unique(m2m_table_name, ['country_id', 'language_id'])

        # Adding M2M table for field neighbours on 'Country'
        m2m_table_name = db.shorten_name(u'geonames_country_neighbours')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_country', models.ForeignKey(orm[u'geonames.country'], null=False)),
            ('to_country', models.ForeignKey(orm[u'geonames.country'], null=False))
        ))
        db.create_unique(m2m_table_name, ['from_country_id', 'to_country_id'])

        # Adding model 'Admin1Code'
        db.create_table(u'geonames_admin1code', (
            ('geonameid', self.gf('django.db.models.fields.PositiveIntegerField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=7)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('name_ascii', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(related_name='admins1', to=orm['geonames.Country'])),
        ))
        db.send_create_signal(u'geonames', ['Admin1Code'])

        # Adding model 'Admin2Code'
        db.create_table(u'geonames_admin2code', (
            ('geonameid', self.gf('django.db.models.fields.PositiveIntegerField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('name_ascii', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(related_name='admins2', to=orm['geonames.Country'])),
            ('admin1', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='admins2', null=True, to=orm['geonames.Admin1Code'])),
        ))
        db.send_create_signal(u'geonames', ['Admin2Code'])

        # Adding model 'Locality'
        db.create_table(u'geonames_locality', (
            ('geonameid', self.gf('django.db.models.fields.PositiveIntegerField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200, db_index=True)),
            ('name_ascii', self.gf('django.db.models.fields.CharField')(max_length=200, db_index=True)),
            ('alternatenames', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('latitude', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=7, decimal_places=2, blank=True)),
            ('longitude', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=7, decimal_places=2, blank=True)),
            ('point', self.gf('django.contrib.gis.db.models.fields.PointField')(null=True, blank=True)),
            ('feature_class', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('feature_code', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(related_name='localities', to=orm['geonames.Country'])),
            ('cc2', self.gf('django.db.models.fields.CharField')(max_length=60, null=True, blank=True)),
            ('admin1_code', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='localities', null=True, to=orm['geonames.Admin1Code'])),
            ('admin2_code', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='localities', null=True, to=orm['geonames.Admin2Code'])),
            ('admin3_code', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('admin4_code', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('population', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('elevation', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('timezone', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='localities', null=True, to=orm['geonames.Timezone'])),
            ('modification_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'geonames', ['Locality'])


    def backwards(self, orm):
        # Removing unique constraint on 'Timezone', fields ['name', 'country', 'gmt_offset']
        db.delete_unique(u'geonames_timezone', ['name', 'country_id', 'gmt_offset'])

        # Deleting model 'GeonamesUpdate'
        db.delete_table(u'geonames_geonamesupdate')

        # Deleting model 'Timezone'
        db.delete_table(u'geonames_timezone')

        # Deleting model 'Language'
        db.delete_table(u'geonames_language')

        # Deleting model 'Currency'
        db.delete_table(u'geonames_currency')

        # Deleting model 'Country'
        db.delete_table(u'geonames_country')

        # Removing M2M table for field languages on 'Country'
        db.delete_table(db.shorten_name(u'geonames_country_languages'))

        # Removing M2M table for field neighbours on 'Country'
        db.delete_table(db.shorten_name(u'geonames_country_neighbours'))

        # Deleting model 'Admin1Code'
        db.delete_table(u'geonames_admin1code')

        # Deleting model 'Admin2Code'
        db.delete_table(u'geonames_admin2code')

        # Deleting model 'Locality'
        db.delete_table(u'geonames_locality')


    models = {
        u'geonames.admin1code': {
            'Meta': {'object_name': 'Admin1Code'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '7'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'admins1'", 'to': u"orm['geonames.Country']"}),
            'geonameid': ('django.db.models.fields.PositiveIntegerField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name_ascii': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'geonames.admin2code': {
            'Meta': {'object_name': 'Admin2Code'},
            'admin1': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'admins2'", 'null': 'True', 'to': u"orm['geonames.Admin1Code']"}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'admins2'", 'to': u"orm['geonames.Country']"}),
            'geonameid': ('django.db.models.fields.PositiveIntegerField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name_ascii': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'geonames.country': {
            'Meta': {'ordering': "['name']", 'object_name': 'Country'},
            'area': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'capital': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'countries'", 'null': 'True', 'to': u"orm['geonames.Locality']"}),
            'capital_name': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'continent': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'currency': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geonames.Currency']", 'null': 'True', 'blank': 'True'}),
            'equivalent_fips_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'fips': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'geonameid': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'iso': ('django.db.models.fields.CharField', [], {'max_length': '2', 'primary_key': 'True', 'db_index': 'True'}),
            'iso3': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'iso_numeric': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'languages': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['geonames.Language']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'neighbours': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'neighbours_rel_+'", 'null': 'True', 'to': u"orm['geonames.Country']"}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'population': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'postal_code_format': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'postal_code_regex': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'tld': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'})
        },
        u'geonames.currency': {
            'Meta': {'ordering': "['name']", 'object_name': 'Currency'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'geonames.geonamesupdate': {
            'Meta': {'object_name': 'GeonamesUpdate'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'update_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'geonames.language': {
            'Meta': {'ordering': "['name']", 'object_name': 'Language'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'iso_639_1': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'iso_639_2': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'iso_639_3': ('django.db.models.fields.CharField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'geonames.locality': {
            'Meta': {'ordering': "['name']", 'object_name': 'Locality'},
            'admin1_code': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'localities'", 'null': 'True', 'to': u"orm['geonames.Admin1Code']"}),
            'admin2_code': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'localities'", 'null': 'True', 'to': u"orm['geonames.Admin2Code']"}),
            'admin3_code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'admin4_code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'alternatenames': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'cc2': ('django.db.models.fields.CharField', [], {'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'localities'", 'to': u"orm['geonames.Country']"}),
            'elevation': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'feature_class': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'feature_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'geonameid': ('django.db.models.fields.PositiveIntegerField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '7', 'decimal_places': '2', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '7', 'decimal_places': '2', 'blank': 'True'}),
            'modification_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'name_ascii': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'point': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
            'population': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'timezone': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'localities'", 'null': 'True', 'to': u"orm['geonames.Timezone']"})
        },
        u'geonames.timezone': {
            'Meta': {'ordering': "['gmt_offset', 'name']", 'unique_together': "(('name', 'country', 'gmt_offset'),)", 'object_name': 'Timezone'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['geonames.Country']"}),
            'dst_offset': ('django.db.models.fields.DecimalField', [], {'max_digits': '4', 'decimal_places': '2'}),
            'gmt_offset': ('django.db.models.fields.DecimalField', [], {'max_digits': '4', 'decimal_places': '2'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['geonames']
