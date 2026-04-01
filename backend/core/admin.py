from django.contrib import admin
from core.models import User, Organisation, Membership, ContractorLink, WorkRecord


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'full_name', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ['name', 'org_type', 'paye_reference', 'paye_scheme_active', 'is_active']
    list_filter = ['org_type', 'is_active', 'paye_scheme_active']
    search_fields = ['name', 'paye_reference']


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'organisation', 'role', 'is_active']
    list_filter = ['role', 'is_active']


@admin.register(ContractorLink)
class ContractorLinkAdmin(admin.ModelAdmin):
    list_display = ['user', 'agency', 'umbrella', 'hourly_rate', 'tax_code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['user__email', 'tax_code', 'ni_number']


@admin.register(WorkRecord)
class WorkRecordAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'contractor', 'agency', 'state',
        'period_start', 'period_end', 'gross_amount', 'version',
    ]
    list_filter = ['state', 'agency', 'umbrella']
    search_fields = ['contractor__email']
    readonly_fields = ['id', 'version', 'created_at', 'updated_at']
