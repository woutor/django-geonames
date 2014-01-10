from django.contrib import admin

try:
    from admin_steroids import BetterRawIdFieldsModelAdmin
    class BaseAdmin(BetterRawIdFieldsModelAdmin):
        pass
except ImportError:
    class BaseAdmin(admin.ModelAdmin):
        pass

import models

class TimezoneAdmin(BaseAdmin):
    list_display = (
        'name',
        'country',
        'gmt_offset',
        'dst_offset',
    )
    search_fields = (
        'name',
        'country__name',
    )
    raw_id_fields = (
        'country',
    )

class LanguageAdmin(BaseAdmin):
    list_display = (
        'name',
        'iso_639_1',
        'iso_639_2',
        'iso_639_3',
    )
    search_fields = (
        'name',
        'iso_639_1',
        'iso_639_2',
        'iso_639_3',
    )

class CurrencyAdmin(BaseAdmin):
    list_display = (
        'code',
        'name',
    )
    search_fields = (
        'code',
        'name',
    )

class CountryAdmin(BaseAdmin):
    list_display = (
        'iso',
        'iso3',
        'name',
        'capital_name',
        'area',
        'population',
        'continent',
        'tld',
    )
    search_fields = (
        'iso',
        'iso3',
        'name',
        'capital_name',
    )
    
    raw_id_fields = (
        'languages',
        'neighbours',
        'capital',
    )

class Admin1CodeAdmin(BaseAdmin):
    list_display = (
        'geonameid',
        'code',
        'name',
        'name_ascii',
        'country',
    )
    search_fields = (
        'geonameid',
        'code',
        'name',
        'name_ascii',
        'country__name',
    )
    raw_id_fields = (
        'country',
    )

class Admin2CodeAdmin(BaseAdmin):
    list_display = (
        'geonameid',
        'code',
        'name',
        'name_ascii',
        'admin1',
        'country',
    )
    search_fields = (
        'geonameid',
        'code',
        'name',
        'name_ascii',
        'country__name',
    )
    raw_id_fields = (
        'admin1',
        'country',
    )

class LocalityAdmin(BaseAdmin):
    list_display = (
        'geonameid',
        'name',
        'name_ascii',
        'admin1_code',
        'admin2_code',
        'admin3_code',
        'admin4_code',
        'country',
        'population',
        'timezone',
        'modification_date',
    )
    search_fields = (
        'geonameid',
        'name',
        'name_ascii',
        'country__name',
    )
    raw_id_fields = (
        'country',
        'admin1_code',
        'admin2_code',
    )
    readonly_fields = (
        'modification_date',
    )

#class AlternateNameAdmin(BaseAdmin):
#    pass

admin.site.register(models.Timezone, TimezoneAdmin)
admin.site.register(models.Language, LanguageAdmin)
admin.site.register(models.Currency, CurrencyAdmin)
admin.site.register(models.Country, CountryAdmin)
admin.site.register(models.Admin1Code, Admin1CodeAdmin)
admin.site.register(models.Admin2Code, Admin2CodeAdmin)
admin.site.register(models.Locality, LocalityAdmin)
#admin.site.register(models.AlternateName, AlternateNameAdmin)
