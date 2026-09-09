from django import forms


class TestSpecForm(forms.Form):
    name = forms.CharField(max_length=200, label="Test name")
    base_url = forms.URLField(label="Website URL to test")
    requirements_doc = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 10}),
        label="Requirements (plain text)",
        help_text='Example: The homepage must load successfully. It should display the text "Welcome".'
    )

    requires_login = forms.BooleanField(
        required=False,
        label="This site requires logging in before testing"
    )
    login_path = forms.CharField(
        max_length=200, required=False,
        label="Login page path",
        help_text='e.g. "/login" — leave blank if not applicable'
    )
    username_selector = forms.CharField(
        max_length=200, required=False,
        label="Username field CSS selector",
        help_text='e.g. input[name="username"]'
    )
    password_selector = forms.CharField(
        max_length=200, required=False,
        label="Password field CSS selector",
        help_text='e.g. input[name="password"]'
    )
    submit_selector = forms.CharField(
        max_length=200, required=False,
        label="Login submit button CSS selector",
        help_text='e.g. button#login-button'
    )
    login_username = forms.CharField(
        max_length=200, required=False,
        label="Test username"
    )
    login_password = forms.CharField(
        max_length=200, required=False,
        widget=forms.PasswordInput(render_value=True),
        label="Test password",
        help_text="Use a disposable test account — not a real production password. Stored as plain text."
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("requires_login"):
            required_fields = [
                "login_path", "username_selector", "password_selector",
                "submit_selector", "login_username", "login_password"
            ]
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, "Required when 'requires login' is checked.")
        return cleaned_data


class AddInteractionCheckForm(forms.Form):
    selector = forms.CharField(
        max_length=200,
        label="Button/link CSS selector",
        help_text='e.g. #contact-button or a.nav-link[href="/projects"]'
    )
    expect_url_contains = forms.CharField(
        max_length=200, required=False,
        label="Expected URL contains (optional)",
        help_text='e.g. /projects — leave blank to skip this check'
    )
    expect_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Expected text after clicking (optional, one per line)",
        help_text="Add multiple lines to check for several things at once"
    )

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("expect_url_contains") and not cleaned_data.get("expect_text"):
            raise forms.ValidationError("Provide at least one of: expected URL or expected text.")
        return cleaned_data
