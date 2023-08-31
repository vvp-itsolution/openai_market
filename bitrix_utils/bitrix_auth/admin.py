# coding=utf-8

from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.shortcuts import render
from django.urls import reverse, NoReverseMatch
from django.utils.safestring import mark_safe
from mptt.admin import MPTTModelAdmin

from bitrix_utils.bitrix_auth.models import *
from bitrix_utils.bitrix_auth.models.bitrix_app_installation import BitrixAppInstallation

from prettyjson import PrettyJSONWidget

from its_utils.functions.compatibility import get_json_field

JSONField = get_json_field()


class JsonInfoAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }


class BitrixUserAdminInline(admin.TabularInline):
    model = BitrixUser
    extra = 0
    fields = 'fullname', 'email', 'is_admin'
    readonly_fields = fields
    ordering = '-is_admin', '-id'

    def fullname(self, obj):
        return mark_safe('<a href="/admin/{}/{}/{}/change/" target="_blank">{} {}</a>'.format(
            obj._meta.app_label, obj._meta.model_name, obj.id, obj.last_name, obj.first_name
        ))

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, *args, **kwargs):
        return False


class BitrixUserTokenAdminInline(admin.TabularInline):
    model = BitrixUserToken
    extra = 0
    fields = ['id', 'name', 'is_active', 'refresh_error']
    readonly_fields = fields

    def name(self, obj):
        return mark_safe('<a href="/admin/{}/{}/{}/change/" target="_blank">{}</a>'.format(
            obj._meta.app_label, obj._meta.model_name, obj.id, obj.application
        ))


@admin.register(BitrixPortal)
class BitrixPortalAdmin(admin.ModelAdmin):
    list_display = 'id', '__str__', 'joined', 'users', 'active'
    list_display_links = list_display
    list_filter = ['active']
    search_fields = ['domain']

    inlines = [BitrixUserAdminInline]

    def users(self, obj):
        return BitrixUser.objects.filter(portal_id=obj.id).count()


@admin.register(BitrixUser)
class BitrixUserAdmin(admin.ModelAdmin):
    list_display = 'id', 'portal', '__str__', 'bitrix_id', 'email', 'application', 'is_admin', 'user_is_active', 'refresh_error'
    list_display_links = list_display
    list_filter = 'user_is_active', 'is_admin', 'refresh_error'
    search_fields = 'first_name', 'last_name', 'portal__domain', 'bitrix_id'
    raw_id_fields = ['portal']

    inlines = [BitrixUserTokenAdminInline]

    class ImNotifyForm(forms.Form):
        TEMPLATE = 'bitrix_auth/admin/bitrix_user_im_notify.html'
        NOTIFY_ACTION = 'notify-action'
        IM_TYPE_CHOICES = (
            ('SYSTEM', 'SYSTEM (Системное без аватара)'),
            ('USER', 'USER (От данного пользователя)'),
        )

        to = forms.IntegerField(min_value=1,
                                required=False,
                                label='ID получателя',
                                help_text='Оставьте поле пустым для '
                                          'нотификации текущих пользователей')
        message = forms.CharField(widget=forms.Textarea,
                                  required=True,
                                  label='Сообщение',
                                  help_text='Поддерживается часть BB-кода')
        type = forms.ChoiceField(choices=IM_TYPE_CHOICES,
                                 required=True,
                                 label='Тип сообщения')
        notify_action = forms.CharField(widget=forms.HiddenInput,
                                        initial=NOTIFY_ACTION)
        app_name = forms.ChoiceField(required=True, label='Приложение')

        def __init__(self, *args, **kwargs):
            super(BitrixUserAdmin.ImNotifyForm, self).__init__(*args, **kwargs)
            self.fields['app_name'].choices = list(sorted(
                [(
                    app.name,
                    '{} ({})'.format(app.name, app.description or 'без описания'),
                ) for app in BitrixApp.objects.only('name', 'description')],
                key=lambda name_and_display: name_and_display[1],
            ))

        def clean(self):
            cleaned_data = super(BitrixUserAdmin.ImNotifyForm, self).clean()
            if cleaned_data.get('notify_action') != self.NOTIFY_ACTION:
                raise forms.ValidationError(
                    'action must be %s' % self.NOTIFY_ACTION)

    def get_actions(self, request):
        actions = super(BitrixUserAdmin, self).get_actions(request)
        actions['im_notify'] = (
            BitrixUserAdmin.im_notify,
            'im_notify',
            'Отправить уведомление от %(verbose_name_plural)s'
        )
        return actions

    def im_notify(self, request, queryset):
        """Action уведомления пользователя
        """
        NOTIFY_ACTION = self.ImNotifyForm.NOTIFY_ACTION

        if request.method == 'POST' and \
                request.POST.get('notify_action') == NOTIFY_ACTION:

            form = self.ImNotifyForm(request.POST)
            if form.is_valid():
                for user in queryset:
                    try:
                        res = user.im_notify(
                            to=form.cleaned_data['to'] or user.bitrix_id,
                            message=form.cleaned_data['message'],
                            type=form.cleaned_data['type'],
                            application_names=[
                                form.cleaned_data['app_name'],
                            ],
                        )
                        if not res['result']:
                            self.message_user(
                                request=request,
                                level=messages.ERROR,
                                message='{u}: user is missing? result {res}'
                                .format(u=user.display_name, res=res),
                            )
                        else:
                            self.message_user(
                                request=request,
                                level=messages.SUCCESS,
                                message='{}: ok'.format(user.display_name),
                            )
                    except Exception as e:
                        self.message_user(
                            request=request,
                            level=messages.ERROR,
                            message='{u}: {e!r}'.format(
                                u=user.display_name,
                                e=e,
                            ),
                        )
                return
        else:
            form = self.ImNotifyForm()

        return render(request, self.ImNotifyForm.TEMPLATE, dict(
            users=queryset,
            form=form,
            django_action_form=dict(
                action=request.POST['action'],
                select_across=request.POST['select_across'],
                index=request.POST['index'],
                selected_action=request.POST.getlist('_selected_action'),
            )
        ))


@admin.register(BitrixDepartment)
class BitrixDepartmentAdmin(MPTTModelAdmin):
    list_display = 'portal', 'name', 'parent'
    list_display_links = list_display
    list_select_related = 'portal', 'parent',
    raw_id_fields = 'portal', 'parent',


@admin.register(BitrixGroup)
class BitrixGroupAdmin(admin.ModelAdmin):
    list_display = 'portal', 'name'
    list_display_links = list_display
    raw_id_fields = ['portal']

@admin.register(BitrixUserGroup)
class BitrixUserGroupAdmin(admin.ModelAdmin):
    list_display = 'group', 'user'
    list_display_links = list_display
    raw_id_fields = ['user']


@admin.register(BitrixAccessObjectSet)
class BitrixAccessObjectSetAdmin(admin.ModelAdmin):
    list_display = 'id', 'objects_related_to_set'
    list_display_links = list_display

    def objects_related_to_set(self, set_):
        return u', '.join(
            ['%s %s' % (o.TYPES[o.type][1], o.type_id) for o in BitrixAccessObject.objects.filter(set=set_)])


@admin.register(BitrixAccessObject)
class BitrixAccessObjectAdmin(admin.ModelAdmin):
    list_display = 'id', 'set', 'type', 'type_id'
    list_display_links = list_display

    raw_id_fields = 'set',


@admin.register(BitrixApp)
class BitrixAppAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'bitrix_client_id', 'bitrix_client_secret', 'description')
    list_display_links = list_display
    search_fields = 'name', 'bitrix_client_id', 'description',


@admin.register(BitrixUserToken)
class BitrixUserTokenAdmin(JsonInfoAdmin):
    readonly_fields = ['id']
    list_display = 'id', 'user', 'get_portal', 'auth_token', 'application', 'is_active', 'refresh_error'
    list_display_links = list_display
    list_filter = 'is_active', 'application', 'user__portal__domain', 'refresh_error'
    search_fields = ['user__first_name', 'user__last_name']
    date_hierarchy = 'auth_token_date'
    raw_id_fields = ['user']
    actions = ['refresh']
    change_form_template = 'bitrix_auth/admin/bitrix_user_token_change_form.html'

    def get_portal(self, obj):
        return obj.user.portal
    get_portal.short_description = 'Portal'
    get_portal.admin_order_field = 'user__portal'

    def refresh(self, request, queryset):
        for instance in queryset:
            if instance.refresh():
                self.message_user(request, '#%s refreshed.' % instance.pk)
            else:
                self.message_user(request, '#%s not refreshed.' % instance.pk,
                                  level=messages.WARNING)
    refresh.short_description = "Refresh tokens"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        url = getattr(settings, 'BITRIX_AUTH_AS_USER_URL', None)
        if url is None:
            app = BitrixUserToken.objects.only('application').get(id=object_id).application
            url = app.redirect_url
            # try:
            #     url = reverse('index')
            # except NoReverseMatch:
            #     url = '/'
        bitrix_user_token_auth_url = (
            '{url}?shs={secret}&token_id={token_id}'.format(
                url=url,
                secret=settings.BITRIX_SHADOW_SECRET,
                token_id=object_id,
            ))
        extra_context['bitrix_user_token_auth_url'] = bitrix_user_token_auth_url
        return super(BitrixUserTokenAdmin, self).change_view(
            request, object_id, form_url, extra_context=extra_context,
        )


@admin.register(BitrixAppInstallation)
class BitrixAppInstallationAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'portal', 'application', 'app_id', 'installation_date',
        'get_url_to_tokens',
    )
    list_display_links = list_display
    search_fields = 'id', 'portal__domain', 'application__name',
    list_filter = 'application',
    raw_id_fields = 'portal',


from its_utils.app_admin.auto_register import auto_register

auto_register("bitrix_auth")