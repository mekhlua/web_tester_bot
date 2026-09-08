from django.db import models
from django.contrib.auth.models import User


class TestSpec(models.Model):
    """
    A saved requirements spec, either uploaded as a doc or written directly.
    Belongs to one user.
    """
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="specs")
    name = models.CharField(max_length=200)
    base_url = models.URLField()
    raw_document = models.TextField(blank=True, null=True)  # original uploaded doc text, if any
    spec_yaml = models.TextField()  # the resolved YAML spec (generated or hand-written)
    needs_review = models.TextField(blank=True, null=True)  # JSON list of items flagged during parsing
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional login support: if requires_login is True, a login workflow
    # is auto-prepended before running any other checks/workflows, so the
    # rest of the test runs in an authenticated session.
    requires_login = models.BooleanField(default=False)
    login_path = models.CharField(max_length=200, blank=True, null=True)  # e.g. "/login"
    username_selector = models.CharField(max_length=200, blank=True, null=True)
    password_selector = models.CharField(max_length=200, blank=True, null=True)
    submit_selector = models.CharField(max_length=200, blank=True, null=True)
    login_username = models.CharField(max_length=200, blank=True, null=True)
    login_password = models.CharField(max_length=200, blank=True, null=True)  # stored plain text — use a disposable test account, not a real password

    def __str__(self):
        return f"{self.name} ({self.owner.username})"


class TestRun(models.Model):
    """
    One execution of a TestSpec. Stores status and links to the report.
    """
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    spec = models.ForeignKey(TestSpec, on_delete=models.CASCADE, related_name="runs")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="runs")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    report_json = models.TextField(blank=True, null=True)  # full report dict, saved as JSON string
    total_checks = models.IntegerField(default=0)
    passed_checks = models.IntegerField(default=0)
    failed_checks = models.IntegerField(default=0)

    def __str__(self):
        return f"Run #{self.id} - {self.spec.name} ({self.status})"