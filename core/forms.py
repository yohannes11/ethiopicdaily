from django import forms
from .models import Advertisement, Article, Category, TelegramChannel


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'summary', 'content', 'image_url', 'video_url', 'category',
                  'is_featured', 'is_breaking']

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None and not user.is_admin():
            self.fields.pop('is_featured', None)
            self.fields.pop('is_breaking', None)

    def clean_title(self):
        value = self.cleaned_data.get('title', '').strip()
        if not value:
            raise forms.ValidationError("Title is required.")
        return value

    def clean_summary(self):
        value = self.cleaned_data.get('summary', '').strip()
        if not value:
            raise forms.ValidationError("Summary is required.")
        return value

    def clean_content(self):
        value = self.cleaned_data.get('content', '').strip()
        if not value:
            raise forms.ValidationError("Content is required.")
        return value


class ChannelForm(forms.ModelForm):
    class Meta:
        model = TelegramChannel
        fields = ['slug', 'display_name', 'fetch_interval']

    def clean_slug(self):
        value = self.cleaned_data.get('slug', '').strip().lower()
        if not value:
            raise forms.ValidationError("Username is required.")
        qs = TelegramChannel.objects.filter(slug=value)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A channel with this username already exists.")
        return value

    def clean_display_name(self):
        value = self.cleaned_data.get('display_name', '').strip()
        if not value:
            raise forms.ValidationError("Display name is required.")
        return value

    def clean_fetch_interval(self):
        value = self.cleaned_data.get('fetch_interval', 5)
        return max(1, int(value))


class AdvertisementForm(forms.ModelForm):
    class Meta:
        model = Advertisement
        fields = ['name', 'placement', 'ad_code', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-200',
                'placeholder': 'e.g. Google AdSense — Homepage Banner',
            }),
            'placement': forms.Select(attrs={
                'class': 'w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-200',
            }),
            'ad_code': forms.Textarea(attrs={
                'class': 'w-full rounded-lg border border-gray-200 px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-amber-200',
                'rows': 8,
                'placeholder': 'Paste your <ins class="adsbygoogle"> ... </ins> code here',
                'spellcheck': 'false',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-amber-600 focus:ring-amber-200',
            }),
        }

    def clean_name(self):
        value = self.cleaned_data.get('name', '').strip()
        if not value:
            raise forms.ValidationError("Name is required.")
        return value

    def clean_ad_code(self):
        value = self.cleaned_data.get('ad_code', '').strip()
        if not value:
            raise forms.ValidationError("Ad code is required.")
        return value


class ArticleSearchForm(forms.Form):
    q = forms.CharField(
        required=False, label="Search",
        widget=forms.TextInput(attrs={
            "class": "w-full rounded-lg border border-gray-200 px-3 py-2 text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-200",
            "placeholder": "Search by title, summary, or content…",
        }),
    )
    status = forms.ChoiceField(
        required=False, label="Status",
        choices=[],
        widget=forms.Select(attrs={
            "class": "rounded-lg border border-gray-200 px-3 py-2 text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-200",
        }),
    )
    category = forms.ModelChoiceField(
        queryset=None, required=False, empty_label="All categories", label="Category",
        widget=forms.Select(attrs={
            "class": "w-full rounded-lg border border-gray-200 px-3 py-2 text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-200",
        }),
    )
    author_email = forms.CharField(
        required=False, label="Author email",
        widget=forms.TextInput(attrs={
            "class": "w-full rounded-lg border border-gray-200 px-3 py-2 text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-200",
            "placeholder": "Filter by author email…",
        }),
    )
    date_from = forms.DateField(
        required=False, label="From",
        widget=forms.DateInput(attrs={
            "type": "date",
            "class": "w-full rounded-lg border border-gray-200 px-3 py-2 text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-200",
        }),
    )
    date_to = forms.DateField(
        required=False, label="To",
        widget=forms.DateInput(attrs={
            "type": "date",
            "class": "w-full rounded-lg border border-gray-200 px-3 py-2 text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-200",
        }),
    )
    is_featured = forms.ChoiceField(
        required=False, label="Featured",
        choices=[("", "Any"), ("1", "Featured only"), ("0", "Not featured")],
        widget=forms.Select(attrs={
            "class": "w-full rounded-lg border border-gray-200 px-3 py-2 text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-200",
        }),
    )
    is_breaking = forms.ChoiceField(
        required=False, label="Breaking",
        choices=[("", "Any"), ("1", "Breaking only"), ("0", "Not breaking")],
        widget=forms.Select(attrs={
            "class": "w-full rounded-lg border border-gray-200 px-3 py-2 text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-200",
        }),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].choices = [("", "All statuses")] + Article.Status.choices
        self.fields["category"].queryset = Category.objects.all()
        if user is not None and not user.is_admin():
            for f in ("author_email", "is_featured", "is_breaking"):
                self.fields.pop(f, None)
