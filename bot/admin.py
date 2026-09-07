from django.contrib import admin
from bot.models import TestSpec, TestRun


@admin.register(TestSpec)
class TestSpecAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "base_url", "created_at")
    list_filter = ("owner",)


@admin.register(TestRun)
class TestRunAdmin(admin.ModelAdmin):
    list_display = ("id", "spec", "owner", "status", "started_at", "passed_checks", "failed_checks")
    list_filter = ("status", "owner")