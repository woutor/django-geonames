#!/usr/bin/env python
import datetime
import os
import re
import sys
import traceback
import zipfile
from optparse import make_option
import dateutil.parser

import django
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from geonames.models import (
    Timezone, Language, Country, Currency, Locality,
    Admin1Code, Admin2Code,
    #AlternateName,
    GeonamesUpdate,
)

FILES = [
    TIMEZONE_URL,
    LANGUAGE_URL,
    COUNTRY_URL,
    ADMIN1CODE_URL,
    ADMIN2CODE_URL,
    CITIES5000_URL,
    #ALTERNATENAME_URL,
] = [
    'http://download.geonames.org/export/dump/timeZones.txt',
    'http://download.geonames.org/export/dump/iso-languagecodes.txt',
    'http://download.geonames.org/export/dump/countryInfo.txt',
    'http://download.geonames.org/export/dump/admin1CodesASCII.txt',
    'http://download.geonames.org/export/dump/admin2Codes.txt',
    'http://download.geonames.org/export/dump/cities5000.zip',
    #'http://download.geonames.org/export/dump/alternateNames.zip',#TODO:what is the purpose of this file?
]

# See http://www.geonames.org/export/codes.html
city_types = ['PPL','PPLA','PPLC','PPLA2','PPLA3','PPLA4', 'PPLG']


class Command(BaseCommand):
    help = "Geonames import command."
    tmpdir = '/tmp'
    curdir = os.getcwd()
    countries = {}
    localities = set()
    no_update = False
    skip_to_line = 0
    
    option_list = BaseCommand.option_list + (
        make_option(
            '--models',
            default=None,
            help='A comma-delimited list of the models to load. Default is to load all models.'),
        make_option(
            '--no-update',
            action='store_true',
            default=False,
            help='If given, records will only be inserted. Existing records will not be modified.'),
        make_option(
            '--skip-to-line',
            default=0,
            help='If given, the processor will skip to the specified line and ignore all previous records..'),
    )

    def handle(self, *args, **options):
        start_time = datetime.datetime.now()
        self.no_update = options['no_update']
        self.skip_to_line = int(options['skip_to_line'])
        self.load(model_list=options['models'])
        print '\nCompleted in {}'.format(datetime.datetime.now() - start_time)

    @transaction.commit_on_success
    def load(self, model_list=None):
        
        model_list = [_ for _ in (model_list or '').split(',') if _.strip()]
        
        all_models = [
            Timezone,
            Language,
            Country,
            Admin1Code,
            Admin2Code,
            Locality,
        ]
#        for mdl in all_models:
#            if (not model_list or mdl.__name__.lower() in model_list) and mdl.objects.all().count() is not 0:
#                print 'ERROR there are %s records in the database' % (mdl.__name__,)
#                sys.exit(1)

        self.download_files()
        
        for mdl in all_models:
            if model_list and mdl.__name__.lower() not in model_list:
                continue
            #self.cleanup()
            getattr(self, 'load_%s' % mdl.__name__.lower())()
        
        #self.check_errors()
        # Save the time when the load happened
        GeonamesUpdate.objects.create()
        #self.cleanup_files()

    def download_files(self):
        try:
            os.mkdir(self.tmpdir)
            os.chdir(self.tmpdir)
        except OSError:
            os.chdir(self.tmpdir)
            #print 'Temporary directory %s exists, using already downloaded data' % self.tmpdir
            #return

        for f in FILES:
            fn = f.split('/')[-1]
            if os.path.isfile(os.path.join(self.tmpdir, fn)):
                continue
            if os.system('wget %s' % f) != 0:
                print 'ERROR fetching %s' % (f,)
                sys.exit(1)

    def cleanup_files(self):
        os.chdir(self.curdir)
        for f in os.listdir(self.tmpdir):
            os.unlink('%s/%s' % (self.tmpdir, f))
        #os.rmdir(self.tmpdir)

    def load_timezone(self):
        print 'Loading Timezones'
        objects = []
        total = open(TIMEZONE_URL.split('/')[-1], 'r').read().count('\n')
        i = 0
        with open(TIMEZONE_URL.split('/')[-1], 'r') as fd:
            fd.readline() # Ignore header.
            for line in fd:
                i += 1
                if not i % 10:
                    print '\r%i of %i' % (i, total),
                    sys.stdout.flush()
                fields = line[:-1].split('\t')
                country_code, name, gmt_offset, dst_offset = fields[0:4]
                country = Country.objects.get(iso=country_code.strip())
                #objects.append(Timezone(country=country, name=name, gmt_offset=gmt_offset, dst_offset=dst_offset))
                timezone, _ = Timezone.objects.get_or_create(country=country, name=name.strip(), gmt_offset=gmt_offset, defaults=dict(dst_offset=dst_offset))
                timezone.dst_offset = dst_offset
                timezone.save()
            print '\r%i of %i' % (total, total),
            sys.stdout.flush()
            print

    def load_language(self):
        print 'Loading Languages'
        objects = []
        fn = LANGUAGE_URL.split('/')[-1]
        with open(fn, 'r') as fd:
            try:
                fd.readline()  # skip the head
                for line in fd:
                    #iso_639_1, name = line.split('\t')[2:4]
                    if not line.strip():
                        continue
                    iso_639_3, iso_639_2, iso_639_1, name = line.split('\t')
                    iso_639_1 = iso_639_1.strip()
                    iso_639_2 = iso_639_2.strip()
                    iso_639_3 = iso_639_3.strip()
                    if not iso_639_3:
                        continue
                    name = name.strip()
                    if not name:
                        continue
                    objects.append(Language(
                        iso_639_1=iso_639_1,
                        iso_639_2=iso_639_2,
                        iso_639_3=iso_639_3,
                        name=name,
                    ))
            except Exception, inst:
                traceback.print_exc(inst)
                raise Exception("ERROR parsing:\n {}\n The error was: {}".format(line, inst))

        print 'objects:',objects
        Language.objects.bulk_create(objects)
        print '{0:8d} Languages loaded'.format(Timezone.objects.all().count())
        self.fix_languagecodes()

    def fix_languagecodes(self):
        print 'Fixing Language codes'
        # Corrections
        Language.objects.filter(iso_639_1='km').update(name='Khmer')
        Language.objects.filter(iso_639_1='ia').update(name='Interlingua')
        Language.objects.filter(iso_639_1='ms').update(name='Malay')
        Language.objects.filter(iso_639_1='el').update(name='Greek')
        Language.objects.filter(iso_639_1='se').update(name='Sami')
        Language.objects.filter(iso_639_1='oc').update(name='Occitan')
        Language.objects.filter(iso_639_1='st').update(name='Sotho')
        Language.objects.filter(iso_639_1='sw').update(name='Swahili')
        Language.objects.filter(iso_639_1='to').update(name='Tonga')
        Language.objects.filter(iso_639_1='fy').update(name='Frisian')

    def load_country(self):
        print 'Loading Countries'
        objects = []
        langs_dic = {}
        dollar, _ = Currency.objects.get_or_create(code='USD', defaults=dict(name='Dollar'))
        fn = COUNTRY_URL.split('/')[-1]
        print 'fn:',fn
        country_neighbours = {} # {country:neighbor iso codes}
        with open(fn) as fd:
            for line in fd:
                line = re.sub(r'\n+', '', line)
                if not line or line[0] == '#':
                    continue

                fields = line.split('\t')
                print fields
#                    code = fields[0]
#                    self.countries[code] = {}
#                    name = unicode(fields[4], 'utf-8')
#                    currency_code = fields[10]
#                    currency_name = fields[11]
#                    langs_dic[code] = fields[15]
                
                [
                    iso,
                    iso3,
                    iso_numeric,
                    fips,
                    country_name,
                    capital_name,
                    area,
                    population,
                    continent,
                    tld,
                    currency_code,
                    currency_name,
                    phone,
                    postal_code_format,
                    postal_code_regex,
                    languages,
                    geonameid,
                    neighbours,
                    equivalent_fips_code,
                ] = fields
                
                if currency_code == '':
                    currency = dollar
                else:
                    currency_code = currency_code.strip()
                    assert len(currency_code) <= 3, 'Invalid currency_code: %s' % (currency_code,)
                    currency, created = Currency.objects.get_or_create(
                            code=currency_code, defaults={'name': currency_name.strip()})

                # The column 'languages' lists the languages spoken in a country ordered by the number of speakers. The language code is a 'locale'                                                                         
                # where any two-letter primary-tag is an ISO-639 language abbreviation and any two-letter initial subtag is an ISO-3166 country code.                                                                        
                #                                                                        
                # Example : es-AR is the Spanish variant spoken in Argentina.
                _languages = languages.strip().split(',')
                languages = []
                for _language in _languages:
                    _language = _language.split('-')
                    if not _language:
                        continue
                    _language = _language[0]
                    if not _language:
                        continue
                    print 'language:',_language
                    if len(_language) == 3:
                        languages.append(Language.objects.get(iso_639_3=_language))
                    else:
                        languages.append(Language.objects.get(iso_639_1=_language))

                print geonameid,country_name
#                continue
            
                country = Country(
                    iso=iso,
                    iso3=iso3,
                    iso_numeric=iso_numeric,
                    fips=fips,
                    name=country_name.strip(),
                    capital_name=capital_name.strip(),
                    area=float(area) if area.strip() else None,
                    population=int(population) if population.strip() else None,
                    continent=continent.strip(),
                    tld=tld.strip(),
                    currency=currency,
                    phone=phone.strip(),
                    postal_code_format=postal_code_format.strip(),
                    postal_code_regex=postal_code_regex.strip(),
                    #languages=languages,
                    geonameid=geonameid.strip() if geonameid.strip() else None,
                    #neighbours,
                    equivalent_fips_code=equivalent_fips_code.strip(),
                )
                country.save()
                country.languages.add(*languages)
                country_neighbours[country] = [_ for _ in neighbours.split(',') if _.strip()]
#            except Exception, inst:
#                traceback.print_exc(inst)
#                raise Exception("ERROR parsing:\n {}\n The error was: {}".format(line, inst))

#        Country.objects.bulk_create(objects)
#        print '{0:8d} Countries loaded'.format(Country.objects.all().count())

        print 'Adding country neighbours...'
        for country, neighbour_iso_codes in country_neighbours.iteritems():
            print country
            for iso in neighbour_iso_codes:
                other_country = Country.objects.get(iso=iso)
                country = Country.objects.get(iso=country.iso)
                country.neighbours.add(other_country)
                other_country.neighbours.add(country)

        #TODO:link capitals?

#        print 'Adding Languages to Countries'
#        default_lang = Language.objects.get(iso_639_1='en')
#        for country in Country.objects.all():
#            for code in langs_dic[country.code].split(','):
#                iso_639_1 = code.split("-")[0]
#                if len(iso_639_1) < 2:
#                    continue
#
#                languages = Language.objects.filter(iso_639_1=iso_639_1)
#                if languages.count() == 1:
#                    country.languages.add(languages[0])
#
#            if country.languages.count() == 0:
#                country.languages.add(default_lang)

    def load_admin1code(self):
        print 'Loading Admin1Codes'
        objects = []
        prior_geonameids = set(Admin1Code.objects.all().values_list('geonameid'))
        with open(ADMIN1CODE_URL.split('/')[-1]) as fd:
            for line in fd:
                fields = line[:-1].split('\t')
                codes, name, name_ascii = fields[0:3]
                country_code, admin1_code = codes.split('.')
                geonameid = fields[3].strip()
                if geonameid in prior_geonameids:
                    continue
#                self.countries.setdefault(country_code, {})
#                self.countries[country_code][admin1_code] = {'geonameid': geonameid, 'admins2': {}}
                country = Country.objects.get(iso=country_code.strip())
                name = unicode(name, 'utf-8')
                objects.append(Admin1Code(
                    geonameid=geonameid,
                    code=admin1_code.strip(),
                    name=name.strip(),
                    name_ascii=name_ascii.strip(),
                    country=country))
        Admin1Code.objects.bulk_create(objects)

    def load_admin2code(self):
        print 'Loading Admin2Codes'
        objects = []
        admin2_list = set()  # to find duplicated
        skipped_duplicated = 0
        total = open(ADMIN2CODE_URL.split('/')[-1]).read().count('\n')
        prior_geonameids = set(Admin2Code.objects.all().values_list('geonameid'))
        with open(ADMIN2CODE_URL.split('/')[-1]) as fd:
            i = 0
            for line in fd:
                i += 1
                if not i % 100:
                    print '\r%i of %i' % (i, total),
                    sys.stdout.flush()
                fields = line[:-1].split('\t')
                codes, name, name_ascii = fields[0:3]
                country_code, admin1_code, admin2_code = codes.split('.')

                # if there is a duplicated
                #admin1_id = "{}.{}.{}".format(country_code, admin1_code, name)
#                long_code = "{}.{}.{}".format(country_code, admin1_code, name)
#                if long_code in admin2_list:
#                    skipped_duplicated += 1
#                    continue
#                admin2_list.add(long_code)

                geonameid = fields[3].strip()
                if geonameid in prior_geonameids:
                    continue
                prior_geonameids.add(geonameid)
                #admin1_dic = self.countries[country_code].get(admin1_code)

                # if there is not admin1 level we save it but we don't keep it for the localities
#                if admin1_dic is None:
#                    admin1_id = None
#                else:
#                    # If not, we get the id of admin1 and we save geonameid for filling in Localities later
#                    admin1_id = admin1_dic['geonameid']
#                    admin1_dic['admins2'][admin2_code] = geonameid
                admin1 = None
                q = Admin1Code.objects.filter(country__iso=country_code, code=admin1_code).order_by('-geonameid')
                if q.count():
                    # TODO: resolve counts higher than 1? The Admin1Code table
                    #contains duplicate country+code combinations due to
                    #historical changes, but we don't necessarily know which
                    #one the current admin1_code refers (although it's probably
                    #the most recent).
                    admin1 = q[0]
                else:
                    #TODO:is this bad data? shouldn't an admin2code always have an admin1code
#                    raise Exception, 'No admin1code found for country %s with code %s!' % (country_code, admin1_code)
                    pass

                country = Country.objects.get(iso=country_code.strip())
                name = unicode(name, 'utf-8')
                objects.append(Admin2Code(geonameid=geonameid,
                                          code=admin2_code,
                                          name=name,
                                          name_ascii=name_ascii,
                                          country=country,
                                          admin1=admin1))

        Admin2Code.objects.bulk_create(objects)
        print '{0:8d} Admin2Codes loaded'.format(Admin2Code.objects.all().count())
#        print '{0:8d} Admin2Codes skipped because duplicated'.format(skipped_duplicated)

    def load_locality(self):
        print 'Loading Localities'
        objects = []
        batch = 1000
        processed = 0
        modifiable_fields = 'name,name_ascii,alternatenames,latitude,longitude,feature_class,feature_code,country,cc2,admin1_code,admin2_code,admin3_code,admin4_code,population,elevation,timezone,modification_date'.split(',')
        prior_geonameids = set(Locality.objects.all().values_list('pk', flat=True))
        fn = CITIES5000_URL.split('/')[-1]
        print 'Counting lines...'
        if fn.endswith('.zip'):
            fh = zipfile.ZipFile(fn).open(fn.replace('.zip', '.txt'))
            total = zipfile.ZipFile(fn).open(fn.replace('.zip', '.txt')).read().count('\n')
        else:
            fh = open(fn, 'r')
            total = open(fn, 'r').read().count('\n')
        print 'Processing lines...'
        with fh as fd:
            for line in fd:
                processed += 1
                
                if not processed % 100:
                    print '\r%i of %i (%.02f%%)' % (processed, total, processed/float(total)*100),
                    sys.stdout.flush()
                
                if self.skip_to_line and processed < self.skip_to_line:
                    continue
                
                fields = line[:-1].split('\t')
                geonameid = int(fields[0].strip())
                if geonameid in prior_geonameids and self.no_update:
                    continue
                        
                name = unicode(fields[1].strip(), 'utf-8')
                name_ascii = fields[2].strip()
                alternatenames = fields[3].strip()
                latitude = fields[4].strip()
                longitude = fields[5].strip()
                feature_class = fields[6].strip()
                feature_code = fields[7].strip()
                country = Country.objects.get(iso=fields[8].strip())
                cc2 = fields[9].strip()
                admin1_code = Admin1Code.lookup(fields[10].strip(), country) if fields[10].strip() else None
                admin2_code = Admin2Code.lookup(admin1_code, fields[11].strip(), country) if fields[11].strip() else None
                admin3_code = fields[12].strip() if fields[12].strip() else None
                admin4_code = fields[13].strip() if fields[13].strip() else None
                population = int(fields[14]) if fields[14].strip() else None
                elevation = int(fields[15]) if fields[15].strip() else None
                dem = None#fields[16]
                try:
                    timezone = Timezone.objects.get(name=fields[17].strip(), country=country)
                except Timezone.DoesNotExist:
                    timezone = None
                modification_date = dateutil.parser.parse(fields[18]) if fields[18].strip() else None

                if geonameid in prior_geonameids:
                    # Update existing record.
                    locality = Locality.objects.get(geonameid=geonameid)
                    for _ in modifiable_fields:
                        setattr(locality, _, locals()[_])
                    locality.save()
                else:
                    # Bulk insert new record.
                    prior_geonameids.add(geonameid)
                    #defaults = dict((_, locals()[_]) for _ in modifiable_fields)
#                    defaults['point'] = Point(longitude, latitude)
#                    defaults['geonameid'] = geonameid
                    #locality = Locality(**defaults)
                    locality = Locality(
                        geonameid=geonameid,
                        name=name,
                        name_ascii=name_ascii,
                        alternatenames=alternatenames,
                        latitude=latitude,
                        longitude=longitude,
                        feature_class=feature_class,
                        feature_code=feature_code,
                        country=country,
                        cc2=cc2,
                        admin1_code=admin1_code,
                        admin2_code=admin2_code,
                        admin3_code=admin3_code,
                        admin4_code=admin4_code,
                        population=population,
                        elevation=elevation,
                        #dem=dem,
                        timezone=timezone,
                        modification_date=modification_date,
                        point=Point(float(longitude), float(latitude)) if longitude and latitude else None,
                    )
                    objects.append(locality)

                if not processed % batch and objects:
                    Locality.objects.bulk_create(objects)
                    django.db.transaction.commit()
                    objects = []

        if objects:
            Locality.objects.bulk_create(objects)
        print "{0:8d} Localities loaded".format(processed)

        print 'Filling missed timezones in localities'
        # Try to find the missing timezones
        for locality in Locality.objects.filter(timezone__isnull=True):
            # We assign the time zone of the most populated locality in the same admin2
            near_localities = Locality.objects.filter(admin2_code=locality.admin2_code)
            near_localities = near_localities.exclude(timezone__isnull=True)
            if not near_localities.exists():
                # We assign the time zone of the most populated locality in the same admin1
                near_localities = Locality.objects.filter(admin1_code=locality.admin1_code)
                near_localities = near_localities.exclude(timezone__isnull=True)

            if not near_localities.exists():
                # We assign the time zone of the most populated locality in the same country
                near_localities = Locality.objects.filter(country=locality.country)
                near_localities = near_localities.exclude(timezone__isnull=True)

            if near_localities.exists():
                near_localities = near_localities.order_by('-population')
                locality.timezone = near_localities[0].timezone
                locality.save()
            else:
                print " ERROR locality with no timezone {}".format(locality)
                raise Exception()

#    def cleanup(self):
#        self.delete_empty_countries()
#        self.delete_duplicated_localities()

#    def delete_empty_countries(self):
#        print 'Setting as deleted empty Countries'
#        # Countries
#        countries = Country.objects.annotate(Count("localities")).filter(localities__count=0)
#        for c in countries:
#            c.deleted = True
#            c.save()

#        print ' {0:8d} Countries set as deleted'.format(countries.count())

#    def delete_duplicated_localities(self):
#        print "Setting as deleted duplicated localities"
#        total = 0
#        for c in Country.objects.all():
#            prev_name = ""
#            for loc in c.localities.order_by("long_name", "-population"):
#                if loc.long_name == prev_name:
#                    loc.deleted = True
#                    loc.save(check_duplicated_longname=False)
#                    total += 1
#
#                prev_name = loc.long_name
#
#        print " {0:8d} localities set as deleted".format(total)

#    def load_alternatename(self):
#        print 'Loading alternate names'
#        objects = []
#        allobjects = {}
#        batch = 10000
#        processed = 0
#        
#        fn = ALTERNATENAME_URL.split('/')[-1]
#        if fn.endswith('.zip'):
#            fh = zipfile.ZipFile(fn).open(fn.replace('.zip', '.txt'))
#        else:
#            fh = open(fn, 'r')
#        with fh as fd:
#            for line in fd:
#                try:
#                    fields = line.split('\t')
#                    locality_geonameid = fields[1]
#                    if locality_geonameid not in self.localities:
#                        continue
#
#                    name = fields[3]
#                    if locality_geonameid in allobjects:
#                        if name in allobjects[locality_geonameid]:
#                            continue
#                    else:
#                        allobjects[locality_geonameid] = set()
#
#                    allobjects[locality_geonameid].add(name)
#                    objects.append(AlternateName(
#                        locality_id=locality_geonameid,
#                        name=name))
#                    processed += 1
#                except Exception, inst:
#                    traceback.print_exc(inst)
#                    raise Exception("ERROR parsing:\n {}\n The error was: {}".format(line, inst))
#
#                if processed % batch == 0:
#                    AlternateName.objects.bulk_create(objects)
#                    print "{0:8d} AlternateNames loaded".format(processed)
#                    objects = []
#
#        AlternateName.objects.bulk_create(objects)
#        print "{0:8d} AlternateNames loaded".format(processed)

    def check_errors(self):
        print 'Checking errors'

        print ' Checking empty country'
        if Country.objects.annotate(Count("localities")).filter(localities__count=0):
            print " ERROR Countries with no localities"
            raise Exception()

        print ' Checking all Localities with timezone'
        if Locality.objects.filter(timezone__isnull=True):
            print " ERROR Localities with no timezone"
            raise Exception()

        print ' Checking duplicated localities per country'
        for country in Country.objects.all():
            duplicated = country.localities.values('long_name').annotate(Count('long_name')).filter(long_name__count__gt=1)
            if len(duplicated) != 0:
                print " ERROR Duplicated localities in {}: {}".format(country, duplicated)
                print duplicated
                raise Exception()


