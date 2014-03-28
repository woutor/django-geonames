from math import degrees, radians, cos, sin, acos, pi, fabs
from decimal import Decimal

from django.contrib.gis.db import models
from django.contrib.gis.measure import D
from django.db.models import Q
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.gis.geos import Point

# Some constants for the geo maths
EARTH_RADIUS_MI = 3959.0
KM_TO_MI = 0.621371192
DEGREES_TO_RADIANS = pi / 180.0


class GeonamesUpdate(models.Model):
    """
    To log the geonames updates
    """
    update_date = models.DateField(auto_now_add=True)


class Timezone(models.Model):
    name = models.CharField(max_length=200)
    country = models.ForeignKey('Country')
    gmt_offset = models.DecimalField(max_digits=4, decimal_places=2)
    dst_offset = models.DecimalField(max_digits=4, decimal_places=2)

    class Meta:
        ordering = ['gmt_offset', 'name']
        unique_together = (('name', 'country', 'gmt_offset'),)

    def __unicode__(self):
        if self.gmt_offset >= 0:
            sign = '+'
        else:
            sign = '-'

        gmt = fabs(self.gmt_offset)
        hours = int(gmt)
        minutes = int((gmt - hours) * 60)
        return u"(UTC{0}{1:02d}:{2:02d}) {3}".format(sign, hours, minutes, self.name)


class Language(models.Model):
    name = models.CharField(max_length=200)
    iso_639_1 = models.CharField(max_length=50, blank=True, null=True)
    iso_639_2 = models.CharField(max_length=50, blank=True, null=True)
    iso_639_3 = models.CharField(max_length=50, blank=True, null=True, unique=True)

#    iso_3166_country = models.CharField(
#        max_length=50,
#        blank=True,
#        null=True,
#        unique=True,
#        help_text=_('The ISO 3166 country code indicating the country where this language variant is spoken.'))

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return u"[{}] {}".format(self.iso_639_1, self.name)


class Currency(models.Model):
    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'currencies'

    def __unicode__(self):
        return '[{}] {}'.format(self.code, self.name)


class ActiveCountryManager(models.Manager):
    def get_query_set(self):
        return super(ActiveCountryManager, self).get_query_set().filter(deleted=False)


class Country(models.Model):

    iso = models.CharField(
        max_length=2,
        db_index=True,
        primary_key=True,
        help_text=_('ISO-3166 2-letter country code'))

    iso3 = models.CharField(
        max_length=3,
        db_index=True,
        blank=True,
        null=True,
        help_text=_('ISO-3166 3-letter country code'))

    iso_numeric = models.IntegerField(
        blank=True,
        null=True,)

    fips = models.CharField(
        max_length=2,
        db_index=True,
        blank=True,
        null=True,
        help_text=_('2-letter country code'))

    name = models.CharField(max_length=500, blank=True, null=True)

    capital_name = models.CharField(max_length=500, blank=True, null=True, verbose_name=_('capital'))

    capital = models.ForeignKey('Locality', blank=True, null=True, related_name='countries')

    area = models.FloatField(blank=True, null=True, help_text=_('in sq km'))

    population = models.PositiveIntegerField(blank=True, null=True, help_text=_('number of people'))

    continent = models.CharField(max_length=2, blank=True, null=True)

    tld = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text=_('Top-level domain used for Internet domain names.'))

    currency = models.ForeignKey('Currency', blank=True, null=True)

    phone = models.CharField(max_length=50, blank=True, null=True, help_text=_('Phone number country code.'))

    postal_code_format = models.CharField(max_length=500, blank=True, null=True)

    postal_code_regex = models.CharField(max_length=500, blank=True, null=True)

    languages = models.ManyToManyField('Language', blank=True, null=True)

    geonameid = models.PositiveIntegerField(
        #primary_key=True,
        blank=True,
        null=True)

    neighbours = models.ManyToManyField('self', blank=True, null=True)

    equivalent_fips_code = models.CharField(max_length=10, blank=True, null=True)

#
#    # is the website available in this country?
#    available = models.BooleanField(default=False)
#    deleted = models.BooleanField(default=False)
#
#    objects = ActiveCountryManager()
#    objects_deleted_inc = models.Manager()

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'countries'

    def __unicode__(self):
        return self.name

#    def save(self, *args, **kwargs):
#        if self.longitude is not None and self.latitude is not None:
#            self.point = Point(float(self.longitude), float(self.latitude))
#        else:
#            self.point = None
#        super(Country, self).save(*args, **kwargs)

#    def search_locality(self, locality_name):
#        if len(locality_name) == 0:
#            return []
#        q = Q(country_id=self.code)
#        q &= (Q(name__iexact=locality_name) | Q(alternatenames__name__iexact=locality_name))
#        return Locality.objects.filter(q).distinct()


class Admin1Code(models.Model):
    """
    Usually represents a state or province.
    """
    geonameid = models.PositiveIntegerField(primary_key=True)
    code = models.CharField(max_length=7)
    name = models.CharField(max_length=200)
    name_ascii = models.CharField(max_length=200, verbose_name=_('name (ASCII)'))
    country = models.ForeignKey(Country, related_name="admins1")

    def __unicode__(self):
        return u"{}, {}".format(self.name_ascii, self.country.name)

    @classmethod
    def lookup(cls, raw_code, country):
        # The code stored usually has leading zeros, but it's referenced
        # elsewhere without leading zeros.
        # On top of this, the code isn't always numeric, so we can't just
        # check for the integer...why must you do this to me geonames?
        # Why can't you just reference the geonameid like a sane person?

        raw_code = raw_code.strip()
        if not raw_code:
            return

        # Check for direct match.
        q = cls.objects.filter(country=country, code=raw_code).order_by('-geonameid')
        if q.count():
            return q[0]

        # Check for leading-zero.
        if raw_code.isdigit():
            num_code = int(raw_code)
            q = cls.objects.filter(country=country, code='%02i' % num_code).order_by('-geonameid')
            if q.count():
                return q[0]
            q = cls.objects.filter(country=country, code='%03i' % num_code).order_by('-geonameid')
            if q.count():
                return q[0]

    def save(self, *args, **kwargs):
        # Call the "real" save() method.
        super(Admin1Code, self).save(*args, **kwargs)

        # Update child localities long name
        for loc in self.localities.all():
            loc.save()


class Admin2Code(models.Model):
    """
    Usually represents a county, or some other area larger than a city
    but smaller than a state or province.
    """
    geonameid = models.PositiveIntegerField(primary_key=True)
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=200)
    name_ascii = models.CharField(max_length=200, verbose_name=_('name (ASCII)'))
    country = models.ForeignKey(Country, related_name="admins2")
    admin1 = models.ForeignKey(Admin1Code, null=True, blank=True, related_name="admins2")

#    class Meta:
        # Don't do this. It contains historical revisions, so these can't be unique.
#        unique_together = (("country", "admin1", "name"),)

    def __unicode__(self):
        s = u"{}".format(self.name)
        if self.admin1 is not None:
            s = u"{}, {}".format(s, self.admin1.name)

        return u"{}, {}".format(s, self.country.name)

    @classmethod
    def lookup(cls, admin1, raw_code, country):
        q = cls.objects.filter(country=country, admin1=admin1, code=raw_code).order_by('-geonameid')
        if q.count():
            return q[0]

    def save(self, *args, **kwargs):
        # Check consistency
        if self.admin1 is not None and self.admin1.country != self.country:
            raise StandardError("The country '{}' from the Admin1 '{}' is different than the country '{}' from the Admin2 '{}' and geonameid {}".format(
                                self.admin1.country, self.admin1, self.country, self.name, self.geonameid))

        # Call the "real" save() method.
        super(Admin2Code, self).save(*args, **kwargs)

        # Update child localities long name
        for loc in self.localities.all():
            loc.save()


class ActiveLocalitiesManager(models.GeoManager):
    def get_query_set(self):
        return super(ActiveLocalitiesManager, self).get_query_set().filter(deleted=False)


class Locality(models.Model):

    geonameid = models.PositiveIntegerField(primary_key=True)

    name = models.CharField(max_length=200, db_index=True)

    name_ascii = models.CharField(max_length=200, db_index=True, verbose_name=_('name (ASCII)'))

    alternatenames = models.TextField(
        blank=True,
        null=True,
        help_text=_('A comma-delimited list of alternative names.'))

    latitude = models.DecimalField(
        blank=True,
        null=True,
        max_digits=7,
        decimal_places=7,
        help_text=_('latitude in decimal degrees (wgs84)'))

    longitude = models.DecimalField(
        blank=True,
        null=True,
        max_digits=7,
        decimal_places=7,
        help_text=_('longitude in decimal degrees (wgs84)'))

    point = models.PointField(
        geography=False,
        blank=True,
        null=True)

    feature_class = models.CharField(
        max_length=1,
        blank=True,
        null=True,
        help_text=_('see http://www.geonames.org/export/codes.html'))

    feature_code = models.CharField(
        blank=True,
        null=True,
        max_length=10,
        help_text=_('see http://www.geonames.org/export/codes.html'))

    country = models.ForeignKey('Country', related_name="localities")

    cc2 = models.CharField(
        max_length=60,
        blank=True,
        null=True,
        help_text=_('alternate country codes, comma separated, ISO-3166 2-letter country code, 60 characters'))

    admin1_code = models.ForeignKey(
        'Admin1Code',
        blank=True,
        null=True,
        related_name='localities',
        help_text=_('fipscode (subject to change to iso code), see exceptions below, see file admin1Codes.txt for display names of this code; varchar(20)'))

    admin2_code = models.ForeignKey(
        'Admin2Code',
        blank=True,
        null=True,
        related_name='localities',
        help_text=_('code for the second administrative division, a county in the US, see file admin2Codes.txt; varchar(80)'))

    admin3_code = models.CharField(
        blank=True,
        null=True,
        max_length=20,
        help_text=_('code for third level administrative division'))

    admin4_code = models.CharField(
        blank=True,
        null=True,
        max_length=20,
        help_text=_('code for fourth level administrative division'))

    population = models.PositiveIntegerField(blank=True, null=True)

    elevation = models.IntegerField(blank=True, null=True, help_text=_('in meters'))

    #TODO:how to implement this?
#    #dem               : digital elevation model, srtm3 or gtopo30, average elevation of 3''x3'' (ca 90mx90m) or 30''x30'' (ca 900mx900m) area in meters, integer. srtm processed by cgiar/ciat.

    timezone = models.ForeignKey(
        'Timezone',
        related_name='localities',
        blank=True,
        null=True)

    modification_date = models.DateField(blank=True, null=True, editable=False)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'localities'

    def __unicode__(self):
        return self.name

    def save(self, check_duplicated_longname=True, *args, **kwargs):

#        if check_duplicated_longname is True:
#            # and check if already exists other locality with the same long name
#            other_localities = Locality.objects.filter(long_name=self.long_name)
#            other_localities = other_localities.exclude(geonameid=self.geonameid)
#
#            if other_localities.count() > 0:
#                raise StandardError("Duplicated locality long name '{}'".format(self.long_name))

        # Check consistency
        if self.admin1_code is not None and self.admin1_code.country != self.country:
            raise StandardError("The country '{}' from the Admin1 '{}' is different than the country '{}' from the locality '{}'".format(
                            self.admin1_code.country, self.admin1_code, self.country, self.long_name))

        if self.admin2_code is not None and self.admin2_code.country != self.country:
            raise StandardError("The country '{}' from the Admin2 '{}' is different than the country '{}' from the locality '{}'".format(
                            self.admin2_code.country, self.admin2_code, self.country, self.long_name))

        if self.longitude and self.latitude:
            self.point = Point(float(self.longitude), float(self.latitude))
        else:
            self.point = None

        # Call the "real" save() method.
        super(Locality, self).save(*args, **kwargs)

#    def generate_long_name(self):
#        long_name = u"{}".format(self.name)
#        if self.admin2 is not None:
#            long_name = u"{}, {}".format(long_name, self.admin2.name)
#
#        if self.admin1 is not None:
#            long_name = u"{}, {}".format(long_name, self.admin1.name)
#
#        return long_name

    def near_localities_rough(self, miles):
        """
        Rough calculation of the localities at 'miles' miles of this locality.
        Is rough because calculates a square instead of a circle and the earth
        is considered as an sphere, but this calculation is fast! And we don't
        need precission.
        """
        diff_lat = Decimal(degrees(miles / EARTH_RADIUS_MI))
        latitude = Decimal(self.latitude)
        longitude = Decimal(self.longitude)
        max_lat = latitude + diff_lat
        min_lat = latitude - diff_lat
        diff_long = Decimal(degrees(miles / EARTH_RADIUS_MI / cos(radians(latitude))))
        max_long = longitude + diff_long
        min_long = longitude - diff_long
        near_localities = Locality.objects.filter(latitude__gte=min_lat, longitude__gte=min_long)
        near_localities = near_localities.filter(latitude__lte=max_lat, longitude__lte=max_long)
        return near_localities

    def near_locals_nogis(self, miles):
        ids = []
        for loc in self.near_localities_rough(miles).values_list("geonameid", "latitude", "longitude"):
            other_geonameid = loc[0]
            if self.geonameid == other_geonameid:
                distance = 0
                ids.append(other_geonameid)
            else:
                distance = self.calc_distance_nogis(loc[1], loc[2])
                if distance <= miles:
                    ids.append(other_geonameid)

        return ids

    def calc_distance_nogis(self, la2, lo2):
        # Convert latitude and longitude to
        # spherical coordinates in radians.
        # phi = 90 - latitude
        phi1 = (90.0 - float(self.latitude)) * DEGREES_TO_RADIANS
        phi2 = (90.0 - float(la2)) * DEGREES_TO_RADIANS

        # theta = longitude
        theta1 = float(self.longitude) * DEGREES_TO_RADIANS
        theta2 = float(lo2) * DEGREES_TO_RADIANS

        # Compute spherical distance from spherical coordinates.
        # For two localities in spherical coordinates
        # (1, theta, phi) and (1, theta, phi)
        # cosine( arc length ) =
        #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
        # distance = rho * arc length
        cosinus = sin(phi1) * sin(phi2) * cos(theta1 - theta2) + cos(phi1) * cos(phi2)
        cosinus = round(cosinus, 14)  # to avoid math domain error in acos
        arc = acos(cosinus)

        # Multiply arc by the radius of the earth
        return arc * EARTH_RADIUS_MI

    def near_localities(self, miles):
        localities = self.near_localities_rough(miles)
        localities = localities.filter(point__distance_lte=(self.point, D(mi=miles)))
        return localities.values_list("geonameid", flat=True)


class AlternateName(models.Model):
    admin1_code = models.ForeignKey(Locality, related_name="admin1_names", null=True, blank=True)
    admin2_code = models.ForeignKey(Locality, related_name="admin2_names", null=True, blank=True)
    locality = models.ForeignKey(Locality, related_name="locality_names", null=True, blank=True)
    language = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=200, db_index=True)
    # TODO include localization code

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name
